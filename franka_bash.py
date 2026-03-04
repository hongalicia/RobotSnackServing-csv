import subprocess, time

def single_init():
    # 先開啟 franka_bringup
    subprocess.Popen([
        "gnome-terminal", "--", "bash", "-c",
        "source /opt/ros/humble/setup.bash;"
        "source ~/franka_ros2_ws/install/setup.bash;"
        "ros2 launch franka_bringup example.launch.py controller_name:=joint_trajectory_controller; exec bash"
    ])

    # 等待 1 秒，確保 driver 啟動成功
    time.sleep(1)
    
    subprocess.Popen([
        "gnome-terminal", "--", "bash", "-c",
        "source /opt/ros/humble/setup.bash;"
        "source ~/franka_ros2_ws/install/setup.bash;"
        "python3 franka_UDP.py; exec bash"
    ])

def shutdown_ros():
    # 關閉 franka_UDP.py
    subprocess.run(["pkill", "-f", "franka_UDP.py"])
    # 關閉 franka_bringup
    subprocess.run(["pkill", "-f", "example.launch.py"])

if __name__ == '__main__':
    # dual_init()
    single_init()