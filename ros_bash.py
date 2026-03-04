import subprocess, time

def dual_init():
    # 先開啟 tm_driver
    subprocess.Popen([
        "gnome-terminal", "--", "bash", "-c",
        # "source ~/ros2_humble/install/local_setup.bash; "
        "source /opt/ros/humble/setup.bash; "
        "source ~/tm2_ws/install/local_setup.bash; "
        "ros2 launch tm_driver dual_tm.launch.py; exec bash"
    ])

    # 等待 1 秒，確保 driver 啟動成功
    time.sleep(1)

    subprocess.Popen([
        "gnome-terminal", "--", "bash", "-c",
        # "source ~/ros2_humble/install/local_setup.bash; "
        "source /opt/ros/humble/setup.bash; "
        "source ~/tm2_ws/install/local_setup.bash; "
        "python3 ros_UDP.py 2; exec bash"
    ])

def single_init():
    # 先開啟 tm_driver
    subprocess.Popen([
        "gnome-terminal", "--", "bash", "-c",
        # "source ~/ros2_humble/install/local_setup.bash; "
        "source /opt/ros/humble/setup.bash; "
        "source ~/tm2_ws/install/local_setup.bash; "
        "ros2 launch tm_driver tm_bringup.launch.py robot_ip:=192.168.1.10; exec bash"
    ])

    # 等待 1 秒，確保 driver 啟動成功
    time.sleep(1)
    
    subprocess.Popen([
        "gnome-terminal", "--", "bash", "-c",
        # "source ~/ros2_humble/install/local_setup.bash; "
        "source /opt/ros/humble/setup.bash; "
        "source ~/tm2_ws/install/local_setup.bash; "
        "python3 ros_UDP.py 1; exec bash"
    ])

def shutdown_ros():
    # 關閉 ros_UDP.py
    subprocess.run(["pkill", "-f", "ros_UDP.py"])
    # 關閉 tm_driver
    subprocess.run(["pkill", "-f", "tm_driver"])

if __name__ == '__main__':
    # dual_init()
    single_init()