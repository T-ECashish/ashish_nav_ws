"""Localization bringup: load saved map + AMCL (auto-activates lifecycle nodes).

Use with the Go2 simulation already running:
  Terminal 1:  ros2 launch go2_description simulation.launch.py
  Terminal 2:  ros2 launch go2_description localization.launch.py

Default map file:
  share/go2_description/maps/go2_map.yaml  (+ go2_map.pgm beside it)
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('go2_description')
    default_map = os.path.join(pkg_share, 'maps', 'go2_map.yaml')
    default_params = os.path.join(pkg_share, 'config', 'localization.yaml')

    map_yaml = LaunchConfiguration('map')
    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file = LaunchConfiguration('params_file')
    autostart = LaunchConfiguration('autostart')

    return LaunchDescription([
        # Same isolation as simulation / slam launches
        SetEnvironmentVariable(name='ROS_DOMAIN_ID', value='42'),
        SetEnvironmentVariable(name='ROS_AUTOMATIC_DISCOVERY_RANGE', value='LOCALHOST'),
        SetEnvironmentVariable(name='ROS_LOCALHOST_ONLY', value='1'),

        DeclareLaunchArgument(
            'map',
            default_value=default_map,
            description='Full path to the saved map YAML (image path is relative to this file)',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use /clock from Gazebo',
        ),
        DeclareLaunchArgument(
            'params_file',
            default_value=default_params,
            description='AMCL / map_server / lifecycle_manager parameters',
        ),
        DeclareLaunchArgument(
            'autostart',
            default_value='true',
            description='Lifecycle manager auto configure+activate map_server and amcl',
        ),

        # Publishes /map from the saved occupancy grid
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[
                params_file,
                {
                    'use_sim_time': use_sim_time,
                    'yaml_filename': map_yaml,
                },
            ],
        ),

        # Estimates map→odom from laser + odom (particle filter)
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[
                params_file,
                {'use_sim_time': use_sim_time},
            ],
        ),

        # RViz's Map display (TF message filter) drops the once-published map
        # if its stamp has no map->odom data or ages out of the TF cache.
        # Keep republishing it with a fresh stamp so RViz always renders it.
        Node(
            package='go2_description',
            executable='map_refresher.py',
            name='map_refresher',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
        ),

        # Replaces manual: ros2 lifecycle set /map_server configure|activate
        # and the same for /amcl.
        # Delayed so map_server/amcl receive /clock BEFORE activation:
        # otherwise the (published-once) /map is stamped sim time 0.000 and
        # RViz's TF message filter drops it forever -> empty Map display.
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='nav2_lifecycle_manager',
                    executable='lifecycle_manager',
                    name='lifecycle_manager_localization',
                    output='screen',
                    parameters=[
                        {
                            'use_sim_time': use_sim_time,
                            'autostart': autostart,
                            'node_names': ['map_server', 'amcl'],
                        },
                    ],
                ),
            ],
        ),
    ])
