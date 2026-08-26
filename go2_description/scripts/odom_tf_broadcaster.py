#!/usr/bin/python3
"""Broadcast odom → base_link at a steady rate so LaserScan TF lookups succeed."""
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped


class OdomTfBroadcaster(Node):
    def __init__(self):
        super().__init__('odom_tf_broadcaster')
        self.tf_broadcaster = TransformBroadcaster(self)
        self.subscription = self.create_subscription(
            Odometry, '/odom/raw', self.handle_odom, 50)
        self.last_odom = None
        self.last_stamp_ns = None
        # Keep TF fresher than /scan so slam_toolbox never extrapolates forward
        self.timer = self.create_timer(0.02, self.publish_tf)

    def handle_odom(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        if abs(x) > 1000.0 or abs(y) > 1000.0:
            return
        self.last_odom = msg

    def publish_tf(self):
        if self.last_odom is None:
            return

        stamp = self.get_clock().now().to_msg()
        stamp_ns = stamp.sec * 10**9 + stamp.nanosec
        if stamp_ns == 0:
            return
        if self.last_stamp_ns is not None and stamp_ns < self.last_stamp_ns:
            if self.last_stamp_ns - stamp_ns < 500_000_000:
                return
            self.last_stamp_ns = None
        if self.last_stamp_ns is not None and stamp_ns == self.last_stamp_ns:
            return
        self.last_stamp_ns = stamp_ns

        msg = self.last_odom
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = 0.0
        t.transform.rotation = msg.pose.pose.orientation
        self.tf_broadcaster.sendTransform(t)


def main():
    rclpy.init()
    node = OdomTfBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    try:
        rclpy.shutdown()
    except Exception:
        pass


if __name__ == '__main__':
    main()
