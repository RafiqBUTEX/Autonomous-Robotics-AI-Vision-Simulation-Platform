import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import numpy as np
import os

class YoloDistance(Node):
    def __init__(self):
        super().__init__('yolo_distance')
        self.bridge = CvBridge()
        self.latest_depth = None

        self.rgb_sub = self.create_subscription(
            Image, '/camera/car_camera/image_raw', self.rgb_callback, 10)
        self.depth_sub = self.create_subscription(
            Image, '/camera/car_depth/depth/image_raw', self.depth_callback, 10)

        model_path = os.path.expanduser('~/car_robot_ws/yolov8n.pt')
        self.model = YOLO(model_path)
        self.last_log_time = self.get_clock().now()
        self.get_logger().info('YOLO distance node started')

    def depth_callback(self, msg):
        depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
        self.latest_depth = depth_image

    def rgb_callback(self, msg):
        if self.latest_depth is None:
            return

        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        results = self.model(cv_image, verbose=False)

        now = self.get_clock().now()
        if (now - self.last_log_time).nanoseconds > 1e9:
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                name = self.model.names[cls_id]

                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                if 0 <= cy < self.latest_depth.shape[0] and 0 <= cx < self.latest_depth.shape[1]:
                    distance = self.latest_depth[cy, cx]
                    if np.isfinite(distance):
                        self.get_logger().info(
                            f'Detected: {name} ({conf:.2f}) at {distance:.2f} m')
                    else:
                        self.get_logger().info(
                            f'Detected: {name} ({conf:.2f}) - distance unavailable')

            self.last_log_time = now

def main(args=None):
    rclpy.init(args=args)
    node = YoloDistance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
