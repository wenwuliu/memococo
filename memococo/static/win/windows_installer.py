import os
import sys
import subprocess
import threading
import ctypes
import winshell
from PIL import Image
from pystray import Icon, Menu, MenuItem

# 配置信息
APP_NAME = "MemoCoco"
PYTHON_PATH = sys.executable  # 自动获取当前Python解释器路径
SCRIPT_PATH = os.path.abspath(sys.argv[0])
ICON_PATH = os.path.join(os.path.dirname(SCRIPT_PATH), "icon.ico")  # 需要准备一个ico图标文件

# 全局变量
app_process = None
is_updating = False

def create_shortcut():
    """在桌面创建快捷方式"""
    try:
        desktop = winshell.desktop()
        path = os.path.join(desktop, f"{APP_NAME} Tool.lnk")
        with winshell.shortcut(path) as shortcut:
            shortcut.path = PYTHON_PATH
            shortcut.arguments = f'"{SCRIPT_PATH}"'
            shortcut.icon_location = (ICON_PATH, 0)
            shortcut.description = f"{APP_NAME} Launcher"
        ctypes.windll.user32.MessageBoxW(0, "桌面快捷方式创建成功！", "成功", 0x40)
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, f"创建快捷方式失败：{str(e)}", "错误", 0x10)

def start_application():
    """启动主应用程序"""
    global app_process
    if app_process and app_process.poll() is None:
        return  # 已经在运行
    
    try:
        app_process = subprocess.Popen([PYTHON_PATH, "-m", "memococo.app"])
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, f"启动失败：{str(e)}", "错误", 0x10)

def update_application():
    """更新应用程序"""
    global is_updating
    if is_updating:
        return
    
    is_updating = True
    try:
        # 先停止正在运行的应用
        if app_process and app_process.poll() is None:
            app_process.terminate()
            app_process.wait()
        
        # 执行更新命令
        result = subprocess.run(
            [PYTHON_PATH, "-m", "pip", "install", "--upgrade", "--no-cache-dir", 
             "git+https://github.com/wenwuliu/memococo.git"],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            ctypes.windll.user32.MessageBoxW(0, "更新成功！请重新启动应用", "成功", 0x40)
        else:
            ctypes.windll.user32.MessageBoxW(0, f"更新失败：{result.stderr}", "错误", 0x10)
    finally:
        is_updating = False

def exit_application(icon):
    """退出应用程序"""
    if app_process and app_process.poll() is None:
        app_process.terminate()
        app_process.wait()
    icon.stop()

def setup_tray_icon():
    """设置系统托盘图标"""
    try:
        image = Image.open(ICON_PATH)
    except FileNotFoundError:
        # 如果图标不存在，创建一个默认的
        image = Image.new('RGB', (64, 64), color=(255, 0, 0))
        ImageDraw.Draw(image).text((10, 25), "MC", fill=(255, 255, 255))
    
    menu = Menu(
        MenuItem('启动应用', lambda: threading.Thread(target=start_application).start()),
        MenuItem('创建桌面快捷方式', lambda: threading.Thread(target=create_shortcut).start()),
        MenuItem('更新应用', lambda: threading.Thread(target=update_application).start()),
        Menu.SEPARATOR,
        MenuItem('退出', lambda icon: threading.Thread(target=exit_application, args=(icon,)).start())
    )
    
    icon = Icon(APP_NAME, image, APP_NAME, menu)
    return icon

if __name__ == "__main__":
    # 确保在退出时清理进程
    try:
        icon = setup_tray_icon()
        icon.run()
    finally:
        if app_process and app_process.poll() is None:
            app_process.terminate()