import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import time
import math
from gazebo_msgs.srv import SetEntityState
from gazebo_msgs.msg import EntityState

NUM_SCAN_BINS = 36  # downsample 360 LiDAR rays into 36 bins (10 deg each)
MAX_RANGE = 15.0
COLLISION_DIST = 0.35

class GazeboCarEnv(gym.Env):
    def __init__(self):
        super().__init__()
        rclpy.init(args=None)
        self.node = Node('rl_env_node')

        self.latest_scan = None
        self.latest_odom = None
        self.start_x = None

        self.node.create_subscription(LaserScan, '/scan', self._scan_cb, 10)
        self.node.create_subscription(Odometry, '/odom', self._odom_cb, 10)
        self.cmd_pub = self.node.create_publisher(Twist, '/cmd_vel', 10)
        self.set_state_client = self.node.create_client(SetEntityState, '/gazebo/set_entity_state')

        self.action_space = spaces.Box(low=np.array([-0.5, -1.0]), high=np.array([0.5, 1.0]), dtype=np.float32)
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(NUM_SCAN_BINS,), dtype=np.float32)

        self.step_count = 0
        self.max_steps = 300

    def _scan_cb(self, msg):
        self.latest_scan = msg

    def _odom_cb(self, msg):
        self.latest_odom = msg

    def _spin_until(self, condition_fn, timeout=2.0):
        start = time.time()
        while not condition_fn() and (time.time() - start) < timeout:
            rclpy.spin_once(self.node, timeout_sec=0.05)

    def _get_obs(self):
        self._spin_until(lambda: self.latest_scan is not None)
        ranges = np.array(self.latest_scan.ranges)
        ranges = np.nan_to_num(ranges, nan=MAX_RANGE, posinf=MAX_RANGE, neginf=0.0)
        ranges = np.clip(ranges, 0.0, MAX_RANGE)
        bin_size = len(ranges) // NUM_SCAN_BINS
        binned = np.array([ranges[i*bin_size:(i+1)*bin_size].min() for i in range(NUM_SCAN_BINS)])
        return (binned / MAX_RANGE).astype(np.float32)

    def _get_min_dist(self):
        if self.latest_scan is None:
            return MAX_RANGE
        ranges = np.array(self.latest_scan.ranges)
        ranges = np.nan_to_num(ranges, nan=MAX_RANGE, posinf=MAX_RANGE, neginf=0.0)
        return float(np.min(ranges)) if len(ranges) else MAX_RANGE

    def _get_x(self):
        self._spin_until(lambda: self.latest_odom is not None)
        return self.latest_odom.pose.pose.position.x

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        twist = Twist()
        self.cmd_pub.publish(twist)

        # Teleport car back to a fixed start pose
        state = EntityState()
        state.name = 'car_robot'
        state.pose.position.x = -8.0
        state.pose.position.y = 0.3
        state.pose.position.z = 0.1
        state.pose.orientation.w = 1.0


        req = SetEntityState.Request()
        req.state = state
        if self.set_state_client.wait_for_service(timeout_sec=2.0):
            future = self.set_state_client.call_async(req)
            self._spin_until(lambda: future.done(), timeout=2.0)
            if future.done():
                print(f"[RESET] Teleport result: {future.result()}")
            else:
                print("[RESET] Teleport call TIMED OUT")
        else:
            print("[RESET] Teleport service NOT AVAILABLE")

        time.sleep(0.3)

        self.step_count = 0
        self.latest_scan = None
        self.latest_odom = None
        self._spin_until(lambda: self.latest_scan is not None, timeout=3.0)
        self._spin_until(lambda: self.latest_odom is not None, timeout=3.0)
        self.start_x = self._get_x()
        self.prev_x = self.start_x
        obs = self._get_obs()
        return obs, {}

    def step(self, action):
        twist = Twist()
        twist.linear.x = float(action[0])
        twist.angular.z = float(action[1])
        self.cmd_pub.publish(twist)
        time.sleep(0.1)
        rclpy.spin_once(self.node, timeout_sec=0.05)

        obs = self._get_obs()
        min_dist = self._get_min_dist()
        x = self._get_x()

        progress = x - self.prev_x
        self.prev_x = x
        reward = progress * 10.0

        collided = min_dist < COLLISION_DIST
        if collided:
            reward -= 20.0

        reward += 0.01  # small alive bonus to encourage survival/forward motion

        self.step_count += 1
        terminated = bool(collided)
        truncated = self.step_count >= self.max_steps

        return obs, reward, terminated, truncated, {}

    def close(self):
        self.node.destroy_node()
        rclpy.shutdown()
