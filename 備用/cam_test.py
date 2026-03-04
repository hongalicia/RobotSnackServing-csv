import cv2

for fcc in ["avc1", "H264", "X264", "mp4v"]:
    fourcc = cv2.VideoWriter_fourcc(*fcc)
    out = cv2.VideoWriter(f"test_{fcc}.mp4", fourcc, 30, (640,480))
    print(f"{fcc}: {out.isOpened()}")
    out.release()

