import os
import time
import sys
import mss
import numpy as np
from PIL import Image
import datetime
from memococo.config import screenshots_path, args,app_name_en,app_name_cn,logger,get_settings
from memococo.database import insert_entry,get_newest_empty_text,update_entry_text,remove_entry
import subprocess
from memococo.ocr import extract_text_from_image
import pyautogui
import psutil
from memococo.utils import (
    get_active_app_name,
    get_active_window_title,
    is_user_active,
    ImageVideoTool,
    get_cpu_temperature
)

WINDOWS = "win32"
LINUX = "linux"
MACOS = "darwin"

def get_screenshot_path(date):
    return os.path.join(screenshots_path, date.strftime("%Y/%m/%d"))

def create_directory_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        

def mean_structured_similarity_index(img1, img2, L=255):
    # 新增形状检查
    if img1.shape != img2.shape:
        logger.debug("Image dimensions changed, skipping similarity check")
        return 0.0  # 返回0表示完全不同
    
    K1, K2 = 0.01, 0.03
    C1, C2 = (K1 * L) ** 2, (K2 * L) ** 2

    def rgb2gray(img):
        return 0.2989 * img[..., 0] + 0.5870 * img[..., 1] + 0.1140 * img[..., 2]

    img1_gray = rgb2gray(img1)
    img2_gray = rgb2gray(img2)
    mu1 = np.mean(img1_gray)
    mu2 = np.mean(img2_gray)
    sigma1_sq = np.var(img1_gray)
    sigma2_sq = np.var(img2_gray)
    sigma12 = np.mean((img1_gray - mu1) * (img2_gray - mu2))
    ssim_index = ((2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)) / (
        (mu1**2 + mu2**2 + C1) * (sigma1_sq + sigma2_sq + C2)
    )
    return ssim_index


def is_similar(img1, img2, similarity_threshold=0.9):
    #如果有一个图像为None，则返回False
    if img1 is None or img2 is None:
        return False
    similarity = mean_structured_similarity_index(img1, img2)
    return similarity >= similarity_threshold

def take_active_on_windows():
    from PIL import ImageGrab
    import pygetwindow as gw
    """
    截取当前活动窗口的屏幕截图，并以 numpy 数组的形式返回。
    
    Returns:
        np.ndarray: 当前活动窗口的截图数据（RGB 格式）。
    """
    try:
        # 获取当前活动窗口
        active_window = gw.getActiveWindow()
        if active_window is None:
            raise ValueError("无法获取当前活动窗口，请确保有活动窗口存在。")
        
        # 获取活动窗口的边界 (left, top, width, height)
        left, top, width, height = active_window.left, active_window.top, active_window.width, active_window.height
        
        # 使用 Pillow 的 ImageGrab 截取指定区域
        screenshot = ImageGrab.grab(bbox=(left, top, left + width, top + height))
        
        # 将截图转换为 numpy 数组 (RGB 格式)
        screenshot_array = np.array(screenshot)
        
        return screenshot_array
    
    except Exception as e:
        print(f"发生错误: {e}")
        return None

def take_active_on_linux():
    try:
        window_id = subprocess.check_output(['xdotool', 'getactivewindow']).strip()
        window_geometry = subprocess.check_output(['xdotool', 'getwindowgeometry', '--shell', window_id]).decode()
        window_geometry = dict(line.split('=') for line in window_geometry.split('\n') if '=' in line)
        x = int(window_geometry['X'])
        y = int(window_geometry['Y'])
        width = int(window_geometry['WIDTH'])
        height = int(window_geometry['HEIGHT'])
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        return np.array(screenshot)
    except Exception as e:
        logger.error(f"Error taking screenshot of active window: {e}")
    return None

def take_active_window_screenshot():
    if sys.platform == WINDOWS:
        return take_active_on_windows()
    elif sys.platform == MACOS:
        return take_active_on_linux()
    elif sys.platform.startswith(LINUX):
        return take_active_on_linux()
    else:
        raise NotImplementedError("This platform is not supported")

def take_screenshots(monitor=1):
    screenshots = []

    with mss.mss() as sct:
        for monitor in range(len(sct.monitors)):

            if args.primary_monitor_only and monitor != 1:
                continue

            monitor_ = sct.monitors[monitor]
            screenshot = np.array(sct.grab(monitor_))
            screenshot = screenshot[:, :, [2, 1, 0]]
            screenshots.append(screenshot)
    active_window_screenshot = take_active_window_screenshot()
    # 如果screenshots数量大于2,则将screenshots列表中相似度超过95%的图片删除
    if len(screenshots) >= 2:
        for i in range(len(screenshots)):
            for j in range(i+1, len(screenshots)):
                if is_similar(screenshots[i], screenshots[j]):
                    screenshots.pop(j)
                    break
    if active_window_screenshot is not None:
        screenshots.append(active_window_screenshot)

                
    return screenshots

def compress_img_PIL(img_path, compress_rate=0.9, show=False):
        img = Image.open(img_path)
        w, h = img.size
        img_resize = img.resize((int(w*compress_rate), int(h*compress_rate)))
        logger.info("compressing image")
        img_resize.save(img_path)
        # 保存到img_path
        if show:
            img_resize.show()  # 在照片应用中打开图片

def power_saving_mode(save_power):
    if save_power:
        battery = psutil.sensors_battery()
        if  battery is not None and battery.percent < 75 and battery.power_plugged == False:
            return True
    return False

import threading
import time

# 自定义异常类，用于表示超时错误
class TimeoutException(Exception):
    pass

# 超时上下文管理器
class timeout:
    def __init__(self, seconds):
        self.seconds = seconds
        self.timer_thread = None
        self.exc = None

    def __enter__(self):
        # 定义一个定时器线程，在超时时抛出异常
        def raise_timeout():
            self.exc = TimeoutException(f"Execution timed out after {self.seconds} seconds")
        
        self.timer_thread = threading.Timer(self.seconds, raise_timeout)
        self.timer_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 停止定时器线程
        if self.timer_thread:
            self.timer_thread.cancel()

        # 如果超时异常被触发，则抛出异常
        if self.exc:
            raise self.exc

        # 返回 False 表示不抑制其他异常
        return False

def get_ocr_result(pic,ocr_engine):
    try:
        with timeout(12):
            result = extract_text_from_image(pic,ocr_engine)
            return result
    except TimeoutException:
        logger.info("OCR执行超时(>12秒)")
        return None
        
    

def record_screenshots_thread(ignored_apps, ignored_apps_updated, save_power = True,idle_time = 4,enable_compress = True):
    # 新增变量记录上次应用状态
    last_app_name = None
    last_window_title = None
    last_window_shot = None
    delay_time = 0
    
    dirDate = datetime.datetime.now()
    create_directory_if_not_exists(get_screenshot_path(dirDate))
    logger.info("Started recording screenshots...")
    last_screenshots = take_screenshots()
    user_inactive_logged = False  # 添加标志位记录上一次用户是否处于非活动状态
    last_user_active_time = datetime.datetime.now()  # 添加变量记录上一次用户活动时间
    default_idle_time = idle_time
    # 间隔时间为4秒
    while True:
        time.sleep(idle_time)
        if ignored_apps_updated.is_set():
            ignored_apps_updated.clear()
            logger.info(f"Updated ignored_apps: {ignored_apps}")
        if not is_user_active():
            if not user_inactive_logged:
                logger.info("User is inactive, sleeping...")
                idle_time = 3
                user_inactive_logged = True
            #如果距离上次用户活动时间超过3分钟，则开始OCR任务
            if (datetime.datetime.now() - last_user_active_time).total_seconds() > 30:
                cpu_usage = psutil.cpu_percent(interval=1)
                cpu_temperature = get_cpu_temperature()
                # logger.info(f"cpu占用：{cpu_usage}%，当前温度：{cpu_temperature}°C")
                # 如果cpu占用率大于70%或者温度高于70度，则增加idle_time来避免高温降频
                if cpu_usage > 70 or ( cpu_temperature is not None and cpu_temperature > 70 ):
                    logger.info(f"cpu占用率过高，当前idle_time为{idle_time}")
                    idle_time += 1
                # 如果处于省电模式，则跳过OCR任务
                if power_saving_mode(save_power):
                    continue
                entry = get_newest_empty_text()
                if entry:
                    logger.info(f"Processing entry: {entry}")
                    # 将entry.timestamp转换为datetime对象
                    screenshot_path = get_screenshot_path(datetime.datetime.fromtimestamp(entry.timestamp))
                    tool = ImageVideoTool(screenshot_path)
                    if tool.is_backed_up():
                        logger.info("images have been backed up")
                        image_stream = tool.query_image(str(entry.timestamp))
                        # 使用 PIL 的 Image 类将字节流读取为图像对象
                        image = Image.open(image_stream)
                    else:
                        logger.info("images have not been backed up")
                        image_path = os.path.join(screenshot_path, f"{entry.timestamp}.webp")
                        image = Image.open(image_path)
                    # 将图片转为nparray
                    image = np.array(image)
                    ocr_text = extract_text_from_image(image,ocr_engine = get_settings()['ocr_tool'])
                    # 如果ocr_json_text为[]，则ocr_text为空字符串
                    if image is not None and ocr_text:
                        if enable_compress:
                            while True:
                                # print(f"File size: {os.path.getsize(image_path) / 1024} KB, File name: {image_path}")
                                if os.path.getsize(image_path) <= 200 * 1024:
                                    break
                                compress_img_PIL(image_path)
                        update_entry_text(entry.id, ocr_text, "")
                        logger.info("ocr task finished")
                    else:
                        logger.info("Image is None")
                        remove_entry(entry.id)
            continue
        else:
            user_inactive_logged = False
            idle_time = default_idle_time
            last_user_active_time = datetime.datetime.now()  # 更新用户活动时间
        active_app_name = get_active_app_name()
        active_window_title = get_active_window_title()

        #如果window_title为空或为None，但app_name不为空,则将window_title设置为app_name
        if not active_window_title and active_app_name:
            active_window_title = active_app_name
        if active_app_name in ignored_apps:
            continue
        
        #如果window title是appName，则不插入数据库
        if active_window_title == app_name_cn or active_window_title == app_name_en:
            continue
        
        screenshots = take_screenshots()
        last_screenshot = last_screenshots[0]
        window_shot = screenshots[-1] if len(screenshots) > 1 else screenshots[0]
        # 新增应用状态比较逻辑
        app_changed = (active_app_name != last_app_name) or (active_window_title != last_window_title)
        should_save = False
        if app_changed:
            should_save = True
        else:
            # 当应用未变化时进行图像相似度比较
            if last_window_shot is not None and window_shot is not None:
                should_save = not is_similar(window_shot, last_window_shot) and not is_similar(last_screenshot,screenshots[0])
            else:
                # 初次运行或截图获取失败时强制保存
                should_save = True
        logger.info(f'{active_app_name} {active_window_title} {should_save} , {app_changed}')
        if should_save:
            startTime = time.time()
            logger.info("Screenshot changed, saving...")
            
            # 更新最后保存的截图和应用状态
            last_app_name = active_app_name
            last_window_title = active_window_title
            last_window_shot = window_shot.copy() if window_shot is not None else None

            # 保存完整截图和windows的OCR
            image = Image.fromarray(screenshots[0])
            timestamp = int(time.time())
            image_path = os.path.join(get_screenshot_path(dirDate), f"{timestamp}.webp")
            image.save(image_path, format="webp", lossless=True)
            
            # 如果系统cpu占用过高，则不进行ocr
            cpu_usage = psutil.cpu_percent(interval=1)
            cpu_temperature = get_cpu_temperature()
            if cpu_usage > 70 or ( cpu_temperature is not None and cpu_temperature > 70 ):
                logger.info(f"CPU占用过高，不进行ocr，当前cpu占用：{cpu_usage}%，当前温度：{cpu_temperature}°C")
                delay_time = 10
                text = ""
            elif power_saving_mode(save_power):
                logger.info(f"省电模式开启，不进行ocr")
                text = ""
            elif delay_time > 0:
                logger.info(f'暂停ocr，剩余等待次数：{delay_time}')
                text = ""
                delay_time -= 1
            else:
                if window_shot is not None:
                    text = get_ocr_result(window_shot,ocr_engine = get_settings()['ocr_tool'])
                    logger.info("window_shot ocr识别完成")
                elif screenshots[0] is not None:
                    text = get_ocr_result(screenshots[0],ocr_engine = get_settings()['ocr_tool'])
                    logger.info("screenshot ocr识别完成")
                else:
                    text = ""
                    delay_time = 10
                    logger.info("ocr识别失败，不存在截图")
            # 如果当前的年月日和dirDate不同，则创建新的目录
            if dirDate != datetime.datetime.now().date():
                dirDate = datetime.datetime.now()
                create_directory_if_not_exists(get_screenshot_path(dirDate))
            # 如果json_text为空，则暂不压缩图片，直接保存
            if text:
                if enable_compress:
                    # 逐步降低图像的质量，直到图像的大小小于200k
                    while True:
                        # print(f"File size: {os.path.getsize(image_path) / 1024} KB, File name: {image_path}")
                        compress_img_PIL(image_path)
                        if os.path.getsize(image_path) <= 200 * 1024:
                            break
            else:
                logger.info("ocr识别结果为空，不压缩图片")
            # print(f"Detected change on monitor {i + 1}: {text}")
            endTime = time.time()
            #耗时计算时，保留小数点后两位
            logger.info(f"截图保存完成，耗时：{endTime - startTime:.2f}秒")
            insert_entry(
                "", timestamp, text, active_app_name, active_window_title
            )

