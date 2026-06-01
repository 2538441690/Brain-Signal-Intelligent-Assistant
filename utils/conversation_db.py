# utils/conversation_db.py 完整替换如下
import os
import datetime
import pymysql
import bcrypt
from typing import List, Dict, Optional
from utils.logger_handler import logger
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "agent_db")

def get_db_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

def init_db():
    """初始化表结构（在模块加载时自动执行）"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 会话表增加 user_id
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    conv_id VARCHAR(36) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conv_id) REFERENCES conversations(id) ON DELETE CASCADE,
                    INDEX idx_conv_id (conv_id)
                )
            ''')
        conn.commit()
        logger.info("MySQL 表初始化成功")
    except Exception as e:
        logger.error(f"MySQL 初始化失败: {e}")
        raise
    finally:
        conn.close()

init_db()

# ---------- 用户相关 ----------
def create_user(username: str, password: str) -> Optional[int]:
    """创建用户，返回用户ID，失败返回None"""
    conn = get_db_connection()
    try:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, hashed)
            )
            conn.commit()
            return cursor.lastrowid
    except pymysql.IntegrityError:
        return None
    finally:
        conn.close()

def authenticate_user(username: str, password: str) -> Optional[int]:
    """验证用户，返回user_id，失败返回None"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                return user['id']
            return None
    finally:
        conn.close()

# ---------- 会话管理（增加 user_id 参数）----------
def create_conversation(conv_id: str, user_id: int, title: str = "新对话") -> bool:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO conversations (id, user_id, title, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
                (conv_id, user_id, title, datetime.datetime.now(), datetime.datetime.now())
            )
        conn.commit()
        return True
    except pymysql.IntegrityError:
        return False
    finally:
        conn.close()

def get_conversation(conv_id: str, user_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, created_at, updated_at FROM conversations WHERE id = %s AND user_id = %s",
                (conv_id, user_id)
            )
            return cursor.fetchone()
    finally:
        conn.close()

def get_all_conversations(user_id: int) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, created_at, updated_at FROM conversations WHERE user_id = %s ORDER BY updated_at DESC",
                (user_id,)
            )
            return cursor.fetchall()
    finally:
        conn.close()

def delete_conversation(conv_id: str, user_id: int) -> bool:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            affected = cursor.execute(
                "DELETE FROM conversations WHERE id = %s AND user_id = %s",
                (conv_id, user_id)
            )
        conn.commit()
        return affected > 0
    finally:
        conn.close()

def update_conversation_title(conv_id: str, user_id: int, title: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE conversations SET title = %s, updated_at = %s WHERE id = %s AND user_id = %s",
                (title, datetime.datetime.now(), conv_id, user_id)
            )
        conn.commit()
    finally:
        conn.close()

def add_message(conv_id: str, user_id: int, role: str, content: str):
    """注意：这里需要确保 conv_id 属于该 user_id，否则应该失败"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 先验证会话属于用户
            cursor.execute("SELECT id FROM conversations WHERE id = %s AND user_id = %s", (conv_id, user_id))
            if not cursor.fetchone():
                raise PermissionError("会话不属于当前用户")
            cursor.execute(
                "INSERT INTO messages (conv_id, role, content, timestamp) VALUES (%s, %s, %s, %s)",
                (conv_id, role, content, datetime.datetime.now())
            )
            cursor.execute(
                "UPDATE conversations SET updated_at = %s WHERE id = %s",
                (datetime.datetime.now(), conv_id)
            )
        conn.commit()
    finally:
        conn.close()

def get_messages(conv_id: str, user_id: int) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 验证会话属于用户
            cursor.execute("SELECT id FROM conversations WHERE id = %s AND user_id = %s", (conv_id, user_id))
            if not cursor.fetchone():
                return []
            cursor.execute(
                "SELECT role, content, timestamp FROM messages WHERE conv_id = %s ORDER BY timestamp ASC",
                (conv_id,)
            )
            return cursor.fetchall()
    finally:
        conn.close()

def clear_conversation_messages(conv_id: str, user_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM conversations WHERE id = %s AND user_id = %s", (conv_id, user_id))
            if cursor.fetchone():
                cursor.execute("DELETE FROM messages WHERE conv_id = %s", (conv_id,))
        conn.commit()
    finally:
        conn.close()