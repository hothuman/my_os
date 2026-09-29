import hashlib
import sqlite3
from datetime import datetime

try:
    from .config import (
        DB_DIR, DB_PATH, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME,
        DEFAULT_STUDENT_PASSWORD, DEFAULT_STUDENT_USERNAME,
    )
except ImportError:  # позволяет запускать: python src/db.py
    from config import (
        DB_DIR, DB_PATH, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME,
        DEFAULT_STUDENT_PASSWORD, DEFAULT_STUDENT_USERNAME,
    )


def get_connection():
    """Возвращает подключение к SQLite с доступом к колонкам по имени."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def init_db():
    """Создаёт таблицы и начального администратора. Повторный запуск безопасен."""
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS processes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                state TEXT NOT NULL,
                owner TEXT NOT NULL,
                memory INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL DEFAULT '',
                owner TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS syscalls_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                syscall_name TEXT NOT NULL,
                arguments TEXT NOT NULL,
                username TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        admin_exists = cursor.execute(
            "SELECT id FROM users WHERE username = ?", (DEFAULT_ADMIN_USERNAME,)
        ).fetchone()

        if admin_exists is None:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    DEFAULT_ADMIN_USERNAME,
                    _sha256(DEFAULT_ADMIN_PASSWORD),
                    "admin",
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )

        student_exists = cursor.execute(
            "SELECT id FROM users WHERE username = ?", (DEFAULT_STUDENT_USERNAME,)
        ).fetchone()
        if student_exists is None:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    DEFAULT_STUDENT_USERNAME,
                    _sha256(DEFAULT_STUDENT_PASSWORD),
                    "user",
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )

        connection.commit()


if __name__ == "__main__":
    init_db()
    print(f"База данных готова: {DB_PATH}")
