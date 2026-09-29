from datetime import datetime

from src.db import get_connection
from src.db import init_db
from src.auth import authenticate
from src.fs import create_file, list_files


def log_syscall(name, args="", user="system", status="OK"):
    """Записывает системный вызов в таблицу syscalls_log."""
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO syscalls_log
            (syscall_name, arguments, username, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                str(args),
                user,
                status,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def sys_login(login: str, password: str, current_user="guest") -> bool:
    """Проверяет логин и пароль."""
    user = authenticate(login, password)
    result = user is not None

    log_syscall(
        "sys_login",
        login,
        current_user,
        "OK" if result else "DENIED",
    )

    return result


def sys_logout(current_user="guest") -> bool:
    """Завершает пользовательский сеанс."""
    log_syscall("sys_logout", "", current_user)
    return True


def sys_whoami(current_user="guest") -> str:
    """Возвращает имя текущего пользователя."""
    log_syscall("sys_whoami", "", current_user)
    return current_user


def sys_create_file(path: str, content: str, current_user="guest") -> int:
    """Создаёт учебный файл и возвращает его id."""
    try:
        file_id = create_file(path, content, current_user)
        log_syscall("sys_create_file", path, current_user)
        return file_id

    except Exception as error:
        log_syscall(
            "sys_create_file",
            path,
            current_user,
            f"ERROR: {error}",
        )
        raise


def sys_read_file(path: str, current_user="guest") -> str:
    """
    Учебная заглушка чтения файла.

    По заданию должна возвращать пустую строку.
    """
    log_syscall("sys_read_file", path, current_user)
    return ""


def sys_delete_file(path: str, current_user="guest") -> bool:
    """Учебная заглушка удаления файла."""
    log_syscall("sys_delete_file", path, current_user)
    return True


def sys_list_files(path="/", current_user="guest") -> list:
    """Возвращает список учебных файлов."""
    files = list_files(path)
    log_syscall("sys_list_files", path, current_user)
    return files


def sys_exec(name: str, current_user="guest") -> int:
    """
    Учебная заглушка запуска процесса.

    По заданию возвращает PID 42.
    """
    log_syscall("sys_exec", name, current_user)
    return 42


def sys_ps(current_user="guest") -> list:
    """
    Учебная заглушка списка процессов.

    По заданию возвращает пустой список.
    """
    log_syscall("sys_ps", "", current_user)
    return []


def sys_kill(pid: int, current_user="guest") -> bool:
    """Учебная заглушка завершения процесса."""
    log_syscall("sys_kill", pid, current_user)
    return True


def sys_mem_alloc(size: int, current_user="guest") -> int:
    """Учебная заглушка выделения памяти."""
    log_syscall("sys_mem_alloc", size, current_user)
    return size


def sys_logs(limit: int = 20, current_user="guest") -> list:
    """Возвращает последние записи журнала."""
    log_syscall("sys_logs", limit, current_user)

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                syscall_name,
                arguments,
                username,
                status,
                created_at
            FROM syscalls_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        connection.close()


def sys_shutdown(current_user="guest") -> bool:
    """Учебная заглушка завершения StudentOS."""
    log_syscall("sys_shutdown", "", current_user)
    return True


# Дополнительные вызовы из первого занятия.
# Они оставлены, чтобы не потерять уже реализованные возможности проекта.

def sys_echo(message, current_user="guest"):
    log_syscall("sys_echo", message, current_user)
    return message


def sys_get_users(current_user="guest"):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT id, username, role, created_at
            FROM users
            ORDER BY id
            """
        ).fetchall()

        result = [dict(row) for row in rows]
    finally:
        connection.close()

    log_syscall("sys_get_users", "", current_user)
    return result


if __name__ == "__main__":
    init_db()

    print("Проверка системных вызовов:")
    print("sys_login:", sys_login("admin", "admin123"))
    print("sys_whoami:", sys_whoami("admin"))

    # Для повторного запуска используем отдельный тестовый файл.
    # Если он уже существует, ошибка не останавливает остальные проверки.
    try:
        print(
            "sys_create_file:",
            sys_create_file("/day2_test.txt", "hello", "admin"),
        )
    except Exception as error:
        print("sys_create_file:", error)

    print("sys_ps:", sys_ps("admin"))