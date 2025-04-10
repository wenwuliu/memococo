"""
测试同步压缩和按时间顺序处理OCR

这个脚本用于测试：
1. 同步图像压缩（先压缩，再保存到数据库）
2. 按时间升序（从旧到新）处理OCR任务
"""

import os
import time
import unittest
from datetime import datetime, timedelta

from PIL import Image
import numpy as np

from memococo.database import create_db, insert_entry, get_batch_empty_text, get_db_connection
from memococo.config import screenshots_path
from memococo.screenshot import compress_img_PIL
from memococo.ocr_processor import process_batch_ocr

class TestSyncCompressionOldestFirstOcr(unittest.TestCase):
    """测试同步压缩和按时间顺序处理OCR"""

    def setUp(self):
        """测试前的准备工作"""
        # 确保数据库已创建
        create_db()

        # 清空数据库中的所有条目
        with get_db_connection() as conn:
            conn.execute("DELETE FROM entries")
            conn.commit()

        # 创建测试目录
        self.test_date = datetime.now()
        self.test_dir = os.path.join(
            screenshots_path,
            self.test_date.strftime("%Y/%m/%d")
        )
        os.makedirs(self.test_dir, exist_ok=True)

        # 创建一个空白图片
        self.blank_image = Image.new('RGB', (100, 100), color='white')

    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试图片
        for timestamp in self.test_timestamps:
            image_path = os.path.join(self.test_dir, f"{timestamp}.webp")
            if os.path.exists(image_path):
                os.remove(image_path)

    def test_sync_compression(self):
        """测试同步压缩图像"""
        # 创建测试图片
        self.test_timestamps = []
        timestamp = int(time.time())
        self.test_timestamps.append(timestamp)

        # 保存图片
        image_path = os.path.join(self.test_dir, f"{timestamp}.webp")
        self.blank_image.save(image_path, 'WEBP')

        # 获取原始文件大小
        original_size = os.path.getsize(image_path)

        # 压缩图片
        compress_img_PIL(image_path, target_size_kb=10)

        # 获取压缩后的文件大小
        compressed_size = os.path.getsize(image_path)

        # 验证压缩是否有效
        self.assertLessEqual(compressed_size, original_size, "压缩后的文件大小应该小于或等于原始大小")

        print(f"原始大小: {original_size/1024:.2f} KB, 压缩后大小: {compressed_size/1024:.2f} KB")

    def test_oldest_first_ocr(self):
        """测试按时间升序（从旧到新）处理OCR任务"""
        # 创建测试数据，使用不同的时间戳
        self.test_timestamps = []
        base_time = int(time.time()) - 100  # 基准时间，100秒前

        # 创建5个条目，时间戳依次增加
        for i in range(5):
            timestamp = base_time + i * 10  # 每个条目间隔10秒
            self.test_timestamps.append(timestamp)

            # 保存图片
            image_path = os.path.join(self.test_dir, f"{timestamp}.webp")
            self.blank_image.save(image_path, 'WEBP')

            # 插入数据库条目，使用空文本
            insert_entry("", timestamp, "", f"TestApp{i}", f"TestTitle{i}")

        # 获取空文本条目，按时间升序（从旧到新）
        entries = get_batch_empty_text(batch_size=10, oldest_first=True)

        # 验证条目是否按时间升序排序
        self.assertEqual(len(entries), 5, "应该获取到5条空文本条目")
        for i in range(len(entries) - 1):
            self.assertLessEqual(entries[i].timestamp, entries[i+1].timestamp,
                               "条目应该按时间升序（从旧到新）排序")

        # 验证第一个条目是最早的
        self.assertEqual(entries[0].timestamp, self.test_timestamps[0],
                       "第一个条目应该是最早的")

        # 处理OCR任务
        processed = process_batch_ocr(batch_size=10)

        # 验证处理结果
        self.assertEqual(processed, 0, "由于OCR返回空文本，processed应该为0")

def main():
    print("\n运行测试: 同步压缩和按时间顺序处理OCR")
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()
