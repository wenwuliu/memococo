# MemoCoco 更新日志

## 2.2.11 (2025-04-16)

### 改进
- 调整OCR后图片压缩逻辑，提高处理效率
- 优化鼠标滚轮滑动时间轴的交互方式，使其更符合人类使用习惯

## 2.2.10 (2025-04-16)

### 新功能
- 增强空闲OCR处理，支持从已备份文件夹中获取图片进行OCR处理

### 改进
- 优化搜索功能，解决JSON解析错误问题
- 改进暗黑模式切换体验，消除页面切换时的闪烁
- 优化语言切换功能，修复设置页和未备份文件夹页面的国际化支持
- 优化下拉菜单在暗黑模式下的显示效果

### 修复
- 修复设置页面中"Use ollama"选项始终显示为True的问题
- 修复404错误，移除对源映射文件的引用
- 修复鼠标滚轮无法滑动时间轴滑块的问题

## 2.2.3 (2025-04-16)

### 新功能
- 添加UmiOCR支持，在UmiOCR可用时自动使用UmiOCR进行OCR识别

### 改进
- 优化OCR引擎选择逻辑，首先尝试使用UmiOCR，如果不可用再根据硬件环境选择
- 提高OCR识别速度，使用UmiOCR时速度提升显著
- 添加详细的OCR日志记录，显示使用的OCR引擎类型、识别文本长度和处理耗时

## 2.2.2 (2025-04-15)

### 新功能
- 添加OCR引擎工厂模式，根据硬件环境自动选择最合适的OCR引擎
- 添加EasyOCR支持，在GPU环境下自动使用EasyOCR进行文本识别

### 改进
- 优化OCR识别效果，提高识别文本量
- 根据硬件环境智能选择OCR引擎，提高性能
- 重构OCR模块，提高代码可维护性

## 2.2.1 (2025-04-08)

### 改进
- 整理项目结构，移除多余的文件和文件夹
- 添加打包脚本，简化 .deb 包的构建过程
- 更新 .gitignore 文件，添加更多应该被忽略的文件和目录
- 改进安装说明文档
- 更新 README.md，提供更详细的项目信息和使用说明
- 移除 trwebocr 和 tesseract OCR，使用 RapidOCR 作为唯一的 OCR 引擎
- 优化 RapidOCR 参数配置，提高识别速度和准确率
- 简化设置页面，移除 OCR 工具选择选项

### 修复
- 修复搜索功能中的分页问题
- 修复搜索结果排序逻辑
- 添加图片左右导航功能
- 优化 OCR 识别效率

## 2.2.0 (2025-03-31)

### 新功能
- 添加持久数据存储功能，移除数据清理选项
- 优化搜索功能，支持按关键词出现次数排序
- 添加应用程序过滤功能
- 改进 OCR 识别准确率

### 改进
- 优化数据库查询性能
- 改进用户界面，提升用户体验
- 添加更多错误处理和日志记录

### 修复
- 修复多个已知问题和 bug
