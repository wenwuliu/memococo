import os
import sys
import argparse
import toml

# 导入共用模块
from memococo.common.config_manager import get_app_data_folder
from memococo.common.file_utils import ensure_directory_exists

# 应用信息
app_name_cn = "时光胶囊"
app_name_en = "MemoCoco"
main_app_name = app_name_en
app_version = "2.2.3"

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

args = parser.parse_args()

# 确定应用数据目录
if args.storage_path:
    appdata_folder = args.storage_path
else:
    appdata_folder = get_app_data_folder(main_app_name)

def get_settings():
    # 从appdata_folder中加载配置文件config.toml
    config_path = os.path.join(appdata_folder, "config.toml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = toml.load(f)

        # 移除了OCR引擎选择功能，只使用RapidOCR

        return config
    else:
    # 如果配置文件不存在，则使用默认配置生成配置文件，并返回默认配置,default_ignored_apps需要保存为list
        print("配置文件不存在，将使用默认配置生成配置文件")
        config_path = os.path.join(appdata_folder, "config.toml")
        config = {
            "use_ollama":False,
            "model": "qwen2.5:3b",
            "ignored_apps": default_ignored_apps,
        }
        with open(config_path, "w", encoding="utf-8") as f:
            toml.dump(config, f)
        return config

def save_settings(config):
    # 将配置保存到appdata_folder中的config.toml文件
    config_path = os.path.join(appdata_folder, "config.toml")
    with open(config_path, "w", encoding="utf-8") as f:
        toml.dump(config, f)

default_ignored_apps = [
    "DBeaver",
    "code"
]


#数据库以app_name_en.db命名
db_path = os.path.join(appdata_folder, f"{app_name_en}.db")
screenshots_path = os.path.join(appdata_folder, "screenshots")

# 确保目录存在
ensure_directory_exists(screenshots_path)

# 日志配置
from memococo.common.logging import initialize_logging, get_logger

# 初始化日志记录
log_file = os.path.join(appdata_folder, "memococo.log")
initialize_logging(log_file)

# 获取日志对象
main_logger = get_logger("memococo.main", "main")
screenshot_logger = get_logger("memococo.screenshot", "screenshot")
ocr_logger = get_logger("memococo.ocr", "ocr")

# 兼容旧代码
logger = main_logger
