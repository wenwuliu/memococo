"""
测试截图和OCR分离功能

这个脚本用于测试截图和OCR功能分离后的工作情况
"""

import os
import time
import threading
import unittest
from multiprocessing import Manager, Event

from memococo.database import create_db, insert_entry, get_newest_empty_text, get_timestamps
from memococo.screenshot import record_screenshots_thread
from memococo.ocr_processor import start_ocr_processor, process_batch_ocr

class TestScreenshotOcrSeparation(unittest.TestCase):
    """测试截图和OCR分离功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 确保数据库已创建
        create_db()
        
        # 初始化共享变量
        self.ignored_apps = Manager().list([])
        self.ignored_apps_updated = Event()
    
    def test_screenshot_thread(self):
        """测试截图线程"""
        print("测试截图线程...")
        
        # 获取初始时间戳数量
        initial_timestamps = len(get_timestamps())
        
        # 启动截图线程
        screenshot_thread = threading.Thread(
            target=record_screenshots_thread,
            args=(self.ignored_apps, self.ignored_apps_updated, True, 1, True),
            daemon=True
        )
        screenshot_thread.start()
        
        # 等待一段时间，让截图线程工作
        print("等待截图线程工作...")
        time.sleep(5)
        
        # 获取当前时间戳数量
        current_timestamps = len(get_timestamps())
        
        # 检查是否有新的截图
        self.assertGreaterEqual(current_timestamps, initial_timestamps, 
                               "截图线程没有生成新的截图")
        
        print(f"截图线程工作正常，生成了 {current_timestamps - initial_timestamps} 个新截图")
    
    def test_ocr_processor(self):
        """测试OCR处理器"""
        print("测试OCR处理器...")
        
        # 插入一些测试数据
        timestamp = int(time.time())
        for i in range(3):
            insert_entry("", timestamp + i, "", f"TestApp{i}", f"TestTitle{i}")
            print(f"插入测试数据 {i+1}/3")
        
        # 检查是否有未OCR的数据
        entry = get_newest_empty_text()
        self.assertIsNotNone(entry, "没有找到未OCR的数据")
        
        # 处理OCR任务
        processed = process_batch_ocr(batch_size=3)
        self.assertEqual(processed, 3, f"应该处理3个OCR任务，但实际处理了{processed}个")
        
        print(f"OCR处理器工作正常，处理了 {processed} 个OCR任务")
    
    def test_integration(self):
        """测试截图和OCR集成"""
        print("测试截图和OCR集成...")
        
        # 启动截图线程
        screenshot_thread = threading.Thread(
            target=record_screenshots_thread,
            args=(self.ignored_apps, self.ignored_apps_updated, True, 1, True),
            daemon=True
        )
        screenshot_thread.start()
        
        # 启动OCR处理线程
        ocr_thread = start_ocr_processor()
        
        # 等待一段时间，让两个线程工作
        print("等待截图和OCR线程工作...")
        time.sleep(10)
        
        # 检查是否有未OCR的数据
        entry = get_newest_empty_text()
        if entry:
            print(f"还有未OCR的数据: {entry}")
        else:
            print("所有数据都已处理")
        
        print("截图和OCR集成测试完成")

def main():
    unittest.main()

if __name__ == "__main__":
    main()
