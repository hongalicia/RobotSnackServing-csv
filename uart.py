import serial
import threading
import time
from queue import LifoQueue

uart_queue = LifoQueue()

class UART:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.valid = False  # 標記是否成功連線
        self.running = False

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self.valid = True
            self.running = True

            # 啟動接收執行緒
            self.thread = threading.Thread(target=self.read_uart, daemon=True)
            self.thread.start()
            print(f"[UARTThread] 已連線到 {self.port} (baud={self.baudrate})")

        except serial.SerialException as e:
            print(f"[UARTThread] 無法連線到 {self.port}: {e}")
            self.ser = None

    def read_uart(self):
        if not self.valid:
            return
        """背景執行緒：接收 UART 資料"""
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    raw = self.ser.read(1)  # 讀取 1 個位元組
                    values = raw.decode('utf-8', errors='ignore')
                    uart_queue.put(values)
                    # print(f"[UARTThread] 接收到資料: {values}")
                time.sleep(0.05)
            except Exception as e:
                print(f"[UART] 讀取錯誤: {e}")
                self.running = False
                break

    def send_str(self, name, text):  # send to Display
        """
        發送顯示文字指令到USART螢幕。
        :param name: 要顯示文字的元件名稱（如 "t0"）
        :param text: 要顯示的文字內容（如 "hello"）
        """
        if not self.valid:
            print("[UART] 裝置無效，無法傳送資料")
            return
        try:
            cmd_str = f'{name}.txt="{text}"'
            cmd_bytes = cmd_str.encode('utf-8') + bytes([0xFF, 0xFF, 0xFF])
            # .print(f"send cmd: {cmd_bytes}", flush=True)  # 顯示發送的指令
            self.ser.write(cmd_bytes)
        except Exception as e:
            print(f"[UART] 傳送錯誤: {e}")

    def send_num(self, name, num):  # send to Display
        """
        發送數字指令到USART螢幕。
        :param name: 要顯示數字的元件名稱（如 "n0"）
        :param num: 要顯示的數字內容（如 5）
        """
        if not self.valid:
            print("[UART] 裝置無效，無法傳送資料")
            return
        try:
            cmd_num = f'{name}.val={num}'
            cmd_bytes = cmd_num.encode('utf-8') + bytes([0xFF, 0xFF, 0xFF])
            # .print(f"send cmd: {cmd_bytes}", flush=True)  # 顯示發送的指令
            self.ser.write(cmd_bytes)
        except Exception as e:
            print(f"[UART] 傳送錯誤: {e}")
    
    def send_clicked(self, name, on_off):  # send to Display
        """
        控制USART螢幕的btn clicked，
        格式: click b0,1 or 0
        """
        if not self.valid:
            print("[UART] 裝置無效，無法傳送資料")
            return
        try:
            click_str = f'click {name},{on_off}'
            cmd_bytes = click_str.encode('utf-8') + bytes([0xFF, 0xFF, 0xFF])
            # print(f"send cmd: {cmd_bytes}", flush=True)  # 顯示發送的指令
            self.ser.write(cmd_bytes)
        except Exception as e:
            print(f"[UART] 傳送錯誤: {e}")

    # def send_page(self, page):  # send to Display
    #     """
    #     控制USART螢幕的btn，使其切換頁面
    #     格式: page 0 or page main
    #     """
    #     page_str = f'page {page}'
    #     cmd_bytes = page_str.encode('utf-8') + bytes([0xFF, 0xFF, 0xFF])
    #     # print(f"send cmd: {cmd_bytes}", flush=True)  # 顯示發送的指令
    #     self.ser.write(cmd_bytes)

    def close(self):
        """關閉 UART"""
        self.running = False
        self.ser.close()
        print("[UARTThread] 已關閉 UART")

# 範例使用
if __name__ == "__main__":
    uart = UART("/dev/ttyUSB0", 115200)
    uart.send_num("n0", 123)
    uart.send_clicked("b1", 1)
    uart.send_clicked("b1", 0)
    while True:
        pass

