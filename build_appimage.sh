#!/bin/bash
# MemoCoco AppImage 打包脚本
# 作者: liuwenwu
# 日期: 2025-01-07

set -e  # 遇到错误立即退出

# 设置版本号和基本信息
VERSION="2.2.12"
APP_NAME="MemoCoco"
APP_DIR_NAME="memococo"
PYTHON_VERSION="3.11"

# 显示欢迎信息
echo "=================================================="
echo "  MemoCoco AppImage 打包脚本 v1.0"
echo "=================================================="
echo "当前版本: $VERSION"
echo "Python版本: $PYTHON_VERSION"
echo "开始打包..."

# 检查必要的工具
echo "正在检查必要的工具..."
command -v wget >/dev/null 2>&1 || { echo "错误: 需要安装 wget"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "错误: 需要安装 python3"; exit 1; }

# 清理旧的打包文件
echo "正在清理旧的打包文件..."
rm -rf AppDir ${APP_NAME}-${VERSION}-x86_64.AppImage build_appimage_temp

# 创建临时构建目录
BUILD_DIR="build_appimage_temp"
mkdir -p $BUILD_DIR
cd $BUILD_DIR

# 下载 Python 嵌入式版本 (使用 Python.org 的嵌入式版本)
echo "正在下载 Python 嵌入式版本..."
PYTHON_EMBED_URL="https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
if [ ! -f "python-embed.zip" ]; then
    wget -O python-embed.zip $PYTHON_EMBED_URL
fi

# 创建 AppDir 结构
echo "正在创建 AppDir 结构..."
mkdir -p AppDir/usr/bin AppDir/usr/lib AppDir/usr/share/applications AppDir/usr/share/icons/hicolor/128x128/apps

# 解压 Python 嵌入式版本
echo "正在解压 Python 嵌入式版本..."
unzip -q python-embed.zip -d AppDir/usr/lib/python3.11

# 下载 get-pip.py
echo "正在下载 pip 安装脚本..."
wget -O AppDir/usr/lib/python3.11/get-pip.py https://bootstrap.pypa.io/get-pip.py

# 修改 Python 路径配置
echo "正在配置 Python 路径..."
cat > AppDir/usr/lib/python3.11/python311._pth << EOF
.
./Lib
./Lib/site-packages
../../../share/memococo
EOF

# 创建 Python 启动脚本
echo "正在创建 Python 启动脚本..."
cat > AppDir/usr/bin/python3 << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(dirname "$(readlink -f "${0}")")")"
export PYTHONPATH="$APPDIR/usr/share/memococo:$APPDIR/usr/lib/python3.11:$APPDIR/usr/lib/python3.11/Lib:$APPDIR/usr/lib/python3.11/Lib/site-packages:$PYTHONPATH"
export PYTHONHOME="$APPDIR/usr/lib/python3.11"
exec "$APPDIR/usr/lib/python3.11/python.exe" "$@"
EOF
chmod +x AppDir/usr/bin/python3

# 安装 pip 和依赖
echo "正在安装 pip..."
cd AppDir/usr/lib/python3.11
./python.exe get-pip.py --target ./Lib/site-packages --no-warn-script-location

# 返回构建目录
cd ../../../..

# 安装 Python 依赖包
echo "正在安装 Python 依赖包..."
PYTHON_EXEC="AppDir/usr/lib/python3.11/python.exe"
PIP_TARGET="AppDir/usr/lib/python3.11/Lib/site-packages"

# 基础依赖
$PYTHON_EXEC -m pip install --target $PIP_TARGET --no-warn-script-location \
    Flask>=3.0.3 \
    numpy>=1.26.4 \
    mss>=9.0.1 \
    toml>=0.10.2 \
    pyautogui>=0.9.54 \
    ffmpeg-python>=0.2.0 \
    requests>=2.32.3 \
    jsonify>=0.5 \
    opencv-python>=4.5.1 \
    pillow>=8.2.0 \
    psutil>=5.8.0 \
    babel>=2.14.0 \
    markupsafe>=2.1.5

# OCR 依赖
echo "正在安装 OCR 依赖..."
$PYTHON_EXEC -m pip install --target $PIP_TARGET --no-warn-script-location \
    rapidocr_onnxruntime>=1.2.3

# 复制应用程序文件
echo "正在复制应用程序文件..."
cp -r ../../memococo AppDir/usr/share/memococo/

# 创建主启动脚本
echo "正在创建主启动脚本..."
cat > AppDir/usr/bin/memococo << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(dirname "$(readlink -f "${0}")")")"

# 设置环境变量
export PYTHONPATH="$APPDIR/usr/share/memococo:$APPDIR/usr/lib/python3.11:$APPDIR/usr/lib/python3.11/Lib:$APPDIR/usr/lib/python3.11/Lib/site-packages"
export PYTHONHOME="$APPDIR/usr/lib/python3.11"

# 设置数据目录
export MEMOCOCO_DATA_DIR="${HOME}/.local/share/MemoCoco"
mkdir -p "$MEMOCOCO_DATA_DIR"

# 启动应用程序
echo "Starting MemoCoco application..."
cd "$MEMOCOCO_DATA_DIR"
exec "$APPDIR/usr/lib/python3.11/python.exe" -m memococo.app
EOF
chmod +x AppDir/usr/bin/memococo

# 创建 AppRun 脚本
echo "正在创建 AppRun 脚本..."
cat > AppDir/AppRun << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(readlink -f "${0}")")"
exec "$APPDIR/usr/bin/memococo" "$@"
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
Categories=Utility;
StartupNotify=true
EOF

# 复制图标
echo "正在复制图标..."
cp ../../memococo/static/favicon144x144.png AppDir/memococo.png
cp ../../memococo/static/favicon144x144.png AppDir/usr/share/icons/hicolor/128x128/apps/memococo.png

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
ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir ../${APP_NAME}-${VERSION}-x86_64.AppImage

# 返回原目录
cd ..

# 检查是否成功创建了 AppImage
if [ -f "${APP_NAME}-${VERSION}-x86_64.AppImage" ]; then
    echo "=================================================="
    echo "AppImage 打包成功！"
    echo "文件: ${APP_NAME}-${VERSION}-x86_64.AppImage"
    echo "文件大小: $(du -h ${APP_NAME}-${VERSION}-x86_64.AppImage | cut -f1)"
    echo "=================================================="
    echo "使用方法:"
    echo "1. 赋予执行权限: chmod +x ${APP_NAME}-${VERSION}-x86_64.AppImage"
    echo "2. 直接运行: ./${APP_NAME}-${VERSION}-x86_64.AppImage"
    echo "3. 或者双击运行"
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
rm -rf $BUILD_DIR

echo "AppImage 打包过程完成。"
