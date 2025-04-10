"""
测试截图间隔时间

这个脚本用于测试截图间隔时间是否已经修改为5秒
"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memococo.screenshot import record_screenshots_thread
from memococo.app import start_background_threads

class TestScreenshotInterval(unittest.TestCase):
    """测试截图间隔时间"""
    
    def test_default_interval(self):
        """测试默认间隔时间是否为5秒"""
        # 获取函数定义中的默认参数
        import inspect
        signature = inspect.signature(record_screenshots_thread)
        default_idle_time = signature.parameters['idle_time'].default
        
        # 验证默认间隔时间是否为5秒
        self.assertEqual(default_idle_time, 5, "截图函数的默认间隔时间应该是5秒")
        print(f"测试通过：截图函数的默认间隔时间是 {default_idle_time} 秒")

def main():
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()
