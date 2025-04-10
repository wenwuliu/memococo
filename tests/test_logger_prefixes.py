"""
测试日志前缀

这个脚本用于测试不同模块的日志输出是否正确添加了前缀
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memococo.config import main_logger, screenshot_logger, ocr_logger

def test_logger_prefixes():
    """测试不同模块的日志前缀"""
    print("\n测试日志前缀...")
    
    # 测试主应用日志
    main_logger.info("这是来自主应用的测试日志")
    
    # 测试截图模块日志
    screenshot_logger.info("这是来自截图模块的测试日志")
    
    # 测试OCR模块日志
    ocr_logger.info("这是来自OCR模块的测试日志")
    
    print("日志测试完成，请检查控制台输出和日志文件")

if __name__ == "__main__":
    test_logger_prefixes()
