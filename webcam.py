import cv2
import os
import file


def cam_names():
    return ['head', 'left', 'right', 'side', 'sider']

# def cam_init(task_index, episode_index, head, left, right, side, sider):


def cam_init(task_index, episode_index):
    # 攝影機初始化
    # cap_head = cv2.VideoCapture(0,cv2.CAP_DSHOW) # 0: 預設攝影機，1: 外接攝影機
    # cap_left = cv2.VideoCapture(2,cv2.CAP_DSHOW) # 0: 預設攝影機，1: 外接攝影機
    # cap_right = cv2.VideoCapture(4,cv2.CAP_DSHOW) # 0: 預設攝影機，1: 外接攝影機
    # cap_side = cv2.VideoCapture(3,cv2.CAP_DSHOW) # 0: 預設攝影機，1: 外接攝影機

    cap_head = cv2.VideoCapture(0)  # 0: 預設攝影機，1: 外接攝影機
    cap_left = cv2.VideoCapture(2)  # 0: 預設攝影機，1: 外接攝影機
    cap_right = cv2.VideoCapture(6)  # 0: 預設攝影機，1: 外接攝影機
    cap_side = cv2.VideoCapture(4)  # 0: 預設攝影機，1: 外接攝影機
    cap_sider = cv2.VideoCapture(10)  # 0: 預設攝影機，1: 外接攝影機

    # 設定解析度與 FPS
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
    # cap.set(cv2.CAP_PROP_FPS, 30)

    # 抓取解析度 & FPS，分別設定
    # cam_flags = [head, left, right, side, sider] # 是否啟用攝影機
    # all_caps = [cap_head, cap_left, cap_right, cap_side, cap_sider] # 所有攝影機
    # caps = [cap for cap, flag in zip(all_caps, cam_flags) if flag] # 啟用的攝影機
    caps = [cap_head, cap_left, cap_right, cap_side, cap_sider]
    outs = []
    valid_caps = []
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    for i, cap in enumerate(caps):
        if not cap.isOpened():
            print(
                f"Warning: Camera_{cam_names()[i]} could not be opened and will be skipped.")
            continue
        # width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        # height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # fps = cap.get(cv2.CAP_PROP_FPS) or 30
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        folder = os.path.join(
            f'task_{task_index}', 'videos', 'chunk-000', f'observation.images.{cam_names()[i]}')
        os.makedirs(folder, exist_ok=True)
        filename = file.get_available_filename(
            os.path.join(folder, 'episode.mp4'), episode_index)
        out = cv2.VideoWriter(filename, fourcc, 30, (640, 480))
        valid_caps.append(cap)
        outs.append(out)
    return valid_caps, outs

# 確保 flag 檔案存在
# flag_path = "frame_flag.txt"
# if os.path.exists(flag_path):
#     os.remove(flag_path)


frame_count = 0


def show_image(cap, out):
    global frame_count

    names = cam_names()
    pairs = list(zip(cap, out))

    # 1) 先把所有 frame 讀完TM_ros2.py
    rets, frames = [], []
    for c, _ in pairs:
        ret, frame = c.read()
        rets.append(ret)
        frames.append(frame if ret else None)

    # 2) 統一處理：旋轉 / 寫入 / 顯示
    for idx, ((_, o), ret, frame) in enumerate(zip(pairs, rets, frames)):
        if not ret or frame is None:
            print(f"❌ Camera {idx} ({names[idx]}) did not return a frame.")
            continue

        if names[idx] in ('right'):
            frame = cv2.rotate(frame, cv2.ROTATE_180)

        o.write(frame)
        cv2.imshow(f'Camera_{names[idx]}', frame)

    frame_count += 1


def clear_resources(cap, out):
    """
    清理攝影機資源。
    """
    for c, o in zip(cap, out):
        c.release()
        o.release()
    cv2.destroyAllWindows()


def main():
    while True:
        show_image(cap, out)
        # 按 'q' 鍵退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    clear_resources(cap, out)


if __name__ == '__main__':
    cap, out = cam_init(7, 7)
    main()
