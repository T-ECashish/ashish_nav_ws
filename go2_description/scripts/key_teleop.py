#!/usr/bin/python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
import select
import termios
import tty

msg = """
Reading from the keyboard and Publishing to Twist!
---------------------------
Moving around:
        w
   a    s    d

w/s : forward/backward
a/d : strafe left/right
j/l : turn left/right
space : force stop

CTRL-C to quit
"""

moveBindings = {
    'w': (1, 0, 0, 0),
    's': (-1, 0, 0, 0),
    'j': (0, 1, 0, 0),
    'l': (0, -1, 0, 0),
    'a': (0, 0, 0, 1),
    'd': (0, 0, 0, -1),
    ' ': (0, 0, 0, 0),
}

class Teleop(Node):
    def __init__(self):
        super().__init__('key_teleop')
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        self.settings = termios.tcgetattr(sys.stdin)
        self.speed = 0.5
        self.turn = 1.0
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.th = 0.0
        self.status = 0
        self.stop_counter = 0

    def getKey(self):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.6)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def run(self):
        print(msg)
        try:
            while rclpy.ok():
                key = self.getKey()
                if key in moveBindings.keys():
                    self.x = moveBindings[key][0]
                    self.y = moveBindings[key][1]
                    self.z = moveBindings[key][2]
                    self.th = moveBindings[key][3]
                    self.stop_counter = 0
                elif key == '\x03': # CTRL-C
                    break
                else:
                    self.x = 0.0
                    self.y = 0.0
                    self.z = 0.0
                    self.th = 0.0
                twist = Twist()
                twist.linear.x = self.x * self.speed
                twist.linear.y = self.y * self.speed
                twist.linear.z = self.z * self.speed
                twist.angular.x = 0.0
                twist.angular.y = 0.0
                twist.angular.z = self.th * self.turn
                self.publisher_.publish(twist)

        except Exception as e:
            print(e)
        finally:
            twist = Twist()
            twist.linear.x = 0.0
            twist.linear.y = 0.0
            twist.linear.z = 0.0
            twist.angular.x = 0.0
            twist.angular.y = 0.0
            twist.angular.z = 0.0
            self.publisher_.publish(twist)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)

def main(args=None):
    rclpy.init(args=args)
    teleop = Teleop()
    teleop.run()
    teleop.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
