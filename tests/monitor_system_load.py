"""
监控系统负载

这个脚本用于监控系统负载，包括CPU使用率和温度
"""

import os
import sys
import time
import psutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memococo.utils import get_cpu_temperature

def main():
    """监控系统负载"""
    print("Monitoring system load...")
    
    # 监控一段时间
    monitor_duration = 30  # 监控30秒
    print(f"Monitoring for {monitor_duration} seconds...")
    
    # 记录初始值
    print("Time(s) | CPU(%) | Temp(°C)")
    print("---------------------------")
    
    start_time = time.time()
    while time.time() - start_time < monitor_duration:
        # 获取CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 获取CPU温度
        cpu_temperature = get_cpu_temperature()
        
        # 打印结果
        elapsed = time.time() - start_time
        print(f"{elapsed:6.1f} | {cpu_percent:6.1f} | {cpu_temperature if cpu_temperature else 'N/A':6}")
        
        # 休眠一段时间
        time.sleep(2)
    
    print("Monitoring complete.")

if __name__ == "__main__":
    main()
