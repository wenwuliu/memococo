import sqlite3
from collections import namedtuple
from typing import Any, List

from memococo.config import db_path

Entry = namedtuple("Entry", ["id", "app", "title", "text", "timestamp", "jsontext","embedding"])

def get_db_connection():
    return sqlite3.connect(db_path)


def create_db() -> None:
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS entries
               (id INTEGER PRIMARY KEY AUTOINCREMENT, app TEXT, title TEXT, text TEXT, timestamp INTEGER, jsontext TEXT)"""
        )
        conn.commit()


def get_all_entries() -> List[Entry]:
    with get_db_connection() as conn:
        c = conn.cursor()
        results = c.execute("SELECT * FROM entries").fetchall()
        return [Entry(*result) for result in results]



def get_timestamps() -> List[int]:
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
            "SELECT jsontext FROM entries WHERE timestamp = ?", (timestamp,)
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
