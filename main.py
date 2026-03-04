import webcam
# import TM_ethernet
import file
import cv2
import sys
import json
import jsonl
import parquet
import os
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from UI import Ui_Form
import importlib
from LeRobotRecord import LerobotPackaging
import time
# from TM_string import event
import threading
import ros_bash  # TM手臂
import franka_bash  # Franka手臂
from uart import UART, uart_queue

mode = sys.argv[1]  # 也可以從 config / argparse / CLI 選項取得
module_name = f"TM_{mode}"  # 組成模組名稱
TM_mode = importlib.import_module(module_name)

if module_name == "TM_ros":
    arm_num = int(sys.argv[2])
    if arm_num == 0:
        franka_bash.single_init()
    elif arm_num == 1:
        ros_bash.single_init()
    elif arm_num == 2:
        ros_bash.dual_init()

start = False
frame_count = 0
task_index, episode_index = 0, 0
timestamp = 0

episodes = jsonl.EpisodesJsonl()

hmi = UART("/dev/ttyUSB0", 115200)

# 啟動攝影機錄影
# cap, out = webcam.cam_init(task_index, episode_index)

def read_uart_thread(ui):
    def read_loop():
        global start
        while True:
            if not uart_queue.empty():
                cmd = uart_queue.get()  # 只 get 一次
                # print(f'uart_queue:{cmd}')
                if cmd=='S' and not start:
                    # print("Start")
                    ui.pushBtn_run.click()
                elif cmd=='T' and start:
                    # print("Stop")
                    ui.pushBtn_stop.click()
                # while not uart_queue.empty():
                #     TM_mode.ros_queue.get() 
            time.sleep(0.05)
    t = threading.Thread(target=read_loop, daemon=True)
    t.start()

def record_start(ui):
    global start, frame_count, task_index, episode_index, cap, out
    global timestamp
    global TM_mode

    file.load_index(task_index)  # 讀取上一次的index
    file_path = os.path.join(
        f'task_{task_index}', 'data', 'chunk-000', 'episode.csv')
    filename = file.get_available_filename(file_path, episode_index)

    # 啟動攝影機錄影
    cap, out = webcam.cam_init(task_index, episode_index)
    names = webcam.cam_names()
    pairs = list(zip(cap, out))

    list_csv_data = []
    # 保持主線程運行，讓背景執行緒可以持續執行
    while start:
        # if frame_count == 0:
        # start_time = cv2.getTickCount() / cv2.getTickFrequency()
        # print(f"Start time: {start_time:.6f} seconds")
        # print("Time Start")

        # 1) 先把所有 frame 讀完
        start_time = time.time()
        rets, frames = [], []
        for c, _ in pairs:
            ret, frame = c.read()
            rets.append(ret)
            frames.append(frame if ret else None)

        # 2) 統一處理：旋轉 / 寫入 / 顯示 / 存檔
        for idx, ((_, o), ret, frame) in enumerate(zip(pairs, rets, frames)):
            if not ret or frame is None:
                print(f"❌ Camera {idx} ({names[idx]}) did not return a frame.")
                continue

            if names[idx] in ('right'):
                frame = cv2.rotate(frame, cv2.ROTATE_180)

            # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
            o.write(frame)
            if ui.checkBox_show_video.isChecked():
                cv2.imshow(f'Camera_{names[idx]}', frame)
        end_time = time.time()
        # print(f"Frame processing time: {end_time - start_time:.6f} seconds")

        # 記錄每個 frame 的 time stamp
        # timestamp = cv2.getTickCount() / cv2.getTickFrequency()
        # timestamp -= start_time
        # print(f"Frame {frame_count} : {timestamp:.6f} sec")

        # 每幀觸發事件 → 讀取 TM 資料
        joint_angle_L = TM_mode.ros_queue.get()
        while not TM_mode.ros_queue.empty():
            TM_mode.ros_queue.get()
        # joint_angle_R=TM_mode.R_queue.get()
        # joint_angle = joint_angle_L + joint_angle_R
        joint_angle = joint_angle_L
        # 將 joint_angle 內的 string 轉成 float64
        joint_angle = [float(j) for j in joint_angle]
        print(f"Joint_Angle = {joint_angle}")
        # 儲存資料到 CSV 檔案
        list_csv_data.append(file.data_create(
            joint_angle, timestamp, frame_count, episode_index, task_index))
        # file.save_to_csv(filename, csv_data)
        frame_count += 1
        timestamp += 1/30

        # TM_mode.L_queue.task_done()
        if ui.checkBox_show_video.isChecked():
            if cv2.waitKey(33) & 0xFF == ord('q'):
                break

    for csv_data in list_csv_data:
        file.save_to_csv(filename, csv_data)

    # 清理資源並存檔
    webcam.clear_resources(cap, out)
    file.save_index(task_index, -1)  # 儲存 index 到檔案
    file.fill_action(filename)  # 填補 action 欄位
    frame_count = 0
    print("Recording stopped")


def episode_jsonl_added(episode_text, final_index, ui):
    # task_index = ui.spinBox_task.value()
    episode_index = ui.spinBox_episode.value()
    global episodes
    episodes.Add(jsonl.Episode(episode_index, [episode_text], final_index))
    # episodes_path = os.path.join(f'task_{task_index}', 'meta', 'episodes.jsonl')
    # episodes.Save(episodes_path)


def episode_jsonl_saved(ui):
    task_index = ui.spinBox_task.value()
    global episodes
    episodes_path = os.path.join(
        f'task_{task_index}', 'meta', 'episodes.jsonl')
    episodes.Save(episodes_path)


def task_jsonl_saved(ui):
    task_name = ui.textEdit_task_name.toPlainText()
    task_index = ui.spinBox_task.value()
    tasks = jsonl.TasksJsonl()
    tasks.Add(jsonl.Task(task_index, task_name))
    # tasks_path = os.path.join(f'task_{task_index}', 'meta', 'tasks.jsonl')
    tasks_path = os.path.join(file.new_dir_path(), 'meta', 'tasks.jsonl')
    tasks.Save(tasks_path)


def all_csv_to_parquet(ui):
    # task_index = ui.spinBox_task.value()
    # data_path = os.path.join(f'task_{task_index}', 'data', 'chunk-000')
    data_path = os.path.join(file.new_dir_path(), 'data', 'chunk-000')
    csv_files = [f for f in os.listdir(data_path) if f.endswith('.csv')]

    # 根據實際存在的 episode_xxxxxx.csv 檔案做轉換
    for fname in csv_files:
        parts = fname.split('_')
        if len(parts) == 2 and parts[0] == 'episode':
            idx_str = parts[1].replace('.csv', '')
            try:
                idx = int(idx_str)
                csv_path = os.path.join(data_path, fname)
                parquet_path = os.path.join(
                    data_path, f'episode_{idx:06d}.parquet')
                parquet.csv_to_parquet(csv_path, parquet_path)
                parquet.string_to_float(parquet_path)
            except ValueError:
                continue  # 略過不是正確數字的檔名
    all_csv_delete(ui)


def all_csv_delete(ui):
    task_index = ui.spinBox_task.value()
    # data_path = os.path.join(f'task_{task_index}', 'data', 'chunk-000')
    data_path = os.path.join(file.new_dir_path(), 'data', 'chunk-000')
    csv_files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    for fname in csv_files:
        os.remove(os.path.join(data_path, fname))
    print(f"All CSV files in {data_path} have been deleted.")


def all_package(ui):
    global arm_num
    config = LerobotPackaging.ArgsConfig()
    # path.folder_dir = f'./task_{task_index}'.format(ui.spinBox_task.value())
    config.folder_dir = file.new_dir_path()
    config.num_arms = arm_num
    print(f'num_arms:  {arm_num}')
    # 呼叫 meta 函數來處理資料夾結構和檔案
    LerobotPackaging.meta(config)


def delete_csv(ui):
    task_index = ui.spinBox_task.value()
    episode_index = ui.spinBox_episode.value()
    csv_path = os.path.join(
        f'task_{task_index}', 'data', 'chunk-000', f'episode_{episode_index:06d}.csv')
    # if not os.path.exists(csv_path):
    #     # 建立並顯示 popout 訊息視窗
    #     message = f"No episode_{episode_index:06d}.csv found"
    #     QMessageBox.information(None, "episode_delete", message)
    #     return
    get_index = file.find_index(csv_path)  # 讀取第1筆index
    file.save_index(task_index, get_index)  # 重新寫入file
    os.remove(csv_path)
    print(f"Deleted {csv_path}")


def delete_mp4(ui):
    task_index = ui.spinBox_task.value()
    episode_index = ui.spinBox_episode.value()
    for i in range(4):
        mp4_path = os.path.join(f'task_{task_index}', 'videos', 'chunk-000',
                                f'observation.images.{webcam.cam_names()[i]}', f'episode_{episode_index:06d}.mp4')
        # if not os.path.exists(mp4_path):
        #     # 建立並顯示 popout 訊息視窗
        #     message = f"No episode_{episode_index:06d}.mp4 found"
        #     QMessageBox.information(None, "episode_delete", message)
        #     return
        os.remove(mp4_path)
        print(f"Deleted {mp4_path}")


def delete_jsonl_index(ui):
    task_index = ui.spinBox_task.value()
    episode_index = ui.spinBox_episode.value()
    # 讀取 JSONL 檔案
    jsonl_path = os.path.join(f'task_{task_index}', 'meta', 'episodes.jsonl')

    # 讀取原始檔案並過濾資料
    with open(jsonl_path, "r", encoding="utf-8") as infile:
        lines = infile.readlines()

    filtered_lines = []
    for line in lines:
        if line.strip():
            try:
                data = json.loads(line)
                # 只保留不等於 target_index 的資料
                if data.get("episode_index") != episode_index:
                    filtered_lines.append(json.dumps(
                        data, ensure_ascii=False) + "\n")
            except json.JSONDecodeError:
                print(f"⚠️ JSON 格式錯誤, 跳過該行: {line.strip()}")

    # 將結果寫入新檔案
    with open(jsonl_path, "w", encoding="utf-8") as outfile:
        outfile.writelines(filtered_lines)


def UI_enabled(ui, enable):
    ui.pushBtn_run.setEnabled(enable)
    ui.pushBtn_index_set.setEnabled(enable)
    ui.pushBtn_task_save.setEnabled(enable)
    ui.pushBtn_delete.setEnabled(enable)
    ui.groupBox_video.setEnabled(enable)

# =======================UI按鈕事件=========================


def run_clicked(ui):
    ui.pushBtn_stop.setEnabled(True)
    UI_enabled(ui, False)
    global start, task_index, episode_index
    global timestamp
    timestamp = 0
    # event.set()
    start = True
    task_index = ui.spinBox_task.value()
    episode_index = ui.spinBox_episode.value()
    print(f"TASK：{task_index}，EPISODE：{episode_index}")
    # HMI
    hmi.send_num("n0", episode_index)
    hmi.send_clicked("b0", 1)
    hmi.send_clicked("b0", 0)
    if ui.checkBox_show_video.isChecked():
        record_start(ui)
    else:
        t = threading.Thread(target=record_start, args=(ui,), daemon=True)
        t.start()


def stop_clicked(ui):
    global start
    start = False
    ui.pushBtn_stop.setEnabled(False)
    episode_jsonl_added(ui.textEdit_task_name.toPlainText(), frame_count, ui)
    episode_jsonl_saved(ui)
    UI_enabled(ui, True)
    #HMI
    hmi.send_clicked("b1", 1)
    hmi.send_clicked("b1", 0)
    #錄製結束後episode+1
    episode_index = ui.spinBox_episode.value()
    ui.spinBox_episode.setValue(episode_index+1)
    hmi.send_num("n0", episode_index+1)



def set_index_clicked(ui):
    file.save_index(ui.spinBox_task.value(), ui.spinBox_index.value())
    message = f"-- Index Reset to {ui.spinBox_index.value()} --"
    # 建立並顯示 popout 訊息視窗
    QMessageBox.information(None, "Index Reset", message)
    # record_start()


def task_end_clicked(ui):
    file.choose_folders(ui)
    task_jsonl_saved(ui)
    all_package(ui)
    if ui.checkBox_parquet.isChecked():
        all_csv_to_parquet(ui)
        # all_package(ui)
        message = f"--all csv to parquet done--"
        time.sleep(1)
    message = f"--package done!!!--"
    # 建立並顯示 popout 訊息視窗
    QMessageBox.information(None, "task_end", message)


def delete_clicked(ui):
    episode_index = ui.spinBox_episode.value()
    delete_jsonl_index(ui)
    # 刪除對應的 CSV 檔案
    delete_csv(ui)
    # 刪除對應的 MP4 檔案
    delete_mp4(ui)
    # 建立並顯示 popout 訊息視窗
    message = f"Episode:{episode_index} was deleted."
    QMessageBox.information(None, "episode_delete", message)


def new_close_event(event):
    global arm_num
    # HMI reset
    hmi.send_num("n0", 0)
    hmi.send_clicked("b1", 1)
    hmi.send_clicked("b1", 0)
    # kill ROS node and console window
    if arm_num==0:
        franka_bash.shutdown_ros()
    else:
        ros_bash.shutdown_ros()
    # print("額外清理完成")
    event.accept()
    

def main():
    # 初始化 TM 以太網連線
    TM_mode.socket_init()
    TM_mode.start_svr_read_thread()
    app = QApplication(sys.argv)
    window = QWidget()
    ui = Ui_Form()
    read_uart_thread(ui) # 啟動讀取 UART 執行緒 for HMI
    ui.setupUi(window)
    window.closeEvent = new_close_event
    ui.pushBtn_stop.setEnabled(False) #一開始先將stop鎖住,跟HMI同步
    window.show()
    ui.pushBtn_run.clicked.connect(lambda: run_clicked(ui))
    ui.pushBtn_stop.clicked.connect(lambda: stop_clicked(ui))
    ui.pushBtn_index_set.clicked.connect(lambda: set_index_clicked(ui))
    ui.pushBtn_task_save.clicked.connect(lambda: task_end_clicked(ui))
    ui.pushBtn_delete.clicked.connect(lambda: delete_clicked(ui))
    sys.exit(app.exec())

    # window = FolderCopyApp()
    # ui=uic.loadUi("window.ui")
    # window.UI_init(ui)
    # ui.show()


if __name__ == "__main__":
    main()
