import time
import os
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from memococo.screenshot import get_ocr_result_async, compress_img_PIL_async

# 创建测试图像
print("创建测试图像...")
img = Image.new('RGB', (1000, 500), color=(255, 255, 255))
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("Arial", 20)
except:
    font = ImageFont.load_default()
draw.text((50, 50), "这是一个测试图像", fill=(0, 0, 0), font=font)
draw.text((50, 100), "用于测试异步任务处理", fill=(0, 0, 0), font=font)
draw.text((50, 150), "包括OCR和图像压缩", fill=(0, 0, 0), font=font)

# 保存图像
temp_file = os.path.join(tempfile.gettempdir(), 'test_async_image.png')
img.save(temp_file, format='PNG')
print(f"图像已保存到: {temp_file}")
print(f"原始图像大小: {os.path.getsize(temp_file) / 1024:.2f} KB")

# 转换为numpy数组
img_array = np.array(img)

# 测试异步OCR
print("\n测试异步OCR处理...")
ocr_results = []

def ocr_callback(result):
    ocr_results.append(result)
    print(f"OCR回调收到结果: {result}")

start_time = time.time()
ocr_future = get_ocr_result_async(img_array, ocr_callback)
print(f"异步OCR任务已提交，耗时: {time.time() - start_time:.4f}秒")

# 测试异步图像压缩
print("\n测试异步图像压缩...")
compress_results = []

def compress_callback(result):
    compress_results.append(True)
    print(f"压缩回调收到结果，压缩后大小: {os.path.getsize(temp_file) / 1024:.2f} KB")

start_time = time.time()
compress_future = compress_img_PIL_async(temp_file, target_size_kb=50, callback=compress_callback)
print(f"异步压缩任务已提交，耗时: {time.time() - start_time:.4f}秒")

# 等待异步任务完成
print("\n等待异步任务完成...")
for i in range(30):
    if len(ocr_results) > 0 and len(compress_results) > 0:
        print("所有任务已完成!")
        break
    time.sleep(0.5)
    print(f"等待中... {i*0.5 + 0.5:.1f}秒")
    print(f"  OCR任务状态: {'完成' if len(ocr_results) > 0 else '进行中'}")
    print(f"  压缩任务状态: {'完成' if len(compress_results) > 0 else '进行中'}")

print("\n测试结果:")
print(f"OCR结果: {ocr_results[0] if ocr_results else '未完成'}")
print(f"压缩后图像大小: {os.path.getsize(temp_file) / 1024:.2f} KB")
