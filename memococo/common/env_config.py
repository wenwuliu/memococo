"""
环境变量配置模块

提供从环境变量中读取配置的功能
"""

import os
import json
from typing import Dict, Any, Optional, List, Union

def get_env_prefix() -> str:
    """获取环境变量前缀
    
    Returns:
        str: 环境变量前缀
    """
    return "MEMOCOCO_"

def env_to_config_key(env_key: str) -> str:
    """将环境变量键名转换为配置键名
    
    Args:
        env_key: 环境变量键名
        
    Returns:
        str: 配置键名
    """
    # 移除前缀
    prefix = get_env_prefix()
    if env_key.startswith(prefix):
        key = env_key[len(prefix):]
    else:
        key = env_key
    
    # 转换为小写
    key = key.lower()
    
    # 将下划线转换为点号（用于嵌套配置）
    key = key.replace("__", ".")
    
    return key

def parse_env_value(value: str) -> Any:
    """解析环境变量值
    
    Args:
        value: 环境变量值
        
    Returns:
        Any: 解析后的值
    """
    # 尝试解析为JSON
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        # 如果不是有效的JSON，则按字符串处理
        return value

def get_env_config() -> Dict[str, Any]:
    """从环境变量中获取配置
    
    Returns:
        Dict[str, Any]: 配置字典
    """
    config = {}
    prefix = get_env_prefix()
    
    # 遍历所有环境变量
    for key, value in os.environ.items():
        # 检查是否是配置环境变量
        if key.startswith(prefix):
            config_key = env_to_config_key(key)
            config_value = parse_env_value(value)
            config[config_key] = config_value
    
    return config

def update_config_from_env(config: Dict[str, Any]) -> Dict[str, Any]:
    """使用环境变量更新配置
    
    Args:
        config: 原始配置
        
    Returns:
        Dict[str, Any]: 更新后的配置
    """
    env_config = get_env_config()
    
    # 更新配置
    for key, value in env_config.items():
        # 处理嵌套配置
        if "." in key:
            parts = key.split(".")
            current = config
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            config[key] = value
    
    return config
