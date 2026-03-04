import cv2
import os
import glob

# 設定要搜尋的資料夾路徑
video_folder = "./task_0/videos/chunk-000/observation.images.head"  # 替換成你的資料夾路徑

# 使用 glob 找出所有 mp4 檔案
video_files = glob.glob(os.path.join(video_folder, "*.mp4"))

# 檢查資料夾內是否有影片
if not video_files:
    print("⚠️ 沒有找到任何 mp4 檔案")
else:
    print(f"找到 {len(video_files)} 個 mp4 檔案，開始計算...\n")

    # 逐一處理影片
    for video_path in video_files:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"❌ 無法開啟影片: {os.path.basename(video_path)}")
            continue

        # 取得總幀數與 FPS
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # 計算影片長度
        duration = total_frames / fps if fps > 0 else 0

        # 輸出結果
        print(f"🎥 {os.path.basename(video_path)}")
        print(f"   - 總幀數: {total_frames}")
        print(f"   - FPS: {fps:.2f}")
        print(f"   - 長度: {duration:.2f} 秒\n")

        cap.release()
