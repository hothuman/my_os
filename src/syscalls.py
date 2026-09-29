import json
from datetime import datetime

from .config import MAX_MEMORY_MB
from .db import get_connection


def log_syscall(syscall_name, arguments, username, status):
    """Записывает факт системного вызова в таблицу syscalls_log."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO syscalls_log
            (syscall_name, arguments, username, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                syscall_name,
                json.dumps(arguments, ensure_ascii=False, default=str),
                username,
                status,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        connection.commit()


def _username(kernel):
    return kernel.username if kernel is not None else "guest"


def _logged_call(name, kernel, arguments, action):
    username = _username(kernel)
    try:
        result = action()
        log_syscall(name, arguments, username, "OK")
        return result
    except Exception as error:
        log_syscall(name, arguments, username, f"ERROR: {error}")
        raise


def sys_echo(message, kernel=None):
    return _logged_call("sys_echo", kernel, {"message": message}, lambda: message)


def sys_get_users(kernel=None):
    def action():
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id, username, role, created_at FROM users ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    return _logged_call("sys_get_users", kernel, {}, action)


def sys_login(kernel, username, password):
    arguments = {"username": username, "password": "***"}
    try:
        result = kernel.login(username, password)
        log_syscall("sys_login", arguments, username, "OK")
        return result
    except Exception as error:
        log_syscall("sys_login", arguments, username, f"ERROR: {error}")
        raise


def sys_logout(kernel):
    old_username = kernel.username

    def action():
        kernel.logout()
        return old_username

    return _logged_call("sys_logout", kernel, {}, action)


def sys_whoami(kernel):
    return _logged_call(
        "sys_whoami",
        kernel,
        {},
        lambda: {"username": kernel.username, "role": kernel.role},
    )


def sys_create(kernel, path, content=""):
    def action():
        kernel.require_login()
        with get_connection() as connection:
            existing = connection.execute(
                "SELECT owner FROM files WHERE path = ?", (path,)
            ).fetchone()
            if existing is not None:
                raise FileExistsError(f"Файл уже существует: {path}")
            connection.execute(
                """
                INSERT INTO files (path, content, owner, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (path, content, kernel.username, datetime.now().isoformat(timespec="seconds")),
            )
            connection.commit()
        return path

    return _logged_call("sys_create", kernel, {"path": path}, action)


def sys_open(kernel, path):
    def action():
        kernel.require_login()
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id, path, owner, created_at FROM files WHERE path = ?", (path,)
            ).fetchone()
        if row is None:
            raise FileNotFoundError(f"Файл не найден: {path}")
        if not kernel.can_manage_owner(row["owner"]):
            raise PermissionError("Нет прав на доступ к этому файлу")
        return dict(row)

    return _logged_call("sys_open", kernel, {"path": path}, action)


def sys_read(kernel, path):
    def action():
        kernel.require_login()
        with get_connection() as connection:
            row = connection.execute(
                "SELECT content, owner FROM files WHERE path = ?", (path,)
            ).fetchone()
        if row is None:
            raise FileNotFoundError(f"Файл не найден: {path}")
        if not kernel.can_manage_owner(row["owner"]):
            raise PermissionError("Нет прав на чтение этого файла")
        return row["content"]

    return _logged_call("sys_read", kernel, {"path": path}, action)


def sys_write(kernel, path, content):
    def action():
        kernel.require_login()
        with get_connection() as connection:
            row = connection.execute(
                "SELECT owner FROM files WHERE path = ?", (path,)
            ).fetchone()
            if row is None:
                raise FileNotFoundError(f"Файл не найден: {path}")
            if not kernel.can_manage_owner(row["owner"]):
                raise PermissionError("Нет прав на изменение этого файла")
            connection.execute(
                "UPDATE files SET content = ? WHERE path = ?", (content, path)
            )
            connection.commit()
        return path

    return _logged_call("sys_write", kernel, {"path": path}, action)


def sys_exec(kernel, name, memory=16):
    def action():
        kernel.require_login()
        memory_mb = int(memory)
        if memory_mb <= 0:
            raise ValueError("Память процесса должна быть больше 0 МБ")
        kernel.check_process_limit()
        kernel.check_memory(memory_mb)
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO processes (name, state, owner, memory, created_at)
                VALUES (?, 'running', ?, ?, ?)
                """,
                (name, kernel.username, memory_mb, datetime.now().isoformat(timespec="seconds")),
            )
            connection.commit()
            return cursor.lastrowid

    return _logged_call("sys_exec", kernel, {"name": name, "memory": memory}, action)


def sys_ps(kernel):
    def action():
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, name, state, owner, memory, created_at
                FROM processes ORDER BY id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    return _logged_call("sys_ps", kernel, {}, action)


def sys_kill(kernel, process_id):
    def action():
        kernel.require_login()
        pid = int(process_id)
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id, owner, state FROM processes WHERE id = ?", (pid,)
            ).fetchone()
            if row is None:
                raise ProcessLookupError(f"Процесс {pid} не найден")
            if not kernel.can_manage_owner(row["owner"]):
                raise PermissionError("Нет прав на завершение этого процесса")
            if row["state"] != "running":
                raise RuntimeError(f"Процесс {pid} уже завершён")
            connection.execute(
                "UPDATE processes SET state = 'terminated' WHERE id = ?", (pid,)
            )
            connection.commit()
        return pid

    return _logged_call("sys_kill", kernel, {"process_id": process_id}, action)


def sys_alloc(kernel, process_id, amount_mb):
    def action():
        kernel.require_login()
        pid = int(process_id)
        amount = int(amount_mb)
        if amount <= 0:
            raise ValueError("Нужно указать положительный объём памяти")
        with get_connection() as connection:
            row = connection.execute(
                "SELECT owner, state, memory FROM processes WHERE id = ?", (pid,)
            ).fetchone()
            if row is None:
                raise ProcessLookupError(f"Процесс {pid} не найден")
            if row["state"] != "running":
                raise RuntimeError("Нельзя выделить память завершённому процессу")
            if not kernel.can_manage_owner(row["owner"]):
                raise PermissionError("Нет прав на изменение памяти этого процесса")
            kernel.check_memory(amount)
            new_memory = row["memory"] + amount
            connection.execute(
                "UPDATE processes SET memory = ? WHERE id = ?", (new_memory, pid)
            )
            connection.commit()
        return new_memory

    return _logged_call(
        "sys_alloc",
        kernel,
        {"process_id": process_id, "amount_mb": amount_mb},
        action,
    )


def sys_mem(kernel):
    def action():
        used = kernel.memory_used()
        return {"used": used, "free": MAX_MEMORY_MB - used, "total": MAX_MEMORY_MB}

    return _logged_call("sys_mem", kernel, {}, action)


def sys_logs(kernel, limit=20):
    def action():
        kernel.require_admin()
        count = max(1, min(int(limit), 100))
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, syscall_name, arguments, username, status, created_at
                FROM syscalls_log ORDER BY id DESC LIMIT ?
                """,
                (count,),
            ).fetchall()
        return [dict(row) for row in rows]

    return _logged_call("sys_logs", kernel, {"limit": limit}, action)


def sys_shutdown(kernel):
    def action():
        kernel.require_admin()
        kernel.shutdown_requested = True
        return "StudentOS завершает работу"

    return _logged_call("sys_shutdown", kernel, {}, action)
