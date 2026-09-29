from datetime import datetime

from src.db import get_connection


def create_file(path: str, content: str, owner: str) -> int:
    """Создаёт учебный файл и возвращает его id."""
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO files (path, content, owner, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                path,
                content,
                owner,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def read_file(path: str) -> str:
    """Возвращает содержимое файла."""
    connection = get_connection()

    try:
        row = connection.execute(
            "SELECT content FROM files WHERE path = ?",
            (path,),
        ).fetchone()

        if row is None:
            return ""

        return row["content"]
    finally:
        connection.close()


def delete_file(path: str) -> bool:
    """Удаляет файл."""
    connection = get_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM files WHERE path = ?",
            (path,),
        )

        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def list_files(path: str = "/") -> list:
    """Возвращает список файлов."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT id, path, owner, created_at
            FROM files
            ORDER BY id
            """
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        connection.close()