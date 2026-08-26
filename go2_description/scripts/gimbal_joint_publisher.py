#!/usr/bin/python3
"""Append gimbal joint states to /joint_states without overwriting leg joints."""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


GIMBAL_JOINTS = ['gimbal_roll_joint', 'gimbal_pitch_joint']


class GimbalJointPublisher(Node):
    def __init__(self):
        super().__init__('gimbal_joint_publisher')
        self.latest_msg = None
        self.subscription = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_callback,
            10,
        )
        self.publisher = self.create_publisher(JointState, '/joint_states', 10)

    def joint_callback(self, msg: JointState):
        if any(name in msg.name for name in GIMBAL_JOINTS):
            return

        merged = JointState()
        merged.header.stamp = self.get_clock().now().to_msg()
        merged.name = list(msg.name) + GIMBAL_JOINTS
        merged.position = list(msg.position) + [0.0, 0.0]
        merged.velocity = list(msg.velocity) + [0.0, 0.0] if msg.velocity else []
        merged.effort = list(msg.effort) + [0.0, 0.0] if msg.effort else []
        self.publisher.publish(merged)


def main(args=None):
    rclpy.init(args=args)
    node = GimbalJointPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
