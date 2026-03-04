#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import socket

DEFAULT_TOPIC = '/NS_1/joint_states'  # 直接指定預設 topic

class JointLogger(Node):
    def __init__(self, topic: str):
        super().__init__('joint_logger')
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,  # 如需更鬆可改 BEST_EFFORT
            history=HistoryPolicy.KEEP_LAST,
            depth=50,
        )
        self.create_subscription(JointState, topic, self.cb, qos)
        self.get_logger().info(f"Subscribed to: {topic}")

        # UDP socket
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_addr = ("127.0.0.1", 5005)  # 發送到本機 port 5005

    def cb(self, msg: JointState):
        # 確保有 position 資料
        if msg.name and msg.position:
            # 將時間戳記合併成浮點數，不限制小數點位數
            timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

            # 將時間 + positions 組成陣列
            output = [timestamp, *msg.position]
            # 直接輸出完整的陣列
            # joint_positions = list(msg.position[:7])
            # 四捨五入到小數點第 2 位
            joint_positions = [round(pos, 2) for pos in msg.position[:7]]
            # self.get_logger().info(str(joint_positions))
            data_str = ','.join(map(str, joint_positions))
            # 發送 UDP
            self.udp_sock.sendto(data_str.encode(), self.udp_addr)
        else:
            self.get_logger().info("Received JointState w/o names/positions")

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--topic', default=DEFAULT_TOPIC)
    args, ros_args = parser.parse_known_args()   # 保留對 --ros-args 的相容
    rclpy.init(args=ros_args)

    node = JointLogger(args.topic)
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
