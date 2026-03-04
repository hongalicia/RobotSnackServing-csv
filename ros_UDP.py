import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import JointState
from tm_msgs.msg import FeedbackState
import math
import time
import socket
import sys

arm_num = int(sys.argv[1])

class SingleRobotStateCollector(Node):
    """
    單機械手臂資料收集器:
    - 訂閱 /joint_states 與 /feedback_states
    - 每次輸出 [j1..j6(度), io0, io1, io2]
    - 利用 UDP 發送給其他程式
    """

    def __init__(self, fps: int = 30):
        super().__init__('single_robot_state_collector')

        # FPS 控制
        self.interval = 1.0 / max(1, fps)
        self.last_emit = 0.0

        # 緩存
        self.joints_deg = None
        self.io = [0, 0, 0]

        # UDP socket
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_addr = ("127.0.0.1", 5005)  # 發送到本機 port 5005

        # QoS
        qos_sensor = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # 訂閱 joint_states
        self.create_subscription(JointState, '/joint_states', self._on_joint, qos_sensor)
        # self.get_logger().info('訂閱: /joint_states')

        # 訂閱 feedback_states
        self.create_subscription(FeedbackState, '/feedback_states', self._on_fb, 10)
        # self.get_logger().info('訂閱: /feedback_states')

        self.get_logger().info("✅ UDP 連線成功，等待資料中...")


    def _on_joint(self, msg: JointState):
        """接收關節角度並轉換成度數"""
        if not msg.position or len(msg.position) < 6:
            return

        j6 = msg.position[:6]
        joints_deg = [round(math.degrees(j), 2) for j in j6]

        if all(j == 0.0 for j in joints_deg):
            return
        
        if self.joints_deg is None:
            self.get_logger().info("✅ ROS啟用完成,可開始抓取關節值...")

        self.joints_deg = joints_deg
        self._try_emit()

    def _on_fb(self, msg: FeedbackState):
        """接收 IO 狀態（Robotiq DO2 → idle 過濾版）"""

        ee = list(msg.ee_digital_output) if msg.ee_digital_output is not None else []
        cb = list(msg.cb_digital_output) if msg.cb_digital_output is not None else []
        src = ee if len(ee) > 0 else cb

        do0 = int(src[0]) if len(src) > 0 else 0
        do1 = int(src[1]) if len(src) > 1 else 0   # close
        do2 = int(src[2]) if len(src) > 2 else 0   # open

        # 👇 Robotiq open 會讓 DO2 = 1，但我們要當作 idle
        if do2 == 1:
            do2 = 0

        self.io = [
            1 if do0 else 0,
            1 if do1 else 0,
            1 if do2 else 0
        ]

        self._try_emit()



    def _try_emit(self):
        """當 joint 與 IO 都有資料，且符合 fps 間隔時發送"""
        now = time.time()
        if self.joints_deg is None:
            return
        if now - self.last_emit < self.interval:
            return

        combined = self.joints_deg + self.io
        # print(self.joints_deg)  # 例如: [j1..j6(度), io0, io1, io2]
        data_str = ",".join(map(str, combined))

        # 發送 UDP
        self.udp_sock.sendto(data_str.encode(), self.udp_addr)
        # self.get_logger().info(f"UDP 發送: {data_str}")

        self.last_emit = now

class DualRobotStateCollector(Node):
    def __init__(self, ns1='robot1', ns2='robot2', fps: int = 30):
        super().__init__('dual_robot_state_collector')

        # 設定 interval = 1/fps
        self.interval = 1.0 / fps
        self.last_emit = 0.0
        self.ns1, self.ns2 = ns1, ns2

        # 緩存
        self.joints_deg = None
        self.robot = {
            ns1: {'joints': None, 'io': [0,0,0], 'fresh': False},
            ns2: {'joints': None, 'io': [0,0,0], 'fresh': False},
        }

        # UDP socket
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_addr = ("127.0.0.1", 5005)  # 發送到本機 port 5005

        # QoS（感測資料）
        qos_sensor = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # topics
        js1, js2 = f'/{ns1}/joint_states', f'/{ns2}/joint_states'
        fb1, fb2 = f'/{ns1}/feedback_states', f'/{ns2}/feedback_states'

        # 訂閱
        self.create_subscription(JointState, js1, lambda m: self._on_joint(ns1, m), qos_sensor)
        self.create_subscription(JointState, js2, lambda m: self._on_joint(ns2, m), qos_sensor)
        self.create_subscription(FeedbackState, fb1, lambda m: self._on_fb(ns1, m), 10)
        self.create_subscription(FeedbackState, fb2, lambda m: self._on_fb(ns2, m), 10)

        self.get_logger().info("✅ UDP 連線成功，等待資料中...")

    def _poll_ctrl(self):
        self.ctrl_sock.setblocking(False)
        try:
            data, _ = self.ctrl_sock.recvfrom(1024)
        except BlockingIOError:
            return
        if data.decode().strip() == "__SHUTDOWN__":
            self.get_logger().info("收到 UI 關閉通知，準備關閉 ROS 節點")
            self.destroy_node()
            rclpy.shutdown()

    # ---- Callbacks ----
    def _on_joint(self, name: str, msg: JointState):
        joints_deg = [round(math.degrees(j), 2) for j in msg.position[:6]]
        if all(j == 0.0 for j in joints_deg):
            return
        
        if self.joints_deg is None:
            self.get_logger().info("✅ ROS啟用完成,可開始抓取關節值...")

        self.robot[name]['joints'] = joints_deg
        self.robot[name]['fresh']  = True
        self.joints_deg = joints_deg
        self._try_emit()

    def _on_fb(self, name: str, msg: FeedbackState):
        ee = list(msg.ee_digital_output) if msg.ee_digital_output is not None else []
        cb = list(msg.cb_digital_output) if msg.cb_digital_output is not None else []
        src = ee if len(ee) > 0 else cb

        a = int(src[0]) if len(src) > 0 else 0
        b = int(src[1]) if len(src) > 1 else 0
        c = int(src[2]) if len(src) > 2 else 0

        self.robot[name]['io'] = [1 if a else 0, 1 if b else 0, 1 if c else 0]

    def _try_emit(self):
        now = time.time()
        if not (self.robot[self.ns1]['fresh'] and self.robot[self.ns2]['fresh']):
            return
        if now - self.last_emit < self.interval:
            return

        r1 = self.robot[self.ns1]['joints']
        r2 = self.robot[self.ns2]['joints']
        if r1 is None or r2 is None:
            return

        g1 = self.robot[self.ns1]['io']
        g2 = self.robot[self.ns2]['io']
        # combined = r1 + g1 + r2 + g2
        combined = r2 + g2 + r1 + g1
        # print(combined)
        data_str = ",".join(map(str, combined))
        # 發送 UDP
        self.udp_sock.sendto(data_str.encode(), self.udp_addr)

        # reset
        self.robot[self.ns1]['fresh'] = False
        self.robot[self.ns2]['fresh'] = False
        self.last_emit = now
        return g1, g2

def joint_collect(args=None):
    rclpy.init(args=args)
    if arm_num == 2:
        node = DualRobotStateCollector(ns1='robot1', ns2='robot2', fps=30)  # 30 fps
    else:
        node = SingleRobotStateCollector(fps=30)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    joint_collect()
