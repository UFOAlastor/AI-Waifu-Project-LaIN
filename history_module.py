# history_module.py

import sqlite3
from typing import List, Dict
import logging
from time_module import DateTime
from logging_config import gcww

logger = logging.getLogger("history_module")


class DialogueHistory:
    """对话历史记录管理类 (线程安全简化版)"""

    def __init__(self, main_settings):
        self.db_path = gcww(main_settings, "history_db_path", "./history.db", logger)
        self.max_history = gcww(main_settings, "history_max_num", 200, logger)
        self.formatted_dt = DateTime()

        # 初始化数据库（仅执行一次）
        with self._get_conn() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS dialogue_history
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          role TEXT NOT NULL,
                          user_name TEXT NOT NULL,
                          content TEXT NOT NULL,
                          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"""
            )

    def _get_conn(self):
        """获取新数据库连接"""
        return sqlite3.connect(
            self.db_path,
            check_same_thread=False,  # 允许跨线程使用
            isolation_level=None,  # 关闭自动提交
        )

    def add_record(self, role: str, user_name: str, content: str):
        """添加新记录（使用独立连接）"""
        try:
            with self._get_conn() as conn:  # 自动管理连接
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO dialogue_history
                               (role, user_name, content)
                               VALUES (?, ?, ?)""",
                    (role, user_name, content),
                )

                # 清理旧记录（保持原子性）
                if self.max_history > 0:
                    cursor.execute(
                        """DELETE FROM dialogue_history
                                   WHERE id <=
                                   (SELECT id FROM dialogue_history
                                    ORDER BY id DESC LIMIT 1 OFFSET ?)""",
                        (self.max_history,),
                    )
                conn.commit()  # 显式提交
        except sqlite3.Error as e:
            logger.error(f"数据库操作失败: {str(e)}")

    def get_records(self, limit: int = 0) -> List[Dict]:
        """获取历史记录（使用独立连接）"""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                query = """SELECT id, role, user_name, content, timestamp
                           FROM dialogue_history ORDER BY id DESC"""
                if limit > 0:
                    query += f" LIMIT {limit}"
                cursor.execute(query)
                return [
                    dict(zip(["id", "role", "user_name", "content", "timestamp"], row))
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            logger.error(f"查询失败: {str(e)}")
            return []

    def update_record(self, record_id: int, new_content: str) -> bool:
        """更新记录内容"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """UPDATE dialogue_history
                            SET content = ?
                            WHERE id = ?""",
                (new_content, record_id),
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"更新失败: {str(e)}")
            self.conn.rollback()
            return False

    def delete_record(self, record_id: int) -> bool:
        """删除指定记录"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """DELETE FROM dialogue_history
                            WHERE id = ?""",
                (record_id,),
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"删除失败: {str(e)}")
            self.conn.rollback()
            return False

    def clear_history(self):
        """清空所有历史记录"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""DELETE FROM dialogue_history""")
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"清空失败: {str(e)}")
            self.conn.rollback()

    def load_history_to_messages(self) -> List[Dict]:
        """加载格式化历史记录"""
        records = self.get_records()
        return [
            {
                "role": r["role"],
                "content": f"[Speaker: {r['user_name']}]\n\n\n"
                + f"[当前时间: {r['timestamp']}]\n\n\n"
                + r["content"],
            }
            for r in reversed(records)
        ]

    def close(self):
        """不再需要手动关闭连接"""
        pass  # 连接由with语句自动管理
