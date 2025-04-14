"""
测试OCR处理器的空桶配额重分配策略

这个脚本用于测试OCR处理器的空桶配额重分配策略：
当某些时间桶为空时，应该从其他有更多条目的桶中取额外的条目进行OCR处理
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

from memococo.database import create_db, insert_entry, get_empty_text_count
from memococo.ocr_processor import find_optimal_entries_for_ocr

class TestOcrEmptyBucketRedistribution(unittest.TestCase):
    """测试OCR处理器的空桶配额重分配策略"""

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
        """创建测试数据，故意让某些桶为空"""

        # 获取当前时间
        now = time.time()

        # 创建5个时间桶的数据，但让第2和第4个桶为空
        # 桶1：10小时前（5个条目）
        self.create_bucket_entries(now - 10*3600, 5, gap=60)

        # 桶2：8小时前（0个条目，空桶）

        # 桶3：6小时前（20个条目）
        self.create_bucket_entries(now - 6*3600, 20, gap=30)  # 增加到20个条目，间隔缩小为30秒

        # 桶4：4小时前（0个条目，空桶）

        # 桶5：2小时前（3个条目）
        self.create_bucket_entries(now - 2*3600, 3, gap=60)

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

    def test_empty_bucket_redistribution(self):
        """测试空桶配额重分配策略"""
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

        # 打印选择的条目时间戳，按时间排序
        timestamps = sorted([entry.timestamp for entry in selected_entries])
        for ts in timestamps:
            dt = datetime.datetime.fromtimestamp(ts)
            print(f"  - {dt.strftime('%Y-%m-%d %H:%M:%S')} ({ts})")

        # 统计每个桶中选择的条目数量
        bucket_counts = {
            "bucket1": 0,  # 10小时前
            "bucket3": 0,  # 6小时前
            "bucket5": 0,  # 2小时前
        }

        # 定义桶的时间范围
        now = time.time()
        bucket_ranges = {
            "bucket1": (now - 11*3600, now - 9*3600),
            "bucket3": (now - 7*3600, now - 5*3600),
            "bucket5": (now - 3*3600, now - 1*3600),
        }

        # 统计每个桶中选择的条目数量
        for entry in selected_entries:
            for bucket, (start, end) in bucket_ranges.items():
                if start <= entry.timestamp <= end:
                    bucket_counts[bucket] += 1
                    break

        print("Distribution of selected entries:")
        for bucket, count in bucket_counts.items():
            print(f"  - {bucket}: {count} entries")

        # 验证空桶的配额是否被重新分配
        # 如果没有空桶配额重分配，每个桶应该有2个条目（batch_size=10，5个桶，每桶2个）
        # 有了空桶配额重分配，非空桶应该有更多的条目
        self.assertGreater(sum(bucket_counts.values()), 6,
                         "Empty bucket quota should be redistributed to non-empty buckets")

        # 验证条目较多的桶3是否获得了更多的配额
        self.assertGreater(bucket_counts["bucket3"], bucket_counts["bucket5"],
                         "Bucket with more entries should get more extra quota")

def main():
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()
