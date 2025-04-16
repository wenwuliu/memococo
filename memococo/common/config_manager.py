"""
配置管理模块

提供统一的配置管理功能，支持配置的读取、保存和验证
"""

import os
import sys
import json
import toml
from typing import Dict, Any, Optional

class ConfigManager:
    """配置管理类"""
    
    def __init__(self, config_file: str, default_config: Dict[str, Any]):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径
            default_config: 默认配置
        """
        self.config_file = config_file
        self.default_config = default_config
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        # 如果配置文件存在，从文件加载配置
        if os.path.exists(self.config_file):
            try:
                # 根据文件扩展名选择解析方法
                if self.config_file.endswith('.toml'):
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        return toml.load(f)
                elif self.config_file.endswith('.json'):
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    print(f"不支持的配置文件格式: {self.config_file}")
                    return self.default_config.copy()
            except Exception as e:
                print(f"加载配置文件失败: {self.config_file}, 错误: {e}")
                return self.default_config.copy()
        else:
            # 如果配置文件不存在，使用默认配置并保存
            config = self.default_config.copy()
            self.save_config(config)
            return config
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """保存配置
        
        Args:
            config: 要保存的配置，如果为None则保存当前配置
            
        Returns:
            bool: 操作是否成功
        """
        if config is None:
            config = self.config
        
        try:
            # 确保配置文件目录存在
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 根据文件扩展名选择序列化方法
            if self.config_file.endswith('.toml'):
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    toml.dump(config, f)
            elif self.config_file.endswith('.json'):
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            else:
                print(f"不支持的配置文件格式: {self.config_file}")
                return False
            
            # 更新当前配置
            self.config = config
            return True
        except Exception as e:
            print(f"保存配置文件失败: {self.config_file}, 错误: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置项键名
            default: 默认值
            
        Returns:
            配置项值
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项
        
        Args:
            key: 配置项键名
            value: 配置项值
        """
        self.config[key] = value
    
    def update(self, config: Dict[str, Any]) -> None:
        """更新配置
        
        Args:
            config: 要更新的配置
        """
        self.config.update(config)
    
    def reset(self) -> None:
        """重置配置为默认值"""
        self.config = self.default_config.copy()
        self.save_config()

def get_app_data_folder(app_name: str) -> str:
    """获取应用数据目录
    
    Args:
        app_name: 应用名称
        
    Returns:
        str: 应用数据目录路径
    """
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA")
        if not appdata:
            raise EnvironmentError("APPDATA environment variable is not set.")
        path = os.path.join(appdata, app_name)
    elif sys.platform == "darwin":
        home = os.path.expanduser("~")
        path = os.path.join(home, "Library", "Application Support", app_name)
    else:
        home = os.path.expanduser("~")
        path = os.path.join(home, ".local", "share", app_name)
    
    # 确保目录存在
    if not os.path.exists(path):
        os.makedirs(path)
    
    return path
