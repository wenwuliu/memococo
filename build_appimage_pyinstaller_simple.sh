#!/bin/bash
# MemoCoco 简化 PyInstaller AppImage 打包脚本
# 作者: liuwenwu
# 日期: 2025-01-07

set -e  # 遇到错误立即退出

# 设置版本号和基本信息
VERSION="2.2.12"
APP_NAME="MemoCoco"

# 显示欢迎信息
echo "=================================================="
echo "  MemoCoco 简化 PyInstaller AppImage 打包脚本 v1.0"
echo "=================================================="
echo "当前版本: $VERSION"
echo "开始打包..."

# 检查必要的工具
echo "正在检查必要的工具..."
command -v python3 >/dev/null 2>&1 || { echo "错误: 需要安装 python3"; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "错误: 需要安装 pip3"; exit 1; }
command -v wget >/dev/null 2>&1 || { echo "错误: 需要安装 wget"; exit 1; }

# 清理旧的打包文件
echo "正在清理旧的打包文件..."
rm -rf build dist *.spec AppDir ${APP_NAME}-${VERSION}-x86_64.AppImage

# 升级pip
echo "正在升级pip..."
python3 -m pip install --upgrade pip

# 安装 PyInstaller
echo "正在安装 PyInstaller..."
pip3 install pyinstaller

# 安装项目依赖
echo "正在安装项目依赖..."
pip3 install -r requirements.txt

# 使用简化的PyInstaller命令直接打包
echo "正在运行 PyInstaller..."
pyinstaller --onedir \
    --name memococo \
    --add-data "memococo/templates:memococo/templates" \
    --add-data "memococo/static:memococo/static" \
    --add-data "memococo/i18n:memococo/i18n" \
    --hidden-import memococo.config \
    --hidden-import memococo.database \
    --hidden-import memococo.screenshot \
    --hidden-import memococo.ocr \
    --hidden-import memococo.ocr_factory \
    --hidden-import memococo.ocr_processor \
    --hidden-import memococo.umiocr_client \
    --hidden-import memococo.utils \
    --hidden-import memococo.ollama \
    --hidden-import memococo.app_map \
    --hidden-import memococo.common.error_handler \
    --hidden-import memococo.common.error_middleware \
    --hidden-import memococo.common.config_manager \
    --hidden-import memococo.common.db_manager \
    --hidden-import memococo.i18n.flask_i18n \
    --hidden-import flask \
    --hidden-import numpy \
    --hidden-import cv2 \
    --hidden-import PIL \
    --hidden-import mss \
    --hidden-import pyautogui \
    --hidden-import psutil \
    --hidden-import requests \
    --hidden-import rapidocr_onnxruntime \
    --hidden-import babel \
    --hidden-import toml \
    --hidden-import sqlite3 \
    --hidden-import threading \
    --hidden-import multiprocessing \
    --hidden-import concurrent.futures \
    --exclude-module tkinter \
    --exclude-module matplotlib \
    --exclude-module scipy \
    --exclude-module pandas \
    --exclude-module jupyter \
    --exclude-module IPython \
    --exclude-module notebook \
    --noconfirm \
    --clean \
    memococo/app.py

# 检查 PyInstaller 输出
if [ ! -d "dist/memococo" ]; then
    echo "错误: PyInstaller 构建失败"
    exit 1
fi

echo "PyInstaller 构建成功！"

# 创建 AppDir 结构
echo "正在创建 AppDir 结构..."
mkdir -p AppDir/usr/bin AppDir/usr/share/applications AppDir/usr/share/icons/hicolor/128x128/apps

# 复制 PyInstaller 输出到 AppDir
echo "正在复制应用程序文件..."
cp -r dist/memococo AppDir/usr/bin/

# 创建启动脚本
echo "正在创建启动脚本..."
cat > AppDir/usr/bin/memococo_launcher << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(dirname "$(readlink -f "${0}")")")"

# 设置数据目录
export MEMOCOCO_DATA_DIR="${HOME}/.local/share/MemoCoco"
mkdir -p "$MEMOCOCO_DATA_DIR"

# 检查必要的系统依赖
check_dependencies() {
    local missing_deps=()
    
    # 检查系统库
    if ! ldconfig -p | grep -q libGL.so; then
        missing_deps+=("libgl1-mesa-glx")
    fi
    
    if ! ldconfig -p | grep -q libglib-2.0.so; then
        missing_deps+=("libglib2.0-0")
    fi
    
    # 检查X11相关
    if ! command -v xprop >/dev/null 2>&1; then
        missing_deps+=("x11-utils")
    fi
    
    if ! command -v xdotool >/dev/null 2>&1; then
        missing_deps+=("xdotool")
    fi
    
    # 检查ffmpeg
    if ! command -v ffmpeg >/dev/null 2>&1; then
        missing_deps+=("ffmpeg")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo "警告: 检测到缺少以下系统依赖:"
        printf '%s\n' "${missing_deps[@]}"
        echo "请使用以下命令安装:"
        echo "sudo apt-get install ${missing_deps[*]}"
        echo ""
        echo "继续启动应用程序..."
    fi
}

# 检查依赖
check_dependencies

# 启动应用程序
echo "Starting MemoCoco application..."
echo "Web界面将在 http://127.0.0.1:8842 启动"
cd "$MEMOCOCO_DATA_DIR"
exec "$APPDIR/usr/bin/memococo/memococo" "$@"
EOF
chmod +x AppDir/usr/bin/memococo_launcher

# 创建 AppRun 脚本
echo "正在创建 AppRun 脚本..."
cat > AppDir/AppRun << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(readlink -f "${0}")")"
exec "$APPDIR/usr/bin/memococo_launcher" "$@"
EOF
chmod +x AppDir/AppRun

# 创建桌面文件
echo "正在创建桌面文件..."
cat > AppDir/memococo.desktop << 'EOF'
[Desktop Entry]
Name=MemoCoco
Comment=时间胶囊 - 自动记录屏幕和文本
Exec=memococo
Icon=memococo
Terminal=false
Type=Application
Categories=Utility;Office;
StartupNotify=true
Keywords=screenshot;ocr;memory;timeline;记录;截图;文字识别;时间线;
EOF

# 复制图标
echo "正在复制图标..."
cp memococo/static/favicon144x144.png AppDir/memococo.png
cp memococo/static/favicon144x144.png AppDir/usr/share/icons/hicolor/128x128/apps/memococo.png

# 创建版本信息文件
echo "正在创建版本信息文件..."
cat > AppDir/usr/share/VERSION << EOF
MemoCoco v${VERSION} (PyInstaller Build)
Build Date: $(date)
Python Version: $(python3 --version)
Build Host: $(hostname)
PyInstaller Version: $(pyinstaller --version)
EOF

# 检查并使用本地 appimagetool
echo "正在检查 appimagetool..."
APPIMAGETOOL_PATH="$HOME/appImages/appimagetool-x86_64.AppImage"

if [ -f "$APPIMAGETOOL_PATH" ]; then
    echo "使用本地 appimagetool: $APPIMAGETOOL_PATH"
    cp "$APPIMAGETOOL_PATH" ./appimagetool-x86_64.AppImage
    chmod +x appimagetool-x86_64.AppImage
elif [ -f "appimagetool-x86_64.AppImage" ]; then
    echo "使用当前目录的 appimagetool"
    chmod +x appimagetool-x86_64.AppImage
else
    echo "错误: 未找到 appimagetool-x86_64.AppImage"
    echo "请将 appimagetool-x86_64.AppImage 放置在以下位置之一:"
    echo "1. $HOME/appImages/appimagetool-x86_64.AppImage"
    echo "2. 当前目录下"
    echo ""
    echo "您可以从以下地址下载:"
    echo "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    exit 1
fi

# 创建 AppImage
echo "正在创建 AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir ${APP_NAME}-${VERSION}-PyInstaller-x86_64.AppImage

# 检查是否成功创建了 AppImage
if [ -f "${APP_NAME}-${VERSION}-PyInstaller-x86_64.AppImage" ]; then
    # 使文件可执行
    chmod +x ${APP_NAME}-${VERSION}-PyInstaller-x86_64.AppImage
    
    echo "=================================================="
    echo "PyInstaller AppImage 打包成功！"
    echo "文件: ${APP_NAME}-${VERSION}-PyInstaller-x86_64.AppImage"
    echo "文件大小: $(du -h ${APP_NAME}-${VERSION}-PyInstaller-x86_64.AppImage | cut -f1)"
    echo "=================================================="
    echo "使用方法:"
    echo "1. 直接运行: ./${APP_NAME}-${VERSION}-PyInstaller-x86_64.AppImage"
    echo "2. 或者双击运行"
    echo ""
    echo "特点:"
    echo "- 使用PyInstaller编译，启动速度快"
    echo "- 自包含所有Python依赖"
    echo "- 无需安装Python环境"
    echo ""
    echo "系统要求:"
    echo "- Ubuntu 18.04+ / Debian 10+ 或兼容发行版"
    echo "- X11 图形环境"
    echo ""
    echo "推荐安装的系统依赖:"
    echo "sudo apt-get install libgl1-mesa-glx libglib2.0-0 x11-utils xdotool ffmpeg"
    echo "=================================================="
else
    echo "=================================================="
    echo "AppImage 打包失败！"
    echo "请检查错误信息。"
    echo "=================================================="
    exit 1
fi

# 清理临时文件
echo "正在清理临时文件..."
rm -rf build dist *.spec AppDir appimagetool-x86_64.AppImage

echo "PyInstaller AppImage 打包过程完成。"
