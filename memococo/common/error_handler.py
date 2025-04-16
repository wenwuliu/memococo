"""
错误处理模块

提供统一的错误处理功能，包括自定义异常类和全局异常处理器
"""

import sys
import traceback
from typing import Callable, Any, Optional, Type

# 自定义异常类
class MemoCocoError(Exception):
    """MemoCoco基础异常类"""
    pass

class ConfigError(MemoCocoError):
    """配置错误"""
    pass

class DatabaseError(MemoCocoError):
    """数据库错误"""
    pass

class OCRError(MemoCocoError):
    """OCR错误"""
    pass

class ScreenshotError(MemoCocoError):
    """截图错误"""
    pass

class FileError(MemoCocoError):
    """文件操作错误"""
    pass

class SystemError(MemoCocoError):
    """系统错误"""
    pass

# 全局异常处理器
class ErrorHandler:
    """错误处理器"""
    
    # 错误处理函数
    _handlers = {}
    
    # 默认错误处理函数
    _default_handler = None
    
    @classmethod
    def register(cls, exception_type: Type[Exception], handler: Callable[[Exception], Any]) -> None:
        """注册错误处理函数
        
        Args:
            exception_type: 异常类型
            handler: 处理函数
        """
        cls._handlers[exception_type] = handler
    
    @classmethod
    def set_default_handler(cls, handler: Callable[[Exception], Any]) -> None:
        """设置默认错误处理函数
        
        Args:
            handler: 处理函数
        """
        cls._default_handler = handler
    
    @classmethod
    def handle(cls, exception: Exception) -> Any:
        """处理异常
        
        Args:
            exception: 异常对象
            
        Returns:
            处理结果
        """
        # 查找异常类型的处理函数
        handler = None
        for exception_type, h in cls._handlers.items():
            if isinstance(exception, exception_type):
                handler = h
                break
        
        # 如果没有找到处理函数，使用默认处理函数
        if handler is None:
            handler = cls._default_handler
        
        # 如果有处理函数，调用处理函数
        if handler is not None:
            return handler(exception)
        else:
            # 如果没有处理函数，重新抛出异常
            raise exception
    
    @classmethod
    def try_except(cls, func: Callable, *args, **kwargs) -> Any:
        """尝试执行函数，捕获异常并处理
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return cls.handle(e)

def default_error_handler(exception: Exception) -> None:
    """默认错误处理函数
    
    Args:
        exception: 异常对象
    """
    print(f"Error: {exception}")
    traceback.print_exc()

def initialize_error_handler() -> None:
    """初始化错误处理器"""
    ErrorHandler.set_default_handler(default_error_handler)

def safe_call(func: Callable, *args, **kwargs) -> Any:
    """安全调用函数，捕获异常并处理
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果
    """
    return ErrorHandler.try_except(func, *args, **kwargs)
