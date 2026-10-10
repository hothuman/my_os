"""SQLite data layer for StudentOS.

All modules work with SQLite through this file. It provides a connection
factory, database initialization and small CRUD helpers.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .config import (
        DB_DIR, DB_PATH, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME,
        DEFAULT_STUDENT_PASSWORD, DEFAULT_STUDENT_USERNAME, MAX_MEMORY_MB,
    )
except ImportError:
    from config import (  # type: ignore
        DB_DIR, DB_PATH, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME,
        DEFAULT_STUDENT_PASSWORD, DEFAULT_STUDENT_USERNAME, MAX_MEMORY_MB,
    )

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

class ManagedConnection(sqlite3.Connection):
    """SQLite connection that always closes after a with block."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def _check_identifier(name: str) -> str:
    """Validate a table or column name used in generated SQL."""
    if not _IDENTIFIER.match(name):
        raise ValueError(f"Unsafe SQL identifier: {name!r}")
    return name


def now() -> str:
    """Return current timestamp in ISO format without microseconds."""
    return datetime.now().isoformat(timespec="seconds")


def get_connection() -> sqlite3.Connection:
    """Return an auto-closing SQLite connection."""
    DB_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DB_PATH,
        timeout=5,
        factory=ManagedConnection,
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def _sha256(text: str) -> str:
    """Return SHA-256 hash for internal seed users."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    """Return existing columns for a table."""
    rows = connection.execute(f"PRAGMA table_info({_check_identifier(table)})").fetchall()
    return {row["name"] for row in rows}


def _ensure_column(connection: sqlite3.Connection, table: str, name: str, sql: str) -> None:
    """Add a column to an existing table if it is absent."""
    if name not in _table_columns(connection, table):
        connection.execute(f"ALTER TABLE {_check_identifier(table)} ADD COLUMN {sql}")


def _create_schema(connection: sqlite3.Connection) -> None:
    """Create all tables required by the educational OS."""
    c = connection.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            name TEXT PRIMARY KEY,
            description TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE,
            name TEXT,
            content TEXT NOT NULL DEFAULT '',
            owner TEXT NOT NULL,
            is_directory INTEGER NOT NULL DEFAULT 0,
            parent_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY(parent_id) REFERENCES files(id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            state TEXT NOT NULL,
            owner TEXT NOT NULL,
            memory INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS memory_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            used INTEGER NOT NULL DEFAULT 0,
            limit_mb INTEGER NOT NULL DEFAULT 1024,
            updated_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS syscalls_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            syscall_name TEXT NOT NULL,
            arguments TEXT NOT NULL,
            username TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    # Lightweight migrations for earlier course versions.
    _ensure_column(connection, "files", "name", "name TEXT")
    _ensure_column(connection, "files", "is_directory", "is_directory INTEGER NOT NULL DEFAULT 0")
    _ensure_column(connection, "files", "parent_id", "parent_id INTEGER")
    _ensure_column(connection, "files", "updated_at", "updated_at TEXT")


def _seed_data(connection: sqlite3.Connection) -> None:
    """Insert default roles, users, root directory and memory state."""
    roles = {
        "admin": "Administrator with full access",
        "user": "Regular user with access to own objects",
        "guest": "Unauthenticated guest",
    }
    for name, description in roles.items():
        connection.execute(
            "INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)",
            (name, description),
        )
    users = [
        (DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, "admin"),
        (DEFAULT_STUDENT_USERNAME, DEFAULT_STUDENT_PASSWORD, "user"),
        ("user", "user1234", "user"),
    ]
    for username, password, role in users:
        connection.execute(
            """
            INSERT OR IGNORE INTO users (username, password_hash, role, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, _sha256(password), role, now()),
        )
    connection.execute(
        """
        INSERT OR IGNORE INTO files
        (id, path, name, content, owner, is_directory, parent_id, created_at, updated_at)
        VALUES (1, '/', '/', '', 'admin', 1, NULL, ?, ?)
        """,
        (now(), now()),
    )
    connection.execute(
        """
        INSERT OR REPLACE INTO memory_state (id, used, limit_mb, updated_at)
        VALUES (1, COALESCE((SELECT SUM(memory) FROM processes WHERE state = 'running'), 0), ?, ?)
        """,
        (MAX_MEMORY_MB, now()),
    )


def init_db() -> None:
    """Create or update the SQLite database. Repeated calls are safe."""
    with get_connection() as connection:
        _create_schema(connection)
        _seed_data(connection)
        connection.commit()


def reset_db() -> None:
    """Delete the SQLite file and create a fresh database for tests."""
    path = Path(DB_PATH)
    if path.exists():
        path.unlink()
    init_db()


def execute_insert(table: str, data: dict[str, Any]) -> int | None:
    """Insert a record into table and return new row id, or None on conflict."""
    _check_identifier(table)
    if not data:
        raise ValueError("Insert data cannot be empty")
    columns = [_check_identifier(column) for column in data]
    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    try:
        with get_connection() as connection:
            cursor = connection.execute(sql, tuple(data.values()))
            connection.commit()
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError:
        return None


def execute_select(
    table: str,
    filters: dict[str, Any] | None = None,
    columns: list[str] | tuple[str, ...] | str = "*",
    order_by: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Select rows from table and return a list of dictionaries."""
    _check_identifier(table)
    selected = columns if isinstance(columns, str) else ", ".join(_check_identifier(c) for c in columns)
    sql = f"SELECT {selected} FROM {table}"
    params: list[Any] = []
    if filters:
        parts = []
        for key, value in filters.items():
            parts.append(f"{_check_identifier(key)} = ?")
            params.append(value)
        sql += " WHERE " + " AND ".join(parts)
    if order_by:
        direction = "DESC" if order_by.startswith("-") else "ASC"
        key = order_by[1:] if order_by.startswith("-") else order_by
        sql += f" ORDER BY {_check_identifier(key)} {direction}"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))
    with get_connection() as connection:
        return [dict(row) for row in connection.execute(sql, tuple(params)).fetchall()]


def execute_update(table: str, data: dict[str, Any], filters: dict[str, Any]) -> int:
    """Update rows and return affected row count."""
    _check_identifier(table)
    if not data or not filters:
        raise ValueError("Update requires data and filters")
    set_sql = ", ".join(f"{_check_identifier(k)} = ?" for k in data)
    where_sql = " AND ".join(f"{_check_identifier(k)} = ?" for k in filters)
    params = tuple(data.values()) + tuple(filters.values())
    with get_connection() as connection:
        cursor = connection.execute(f"UPDATE {table} SET {set_sql} WHERE {where_sql}", params)
        connection.commit()
        return int(cursor.rowcount)


def execute_delete(table: str, filters: dict[str, Any]) -> int:
    """Delete rows and return affected row count."""
    _check_identifier(table)
    if not filters:
        raise ValueError("Delete requires filters")
    where_sql = " AND ".join(f"{_check_identifier(k)} = ?" for k in filters)
    with get_connection() as connection:
        cursor = connection.execute(f"DELETE FROM {table} WHERE {where_sql}", tuple(filters.values()))
        connection.commit()
        return int(cursor.rowcount)


def execute_query(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]] | int | None:
    """Execute raw SQL for compatibility with earlier practical tasks."""
    try:
        with get_connection() as connection:
            cursor = connection.execute(sql, params)
            if sql.lstrip().upper().startswith("SELECT") or sql.lstrip().upper().startswith("PRAGMA"):
                return [dict(row) for row in cursor.fetchall()]
            connection.commit()
            return int(cursor.lastrowid)
    except (sqlite3.IntegrityError, sqlite3.OperationalError) as error:
        print(f"Ошибка SQLite: {error}")
        return None


if __name__ == "__main__":
    init_db()
    print(f"База данных готова: {DB_PATH}")
