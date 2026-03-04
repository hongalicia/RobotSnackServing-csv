import socket
import struct
import time
import re
import threading
# from queue import Queue
from queue import LifoQueue

s=0
left=0
right=0

# L_queue = Queue()
# R_queue = Queue()

L_queue = LifoQueue()
R_queue = LifoQueue()

def socket_init():
    global left
    global right
    HOST_L = '192.168.1.100'   # 第一台設備 IP
    HOST_R = '192.168.1.10'   # 第二台設備 IP
    PORT = 5891              # 假設使用相同 Port

    try:
        left = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        left.settimeout(3.0)
        left.connect((HOST_L, PORT))
        print(f"連線到{HOST_L}成功！")
    except socket.timeout:
        print(f"連線到{HOST_L}逾時，無法讀取設備資料。")
    except Exception as e:
        print(f"{HOST_L}讀取錯誤: {e}")

    try:
        right = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        right.settimeout(3.0)
        right.connect((HOST_R, PORT))
        print(f"連線到{HOST_R}成功！")
    except socket.timeout:
        print(f"連線到{HOST_R}逾時，無法讀取設備資料。")
    except Exception as e:
        print(f"{HOST_R}讀取錯誤: {e}")

def start_svr_read_thread():
    def read_loop():
        while True:
            joint_angle_L=svr_read_L()
            joint_angle_R=svr_read_R()
            L_queue.put(joint_angle_L)
            R_queue.put(joint_angle_R)
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
    length_data = left.recv(4)
    # print(f"Length data received: {length_data}")
    data_len = struct.unpack('I', length_data)[0]
    # print(f"data_len received: {data_len}")
    data = left.recv(data_len)
    # print(f"data: {data}")
    # return data.decode().split('\0')[:-1]
    # joint_values = extract_joint_angle(length_data.decode())
    joint_values = extract_tm_values(data.decode())
    # print(f"Joint_Angle_L = {joint_values}")
    return joint_values
    # return data

def svr_read_R():
    global right
    # request = f'svr_read("{item_name}")'
    # print(f"請求資料:{request}")
    # s.sendall(request.encode())
    # 假設回傳的資料是：資料長度 (4 bytes) + 資料內容
    length_data = right.recv(4)
    # print(f"Length data received: {length_data}")
    data_len = struct.unpack('I', length_data)[0]
    data = right.recv(data_len)
    # return data.decode().split('\0')[:-1]
    # joint_values = extract_joint_angle(length_data.decode())
    joint_values = extract_tm_values(data.decode())
    # print(f"Joint_Angle_R = {joint_values}")
    return joint_values
    # return data

def extract_joint_angle(data: str):
    # 使用正規表達式擷取 Joint_Angle 中的數值
    match = re.search(r'Joint_Angle=\{([^}]+)\}', data)
    if match:
        values_str = match.group(1)  # 拿到 {-14.249852,...} 中間的部分
        # values = [float(x) for x in values_str.split(',')]
        values = [round(float(x), 2) for x in values_str.split(',')]
        return values
    else:
        print("找不到 Joint_Angle 資料")
        return None

def extract_tm_values(data: str):
    """
    從 TM robot 的純文字資料中同時擷取:
      - Joint_Angle (6個float)
      - End_DO0, End_DO1, End_DO2 (各一個int)
    回傳格式: (angles, do0, do1, do2)
    """
    # 使用一個正規表達式，一次抓到所有想要的東西
    pattern = (
        r'Joint_Angle=\{([^}]+)\}'         # 1) Joint_Angle {...} 內的值
        r'.*?End_DO0=(\d+)'                # 2) End_DO0=數字
        r'.*?End_DO1=(\d+)'                # 3) End_DO1=數字
        r'.*?End_DO2=(\d+)'                # 4) End_DO2=數字
    )

    match = re.search(pattern, data, re.DOTALL)  # DOTALL讓 '.' 可以跨行
    if match:
        # ---- 解析 Joint_Angle ----
        values_str = match.group(1)
        # angles = [round(float(x.strip()), 2) for x in values_str.split(',')]
        joint_angles = [round(float(x), 2) for x in values_str.split(',')]

        # ---- 解析 DO 值 ----
        do0 = int(match.group(2))
        do1 = int(match.group(3))
        do2 = int(match.group(4))

        return *joint_angles, do0, do1, do2
    else:
        print("找不到完整的 Joint_Angle 或 End_DO 資料")
        return None, None, None, None


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






