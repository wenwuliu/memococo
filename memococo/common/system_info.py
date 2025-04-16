"""
系统信息模块

提供获取系统信息的功能，如CPU使用率、内存使用率、温度等
"""

import os
import platform
import psutil
from typing import Optional, Dict, Any, Tuple

def get_cpu_usage() -> float:
    """获取CPU使用率
    
    Returns:
        float: CPU使用率（百分比）
    """
    try:
        return psutil.cpu_percent(interval=0.1)
    except Exception as e:
        print(f"获取CPU使用率失败: {e}")
        return 0.0

def get_memory_usage() -> Dict[str, Any]:
    """获取内存使用情况
    
    Returns:
        Dict[str, Any]: 内存使用情况
    """
    try:
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent
        }
    except Exception as e:
        print(f"获取内存使用情况失败: {e}")
        return {
            "total": 0,
            "available": 0,
            "used": 0,
            "percent": 0
        }

def get_disk_usage(path: str = "/") -> Dict[str, Any]:
    """获取磁盘使用情况
    
    Args:
        path: 磁盘路径
        
    Returns:
        Dict[str, Any]: 磁盘使用情况
    """
    try:
        disk = psutil.disk_usage(path)
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
    except Exception as e:
        print(f"获取磁盘使用情况失败: {path}, 错误: {e}")
        return {
            "total": 0,
            "used": 0,
            "free": 0,
            "percent": 0
        }

def get_cpu_temperature() -> Optional[float]:
    """获取CPU温度
    
    Returns:
        Optional[float]: CPU温度（摄氏度），如果无法获取则返回None
    """
    try:
        # Linux系统
        if platform.system() == "Linux":
            # 尝试从thermal_zone读取温度
            for i in range(10):  # 尝试前10个thermal_zone
                thermal_zone_path = f"/sys/class/thermal/thermal_zone{i}/temp"
                if os.path.exists(thermal_zone_path):
                    with open(thermal_zone_path, "r") as f:
                        temp = int(f.read().strip()) / 1000.0
                        if temp > 0 and temp < 150:  # 合理的温度范围
                            return temp
            
            # 尝试从hwmon读取温度
            hwmon_dir = "/sys/class/hwmon"
            if os.path.exists(hwmon_dir):
                for hwmon in os.listdir(hwmon_dir):
                    hwmon_path = os.path.join(hwmon_dir, hwmon)
                    for i in range(10):  # 尝试前10个温度传感器
                        temp_path = os.path.join(hwmon_path, f"temp{i}_input")
                        if os.path.exists(temp_path):
                            with open(temp_path, "r") as f:
                                temp = int(f.read().strip()) / 1000.0
                                if temp > 0 and temp < 150:  # 合理的温度范围
                                    return temp
        
        # macOS系统
        elif platform.system() == "Darwin":
            try:
                import subprocess
                result = subprocess.run(["sysctl", "-n", "machdep.xcpm.cpu_thermal_level"], capture_output=True, text=True)
                if result.returncode == 0:
                    return float(result.stdout.strip())
            except Exception:
                pass
        
        # Windows系统
        elif platform.system() == "Windows":
            try:
                import wmi
                w = wmi.WMI(namespace="root\\wmi")
                temperature_info = w.MSAcpi_ThermalZoneTemperature()[0]
                return float(temperature_info.CurrentTemperature) / 10.0 - 273.15
            except Exception:
                pass
        
        # 如果以上方法都失败，尝试使用psutil
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current > 0:
                            return entry.current
        
        return None
    except Exception as e:
        print(f"获取CPU温度失败: {e}")
        return None

def get_system_info() -> Dict[str, Any]:
    """获取系统信息
    
    Returns:
        Dict[str, Any]: 系统信息
    """
    try:
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "platform_release": platform.release(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "cpu_usage": get_cpu_usage(),
            "memory": get_memory_usage(),
            "disk": get_disk_usage(),
            "cpu_temperature": get_cpu_temperature()
        }
    except Exception as e:
        print(f"获取系统信息失败: {e}")
        return {}

def check_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """检查端口是否可用
    
    Args:
        port: 端口号
        host: 主机地址
        
    Returns:
        bool: 端口是否可用
    """
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((host, port)) != 0
    except Exception as e:
        print(f"检查端口可用性失败: {host}:{port}, 错误: {e}")
        return False

def set_cpu_affinity(pid: Optional[int] = None, cpu_list: Optional[list] = None) -> bool:
    """设置进程的CPU亲和性
    
    Args:
        pid: 进程ID，默认为当前进程
        cpu_list: 允许运行的CPU核心列表，例如[0, 1, 2, 3]
        
    Returns:
        bool: 操作是否成功
    """
    try:
        if pid is None:
            pid = os.getpid()  # 默认操作当前进程
        
        process = psutil.Process(pid)
        
        if cpu_list is None:
            cpu_list = list(range(psutil.cpu_count()))  # 默认使用所有核心
        
        process.cpu_affinity(cpu_list)
        print(f"Set CPU affinity for PID {pid} to cores: {cpu_list}")
        return True
    except Exception as e:
        print(f"设置CPU亲和性失败: {e}")
        return False
