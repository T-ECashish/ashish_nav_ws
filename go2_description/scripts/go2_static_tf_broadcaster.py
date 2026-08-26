#!/usr/bin/python3
"""Static TF with timestamp 0 (valid for static transforms, immune to clock jumps)."""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import StaticTransformBroadcaster


class Go2StaticTfBroadcaster(Node):
    def __init__(self):
        super().__init__('go2_static_tf_broadcaster')
        self.broadcaster = StaticTransformBroadcaster(self)
        self.published = False
        self.timer = self.create_timer(1.0, self.publish_once)

    def publish_once(self):
        if self.published:
            return
        # Wait until /clock is alive
        if self.get_clock().now().nanoseconds == 0:
            return

        t = TransformStamped()
        t.header.stamp.sec = 0
        t.header.stamp.nanosec = 0
        t.header.frame_id = 'imu_link'
        t.child_frame_id = 'go2/imu_link/imu_sensor'
        t.transform.rotation.w = 1.0
        self.broadcaster.sendTransform([t])
        self.published = True
        self.get_logger().info('Static IMU TF published')
        self.timer.cancel()


def main():
    rclpy.init()
    node = Go2StaticTfBroadcaster()
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
