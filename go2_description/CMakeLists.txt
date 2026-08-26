cmake_minimum_required(VERSION 3.8)

project(go2_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(urdf REQUIRED)

install(PROGRAMS
  scripts/key_teleop.py
  scripts/odom_tf_broadcaster.py
  scripts/gimbal_joint_publisher.py
  scripts/scan_frame_fixer.py
  scripts/go2_static_tf_broadcaster.py
  scripts/gz_odom_publisher.py
  scripts/robot_description_publisher.py
  scripts/stand_pose_hold.py
  scripts/map_refresher.py
  scripts/kill_simulation.sh
  scripts/go2_env.sh
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY config dae launch maps meshes urdf xacro worlds
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
