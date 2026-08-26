#!/usr/bin/python3
"""Publish Go2 URDF on /go2_description/robot_description for RViz RobotModel.

Separate from /robot_description so RViz never latches onto a stale slam_go2 URDF.
"""
import subprocess

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import String
from ament_index_python.packages import get_package_share_directory


class RobotDescriptionPublisher(Node):
    def __init__(self):
        super().__init__('robot_description_publisher')
        pkg_share = get_package_share_directory('go2_description')
        xacro_path = f'{pkg_share}/xacro/robot.xacro'
        xml_string = subprocess.check_output(['xacro', xacro_path], text=True)

        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.publisher = self.create_publisher(String, '/go2_description/robot_description', qos)
        self.msg = String()
        self.msg.data = xml_string
        self.publisher.publish(self.msg)
        self.timer = self.create_timer(2.0, lambda: self.publisher.publish(self.msg))
        self.get_logger().info(
            'RobotModel topic: /go2_description/robot_description '
            '(do not use /robot_description in RViz)'
        )


def main():
    rclpy.init()
    node = RobotDescriptionPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
