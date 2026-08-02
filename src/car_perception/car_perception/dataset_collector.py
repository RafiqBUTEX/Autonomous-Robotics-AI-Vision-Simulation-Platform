import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
import cv2
import math
import os

IMG_WIDTH = 640
IMG_HEIGHT = 480
HFOV = 1.3962634
FX = IMG_WIDTH / (2 * math.tan(HFOV / 2))
FY = FX
CX = IMG_WIDTH / 2
CY = IMG_HEIGHT / 2

CAM_OFFSET = (0.375, 0.0, 0.075)

OBJECTS = [
    (0, (-4.0, 1.3, 0.25), (0.2, 0.2, 0.3)),
    (1, (0.0, 1.3, 0.15), (0.15, 0.15, 0.15)),
    (2, (4.0, 1.3, 0.5), (0.15, 0.15, 0.15)),
]

class DatasetCollector(Node):
    def __init__(self):
        super().__init__('dataset_collector')
        self.bridge = CvBridge()
        self.car_pos = None
        self.car_yaw = 0.0
        self.frame_count = 0

        self.out_dir = os.path.expanduser('~/car_robot_ws/dataset')
        os.makedirs(os.path.join(self.out_dir, 'images'), exist_ok=True)
        os.makedirs(os.path.join(self.out_dir, 'labels'), exist_ok=True)

        self.create_subscription(Image, '/camera/car_camera/image_raw', self.image_callback, 10)
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.drive_timer = self.create_timer(0.1, self.drive_pattern)
        self.going_forward = True
        self.turning = False
        self.turn_progress = 0.0
        self.turn_duration = 3.0

        self.get_logger().info('Dataset collector started, saving to ' + self.out_dir)

    def odom_callback(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self.car_pos = (p.x, p.y, p.z)
        self.car_yaw = 2.0 * math.atan2(q.z, q.w)

    def drive_pattern(self):
        if self.car_pos is None:
            return

        twist = Twist()
        x = self.car_pos[0]

        if self.turning:
            twist.linear.x = 0.0
            twist.angular.z = 0.5
            self.turn_progress += 0.1
            if self.turn_progress >= self.turn_duration:
                self.turning = False
                self.turn_progress = 0.0
                self.going_forward = not self.going_forward

        else:
            if self.going_forward:
                twist.linear.x = -0.4
                if x >= 8.0:
                    self.turning = True
            else:
                twist.linear.x = 0.4
                if x <= -8.0:
                    self.turning = True


        self.cmd_pub.publish(twist)

    def project(self, obj_world):
        dx = obj_world[0] - self.car_pos[0]
        dy = obj_world[1] - self.car_pos[1]
        dz = obj_world[2] - self.car_pos[2]
        c = math.cos(self.car_yaw)
        s = math.sin(self.car_yaw)
        x_base = c * dx + s * dy
        y_base = -s * dx + c * dy
        z_base = dz

        x_cam = x_base - CAM_OFFSET[0]
        y_cam = y_base - CAM_OFFSET[1]
        z_cam = z_base - CAM_OFFSET[2]

        if x_cam <= 0.1:
            return None

        u = FX * (-y_cam) / x_cam + CX
        v = FY * (-z_cam) / x_cam + CY
        return u, v, x_cam

    def image_callback(self, msg):
        if self.car_pos is None:
            return

        self.frame_count += 1
        if self.frame_count % 10 != 0:
            return

        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        labels = []

        for cls_id, world_pos, half_ext in OBJECTS:
            corners = []
            for sx in (-1, 1):
                for sy in (-1, 1):
                    for sz in (-1, 1):
                        corner = (world_pos[0] + sx * half_ext[0],
                                  world_pos[1] + sy * half_ext[1],
                                  world_pos[2] + sz * half_ext[2])
                        proj = self.project(corner)
                        if proj is not None:
                            corners.append(proj)

            if len(corners) < 8:
                continue

            us = [c[0] for c in corners]
            vs = [c[1] for c in corners]
            u_min, u_max = min(us), max(us)
            v_min, v_max = min(vs), max(vs)

            u_min = max(0, u_min)
            v_min = max(0, v_min)
            u_max = min(IMG_WIDTH, u_max)
            v_max = min(IMG_HEIGHT, v_max)

            if u_max - u_min < 5 or v_max - v_min < 5:
                continue

            x_center = ((u_min + u_max) / 2) / IMG_WIDTH
            y_center = ((v_min + v_max) / 2) / IMG_HEIGHT
            box_w = (u_max - u_min) / IMG_WIDTH
            box_h = (v_max - v_min) / IMG_HEIGHT

            labels.append(f'{cls_id} {x_center:.6f} {y_center:.6f} {box_w:.6f} {box_h:.6f}')

        if labels:
            fname = f'frame_{self.frame_count:06d}'
            cv2.imwrite(os.path.join(self.out_dir, 'images', fname + '.jpg'), cv_image)
            with open(os.path.join(self.out_dir, 'labels', fname + '.txt'), 'w') as f:
                f.write('\n'.join(labels))
            self.get_logger().info(f'Saved {fname} with {len(labels)} labels')

def main(args=None):
    rclpy.init(args=args)
    node = DatasetCollector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
