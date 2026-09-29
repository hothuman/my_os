from datetime import datetime

from src.db import get_connection


def create_process(name: str, owner: str, memory: int = 0) -> int:
    """Создаёт учебный процесс и возвращает PID."""
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO processes
            (name, state, owner, memory, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                "running",
                owner,
                memory,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def get_processes() -> list:
    """Возвращает список процессов."""
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT id, name, state, owner, memory, created_at
            FROM processes
            ORDER BY id
            """
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        connection.close()


def kill_process(pid: int) -> bool:
    """Помечает процесс как завершённый."""
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE processes
            SET state = 'terminated'
            WHERE id = ?
            """,
            (pid,),
        )

        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()