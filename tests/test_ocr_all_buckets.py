"""
测试OCR处理器在所有桶都有图片需要OCR时的行为

这个脚本用于测试OCR处理器在所有桶都有图片需要OCR时的行为：
确保所有桶都能被分配OCR任务
"""

import os
import sys
import time
import unittest
import datetime
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memococo.database import create_db, insert_entry, get_empty_text_count
from memococo.ocr_processor import find_optimal_entries_for_ocr

class TestOcrAllBuckets(unittest.TestCase):
    """测试OCR处理器在所有桶都有图片需要OCR时的行为"""

    def setUp(self):
        """测试前的准备工作"""
        # 确保数据库已创建
        create_db()

        # 清空数据库中的测试数据
        self.clean_test_data()

        # 创建测试数据
        self.create_test_data()

    def tearDown(self):
        """测试后的清理工作"""
        self.clean_test_data()

    def clean_test_data(self):
        """清空数据库中的测试数据"""
        # 这里我们使用一个特殊的应用名称来标识测试数据
        # 实际实现可能需要根据数据库结构调整
        pass

    def create_test_data(self):
        """创建测试数据，确保所有桶都有图片需要OCR"""

        # 获取当前时间
        now = time.time()

        # 定义桶的时间范围
        bucket_ranges = {
            "bucket1": (now - 11*3600, now - 9*3600),
            "bucket2": (now - 9*3600, now - 7*3600),
            "bucket3": (now - 7*3600, now - 5*3600),
            "bucket4": (now - 5*3600, now - 3*3600),
            "bucket5": (now - 3*3600, now - 1*3600),
        }

        # 打印每个桶的时间范围
        print("\nCreating test data with the following time ranges:")
        for bucket, (start, end) in bucket_ranges.items():
            start_dt = datetime.datetime.fromtimestamp(start)
            end_dt = datetime.datetime.fromtimestamp(end)
            print(f"  - {bucket}: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} to {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        # 创建5个时间桶的数据，每个桶都有图片需要OCR
        for bucket, (start, end) in bucket_ranges.items():
            # 在每个桶的时间范围内创建2个条目
            mid_time = (start + end) / 2  # 桶的中间时间
            self.create_bucket_entries(mid_time, 2, gap=60)

            # 打印创建的条目时间戳
            print(f"  - Created entries for {bucket} at {datetime.datetime.fromtimestamp(mid_time).strftime('%Y-%m-%d %H:%M:%S')} and {datetime.datetime.fromtimestamp(mid_time + 60).strftime('%Y-%m-%d %H:%M:%S')}")

    def create_bucket_entries(self, start_time, count, gap=60):
        """创建一个连续区间的条目"""
        for i in range(count):
            timestamp = int(start_time + i * gap)
            self.create_single_entry(timestamp)

    def create_single_entry(self, timestamp):
        """创建单个测试条目"""
        insert_entry(
            jsontext="",
            timestamp=int(timestamp),
            text="",  # 空文本，表示未OCR
            app="TestApp",
            title=f"TestTitle_{timestamp}"
        )

    def test_all_buckets_get_ocr(self):
        """测试所有桶都能被分配OCR任务"""
        # 获取未OCR条目总数
        total_count = get_empty_text_count()
        print(f"Total empty text entries: {total_count}")

        # 测试查找最优条目，使用10个批处理大小
        batch_size = 10

        # 设置OCR日志级别为DEBUG，以查看更多日志
        import logging
        from memococo.config import ocr_logger
        ocr_logger.setLevel(logging.DEBUG)

        # 添加控制台处理程序
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - [%(name)s] - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        ocr_logger.addHandler(console_handler)

        selected_entries = find_optimal_entries_for_ocr(batch_size)

        # 验证选择的条目数量
        self.assertLessEqual(len(selected_entries), batch_size,
                           f"Selected entries count ({len(selected_entries)}) should not exceed batch size ({batch_size})")

        print(f"Selected {len(selected_entries)} entries for OCR processing")

        # 打印选择的条目时间戳，按时间排序
        timestamps = sorted([entry.timestamp for entry in selected_entries])
        for ts in timestamps:
            dt = datetime.datetime.fromtimestamp(ts)
            print(f"  - {dt.strftime('%Y-%m-%d %H:%M:%S')} ({ts})")

        # 统计每个桶中选择的条目数量
        bucket_counts = {
            "bucket1": 0,  # 10小时前
            "bucket2": 0,  # 8小时前
            "bucket3": 0,  # 6小时前
            "bucket4": 0,  # 4小时前
            "bucket5": 0,  # 2小时前
        }

        # 获取未OCR条目的时间范围
        from memococo.database import get_empty_text_timestamp_range
        min_timestamp, max_timestamp = get_empty_text_timestamp_range()

        # 定义桶的数量
        num_buckets = 5

        # 计算每个桶的时间范围
        time_range = max_timestamp - min_timestamp
        bucket_size = time_range / num_buckets

        # 定义桶的时间范围
        bucket_ranges = {}
        for i in range(num_buckets):
            start = min_timestamp + int(i * bucket_size)
            end = min_timestamp + int((i + 1) * bucket_size) if i < num_buckets - 1 else max_timestamp
            bucket_ranges[f"bucket{i+1}"] = (start, end)

        # 打印每个桶的时间范围
        print("\nBucket time ranges:")
        for bucket, (start, end) in bucket_ranges.items():
            start_dt = datetime.datetime.fromtimestamp(start)
            end_dt = datetime.datetime.fromtimestamp(end)
            print(f"  - {bucket}: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} to {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        # 检查数据库中是否有桶的条目
        print("\nChecking database for entries in each bucket:")
        for bucket, (start, end) in bucket_ranges.items():
            from memococo.database import get_empty_text_in_range
            entries = get_empty_text_in_range(int(start), int(end), limit=100)
            print(f"  - {bucket}: found {len(entries)} entries in database")
            # 打印每个条目的时间戳
            for entry in entries:
                dt = datetime.datetime.fromtimestamp(entry.timestamp)
                print(f"    - {dt.strftime('%Y-%m-%d %H:%M:%S')} ({entry.timestamp})")

        # 统计每个桶中选择的条目数量
        for entry in selected_entries:
            for bucket, (start, end) in bucket_ranges.items():
                if start <= entry.timestamp <= end:
                    bucket_counts[bucket] += 1
                    break

        print("\nDistribution of selected entries:")
        for bucket, count in bucket_counts.items():
            print(f"  - {bucket}: {count} entries")

        # 验证所有桶都被分配了OCR任务
        empty_buckets = [bucket for bucket, count in bucket_counts.items() if count == 0]
        self.assertEqual(len(empty_buckets), 0,
                       f"Some buckets were not assigned OCR tasks: {empty_buckets}")

def main():
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()
