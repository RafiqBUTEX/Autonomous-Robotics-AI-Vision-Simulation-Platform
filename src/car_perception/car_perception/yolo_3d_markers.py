import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import String
from cv_bridge import CvBridge
from ultralytics import YOLO
import numpy as np
import math
import json
import os

IMG_WIDTH = 640
IMG_HEIGHT = 480
HFOV = 1.3962634
FX = IMG_WIDTH / (2 * math.tan(HFOV / 2))
FY = FX
CX = IMG_WIDTH / 2
CY = IMG_HEIGHT / 2

class Yolo3DMarkers(Node):
    def __init__(self):
        super().__init__('yolo_3d_markers')
        self.bridge = CvBridge()
        self.latest_depth = None

        self.rgb_sub = self.create_subscription(
            Image, '/camera/car_camera/image_raw', self.rgb_callback, 10)
        self.depth_sub = self.create_subscription(
            Image, '/camera/car_depth/depth/image_raw', self.depth_callback, 10)

        self.marker_pub = self.create_publisher(MarkerArray, '/detected_objects_markers', 10)
        self.unity_pub = self.create_publisher(String, '/detections_json', 10)

        model_path = os.path.expanduser('~/car_robot_ws/custom_yolo.pt')
        self.model = YOLO(model_path)
        self.last_log_time = self.get_clock().now()
        self.get_logger().info('YOLO 3D marker node started')

    def depth_callback(self, msg):
        self.latest_depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')

    def rgb_callback(self, msg):
        if self.latest_depth is None:
            return

        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        results = self.model(cv_image, verbose=False)

        marker_array = MarkerArray()
        detections_list = []
        marker_id = 0

        for box in results[0].boxes:
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            name = self.model.names[cls_id]

            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            u = int((x1 + x2) / 2)
            v = int((y1 + y2) / 2)

            if not (0 <= v < self.latest_depth.shape[0] and 0 <= u < self.latest_depth.shape[1]):
                continue

            z = float(self.latest_depth[v, u])
            if not np.isfinite(z) or z <= 0:
                continue

            x = (u - CX) * z / FX
            y = (v - CY) * z / FY

            detections_list.append({'label': name, 'confidence': round(conf, 2), 'distance': round(z, 2)})

            marker = Marker()
            marker.header.frame_id = 'camera_link'
            marker.header.stamp = msg.header.stamp
            marker.ns = 'detections'
            marker.id = marker_id
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD
            marker.pose.position.x = z
            marker.pose.position.y = -x
            marker.pose.position.z = -y
            marker.pose.orientation.w = 1.0
            marker.scale.x = 0.4
            marker.scale.y = 0.4
            marker.scale.z = 0.4
            marker.color.r = 1.0
            marker.color.g = 0.2
            marker.color.b = 0.2
            marker.color.a = 0.8
            marker.lifetime.sec = 5

            text_marker = Marker()
            text_marker.header.frame_id = 'camera_link'
            text_marker.header.stamp = msg.header.stamp
            text_marker.ns = 'labels'
            text_marker.id = marker_id
            text_marker.type = Marker.TEXT_VIEW_FACING
            text_marker.action = Marker.ADD
            text_marker.pose.position.x = z
            text_marker.pose.position.y = -x
            text_marker.pose.position.z = -y + 0.3
            text_marker.scale.z = 0.2
            text_marker.color.r = 1.0
            text_marker.color.g = 1.0
            text_marker.color.b = 1.0
            text_marker.color.a = 1.0
            text_marker.text = f'{name} {conf:.2f} ({z:.1f}m)'
            text_marker.lifetime.sec = 5

            marker_array.markers.append(marker)
            marker_array.markers.append(text_marker)
            marker_id += 1

        self.marker_pub.publish(marker_array)
        self.unity_pub.publish(String(data=json.dumps(detections_list)))

def main(args=None):
    rclpy.init(args=args)
    node = Yolo3DMarkers()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
