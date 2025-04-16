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
    def __init__(self, message: str = "", details: dict = None, cause: Exception = None):
        self.message = message
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)

    def __str__(self):
        result = self.message
        if self.details:
            result += f" - 详情: {self.details}"
        if self.cause:
            result += f" - 原因: {str(self.cause)}"
        return result

# 配置相关异常
class ConfigError(MemoCocoError):
    """配置错误"""
    pass

class ConfigNotFoundError(ConfigError):
    """配置文件不存在"""
    pass

class ConfigParseError(ConfigError):
    """配置文件解析错误"""
    pass

class ConfigValidationError(ConfigError):
    """配置验证错误"""
    pass

# 数据库相关异常
class DatabaseError(MemoCocoError):
    """数据库错误"""
    pass

class DatabaseConnectionError(DatabaseError):
    """数据库连接错误"""
    pass

class DatabaseQueryError(DatabaseError):
    """数据库查询错误"""
    pass

class DatabaseTransactionError(DatabaseError):
    """数据库事务错误"""
    pass

# OCR相关异常
class OCRError(MemoCocoError):
    """文字识别错误"""
    pass

class OCREngineError(OCRError):
    """文字识别引擎错误"""
    pass

class OCRProcessingError(OCRError):
    """文字识别处理错误"""
    pass

class OCRTimeoutError(OCRError):
    """文字识别超时"""
    pass

# 截图相关异常
class ScreenshotError(MemoCocoError):
    """截图错误"""
    pass

class ScreenshotCaptureError(ScreenshotError):
    """截图捕获错误"""
    pass

class ScreenshotSaveError(ScreenshotError):
    """截图保存错误"""
    pass

class ScreenshotProcessingError(ScreenshotError):
    """截图处理错误"""
    pass

# 文件相关异常
class FileError(MemoCocoError):
    """文件操作错误"""
    pass

class FileNotFoundError(FileError):
    """文件不存在错误"""
    pass

class FilePermissionError(FileError):
    """文件权限错误"""
    pass

class FileFormatError(FileError):
    """文件格式错误"""
    pass

class FileIOError(FileError):
    """文件输入输出错误"""
    pass

# 系统相关异常
class SystemError(MemoCocoError):
    """系统错误"""
    pass

class ResourceError(SystemError):
    """资源错误"""
    pass

class NetworkError(SystemError):
    """网络错误"""
    pass

class PermissionError(SystemError):
    """权限错误"""
    pass

# 用户界面相关异常
class UIError(MemoCocoError):
    """用户界面错误"""
    pass

class ValidationError(MemoCocoError):
    """数据验证错误"""
    pass

# 全局异常处理器
class ErrorHandler:
    """错误处理器

    提供统一的错误处理机制，包括错误捕获、处理和日志记录。
    支持按异常类型注册不同的处理函数。
    """

    # 错误处理函数
    _handlers = {}

    # 默认错误处理函数
    _default_handler = None

    # 错误日志记录器
    _logger = None

    # 是否在控制台显示错误
    _show_in_console = True

    # 是否在用户界面显示错误
    _show_in_ui = False

    # 错误恢复策略
    _recovery_strategies = {}

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
    def set_logger(cls, logger) -> None:
        """设置日志记录器

        Args:
            logger: 日志记录器
        """
        cls._logger = logger

    @classmethod
    def set_ui_display(cls, show: bool) -> None:
        """设置是否在用户界面显示错误

        Args:
            show: 是否显示
        """
        cls._show_in_ui = show

    @classmethod
    def set_console_display(cls, show: bool) -> None:
        """设置是否在控制台显示错误

        Args:
            show: 是否显示
        """
        cls._show_in_console = show

    @classmethod
    def register_recovery_strategy(cls, exception_type: Type[Exception], strategy: Callable[[Exception], Any]) -> None:
        """注册错误恢复策略

        Args:
            exception_type: 异常类型
            strategy: 恢复策略函数
        """
        cls._recovery_strategies[exception_type] = strategy

    @classmethod
    def log_error(cls, exception: Exception, context: dict = None) -> None:
        """记录错误日志

        Args:
            exception: 异常对象
            context: 错误上下文信息
        """
        if cls._logger is None:
            return

        # 构建错误消息
        error_message = str(exception)
        if context:
            error_message += f" - 上下文: {context}"

        # 记录错误堆栈
        error_traceback = traceback.format_exc()

        # 记录日志
        cls._logger.error(error_message)
        cls._logger.debug(error_traceback)

    @classmethod
    def handle(cls, exception: Exception, context: dict = None) -> Any:
        """处理异常

        Args:
            exception: 异常对象
            context: 错误上下文信息

        Returns:
            处理结果
        """
        # 记录错误日志
        cls.log_error(exception, context)

        # 在控制台显示错误
        if cls._show_in_console:
            print(f"Error: {exception}")
            if context:
                print(f"Context: {context}")
            traceback.print_exc()

        # 尝试恢复
        recovery_result = cls.try_recovery(exception)
        if recovery_result is not None:
            return recovery_result

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
    def try_recovery(cls, exception: Exception) -> Any:
        """尝试恢复错误

        Args:
            exception: 异常对象

        Returns:
            恢复结果，如果没有恢复策略或恢复失败则返回None
        """
        # 查找异常类型的恢复策略
        strategy = None
        for exception_type, s in cls._recovery_strategies.items():
            if isinstance(exception, exception_type):
                strategy = s
                break

        # 如果有恢复策略，尝试恢复
        if strategy is not None:
            try:
                return strategy(exception)
            except Exception as e:
                if cls._logger:
                    cls._logger.error(f"恢复失败: {e}")
                return None

        return None

    @classmethod
    def try_except(cls, func: Callable, *args, context: dict = None, **kwargs) -> Any:
        """尝试执行函数，捕获异常并处理

        Args:
            func: 要执行的函数
            *args: 函数参数
            context: 错误上下文信息
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return cls.handle(e, context)

    @classmethod
    def with_context(cls, context: dict = None):
        """创建一个带有上下文的错误处理装饰器

        Args:
            context: 错误上下文信息

        Returns:
            装饰器函数
        """
        def decorator(func):
            from functools import wraps
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    return cls.handle(e, context)
            return wrapper
        return decorator

def default_error_handler(exception: Exception) -> None:
    """默认错误处理函数

    Args:
        exception: 异常对象
    """
    print(f"Error: {exception}")
    traceback.print_exc()

def initialize_error_handler(logger=None, show_in_console=True, show_in_ui=False) -> None:
    """初始化错误处理器

    Args:
        logger: 日志记录器
        show_in_console: 是否在控制台显示错误
        show_in_ui: 是否在用户界面显示错误
    """
    ErrorHandler.set_default_handler(default_error_handler)
    if logger:
        ErrorHandler.set_logger(logger)
    ErrorHandler.set_console_display(show_in_console)
    ErrorHandler.set_ui_display(show_in_ui)

def safe_call(func: Callable, *args, context: dict = None, **kwargs) -> Any:
    """安全调用函数，捕获异常并处理

    Args:
        func: 要执行的函数
        *args: 函数参数
        context: 错误上下文信息
        **kwargs: 函数关键字参数

    Returns:
        函数执行结果
    """
    return ErrorHandler.try_except(func, *args, context=context, **kwargs)

def with_error_handling(context: dict = None):
    """错误处理装饰器

    Args:
        context: 错误上下文信息

    Returns:
        装饰器函数
    """
    return ErrorHandler.with_context(context)
