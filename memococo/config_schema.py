"""
配置模式定义模块

定义配置项的模式，用于验证配置
"""

# 配置模式定义
CONFIG_SCHEMA = {
    # 基本配置
    "use_ollama": {
        "type": "boolean",
        "default": False,
        "description": "是否使用Ollama进行关键词提取"
    },
    "model": {
        "type": "string",
        "default": "qwen2.5:3b",
        "description": "使用的Ollama模型名称"
    },
    "ignored_apps": {
        "type": "array",
        "default": ["DBeaver", "code"],
        "description": "忽略的应用程序列表，这些应用程序的窗口不会被截图"
    },
    
    # 截图配置
    "screenshot_interval": {
        "type": "integer",
        "default": 5,
        "minimum": 1,
        "maximum": 3600,
        "description": "截图间隔时间（秒）"
    },
    "primary_monitor_only": {
        "type": "boolean",
        "default": False,
        "description": "是否只截取主显示器的屏幕"
    },
    "compress_images": {
        "type": "boolean",
        "default": True,
        "description": "是否压缩截图以节省存储空间"
    },
    "compression_quality": {
        "type": "integer",
        "default": 85,
        "minimum": 1,
        "maximum": 100,
        "description": "图像压缩质量（1-100），值越大质量越高，文件越大"
    },
    
    # OCR配置
    "ocr_engine": {
        "type": "string",
        "default": "umiocr",
        "enum": ["umiocr", "rapidocr", "easyocr"],
        "description": "使用的OCR引擎"
    },
    "ocr_batch_size": {
        "type": "integer",
        "default": 5,
        "minimum": 1,
        "maximum": 100,
        "description": "每批处理的OCR任务数量"
    },
    "ocr_min_queue": {
        "type": "integer",
        "default": 5,
        "minimum": 0,
        "maximum": 1000,
        "description": "OCR处理队列最小长度，低于此值时停止OCR处理"
    },
    "ocr_max_queue": {
        "type": "integer",
        "default": 50,
        "minimum": 1,
        "maximum": 10000,
        "description": "OCR处理队列最大长度，超过此值时开始OCR处理"
    },
    "ocr_cpu_threshold": {
        "type": "integer",
        "default": 70,
        "minimum": 0,
        "maximum": 100,
        "description": "CPU使用率阈值（百分比），超过此值时暂停OCR处理"
    },
    "ocr_temp_threshold": {
        "type": "integer",
        "default": 70,
        "minimum": 0,
        "maximum": 100,
        "description": "CPU温度阈值（摄氏度），超过此值时暂停OCR处理"
    },
    
    # 界面配置
    "theme": {
        "type": "string",
        "default": "light",
        "enum": ["light", "dark", "system"],
        "description": "界面主题"
    },
    "language": {
        "type": "string",
        "default": "zh_CN",
        "enum": ["zh_CN", "en_US"],
        "description": "界面语言"
    },
    "items_per_page": {
        "type": "integer",
        "default": 20,
        "minimum": 1,
        "maximum": 1000,
        "description": "每页显示的条目数量"
    }
}

# 从模式中提取默认配置
DEFAULT_CONFIG = {key: schema["default"] for key, schema in CONFIG_SCHEMA.items()}
