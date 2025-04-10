"""
测试优化后的OCR处理模块

这个脚本用于测试优化后的OCR处理模块的功能：
1. 批量查询空文本条目
2. 当图片不存在时删除数据库条目
"""

import os
import time
import unittest
import tempfile
import shutil
from datetime import datetime

from memococo.database import create_db, insert_entry, get_batch_empty_text, get_db_connection
from memococo.config import screenshots_path
from memococo.ocr_processor import process_ocr_task, process_batch_ocr

class TestOptimizedOcr(unittest.TestCase):
    """测试优化后的OCR处理模块"""

    def setUp(self):
        """测试前的准备工作"""
        # 确保数据库已创建
        create_db()

        # 清空数据库中的所有条目
        with get_db_connection() as conn:
            conn.execute("DELETE FROM entries")
            conn.commit()

        # 创建临时测试目录
        self.test_date = datetime.now()
        self.test_dir = os.path.join(
            screenshots_path,
            self.test_date.strftime("%Y/%m/%d")
        )
        os.makedirs(self.test_dir, exist_ok=True)

        # 创建一些测试图片
        self.test_timestamps = []

        # 创建一个空白图片
        from PIL import Image
        import numpy as np

        # 创建一个简单的空白图片
        blank_image = Image.new('RGB', (100, 100), color='white')

        for i in range(5):
            timestamp = int(time.time()) - i
            self.test_timestamps.append(timestamp)

            # 只为前3个时间戳创建图片文件
            if i < 3:
                image_path = os.path.join(self.test_dir, f"{timestamp}.webp")
                blank_image.save(image_path, 'WEBP')

    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试图片
        for timestamp in self.test_timestamps:
            image_path = os.path.join(self.test_dir, f"{timestamp}.webp")
            if os.path.exists(image_path):
                os.remove(image_path)

    def test_batch_empty_text(self):
        """测试批量获取空文本条目"""
        # 插入测试数据
        for timestamp in self.test_timestamps:
            insert_entry("", timestamp, "", f"TestApp{timestamp}", f"TestTitle{timestamp}")

        # 批量获取空文本条目
        entries = get_batch_empty_text(batch_size=10)
        self.assertEqual(len(entries), 5, "应该获取到5条空文本条目")

        # 检查条目是否按时间戳降序排序
        for i in range(len(entries) - 1):
            self.assertGreaterEqual(entries[i].timestamp, entries[i+1].timestamp,
                                   "条目应该按时间戳降序排序")

    def test_delete_missing_image(self):
        """测试当图片不存在时删除数据库条目"""
        # 插入测试数据
        for timestamp in self.test_timestamps:
            insert_entry("", timestamp, "", f"TestApp{timestamp}", f"TestTitle{timestamp}")

        # 获取所有空文本条目
        entries = get_batch_empty_text(batch_size=10)
        self.assertEqual(len(entries), 5, "应该获取到5条空文本条目")

        # 处理所有条目
        for entry in entries:
            result = process_ocr_task(entry)

            # 检查结果
            if entry.timestamp in self.test_timestamps[:3]:
                # 前3个时间戳有图片文件，应该返回None（OCR失败，但不删除条目）
                self.assertIsNone(result, f"有图片的条目应该返回None，但返回了{result}")
            else:
                # 后2个时间戳没有图片文件，应该返回"DELETED"
                self.assertEqual(result, "DELETED", f"没有图片的条目应该返回DELETED，但返回了{result}")

        # 再次获取所有空文本条目，应该只剩下3条（有图片的条目）
        entries = get_batch_empty_text(batch_size=10)
        self.assertEqual(len(entries), 3, "应该只剩下3条有图片的条目")

    def test_batch_processing(self):
        """测试批量处理OCR任务"""
        # 插入测试数据
        for timestamp in self.test_timestamps:
            insert_entry("", timestamp, "", f"TestApp{timestamp}", f"TestTitle{timestamp}")

        # 批量处理OCR任务
        processed = process_batch_ocr(batch_size=10)

        # 由于OCR实际处理会失败（测试图片不是真正的图片），所以processed应该为0
        self.assertEqual(processed, 0, "由于测试图片不是真正的图片，OCR处理应该失败")

        # 再次获取所有空文本条目，应该只剩下3条（有图片的条目）
        entries = get_batch_empty_text(batch_size=10)
        self.assertEqual(len(entries), 3, "应该只剩下3条有图片的条目")

def main():
    unittest.main()

if __name__ == "__main__":
    main()
