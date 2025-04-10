"""
测试CPU友好型OCR处理

这个脚本用于测试OCR处理器在高CPU负载下的行为
"""

import unittest
import time
import sys
import os
import threading
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memococo.ocr_processor import process_batch_ocr, process_ocr_task

class TestCpuFriendlyOcr(unittest.TestCase):
    """测试CPU友好型OCR处理"""
    
    @patch('psutil.cpu_percent')
    @patch('memococo.utils.get_cpu_temperature')
    def test_skip_on_high_cpu(self, mock_get_temp, mock_cpu_percent):
        """测试CPU占用率高时跳过OCR处理"""
        # 模拟高CPU占用率
        mock_cpu_percent.return_value = 60  # 设置为60%，超过新的50%阈值
        mock_get_temp.return_value = 60
        
        # 创建一个模拟的数据库条目
        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.timestamp = int(time.time())
        
        # 调用处理函数
        result = process_ocr_task(mock_entry)
        
        # 验证结果
        self.assertEqual(result, "SKIPPED", "当CPU占用率高时应该跳过处理并返回SKIPPED")
        print("CPU占用率高时成功跳过OCR处理")
    
    @patch('psutil.cpu_percent')
    @patch('memococo.utils.get_cpu_temperature')
    @patch('memococo.ocr_processor.get_batch_empty_text')
    def test_batch_skip_on_high_cpu(self, mock_get_entries, mock_get_temp, mock_cpu_percent):
        """测试批处理时CPU占用率高时跳过OCR处理"""
        # 模拟高CPU占用率
        mock_cpu_percent.return_value = 60  # 设置为60%，超过新的50%阈值
        mock_get_temp.return_value = 60
        
        # 调用批处理函数
        result = process_batch_ocr(batch_size=3)
        
        # 验证结果
        self.assertEqual(result, 0, "当CPU占用率高时应该跳过处理并返回0")
        # 验证get_batch_empty_text没有被调用，说明在CPU检查阶段就跳过了
        mock_get_entries.assert_not_called()
        print("批处理时CPU占用率高时成功跳过OCR处理")
    
    @patch('psutil.cpu_percent')
    @patch('memococo.utils.get_cpu_temperature')
    @patch('memococo.ocr_processor.get_batch_empty_text')
    def test_batch_proceed_on_normal_load(self, mock_get_entries, mock_get_temp, mock_cpu_percent):
        """测试批处理时正常负载下继续OCR处理"""
        # 模拟正常CPU负载
        mock_cpu_percent.return_value = 30  # 设置为30%，低于50%阈值
        mock_get_temp.return_value = 50
        
        # 模拟空数据库（没有条目需要处理）
        mock_get_entries.return_value = []
        
        # 调用批处理函数
        result = process_batch_ocr(batch_size=3)
        
        # 验证结果
        self.assertEqual(result, 0, "当没有条目需要处理时应该返回0")
        # 验证get_batch_empty_text被调用，说明CPU检查通过
        mock_get_entries.assert_called_once()
        print("正常负载时成功继续OCR处理流程")

def main():
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()
