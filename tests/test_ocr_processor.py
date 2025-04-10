"""
测试OCR处理模块

这个脚本用于测试OCR处理模块的功能
"""

import time
import threading
from memococo.database import create_db, insert_entry, get_newest_empty_text
from memococo.ocr_processor import process_batch_ocr, start_ocr_processor

def test_process_batch_ocr():
    """测试批量处理OCR任务"""
    print("测试批量处理OCR任务...")
    
    # 确保数据库已创建
    create_db()
    
    # 插入一些测试数据
    timestamp = int(time.time())
    for i in range(5):
        insert_entry("", timestamp + i, "", f"TestApp{i}", f"TestTitle{i}")
        print(f"插入测试数据 {i+1}/5")
    
    # 检查是否有未OCR的数据
    entry = get_newest_empty_text()
    if entry:
        print(f"找到未OCR的数据: {entry}")
    else:
        print("没有找到未OCR的数据")
        return
    
    # 处理一批OCR任务
    processed = process_batch_ocr(batch_size=3)
    print(f"处理了 {processed} 个OCR任务")
    
    # 检查是否还有未OCR的数据
    entry = get_newest_empty_text()
    if entry:
        print(f"还有未OCR的数据: {entry}")
    else:
        print("所有数据都已处理")

def test_ocr_processor_thread():
    """测试OCR处理线程"""
    print("测试OCR处理线程...")
    
    # 确保数据库已创建
    create_db()
    
    # 插入一些测试数据
    timestamp = int(time.time())
    for i in range(10):
        insert_entry("", timestamp + i, "", f"TestApp{i}", f"TestTitle{i}")
        print(f"插入测试数据 {i+1}/10")
    
    # 启动OCR处理线程
    ocr_thread = start_ocr_processor()
    print("OCR处理线程已启动")
    
    # 等待一段时间，让OCR处理线程工作
    print("等待OCR处理线程工作...")
    for i in range(10):
        time.sleep(1)
        print(f"等待中... {i+1}/10秒")
        
        # 检查是否还有未OCR的数据
        entry = get_newest_empty_text()
        if entry:
            print(f"还有未OCR的数据: {entry}")
        else:
            print("所有数据都已处理")
            break
    
    print("测试完成")

if __name__ == "__main__":
    # 测试批量处理OCR任务
    test_process_batch_ocr()
    
    # 测试OCR处理线程
    test_ocr_processor_thread()
