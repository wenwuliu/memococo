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
from memococo.database import update_entry_text, remove_entry, get_empty_text_count, \
    get_empty_text_timestamp_range, get_empty_text_in_range, get_batch_empty_text
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

def find_optimal_entries_for_ocr(batch_size=5):
    """使用均匀时间分桶和连续未OCR区间优化策略找出最优的OCR条目

    策略描述：
    1. 将整个时间线均匀划分为多个“时间桶”
    2. 在每个桶内识别最长的连续未OCR区间
    3. 优先处理这些区间的中间点，以最大限度地减少连续未OCR的长度
    4. 从每个桶中选择相等数量的条目，确保时间线上的均匀分布

    Args:
        batch_size: 批处理大小

    Returns:
        选中的条目列表
    """
    # 获取未OCR条目的时间范围
    min_timestamp, max_timestamp = get_empty_text_timestamp_range()

    # 获取未OCR条目总数
    total_count = get_empty_text_count()

    # 如果没有未OCR条目，返回空列表
    if min_timestamp is None or max_timestamp is None or total_count == 0:
        ocr_logger.debug(f"No empty text entries found, returning empty list")
        return []

    # 如果批处理大小大于所有条目总数，直接返回所有条目
    if batch_size >= total_count and total_count > 0:
        ocr_logger.debug(f"Batch size {batch_size} is greater than or equal to total entries count {total_count}, returning all entries")
        return get_batch_empty_text(total_count, oldest_first=True)

    # 定义桶的数量
    num_buckets = 5

    # 计算每个桶的时间范围
    time_range = max_timestamp - min_timestamp
    if time_range <= 0:
        # 如果时间范围为0，只有一个桶
        buckets = [(min_timestamp, max_timestamp)]
    else:
        bucket_size = time_range / num_buckets
        buckets = []
        for i in range(num_buckets):
            start = min_timestamp + int(i * bucket_size)
            end = min_timestamp + int((i + 1) * bucket_size) if i < num_buckets - 1 else max_timestamp
            buckets.append((start, end))

    # 计算每个桶应该选择的条目数量
    entries_per_bucket = batch_size // len(buckets)
    # 保存所有选中的条目
    selected_entries = []

    # 从每个桶中选择条目
    ocr_logger.debug(f"Time range: {min_timestamp} to {max_timestamp}, divided into {len(buckets)} buckets")

    # 第一阶段：从每个桶中获取条目并分析连续区间
    bucket_entries = []
    bucket_continuous_intervals = []

    for i, (start, end) in enumerate(buckets):
        # 获取桶内的所有未OCR条目
        entries = get_empty_text_in_range(start, end, limit=100)  # 获取足够多的条目以分析连续区间
        bucket_entries.append(entries)
        ocr_logger.debug(f"Bucket {i+1}: {start} to {end}, found {len(entries)} entries")

        # 分析连续未OCR区间
        intervals = []
        if len(entries) > 0:
            # 定义连续区间的时间阈值（秒）
            time_threshold = 20  # 5分钟

            # 按时间戳排序
            sorted_entries = sorted(entries, key=lambda e: e.timestamp)

            # 初始化第一个区间
            current_interval = [sorted_entries[0]]

            # 遍历所有条目，识别连续区间
            for j in range(1, len(sorted_entries)):
                current_entry = sorted_entries[j]
                prev_entry = sorted_entries[j-1]

                # 如果与前一个条目的时间差小于阈值，则属于同一区间
                if current_entry.timestamp - prev_entry.timestamp <= time_threshold:
                    current_interval.append(current_entry)
                else:
                    # 否则开始新的区间
                    if len(current_interval) > 0:
                        intervals.append(current_interval)
                    current_interval = [current_entry]

            # 添加最后一个区间
            if len(current_interval) > 0:
                intervals.append(current_interval)

            # 如果没有识别出连续区间（可能是因为条目间隔太大），则创建一个包含所有条目的人工区间
            if not intervals and len(sorted_entries) > 0:
                ocr_logger.debug(f"Bucket {i+1}: No continuous intervals found, creating artificial interval with all {len(sorted_entries)} entries")
                intervals.append(sorted_entries)

        # 按区间长度排序（从长到短）
        intervals.sort(key=lambda x: len(x), reverse=True)
        bucket_continuous_intervals.append(intervals)

        # 记录日志
        if intervals:
            ocr_logger.debug(f"Bucket {i+1}: Found {len(intervals)} intervals, longest has {len(intervals[0])} entries")
        else:
            ocr_logger.debug(f"Bucket {i+1}: No intervals found")

    # 第二阶段：从每个桶中选择最优的条目
    selected_entries = []

    # 收集每个桶的条目数量信息
    bucket_info = []
    empty_buckets = []
    non_empty_buckets = []

    for i, (entries, intervals) in enumerate(zip(bucket_entries, bucket_continuous_intervals)):
        if not entries:  # 空桶（没有条目）
            empty_buckets.append(i)
            bucket_info.append({"index": i, "count": 0, "entries": entries})
        else:  # 非空桶（有条目）
            non_empty_buckets.append(i)
            # 如果有连续区间，使用区间信息；如果没有，使用条目数量
            if intervals:
                total_entries = sum(len(interval) for interval in intervals)
            else:
                total_entries = len(entries)
            bucket_info.append({"index": i, "count": total_entries, "entries": entries, "intervals": intervals})

    # 如果只有一个桶有条目，则只从该桶中选择条目
    if len(non_empty_buckets) == 1:
        ocr_logger.debug(f"Only one bucket (bucket {non_empty_buckets[0]+1}) has entries, selecting all entries from this bucket")
        # 直接返回该桶中的条目（不超过batch_size个）
        entries = bucket_info[non_empty_buckets[0]]["entries"]
        if len(entries) <= batch_size:
            return entries
        else:
            # 如果条目数量超过batch_size，则选择batch_size个条目
            # 按时间戳排序
            sorted_entries = sorted(entries, key=lambda e: e.timestamp)
            # 均匀选择
            step = len(sorted_entries) / batch_size
            selected = []
            for i in range(batch_size):
                index = min(int(i * step), len(sorted_entries) - 1)
                selected.append(sorted_entries[index])
            return selected

    # 如果批处理大小小于非空桶数量，则只选择批处理大小个非空桶
    if batch_size < len(non_empty_buckets):
        ocr_logger.debug(f"Batch size {batch_size} is smaller than the number of non-empty buckets {len(non_empty_buckets)}")
        # 按条目数量排序非空桶，选择条目数量最多的桶
        sorted_buckets = sorted(non_empty_buckets, key=lambda i: bucket_info[i]["count"], reverse=True)
        # 只选择批处理大小个非空桶
        non_empty_buckets = sorted_buckets[:batch_size]
        ocr_logger.debug(f"Selected {len(non_empty_buckets)} non-empty buckets with most entries")

    # 确保每个非空桶至少选择一个条目

    # 计算每个桶应该选择的条目数量
    entries_per_bucket = max(0, batch_size // len(non_empty_buckets)) if non_empty_buckets else 0
    remaining_slots = batch_size

    # 计算空桶的配额总数
    empty_bucket_quota = len(empty_buckets) * entries_per_bucket

    # 如果有空桶，重新分配其配额
    if empty_bucket_quota > 0 and non_empty_buckets:
        ocr_logger.debug(f"Found {len(empty_buckets)} empty buckets, redistributing {empty_bucket_quota} slots")

        # 按非空桶中条目数量比例分配额外配额
        non_empty_bucket_info = [bucket_info[i] for i in non_empty_buckets]

        # 直接按条目数量排序，将额外配额分配给条目最多的桶
        sorted_buckets = sorted(non_empty_bucket_info, key=lambda x: x["count"], reverse=True)

        # 如果所有非空桶的条目总数为0，均匀分配
        if len(sorted_buckets) == 0 or sorted_buckets[0]["count"] == 0:
            extra_per_bucket = empty_bucket_quota // len(non_empty_buckets) if non_empty_buckets else 0
            for i in non_empty_buckets:
                bucket_info[i]["extra_quota"] = extra_per_bucket
        else:
            # 完全按条目数量比例分配额外配额
            # 计算所有非空桶的条目总数
            total_entries = sum(info["count"] for info in sorted_buckets)

            # 初始化所有桶的额外配额为0
            for info in non_empty_bucket_info:
                bucket_info[info["index"]]["extra_quota"] = 0

            # 分配额外配额，确保条目数量多的桶获得更多的配额
            remaining_extra = empty_bucket_quota

            # 按条目数量比例分配额外配额，确保条目数量多的桶获得更多的配额
            total_entries = sum(info["count"] for info in non_empty_bucket_info)

            # 初始化所有桶的额外配额为0
            for info in non_empty_bucket_info:
                bucket_info[info["index"]]["extra_quota"] = 0

            # 如果所有非空桶的条目总数为0，均匀分配
            if total_entries == 0:
                extra_per_bucket = empty_bucket_quota // len(non_empty_buckets) if non_empty_buckets else 0
                for i in non_empty_buckets:
                    bucket_info[i]["extra_quota"] = extra_per_bucket
            else:
                # 按条目数量比例分配额外配额，但确保条目数量最多的桶获得更多的配额
                # 首先给每个桶分配一个基本的额外配额
                for info in sorted_buckets:
                    if remaining_extra <= 0:
                        break
                    bucket_info[info["index"]]["extra_quota"] = 1
                    remaining_extra -= 1

                # 然后按条目数量比例分配剩余的额外配额
                if remaining_extra > 0:
                    # 先将所有配额分配给条目最多的桶
                    if sorted_buckets:
                        # 确保条目最多的桶获得至少一半的配额
                        most_entries_bucket = sorted_buckets[0]
                        most_entries_extra = max(remaining_extra // 2, 2)  # 至少分配2个，确保比其他桶多
                        most_entries_extra = min(most_entries_extra, remaining_extra)  # 不超过剩余配额

                        bucket_info[most_entries_bucket["index"]]["extra_quota"] += most_entries_extra
                        remaining_extra -= most_entries_extra

                        ocr_logger.debug(f"Assigned {most_entries_extra} extra quota to bucket {most_entries_bucket['index']+1} with most entries ({most_entries_bucket['count']})")

                    # 然后按条目数量比例分配剩余的额外配额
                    if remaining_extra > 0:
                        for info in sorted_buckets:
                            if remaining_extra <= 0:
                                break
                            # 计算比例
                            proportion = info["count"] / total_entries
                            # 计算额外配额，至少为1
                            extra = max(1, int(empty_bucket_quota * proportion * 0.5))  # 使用一半的配额按比例分配
                            extra = min(extra, remaining_extra)  # 不超过剩余配额

                            # 增加额外配额
                            bucket_info[info["index"]]["extra_quota"] += extra
                            remaining_extra -= extra

                            ocr_logger.debug(f"Assigned {extra} extra quota to bucket {info['index']+1} with {info['count']} entries (proportion: {proportion:.2f})")

                # 如果还有剩余配额，全部分配给条目最多的桶
                if remaining_extra > 0 and sorted_buckets:
                    bucket_info[sorted_buckets[0]["index"]]["extra_quota"] += remaining_extra
                    ocr_logger.debug(f"Assigned all remaining {remaining_extra} extra quota to bucket {sorted_buckets[0]['index']+1} with {sorted_buckets[0]['count']} entries")
                    remaining_extra = 0

            ocr_logger.debug(f"Redistributed extra quota to buckets with most entries: {[(info['index']+1, info['count'], bucket_info[info['index']].get('extra_quota', 0)) for info in sorted_buckets]}")

    # 首先确保每个非空桶至少选择一个条目
    guaranteed_entries = []

    # 打印每个桶的条目数量
    ocr_logger.debug("Bucket entries count:")
    for i, (entries, intervals) in enumerate(zip(bucket_entries, bucket_continuous_intervals)):
        ocr_logger.debug(f"Bucket {i+1}: {len(entries)} entries")
        if len(entries) > 0:
            # 打印第一个和最后一个条目的时间戳
            sorted_entries = sorted(entries, key=lambda e: e.timestamp)
            first_dt = datetime.datetime.fromtimestamp(sorted_entries[0].timestamp)
            last_dt = datetime.datetime.fromtimestamp(sorted_entries[-1].timestamp)
            ocr_logger.debug(f"  - Time range: {first_dt.strftime('%Y-%m-%d %H:%M:%S')} to {last_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    # 强制为每个非空桶选择一个条目
    for i, (entries, intervals) in enumerate(zip(bucket_entries, bucket_continuous_intervals)):
        if entries:  # 如果桶不为空
            # 选择桶中间时间点的条目
            sorted_entries = sorted(entries, key=lambda e: e.timestamp)
            mid_index = len(sorted_entries) // 2
            mid_entry = sorted_entries[mid_index]
            guaranteed_entries.append(mid_entry)
            ocr_logger.debug(f"Guaranteed one entry from bucket {i+1} at {datetime.datetime.fromtimestamp(mid_entry.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            # 从可用条目中移除该条目
            entries_copy = entries.copy()  # 创建副本以避免修改原始列表
            entries_copy.remove(mid_entry)
            bucket_entries[i] = entries_copy  # 替换原始列表

    # 将保证的条目添加到选中列表
    # 如果保证的条目数量已经超过批处理大小，只选择批处理大小个条目
    if len(guaranteed_entries) > batch_size:
        ocr_logger.debug(f"Guaranteed entries count {len(guaranteed_entries)} exceeds batch size {batch_size}, selecting only {batch_size} entries")
        # 按桶的条目数量排序，选择条目数量最多的桶
        bucket_entry_counts = []
        for i, (entries, intervals) in enumerate(zip(bucket_entries, bucket_continuous_intervals)):
            if entries:  # 如果桶不为空
                bucket_entry_counts.append((i, len(entries)))
        sorted_buckets = sorted(bucket_entry_counts, key=lambda x: x[1], reverse=True)
        # 只选择批处理大小个桶的保证条目
        selected_bucket_indices = [x[0] for x in sorted_buckets[:batch_size]]
        # 根据桶索引选择保证条目
        filtered_guaranteed_entries = []
        for i, entry in enumerate(guaranteed_entries):
            # 找出该条目所属的桶
            for bucket_idx, (start, end) in enumerate(buckets):
                if start <= entry.timestamp <= end and bucket_idx in selected_bucket_indices:
                    filtered_guaranteed_entries.append(entry)
                    break
        guaranteed_entries = filtered_guaranteed_entries[:batch_size]

    selected_entries.extend(guaranteed_entries)
    remaining_slots = max(0, batch_size - len(selected_entries))

    # 然后正常处理剩余的配额
    for i, info in enumerate(bucket_info):
        bucket_selected = []

        # 如果没有条目，跳过这个桶
        if i in empty_buckets:
            continue

        intervals = info.get("intervals", [])
        entries = info.get("entries", [])

        # 计算这个桶的总配额（基本配额 + 额外配额）
        base_quota = entries_per_bucket
        extra_quota = info.get("extra_quota", 0)
        total_quota = base_quota + extra_quota

        # 计算这个桶的配额
        slots_for_bucket = min(total_quota, remaining_slots)
        slots_used = 0

        ocr_logger.debug(f"Bucket {i+1}: allocated {slots_for_bucket} slots (base: {base_quota}, extra: {extra_quota})")

        # 如果有连续区间，使用连续区间优化策略
        if intervals:
            for interval in intervals:
                if slots_used >= slots_for_bucket:
                    break

                # 如果区间长度为1，直接选择该条目
                if len(interval) == 1:
                    bucket_selected.append(interval[0])
                    slots_used += 1
                else:
                    # 选择区间的中间点
                    mid_index = len(interval) // 2
                    bucket_selected.append(interval[mid_index])
                    slots_used += 1

                    # 如果还有空位且区间足够长，选择更多的点
                    if slots_used < slots_for_bucket and len(interval) >= 4:
                        # 选择四分位置的点
                        quarter_index = len(interval) // 4
                        if quarter_index > 0 and slots_used < slots_for_bucket:
                            bucket_selected.append(interval[quarter_index])
                            slots_used += 1

                        three_quarter_index = (len(interval) * 3) // 4
                        if three_quarter_index < len(interval) - 1 and slots_used < slots_for_bucket:
                            bucket_selected.append(interval[three_quarter_index])
                            slots_used += 1
        # 如果没有连续区间但有条目，直接从条目中选择
        elif entries:
            ocr_logger.debug(f"Bucket {i+1}: No intervals but has {len(entries)} entries, selecting directly from entries")
            # 按时间戳排序
            sorted_entries = sorted(entries, key=lambda e: e.timestamp)

            # 选择尽可能均匀分布的条目
            if len(sorted_entries) <= slots_for_bucket:
                # 如果条目数量小于等于配额，全部选择
                bucket_selected.extend(sorted_entries)
                slots_used = len(sorted_entries)
                ocr_logger.debug(f"Bucket {i+1}: Selected all {slots_used} entries")
            else:
                # 如果条目数量大于配额，均匀选择
                step = len(sorted_entries) / slots_for_bucket
                for j in range(slots_for_bucket):
                    index = min(int(j * step), len(sorted_entries) - 1)
                    bucket_selected.append(sorted_entries[index])
                    slots_used += 1
                ocr_logger.debug(f"Bucket {i+1}: Selected {slots_used} entries evenly distributed")

        # 如果还有空位但没有更多的连续区间，从桶中随机选择条目
        if slots_used < slots_for_bucket and info["entries"]:
            # 将所有已选择的条目排除
            remaining_entries = [e for e in info["entries"] if e not in bucket_selected]
            # 随机选择剩余的条目
            import random
            additional_count = min(slots_for_bucket - slots_used, len(remaining_entries))
            if additional_count > 0 and remaining_entries:
                bucket_selected.extend(random.sample(remaining_entries, additional_count))
                slots_used += additional_count

        # 添加到总选择列表
        selected_entries.extend(bucket_selected)
        remaining_slots -= slots_used

        # 记录日志，包含额外配额信息
        extra_info = ""
        if info.get("extra_quota", 0) > 0:
            extra_info = f" (including {info.get('extra_quota')} from empty buckets)"
        ocr_logger.debug(f"Bucket {i+1}: selected {slots_used} entries from {len(intervals)} intervals{extra_info}")

    # 如果还有剩余的空位，从所有桶中随机选择
    if remaining_slots > 0:
        # 收集所有未选择的条目
        all_remaining_entries = []
        for i, entries in enumerate(bucket_entries):
            all_remaining_entries.extend([e for e in entries if e not in selected_entries])

        # 随机选择剩余的条目
        import random
        additional_count = min(remaining_slots, len(all_remaining_entries))
        if additional_count > 0 and all_remaining_entries:
            selected_entries.extend(random.sample(all_remaining_entries, additional_count))
            ocr_logger.debug(f"Selected {additional_count} additional entries to fill remaining slots")

    # 确保最终选择的条目数量不超过批处理大小
    if len(selected_entries) > batch_size:
        ocr_logger.debug(f"Final selected entries count {len(selected_entries)} exceeds batch size {batch_size}, truncating to {batch_size} entries")
        # 按时间戳排序，并均匀选择
        sorted_entries = sorted(selected_entries, key=lambda e: e.timestamp)
        step = len(sorted_entries) / batch_size
        final_selected = []
        for i in range(batch_size):
            index = min(int(i * step), len(sorted_entries) - 1)
            final_selected.append(sorted_entries[index])
        selected_entries = final_selected

    ocr_logger.info(f"Selected {len(selected_entries)} entries for OCR processing using time bucket strategy")
    return selected_entries

def process_batch_ocr(batch_size=5):
    """批量处理OCR任务

    改进版本：
    1. 不再先移除条目，而是在处理成功后才更新条目，避免数据丢失
    2. 一次性查询多条空文本条目，提高效率
    3. 当图片不存在时直接删除数据库条目
    4. 顺序处理OCR任务，每完成一个任务后等待3秒
    5. 在处理前检查CPU负载，如果负载过高则跳过
    6. 使用均匀时间分桶和连续未OCR区间优化策略

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

    # 使用均匀时间分桶和连续未OCR区间优化策略选择条目
    entries = find_optimal_entries_for_ocr(batch_size)

    if not entries:
        return 0

    ocr_logger.debug(f"Selected {len(entries)} entries to process using time bucket strategy")

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

    # 顺序处理OCR任务，每完成一个任务后等待3秒
    processed_count = 0
    skipped_count = 0

    for entry in valid_entries:
        try:
            # 直接调用OCR处理函数，不使用线程池
            result = process_ocr_task(entry)

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

            # 每完成一个OCR任务后等待3秒
            ocr_logger.debug(f"Waiting 3 seconds before processing next OCR task")
            time.sleep(3)

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
                # 每轮完成OCR后，休息5秒，降低OCR频率
                ocr_logger.debug(f"OCR round completed, resting for 5 seconds")
                time.sleep(5)  # 休息5秒

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

def start_ocr_processor(idle_time=10, max_batch_size=5):
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
