import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('go2_description')
    
    # Path to our custom nav2 params
    default_params_file = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    
    # Path to nav2_bringup navigation launch
    nav2_bringup_share = get_package_share_directory('nav2_bringup')
    nav2_navigation_launch = os.path.join(nav2_bringup_share, 'launch', 'navigation_launch.py')

    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        # Force isolated domain environment variables
        SetEnvironmentVariable(name='ROS_DOMAIN_ID', value='42'),
        SetEnvironmentVariable(name='ROS_AUTOMATIC_DISCOVERY_RANGE', value='LOCALHOST'),
        SetEnvironmentVariable(name='ROS_LOCALHOST_ONLY', value='1'),

        DeclareLaunchArgument(
            'params_file',
            default_value=default_params_file,
            description='Full path to the ROS2 parameters file to use for all launched nodes'
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_navigation_launch),
            launch_arguments={
                'params_file': params_file,
                'use_sim_time': use_sim_time,
                'use_lifecycle_mgr': 'true',
                'autostart': 'true'
            }.items()
        )
    ])
