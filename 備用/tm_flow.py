import socket
import struct
import time


class TMflow:
    def tmflow_init(self):
        HOST_L = '192.168.1.100'  # 左臂IP
        HOST_R = '192.168.1.10'  # 右臂IP
        PORT = 5891

        try:
            self.left = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.left.settimeout(3.0)
            self.left.connect((HOST_L, PORT))
            print(f"連線到{HOST_L}成功！")
        except socket.timeout:
            print(f"連線到{HOST_L}逾時，無法讀取設備資料。")
        except Exception as e:
            print(f"{HOST_L}讀取錯誤: {e}")

        try:
            self.right = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.right.settimeout(3.0)
            self.right.connect((HOST_R, PORT))
            print(f"連線到{HOST_R}成功！")
        except socket.timeout:
            print(f"連線到{HOST_R}逾時，無法讀取設備資料。")
        except Exception as e:
            print(f"{HOST_R}讀取錯誤: {e}")

    def get_data(self):
        left_data = self.left.recv(952)  # 資料長度為 952 bytes
        if not left_data:
            print("❌ 左臂接收到空的資料")
            return None
        right_data = self.right.recv(952)  # 資料長度為 952 bytes
        if not right_data:
            print("❌ 右臂接收到空的資料")
            return None
        joint_left = self.extract_joint_angle(left_data)
        print(f"Joint_Angle_L = {joint_left}")
        joint_right = self.extract_joint_angle(right_data)
        print(f"Joint_Angle_R = {joint_right}")
        # joint_values = joint_left + joint_right
        end_do_left = self.extract_end_do(left_data)
        print(f"End_DO_L = {end_do_left}")
        end_do_right = self.extract_end_do(right_data)
        print(f"End_DO_R = {end_do_right}")
        return joint_left, end_do_left, joint_right, end_do_right

    def extract_joint_angle(self, data: bytes):
        # Joint_Angle float 資料從 offset + len('Joint_Angle') + 2 開始
        float_start = 82 + len('Joint_Angle') + 2  # 82 + 11 + 2 = 95
        float_end = float_start + 24  # 95 + 24 = 119

        float_bytes = data[float_start:float_end]
        joint_values = struct.unpack(
            '<6f', float_bytes)  # little-endian 6個 float

        return [round(val, 2) for val in joint_values]

    def extract_end_do(self, data: bytes):
        do0 = data[707 + len('End_DO0') + 2]  # label 後第3個byte才是值
        do1 = data[719 + len('End_DO1') + 2]  # label 後第3個byte才是值
        do2 = data[731 + len('End_DO2') + 2]  # label 後第3個byte才是值

        return [do0, do1, do2]

# ===== 使用範例 =====


def main():
    tm = TMflow()
    tm.tmflow_init()
    for i in range(10):
        joint_angle = tm.get_data()
        print(f"Joint Angles: {joint_angle}")
        print(f"time_elapsed: {time.time()}")


if __name__ == '__main__':
    main()
