import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO
import os

class YoloDetector(Node):
    def __init__(self):
        super().__init__('yolo_detector')
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            '/camera/car_camera/image_raw',
            self.listener_callback,
            10)
        self.publisher = self.create_publisher(Image, '/camera/detections_image', 10)

        model_path = os.path.expanduser('~/car_robot_ws/custom_yolo.pt')
        self.model = YOLO(model_path)
        self.last_log_time = self.get_clock().now()
        self.get_logger().info('YOLO detector node started')

    def listener_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        results = self.model(cv_image, verbose=False)
        annotated = results[0].plot()

        now = self.get_clock().now()
        if (now - self.last_log_time).nanoseconds > 1e9:
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                name = self.model.names[cls_id]
                self.get_logger().info(f'Detected: {name} ({conf:.2f})')
            self.last_log_time = now

        out_msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
        out_msg.header = msg.header
        self.publisher.publish(out_msg)

def main(args=None):
    rclpy.init(args=args)
    node = YoloDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
