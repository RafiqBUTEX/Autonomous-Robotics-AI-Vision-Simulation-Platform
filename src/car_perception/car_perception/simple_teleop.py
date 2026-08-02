import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
import termios
import tty

SPEED = 0.15
TURN = 0.3

class SimpleTeleop(Node):
    def __init__(self):
        super().__init__('simple_teleop')
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.get_logger().info('Keys: f=forward b=backward l=left r=right s=stop q=quit')

    def send(self, linear, angular):
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.publisher.publish(msg)

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

def main(args=None):
    rclpy.init(args=args)
    node = SimpleTeleop()
    print("f=forward b=backward l=left r=right s=stop q=quit")
    try:
        while True:
            key = get_key()
            if key == 'f':
                node.send(SPEED, 0.0)
                print("forward")
            elif key == 'b':
                node.send(-SPEED, 0.0)
                print("backward")
            elif key == 'l':
                node.send(0.0, TURN)
                print("left")
            elif key == 'r':
                node.send(0.0, -TURN)
                print("right")
            elif key == 's':
                node.send(0.0, 0.0)
                print("stop")
            elif key == 'q':
                node.send(0.0, 0.0)
                break
    except KeyboardInterrupt:
        pass
    finally:
        node.send(0.0, 0.0)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
