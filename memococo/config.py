import os
import sys
import argparse
import toml

app_name_cn = "时光胶囊"
app_name_en = "MemoCoco"
main_app_name = app_name_en
app_version = "2.1.41"

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


def get_appdata_folder(app_name=main_app_name):
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
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def create_directory_if_not_exists(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except Exception as e:
        print(f"创建目录失败，错误信息：{e}")


if args.storage_path:
    appdata_folder = args.storage_path
else:
    appdata_folder = get_appdata_folder()

def get_settings():
    # 从appdata_folder中加载配置文件config.toml
    config_path = os.path.join(appdata_folder, "config.toml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = toml.load(f)
            
        return config
    else:
    # 如果配置文件不存在，则使用默认配置生成配置文件，并返回默认配置,default_ignored_apps需要保存为list
        print("配置文件不存在，将使用默认配置生成配置文件")
        config_path = os.path.join(appdata_folder, "config.toml")
        config = {
            "ocr_tool": "trwebocr",
            "use_ollama":True,
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

create_directory_if_not_exists(screenshots_path)

# logger配置
import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger("memococo")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)
#设置logger最大文件大小为10MB，最多保留5个备份文件
file_handler = RotatingFileHandler(os.path.join(appdata_folder, "memococo.log"), maxBytes=10*1024*1024, backupCount=4)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
