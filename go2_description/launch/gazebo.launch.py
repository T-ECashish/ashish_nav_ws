import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node

SIM_TIME = [{'use_sim_time': True}]


def generate_launch_description():
    pkg_share = get_package_share_directory('go2_description')
    default_model_path = os.path.join(pkg_share, 'xacro/robot.xacro')

    ros_gz_sim = get_package_share_directory('ros_gz_sim')
    world_path = os.path.join(pkg_share, 'worlds', '2d.sdf')
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': ['-r ', world_path]}.items(),
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': Command(['xacro ', LaunchConfiguration('model')]),
            'use_sim_time': True,
            # Use /clock instead of joint_state stamps — stops TF_OLD_DATA / jump-backs
            'ignore_timestamp': True,
        }],
    )

    robot_description_publisher_node = Node(
        package='go2_description',
        executable='robot_description_publisher.py',
        name='robot_description_publisher',
        output='screen',
        parameters=SIM_TIME,
    )

    # Spawn upright, high enough so standing-pose feet clear the floor
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'go2',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.45',
            '-R', '0.0',
            '-P', '0.0',
            '-Y', '0.0',
        ],
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/trunk_imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/scan_gz@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/model/go2/pose@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
        ],
        remappings=[('/model/go2/pose', '/gz_model_pose')],
        output='screen',
        parameters=SIM_TIME,
    )

    scan_frame_fixer_node = Node(
        package='go2_description',
        executable='scan_frame_fixer.py',
        name='scan_frame_fixer',
        output='screen',
        parameters=SIM_TIME,
    )

    go2_static_tf_node = Node(
        package='go2_description',
        executable='go2_static_tf_broadcaster.py',
        name='go2_static_tf_broadcaster',
        output='screen',
        parameters=SIM_TIME,
    )

    gz_odom_publisher_node = Node(
        package='go2_description',
        executable='gz_odom_publisher.py',
        name='gz_odom_publisher',
        output='screen',
        parameters=SIM_TIME,
    )

    odom_tf_broadcaster_node = Node(
        package='go2_description',
        executable='odom_tf_broadcaster.py',
        name='odom_tf_broadcaster',
        parameters=SIM_TIME,
        output='screen',
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60',
        ],
    )

    joint_trajectory_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_trajectory_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60',
        ],
    )

    stand_pose_hold_node = Node(
        package='go2_description',
        executable='stand_pose_hold.py',
        name='stand_pose_hold',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'hold_seconds': 8.0},
            {'reset_pose': True},
            {'spawn_z': 0.35},
        ],
    )

    joints_config = os.path.join(pkg_share, 'config/champ_joints.yaml')
    gait_config = os.path.join(pkg_share, 'config/champ_gait.yaml')
    links_config = os.path.join(pkg_share, 'config/champ_links.yaml')

    # Start champ AFTER standing pose settles, so it does not tip the robot
    quadruped_controller_node = Node(
        package='champ_base',
        executable='quadruped_controller_node',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'gazebo': True},
            {'publish_joint_states': False},
            {'publish_joint_control': True},
            {'publish_foot_contacts': False},
            {'joint_controller_topic': 'joint_trajectory_controller/joint_trajectory'},
            {'urdf': Command(['xacro ', LaunchConfiguration('model')])},
            joints_config,
            links_config,
            gait_config,
        ],
        remappings=[('/cmd_vel/smooth', '/cmd_vel_nav')],
    )

    delay_controllers = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[
                joint_state_broadcaster_spawner,
                joint_trajectory_controller_spawner,
            ],
        ),
    )

    # Hold standing pose as soon as trajectory controller is up
    start_stand_after_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_trajectory_controller_spawner,
            on_exit=[stand_pose_hold_node],
        ),
    )

    # Champ teleop after stand + upright reset
    delayed_champ = TimerAction(period=12.0, actions=[quadruped_controller_node])

    return LaunchDescription([
        # Isolate from other ROS 2 machines on the LAN (ghost TF / joint_states)
        SetEnvironmentVariable(name='ROS_DOMAIN_ID', value='42'),
        SetEnvironmentVariable(name='ROS_AUTOMATIC_DISCOVERY_RANGE', value='LOCALHOST'),
        SetEnvironmentVariable(name='ROS_LOCALHOST_ONLY', value='1'),
        DeclareLaunchArgument(
            name='model',
            default_value=default_model_path,
            description='Absolute path to robot urdf file',
        ),
        robot_state_publisher_node,
        robot_description_publisher_node,
        gz_sim,
        spawn_entity,
        bridge,
        scan_frame_fixer_node,
        go2_static_tf_node,
        gz_odom_publisher_node,
        odom_tf_broadcaster_node,
        delay_controllers,
        start_stand_after_controller,
        delayed_champ,
    ])
