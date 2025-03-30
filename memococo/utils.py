import sys
import subprocess
from memococo.config import logger
import cv2
import csv
import os
from datetime import timedelta
import datetime
from typing import List, Optional
import io

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
RECORD_NAME = "record.mp4"

def check_port(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def count_unique_keywords(text, keywords):
    # 将 keywords 转换为集合以去重（防止输入中有重复关键词）
    keyword_set = set(keywords)
    
    # 用于存储已经找到的关键词
    found_keywords = set()
    
    # 遍历每个关键词，检查是否在 text 中
    for keyword in keyword_set:
        if keyword in text:  # 如果关键词存在于 text 中
            found_keywords.add(keyword)  # 添加到已找到的集合中
    
    # 返回找到的不重复关键词的数量
    return len(found_keywords)




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


# def get_active_app_name_windows():
#     import psutil
#     import win32gui
#     import win32process

#     try:
#         hwnd = win32gui.GetForegroundWindow()
#         _, pid = win32process.GetWindowThreadProcessId(hwnd)
#         exe = psutil.Process(pid).name()
#         return exe
#     except Exception as e:
#         logger.warning(f"Error getting active app name on Windows: {e}")
#         return ""

def get_active_app_name_windows():
    import psutil
    import win32gui
    import win32process
    import win32api
    import win32con
    """
    获取当前活动应用程序的友好名称。
    
    Returns:
        str: 当前活动应用程序的友好名称（如 "Google Chrome"）。
    """
    try:
        # 获取当前活动窗口的句柄
        hwnd = win32gui.GetForegroundWindow()
        
        # 获取该窗口所属的进程 ID
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        # 根据进程 ID 获取对应的进程对象
        process = psutil.Process(pid)
        
        # 获取可执行文件的路径
        exe_path = process.exe()
        # 从可执行文件路径提取友好名称
        friendly_name = get_friendly_app_name(exe_path)
        return friendly_name
    
    except Exception as e:
        logger.info(f"发生错误: {e}")
        return None


def get_friendly_app_name(exe_path):
    import psutil
    import win32gui
    import win32process
    import win32api
    import win32con
    """
    根据可执行文件路径获取应用程序的友好名称。
    
    Args:
        exe_path (str): 可执行文件的完整路径。
        
    Returns:
        str: 应用程序的友好名称。
    """
    try:
        # 使用 Windows API 获取文件的版本信息
        info = win32api.GetFileVersionInfo(exe_path, "\\")
        # 提取内部名称（通常是应用程序的友好名称）
        if "FileDescription" in info:
            return info["FileDescription"]
        
        # 如果没有 FileDescription，则返回文件名
        return os.path.basename(exe_path)
    
    except Exception:
        # 如果无法获取版本信息，则返回文件名
        return os.path.basename(exe_path)


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
    

def get_idle_time():
    import ctypes
    """
    获取用户当前的空闲时间（以秒为单位）。
    
    Returns:
        int: 用户空闲时间（秒）。
    """
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint),
                    ("dwTime", ctypes.c_ulong)]

    # 初始化结构体
    last_input_info = LASTINPUTINFO()
    last_input_info.cbSize = ctypes.sizeof(LASTINPUTINFO)

    # 调用 GetLastInputInfo 函数
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input_info)):
        raise RuntimeError("无法获取用户最后一次输入信息。")

    # 获取当前的系统运行时间 (ticks)
    current_time = ctypes.windll.kernel32.GetTickCount()

    # 计算空闲时间（毫秒）
    idle_time_ms = current_time - last_input_info.dwTime

    # 转换为秒
    return idle_time_ms // 1000


def is_user_active_windows(idle_threshold=5):
    """
    判断用户当前是否处于活跃状态。
    
    Args:
        idle_threshold (int): 允许的最大空闲时间（秒）。默认为 5 秒。
        
    Returns:
        bool: 如果用户活跃，返回 True；否则返回 False。
    """
    idle_time = get_idle_time()
    return idle_time <= idle_threshold

    
def is_user_active_linux():
    try:
        idle_time = int(subprocess.check_output([XPRINTIDLE]).strip()) / 1000  # 转换为秒
        return idle_time < 5
    except Exception as e:
        logger.warning(f"Error getting user idle time on Linux: {e}")
        return True


def is_user_active():
    if sys.platform == WINDOWS:
        return is_user_active_windows()
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
    
def get_folder_paths(path, days_ago_min, days_ago_max):
    """
    获取指定路径下，距离当前日期在 min_days_ago 和 max_days_ago 天之间的文件夹路径列表。
    """
    folder_paths = []
    now = datetime.datetime.now()
    for root, dirs, files in os.walk(path):
        for dir_name in dirs:
            folder_path = os.path.join(root, dir_name)
            # 检查是否是三级子文件夹
            if folder_path.count(os.sep) - path.count(os.sep) == 3:
                # 截取文件夹名最后三级，即yyyy/mm/dd三层
                day = os.path.basename(folder_path)
                month = os.path.basename(os.path.dirname(folder_path))
                year = os.path.basename(os.path.dirname(os.path.dirname(folder_path)))
                last_three_parts = f"{year}/{month}/{day}"
                try:
                    folder_date = datetime.datetime.strptime(last_three_parts, "%Y/%m/%d")
                    days_ago = (now - folder_date).days
                    if days_ago_min <= days_ago <= days_ago_max:
                        folder_paths.append(folder_path)
                except ValueError:
                    # 忽略无法解析为日期的文件夹
                    pass
    return folder_paths

# 获取 CPU 温度
def get_cpu_temperature():
    #如果是Windows下，则直接返回
    if sys.platform == WINDOWS:
        return None
    try:
        temperatures = psutil.sensors_temperatures()
        if 'coretemp' in temperatures:
            for entry in temperatures['coretemp']:
                if entry.label == 'Package id 0':
                    return entry.current
    except Exception as e:
        logger.warning(f"Error getting CPU temperature: {e}")
    return None


class ImageVideoTool:
    def __init__(self, 
                 image_folder: str,
                 output_video: str = RECORD_NAME, 
                 framerate: int = 30, 
                 crf: int = 23, 
                 resolution: Optional[str] = None):
        """
        :param output_video: 输出视频路径
        :param framerate: 帧率（默认30fps）
        :param crf: 压缩质量（18-28，越小质量越高）<button class="citation-flag" data-index="3"><button class="citation-flag" data-index="6">
        :param resolution: 输出分辨率（格式如"1280x720"，默认保持原图尺寸）
        """
        self.image_folder = image_folder
        self.output_video = os.path.join(self.image_folder, output_video)
        self.framerate = framerate
        self.crf = crf
        self.resolution = resolution
        self.mapping_file = os.path.join(self.image_folder, f"{output_video}.csv")
        self.cap = cv2.VideoCapture(self.output_video)
        self.max_frame_num = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        
    def is_backed_up(self):
        return os.path.exists(self.mapping_file)
    
    def get_image_count(self):
        return len(os.listdir(self.image_folder))
    
    def get_folder_size(self):
        from pathlib import Path
        
        folder = Path(self.image_folder)
        
        # 递归遍历所有文件并计算总大小
        total_size = sum(file.stat().st_size for file in folder.rglob("*") if file.is_file())
        size_in_mb = total_size / (1024 ** 2)
        size_in_mb = round(size_in_mb, 2)
        size_in_gb = total_size / (1024 ** 3)
        size_in_gb = round(size_in_gb, 2)
        # 如果size_in_gb小于小数点后两位，则采用size_in_mb
        if size_in_gb < 1:
            return str(size_in_mb) + "MB"
        else:
            return str(size_in_gb) + "GB"

    def images_to_video(self, 
                        sort_by: str = "name", 
                        image_extensions: List[str] = [".jpg", ".jpeg", ".png",".webp"],
                        ):
        """
        将文件夹内所有图片转为视频（支持多格式、智能排序）
        :param image_folder: 图片文件夹路径
        :param sort_by: 排序方式（"name"/"time"/"custom"）<button class="citation-flag" data-index="8">
        :param image_extensions: 支持的图片格式列表
        """
        # 1. 收集并过滤图片
        images = []
        for file in os.listdir(self.image_folder):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                # 要求文件大小大于0字节
                if os.path.getsize(os.path.join(self.image_folder, file)) > 0:
                    images.append(file)
                else:
                    #删除空文件
                    os.remove(os.path.join(self.image_folder, file))
        
        if not images:
            raise FileNotFoundError("No valid images found in folder")
        
        # 2. 排序逻辑
        if sort_by == "name":
            images = sorted(images)  # 按文件名排序（需规范命名如image_001.jpg）<button class="citation-flag" data-index="8">
        elif sort_by == "time":
            images = sorted(images, key=lambda x: os.path.getmtime(os.path.join(self.image_folder, x)))
        elif sort_by == "custom":
            # 可扩展自定义排序逻辑（如按EXIF时间）
            pass
        else:
            raise ValueError("sort_by must be 'name', 'time' or 'custom'")
        
        # 3. 重命名图片文件
        renamed_images = []
        for idx, img in enumerate(images):
            old_path = os.path.join(self.image_folder, img)
            new_filename = f"{idx + 1:03d}.webp"
            new_path = os.path.join(self.image_folder, new_filename)
            os.rename(old_path, new_path)
            renamed_images.append(new_filename)

        # 4. 生成映射表（含时间戳和元数据）<button class="citation-flag" data-index="6"><button class="citation-flag" data-index="10">
        with open(self.mapping_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "timestamp", "frame_number"])
            for idx, img in enumerate(images):
                timestamp = timedelta(seconds=idx/self.framerate)
                writer.writerow([img, str(timestamp), idx+1])

        # 5. 读取第一张图片获取尺寸
        # first_image_path = os.path.join(self.image_folder, renamed_images[0])
        # first_image = cv2.imread(first_image_path)
        # height, width, _ = first_image.shape

        # 6. 生成视频
        # fourcc = cv2.VideoWriter_fourcc(*'H264')  # 设置编码格式
        # out = cv2.VideoWriter(self.output_video, fourcc, self.framerate, (width, height))  # 创建视频写入对象

        # for img in renamed_images:
        #     img_path = os.path.join(self.image_folder, img)
        #     frame = cv2.imread(img_path)
        #     out.write(frame)  # 写入帧

        # out.release()  # 释放视频写入对象
        command = [
            "ffmpeg",
            "-framerate", f"{self.framerate}",          # 输入帧率
            "-i", self.image_folder + "/%03d.webp",         # 输入文件名模式
            "-c:v", "h264",           # 视频编码器
            "-crf", f"{self.crf}",            # CRF值（视频质量）
            "-preset", "medium",       # 编码速度（慢=高质量）
            "-y", self.output_video
        ]

        try:
            result = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True  # 自动检查错误
            )
            logger.info("STDOUT:", result.stdout.decode())
        except subprocess.CalledProcessError as e:
            logger.warning("FFmpeg Error:", e.stderr.decode())
            raise
        
        # 7. 删除重命名后的图片
        for img in renamed_images:
            os.remove(os.path.join(self.image_folder, img))

        logger.info(f"Video created: {self.output_video}, mapping saved to {self.mapping_file}")

    def query_image(self, target_image: str):
        """
        通过图片名称查询并提取对应帧（支持模糊匹配）<button class="citation-flag" data-index="3"><button class="citation-flag" data-index="10">
        :param target_image: 要查询的图片名称（支持全名或部分匹配）
        :param image_name: 提取帧的图片名称
        :return: 是否找到并提取成功
        """
        # 1. 动态设置output_video和mapping_file路径
        # 1. 读取映射表
        mapping = {}
        try:
            with open(self.mapping_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    mapping[row["filename"]] = {
                        "timestamp": row["timestamp"],
                        "frame_number": row["frame_number"]
                    }
        except FileNotFoundError:
            logger.error("Mapping file not found. Please run images_to_video first.")
            return None
        
        # 2. 模糊匹配（支持不完整文件名）<button class="citation-flag" data-index="10">
        matches = [k for k in mapping.keys() if target_image in k]
        if not matches:
            logger.warning(f"No match found for: {target_image}")
            return None
        if len(matches) > 1:
            logger.warning(f"Multiple matches found: {matches}. Using first match.")
        target = matches[0]
        
        # 3. 提取帧（使用OpenCV优化效率）<button class="citation-flag" data-index="5"><button class="citation-flag" data-index="6">
        
        frame_num = int(mapping[target]["frame_number"])
        print(f"max_frame_num: {self.max_frame_num},frame_num: {frame_num}")
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num - 1)
        ret, frame = self.cap.read()
        if ret:
            _, buffer = cv2.imencode('.jpg', frame,[cv2.IMWRITE_JPEG_QUALITY, 90])
            byte_stream = io.BytesIO(buffer.tobytes())
            return byte_stream
        else:
            logger.error("Failed to extract frame")
            return None
        
if __name__ == "__main__":
    
    # text = "这是一个超大的字符串示例，包含一些关键词如apple、banana、cherry和date。"
    # keywords = ["app22le", "b33anana", "ch33erry", "d22ate", "egg11"]
    # result = count_unique_keywords(text, keywords)
    import time
    start_time = time.time()
    tool = ImageVideoTool("/home/liuwenwu/.local/share/MemoCoco/screenshots/2025/03/24")
    # # 转换图片（按文件名排序）
    tool.images_to_video( sort_by="name")
    # time.sleep(1)
    end_time = time.time()
    print(f"程序加载工具：{end_time - start_time:.2f}秒")
    # start_time = time.time()
    # byte_stream = tool.query_image("1739516282")
    # if byte_stream:
    #     # 提取图片（支持模糊查询）
    #     end_time = time.time()
    #     print(f"程序提取图像：{end_time - start_time:.2f}秒")
    # else:
    #     print("未找到匹配的图片")
    # end_time = time.time()
    # print(f"程序加载工具：{end_time - start_time:.2f}秒")
    # start_time = time.time()
    # byte_stream = tool.query_image("1739516688")
    # if byte_stream:
    #     # 提取图片（支持模糊查询）
    #     end_time = time.time()
    #     print(f"程序提取图像：{end_time - start_time:.2f}秒")
    # else:
    #     print("未找到匹配的图片")