"""
数据库连接管理模块

提供数据库连接管理功能，支持连接池和事务管理
"""

import sqlite3
import threading
from typing import Dict, Any, Optional, List, Tuple

class DatabaseManager:
    """数据库管理类"""

    # 线程本地存储，用于存储每个线程的数据库连接
    _local = threading.local()

    # 数据库连接池
    _connections = {}

    # 数据库连接锁
    _lock = threading.Lock()

    @classmethod
    def initialize(cls, db_path: str, max_connections: int = 5) -> None:
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
            max_connections: 最大连接数
        """
        cls.db_path = db_path
        cls.max_connections = max_connections

        # 初始化连接池
        with cls._lock:
            for i in range(max_connections):
                conn = sqlite3.connect(db_path)
                # 启用外键约束
                conn.execute("PRAGMA foreign_keys = ON")
                # 设置超时时间，避免数据库锁定问题
                conn.execute("PRAGMA busy_timeout = 5000")
                # 设置行工厂，返回字典
                conn.row_factory = sqlite3.Row
                cls._connections[i] = {
                    "connection": conn,
                    "in_use": False
                }

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        """获取数据库连接

        Returns:
            sqlite3.Connection: 数据库连接
        """
        # 如果线程本地存储中已有连接，直接返回
        if hasattr(cls._local, 'connection'):
            return cls._local.connection

        # 不使用连接池，而是为每个线程创建新连接
        # 这样可以避免SQLite的线程安全问题
        conn = sqlite3.connect(cls.db_path, check_same_thread=False)
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")
        # 设置超时时间，避免数据库锁定问题
        conn.execute("PRAGMA busy_timeout = 5000")
        # 设置行工厂，返回字典
        conn.row_factory = sqlite3.Row
        cls._local.connection = conn
        cls._local.connection_id = -1  # 标记为临时连接

        return cls._local.connection

    @classmethod
    def release_connection(cls) -> None:
        """释放数据库连接

        注意：为了避免频繁地创建和关闭连接，我们不在每次调用后关闭连接
        而是将连接保存在线程本地存储中，供后续使用
        """
        # 不做任何操作，保持连接打开
        pass

    @classmethod
    def execute(cls, query: str, parameters: Tuple = ()) -> List[Dict[str, Any]]:
        """执行SQL查询

        Args:
            query: SQL查询语句
            parameters: 查询参数

        Returns:
            List[Dict[str, Any]]: 查询结果
        """
        conn = cls.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, parameters)

            # 如果是SELECT查询，返回结果
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                # 如果是其他查询，提交事务并返回空列表
                conn.commit()
                return []
        except Exception as e:
            # 发生异常时回滚事务
            conn.rollback()
            raise e
        finally:
            cls.release_connection()

    @classmethod
    def execute_many(cls, query: str, parameters_list: List[Tuple]) -> None:
        """执行多个SQL查询

        Args:
            query: SQL查询语句
            parameters_list: 查询参数列表
        """
        conn = cls.get_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany(query, parameters_list)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cls.release_connection()

    @classmethod
    def transaction(cls):
        """事务上下文管理器

        用法:
        with DatabaseManager.transaction() as conn:
            conn.execute("INSERT INTO table VALUES (?)", (value,))
            conn.execute("UPDATE table SET column = ? WHERE id = ?", (value, id))
        """
        class Transaction:
            def __enter__(self):
                self.conn = cls.get_connection()
                return self.conn

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    # 如果没有异常，提交事务
                    self.conn.commit()
                else:
                    # 如果有异常，回滚事务
                    self.conn.rollback()

                # 释放连接
                cls.release_connection()

        return Transaction()

    @classmethod
    def close_all(cls) -> None:
        """关闭所有数据库连接"""
        # 关闭连接池中的连接
        with cls._lock:
            for conn_info in cls._connections.values():
                try:
                    conn_info["connection"].close()
                except Exception:
                    pass  # 忽略关闭连接时的错误
            cls._connections.clear()

        # 尝试关闭线程本地存储中的连接
        # 注意：这只会关闭当前线程的连接
        if hasattr(cls._local, 'connection'):
            try:
                cls._local.connection.close()
            except Exception:
                pass  # 忽略关闭连接时的错误
            delattr(cls._local, 'connection')
            if hasattr(cls._local, 'connection_id'):
                delattr(cls._local, 'connection_id')

def initialize_database(db_path: str, max_connections: int = 5) -> None:
    """初始化数据库

    Args:
        db_path: 数据库文件路径
        max_connections: 最大连接数
    """
    DatabaseManager.initialize(db_path, max_connections)
