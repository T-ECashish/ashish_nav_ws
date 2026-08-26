#!/usr/bin/python3
"""Republish the latched /map with a fresh timestamp every few seconds.

nav2 map_server publishes the map exactly once (transient local). In Jazzy,
RViz's Map display runs incoming maps through a TF message filter: if the
map's stamp predates the first map->odom transform from AMCL (which activates
AFTER map_server), or falls out of the 10 s TF cache, RViz silently drops it
and the display stays empty forever. Refreshing the stamp keeps a passable
message available no matter when RViz subscribes or what the fixed frame is.
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from nav_msgs.msg import OccupancyGrid


class MapRefresher(Node):
    def __init__(self):
        super().__init__('map_refresher')
        qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
        )
        self.map_msg = None
        # Subscription is created before we ever publish, so the first
        # (latched) message we receive is guaranteed to be map_server's.
        self.sub = self.create_subscription(OccupancyGrid, 'map', self.on_map, qos)
        self.pub = self.create_publisher(OccupancyGrid, 'map', qos)
        self.timer = self.create_timer(2.0, self.republish)
        self.get_logger().info('Waiting for map from map_server...')

    def on_map(self, msg):
        if self.map_msg is None:
            self.map_msg = msg
            self.get_logger().info(
                'Got %dx%d map; republishing with fresh stamps every 2 s'
                % (msg.info.width, msg.info.height))

    def republish(self):
        if self.map_msg is None:
            return
        now = self.get_clock().now()
        if now.nanoseconds == 0:
            return  # sim clock not received yet; a 0 stamp would be dropped
        self.map_msg.header.stamp = now.to_msg()
        self.pub.publish(self.map_msg)


def main():
    rclpy.init()
    node = MapRefresher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
