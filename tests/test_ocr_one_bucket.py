"""
测试OCR处理器在只有一个桶有条目的情况下的分配策略
"""

import os
import sys
import time
import unittest
import datetime
import random
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memococo.database import create_db, insert_entry, get_empty_text_count, get_empty_text_timestamp_range, get_db_connection
from memococo.ocr_processor import find_optimal_entries_for_ocr

class TestOcrOneBucket(unittest.TestCase):
    """测试OCR处理器在只有一个桶有条目的情况下的分配策略"""

    def setUp(self):
        """测试前的准备工作"""
        # 确保数据库已创建
        create_db()

        # 清空数据库中的测试数据
        self.clean_test_data()

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

    def tearDown(self):
        """测试后的清理工作"""
        self.clean_test_data()

    def clean_test_data(self):
        """清空数据库中的测试数据"""
        # 清空数据库中的所有未OCR条目
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM entries WHERE text = '' OR text IS NULL")
            conn.commit()

    def create_single_entry(self, timestamp):
        """创建单个测试条目"""
        insert_entry(
            jsontext="",
            timestamp=int(timestamp),
            text="",  # 空文本，表示未OCR
            app="TestApp",
            title=f"TestTitle_{timestamp}"
        )

    def get_bucket_distribution(self, selected_entries):
        """获取选中条目在各个桶中的分布"""
        # 获取未OCR条目的时间范围
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

        # 统计每个桶中选择的条目数量
        bucket_counts = {
            "bucket1": 0,
            "bucket2": 0,
            "bucket3": 0,
            "bucket4": 0,
            "bucket5": 0,
        }

        # 统计每个桶中选择的条目数量
        for entry in selected_entries:
            for bucket, (start, end) in bucket_ranges.items():
                if start <= entry.timestamp <= end:
                    bucket_counts[bucket] += 1
                    break

        print("\nDistribution of selected entries:")
        for bucket, count in bucket_counts.items():
            print(f"  - {bucket}: {count} entries")

        return bucket_counts

    def test_only_one_bucket_has_entries(self):
        """测试只有一个桶有条目的情况"""
        print("\n=== 测试只有一个桶有条目的情况 ===")

        # 清空数据库中的所有条目
        self.clean_test_data()

        # 获取当前时间
        now = time.time()

        # 只在一个桶中创建条目，确保所有条目都在同一个桶中
        # 使用非常小的时间范围，确保所有条目都在同一个桶中
        bucket_start = now
        # 创建非常小的时间范围内的条目，确保所有条目都在同一个桶中
        # 所有条目都在同一秒内，确保它们都在同一个桶中
        for i in range(10):
            self.create_single_entry(bucket_start)

        # 获取未OCR条目总数
        total_count = get_empty_text_count()
        print(f"Total empty text entries: {total_count}")

        # 测试查找最优条目，使用10个批处理大小
        batch_size = 10
        selected_entries = find_optimal_entries_for_ocr(batch_size)

        # 验证选择的条目数量
        self.assertLessEqual(len(selected_entries), batch_size,
                           f"Selected entries count ({len(selected_entries)}) should not exceed batch size ({batch_size})")

        print(f"Selected {len(selected_entries)} entries for OCR processing")

        # 获取选中条目在各个桶中的分布
        bucket_counts = self.get_bucket_distribution(selected_entries)

        # 验证只有一个桶有条目被选中
        non_empty_buckets = [bucket for bucket, count in bucket_counts.items() if count > 0]
        self.assertEqual(len(non_empty_buckets), 1,
                       f"Only one bucket should have entries selected, but got {len(non_empty_buckets)}")

        # 验证选中的条目数量等于批处理大小或总条目数（取较小值）
        self.assertEqual(len(selected_entries), min(batch_size, total_count),
                       f"Selected entries count ({len(selected_entries)}) should be min(batch_size, total_count) = {min(batch_size, total_count)}")

def main():
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()
