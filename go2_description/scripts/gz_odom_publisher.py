#!/usr/bin/python3
"""Publish /odom/raw from Gazebo model pose using /clock timestamps."""
import math

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Quaternion
from tf2_msgs.msg import TFMessage


PREFERRED_FRAMES = ('base_link', 'trunk', 'go2')


def yaw_from_quaternion(x, y, z, w):
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def yaw_to_quaternion(yaw):
    q = Quaternion()
    q.z = math.sin(yaw * 0.5)
    q.w = math.cos(yaw * 0.5)
    return q


def pick_base_transform(transforms):
    by_child = {t.child_frame_id: t for t in transforms}
    for name in PREFERRED_FRAMES:
        for child, t in by_child.items():
            if child == name or child.endswith('/' + name):
                return t
    return min(transforms, key=lambda t: len(t.child_frame_id))


class GzOdomPublisher(Node):
    def __init__(self):
        super().__init__('gz_odom_publisher')
        self.publisher = self.create_publisher(Odometry, '/odom/raw', 10)
        self.subscription = self.create_subscription(
            TFMessage, '/gz_model_pose', self.callback, 10)
        self.last_pose = None
        self.last_time = None
        self._logged = False

    def callback(self, msg: TFMessage):
        if not msg.transforms:
            return
        t = pick_base_transform(msg.transforms)
        if not self._logged:
            self.get_logger().info(f'Using Gazebo pose frame: {t.child_frame_id}')
            self._logged = True

        # Always stamp with /clock (sim time) — never Gazebo pose stamp
        stamp = self.get_clock().now().to_msg()
        now_sec = stamp.sec + stamp.nanosec * 1e-9
        if now_sec <= 0.0:
            return

        x = t.transform.translation.x
        y = t.transform.translation.y
        q = t.transform.rotation
        yaw = yaw_from_quaternion(q.x, q.y, q.z, q.w)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = x
        odom.pose.pose.position.y = y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation = yaw_to_quaternion(yaw)

        if self.last_pose is not None and self.last_time is not None:
            dt = now_sec - self.last_time
            if dt < 0.0:
                # Sim clock jumped back — reset velocity state
                self.last_pose = None
                self.last_time = None
            elif 1e-4 < dt < 1.0:
                odom.twist.twist.linear.x = (x - self.last_pose[0]) / dt
                odom.twist.twist.linear.y = (y - self.last_pose[1]) / dt
                dyaw = yaw - self.last_pose[2]
                while dyaw > math.pi:
                    dyaw -= 2.0 * math.pi
                while dyaw < -math.pi:
                    dyaw += 2.0 * math.pi
                odom.twist.twist.angular.z = dyaw / dt

        self.last_pose = (x, y, yaw)
        self.last_time = now_sec
        self.publisher.publish(odom)


def main():
    rclpy.init()
    node = GzOdomPublisher()
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
