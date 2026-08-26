#!/usr/bin/env bash
# Source this in every terminal that uses ros2 CLI with go2_description.
# Launch files already set these; bare terminals do not.
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
export ROS_AUTOMATIC_DISCOVERY_RANGE="${ROS_AUTOMATIC_DISCOVERY_RANGE:-LOCALHOST}"
export ROS_LOCALHOST_ONLY="${ROS_LOCALHOST_ONLY:-1}"
echo "go2 env: ROS_DOMAIN_ID=${ROS_DOMAIN_ID} LOCALHOST_ONLY=${ROS_LOCALHOST_ONLY}"
