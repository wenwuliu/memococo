#!/bin/bash
# AppImageTool 设置脚本
# 作者: liuwenwu
# 日期: 2025-01-07

set -e  # 遇到错误立即退出

# 显示欢迎信息
echo "=================================================="
echo "  AppImageTool 设置脚本"
echo "=================================================="

# 创建目录
APPIMAGES_DIR="$HOME/appImages"
echo "正在创建目录: $APPIMAGES_DIR"
mkdir -p "$APPIMAGES_DIR"

# 检查是否已存在
APPIMAGETOOL_PATH="$APPIMAGES_DIR/appimagetool-x86_64.AppImage"

if [ -f "$APPIMAGETOOL_PATH" ]; then
    echo "AppImageTool 已存在: $APPIMAGETOOL_PATH"
    echo "文件大小: $(du -h "$APPIMAGETOOL_PATH" | cut -f1)"
    echo "如需重新下载，请删除该文件后重新运行此脚本"
    exit 0
fi

# 下载 AppImageTool
echo "正在下载 AppImageTool..."
echo "下载地址: https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"

# 尝试使用不同的下载工具
if command -v wget >/dev/null 2>&1; then
    echo "使用 wget 下载..."
    wget -O "$APPIMAGETOOL_PATH" https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
elif command -v curl >/dev/null 2>&1; then
    echo "使用 curl 下载..."
    curl -L -o "$APPIMAGETOOL_PATH" https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
else
    echo "错误: 未找到 wget 或 curl 下载工具"
    echo "请手动下载 AppImageTool 并放置到: $APPIMAGETOOL_PATH"
    echo "下载地址: https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    exit 1
fi

# 检查下载是否成功
if [ ! -f "$APPIMAGETOOL_PATH" ]; then
    echo "错误: 下载失败"
    echo "请检查网络连接或手动下载文件"
    exit 1
fi

# 设置执行权限
echo "正在设置执行权限..."
chmod +x "$APPIMAGETOOL_PATH"

# 验证文件
echo "正在验证文件..."
if [ -x "$APPIMAGETOOL_PATH" ]; then
    echo "=================================================="
    echo "AppImageTool 设置成功！"
    echo "文件位置: $APPIMAGETOOL_PATH"
    echo "文件大小: $(du -h "$APPIMAGETOOL_PATH" | cut -f1)"
    echo "=================================================="
    echo "现在您可以运行 AppImage 打包脚本了:"
    echo "./build_appimage_simple.sh"
    echo "./build_appimage_pyinstaller_simple.sh"
    echo "./build_appimage.sh"
    echo "=================================================="
else
    echo "错误: 文件验证失败"
    echo "请检查文件是否正确下载"
    exit 1
fi
