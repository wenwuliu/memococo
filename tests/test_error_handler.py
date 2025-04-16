"""
错误处理测试模块

测试错误处理机制的功能
"""

import unittest
import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memococo.common.error_handler import (
    MemoCocoError, ConfigError, DatabaseError, OCRError, ScreenshotError,
    FileError, SystemError, ErrorHandler, initialize_error_handler,
    safe_call, with_error_handling
)

class TestErrorHandler(unittest.TestCase):
    """测试错误处理器"""

    def setUp(self):
        """测试前的准备工作"""
        # 创建一个测试日志记录器
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.DEBUG)
        
        # 创建一个控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # 创建一个格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # 添加处理器到日志记录器
        self.logger.addHandler(console_handler)
        
        # 初始化错误处理器
        initialize_error_handler(logger=self.logger, show_in_console=True, show_in_ui=False)
        
        # 记录测试开始
        self.logger.info("Starting error handler tests")
    
    def test_basic_error(self):
        """测试基本错误"""
        # 创建一个基本错误
        error = MemoCocoError("测试错误")
        
        # 验证错误消息
        self.assertEqual(str(error), "测试错误")
        
        # 创建一个带有详细信息的错误
        error_with_details = MemoCocoError("测试错误", {"key": "value"})
        
        # 验证错误消息包含详细信息
        self.assertIn("详情", str(error_with_details))
        self.assertIn("key", str(error_with_details))
    
    def test_specific_errors(self):
        """测试特定类型的错误"""
        # 测试配置错误
        config_error = ConfigError("配置错误")
        self.assertIsInstance(config_error, MemoCocoError)
        
        # 测试数据库错误
        db_error = DatabaseError("数据库错误")
        self.assertIsInstance(db_error, MemoCocoError)
        
        # 测试OCR错误
        ocr_error = OCRError("OCR错误")
        self.assertIsInstance(ocr_error, MemoCocoError)
        
        # 测试截图错误
        screenshot_error = ScreenshotError("截图错误")
        self.assertIsInstance(screenshot_error, MemoCocoError)
        
        # 测试文件错误
        file_error = FileError("文件错误")
        self.assertIsInstance(file_error, MemoCocoError)
        
        # 测试系统错误
        system_error = SystemError("系统错误")
        self.assertIsInstance(system_error, MemoCocoError)
    
    def test_error_handler(self):
        """测试错误处理器"""
        # 定义一个测试处理函数
        def test_handler(exception):
            return f"Handled: {exception}"
        
        # 注册处理函数
        ErrorHandler.register(ConfigError, test_handler)
        
        # 测试处理函数
        result = ErrorHandler.handle(ConfigError("测试配置错误"))
        self.assertEqual(result, "Handled: 测试配置错误")
        
        # 测试未注册的错误类型
        try:
            ErrorHandler.handle(ValueError("测试值错误"))
            self.fail("应该抛出异常")
        except Exception as e:
            self.assertIsInstance(e, ValueError)
    
    def test_safe_call(self):
        """测试安全调用函数"""
        # 定义一个可能抛出异常的函数
        def risky_function(should_fail=False):
            if should_fail:
                raise ConfigError("函数失败")
            return "函数成功"
        
        # 定义一个错误处理函数
        def error_handler(exception):
            return f"错误已处理: {exception}"
        
        # 注册错误处理函数
        ErrorHandler.register(ConfigError, error_handler)
        
        # 测试成功调用
        result = safe_call(risky_function, should_fail=False)
        self.assertEqual(result, "函数成功")
        
        # 测试失败调用
        result = safe_call(risky_function, should_fail=True)
        self.assertEqual(result, "错误已处理: 函数失败")
    
    def test_with_error_handling(self):
        """测试错误处理装饰器"""
        # 定义一个错误处理函数
        def error_handler(exception):
            return f"装饰器处理: {exception}"
        
        # 注册错误处理函数
        ErrorHandler.register(ConfigError, error_handler)
        
        # 定义一个使用装饰器的函数
        @with_error_handling({"test": "decorator"})
        def decorated_function(should_fail=False):
            if should_fail:
                raise ConfigError("装饰器函数失败")
            return "装饰器函数成功"
        
        # 测试成功调用
        result = decorated_function(should_fail=False)
        self.assertEqual(result, "装饰器函数成功")
        
        # 测试失败调用
        result = decorated_function(should_fail=True)
        self.assertEqual(result, "装饰器处理: 装饰器函数失败")
    
    def test_error_recovery(self):
        """测试错误恢复策略"""
        # 定义一个恢复策略
        def recovery_strategy(exception):
            return "已恢复"
        
        # 注册恢复策略
        ErrorHandler.register_recovery_strategy(DatabaseError, recovery_strategy)
        
        # 测试恢复策略
        result = ErrorHandler.try_recovery(DatabaseError("数据库错误"))
        self.assertEqual(result, "已恢复")
        
        # 测试未注册的错误类型
        result = ErrorHandler.try_recovery(ValueError("值错误"))
        self.assertIsNone(result)
    
    def tearDown(self):
        """测试后的清理工作"""
        # 记录测试结束
        self.logger.info("Finished error handler tests")

if __name__ == "__main__":
    unittest.main()
