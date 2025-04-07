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
    with get_db_connection() as conn:
        c = conn.cursor()
        result = c.execute(
            "SELECT * FROM entries WHERE text = '' ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        return Entry(*result) if result else None

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
