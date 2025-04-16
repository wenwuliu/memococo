"""
配置模块

提供应用程序配置的读取、保存和管理功能
"""

import os
import sys
import argparse
import toml
import logging
from typing import Dict, Any

# 导入共用模块
from memococo.common.config_manager import get_app_data_folder, ConfigManager
from memococo.common.file_utils import ensure_directory_exists
from memococo.common.env_config import update_config_from_env
from memococo.config_schema import CONFIG_SCHEMA, DEFAULT_CONFIG

# 应用信息
app_name_cn = "时光胶囊"
app_name_en = "MemoCoco"
main_app_name = app_name_en
app_version = "2.2.10"

# 命令行参数解析
parser = argparse.ArgumentParser(description=main_app_name)

parser.add_argument(
    "--storage-path",
    default=None,
    help="Path to store the screenshots and database",
)

parser.add_argument(
    "--primary-monitor-only",
    action="store_true",
    help="Only record the primary monitor",
    default=False,
)

parser.add_argument(
    "--config",
    default=None,
    help="Path to the configuration file",
)

args = parser.parse_args()

# 确定应用数据目录
if args.storage_path:
    appdata_folder = args.storage_path
else:
    appdata_folder = get_app_data_folder(main_app_name)

# 确定配置文件路径
if args.config:
    config_path = args.config
else:
    config_path = os.path.join(appdata_folder, "config.toml")

# 数据库以app_name_en.db命名
db_path = os.path.join(appdata_folder, f"{app_name_en}.db")
screenshots_path = os.path.join(appdata_folder, "screenshots")

# 确保目录存在
ensure_directory_exists(screenshots_path)

# 初始化日志记录
from memococo.common.logging import initialize_logging, get_logger

# 初始化日志记录
log_file = os.path.join(appdata_folder, "memococo.log")
initialize_logging(log_file)

# 获取日志对象
config_logger = get_logger("memococo.config", "config")
main_logger = get_logger("memococo.main", "main")
screenshot_logger = get_logger("memococo.screenshot", "screenshot")
ocr_logger = get_logger("memococo.ocr", "ocr")

# 兼容旧代码
logger = main_logger

# 使用环境变量更新默认配置
env_updated_config = update_config_from_env(DEFAULT_CONFIG.copy())

# 创建配置管理器
config_manager = ConfigManager(
    config_file=config_path,
    default_config=env_updated_config,
    schema=CONFIG_SCHEMA,
    logger=config_logger
)

# 如果指定了primary_monitor_only参数，更新配置
if args.primary_monitor_only:
    config_manager.set("primary_monitor_only", True)

# 启动配置热加载
config_manager.start_watching()

def get_settings() -> Dict[str, Any]:
    """获取配置

    Returns:
        Dict[str, Any]: 配置字典
    """
    return config_manager.config

def save_settings(config: Dict[str, Any]) -> None:
    """保存配置

    Args:
        config: 要保存的配置
    """
    config_manager.update(config)

# 注册配置变更回调函数
def config_changed_callback(config: Dict[str, Any]) -> None:
    """配置变更回调函数

    Args:
        config: 新的配置
    """
    config_logger.info("配置已变更，正在应用新配置...")

    # 这里可以添加配置变更后的处理逻辑
    # 例如，更新应用程序的状态、重新加载模块等

# 注册回调函数
config_manager.register_callback(config_changed_callback)
