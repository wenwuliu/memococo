import sys
import subprocess
from memococo.config import logger

XDOTOOL = "xdotool"
XPROP = "xprop"
WINDOWS = "win32"
LINUX = "linux"
MACOS = "darwin"
WM_CLASS = "WM_CLASS"
_NET_WM_NAME = "_NET_WM_NAME"
IOREG = "ioreg"
IOHIDSYSTEM = "IOHIDSystem"
HID_IDLE_TIME = "HIDIdleTime"
XPRINTIDLE = "xprintidle"

def human_readable_time(timestamp):
    import datetime

    now = datetime.datetime.now()
    dt_object = datetime.datetime.fromtimestamp(timestamp)
    diff = now - dt_object
    if diff.days > 0:
        return f"{diff.days} 天前"
    elif diff.seconds < 60:
        return f"{diff.seconds} 秒前"
    elif diff.seconds < 3540:
        return f"{diff.seconds // 60} 分钟前"
    else:
        #小时需要考四舍五入
        hours = round(diff.seconds / 3600)
        #取整
        return f"{hours} 小时前"
    


def timestamp_to_human_readable(timestamp):
    import datetime

    try:
        dt_object = datetime.datetime.fromtimestamp(timestamp)
        return dt_object.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.warning(f"Error converting timestamp to human readable format: {e}")
        return ""


def get_active_app_name_osx():
    from AppKit import NSWorkspace

    try:
        active_app = NSWorkspace.sharedWorkspace().activeApplication()
        return active_app["NSApplicationName"]
    except Exception as e:
        logger.warning(f"Error getting active app name on macOS: {e}")
        return ""


def get_active_window_title_osx():
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGNullWindowID,
        kCGWindowListOptionOnScreenOnly,
    )

    try:
        app_name = get_active_app_name_osx()
        windows = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        )
        for window in windows:
            if window["kCGWindowOwnerName"] == app_name:
                return window.get("kCGWindowName", "Unknown")
    except Exception as e:
        logger.warning(f"Error getting active window title on macOS: {e}")
        return ""
    return ""


def get_active_app_name_windows():
    import psutil
    import win32gui
    import win32process

    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        exe = psutil.Process(pid).name()
        return exe
    except Exception as e:
        logger.warning(f"Error getting active app name on Windows: {e}")
        return ""


def get_active_window_title_windows():
    import win32gui

    try:
        hwnd = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(hwnd)
    except Exception as e:
        logger.warning(f"Error getting active window title on Windows: {e}")
        return ""


def get_active_app_name_linux():
    try:
        # 获取当前活动窗口的ID
        window_id = subprocess.check_output([XDOTOOL, 'getactivewindow']).strip()
        # 使用xprop获取窗口的应用程序名称
        app_name = subprocess.check_output([XPROP, '-id', window_id, WM_CLASS]).decode()
        # 提取应用程序名称
        app_name = app_name.split('=')[1].strip().split(',')[0].strip('"')
        return app_name
    except Exception as e:
        logger.warning(f"Error getting active app name on Linux: {e}")
        return None


def get_active_window_title_linux():
    try:
        window_id = subprocess.check_output([XDOTOOL, 'getactivewindow']).strip()
        window_title = subprocess.check_output([XPROP, '-id', window_id, _NET_WM_NAME]).decode()
        window_title = window_title.split('=')[1].strip().strip('"')
        return window_title
    except Exception as e:
        logger.warning(f"Error getting active window title on Linux: {e}")
        return None


def get_active_app_name():
    if sys.platform == WINDOWS:
        return get_active_app_name_windows()
    elif sys.platform == MACOS:
        return get_active_app_name_osx()
    elif sys.platform.startswith(LINUX):
        return get_active_app_name_linux()
    else:
        raise NotImplementedError("This platform is not supported")


def get_active_window_title():
    if sys.platform == WINDOWS:
        return get_active_window_title_windows()
    elif sys.platform == MACOS:
        return get_active_window_title_osx()
    elif sys.platform.startswith(LINUX):
        return get_active_window_title_linux()
    else:
        raise NotImplementedError("This platform is not supported")


def is_user_active_osx():

    try:
        # Run the 'ioreg' command to get idle time information
        output = subprocess.check_output([IOREG, "-c", IOHIDSYSTEM]).decode()

        # Find the line containing "HIDIdleTime"
        for line in output.split("\n"):
            if HID_IDLE_TIME in line:
                # Extract the idle time value
                idle_time = int(line.split("=")[-1].strip())

                # Convert idle time from nanoseconds to seconds
                idle_seconds = idle_time / 1000000000

                # If idle time is less than 5 seconds, consider the user not idle
                return idle_seconds < 5

        # If "HIDIdleTime" is not found, assume the user is not idle
        return True

    except subprocess.CalledProcessError:
        # If there's an error running the command, assume the user is not idle
        return True
    except Exception as e:
        logger.warning(f"An error occurred: {e}")
        # If there's any other error, assume the user is not idle
        return True
    
def is_user_active_linux():
    try:
        idle_time = int(subprocess.check_output([XPRINTIDLE]).strip()) / 1000  # 转换为秒
        return idle_time < 5
    except Exception as e:
        logger.warning(f"Error getting user idle time on Linux: {e}")
        return True


def is_user_active():
    if sys.platform == WINDOWS:
        return True
    elif sys.platform == MACOS:
        return is_user_active_osx()
    elif sys.platform.startswith(LINUX):
        return is_user_active_linux()
    else:
        raise NotImplementedError("This platform is not supported")

# todo:bug fix
def is_battery_charging():
    import power
    ans = power.PowerManagement().get_providing_power_source_type()
    if not ans:
        return False
    else:
        return True