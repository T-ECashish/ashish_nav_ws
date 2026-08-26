import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('go2_description')

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'gazebo.launch.py')
        )
    )

    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'rviz.launch.py')
        )
    )

    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'localization.launch.py')
        ),
        launch_arguments={'params_file': os.path.join(pkg_share, 'config', 'localization.yaml')}.items()
    )

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={'params_file': os.path.join(pkg_share, 'config', 'nav2_params.yaml')}.items()
    )

    teleop_node = Node(
        package='go2_description',
        executable='key_teleop.py',
        name='key_teleop',
        prefix='gnome-terminal --',
        output='screen',
        remappings=[('/cmd_vel', '/cmd_vel_nav')]
    )

    # Start RViz after /clock + TF settle so RobotModel is not stuck yellow
    delayed_rviz = TimerAction(period=8.0, actions=[rviz_launch])

    return LaunchDescription([
        SetEnvironmentVariable(name='ROS_DOMAIN_ID', value='42'),
        SetEnvironmentVariable(name='ROS_AUTOMATIC_DISCOVERY_RANGE', value='LOCALHOST'),
        SetEnvironmentVariable(name='ROS_LOCALHOST_ONLY', value='1'),
        gazebo_launch,
        localization_launch,
        navigation_launch,
        delayed_rviz,
        teleop_node
    ])
