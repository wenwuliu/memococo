#!/usr/bin/env python3
"""
OCR性能测试脚本

这个脚本用于测试OCR的性能，比较CPU和GPU版本的速度差异
"""

import os
import sys
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memococo.ocr import rapid_ocr, get_ocr_engine

def create_test_image(text="这是一个测试图像", size=(800, 600)):
    """创建测试图像

    Args:
        text: 图像中的文本
        size: 图像大小

    Returns:
        numpy 数组形式的图像
    """
    # 创建空白图像
    img = Image.new('RGB', size, color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 尝试加载字体
    try:
        font = ImageFont.truetype("Arial", 20)
    except:
        font = ImageFont.load_default()

    # 添加文本
    lines = text.split('\n')
    y = 50
    for line in lines:
        draw.text((50, y), line, fill=(0, 0, 0), font=font)
        y += 30

    # 转换为 numpy 数组
    return np.array(img)

def test_ocr_performance(num_images=5, num_runs=3, check_gpu=False):
    """测试OCR性能

    Args:
        num_images: 测试图像数量
        num_runs: 测试运行次数
        check_gpu: 是否检查GPU使用情况
    """
    print(f"\n测试OCR性能 ({num_images} 张图像, {num_runs} 次运行)...")

    # 创建测试图像
    test_images = []
    for i in range(num_images):
        test_images.append(create_test_image(
            f"测试图像 {i+1}\n这是用于测试OCR性能的图像\n包含中文和数字123456789\n"
            f"测试GPU加速效果\n第五行文本\n第六行文本"
        ))

    # 初始化OCR引擎
    engine = get_ocr_engine()
    if engine is None:
        print("❌ OCR引擎初始化失败")
        return

    # 检查OCR引擎是否使用GPU
    print(f"OCR引擎: {engine}")

    # 如果需要检查GPU使用情况，等待用户确认
    if check_gpu:
        print("\n请在另一个终端运行 nvtop 或 nvidia-smi 监控GPU使用情况")
        print("按Enter键继续...")
        input()

    # 测试单张图像OCR性能
    print("\n单张图像OCR性能测试:")
    single_times = []
    for run in range(num_runs):
        start_time = time.time()
        result = rapid_ocr(test_images[0])
        end_time = time.time()
        elapsed = end_time - start_time
        single_times.append(elapsed)
        print(f"  运行 {run+1}: {elapsed:.4f} 秒")

    avg_single_time = sum(single_times) / len(single_times)
    print(f"  平均时间: {avg_single_time:.4f} 秒")

    # 测试批量图像OCR性能
    print("\n批量图像OCR性能测试:")
    batch_times = []
    for run in range(num_runs):
        start_time = time.time()
        results = []
        for img in test_images:
            result = rapid_ocr(img)
            results.append(result)
        end_time = time.time()
        elapsed = end_time - start_time
        batch_times.append(elapsed)
        print(f"  运行 {run+1}: {elapsed:.4f} 秒 (平均每张 {elapsed/num_images:.4f} 秒)")

    avg_batch_time = sum(batch_times) / len(batch_times)
    print(f"  总平均时间: {avg_batch_time:.4f} 秒 (平均每张 {avg_batch_time/num_images:.4f} 秒)")

    # 输出结果
    import onnxruntime as ort
    providers = ort.get_available_providers()
    gpu_available = any(p in providers for p in ['CUDAExecutionProvider', 'TensorrtExecutionProvider'])
    acceleration = "GPU" if gpu_available else "CPU"

    print(f"\n使用 {acceleration} 的OCR性能总结:")
    print(f"  单张图像平均时间: {avg_single_time:.4f} 秒")
    print(f"  批量处理平均时间: {avg_batch_time:.4f} 秒 (每张 {avg_batch_time/num_images:.4f} 秒)")

    # 显示OCR结果示例
    if results:
        print("\nOCR结果示例:")
        for i, result in enumerate(results[:2]):  # 只显示前两个结果
            text = ""
            for item in result:
                text += item[1]
            print(f"  图像 {i+1}: {text[:100]}...")  # 只显示前100个字符

def main():
    """主函数"""
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="OCR性能测试")
    parser.add_argument("--check-gpu", action="store_true", help="检查GPU使用情况")
    parser.add_argument("--images", type=int, default=5, help="测试图像数量")
    parser.add_argument("--runs", type=int, default=3, help="测试运行次数")
    args = parser.parse_args()

    print("=" * 50)
    print("OCR性能测试")
    print("=" * 50)

    # 测试OCR性能
    test_ocr_performance(num_images=args.images, num_runs=args.runs, check_gpu=args.check_gpu)

    print("\n测试完成!")

if __name__ == "__main__":
    main()
