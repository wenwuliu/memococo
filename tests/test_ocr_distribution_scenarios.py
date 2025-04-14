"""
测试OCR处理器在各种桶场景下的分配策略

这个脚本用于测试OCR处理器在各种桶场景下的分配策略，包括：
1. 只有一个桶有条目
2. 所有桶都为空
3. 条目数量极度不平衡
4. 批处理大小小于桶数量
5. 批处理大小大于所有条目总数
6. 时间范围极小
7. 时间范围极大
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

class TestOcrDistributionScenarios(unittest.TestCase):
    """测试OCR处理器在各种桶场景下的分配策略"""

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

        # 获取当前时间
        now = time.time()

        # 只在一个桶中创建条目，确保所有条目都在同一个桶中
        # 所有条目都使用相同的时间戳，确保它们都在同一个桶中
        for i in range(10):
            self.create_single_entry(now)

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

        # 验证只有桶3有条目被选中
        non_empty_buckets = [bucket for bucket, count in bucket_counts.items() if count > 0]
        self.assertEqual(len(non_empty_buckets), 1,
                       f"Only one bucket should have entries selected, but got {len(non_empty_buckets)}")

        # 验证选中的条目数量等于批处理大小或总条目数（取较小值）
        self.assertEqual(len(selected_entries), min(batch_size, total_count),
                       f"Selected entries count ({len(selected_entries)}) should be min(batch_size, total_count) = {min(batch_size, total_count)}")

    def test_all_buckets_empty(self):
        """测试所有桶都为空的情况"""
        print("\n=== 测试所有桶都为空的情况 ===")

        # 清空数据库中的所有条目
        from memococo.database import get_db_connection
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM entries WHERE text = '' OR text IS NULL")
            conn.commit()

        # 获取未OCR条目总数
        total_count = get_empty_text_count()
        print(f"Total empty text entries: {total_count}")

        # 测试查找最优条目，使用10个批处理大小
        batch_size = 10
        selected_entries = find_optimal_entries_for_ocr(batch_size)

        # 验证选择的条目数量为0
        self.assertEqual(len(selected_entries), 0,
                       f"Selected entries count ({len(selected_entries)}) should be 0 when all buckets are empty")

        print(f"Selected {len(selected_entries)} entries for OCR processing")

    def test_extremely_unbalanced_entries(self):
        """测试条目数量极度不平衡的情况"""
        print("\n=== 测试条目数量极度不平衡的情况 ===")

        # 获取当前时间
        now = time.time()

        # 桶1：1个条目
        self.create_bucket_entries(now - 10*3600, 1, gap=60)

        # 桶2：2个条目
        self.create_bucket_entries(now - 8*3600, 2, gap=60)

        # 桶3：100个条目
        self.create_bucket_entries(now - 6*3600, 100, gap=10)

        # 桶4：3个条目
        self.create_bucket_entries(now - 4*3600, 3, gap=60)

        # 桶5：4个条目
        self.create_bucket_entries(now - 2*3600, 4, gap=60)

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

        # 验证所有非空桶都有条目被选中
        empty_buckets = [bucket for bucket, count in bucket_counts.items() if count == 0]
        self.assertEqual(len(empty_buckets), 0,
                       f"All non-empty buckets should have entries selected, but these buckets have none: {empty_buckets}")

        # 验证桶3（条目最多的桶）获得了更多的配额
        self.assertGreater(bucket_counts["bucket3"], bucket_counts["bucket1"],
                         "Bucket with more entries should get more quota")
        self.assertGreaterEqual(bucket_counts["bucket3"], bucket_counts["bucket2"],
                         "Bucket with more entries should get more quota")
        self.assertGreater(bucket_counts["bucket3"], bucket_counts["bucket4"],
                         "Bucket with more entries should get more quota")
        self.assertGreater(bucket_counts["bucket3"], bucket_counts["bucket5"],
                         "Bucket with more entries should get more quota")

    def test_batch_size_less_than_bucket_count(self):
        """测试批处理大小小于桶数量的情况"""
        print("\n=== 测试批处理大小小于桶数量的情况 ===")

        # 获取当前时间
        now = time.time()

        # 在每个桶中创建条目
        for i in range(5):
            self.create_bucket_entries(now - (10-i*2)*3600, 5, gap=60)

        # 获取未OCR条目总数
        total_count = get_empty_text_count()
        print(f"Total empty text entries: {total_count}")

        # 测试查找最优条目，使用3个批处理大小（小于5个桶）
        batch_size = 3
        selected_entries = find_optimal_entries_for_ocr(batch_size)

        # 验证选择的条目数量
        self.assertLessEqual(len(selected_entries), batch_size,
                           f"Selected entries count ({len(selected_entries)}) should not exceed batch size ({batch_size})")

        print(f"Selected {len(selected_entries)} entries for OCR processing")

        # 获取选中条目在各个桶中的分布
        bucket_counts = self.get_bucket_distribution(selected_entries)

        # 验证选中的条目数量等于批处理大小
        self.assertEqual(len(selected_entries), batch_size,
                       f"Selected entries count ({len(selected_entries)}) should be equal to batch size ({batch_size})")

        # 验证至少有3个桶有条目被选中
        non_empty_buckets = [bucket for bucket, count in bucket_counts.items() if count > 0]
        self.assertGreaterEqual(len(non_empty_buckets), 3,
                              f"At least 3 buckets should have entries selected, but only {len(non_empty_buckets)} have")

    def test_batch_size_greater_than_total_entries(self):
        """测试批处理大小大于所有条目总数的情况"""
        print("\n=== 测试批处理大小大于所有条目总数的情况 ===")

        # 获取当前时间
        now = time.time()

        # 在每个桶中创建少量条目
        for i in range(5):
            self.create_bucket_entries(now - (10-i*2)*3600, 1, gap=60)

        # 获取未OCR条目总数
        total_count = get_empty_text_count()
        print(f"Total empty text entries: {total_count}")

        # 测试查找最优条目，使用20个批处理大小（大于总条目数5）
        batch_size = 20
        selected_entries = find_optimal_entries_for_ocr(batch_size)

        # 验证选择的条目数量
        self.assertLessEqual(len(selected_entries), total_count,
                           f"Selected entries count ({len(selected_entries)}) should not exceed total entries count ({total_count})")

        print(f"Selected {len(selected_entries)} entries for OCR processing")

        # 获取选中条目在各个桶中的分布
        bucket_counts = self.get_bucket_distribution(selected_entries)

        # 验证选中的条目数量等于总条目数
        self.assertEqual(len(selected_entries), total_count,
                       f"Selected entries count ({len(selected_entries)}) should be equal to total entries count ({total_count})")

        # 验证所有桶都有条目被选中
        non_empty_buckets = [bucket for bucket, count in bucket_counts.items() if count > 0]
        self.assertEqual(len(non_empty_buckets), 5,
                       f"All 5 buckets should have entries selected, but only {len(non_empty_buckets)} have")

    def test_very_small_time_range(self):
        """测试时间范围极小的情况"""
        print("\n=== 测试时间范围极小的情况 ===")

        # 获取当前时间
        now = time.time()

        # 在很短的时间范围内创建条目（10分钟内）
        for i in range(10):
            self.create_single_entry(now - i*60)

        # 获取未OCR条目总数
        total_count = get_empty_text_count()
        print(f"Total empty text entries: {total_count}")

        # 测试查找最优条目，使用5个批处理大小
        batch_size = 5
        selected_entries = find_optimal_entries_for_ocr(batch_size)

        # 验证选择的条目数量
        self.assertLessEqual(len(selected_entries), batch_size,
                           f"Selected entries count ({len(selected_entries)}) should not exceed batch size ({batch_size})")

        print(f"Selected {len(selected_entries)} entries for OCR processing")

        # 获取选中条目在各个桶中的分布
        bucket_counts = self.get_bucket_distribution(selected_entries)

        # 验证选中的条目数量等于批处理大小
        self.assertEqual(len(selected_entries), batch_size,
                       f"Selected entries count ({len(selected_entries)}) should be equal to batch size ({batch_size})")

        # 由于时间范围极小，所有条目可能都在同一个桶中
        # 验证至少有一个桶有条目被选中
        non_empty_buckets = [bucket for bucket, count in bucket_counts.items() if count > 0]
        self.assertGreaterEqual(len(non_empty_buckets), 1,
                              f"At least 1 bucket should have entries selected, but none have")

    def test_very_large_time_range(self):
        """测试时间范围极大的情况"""
        print("\n=== 测试时间范围极大的情况 ===")

        # 创建跨越很长时间范围的条目（1年）
        now = time.time()
        for i in range(5):
            # 每个桶创建2个条目，相隔很远
            self.create_single_entry(now - i*30*24*3600)  # 每隔30天
            self.create_single_entry(now - i*30*24*3600 - 24*3600)  # 再隔1天

        # 获取未OCR条目总数
        total_count = get_empty_text_count()
        print(f"Total empty text entries: {total_count}")

        # 测试查找最优条目，使用5个批处理大小
        batch_size = 5
        selected_entries = find_optimal_entries_for_ocr(batch_size)

        # 验证选择的条目数量
        self.assertLessEqual(len(selected_entries), batch_size,
                           f"Selected entries count ({len(selected_entries)}) should not exceed batch size ({batch_size})")

        print(f"Selected {len(selected_entries)} entries for OCR processing")

        # 获取选中条目在各个桶中的分布
        bucket_counts = self.get_bucket_distribution(selected_entries)

        # 验证选中的条目数量等于批处理大小
        self.assertEqual(len(selected_entries), batch_size,
                       f"Selected entries count ({len(selected_entries)}) should be equal to batch size ({batch_size})")

        # 验证至少有3个桶有条目被选中（考虑到时间范围极大，应该会分布在多个桶中）
        non_empty_buckets = [bucket for bucket, count in bucket_counts.items() if count > 0]
        self.assertGreaterEqual(len(non_empty_buckets), 3,
                              f"At least 3 buckets should have entries selected, but only {len(non_empty_buckets)} have")

def main():
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()
