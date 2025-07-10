# MemoCoco 配置文档

本文档详细说明了MemoCoco应用的配置项，包括其作用、可选值和默认值。

## 配置文件位置

MemoCoco的配置文件位于应用数据目录下的`config.toml`文件中：

- Windows: `%APPDATA%\MemoCoco\config.toml`
- macOS: `~/Library/Application Support/MemoCoco/config.toml`
- Linux: `~/.local/share/MemoCoco/config.toml`

如果使用`--storage-path`命令行参数指定了存储路径，则配置文件位于该路径下。

## 配置项

### 基本配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `use_ollama` | 布尔值 | `false` | 是否使用Ollama进行关键词提取 |
| `model` | 字符串 | `"qwen2.5:3b"` | 使用的Ollama模型名称 |
| `ignored_apps` | 字符串数组 | `["DBeaver", "code"]` | 忽略的应用程序列表，这些应用程序的窗口不会被截图 |

### 截图配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `screenshot_interval` | 整数 | `5` | 截图间隔时间（秒） |
| `primary_monitor_only` | 布尔值 | `false` | 是否只截取主显示器的屏幕 |
| `compress_images` | 布尔值 | `true` | 是否压缩截图以节省存储空间 |
| `compression_quality` | 整数 | `85` | 图像压缩质量（1-100），值越大质量越高，文件越大 |

### OCR配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `ocr_engine` | 字符串 | `"umiocr"` | 使用的OCR引擎，可选值：`"umiocr"`, `"rapidocr"` |
| `ocr_batch_size` | 整数 | `5` | 每批处理的OCR任务数量 |
| `ocr_min_queue` | 整数 | `5` | OCR处理队列最小长度，低于此值时停止OCR处理 |
| `ocr_max_queue` | 整数 | `50` | OCR处理队列最大长度，超过此值时开始OCR处理 |
| `ocr_cpu_threshold` | 整数 | `70` | CPU使用率阈值（百分比），超过此值时暂停OCR处理 |
| `ocr_temp_threshold` | 整数 | `70` | CPU温度阈值（摄氏度），超过此值时暂停OCR处理 |

### 界面配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `theme` | 字符串 | `"light"` | 界面主题，可选值：`"light"`, `"dark"`, `"system"` |
| `language` | 字符串 | `"zh_CN"` | 界面语言，可选值：`"zh_CN"`, `"en_US"` |
| `items_per_page` | 整数 | `20` | 每页显示的条目数量 |

## 配置示例

```toml
# 基本配置
use_ollama = false
model = "qwen2.5:3b"
ignored_apps = ["DBeaver", "code", "Visual Studio Code"]

# 截图配置
screenshot_interval = 5
primary_monitor_only = false
compress_images = true
compression_quality = 85

# OCR配置
ocr_engine = "umiocr"
ocr_batch_size = 5
ocr_min_queue = 5
ocr_max_queue = 50
ocr_cpu_threshold = 70
ocr_temp_threshold = 70

# 界面配置
theme = "light"
language = "zh_CN"
items_per_page = 20
```

## 环境变量

MemoCoco也支持通过环境变量进行配置，环境变量的优先级高于配置文件。环境变量名称格式为`MEMOCOCO_<配置项名称大写>`，例如：

- `MEMOCOCO_USE_OLLAMA`: 是否使用Ollama
- `MEMOCOCO_MODEL`: 使用的Ollama模型名称
- `MEMOCOCO_SCREENSHOT_INTERVAL`: 截图间隔时间（秒）

## 配置热加载

MemoCoco支持配置热加载，当配置文件发生变化时，应用会自动重新加载配置，无需重启应用。

## 配置验证

MemoCoco会对配置进行验证，确保配置项的类型和值符合要求。如果配置项不符合要求，应用会记录错误日志，并使用默认值或上一次有效的配置值。
