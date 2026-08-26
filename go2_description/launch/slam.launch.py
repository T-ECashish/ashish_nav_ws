from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = FindPackageShare('go2_description')
    default_params_file_path = PathJoinSubstitution(
        [pkg_share, 'config', 'slam.yaml']
    )
    slam_launch_path = PathJoinSubstitution(
        [FindPackageShare('slam_toolbox'), 'launch', 'online_async_launch.py']
    )
    rviz_config_path = PathJoinSubstitution(
        [pkg_share, 'launch', '2D.rviz']
    )

    return LaunchDescription([
        SetEnvironmentVariable(name='ROS_DOMAIN_ID', value='42'),
        SetEnvironmentVariable(name='ROS_AUTOMATIC_DISCOVERY_RANGE', value='LOCALHOST'),
        SetEnvironmentVariable(name='ROS_LOCALHOST_ONLY', value='1'),
        DeclareLaunchArgument(
            name='slam_params_file',
            default_value=default_params_file_path,
            description='slam_toolbox parameter file'
        ),
        DeclareLaunchArgument(
            name='sim',
            default_value='true',
            description='Enable use_sim_time'
        ),
        DeclareLaunchArgument(
            name='rviz',
            default_value='true',
            description='Launch RViz with the SLAM configuration'
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch_path),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('sim'),
                'slam_params_file': LaunchConfiguration('slam_params_file'),
            }.items()
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config_path],
            condition=IfCondition(LaunchConfiguration('rviz')),
            parameters=[{'use_sim_time': LaunchConfiguration('sim')}],
        ),
    ])
