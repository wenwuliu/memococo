import sqlite3
from collections import namedtuple
from typing import Any, List

from memococo.config import db_path

Entry = namedtuple("Entry", ["id", "app", "title", "text", "timestamp", "jsontext"])

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
