#!/bin/bash
# MemoCoco 简化 AppImage 打包脚本
# 作者: liuwenwu
# 日期: 2025-01-07
# 说明: 使用系统Python和虚拟环境创建轻量级AppImage

set -e  # 遇到错误立即退出

# 设置版本号和基本信息
VERSION="2.2.12"
APP_NAME="MemoCoco"

# 显示欢迎信息
echo "=================================================="
echo "  MemoCoco 简化 AppImage 打包脚本 v1.0"
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
rm -rf AppDir ${APP_NAME}-${VERSION}-x86_64.AppImage venv_appimage

# 创建虚拟环境
echo "正在创建虚拟环境..."
python3 -m venv venv_appimage
source venv_appimage/bin/activate

# 升级pip
pip install --upgrade pip

# 安装项目依赖
echo "正在安装项目依赖..."
pip install -r requirements.txt

# 创建 AppDir 结构
echo "正在创建 AppDir 结构..."
mkdir -p AppDir/usr/bin AppDir/usr/lib AppDir/usr/share/applications AppDir/usr/share/icons/hicolor/128x128/apps

# 复制虚拟环境
echo "正在复制虚拟环境..."
cp -r venv_appimage AppDir/usr/lib/

# 复制应用程序文件
echo "正在复制应用程序文件..."
cp -r memococo AppDir/usr/share/

# 创建Python启动脚本
echo "正在创建Python启动脚本..."
cat > AppDir/usr/bin/python3_memococo << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(dirname "$(readlink -f "${0}")")")"
export PYTHONPATH="$APPDIR/usr/share:$PYTHONPATH"
exec "$APPDIR/usr/lib/venv_appimage/bin/python" "$@"
EOF
chmod +x AppDir/usr/bin/python3_memococo

# 创建主启动脚本
echo "正在创建主启动脚本..."
cat > AppDir/usr/bin/memococo << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(dirname "$(readlink -f "${0}")")")"

# 设置环境变量
export PYTHONPATH="$APPDIR/usr/share:$PYTHONPATH"

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
exec "$APPDIR/usr/lib/venv_appimage/bin/python" -m memococo.app
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
MemoCoco v${VERSION}
Build Date: $(date)
Python Version: $(python3 --version)
Build Host: $(hostname)
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
ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir ${APP_NAME}-${VERSION}-x86_64.AppImage

# 停用虚拟环境
deactivate

# 检查是否成功创建了 AppImage
if [ -f "${APP_NAME}-${VERSION}-x86_64.AppImage" ]; then
    # 使文件可执行
    chmod +x ${APP_NAME}-${VERSION}-x86_64.AppImage
    
    echo "=================================================="
    echo "AppImage 打包成功！"
    echo "文件: ${APP_NAME}-${VERSION}-x86_64.AppImage"
    echo "文件大小: $(du -h ${APP_NAME}-${VERSION}-x86_64.AppImage | cut -f1)"
    echo "=================================================="
    echo "使用方法:"
    echo "1. 直接运行: ./${APP_NAME}-${VERSION}-x86_64.AppImage"
    echo "2. 或者双击运行"
    echo ""
    echo "系统要求:"
    echo "- Ubuntu 18.04+ / Debian 10+ 或兼容发行版"
    echo "- Python 3.8+"
    echo "- X11 图形环境"
    echo ""
    echo "推荐安装的系统依赖:"
    echo "sudo apt-get install libgl1-mesa-glx libglib2.0-0 x11-utils xdotool ffmpeg"
    echo ""
    echo "首次运行说明:"
    echo "- 数据目录: ~/.local/share/MemoCoco"
    echo "- Web界面: http://127.0.0.1:8842"
    echo "- 推荐安装 UmiOCR 以获得最佳OCR性能"
    echo "=================================================="
    
    # 创建安装说明文件
    cat > ${APP_NAME}-${VERSION}-INSTALL.txt << EOF
MemoCoco v${VERSION} AppImage 安装说明

1. 系统要求:
   - Ubuntu 18.04+ / Debian 10+ 或兼容发行版
   - Python 3.8+
   - X11 图形环境

2. 安装系统依赖:
   sudo apt-get update
   sudo apt-get install libgl1-mesa-glx libglib2.0-0 x11-utils xdotool ffmpeg

3. 运行应用:
   chmod +x ${APP_NAME}-${VERSION}-x86_64.AppImage
   ./${APP_NAME}-${VERSION}-x86_64.AppImage

4. 数据存储:
   - 配置文件: ~/.local/share/MemoCoco/
   - 截图数据: ~/.local/share/MemoCoco/screenshots/
   - 数据库: ~/.local/share/MemoCoco/memococo.db

5. Web界面:
   - 地址: http://127.0.0.1:8842
   - 建议将此地址添加为浏览器书签

6. OCR优化:
   - 推荐安装 UmiOCR: https://github.com/hiroi-sora/Umi-OCR
   - 启用UmiOCR API服务可显著提升OCR速度和准确率

7. 卸载:
   - 删除AppImage文件
   - 删除数据目录: rm -rf ~/.local/share/MemoCoco

构建信息:
- 版本: ${VERSION}
- 构建时间: $(date)
- Python版本: $(python3 --version)
EOF
    
    echo "安装说明已保存到: ${APP_NAME}-${VERSION}-INSTALL.txt"
    
else
    echo "=================================================="
    echo "AppImage 打包失败！"
    echo "请检查错误信息。"
    echo "=================================================="
    exit 1
fi

# 清理临时文件
echo "正在清理临时文件..."
rm -rf AppDir appimagetool-x86_64.AppImage venv_appimage

echo "AppImage 打包过程完成。"
