import socket
import struct
import time
import re
import threading
from queue import LifoQueue

event = threading.Event()

s=0
left=0
right=0

L_queue = LifoQueue()
R_queue = LifoQueue()

HOST_L = '192.168.1.10'   # 第一台設備 IP
HOST_R = '192.168.1.100'   # 第二台設備 IP
PORT = 5891              # 假設使用相同 Port

def socket_init():
    global left
    global right

    try:
        left = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        left.settimeout(3.0)
        left.connect((HOST_L, PORT))
        print(f"連線到{HOST_L}成功！")
    except socket.timeout:
        print(f"連線到{HOST_L}逾時，無法讀取設備資料。")
    except Exception as e:
        print(f"{HOST_L}讀取錯誤: {e}")

    # try:
    #     right = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     right.settimeout(3.0)
    #     right.connect((HOST_R, PORT))
    #     print(f"連線到{HOST_R}成功！")
    # except socket.timeout:
    #     print(f"連線到{HOST_R}逾時，無法讀取設備資料。")
    # except Exception as e:
    #     print(f"{HOST_R}讀取錯誤: {e}")

def clear_L_queue():
    global L_queue
    L_queue=LifoQueue()

def clear_R_queue():
    global R_queue
    R_queue=LifoQueue()

def start_svr_read_thread():
    def read_loop():
        global left
        while True:
            left = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            left.settimeout(3.0)
            left.connect((HOST_L, PORT))
            # socket_init()
            joint_angle_L=svr_read_L()
            # joint_angle_R=svr_read_R()
            L_queue.put(joint_angle_L)
            # R_queue.put(joint_angle_R)
            time.sleep(0.01)
    t = threading.Thread(target=read_loop, daemon=True)
    t.start()

def svr_confirm(socket):
    # 假設回傳的資料是：資料長度 (4 bytes) + 資料內容
    length_data = socket.recv(16)
    # print(f"Length data received: {length_data}")
    if length_data:
        return length_data
    else:
        print("接收到空的 length_data")
        return False

def svr_read_L():
    global left
    # request = f'svr_read("{item_name}")'
    # print(f"請求資料:{request}")
    # s.sendall(request.encode())
    # 假設回傳的資料是：資料長度 (4 bytes) + 資料內容
    # length_data = left.recv(952) # 資料長度為 952 bytes
    length_data = left.recv(74) # 資料長度為 94 bytes
    # print(f"Length data received: {length_data}")
    # joint_values = extract_arm_data(length_data)
    joint_values = extract_joint_values(length_data)
    # print(f"Joint_Angle_L = {joint_values}")
    return joint_values
    # return data

def svr_read_R():
    global right
    # request = f'svr_read("{item_name}")'
    # print(f"請求資料:{request}")
    # s.sendall(request.encode())
    # 假設回傳的資料是：資料長度 (4 bytes) + 資料內容
    length_data = right.recv(952) # 資料長度為 952 bytes
    print(f"Length data received: {length_data}")
    # joint_values = extract_arm_data(length_data)
    # print(f"Joint_Angle_R = {joint_values}")
    # return joint_values
    # return data

def extract_arm_data(data: bytes):
    # Joint_Angle float 資料從 offset + len('Joint_Angle') + 2 開始
    # float_start = 82 + len('Joint_Angle') + 2  # 82 + 11 + 2 = 95
    float_start = 31 + len('Joint_Angle') + 2  # 31 + 11 + 2 = 44
    float_end = float_start + 24  # 95 + 24 = 119

    float_bytes = data[float_start:float_end]
    try:
        joint_values = struct.unpack('<6f', float_bytes)  # little-endian 6個 float    

        do0 = data[70 + len('End_DO0') + 2]  # label 後第3個byte才是值
        do1 = data[82 + len('End_DO1') + 2]  # label 後第3個byte才是值
        do2 = data[94 + len('End_DO2') + 2]  # label 後第3個byte才是值

        return [round(val, 2) for val in joint_values]+[do0, do1, do2]
    except Exception as e:
        print(e)
        print("data length:", len(data))

def extract_joint_values(data: bytes):
    # 找到 'Joint_Angle' 在資料中的位置
    key = b'Joint_Angle'
    idx = data.find(key)
    if idx == -1:
        raise ValueError("Joint_Angle not found")

    # Joint_Angle 後面就是角度資料，假設每個角度 4 bytes，總共有 6 個角度
    start = idx + len(key)
    # 先忽略中間可能的 2 bytes header (例如 \x18\x00)
    start += 2
    angles_bytes = data[start:start + 6*4]  # 6 個 float，每個 4 bytes

    # 解析為浮點數，假設小端序
    angles = [round(a, 2) for a in struct.unpack('<6f', angles_bytes)]
    return angles

if __name__ == '__main__':
    # 測試資料
    socket_init()
    start_svr_read_thread()
    # 保持主線程運行，讓背景執行緒可以持續執行
    while True:
        pass
    # print(svr_read('Robot_Link'))
    # while True:
    #     svr_read()
    #     time.sleep(0.01)
        # pass
        # 📦 測試用法
        # print(svr_read('Robot_Link'))
        # print(svr_read("Robot_Link"))
        # print(svr_read("Ctrl_DO0"))






