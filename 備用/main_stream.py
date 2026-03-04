# import TM_ethernet
import file
import cv2
import sys
import 備用.jsonl as jsonl
import parquet
import os
import time
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from UI import Ui_Form
import importlib
from LeRobotRecord import LerobotPackaging
from 備用.camera_stream import CameraStream

mode = sys.argv[1]  # 也可以從 config / argparse / CLI 選項取得
module_name = f"TM_{mode}"  # 組成模組名稱

TM_mode = importlib.import_module(module_name)

start = False
frame_count = 0
task_index, episode_index = 0, 0
timestamp = 0

def record_start():
    global start, frame_count, task_index, episode_index, cap, out
    global timestamp

    file.load_index(task_index) # 讀取上一次的index
    csv_folder = os.path.join(f'task_{task_index}', 'data', 'chunk-000', 'episode.csv')
    csvfile_path = file.get_available_filename(csv_folder,episode_index)

    # 依你的需求映射名字
    cam_indices = [6, 2, 4, 0]
    cam_names   = ["head", "left", "right", "side"]

    # 初始化相機與對應的 VideoWriter（示範，每支相機一個檔）
    cams = []
    writers = []
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # H.264 later
    for idx, (dev_idx, name) in enumerate(zip(cam_indices, cam_names)):
        cam = CameraStream(dev_idx, 640, 480, 30, name=name)
        cams.append(cam)
        mp4_folder = os.path.join(f'task_{task_index}', 'videos', 'chunk-000', f'observation.images.{cam_names[idx]}')
        os.makedirs(mp4_folder, exist_ok=True)
        mp4file = file.get_available_filename(os.path.join(mp4_folder, 'episode.mp4'), episode_index)
        writers.append(cv2.VideoWriter(
            mp4file, fourcc, 30, (640, 480)
        ))

    last_seq = [ -1 ] * len(cams)

    while start:
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
        else:
            # 每幀觸發事件 → 讀取 TM 資料
            joint_angle_L=TM_mode.L_queue.get()
            joint_angle_R=TM_mode.R_queue.get()
            joint_angle = joint_angle_L + joint_angle_R
            # 將 joint_angle 內的 string 轉成 float64
            joint_angle = [float(j) for j in joint_angle]
            print(f"Joint_Angle = {joint_angle}")
            # 儲存資料到 CSV 檔案
            csv_data = file.data_create(joint_angle, timestamp, frame_count, episode_index, task_index)
            file.save_to_csv(csvfile_path, csv_data)
            frame_count += 1
            timestamp += 1/30 

        if cv2.waitKey(33) & 0xFF == ord('q'):
            break

    # 清理資源並存檔
    for w in writers: w.release()
    for c in cams: c.release()
    cv2.destroyAllWindows()
    file.save_index(task_index,-1) # 儲存 index 到檔案
    file.fill_action(csvfile_path)  # 填補 action 欄位
    frame_count=0

def episode_jsonl_saved(episode_text,final_index,ui):
    task_index = ui.spinBox_task.value()
    episode_index = ui.spinBox_episode.value()
    episodes = jsonl.EpisodesJsonl()  
    episodes.Add(jsonl.Episode(episode_index, [episode_text], final_index))
    episodes_path = os.path.join(f'task_{task_index}', 'meta', 'episodes.jsonl')
    episodes.Save(episodes_path)

def task_jsonl_saved(ui):
    task_name = ui.textEdit_task_name.toPlainText()
    task_index = ui.spinBox_task.value()
    tasks = jsonl.TasksJsonl()
    tasks.Add(jsonl.Task(task_index, task_name))
    tasks_path = os.path.join(f'task_{task_index}', 'meta', 'tasks.jsonl')
    tasks.Save(tasks_path)

def all_csv_to_parquet(ui):
    task_index = ui.spinBox_task.value()
    data_path = os.path.join(f'task_{task_index}', 'data', 'chunk-000')
    csv_files = [f for f in os.listdir(data_path) if f.endswith('.csv')]

    # 根據實際存在的 episode_xxxxxx.csv 檔案做轉換
    for fname in csv_files:
        parts = fname.split('_')
        if len(parts) == 2 and parts[0] == 'episode':
            idx_str = parts[1].replace('.csv', '')
            try:
                idx = int(idx_str)
                csv_path = os.path.join(data_path, fname)
                parquet_path = os.path.join(data_path, f'episode_{idx:06d}.parquet')
                parquet.csv_to_parquet(csv_path, parquet_path)
                parquet.string_to_float(parquet_path)
            except ValueError:
                continue  # 略過不是正確數字的檔名
    all_csv_delete(ui)

def all_csv_delete(ui):
    task_index = ui.spinBox_task.value()
    data_path = os.path.join(f'task_{task_index}', 'data', 'chunk-000')
    csv_files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    for fname in csv_files:
        os.remove(os.path.join(data_path, fname))
    print(f"All CSV files in {data_path} have been deleted.")

def all_package(ui):
    path = LerobotPackaging.ArgsConfig()
    path.folder_dir = f'./task_{task_index}'.format(ui.spinBox_task.value())
    # 呼叫 meta 函數來處理資料夾結構和檔案
    LerobotPackaging.meta(path) 

def delete_episode(ui):
    task_index = ui.spinBox_task.value()
    episode_index = ui.spinBox_episode.value()
    file_path = os.path.join(f'task_{task_index}', 'data', 'chunk-000', f'episode_{episode_index:06d}.csv')
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Episode {episode_index} in task {task_index} has been deleted.")
    else:
        print(f"Episode {episode_index} in task {task_index} does not exist.")

def run_clicked(ui):
    global start, task_index, episode_index
    global timestamp
    timestamp = 0
    start = True
    task_index = ui.spinBox_task.value()
    episode_index = ui.spinBox_episode.value()
    print(f"TASK：{task_index}，EPISODE：{episode_index}")
    record_start()

def stop_clicked(ui):
    global start
    start = False
    episode_jsonl_saved(ui.textEdit_task_name.toPlainText(),frame_count,ui)
    print("Recording stopped, episode_jsonl saved.")

def reset_clicked(ui):
    file.save_index(ui.spinBox_task.value(),0)
    message = f"-----Done!!!-----"
    # 建立並顯示 popout 訊息視窗
    QMessageBox.information(None, "Index Reset", message)
    # record_start()

def task_end_clicked(ui):
    task_jsonl_saved(ui)
    if ui.checkBox_parquet.isChecked():
        all_csv_to_parquet(ui)
        all_package(ui)
        message = f"--package done!!!--"
    else:
        message = f"--task_jsonl saved!!!--"
    # 建立並顯示 popout 訊息視窗
    QMessageBox.information(None, "task_end", message)

def delete_clicked(ui):
    task_index = ui.spinBox_task.value()
    episode_index = ui.spinBox_episode.value()
    # 刪除對應的 CSV 檔案
    csv_path = os.path.join(f'task_{task_index}', 'data', 'chunk-000', f'episode_{episode_index:06d}.csv')
    if not os.path.exists(csv_path):
        # 建立並顯示 popout 訊息視窗
        message = f"No episode_{episode_index:06d}.csv found"
        QMessageBox.information(None, "episode_delete", message)
        return
    get_index = file.find_index(csv_path)  # 讀取第1筆index
    file.save_index(task_index, get_index)  # 重新寫入file
    os.remove(csv_path)
    print(f"Deleted {csv_path}")
    # 刪除對應的 MP4 檔案
    for i in range(4):
        mp4_path = os.path.join(f'task_{task_index}', 'videos', 'chunk-000', f'observation.images.{webcam.cam_names()[i]}', f'episode_{episode_index:06d}.mp4')
        if not os.path.exists(mp4_path):
            # 建立並顯示 popout 訊息視窗
            message = f"No episode_{episode_index:06d}.mp4 found"
            QMessageBox.information(None, "episode_delete", message)
            return
        os.remove(mp4_path)
        print(f"Deleted {mp4_path}")

    # 建立並顯示 popout 訊息視窗
    message = f"Episode:{episode_index} was deleted."
    QMessageBox.information(None, "episode_delete", message)

def main():
    # 初始化 TM 以太網連線
    TM_mode.socket_init()
    TM_mode.start_svr_read_thread()
    app = QApplication(sys.argv)
    window = QWidget()
    ui = Ui_Form()
    ui.setupUi(window)
    window.show()
    ui.pushBtn_run.clicked.connect(lambda: run_clicked(ui))
    ui.pushBtn_stop.clicked.connect(lambda: stop_clicked(ui))
    ui.pushBtn_reset.clicked.connect(lambda: reset_clicked(ui))
    ui.pushBtn_task_save.clicked.connect(lambda: task_end_clicked(ui))
    ui.pushBtn_delete.clicked.connect(lambda: delete_clicked(ui))
    sys.exit(app.exec())

if __name__ == "__main__":
    main()