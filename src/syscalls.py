"""System call facade for StudentOS."""
from __future__ import annotations

from . import fs, scheduler
from .auth import authenticate, check_permission, register_user
from .db import execute_select, init_db
from .kernel import kernel_instance
from .logger import log_syscall


def sys_login(login: str, password: str, current_user: str = "guest") -> bool:
    """Authenticate user and update kernel state."""
    log_syscall("sys_login", login, current_user, "check")
    user = authenticate(login, password)
    if user is None:
        log_syscall("sys_login", login, current_user, "DENIED")
        return False
    kernel_instance.set_user(user["username"], user["role"])
    log_syscall("sys_login", login, user["username"], "OK")
    return True


def sys_register(login: str, password: str, role: str = "user", current_user: str = "admin") -> int | None:
    """Register a new user."""
    log_syscall("sys_register", login, current_user, "check")
    if current_user != "admin":
        log_syscall("sys_register", login, current_user, "DENIED")
        return None
    result = register_user(login, password, role)
    log_syscall("sys_register", login, current_user, "OK" if result else "EXISTS")
    return result


def sys_logout(current_user: str = "guest") -> bool:
    """Logout current user."""
    kernel_instance.logout()
    log_syscall("sys_logout", "", current_user, "OK")
    return True


def sys_whoami(current_user: str = "guest") -> str:
    """Return current user name."""
    log_syscall("sys_whoami", "", current_user, "OK")
    return current_user


def sys_create_file(path: str, content: str, current_user: str = "guest") -> int:
    """Create a file after permission check."""
    log_syscall("sys_create_file", path, current_user, "check")
    if not check_permission(current_user, "create_file"):
        log_syscall("sys_create_file", path, current_user, "DENIED")
        return -1
    result = fs.create_file(path, content, current_user)
    log_syscall("sys_create_file", path, current_user, "OK" if result != -1 else "EXISTS")
    return result


def sys_read_file(path: str, current_user: str = "guest") -> str:
    """Read a file if allowed."""
    log_syscall("sys_read_file", path, current_user, "check")
    owner = fs.get_owner(path)
    if owner is None:
        log_syscall("sys_read_file", path, current_user, "NOT_FOUND")
        return ""
    if not check_permission(current_user, "read_file", owner):
        log_syscall("sys_read_file", path, current_user, "DENIED")
        return ""
    content = fs.read_file(path)
    log_syscall("sys_read_file", path, current_user, "OK")
    return content


def sys_write_file(path: str, content: str, current_user: str = "guest") -> bool:
    """Write a file if allowed."""
    owner = fs.get_owner(path)
    log_syscall("sys_write_file", path, current_user, "check")
    if owner is None:
        log_syscall("sys_write_file", path, current_user, "NOT_FOUND")
        return False
    if not check_permission(current_user, "write_file", owner):
        log_syscall("sys_write_file", path, current_user, "DENIED")
        return False
    result = fs.write_file(path, content)
    log_syscall("sys_write_file", path, current_user, "OK" if result else "ERROR")
    return result


def sys_delete_file(path: str, current_user: str = "guest") -> bool:
    """Delete a file with permission check."""
    owner = fs.get_owner(path)
    log_syscall("sys_delete_file", path, current_user, "check")
    if owner is None:
        log_syscall("sys_delete_file", path, current_user, "NOT_FOUND")
        return False
    if not check_permission(current_user, "delete_file", owner):
        log_syscall("sys_delete_file", path, current_user, "DENIED")
        return False
    result = fs.delete_file(path)
    log_syscall("sys_delete_file", path, current_user, "OK" if result else "ERROR")
    return result


def sys_list_files(path: str = "/", current_user: str = "guest") -> list[dict]:
    """Return files from directory."""
    result = fs.list_files(path)
    log_syscall("sys_list_files", path, current_user, "OK")
    return result


def sys_mkdir(path: str, current_user: str = "guest") -> int:
    """Create a directory."""
    log_syscall("sys_mkdir", path, current_user, "check")
    result = fs.create_directory(path, current_user)
    log_syscall("sys_mkdir", path, current_user, "OK" if result != -1 else "ERROR")
    return result


def sys_rmdir(path: str, current_user: str = "guest") -> bool:
    """Remove a directory recursively."""
    owner = fs.get_owner(path)
    log_syscall("sys_rmdir", path, current_user, "check")
    if owner is None or not check_permission(current_user, "rmdir", owner):
        log_syscall("sys_rmdir", path, current_user, "DENIED")
        return False
    result = fs.delete_directory(path)
    log_syscall("sys_rmdir", path, current_user, "OK" if result else "ERROR")
    return result


def sys_rename_file(old_path: str, new_path: str, current_user: str = "guest") -> bool:
    """Rename a virtual path."""
    owner = fs.get_owner(old_path)
    if owner is None or not check_permission(current_user, "rename", owner):
        log_syscall("sys_rename_file", old_path, current_user, "DENIED")
        return False
    result = fs.rename_file(old_path, new_path)
    log_syscall("sys_rename_file", f"{old_path}->{new_path}", current_user, "OK" if result else "ERROR")
    return result


def sys_copy_file(source: str, destination: str, current_user: str = "guest") -> int:
    """Copy a virtual path."""
    owner = fs.get_owner(source)
    if owner is None or not check_permission(current_user, "copy", owner):
        log_syscall("sys_copy_file", source, current_user, "DENIED")
        return -1
    result = fs.copy_file(source, destination, current_user)
    log_syscall("sys_copy_file", f"{source}->{destination}", current_user, "OK" if result != -1 else "ERROR")
    return result


def sys_move_file(source: str, destination: str, current_user: str = "guest") -> bool:
    """Move a virtual path."""
    owner = fs.get_owner(source)
    if owner is None or not check_permission(current_user, "move", owner):
        log_syscall("sys_move_file", source, current_user, "DENIED")
        return False
    result = fs.move_file(source, destination)
    log_syscall("sys_move_file", f"{source}->{destination}", current_user, "OK" if result else "ERROR")
    return result


def sys_tree(path: str = "/", current_user: str = "guest") -> list[str]:
    """Return tree representation."""
    result = fs.tree(path)
    log_syscall("sys_tree", path, current_user, "OK")
    return result


def sys_exec(name: str, current_user: str = "guest", memory: int = 10) -> int:
    """Start a process."""
    log_syscall("sys_exec", name, current_user, "check")
    if not check_permission(current_user, "run_process"):
        log_syscall("sys_exec", name, current_user, "DENIED")
        return -1
    pid = scheduler.create_process(name, current_user, memory)
    log_syscall("sys_exec", name, current_user, "OK" if pid != -1 else "ERROR")
    return pid


def sys_ps(current_user: str = "guest") -> list[dict]:
    """Return process list."""
    result = scheduler.list_processes()
    log_syscall("sys_ps", "", current_user, "OK")
    return result


def sys_kill(pid: int, current_user: str = "guest") -> bool:
    """Terminate a process with permission check."""
    process = scheduler.get_process(int(pid))
    log_syscall("sys_kill", str(pid), current_user, "check")
    if process is None:
        log_syscall("sys_kill", str(pid), current_user, "NOT_FOUND")
        return False
    if not check_permission(current_user, "kill_process", process["owner"]):
        log_syscall("sys_kill", str(pid), current_user, "DENIED")
        return False
    result = scheduler.terminate_process(int(pid))
    log_syscall("sys_kill", str(pid), current_user, "OK" if result else "ERROR")
    return result


def sys_mem_alloc(size: int, current_user: str = "guest") -> int:
    """Allocate memory directly through kernel."""
    log_syscall("sys_mem_alloc", size, current_user, "check")
    result = kernel_instance.allocate_memory(int(size))
    log_syscall("sys_mem_alloc", size, current_user, "OK" if result else "DENIED")
    return kernel_instance.memory_info()["used"] if result else -1


def sys_mem_info(current_user: str = "guest") -> dict[str, int]:
    """Return current memory info."""
    result = kernel_instance.memory_info()
    log_syscall("sys_mem_info", "", current_user, "OK")
    return result


def sys_logs(limit: int = 20, current_user: str = "guest") -> list[dict]:
    """Return syscall log for admins."""
    if not check_permission(current_user, "view_logs"):
        log_syscall("sys_logs", limit, current_user, "DENIED")
        return []
    rows = execute_select("syscalls_log", order_by="-id", limit=int(limit))
    log_syscall("sys_logs", limit, current_user, "OK")
    return rows


def sys_shutdown(current_user: str = "guest") -> bool:
    """Request OS shutdown."""
    if current_user != "admin":
        log_syscall("sys_shutdown", "", current_user, "DENIED")
        return False
    kernel_instance.shutdown_requested = True
    log_syscall("sys_shutdown", "", current_user, "OK")
    return True


def sys_echo(message: str, current_user: str = "guest") -> str:
    """Return message and log the call."""
    log_syscall("sys_echo", message, current_user, "OK")
    return message


def sys_get_users(current_user: str = "guest") -> list[dict]:
    """Return users for admin."""
    if current_user != "admin":
        log_syscall("sys_get_users", "", current_user, "DENIED")
        return []
    log_syscall("sys_get_users", "", current_user, "OK")
    return execute_select("users", columns=["id", "username", "role", "created_at"], order_by="id")


if __name__ == "__main__":
    init_db()
    print("sys_login:", sys_login("admin", "admin123"))
    print("sys_whoami:", sys_whoami("admin"))
    print("sys_create_file:", sys_create_file("/day_test.txt", "hello", "admin"))
    print("sys_read_file:", sys_read_file("/day_test.txt", "admin"))
    print("sys_exec:", sys_exec("demo", "admin"))
    print("sys_ps:", sys_ps("admin"))

def sys_pwd(path: str = "/", current_user: str = "guest") -> str:
    """Return current virtual directory path."""
    log_syscall("sys_pwd", path, current_user, "OK")
    return path
