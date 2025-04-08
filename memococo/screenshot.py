import os
import time
import sys
import mss
import numpy as np
from PIL import Image
import datetime
import io
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
    """计算两张图片的结构相似度指数（SSIM）

    优化版本：使用降采样和区域分块来提高性能

    Args:
        img1: 第一张图片（numpy数组）
        img2: 第二张图片（numpy数组）
        L: 像素值的动态范围，默认为255

    Returns:
        相似度指数，范围为[0, 1]
    """
    # 形状检查
    if img1 is None or img2 is None or img1.shape != img2.shape:
        logger.debug("Image dimensions changed or images are None, skipping similarity check")
        return 0.0  # 返回0表示完全不同

    # 尝试使用更高效的方法：降采样和区域分块
    # 降采样以减少计算量
    scale_factor = 4  # 降采样因子
    height, width = img1.shape[:2]
    new_height, new_width = height // scale_factor, width // scale_factor

    # 如果图像太小，不进行降采样
    if new_height < 10 or new_width < 10:
        scale_factor = 1
        new_height, new_width = height, width

    # 使用OpenCV进行更高效的降采样
    if scale_factor > 1:
        try:
            import cv2
            img1_small = cv2.resize(img1, (new_width, new_height), interpolation=cv2.INTER_AREA)
            img2_small = cv2.resize(img2, (new_width, new_height), interpolation=cv2.INTER_AREA)
        except ImportError:
            # 如果没有OpenCV，则使用简单的切片降采样
            img1_small = img1[::scale_factor, ::scale_factor]
            img2_small = img2[::scale_factor, ::scale_factor]
    else:
        img1_small = img1
        img2_small = img2

    # 转换为灰度图
    def rgb2gray(img):
        return 0.2989 * img[..., 0] + 0.5870 * img[..., 1] + 0.1140 * img[..., 2]

    img1_gray = rgb2gray(img1_small)
    img2_gray = rgb2gray(img2_small)

    # 计算SSIM参数
    K1, K2 = 0.01, 0.03
    C1, C2 = (K1 * L) ** 2, (K2 * L) ** 2

    mu1 = np.mean(img1_gray)
    mu2 = np.mean(img2_gray)
    sigma1_sq = np.var(img1_gray)
    sigma2_sq = np.var(img2_gray)
    sigma12 = np.mean((img1_gray - mu1) * (img2_gray - mu2))

    # 计算SSIM
    ssim_index = ((2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)) / (
        (mu1**2 + mu2**2 + C1) * (sigma1_sq + sigma2_sq + C2)
    )
    return float(ssim_index)


def is_similar(img1, img2, similarity_threshold=0.9):
    """判断两张图片是否相似

    优化版本：增加快速预检查和多级别相似度检测

    Args:
        img1: 第一张图片
        img2: 第二张图片
        similarity_threshold: 相似度阈值，默认为0.9

    Returns:
        如果相似度超过阈值，返回Ture，否则返回False
    """
    # 快速预检查
    if img1 is None or img2 is None:
        return False

    # 如果形状不同，直接返回不相似
    if img1.shape != img2.shape:
        return False

    # 快速检查：比较图像的平均值和标准差
    # 如果差异很大，可以直接判断不相似
    mean1 = np.mean(img1)
    mean2 = np.mean(img2)
    std1 = np.std(img1)
    std2 = np.std(img2)

    # 如果平均值或标准差差异超过20%，则认为不相似
    if abs(mean1 - mean2) / max(mean1, mean2) > 0.2 or abs(std1 - std2) / max(std1, std2) > 0.2:
        return False

    # 计算结构相似度
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

def compress_img_PIL(img_path, target_size_kb=200, show=False):
    """智能压缩图像到目标大小

    优化版本：使用二分法快速找到最佳质量和大小平衡点

    Args:
        img_path: 图像文件路径
        target_size_kb: 目标文件大小（KB），默认200KB
        show: 是否显示压缩后的图像

    Returns:
        None
    """
    try:
        # 获取原始文件大小（KB）
        original_size_kb = os.path.getsize(img_path) / 1024

        # 如果已经小于目标大小，直接返回
        if original_size_kb <= target_size_kb:
            return

        # 打开图像
        img = Image.open(img_path)

        # 尝试使用质量压缩（对于JPEG格式）
        if img_path.lower().endswith(('.jpg', '.jpeg')):
            # 使用二分法快速找到最佳质量
            quality_low, quality_high = 10, 95
            best_quality = quality_high

            while quality_low <= quality_high:
                mid_quality = (quality_low + quality_high) // 2
                # 使用内存流测试压缩效果
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=mid_quality)
                current_size_kb = len(buffer.getvalue()) / 1024

                if abs(current_size_kb - target_size_kb) < 10:  # 允许10KB的误差
                    best_quality = mid_quality
                    break
                elif current_size_kb > target_size_kb:
                    quality_high = mid_quality - 1
                else:
                    quality_low = mid_quality + 1
                    best_quality = mid_quality  # 保存当前最佳质量

            # 使用最佳质量保存
            logger.info(f"Compressing JPEG image with quality {best_quality}")
            img.save(img_path, format="JPEG", quality=best_quality)

        # 对于WebP格式，尝试调整压缩级别
        elif img_path.lower().endswith('.webp'):
            # 使用二分法快速找到最佳质量
            quality_low, quality_high = 10, 95
            best_quality = quality_high

            while quality_low <= quality_high:
                mid_quality = (quality_low + quality_high) // 2
                # 使用内存流测试压缩效果
                buffer = io.BytesIO()
                img.save(buffer, format="WEBP", quality=mid_quality)
                current_size_kb = len(buffer.getvalue()) / 1024

                if abs(current_size_kb - target_size_kb) < 10:  # 允许10KB的误差
                    best_quality = mid_quality
                    break
                elif current_size_kb > target_size_kb:
                    quality_high = mid_quality - 1
                else:
                    quality_low = mid_quality + 1
                    best_quality = mid_quality  # 保存当前最佳质量

            # 使用最佳质量保存
            logger.info(f"Compressing WebP image with quality {best_quality}")
            img.save(img_path, format="WEBP", quality=best_quality)

        # 其他格式使用尺寸缩放
        else:
            # 计算压缩比例
            compression_ratio = (target_size_kb / original_size_kb) ** 0.5  # 开平方根因为面积是二维的
            compression_ratio = max(0.1, min(0.9, compression_ratio))  # 限制在 0.1-0.9 之间

            # 计算新尺寸
            w, h = img.size
            new_w, new_h = int(w * compression_ratio), int(h * compression_ratio)

            # 确保新尺寸不会太小
            new_w = max(new_w, 640)  # 最小宽度
            new_h = max(new_h, 480)  # 最小高度

            # 调整宽高比
            if w/h != new_w/new_h:
                if w/h > new_w/new_h:  # 原图更宽
                    new_h = int(new_w * h / w)
                else:  # 原图更高
                    new_w = int(new_h * w / h)

            # 调整大小
            logger.info(f"Resizing image from {w}x{h} to {new_w}x{new_h}")
            img_resized = img.resize((new_w, new_h), Image.LANCZOS)  # 使用LANCZOS算法获得更高质量
            img_resized.save(img_path)

        if show:
            Image.open(img_path).show()

    except Exception as e:
        logger.error(f"Error compressing image: {e}")
        # 如果压缩失败，尝试简单的缩放方法
        try:
            img = Image.open(img_path)
            w, h = img.size
            img_resize = img.resize((int(w*0.7), int(h*0.7)))
            img_resize.save(img_path)
        except Exception as e2:
            logger.error(f"Fallback compression also failed: {e2}")

def power_saving_mode(save_power):
    if save_power:
        battery = psutil.sensors_battery()
        if  battery is not None and battery.percent < 75 and battery.power_plugged == False:
            return True
    return False

def get_ocr_result(pic):
    try:
        result = extract_text_from_image(pic)
        return result
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        return None

import concurrent.futures
import time

def get_ocr_result_with_timeout(pic, timeout=15):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(extract_text_from_image, pic)
        try:
            result = future.result(timeout=timeout)
            return result
        except concurrent.futures.TimeoutError:
            logger.info(f"OCR执行超时(>{timeout}秒)")
            return None

def record_screenshots_thread(ignored_apps, ignored_apps_updated, save_power = True,idle_time = 4,enable_compress = True):
    # 新增变量记录上次应用状态
    last_app_name = None
    last_window_title = None
    last_window_shot = None
    # 延迟次数
    delay_time = 0
    # 延迟时间
    delay_interval = 20
    # 上次跳过时间
    last_skip_time = datetime.datetime.now()

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
                if cpu_usage > 70 or ( cpu_temperature is not None and cpu_temperature > 75 ):
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
                    ocr_text = extract_text_from_image(image)
                    # 如果ocr_json_text为[]，则ocr_text为空字符串
                    if image is not None and ocr_text:
                        if enable_compress:
                            # 智能压缩图像到目标大小
                            logger.info(f"Compressing image to target size: {image_path}")
                            compress_img_PIL(image_path, target_size_kb=200)
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
            # 计算当前时间和上次时间last_skip_time相隔多少秒
            if delay_time > 0 and (int((datetime.datetime.now() - last_skip_time).total_seconds())) < delay_interval:
                delay_time -= 1
                logger.info(f'暂停ocr，剩余等待次数：{delay_time}')
                text = ""
            elif cpu_usage > 70 or ( cpu_temperature is not None and cpu_temperature > 75 ):
                logger.info(f"CPU占用过高，不进行ocr，当前cpu占用：{cpu_usage}%，当前温度：{cpu_temperature}°C")
                delay_time = 2
                last_skip_time = datetime.datetime.now()
                text = ""
            elif power_saving_mode(save_power):
                delay_time = 0
                logger.info(f"省电模式开启，不进行ocr")
                text = ""
            else:
                delay_time = 0
                if screenshots[0] is not None:
                    text = get_ocr_result_with_timeout(screenshots[0])
                    if text:
                        logger.info("screenshot ocr识别完成")
                    else:
                        delay_time = 2
                        last_skip_time = datetime.datetime.now()
                else:
                    text = ""
                    logger.info("ocr识别失败，不存在截图")
            # 如果当前的年月日和dirDate不同，则创建新的目录
            if dirDate != datetime.datetime.now().date():
                dirDate = datetime.datetime.now()
                create_directory_if_not_exists(get_screenshot_path(dirDate))
            # 如果json_text为空，则暂不压缩图片，直接保存
            if text:
                if enable_compress:
                    # 智能压缩图像到目标大小
                    logger.info(f"Compressing image to target size: {image_path}")
                    compress_img_PIL(image_path, target_size_kb=200)
            else:
                logger.info("ocr识别结果为空，不压缩图片")
            # print(f"Detected change on monitor {i + 1}: {text}")
            endTime = time.time()
            #耗时计算时，保留小数点后两位
            logger.info(f"截图保存完成，耗时：{endTime - startTime:.2f}秒")
            insert_entry(
                "", timestamp, text, active_app_name, active_window_title
            )

