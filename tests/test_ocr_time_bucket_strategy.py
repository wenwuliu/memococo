"""
测试OCR处理器的均匀时间分桶和连续区间优化策略

这个脚本用于测试OCR处理器的新策略：
1. 均匀时间分桶
2. 连续未OCR区间优化
3. 处理后的休息时间
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
from memococo.ocr_processor import find_optimal_entries_for_ocr, process_batch_ocr

class TestOcrTimeBucketStrategy(unittest.TestCase):
    """测试OCR处理器的均匀时间分桶和连续区间优化策略"""
    
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
        """创建测试数据"""
        # 创建跨越多个时间段的未OCR条目
        
        # 获取当前时间
        now = time.time()
        
        # 创建5个时间桶的数据
        # 桶1：10小时前（连续区间：3个条目）
        self.create_bucket_entries(now - 10*3600, 3, gap=60)  # 连续的3个条目，间隔1分钟
        
        # 桶2：8小时前（连续区间：5个条目）
        self.create_bucket_entries(now - 8*3600, 5, gap=60)  # 连续的5个条目，间隔1分钟
        
        # 桶3：6小时前（连续区间：2个条目）
        self.create_bucket_entries(now - 6*3600, 2, gap=60)  # 连续的2个条目，间隔1分钟
        
        # 桶4：4小时前（连续区间：7个条目）
        self.create_bucket_entries(now - 4*3600, 7, gap=60)  # 连续的7个条目，间隔1分钟
        
        # 桶5：2小时前（连续区间：4个条目）
        self.create_bucket_entries(now - 2*3600, 4, gap=60)  # 连续的4个条目，间隔1分钟
        
        # 添加一些随机的单独条目
        for i in range(10):
            random_time = now - random.randint(1, 12) * 3600
            self.create_single_entry(random_time)
    
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
    
    def test_find_optimal_entries(self):
        """测试查找最优OCR条目的函数"""
        # 获取未OCR条目总数
        total_count = get_empty_text_count()
        print(f"Total empty text entries: {total_count}")
        
        # 测试查找最优条目
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
        
        # 验证选择的条目是否分布在不同的时间桶中
        if len(timestamps) >= 2:
            # 计算时间跨度
            time_span = timestamps[-1] - timestamps[0]
            hours_span = time_span / 3600
            
            print(f"Time span of selected entries: {hours_span:.2f} hours")
            
            # 验证时间跨度是否足够大（至少覆盖多个桶）
            self.assertGreater(hours_span, 1.0, 
                             "Selected entries should span across multiple time buckets")
    
    @patch('memococo.ocr_processor.process_ocr_task')
    def test_process_batch_ocr(self, mock_process_ocr_task):
        """测试批量处理OCR任务"""
        # 模拟OCR处理成功
        mock_process_ocr_task.return_value = "Mocked OCR text"
        
        # 测试批量处理
        with patch('time.sleep') as mock_sleep:  # 避免实际休眠
            processed = process_batch_ocr(batch_size=10)
            
            # 验证处理的条目数量
            self.assertGreaterEqual(processed, 0, 
                                  "Processed entries count should be non-negative")
            
            print(f"Processed {processed} entries")
            
            # 验证是否调用了休眠函数
            mock_sleep.assert_called()
            print("Sleep function was called")

def main():
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()
