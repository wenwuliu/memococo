"""
文件操作模块

提供文件和目录操作的通用功能
"""

import os
import shutil
import datetime
from typing import List, Optional

def ensure_directory_exists(path: str) -> bool:
    """确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        bool: 操作是否成功
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        return True
    except Exception as e:
        print(f"创建目录失败: {path}, 错误: {e}")
        return False

def get_file_size(file_path: str) -> int:
    """获取文件大小
    
    Args:
        file_path: 文件路径
        
    Returns:
        int: 文件大小（字节）
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        print(f"获取文件大小失败: {file_path}, 错误: {e}")
        return 0

def get_directory_size(directory: str) -> int:
    """获取目录大小
    
    Args:
        directory: 目录路径
        
    Returns:
        int: 目录大小（字节）
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                total_size += get_file_size(file_path)
        return total_size
    except Exception as e:
        print(f"获取目录大小失败: {directory}, 错误: {e}")
        return 0

def format_size(size_bytes: int) -> str:
    """格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小
    """
    # 定义单位
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    
    # 计算单位
    unit_index = 0
    size = float(size_bytes)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    # 格式化输出
    return f"{size:.2f} {units[unit_index]}"

def list_files(directory: str, extension: Optional[str] = None) -> List[str]:
    """列出目录中的文件
    
    Args:
        directory: 目录路径
        extension: 文件扩展名过滤器
        
    Returns:
        List[str]: 文件路径列表
    """
    files = []
    try:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                if extension is None or file.endswith(extension):
                    files.append(file_path)
        return files
    except Exception as e:
        print(f"列出文件失败: {directory}, 错误: {e}")
        return []

def list_directories(directory: str) -> List[str]:
    """列出目录中的子目录
    
    Args:
        directory: 目录路径
        
    Returns:
        List[str]: 子目录路径列表
    """
    directories = []
    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                directories.append(item_path)
        return directories
    except Exception as e:
        print(f"列出目录失败: {directory}, 错误: {e}")
        return []

def get_date_directory(base_directory: str, date: datetime.datetime) -> str:
    """获取日期目录路径
    
    Args:
        base_directory: 基础目录路径
        date: 日期对象
        
    Returns:
        str: 日期目录路径
    """
    # 格式化日期为年/月/日
    date_path = date.strftime("%Y/%m/%d")
    # 替换路径分隔符
    date_path = date_path.replace("/", os.sep)
    # 拼接完整路径
    return os.path.join(base_directory, date_path)

def copy_file(source: str, destination: str) -> bool:
    """复制文件
    
    Args:
        source: 源文件路径
        destination: 目标文件路径
        
    Returns:
        bool: 操作是否成功
    """
    try:
        # 确保目标目录存在
        destination_dir = os.path.dirname(destination)
        ensure_directory_exists(destination_dir)
        # 复制文件
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        print(f"复制文件失败: {source} -> {destination}, 错误: {e}")
        return False

def move_file(source: str, destination: str) -> bool:
    """移动文件
    
    Args:
        source: 源文件路径
        destination: 目标文件路径
        
    Returns:
        bool: 操作是否成功
    """
    try:
        # 确保目标目录存在
        destination_dir = os.path.dirname(destination)
        ensure_directory_exists(destination_dir)
        # 移动文件
        shutil.move(source, destination)
        return True
    except Exception as e:
        print(f"移动文件失败: {source} -> {destination}, 错误: {e}")
        return False

def delete_file(file_path: str) -> bool:
    """删除文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 操作是否成功
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        print(f"删除文件失败: {file_path}, 错误: {e}")
        return False

def delete_directory(directory: str) -> bool:
    """删除目录
    
    Args:
        directory: 目录路径
        
    Returns:
        bool: 操作是否成功
    """
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        return True
    except Exception as e:
        print(f"删除目录失败: {directory}, 错误: {e}")
        return False
