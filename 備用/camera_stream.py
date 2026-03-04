import cv2
import threading
import time

class CameraStream:
    # def cam_names():
    #     return ['head', 'left', 'right', 'side']

    def __init__(self, index, width=640, height=480, fps=30, name=""):
        self.name = name or f"cam{index}"
        # 建議指定 V4L2，並把 buffer 降到 1，避免堆積延遲
        self.cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        # 有些平台支援：把 capture buffer 設 1，永遠拿最新
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self.cap.isOpened():
            raise RuntimeError(f"[{self.name}] cannot open camera {index}")

        self.lock = threading.Lock()
        self.running = True
        self.ret = False
        self.frame = None
        self.seq = 0  # 每拿到一張新影像就 +1

        self.t = threading.Thread(target=self._reader, daemon=True)
        self.t.start()

    def _reader(self):
        # 背景執行緒：不斷 read 最新影像
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                # 避免忙迴圈；短暫睡一下再試
                time.sleep(0.005)
                continue
            with self.lock:
                self.ret = True
                self.frame = frame
                self.seq += 1  # 告訴外界「有新 frame 了」

    def snapshot(self):
        # 取一份快照（回傳 ret, frame, seq）
        with self.lock:
            return self.ret, (None if self.frame is None else self.frame.copy()), self.seq

    def release(self):
        self.running = False
        self.t.join(timeout=1.0)
        self.cap.release()

# ==== 你的主程式 ====
def main():
    # 依你的需求映射名字
    cam_indices = [0, 2, 4, 6]
    cam_names   = ["head", "left", "right", "side"]

    # 初始化相機與對應的 VideoWriter（示範，每支相機一個檔）
    cams = []
    writers = []
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # 若你要 H.264，見下方補充
    for idx, name in zip(cam_indices, cam_names):
        cam = CameraStream(idx, 640, 480, 30, name=name)
        cams.append(cam)
        writers.append(cv2.VideoWriter(
            f"{name}.mp4", fourcc, 30, (640, 480)
        ))

    last_seq = [ -1 ] * len(cams)

    try:
        while True:
            any_updated = False
            for i, (cam, writer) in enumerate(zip(cams, writers)):
                ret, frame, seq = cam.snapshot()
                if not ret or frame is None:
                    continue

                # 只有在 seq 變化（=有新 frame）時才處理
                if seq == last_seq[i]:
                    continue
                last_seq[i] = seq
                any_updated = True

                # 你的旋轉規則
                if cam.name in ("left", "right"):
                    frame = cv2.rotate(frame, cv2.ROTATE_180)

                writer.write(frame)
                cv2.imshow(f"Camera_{cam.name}", frame)

            # 若這一輪完全沒有新 frame，就小睡一下，避免空轉
            if not any_updated:
                time.sleep(0.002)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        for w in writers: w.release()
        for c in cams: c.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
