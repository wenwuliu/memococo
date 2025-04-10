"""
测试OCR处理的启动和停止阈值

这个脚本用于测试OCR处理的启动和停止阈值功能
"""

import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memococo.database import create_db, insert_entry
from memococo.ocr_processor import ocr_processor_thread, _OCR_START_THRESHOLD, _OCR_STOP_THRESHOLD

class TestOcrThreshold(unittest.TestCase):
    """测试OCR处理的启动和停止阈值"""
    
    @patch('memococo.ocr_processor.get_empty_text_count')
    @patch('memococo.ocr_processor.process_batch_ocr')
    @patch('memococo.ocr_processor._ocr_processing_enabled', False)
    def test_start_ocr_when_above_threshold(self, mock_process_batch, mock_get_count):
        """测试当条目数量超过启动阈值时启动OCR处理"""
        # 模拟条目数量超过启动阈值
        mock_get_count.return_value = _OCR_START_THRESHOLD + 10
        
        # 创建一个模拟的线程对象
        mock_thread = MagicMock()
        
        # 调用一次OCR处理线程函数（模拟一次循环）
        with patch('time.sleep'):  # 避免实际休眠
            with patch('memococo.ocr_processor._ocr_processing_enabled', False) as mock_enabled:
                # 执行一次循环
                try:
                    # 设置一个超时，避免无限循环
                    ocr_processor_thread.__wrapped__ = lambda *args, **kwargs: None
                    ocr_processor_thread(idle_time=0.1, max_batch_size=1)
                except AttributeError:
                    pass
                
                # 验证OCR处理已启动
                self.assertTrue(mock_enabled, "当条目数量超过启动阈值时应该启动OCR处理")
                print(f"测试通过：当条目数量超过启动阈值({_OCR_START_THRESHOLD})时启动OCR处理")
    
    @patch('memococo.ocr_processor.get_empty_text_count')
    @patch('memococo.ocr_processor.process_batch_ocr')
    @patch('memococo.ocr_processor._ocr_processing_enabled', True)
    def test_stop_ocr_when_below_threshold(self, mock_process_batch, mock_get_count):
        """测试当条目数量低于停止阈值时停止OCR处理"""
        # 模拟条目数量低于停止阈值
        mock_get_count.return_value = _OCR_STOP_THRESHOLD - 1
        
        # 创建一个模拟的线程对象
        mock_thread = MagicMock()
        
        # 调用一次OCR处理线程函数（模拟一次循环）
        with patch('time.sleep'):  # 避免实际休眠
            with patch('memococo.ocr_processor._ocr_processing_enabled', True) as mock_enabled:
                # 执行一次循环
                try:
                    # 设置一个超时，避免无限循环
                    ocr_processor_thread.__wrapped__ = lambda *args, **kwargs: None
                    ocr_processor_thread(idle_time=0.1, max_batch_size=1)
                except AttributeError:
                    pass
                
                # 验证OCR处理已停止
                self.assertFalse(mock_enabled, "当条目数量低于停止阈值时应该停止OCR处理")
                print(f"测试通过：当条目数量低于停止阈值({_OCR_STOP_THRESHOLD})时停止OCR处理")

def main():
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()
