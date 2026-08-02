import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO
import json
import os

class YoloDetectorRear(Node):
    def __init__(self):
        super().__init__('yolo_detector_rear')
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            '/camera/car_camera_rear/image_raw',
            self.listener_callback,
            10)
        self.publisher = self.create_publisher(Image, '/camera/detections_image_rear', 10)
        self.unity_pub = self.create_publisher(String, '/detections_json_rear', 10)

        model_path = os.path.expanduser('~/car_robot_ws/custom_yolo.pt')
        self.model = YOLO(model_path)
        self.last_log_time = self.get_clock().now()
        self.get_logger().info('YOLO rear detector node started')

    def listener_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        results = self.model(cv_image, verbose=False)
        annotated = results[0].plot()

        detections_list = []
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            name = self.model.names[cls_id]
            detections_list.append({'label': name, 'confidence': round(conf, 2)})

        now = self.get_clock().now()
        if (now - self.last_log_time).nanoseconds > 1e9:
            for d in detections_list:
                self.get_logger().info(f"[REAR] Detected: {d['label']} ({d['confidence']})")
            self.last_log_time = now

        self.unity_pub.publish(String(data=json.dumps(detections_list)))

        out_msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
        out_msg.header = msg.header
        self.publisher.publish(out_msg)

def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectorRear()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
