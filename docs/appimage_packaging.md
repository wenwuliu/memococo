# MemoCoco AppImage 打包指南

本文档介绍如何将MemoCoco项目打包为AppImage格式的可执行文件。

## 📦 AppImage 简介

AppImage是一种Linux应用程序的便携格式，具有以下优势：
- **一次构建，到处运行**: 在任何Linux发行版上都能运行
- **无需安装**: 直接下载运行，无需root权限
- **自包含**: 包含所有依赖，不会与系统冲突
- **便携性**: 可以放在U盘中随身携带

## 🛠️ 打包方案对比

我们提供了三种不同的AppImage打包方案：

### 1. 简化方案 (推荐) - `build_appimage_simple.sh`

**特点:**
- 使用系统Python和虚拟环境
- 打包体积较小 (~200-300MB)
- 构建速度快
- 依赖系统的基础库

**适用场景:**
- 快速打包测试
- 目标用户有基本的Linux环境
- 对体积有要求

**使用方法:**
```bash
./build_appimage_simple.sh
```

### 2. PyInstaller方案 - `build_appimage_pyinstaller.sh`

**特点:**
- 使用PyInstaller将Python代码编译为二进制
- 启动速度快
- 打包体积中等 (~400-600MB)
- 更好的代码保护

**适用场景:**
- 商业发布
- 需要代码保护
- 对启动速度有要求

**使用方法:**
```bash
./build_appimage_pyinstaller.sh
```

### 3. 完整嵌入方案 - `build_appimage.sh`

**特点:**
- 嵌入完整的Python运行时
- 完全自包含，无外部依赖
- 打包体积最大 (~800MB-1GB)
- 兼容性最好

**适用场景:**
- 最终用户发布
- 目标系统环境未知
- 需要最大兼容性

**使用方法:**
```bash
./build_appimage.sh
```

## 🔧 构建环境要求

### 系统要求
- Ubuntu 18.04+ / Debian 10+ 或兼容发行版
- Python 3.8+
- 至少2GB可用磁盘空间
- 网络连接（下载依赖）

### 必需工具
```bash
# 安装基础工具
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv wget curl build-essential

# 安装系统依赖
sudo apt-get install libgl1-mesa-glx libglib2.0-0 x11-utils xdotool ffmpeg
```

## 📋 构建步骤

### 1. 准备环境
```bash
# 克隆项目
git clone https://github.com/liuwenwu520/MemoCoco.git
cd MemoCoco

# 确保所有依赖已安装
pip3 install -r requirements.txt
```

### 2. 设置 AppImageTool
```bash
# 自动下载并设置 AppImageTool
./setup_appimagetool.sh

# 或者手动下载到指定位置
mkdir -p ~/appImages
wget -O ~/appImages/appimagetool-x86_64.AppImage \
  https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x ~/appImages/appimagetool-x86_64.AppImage
```

### 3. 选择打包方案并执行
```bash
# 推荐：简化方案
./build_appimage_simple.sh

# 或者：PyInstaller简化方案
./build_appimage_pyinstaller_simple.sh

# 或者：PyInstaller完整方案
./build_appimage_pyinstaller.sh

# 或者：完整嵌入方案
./build_appimage.sh
```

### 3. 验证构建结果
```bash
# 检查生成的AppImage文件
ls -lh MemoCoco-*.AppImage

# 测试运行
chmod +x MemoCoco-2.2.11-x86_64.AppImage
./MemoCoco-2.2.11-x86_64.AppImage
```

## 🎯 使用生成的AppImage

### 基本使用
```bash
# 赋予执行权限
chmod +x MemoCoco-2.2.11-x86_64.AppImage

# 直接运行
./MemoCoco-2.2.11-x86_64.AppImage

# 或者双击运行（在图形界面中）
```

### 系统集成
```bash
# 将AppImage移动到应用程序目录
sudo mv MemoCoco-2.2.11-x86_64.AppImage /opt/

# 创建桌面快捷方式
cat > ~/.local/share/applications/memococo.desktop << EOF
[Desktop Entry]
Name=MemoCoco
Comment=时间胶囊 - 自动记录屏幕和文本
Exec=/opt/MemoCoco-2.2.11-x86_64.AppImage
Icon=memococo
Terminal=false
Type=Application
Categories=Utility;Office;
EOF
```

### 数据目录
- **配置文件**: `~/.local/share/MemoCoco/`
- **截图数据**: `~/.local/share/MemoCoco/screenshots/`
- **数据库**: `~/.local/share/MemoCoco/memococo.db`

## 🔍 故障排除

### 常见问题

#### 1. 权限错误
```bash
# 确保AppImage有执行权限
chmod +x MemoCoco-*.AppImage
```

#### 2. 缺少系统依赖
```bash
# 安装必要的系统库
sudo apt-get install libgl1-mesa-glx libglib2.0-0 x11-utils xdotool ffmpeg
```

#### 3. Python版本不兼容
```bash
# 检查Python版本
python3 --version

# 确保版本 >= 3.8
```

#### 4. 网络连接问题
```bash
# 检查网络连接
ping -c 3 github.com

# 如果在代理环境下，设置代理
export http_proxy=http://proxy:port
export https_proxy=http://proxy:port
```

### 调试模式
```bash
# 在终端中运行以查看详细输出
./MemoCoco-2.2.11-x86_64.AppImage

# 检查日志文件
tail -f ~/.local/share/MemoCoco/memococo.log
```

## 📊 性能对比

| 方案 | 构建时间 | 包大小 | 启动时间 | 兼容性 | 推荐度 |
|------|----------|--------|----------|--------|--------|
| 简化方案 | ~5分钟 | ~250MB | ~3秒 | 中等 | ⭐⭐⭐⭐⭐ |
| PyInstaller | ~10分钟 | ~500MB | ~2秒 | 良好 | ⭐⭐⭐⭐ |
| 完整嵌入 | ~15分钟 | ~900MB | ~4秒 | 最佳 | ⭐⭐⭐ |

## 🚀 发布建议

### 开发测试
- 使用**简化方案**进行快速迭代测试
- 构建速度快，便于调试

### 用户发布
- 使用**PyInstaller方案**或**完整嵌入方案**
- 提供更好的用户体验和兼容性

### 版本管理
```bash
# 为不同版本创建不同的AppImage
MemoCoco-2.2.11-x86_64.AppImage
MemoCoco-2.2.12-x86_64.AppImage
```

## 📝 注意事项

1. **构建环境**: 建议在干净的Ubuntu环境中构建
2. **依赖管理**: 确保requirements.txt包含所有必要依赖
3. **测试验证**: 在不同的Linux发行版上测试AppImage
4. **文件大小**: 注意AppImage文件大小，避免过大影响分发
5. **更新机制**: AppImage本身不支持自动更新，需要手动下载新版本

## 🔗 相关链接

- [AppImage官方文档](https://appimage.org/)
- [PyInstaller文档](https://pyinstaller.readthedocs.io/)
- [MemoCoco项目主页](https://github.com/liuwenwu520/MemoCoco)
- [UmiOCR项目](https://github.com/hiroi-sora/Umi-OCR)
