#!/bin/bash
# Stop leftover simulation/SLAM processes before a clean run.
# Avoid matching this script's own command line.
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
export ROS_LOCALHOST_ONLY="${ROS_LOCALHOST_ONLY:-1}"

pkill -f 'ros2 launch go2_description simulation' 2>/dev/null || true
pkill -f 'ros2 launch go2_description gazebo' 2>/dev/null || true
pkill -f 'ros2 launch go2_description slam' 2>/dev/null || true
pkill -f 'slam_toolbox online_async' 2>/dev/null || true
pkill -f 'async_slam_toolbox_node' 2>/dev/null || true
pkill -f 'gz sim -r' 2>/dev/null || true
pkill -f 'ruby .*/gz sim' 2>/dev/null || true
pkill -f 'gz-sim-server' 2>/dev/null || true
pkill -f 'gz sim gui' 2>/dev/null || true
pkill -f 'gz sim server' 2>/dev/null || true
pkill -f '/lib/rviz2/rviz2' 2>/dev/null || true
pkill -f 'parameter_bridge' 2>/dev/null || true
pkill -f 'quadruped_controller_node' 2>/dev/null || true
pkill -f 'stand_pose_hold.py' 2>/dev/null || true
pkill -f 'gz_odom_publisher.py' 2>/dev/null || true
pkill -f 'odom_tf_broadcaster.py' 2>/dev/null || true
pkill -f 'scan_frame_fixer.py' 2>/dev/null || true
pkill -f 'go2_static_tf_broadcaster.py' 2>/dev/null || true
pkill -f 'robot_description_publisher.py' 2>/dev/null || true
pkill -f 'robot_state_publisher' 2>/dev/null || true
pkill -f 'key_teleop.py' 2>/dev/null || true
pkill -f 'controller_manager' 2>/dev/null || true
pkill -f 'spawner' 2>/dev/null || true
sleep 2
pkill -9 -f 'gz sim -r' 2>/dev/null || true
pkill -9 -f 'gz-sim-server' 2>/dev/null || true
pkill -9 -f '/lib/rviz2/rviz2' 2>/dev/null || true
pkill -9 -f 'parameter_bridge' 2>/dev/null || true
pkill -9 -f 'robot_state_publisher' 2>/dev/null || true
sleep 1
ros2 daemon stop 2>/dev/null || true
ros2 daemon start 2>/dev/null || true
sleep 1
echo "Simulation stopped (ROS_DOMAIN_ID=${ROS_DOMAIN_ID}, ROS_LOCALHOST_ONLY=${ROS_LOCALHOST_ONLY})."
echo "In EVERY new terminal run:"
echo "  source ~/slam/install/setup.bash"
echo "  source ~/slam/install/go2_description/lib/go2_description/go2_env.sh"
echo "Then: ros2 launch go2_description simulation.launch.py"
