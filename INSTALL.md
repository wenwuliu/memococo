# MemoCoco 安装说明

## 使用 .deb 包安装

1. 下载 memococo_2.2.1_amd64.deb 包
2. 使用以下命令安装：
   ```bash
   sudo dpkg -i memococo_2.2.1_amd64.deb
   ```
3. 安装脚本会自动安装所有必要的依赖
4. 安装完成后，可以通过以下方式启动 MemoCoco：
   - 从应用程序菜单启动
   - 在终端中运行 `memococo` 命令
   - 设置为系统服务自动启动：`sudo systemctl enable --now memococo@<用户名>`

## 注意事项

- 安装过程需要 sudo 权限
- 安装脚本会使用 apt-get 和 pip3 安装依赖，需要联网
- 用户数据存储在 /var/lib/memococo 目录中
- 卸载时不会删除用户数据，需要手动删除

## 卸载方法

使用以下命令卸载 MemoCoco：

```bash
sudo apt remove memococo
```

如果想完全删除所有数据，请手动运行：

```bash
sudo rm -rf /var/lib/memococo
```

## 从源码构建 .deb 包

如果你想自己构建 .deb 包，可以使用项目根目录下的 `build_deb.sh` 脚本：

```bash
./build_deb.sh
```

构建前需要安装以下依赖：

```bash
sudo apt-get install ruby ruby-dev rubygems build-essential
sudo gem install fpm
```
