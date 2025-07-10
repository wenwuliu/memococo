#!/bin/bash
# MemoCoco AppImage 打包脚本 (使用 PyInstaller)
# 作者: liuwenwu
# 日期: 2025-01-07

set -e  # 遇到错误立即退出

# 设置版本号和基本信息
VERSION="2.2.12"
APP_NAME="MemoCoco"
APP_DIR_NAME="memococo"

# 显示欢迎信息
echo "=================================================="
echo "  MemoCoco AppImage 打包脚本 (PyInstaller) v1.0"
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

# 创建 PyInstaller 规格文件
echo "正在创建 PyInstaller 规格文件..."
cat > memococo.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# 获取项目根目录 - 使用当前工作目录
project_root = Path.cwd()

# 收集所有需要的数据文件
datas = []

# 添加模板文件
templates_dir = project_root / 'memococo' / 'templates'
if templates_dir.exists():
    datas.append((str(templates_dir), 'memococo/templates'))

# 添加静态文件
static_dir = project_root / 'memococo' / 'static'
if static_dir.exists():
    datas.append((str(static_dir), 'memococo/static'))

# 添加国际化文件
i18n_dir = project_root / 'memococo' / 'i18n'
if i18n_dir.exists():
    datas.append((str(i18n_dir), 'memococo/i18n'))

# 隐藏导入
hiddenimports = [
    # MemoCoco 核心模块
    'memococo.app',
    'memococo.config',
    'memococo.config_schema',
    'memococo.database',
    'memococo.screenshot',
    'memococo.ocr',
    'memococo.ocr_factory',
    'memococo.ocr_processor',
    'memococo.umiocr_client',
    'memococo.utils',
    'memococo.ollama',
    'memococo.app_map',

    # 通用模块
    'memococo.common.error_handler',
    'memococo.common.error_middleware',
    'memococo.common.config_manager',
    'memococo.common.db_manager',

    # 国际化模块
    'memococo.i18n',
    'memococo.i18n.flask_i18n',

    # 第三方库
    'flask',
    'flask.templating',
    'jinja2',
    'werkzeug',
    'numpy',
    'cv2',
    'PIL',
    'PIL.Image',
    'mss',
    'pyautogui',
    'psutil',
    'requests',
    'rapidocr_onnxruntime',
    'babel',
    'babel.core',
    'toml',
    'sqlite3',
    'threading',
    'multiprocessing',
    'concurrent.futures',
    'json',
    'base64',
    'datetime',
    'time',
    'os',
    'sys',
    'platform',
    'subprocess',
    'logging',
    'collections',
    'pathlib',
    'urllib',
    'urllib.parse',
    'urllib.request',
]

# 排除不需要的模块
excludes = [
    'tkinter',
    'matplotlib',
    'scipy',
    'pandas',
    'jupyter',
    'IPython',
    'notebook',
]

block_cipher = None

a = Analysis(
    ['memococo/app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='memococo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='memococo',
)
EOF

# 运行 PyInstaller
echo "正在运行 PyInstaller..."
pyinstaller --clean --noconfirm memococo.spec

# 检查 PyInstaller 输出
if [ ! -d "dist/memococo" ]; then
    echo "错误: PyInstaller 构建失败"
    exit 1
fi

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

# 启动应用程序
echo "Starting MemoCoco application..."
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
Categories=Utility;
StartupNotify=true
EOF

# 复制图标
echo "正在复制图标..."
cp memococo/static/favicon144x144.png AppDir/memococo.png
cp memococo/static/favicon144x144.png AppDir/usr/share/icons/hicolor/128x128/apps/memococo.png

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
    echo "注意事项:"
    echo "- 首次运行时会在 ~/.local/share/MemoCoco 创建数据目录"
    echo "- 应用程序会在 http://127.0.0.1:8842 启动Web界面"
    echo "- 建议安装 UmiOCR 以获得最佳OCR性能"
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

echo "AppImage 打包过程完成。"
