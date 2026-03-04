import csv
import os
import pandas as pd
import shutil
from datetime import datetime

new_dir = ""

def load_index(task_index):
    global csv_index
    file_path = os.path.join(f'task_{task_index}', 'index.txt')
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                csv_index=int(f.read())
            except ValueError:
                print(f"Index file {file_path} is corrupted or empty.")
    else:
        # 若檔案不存在則建立並寫入0
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path)
        with open(file_path, 'w') as f:
            f.write('0')
        csv_index = 0

def save_index(task_index,assign_index):
    global csv_index
    file_path = os.path.join(f'task_{task_index}', 'index.txt')
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(file_path, 'w') as f:
        if assign_index < 0:
            f.write(str(csv_index))
        else:
            f.write(str(assign_index))

CSV_FIELDS = [
    'observation.state', 'action', 'timestamp', 'frame_index',
    'episode_index', 'index', 'task_index'
]

def get_available_filename(filename, index):
    """
    根據 index 產生 6 位數排序的檔名，例如 filename_000001.csv。
    若檔案已存在則直接覆蓋。
    """
    base, ext = os.path.splitext(filename)
    numbered_filename = f"{base}_{index:06d}{ext}"
    return numbered_filename

def find_index(file_path):
    df = pd.read_csv(file_path)
    if df.empty or 'index' not in df.columns:
        return None
    return int(df['index'].iloc[0]) #返回第一行的 index 值
    

def save_to_csv(filename, data):
    """
    儲存資料到CSV檔案。若資料缺少欄位則自動補0。
    :param filename: CSV檔案名稱
    :param data: dict 或 dict list，每個dict對應一列
    """
    global csv_index
    # 若檔案不存在則建立新檔案
    dir_path = os.path.dirname(filename)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    # if not os.path.isfile(filename):
    #     open(filename, 'w').close()
    # 確保資料為list of dict
    if isinstance(data, dict):
        data = [data]
    rows = []
    for row in data:
        filled_row = {field: row.get(field, 0) for field in CSV_FIELDS}
        # filled_row['validity'] = 1  # 強制將 validity 欄位設為 1
        filled_row['index'] = csv_index
        rows.append(filled_row)
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
    csv_index += 1  # 每次寫入後自動遞增 index

def data_create(state, timestamp, frame_index, episode_index, task_index):  
    """
    根據state和timestamp產生完整的資料dict，其餘欄位補0。
    :param state: 狀態
    :param timestamp: 時間戳
    :return: dict，包含所有CSV_FIELDS欄位
    """
    
    data = {field: 0 for field in CSV_FIELDS}
    data['observation.state'] = state
    data['timestamp'] = timestamp
    data['frame_index'] = frame_index
    data['episode_index'] = episode_index
    data['task_index'] = task_index
    
    return data

def fill_action(filename):
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = list(csv.DictReader(csvfile))
        if not reader:
            print("No data to process.")
            return

    for i in range(len(reader) - 1):
        reader[i]['action'] = reader[i+1]['observation.state']
    
    # 最後一行的 action 設為與 observation.state 相同
    reader[len(reader) - 1]['action'] = reader[len(reader) - 1]['observation.state'] 

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(reader)

def file_type(filename):
    df = pd.read_csv(filename)
    print(df.dtypes)

def choose_folders(ui):
    global new_dir

    folder_map = {
            ui.checkBox_save_head: "head",
            ui.checkBox_save_left: "left",
            ui.checkBox_save_right: "right",
            ui.checkBox_save_side: "side",
            ui.checkBox_save_sider: "sider",
        }
    # 選擇目標資料夾
    target_dir = "./"

    # 產生新資料夾名稱
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_dir = os.path.join(target_dir, f"dataset-{timestamp}")

    # 複製整個資料夾
    shutil.copytree("task_0", new_dir)

    # 刪除沒勾選的子資料夾
    for checkbox, folder_name in folder_map.items():
        folder_path = os.path.join('videos', 'chunk-000', f'observation.images.{folder_name}')
        if not checkbox.isChecked():
            del_path = os.path.join(new_dir, folder_path)
            # print(f"Deleting {del_path}")
            if os.path.isdir(del_path):
                shutil.rmtree(del_path)

    print("Completed copying to", new_dir)

def new_dir_path():
    global new_dir
    return new_dir

# 範例用法
if __name__ == "__main__":
    task_index = 0
    # save_index(task_index,-1)
    load_index(task_index)
    # print(f"Loaded index: {csv_index}")

    # csv_index = 0
    # data=data_create("[-286.0044, -34.819267, -72.749016, -72.22843, 113.77002, -318.4129, 109.83017, 75.720665, -11.652917, -40.6819, 109.805435, 140.41542]","2.219326","2","3","1")
    # print(data)
    # save_to_csv('output.csv', data)
    # file_type('output.csv')

    