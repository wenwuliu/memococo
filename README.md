# MemoCoco - 时间胶囊

![MemoCoco Logo](memococo/static/favicon144x144.png)

MemoCoco 是一个全开源、注重隐私的数字记忆工具，是 Microsoft Windows Recall 或 Limitless Rewind.ai 等专有解决方案的替代品。使用 MemoCoco，您可以轻松访问您的数字历史记录，增强记忆力和工作效率，同时不会泄露您的隐私。

本项目基于 [OpenRecall](https://github.com/openrecall/openrecall) 项目，进行了丰富和优化。

## 主要特性

### 核心功能

- **时间旅行**：在 Windows、macOS 或 Linux 上无缝浏览您过去的数字活动
- **本地处理**：所有数据处理在本地进行，不依赖云服务，保持数据的私密性和安全性
- **文本搜索**：高效的OCR文本识别和索引，支持快速搜索历史截图中的文本内容
- **完全控制存储**：您的数据存储在本地，让您完全控制其管理和安全性
- **持久数据存储**：所有数据永久保存，无自动或手动清理功能

### 增强功能

- **智能 OCR 引擎**：支持多种 OCR 引擎，优先使用 UmiOCR API（速度最快），如果不可用则根据硬件环境自动选择 EasyOCR（GPU模式，识别文本量最多）或 RapidOCR（CPU模式，准确率高）
- **本地搜索引擎**：高效的本地搜索功能，支持全文本搜索和关键词匹配
- **存储路径优化**：使用文件夹切片模式优化图像存储路径
- **异步图片压缩**：高效的后台图片压缩功能，在不影响截图速度的同时减小存储空间占用
- **应用搜索**：优化搜索功能，支持通过应用选项查询相应内容
- **搜索结果排序**：按关键词不重复出现次数和总出现次数排序
- **图片导航**：支持在搜索结果中查看放大图片时使用左右导航

## 系统要求

- Python 3.8 或更高版本
- 支持平台：Windows、macOS、Linux
- 依赖：Flask、OpenCV、NumPy、MSS 等
- 强烈推荐安装 [UmiOCR](https://github.com/hiroi-sora/Umi-OCR) 并启用API服务，可将OCR识别速度提高约3-6倍，并提高识别准确率

## 安装方法

### 使用 .deb 包安装 (推荐，仅限 Debian/Ubuntu)

1. 下载最新的 .deb 包
2. 使用以下命令安装：
   ```bash
   sudo dpkg -i memococo_2.2.11_amd64.deb
   ```
   安装脚本会自动安装所有必要的依赖

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/liuwenwu520/MemoCoco.git
cd MemoCoco

# 安装依赖
pip3 install -r requirements.txt

# 运行应用
python3 -m memococo.app
```

## 使用方法

### 安装和配置UmiOCR（推荐）

为了获得最佳的OCR识别效果和速度，强烈推荐安装UmiOCR：

1. 从[UmiOCR官方仓库](https://github.com/hiroi-sora/Umi-OCR/releases)下载最新版本
2. 安装并启动UmiOCR
3. 在UmiOCR中启用API服务：
   - 点击“系统设置”
   - 在“高级功能”中启用“API服务”
   - 确保API服务端口为1224（默认值）

4. 设置UmiOCR开机自启动：
   - **Windows**：在UmiOCR系统设置中勾选“开机自启动”
   - **Linux**：创建自启动服务
     ```bash
     # 创建自启动服务文件
     mkdir -p ~/.config/autostart
     cat > ~/.config/autostart/umiocr.desktop << EOF
     [Desktop Entry]
     Type=Application
     Name=UmiOCR
     Exec=/path/to/UmiOCR  # 替换为实际的UmiOCR路径
     Terminal=false
     X-GNOME-Autostart-enabled=true
     EOF
     ```
   - **macOS**：将UmiOCR添加到登录项目中
     1. 系统偏好设置 > 用户与群组 > 登录项目
     2. 点击“+”按钮，选择UmiOCR应用

安装并配置好UmiOCR后，MemoCoco将自动检测并使用UmiOCR进行OCR识别。根据测试结果，UmiOCR的识别速度比RapidOCR快约2.7倍，比EasyOCR快约4.5倍，同时识别的文本量与EasyOCR相当。这将显著提高您的使用体验。

### 启动应用

- **使用 .deb 包安装后**：
  - 从应用程序菜单启动
  - 在终端中运行 `memococo` 命令
  - 设置为系统服务自动启动：`sudo systemctl enable --now memococo@<用户名>`

- **从源码安装后**：
  ```bash
  python3 -m memococo.app
  ```

### 访问 Web 界面

在浏览器中访问（建议将此站点安装为应用）：
http://127.0.0.1:8842

### 数据存储路径

- **使用 .deb 包安装**：`/var/lib/memococo/`
- **从源码安装**：
  - Linux: `~/.local/share/MemoCoco/`
  - macOS: `~/Library/Application Support/MemoCoco/`
  - Windows: `%APPDATA%\MemoCoco\`

## 卸载说明

### 使用 .deb 包安装的用户

1. 卸载应用：
   ```bash
   sudo apt remove memococo
   ```

2. 删除数据（可选）：
   ```bash
   sudo rm -rf /var/lib/memococo
   ```

### 从源码安装的用户

1. 卸载包：
   ```bash
   python3 -m pip uninstall memococo
   ```

2. 删除数据（可选）：
   - Windows：
     ```bash
     rmdir /s %APPDATA%\MemoCoco
     ```
   - macOS：
     ```bash
     rm -rf ~/Library/Application\ Support/MemoCoco
     ```
   - Linux：
     ```bash
     rm -rf ~/.local/share/MemoCoco
     ```

注意：如果您使用 `--storage-path` 参数指定了自定义存储路径，请确保也删除该目录。

## 打包说明

本项目提供了一个打包脚本，可以将应用打包为 .deb 包：

```bash
# 安装打包依赖
sudo apt-get install ruby ruby-dev rubygems build-essential
sudo gem install fpm

# 运行打包脚本
./build_deb.sh
```

打包完成后，会在当前目录生成 `memococo_2.2.11_amd64.deb` 文件。

## 贡献

作为一个开源项目，我们欢迎来自社区的贡献。如果您想帮助改进 MemoCoco，请在我们的 GitHub 仓库上提交 Pull Request 或打开 Issue。

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/liuwenwu520/MemoCoco.git
cd MemoCoco

# 安装开发依赖
python3 scripts/setup_dev_env.py
```

### 代码风格

我们使用了一系列工具来维护代码风格的一致性：

- **black**：代码格式化
- **isort**：导入语句排序
- **flake8**：代码风格检查
- **mypy**：类型检查
- **pre-commit**：提交前检查

请在提交代码前运行以下命令检查代码风格：

```bash
python3 scripts/format_code.py
```

或者使用 pre-commit 钩子自动检查：

```bash
pre-commit install  # 只需要运行一次
```

详细的代码风格规范请参考 [docs/code_style_guide.md](docs/code_style_guide.md)。

## 联系维护者

liuawu625@163.com

## 许可证

MemoCoco 在 [AGPLv3](https://opensource.org/licenses/AGPL-3.0) 许可证下发布，确保它对所有人保持开放和可访问。

**喜欢这个项目吗？** 通过给它加星来表达您的支持！ ⭐️ 谢谢！