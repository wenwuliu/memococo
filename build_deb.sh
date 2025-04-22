#!/bin/bash
# MemoCoco .deb 打包脚本
# 作者: liuwenwu
# 日期: 2024-04-08

# 设置版本号
VERSION="2.2.11"
PACKAGE_NAME="memococo"

# 显示欢迎信息
echo "=================================================="
echo "  MemoCoco .deb 打包脚本 v1.0"
echo "=================================================="
echo "当前版本: $VERSION"
echo "开始打包..."

# 清理旧的打包文件
echo "正在清理旧的打包文件..."
rm -rf pkg debian/.debhelper debian/memococo debian/debhelper-build-stamp debian/files debian/*.log debian/*.substvars
rm -f ${PACKAGE_NAME}_${VERSION}_amd64.deb

# 创建目录结构
echo "正在创建目录结构..."
mkdir -p pkg/usr/bin pkg/usr/share/memococo pkg/usr/share/applications pkg/usr/share/icons/hicolor/128x128/apps

# 复制应用程序文件
echo "正在复制应用程序文件..."
cp -r memococo pkg/usr/share/memococo/

# 创建启动脚本
echo "正在创建启动脚本..."
cat > pkg/usr/bin/memococo << 'EOF'
#!/bin/bash
# 启动 MemoCoco 应用程序的脚本

# 设置环境变量
export PYTHONPATH=/usr/share/memococo:$PYTHONPATH

# 检查数据目录
DATA_DIR="/var/lib/memococo"
if [ ! -d "$DATA_DIR" ]; then
    echo "Creating data directory: $DATA_DIR"
    mkdir -p "$DATA_DIR"
    # 如果以root运行，尝试设置正确的权限
    if [ "$(id -u)" = "0" ]; then
        chown $(logname):$(logname) "$DATA_DIR"
    fi
fi

# 检查数据目录权限
if [ ! -w "$DATA_DIR" ]; then
    echo "Warning: Data directory $DATA_DIR is not writable by current user"
fi

# 启动应用程序
echo "Starting MemoCoco application..."
python3 -m memococo.app
EOF

# 设置可执行权限
chmod +x pkg/usr/bin/memococo

# 创建桌面快捷方式
echo "正在创建桌面快捷方式..."
cat > pkg/usr/share/applications/memococo.desktop << 'EOF'
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
cp memococo/static/favicon144x144.png pkg/usr/share/icons/hicolor/128x128/apps/memococo.png

# 创建 systemd 服务文件
echo "正在创建 systemd 服务文件..."
cat > pkg/usr/share/memococo/memococo@.service << 'EOF'
[Unit]
Description=MemoCoco Service
After=network.target graphical-session.target
Wants=network.target graphical-session.target

[Service]
Type=simple
User=%i
Environment="PYTHONPATH=/usr/share/memococo:${PYTHONPATH}"
WorkingDirectory=/var/lib/memococo
ExecStart=/usr/bin/memococo
Restart=on-failure
RestartSec=5s

# 确保服务可以访问数据目录
ExecStartPre=/bin/sh -c 'mkdir -p /var/lib/memococo && chown %i:%i /var/lib/memococo'

# 添加日志配置
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 创建安装后脚本
echo "正在创建安装后脚本..."
cat > postinst.sh << 'EOF'
#!/bin/bash
# 安装后脚本

# 安装系统依赖
echo "正在安装系统依赖..."
apt-get update
apt-get install -y python3-flask python3-mss python3-toml python3-opencv xprop ffmpeg xdotool python3-numpy python3-requests

# 安装 Python 依赖
echo "正在安装 Python 依赖..."
pip3 install Flask>=3.0.3 numpy>=1.26.4 mss>=9.0.1 toml>=0.10.2 pyautogui>=0.9.54 ffmpeg-python>=0.2.0 requests>=2.32.3 jsonify>=0.5 opencv-python>=4.5.1 pillow>=8.2.0 psutil>=5.8.0

# 尝试安装 rapidocr-onnxruntime（必需）
echo "正在安装 OCR 引擎..."
pip3 install rapidocr_onnxruntime>=1.2.3 || echo "警告: 无法安装 rapidocr-onnxruntime。OCR 功能将无法使用。"

# 创建数据目录
echo "正在创建数据目录..."
mkdir -p /var/lib/memococo
chmod 777 /var/lib/memococo
# 注意：这里我们使用777权限确保所有用户都可以访问该目录
# 服务启动时会为特定用户设置正确的权限

# 安装 systemd 服务
echo "正在安装系统服务..."
cp /usr/share/memococo/memococo@.service /etc/systemd/system/
systemctl daemon-reload

echo "=================================================="
echo "MemoCoco 已成功安装！"
echo "你可以通过运行 'memococo' 命令或从应用程序菜单启动它。"
echo "要设置服务自动启动，请运行: sudo systemctl enable --now memococo@<用户名>"
echo "=================================================="
EOF

# 创建卸载前脚本
echo "正在创建卸载前脚本..."
cat > prerm.sh << 'EOF'
#!/bin/bash
# 卸载前脚本

echo "正在停止 MemoCoco 服务..."
# 停止并禁用服务
systemctl stop memococo@* || true
systemctl disable memococo@* || true

echo "正在删除系统服务文件..."
# 删除 systemd 服务文件
rm -f /etc/systemd/system/memococo@.service
systemctl daemon-reload

echo "注意: 用户数据在 /var/lib/memococo 目录中保留。"
echo "如果你想完全删除所有数据，请手动运行: sudo rm -rf /var/lib/memococo"
EOF

# 设置脚本可执行权限
chmod +x postinst.sh prerm.sh

# 使用 fpm 创建 Debian 包
echo "正在使用 fpm 创建 Debian 包..."
fpm -s dir -t deb -n $PACKAGE_NAME -v $VERSION -C pkg \
    --after-install postinst.sh \
    --before-remove prerm.sh \
    --depends python3 \
    --depends python3-pip \
    --description "MemoCoco - 时间胶囊，自动记录屏幕截图和文本" \
    --maintainer "liuwenwu <liuawu625@163.com>" \
    --url "https://github.com/liuwenwu520/MemoCoco" \
    --license "MIT" \
    .

# 检查是否成功创建了 .deb 包
if [ -f "${PACKAGE_NAME}_${VERSION}_amd64.deb" ]; then
    echo "=================================================="
    echo "打包成功！"
    echo "包文件: ${PACKAGE_NAME}_${VERSION}_amd64.deb"
    echo "文件大小: $(du -h ${PACKAGE_NAME}_${VERSION}_amd64.deb | cut -f1)"
    echo "=================================================="
else
    echo "=================================================="
    echo "打包失败！"
    echo "请检查错误信息。"
    echo "=================================================="
    exit 1
fi

# 清理临时文件
echo "正在清理临时文件..."
rm -rf pkg postinst.sh prerm.sh

echo "打包过程完成。"
