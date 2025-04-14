import sqlite3
from collections import namedtuple
from typing import List

from memococo.config import db_path

Entry = namedtuple("Entry", ["id", "app", "title", "text", "timestamp", "jsontext"])

def get_db_connection():
    conn = sqlite3.connect(db_path)
    # 启用外键约束
    conn.execute("PRAGMA foreign_keys = ON")
    # 设置超时时间，避免数据库锁定问题
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def create_db() -> None:
    with get_db_connection() as conn:
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
        conn.commit()


def get_all_entries(limit: int = 1000, offset: int = 0) -> List[Entry]:
    """获取所有条目，支持分页

    Args:
        limit: 每页条目数，默认1000
        offset: 偏移量，默认0

    Returns:
        条目列表
    """
    with get_db_connection() as conn:
        c = conn.cursor()
        results = c.execute(
            "SELECT * FROM entries ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        return [Entry(*result) for result in results]



def get_timestamps() -> List[int]:
    """获取所有时间戳列表

    根据记忆要求，返回所有时间戳而不使用分页

    Returns:
        所有时间戳列表
    """
    with get_db_connection() as conn:
        c = conn.cursor()
        results = c.execute(
            "SELECT timestamp FROM entries ORDER BY timestamp DESC"
        ).fetchall()
        return [result[0] for result in results]

def get_ocr_text(timestamp: int) -> str:
    with get_db_connection() as conn:
        c = conn.cursor()
        result = c.execute(
            "SELECT text FROM entries WHERE timestamp = ?", (timestamp,)
        ).fetchone()
        return result[0] if result else ""

def get_unique_apps() ->List[str]:
    with get_db_connection() as conn:
        c = conn.cursor()
        results = c.execute(
            "SELECT app, COUNT(*) as count FROM entries GROUP BY app ORDER BY count DESC"
        ).fetchall()
        # 去掉空的内容
        return [result[0] for result in results if result[0]]

def get_newest_empty_text() -> Entry:
    """获取最新的空文本条目

    Returns:
        最新的空文本条目，如果没有则返回None
    """
    with get_db_connection() as conn:
        c = conn.cursor()
        result = c.execute(
            "SELECT * FROM entries WHERE text = '' or text IS NULL ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        return Entry(*result) if result else None

def get_empty_text_count() -> int:
    """获取需要OCR的条目总数

    Returns:
        需要OCR的条目总数
    """
    with get_db_connection() as conn:
        c = conn.cursor()
        result = c.execute(
            "SELECT COUNT(*) FROM entries WHERE text = '' or text IS NULL"
        ).fetchone()
        return result[0] if result else 0

def get_batch_empty_text(batch_size: int = 5, oldest_first: bool = True) -> List[Entry]:
    """批量获取空文本条目

    一次性获取多条空文本条目，提高效率

    Args:
        batch_size: 批处理大小
        oldest_first: 是否按时间升序（从旧到新）排序，默认为True

    Returns:
        空文本条目列表
    """
    with get_db_connection() as conn:
        c = conn.cursor()
        # 根据参数决定排序方式
        order = "ASC" if oldest_first else "DESC"
        results = c.execute(
            f"SELECT * FROM entries WHERE text = '' or text IS NULL ORDER BY timestamp {order} LIMIT ?",
            (batch_size,)
        ).fetchall()
        return [Entry(*result) for result in results]

def get_empty_text_timestamp_range() -> tuple:
    """获取未OCR条目的时间戳范围

    Returns:
        (最早时间戳, 最新时间戳)的元组，如果没有未OCR条目则返回(None, None)
    """
    with get_db_connection() as conn:
        c = conn.cursor()
        # 获取最早的未OCR条目时间戳
        min_result = c.execute(
            "SELECT MIN(timestamp) FROM entries WHERE text = '' or text IS NULL"
        ).fetchone()

        # 获取最新的未OCR条目时间戳
        max_result = c.execute(
            "SELECT MAX(timestamp) FROM entries WHERE text = '' or text IS NULL"
        ).fetchone()

        min_timestamp = min_result[0] if min_result and min_result[0] is not None else None
        max_timestamp = max_result[0] if max_result and max_result[0] is not None else None

        return (min_timestamp, max_timestamp)

def get_empty_text_in_range(start_timestamp: int, end_timestamp: int, limit: int = 10) -> List[Entry]:
    """获取指定时间范围内的未OCR条目

    Args:
        start_timestamp: 开始时间戳
        end_timestamp: 结束时间戳
        limit: 最大返回条目数

    Returns:
        指定时间范围内的未OCR条目列表，按时间戳升序排序
    """
    with get_db_connection() as conn:
        c = conn.cursor()
        results = c.execute(
            "SELECT * FROM entries WHERE (text = '' or text IS NULL) AND timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC LIMIT ?",
            (start_timestamp, end_timestamp, limit)
        ).fetchall()
        return [Entry(*result) for result in results]

def update_entry_text(entry_id: int, text: str, jsontext: str) -> None:
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE entries SET text = ?, jsontext = ? WHERE id = ?",
                (text, jsontext, entry_id),
            )
            conn.commit()
    except sqlite3.OperationalError as e:
        print("Error updating entry:", e)

def remove_entry(entry_id: int) -> None:
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
            conn.commit()
    except sqlite3.OperationalError as e:
        print("Error removing entry:", e)


def insert_entry(
    jsontext: str, timestamp: int, text: str, app: str, title: str
) -> None:
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO entries (jsontext, timestamp, text, app, title) VALUES (?, ?, ?, ?, ?)",
                (jsontext, timestamp, text, app, title),
            )
            conn.commit()
    except sqlite3.OperationalError as e:
        print("Error inserting entry:", e)


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
    with get_db_connection() as conn:
        c = conn.cursor()

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

        results = c.execute(query, params).fetchall()
        return [Entry(*result) for result in results]


# 注意：数据清理功能已移除，以确保数据持久保存
