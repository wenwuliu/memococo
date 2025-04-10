"""
测试改进后的OCR处理模块

这个脚本用于测试改进后的OCR处理模块的功能
"""

import os
import time
import unittest
import threading
from datetime import datetime

from memococo.database import create_db, insert_entry, get_newest_empty_text
from memococo.config import screenshots_path
from memococo.ocr_processor import process_batch_ocr, start_ocr_processor

class TestImprovedOcrProcessor(unittest.TestCase):
    """测试改进后的OCR处理模块"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 确保数据库已创建
        create_db()
        
        # 创建测试目录
        self.test_date = datetime.now()
        self.test_dir = os.path.join(
            screenshots_path, 
            self.test_date.strftime("%Y/%m/%d")
        )
        os.makedirs(self.test_dir, exist_ok=True)
    
    def test_process_batch_ocr_empty(self):
        """测试批量处理OCR任务（空数据库）"""
        # 处理一批OCR任务
        processed = process_batch_ocr(batch_size=3)
        self.assertEqual(processed, 0, "应该处理0个OCR任务，因为数据库为空")
    
    def test_process_batch_ocr_with_data(self):
        """测试批量处理OCR任务（有数据）"""
        # 插入一些测试数据
        timestamp = int(time.time())
        for i in range(3):
            insert_entry("", timestamp + i, "", f"TestApp{i}", f"TestTitle{i}")
            print(f"插入测试数据 {i+1}/3")
        
        # 检查是否有未OCR的数据
        entry = get_newest_empty_text()
        self.assertIsNotNone(entry, "没有找到未OCR的数据")
        
        # 处理一批OCR任务
        processed = process_batch_ocr(batch_size=3)
        print(f"处理了 {processed} 个OCR任务")
        
        # 由于没有实际的图像文件，OCR处理应该失败，但不会抛出异常
        self.assertEqual(processed, 0, "应该处理0个OCR任务，因为没有实际的图像文件")
    
    def test_ocr_processor_thread(self):
        """测试OCR处理线程"""
        # 启动OCR处理线程
        ocr_thread = start_ocr_processor(idle_time=1, max_batch_size=3)
        self.assertTrue(ocr_thread.is_alive(), "OCR处理线程应该处于活动状态")
        
        # 插入一些测试数据
        timestamp = int(time.time())
        for i in range(3):
            insert_entry("", timestamp + i, "", f"TestApp{i}", f"TestTitle{i}")
            print(f"插入测试数据 {i+1}/3")
        
        # 等待一段时间，让OCR处理线程工作
        print("等待OCR处理线程工作...")
        time.sleep(5)
        
        # 检查线程是否仍然活动
        self.assertTrue(ocr_thread.is_alive(), "OCR处理线程应该仍然处于活动状态")
        
        print("OCR处理线程测试完成")

def main():
    unittest.main()

if __name__ == "__main__":
    main()
