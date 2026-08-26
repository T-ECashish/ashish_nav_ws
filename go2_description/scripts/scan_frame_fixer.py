#!/usr/bin/python3
"""Republish Gazebo laser scans with URDF frame_id and a TF-safe stamp.

Stamps are shifted slightly into the past so slam_toolbox / RViz can look up
odom → livox_frame without extrapolating into the future.
"""
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import LaserScan


class ScanFrameFixer(Node):
    def __init__(self):
        super().__init__('scan_frame_fixer')
        self.declare_parameter('stamp_delay_sec', 0.1)
        self.stamp_delay_ns = int(
            float(self.get_parameter('stamp_delay_sec').value) * 1e9)
        self.publisher = self.create_publisher(LaserScan, '/scan', 10)
        self.subscription = self.create_subscription(
            LaserScan, '/scan_gz', self.callback, 10)
        self._logged_ready = False

    def callback(self, msg: LaserScan):
        now_ns = self.get_clock().now().nanoseconds
        # Wait until /clock is alive and large enough for the delay
        if now_ns <= self.stamp_delay_ns:
            return

        fixed = LaserScan()
        fixed.header.stamp = Time(nanoseconds=now_ns - self.stamp_delay_ns).to_msg()
        fixed.header.frame_id = 'livox_frame'
        fixed.angle_min = msg.angle_min
        fixed.angle_max = msg.angle_max
        fixed.angle_increment = msg.angle_increment
        fixed.time_increment = msg.time_increment
        fixed.scan_time = msg.scan_time
        fixed.range_min = msg.range_min
        fixed.range_max = msg.range_max
        fixed.ranges = msg.ranges
        fixed.intensities = msg.intensities
        self.publisher.publish(fixed)

        if not self._logged_ready:
            self.get_logger().info('Publishing /scan on frame livox_frame')
            self._logged_ready = True


def main():
    rclpy.init()
    node = ScanFrameFixer()
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
