import cv2


def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Cannot open video file.")
        return

    # Codec info
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

    # Pixel format (OpenCV returns frames as BGR by default)
    ret, frame = cap.read()
    if ret:
        pixel_format = "BGR"
    else:
        pixel_format = "Unknown"

    cap.release()
    print(f"Codec: {codec}")
    print(f"Pixel Format: {pixel_format}")


if __name__ == "__main__":
    # Replace with your video file path
    video_path = "/home/wtyen/Multi_TMFlow_ROS/task_7/videos/chunk-000/observation.images.left/episode_000007.mp4"
    get_video_info(video_path)
