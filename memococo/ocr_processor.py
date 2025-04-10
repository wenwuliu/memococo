"""
OCR处理模块

负责从数据库查询未OCR的数据，进行OCR处理，然后将结果保存回数据库
支持多线程批量处理，提高处理效率
"""

import os
import time
import datetime
import threading
import concurrent.futures
import multiprocessing
import numpy as np
from PIL import Image

from memococo.config import ocr_logger, screenshots_path
from memococo.database import get_batch_empty_text, update_entry_text, remove_entry, get_empty_text_count
from memococo.ocr import extract_text_from_image
from memococo.utils import ImageVideoTool, get_cpu_temperature

# 获取CPU核心数，用于设置线程池大小
_cpu_count = multiprocessing.cpu_count()

# 全局线程池，用于处理OCR任务
# 为了避免系统卡顿，将线程数限制为CPU核心数的一半
# 这样可以确保系统有足够的资源处理其他任务
_ocr_thread_count = max(1, _cpu_count // 2)  # 至少使用1个线程
_ocr_executor = concurrent.futures.ThreadPoolExecutor(max_workers=_ocr_thread_count)

# OCR处理的启动和停止阈值
# 当需要OCR的条目数量大于该值时启动OCR处理
_OCR_START_THRESHOLD = 50
# 当需要OCR的条目数量小于该值时停止OCR处理
_OCR_STOP_THRESHOLD = 5

# OCR处理状态，用于控制OCR处理的启动和停止
_ocr_processing_enabled = True

def get_screenshot_path(date):
    """获取指定日期的截图路径

    Args:
        date: 日期对象

    Returns:
        截图路径
    """
    return os.path.join(screenshots_path, date.strftime("%Y/%m/%d"))

def process_ocr_task(entry):
    """处理单个OCR任务

    改进版本：
    1. 增强错误处理和日志记录
    2. 当图片不存在时直接删除数据库条目
    3. 在处理过程中检查CPU使用率，避免系统卡顿

    Args:
        entry: 数据库条目

    Returns:
        OCR结果，如果失败则返回None
        如果返回特殊值'DELETED'，表示条目已被删除
        如果返回特殊值'SKIPPED'，表示由于系统负载过高而跳过处理
    """
    # 先检查CPU使用率，避免系统卡顿
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_temperature = get_cpu_temperature()

        # 如果CPU占用率超过50%或温度超过70度，跳过本次OCR
        if cpu_percent > 50 or (cpu_temperature is not None and cpu_temperature > 70):
            ocr_logger.warning(f"Skipping OCR task for entry {entry.id} due to high system load: CPU usage {cpu_percent}%, temperature {cpu_temperature}°C")
            return "SKIPPED"
    except (ImportError, Exception) as e:
        ocr_logger.warning(f"Failed to check CPU stats in OCR task: {e}")

    try:
        # 将entry.timestamp转换为datetime对象
        timestamp_dt = datetime.datetime.fromtimestamp(entry.timestamp)
        screenshot_path = get_screenshot_path(timestamp_dt)
        ocr_logger.info(f"Processing OCR for entry {entry.id}, timestamp: {entry.timestamp} ({timestamp_dt})")

        # 检查目录是否存在
        if not os.path.exists(screenshot_path):
            ocr_logger.error(f"Screenshot path does not exist: {screenshot_path}, deleting entry {entry.id}")
            remove_entry(entry.id)
            return "DELETED"

        tool = ImageVideoTool(screenshot_path)

        # 获取图像
        image = None
        image_path = os.path.join(screenshot_path, f"{entry.timestamp}.webp")

        try:
            if tool.is_backed_up():
                ocr_logger.info(f"Images have been backed up for entry {entry.id}")
                try:
                    image_stream = tool.query_image(str(entry.timestamp))
                    # 使用PIL的Image类将字节流读取为图像对象
                    image = Image.open(image_stream)
                except Exception as e:
                    ocr_logger.error(f"Error querying backed up image for entry {entry.id}: {e}")
                    # 如果备份图片查询失败，尝试从原始文件读取
                    if os.path.exists(image_path):
                        image = Image.open(image_path)
                    else:
                        ocr_logger.error(f"Image file does not exist: {image_path}, deleting entry {entry.id}")
                        remove_entry(entry.id)
                        return "DELETED"
            else:
                ocr_logger.info(f"Loading image from file: {image_path}")
                if not os.path.exists(image_path):
                    ocr_logger.error(f"Image file does not exist: {image_path}, deleting entry {entry.id}")
                    remove_entry(entry.id)
                    return "DELETED"
                image = Image.open(image_path)
        except IOError as e:
            ocr_logger.error(f"Error opening image for entry {entry.id}: {e}, deleting entry")
            remove_entry(entry.id)
            return "DELETED"

        if image is None:
            ocr_logger.error(f"Failed to load image for entry {entry.id}, deleting entry")
            remove_entry(entry.id)
            return "DELETED"

        # 将图片转为nparray
        try:
            image_array = np.array(image)
        except Exception as e:
            ocr_logger.error(f"Error converting image to numpy array for entry {entry.id}: {e}, deleting entry")
            remove_entry(entry.id)
            return "DELETED"

        # 执行OCR识别
        start_time = time.time()
        try:
            ocr_text = extract_text_from_image(image_array)
            end_time = time.time()
            ocr_logger.info(f"OCR completed for entry {entry.id}, time: {end_time - start_time:.2f}s")
        except Exception as e:
            ocr_logger.error(f"Error during OCR processing for entry {entry.id}: {e}")
            return None

        # 返回OCR结果，不在这里更新数据库，由调用者负责更新
        if ocr_text:
            return ocr_text
        else:
            ocr_logger.warning(f"OCR returned empty result for entry {entry.id}")
            return None
    except Exception as e:
        ocr_logger.error(f"Unexpected error processing OCR task for entry {entry.id}: {e}")
        return None

def process_batch_ocr(batch_size=5):
    """批量处理OCR任务

    改进版本：
    1. 不再先移除条目，而是在处理成功后才更新条目，避免数据丢失
    2. 一次性查询多条空文本条目，提高效率
    3. 当图片不存在时直接删除数据库条目
    4. 使用并行处理提高效率
    5. 在处理前检查CPU负载，如果负载过高则跳过

    Args:
        batch_size: 批处理大小

    Returns:
        处理的任务数量
    """
    # 检查CPU占用率和温度
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_temperature = get_cpu_temperature()

        # 如果CPU占用率超过50%或温度超过70度，跳过本次OCR
        # 降低阈值可以更早地跳过OCR处理，避免系统卡顿
        if cpu_percent > 50 or (cpu_temperature is not None and cpu_temperature > 70):
            ocr_logger.warning(f"Skipping batch OCR due to high system load: CPU usage {cpu_percent}%, temperature {cpu_temperature}°C")
            return 0
    except (ImportError, Exception) as e:
        ocr_logger.warning(f"Failed to check CPU stats in batch processing: {e}")

    # 一次性获取多条未OCR的条目，按时间升序（从旧到新）排序
    entries = get_batch_empty_text(batch_size, oldest_first=True)

    if not entries:
        return 0

    ocr_logger.debug(f"Found {len(entries)} entries to process")

    # 首先检查所有图像是否存在，删除不存在图像的条目
    valid_entries = []
    deleted_count = 0

    for entry in entries:
        # 将entry.timestamp转换为datetime对象
        timestamp_dt = datetime.datetime.fromtimestamp(entry.timestamp)
        screenshot_path = get_screenshot_path(timestamp_dt)
        image_path = os.path.join(screenshot_path, f"{entry.timestamp}.webp")

        # 检查图像是否存在
        if not os.path.exists(image_path):
            ocr_logger.warning(f"Image file does not exist: {image_path}, deleting entry {entry.id}")
            remove_entry(entry.id)
            deleted_count += 1
            continue

        valid_entries.append(entry)

    if deleted_count > 0:
        ocr_logger.info(f"Deleted {deleted_count} entries due to missing images")
    else:
        ocr_logger.debug("No entries deleted due to missing images")

    if not valid_entries:
        return 0

    # 使用线程池并行处理OCR任务
    futures = []
    for entry in valid_entries:
        future = _ocr_executor.submit(process_ocr_task, entry)
        futures.append((future, entry))

    # 等待所有任务完成
    processed_count = 0
    skipped_count = 0
    for future, entry in futures:
        try:
            result = future.result(timeout=60)  # 添加超时控制，避免无限期等待
            if result == "DELETED":
                # 条目已被删除（图片不存在）
                ocr_logger.debug(f"Entry {entry.id} was deleted due to missing image")
            elif result == "SKIPPED":
                # 由于系统负载过高而跳过处理
                skipped_count += 1
            elif result:
                # OCR成功，更新条目
                update_entry_text(entry.id, result, "")
                ocr_logger.debug(f"Entry {entry.id} updated with OCR text")
                processed_count += 1
            else:
                # OCR失败，保留空文本条目
                ocr_logger.warning(f"OCR failed for entry {entry.id}, text is empty")
        except concurrent.futures.TimeoutError:
            ocr_logger.error(f"OCR task for entry {entry.id} timed out")
        except Exception as e:
            ocr_logger.error(f"Error processing OCR task for entry {entry.id}: {e}")

    # 记录跳过的任务数量
    if skipped_count > 0:
        ocr_logger.info(f"Skipped {skipped_count} OCR tasks due to high system load")

    return processed_count

def ocr_processor_thread(idle_time=5, max_batch_size=5):
    """处理线程

    持续从数据库查询未OCR的数据，进行OCR处理

    改进版本：
    1. 增加批处理大小控制和健康检查
    2. 根据需要OCR的条目数量决定是否启动或停止OCR处理

    Args:
        idle_time: 空闲时间（秒）
        max_batch_size: 最大批处理大小
    """
    ocr_logger.info(f"Started OCR processor thread (idle_time={idle_time}s, max_batch_size={max_batch_size})")

    # 记录线程启动时间
    start_time = time.time()
    processed_total = 0

    # OCR处理状态
    global _ocr_processing_enabled
    _ocr_processing_enabled = False  # 初始化为停止状态，等待条件触发启动

    while True:
        try:
            # 查询需要OCR的条目总数
            empty_text_count = get_empty_text_count()

            ocr_logger.debug(f"Empty text count: {empty_text_count}")

            # 根据条目数量决定是否启动或停止OCR处理
            if not _ocr_processing_enabled and empty_text_count >= _OCR_START_THRESHOLD:
                _ocr_processing_enabled = True
                ocr_logger.info(f"Starting OCR processing: {empty_text_count} entries need OCR (threshold: {_OCR_START_THRESHOLD})")
            elif _ocr_processing_enabled and empty_text_count <= _OCR_STOP_THRESHOLD:
                _ocr_processing_enabled = False
                ocr_logger.info(f"Stopping OCR processing: only {empty_text_count} entries need OCR (threshold: {_OCR_STOP_THRESHOLD})")

            # 如果OCR处理已停止，休眠一段时间后继续检查
            if not _ocr_processing_enabled:
                time.sleep(idle_time * 2)  # 停止状态下休眠时间加倍，减少检查频率
                continue

            # 检查CPU占用率和温度
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_temperature = get_cpu_temperature()

                # 如果CPU占用率超过50%或温度超过70度，跳过本次OCR
                # 降低阈值可以更早地跳过OCR处理，避免系统卡顿
                if cpu_percent > 50 or (cpu_temperature is not None and cpu_temperature > 70):
                    ocr_logger.warning(f"Skipping OCR due to high system load: CPU usage {cpu_percent}%, temperature {cpu_temperature}°C")
                    time.sleep(idle_time)
                    continue
            except (ImportError, Exception) as e:
                ocr_logger.warning(f"Failed to check CPU stats: {e}")

            # 批量处理OCR任务
            processed = process_batch_ocr(batch_size=max_batch_size)
            processed_total += processed

            # 如果没有处理任何条目，可能是所有条目都已处理完成
            # 再次检查条目数量，决定是否停止OCR处理
            if processed == 0:
                empty_text_count = get_empty_text_count()
                if empty_text_count <= _OCR_STOP_THRESHOLD:
                    _ocr_processing_enabled = False
                    ocr_logger.info(f"Stopping OCR processing: only {empty_text_count} entries need OCR (threshold: {_OCR_STOP_THRESHOLD})")

            # 定期输出统计信息
            elapsed = time.time() - start_time
            if elapsed > 3600:  # 每小时输出一次统计信息
                ocr_logger.info(f"OCR thread stats: processed {processed_total} entries in {elapsed/3600:.2f} hours")
                start_time = time.time()
                processed_total = 0

            if processed == 0:
                # 如果没有任务，休眠一段时间
                time.sleep(idle_time)
            else:
                # 如果有任务，记录处理结果
                ocr_logger.debug(f"Processed {processed} OCR tasks")

                # 处理完成后强制休眠一段时间，让系统有时间恢复
                # 这可以避免连续的OCR处理导致系统卡顿
                time.sleep(idle_time / 2)  # 休眠一半的idle_time

                # 检查系统负载，如果负载过高，增加休眠时间
                try:
                    import psutil
                    cpu_percent = psutil.cpu_percent(interval=0.5)
                    if cpu_percent > 80:  # CPU使用率超过80%
                        ocr_logger.warning(f"High CPU usage detected: {cpu_percent}%, sleeping for {idle_time*2}s")
                        time.sleep(idle_time * 2)  # 休眠时间加倍
                except ImportError:
                    pass  # 如果没有psutil模块，忽略负载检查

        except Exception as e:
            ocr_logger.error(f"Error in OCR processor thread: {e}")
            # 出错时休眠一段时间
            time.sleep(idle_time)

def start_ocr_processor(idle_time=10, max_batch_size=3):
    """启动OCR处理线程

    Args:
        idle_time: 空闲时间（秒）
        max_batch_size: 最大批处理大小

    Returns:
        启动的线程对象
    """
    # 尝试降低进程优先级
    try:
        import os
        # 在Linux/macOS上使用nice命令降低当前进程的优先级
        if os.name == 'posix':
            os.nice(10)  # 增加nice值，降低优先级
            ocr_logger.info("Lowered OCR process priority using nice")
    except Exception as e:
        ocr_logger.warning(f"Failed to lower process priority: {e}")

    thread = threading.Thread(
        target=ocr_processor_thread,
        args=(idle_time, max_batch_size),
        daemon=True,
        name="OCRProcessorThread"
    )
    thread.start()
    ocr_logger.info(f"OCR processor started with idle_time={idle_time}s, batch_size={max_batch_size}")
    return thread

# 在模块退出时关闭线程池
import atexit

def _cleanup():
    """清理资源"""
    ocr_logger.debug("Shutting down OCR executor...")
    _ocr_executor.shutdown(wait=False)
    ocr_logger.debug("OCR executor shut down")

# 注册清理函数
atexit.register(_cleanup)
