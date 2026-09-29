from src.config import MAX_MEMORY_MB
from src.db import get_connection


def get_used_memory() -> int:
    """Возвращает объём памяти работающих процессов."""
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT COALESCE(SUM(memory), 0) AS total
            FROM processes
            WHERE state = 'running'
            """
        ).fetchone()

        return row["total"]
    finally:
        connection.close()


def get_free_memory() -> int:
    """Возвращает свободный объём условной памяти."""
    return MAX_MEMORY_MB - get_used_memory()


def allocate_memory(pid: int, size: int) -> int:
    """Выделяет дополнительную память процессу."""
    if size <= 0:
        raise ValueError("Размер памяти должен быть больше нуля")

    if get_used_memory() + size > MAX_MEMORY_MB:
        raise MemoryError("Недостаточно памяти")

    connection = get_connection()

    try:
        process = connection.execute(
            """
            SELECT memory
            FROM processes
            WHERE id = ? AND state = 'running'
            """,
            (pid,),
        ).fetchone()

        if process is None:
            raise ProcessLookupError("Процесс не найден")

        new_size = process["memory"] + size

        connection.execute(
            """
            UPDATE processes
            SET memory = ?
            WHERE id = ?
            """,
            (new_size, pid),
        )

        connection.commit()
        return new_size
    finally:
        connection.close()