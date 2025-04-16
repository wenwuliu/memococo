"""
数据库操作模块

提供数据库操作功能，包括创建、查询、更新和删除操作
"""

import sqlite3
from collections import namedtuple
from typing import List, Optional, Tuple, Dict, Any

from memococo.config import db_path, logger
from memococo.common.db_manager import DatabaseManager
from memococo.common.error_handler import DatabaseError, safe_call

# 初始化数据库连接管理器
DatabaseManager.initialize(db_path)

# 定义数据结构
Entry = namedtuple("Entry", ["id", "app", "title", "text", "timestamp", "jsontext"])

def create_db() -> None:
    """创建数据库表和索引"""
    try:
        with DatabaseManager.transaction() as conn:
            c = conn.cursor()
            # 创建主表
            c.execute(
                """CREATE TABLE IF NOT EXISTS entries
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app TEXT,
                    title TEXT,
                    text TEXT,
                    timestamp INTEGER,
                    jsontext TEXT)"""
            )

            # 添加索引以提高查询性能
            c.execute("CREATE INDEX IF NOT EXISTS idx_entries_timestamp ON entries(timestamp)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_entries_app ON entries(app)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_entries_text ON entries(text)")

            # 执行VACUUM操作优化数据库
            c.execute("VACUUM")
    except Exception as e:
        logger.error(f"创建数据库失败: {e}")
        raise DatabaseError(f"创建数据库失败: {e}")


def get_all_entries(limit: int = 1000, offset: int = 0) -> List[Entry]:
    """获取所有条目，支持分页

    Args:
        limit: 每页条目数，默认1000
        offset: 偏移量，默认0

    Returns:
        条目列表
    """
    try:
        results = DatabaseManager.execute(
            "SELECT * FROM entries ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [Entry(
            result["id"],
            result["app"],
            result["title"],
            result["text"],
            result["timestamp"],
            result["jsontext"]
        ) for result in results]
    except Exception as e:
        logger.error(f"获取条目失败: {e}")
        return []


def get_timestamps() -> List[int]:
    """获取所有时间戳列表

    根据记忆要求，返回所有时间戳而不使用分页

    Returns:
        所有时间戳列表
    """
    try:
        results = DatabaseManager.execute(
            "SELECT timestamp FROM entries ORDER BY timestamp DESC"
        )
        return [result["timestamp"] for result in results]
    except Exception as e:
        logger.error(f"获取时间戳列表失败: {e}")
        return []


def get_ocr_text(timestamp: int) -> str:
    """获取指定时间戳的OCR文本

    Args:
        timestamp: 时间戳

    Returns:
        OCR文本或JSON文本
    """
    try:
        results = DatabaseManager.execute(
            "SELECT text, jsontext FROM entries WHERE timestamp = ?", (timestamp,)
        )
        if not results:
            return ""

        # 优先使用jsontext字段
        if results[0]["jsontext"]:
            return results[0]["jsontext"]
        # 如果jsontext为空，使用text字段
        return results[0]["text"] or ""
    except Exception as e:
        logger.error(f"获取OCR文本失败: {e}")
        return ""


def get_unique_apps() -> List[str]:
    """获取唯一的应用程序列表

    Returns:
        应用程序列表
    """
    try:
        results = DatabaseManager.execute(
            "SELECT app, COUNT(*) as count FROM entries GROUP BY app ORDER BY count DESC"
        )
        # 去掉空的内容
        return [result["app"] for result in results if result["app"]]
    except Exception as e:
        logger.error(f"获取应用程序列表失败: {e}")
        return []


def get_newest_empty_text() -> Optional[Entry]:
    """获取最新的空文本条目

    Returns:
        最新的空文本条目，如果没有则返回None
    """
    try:
        results = DatabaseManager.execute(
            "SELECT * FROM entries WHERE text = '' or text IS NULL ORDER BY timestamp DESC LIMIT 1"
        )
        if not results:
            return None

        result = results[0]
        return Entry(
            result["id"],
            result["app"],
            result["title"],
            result["text"],
            result["timestamp"],
            result["jsontext"]
        )
    except Exception as e:
        logger.error(f"获取最新空文本条目失败: {e}")
        return None


def get_empty_text_count() -> int:
    """获取需要OCR的条目总数

    Returns:
        需要OCR的条目总数
    """
    try:
        results = DatabaseManager.execute(
            "SELECT COUNT(*) as count FROM entries WHERE text = '' or text IS NULL"
        )
        return results[0]["count"] if results else 0
    except Exception as e:
        logger.error(f"获取空文本条目数量失败: {e}")
        return 0


def get_batch_empty_text(batch_size: int = 5, oldest_first: bool = True) -> List[Entry]:
    """批量获取空文本条目

    一次性获取多条空文本条目，提高效率

    Args:
        batch_size: 批处理大小
        oldest_first: 是否按时间升序（从旧到新）排序，默认为True

    Returns:
        空文本条目列表
    """
    try:
        # 根据参数决定排序方式
        order = "ASC" if oldest_first else "DESC"
        results = DatabaseManager.execute(
            f"SELECT * FROM entries WHERE text = '' or text IS NULL ORDER BY timestamp {order} LIMIT ?",
            (batch_size,)
        )
        return [Entry(
            result["id"],
            result["app"],
            result["title"],
            result["text"],
            result["timestamp"],
            result["jsontext"]
        ) for result in results]
    except Exception as e:
        logger.error(f"批量获取空文本条目失败: {e}")
        return []


def get_empty_text_timestamp_range() -> Tuple[Optional[int], Optional[int]]:
    """获取未OCR条目的时间戳范围

    Returns:
        (最早时间戳, 最新时间戳)的元组，如果没有未OCR条目则返回(None, None)
    """
    try:
        # 获取最早的未OCR条目时间戳
        min_results = DatabaseManager.execute(
            "SELECT MIN(timestamp) as min_timestamp FROM entries WHERE text = '' or text IS NULL"
        )
        min_timestamp = min_results[0]["min_timestamp"] if min_results else None

        # 获取最新的未OCR条目时间戳
        max_results = DatabaseManager.execute(
            "SELECT MAX(timestamp) as max_timestamp FROM entries WHERE text = '' or text IS NULL"
        )
        max_timestamp = max_results[0]["max_timestamp"] if max_results else None

        return (min_timestamp, max_timestamp)
    except Exception as e:
        logger.error(f"获取未OCR条目时间戳范围失败: {e}")
        return (None, None)


def get_empty_text_in_range(start_timestamp: int, end_timestamp: int, limit: int = 10) -> List[Entry]:
    """获取指定时间范围内的未OCR条目

    Args:
        start_timestamp: 开始时间戳
        end_timestamp: 结束时间戳
        limit: 最大返回条目数

    Returns:
        指定时间范围内的未OCR条目列表，按时间戳升序排序
    """
    try:
        results = DatabaseManager.execute(
            "SELECT * FROM entries WHERE (text = '' or text IS NULL) AND timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC LIMIT ?",
            (start_timestamp, end_timestamp, limit)
        )
        return [Entry(
            result["id"],
            result["app"],
            result["title"],
            result["text"],
            result["timestamp"],
            result["jsontext"]
        ) for result in results]
    except Exception as e:
        logger.error(f"获取指定时间范围内的未OCR条目失败: {e}")
        return []


def update_entry_text(entry_id: int, text: str, jsontext: str) -> bool:
    """更新条目文本

    Args:
        entry_id: 条目ID
        text: 文本内容
        jsontext: JSON文本

    Returns:
        操作是否成功
    """
    try:
        DatabaseManager.execute(
            "UPDATE entries SET text = ?, jsontext = ? WHERE id = ?",
            (text, jsontext, entry_id)
        )
        return True
    except Exception as e:
        logger.error(f"更新条目文本失败: {e}")
        return False


def remove_entry(entry_id: int) -> bool:
    """删除条目

    Args:
        entry_id: 条目ID

    Returns:
        操作是否成功
    """
    try:
        DatabaseManager.execute(
            "DELETE FROM entries WHERE id = ?",
            (entry_id,)
        )
        return True
    except Exception as e:
        logger.error(f"删除条目失败: {e}")
        return False


def insert_entry(jsontext: str, timestamp: int, text: str, app: str, title: str) -> bool:
    """插入条目

    Args:
        jsontext: JSON文本
        timestamp: 时间戳
        text: 文本内容
        app: 应用程序名称
        title: 标题

    Returns:
        操作是否成功
    """
    try:
        DatabaseManager.execute(
            "INSERT INTO entries (jsontext, timestamp, text, app, title) VALUES (?, ?, ?, ?, ?)",
            (jsontext, timestamp, text, app, title)
        )
        return True
    except Exception as e:
        logger.error(f"插入条目失败: {e}")
        return False


def search_entries(keywords: List[str], app: str = None, limit: int = 100, offset: int = 0) -> List[Entry]:
    """高级搜索功能，支持关键词和应用程序过滤

    Args:
        keywords: 关键词列表
        app: 应用程序名称
        limit: 每页条目数
        offset: 偏移量

    Returns:
        符合条件的条目列表
    """
    try:
        # 构建基本查询
        query = "SELECT * FROM entries WHERE "
        params = []

        # 添加关键词搜索条件
        if keywords:
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append("text LIKE ?")
                params.append(f"%{keyword}%")

            query += "(" + " OR ".join(keyword_conditions) + ")"
        else:
            query += "1=1"  # 如果没有关键词，则选择所有条目

        # 添加应用程序过滤
        if app:
            query += " AND app = ?"
            params.append(app)

        # 添加排序和分页
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        results = DatabaseManager.execute(query, tuple(params))
        return [Entry(
            result["id"],
            result["app"],
            result["title"],
            result["text"],
            result["timestamp"],
            result["jsontext"]
        ) for result in results]
    except Exception as e:
        logger.error(f"搜索条目失败: {e}")
        return []


def close_db_connections():
    """关闭所有数据库连接"""
    try:
        DatabaseManager.close_all()
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")


# 注意：数据清理功能已移除，以确保数据持久保存
