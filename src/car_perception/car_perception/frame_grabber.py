import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os

class FrameGrabber(Node):
    def __init__(self):
        super().__init__('frame_grabber')
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            '/camera/car_camera/image_raw',
            self.listener_callback,
            10)
        self.save_dir = os.path.expanduser('~/car_robot_ws/sample_frames')
        os.makedirs(self.save_dir, exist_ok=True)
        self.count = 0
        self.get_logger().info('Frame grabber started, saving to ' + self.save_dir)

    def listener_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        if self.count % 30 == 0:  # save roughly every 30th frame (~1 per second at 30fps)
            filename = os.path.join(self.save_dir, f'frame_{self.count:05d}.jpg')
            cv2.imwrite(filename, cv_image)
            self.get_logger().info(f'Saved {filename}')
        self.count += 1

def main(args=None):
    rclpy.init(args=args)
    node = FrameGrabber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
