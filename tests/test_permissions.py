"""Автоматическая проверка разграничения прав StudentOS."""

from src.db import get_connection, init_db
from src.fs import create_file
from src.scheduler import create_process
from src.syscalls import sys_delete_file, sys_kill


ADMIN_FILE = "/permission_admin.txt"
USER_FILE = "/permission_user.txt"


def cleanup():
    """Удаляет данные предыдущего запуска тестов."""
    connection = get_connection()

    try:
        connection.execute(
            "DELETE FROM files WHERE path IN (?, ?)",
            (ADMIN_FILE, USER_FILE),
        )

        connection.execute(
            """
            DELETE FROM processes
            WHERE name IN (?, ?)
            """,
            ("guest_kill_test", "admin_kill_test"),
        )

        connection.commit()
    finally:
        connection.close()


def process_state(pid):
    """Возвращает состояние процесса."""
    connection = get_connection()

    try:
        row = connection.execute(
            "SELECT state FROM processes WHERE id = ?",
            (pid,),
        ).fetchone()

        return row["state"] if row is not None else None
    finally:
        connection.close()


def test_guest_cannot_delete_admin_file():
    create_file(ADMIN_FILE, "admin data", "admin")

    result = sys_delete_file(
        ADMIN_FILE,
        current_user="guest",
    )

    assert result is False, "guest не должен удалять файл admin"

    connection = get_connection()

    try:
        row = connection.execute(
            "SELECT id FROM files WHERE path = ?",
            (ADMIN_FILE,),
        ).fetchone()
    finally:
        connection.close()

    assert row is not None, "файл admin был удалён"

    print("[PASS] TC-02: guest не может удалить файл admin")


def test_admin_can_delete_user_file():
    create_file(USER_FILE, "user data", "student")

    result = sys_delete_file(
        USER_FILE,
        current_user="admin",
    )

    assert result is True, "admin должен удалить файл user"

    connection = get_connection()

    try:
        row = connection.execute(
            "SELECT id FROM files WHERE path = ?",
            (USER_FILE,),
        ).fetchone()
    finally:
        connection.close()

    assert row is None, "файл user остался после удаления"

    print("[PASS] admin может удалить файл user")


def test_guest_cannot_kill_process():
    pid = create_process(
        "guest_kill_test",
        owner="admin",
        memory=0,
    )

    result = sys_kill(
        pid,
        current_user="guest",
    )

    assert result is False, "guest не должен завершать процессы"
    assert process_state(pid) == "running", "процесс был завершён"

    print("[PASS] guest не может убить процесс")


def test_admin_can_kill_process():
    pid = create_process(
        "admin_kill_test",
        owner="student",
        memory=0,
    )

    result = sys_kill(
        pid,
        current_user="admin",
    )

    assert result is True, "admin должен завершать процессы"
    assert process_state(pid) == "terminated", "процесс не завершён"

    print("[PASS] admin может убить процесс")


if __name__ == "__main__":
    init_db()
    cleanup()

    try:
        test_guest_cannot_delete_admin_file()
        test_admin_can_delete_user_file()
        test_guest_cannot_kill_process()
        test_admin_can_kill_process()

        print("Все тесты пройдены.")
    finally:
        cleanup()