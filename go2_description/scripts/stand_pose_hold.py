#!/usr/bin/python3
"""Hold standing pose, then reset the Go2 upright once in Gazebo."""
import subprocess
import time

import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Duration
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


JOINTS = [
    'FL_hip_joint', 'FL_thigh_joint', 'FL_calf_joint',
    'FR_hip_joint', 'FR_thigh_joint', 'FR_calf_joint',
    'RL_hip_joint', 'RL_thigh_joint', 'RL_calf_joint',
    'RR_hip_joint', 'RR_thigh_joint', 'RR_calf_joint',
]

STAND = [
    0.0, 0.8, -1.5,
    0.0, 0.8, -1.5,
    0.0, 0.8, -1.5,
    0.0, 0.8, -1.5,
]


class StandPoseHold(Node):
    def __init__(self):
        super().__init__('stand_pose_hold')
        self.declare_parameter('hold_seconds', 8.0)
        self.declare_parameter('reset_pose', True)
        self.declare_parameter('spawn_z', 0.35)
        self.hold_seconds = float(self.get_parameter('hold_seconds').value)
        self.reset_pose = bool(self.get_parameter('reset_pose').value)
        self.spawn_z = float(self.get_parameter('spawn_z').value)

        self.publisher = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            10,
        )
        self.start_time = None
        self.did_reset = False
        self.done = False
        self.timer = self.create_timer(0.05, self.tick)
        self.get_logger().info('Standing pose hold started')

    def publish_stand(self):
        msg = JointTrajectory()
        msg.header.stamp.sec = 0
        msg.header.stamp.nanosec = 0
        msg.joint_names = list(JOINTS)
        point = JointTrajectoryPoint()
        point.positions = list(STAND)
        point.velocities = [0.0] * len(STAND)
        point.time_from_start = Duration(sec=0, nanosec=200_000_000)
        msg.points = [point]
        self.publisher.publish(msg)

    def reset_upright(self):
        req = (
            'name: "go2", '
            f'position: {{x: 0.0, y: 0.0, z: {self.spawn_z}}}, '
            'orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}'
        )
        try:
            subprocess.run(
                [
                    'gz', 'service',
                    '-s', '/world/my_world/set_pose',
                    '--reqtype', 'gz.msgs.Pose',
                    '--reptype', 'gz.msgs.Boolean',
                    '--timeout', '2000',
                    '--req', req,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.get_logger().info('Reset Go2 pose upright')
        except Exception as exc:
            self.get_logger().warn(f'Pose reset failed: {exc}')

    def tick(self):
        now = self.get_clock().now()
        if now.nanoseconds == 0:
            return
        if self.start_time is None:
            self.start_time = now

        self.publish_stand()
        elapsed = (now - self.start_time).nanoseconds * 1e-9

        # After joints have tracked stand for a bit, flip upright once
        if self.reset_pose and not self.did_reset and elapsed >= 1.5:
            self.reset_upright()
            self.did_reset = True

        if elapsed >= self.hold_seconds and not self.done:
            self.get_logger().info('Standing pose hold finished — ready for teleop')
            self.done = True
            self.timer.cancel()


def main():
    rclpy.init()
    node = StandPoseHold()
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
