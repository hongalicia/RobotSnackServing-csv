import socket
import time
# import re
import threading
from queue import LifoQueue

sock=0

# L_queue = LifoQueue()
# R_queue = LifoQueue()
ros_queue = LifoQueue()

def socket_init():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 5005))  # 監聽來自 port 5005
    # print("等待資料中...")

def start_svr_read_thread():
    def read_loop():
        global sock
        while True:
            data, addr = sock.recvfrom(1024)  # 收最多 1024 bytes
            # print("len(data)=", len(data), "raw=", repr(data))
            values = list(map(float, data.decode().split(",")))
            # print("收到:", values)
            ros_queue.put(values)
            time.sleep(0.01)
    t = threading.Thread(target=read_loop, daemon=True)
    t.start()

if __name__ == '__main__':
    # 測試資料
    socket_init()
    start_svr_read_thread()
    # 保持主線程運行，讓背景執行緒可以持續執行
    while True:
        pass
    