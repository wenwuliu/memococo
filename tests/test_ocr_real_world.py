"""
测试实际应用中的OCR处理

这个脚本用于测试实际应用中的OCR处理，包括：
1. 均匀时间分桶策略
2. 连续未OCR区间优化
3. 处理后的休息时间
"""

import os
import sys
import time
import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memococo.database import get_empty_text_count
from memococo.ocr_processor import start_ocr_processor

def main():
    """测试实际应用中的OCR处理"""
    print("Testing OCR processing in real-world application...")
    
    # 获取未OCR条目总数
    total_count = get_empty_text_count()
    print(f"Total empty text entries: {total_count}")
    
    # 启动OCR处理线程
    print("Starting OCR processor thread...")
    thread = start_ocr_processor(idle_time=3, max_batch_size=5)
    
    # 监控一段时间
    monitor_duration = 30  # 监控30秒
    print(f"Monitoring for {monitor_duration} seconds...")
    
    start_time = time.time()
    while time.time() - start_time < monitor_duration:
        # 每5秒检查一次未OCR条目数量
        time.sleep(5)
        current_count = get_empty_text_count()
        processed = total_count - current_count
        print(f"Time: {time.time() - start_time:.1f}s, Remaining: {current_count}, Processed: {processed}")
    
    print("Monitoring complete.")
    print(f"Final empty text count: {get_empty_text_count()}")
    print(f"Total processed: {total_count - get_empty_text_count()}")
    
    # 注意：在实际应用中，OCR处理线程是守护线程，会随主线程退出而终止
    # 这里我们不需要显式停止它

if __name__ == "__main__":
    main()
