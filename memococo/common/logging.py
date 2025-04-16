"""
日志记录模块

提供统一的日志记录功能，支持不同组件的日志记录
"""

import os
import logging
from logging.handlers import RotatingFileHandler

class LoggerFactory:
    """日志工厂类，用于创建和管理日志对象"""
    
    # 日志格式器
    _formatters = {
        "main": logging.Formatter('%(asctime)s - [MAIN] - %(levelname)s - %(message)s'),
        "screenshot": logging.Formatter('%(asctime)s - [SCREENSHOT] - %(levelname)s - %(message)s'),
        "ocr": logging.Formatter('%(asctime)s - [OCR] - %(levelname)s - %(message)s'),
        "database": logging.Formatter('%(asctime)s - [DATABASE] - %(levelname)s - %(message)s'),
        "utils": logging.Formatter('%(asctime)s - [UTILS] - %(levelname)s - %(message)s'),
    }
    
    # 日志处理器
    _handlers = {}
    
    # 日志对象
    _loggers = {}
    
    @classmethod
    def initialize(cls, log_file, max_bytes=10*1024*1024, backup_count=1):
        """初始化日志工厂
        
        Args:
            log_file: 日志文件路径
            max_bytes: 单个日志文件最大字节数
            backup_count: 备份文件数量
        """
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建文件处理器
        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        file_handler.setLevel(logging.DEBUG)
        
        # 保存处理器
        cls._handlers["console"] = console_handler
        cls._handlers["file"] = file_handler
    
    @classmethod
    def get_logger(cls, name, component="main"):
        """获取日志对象
        
        Args:
            name: 日志对象名称
            component: 组件名称，用于选择日志格式器
            
        Returns:
            日志对象
        """
        # 如果日志对象已存在，直接返回
        if name in cls._loggers:
            return cls._loggers[name]
        
        # 创建日志对象
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # 获取日志格式器
        formatter = cls._formatters.get(component, cls._formatters["main"])
        
        # 添加处理器
        for handler in cls._handlers.values():
            handler_copy = handler.__class__(handler.baseFilename) if hasattr(handler, 'baseFilename') else handler.__class__()
            handler_copy.setLevel(handler.level)
            handler_copy.setFormatter(formatter)
            logger.addHandler(handler_copy)
        
        # 保存日志对象
        cls._loggers[name] = logger
        
        return logger

def initialize_logging(log_file):
    """初始化日志记录
    
    Args:
        log_file: 日志文件路径
    """
    LoggerFactory.initialize(log_file)

def get_logger(name, component="main"):
    """获取日志对象
    
    Args:
        name: 日志对象名称
        component: 组件名称，用于选择日志格式器
        
    Returns:
        日志对象
    """
    return LoggerFactory.get_logger(name, component)
