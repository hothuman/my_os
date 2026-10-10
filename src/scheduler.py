"""Process scheduler for StudentOS."""
from __future__ import annotations

from .config import DEFAULT_PROCESS_MEMORY
from .db import execute_delete, execute_insert, execute_select, now
from .kernel import kernel_instance


def _public(row: dict) -> dict:
    """Convert process DB row to public dict."""
    return {"pid": row["id"], "name": row["name"], "state": row["state"], "owner": row["owner"], "memory_used": row["memory"], "created_at": row["created_at"]}


def create_process(name: str, owner: str, memory: int = DEFAULT_PROCESS_MEMORY) -> int:
    """Create a process and return PID, or -1 if it cannot start."""
    if not name or int(memory) <= 0 or not kernel_instance.check_process_limit():
        return -1
    if not kernel_instance.allocate_memory(int(memory)):
        return -1
    pid = execute_insert("processes", {"name": name, "state": "running", "owner": owner, "memory": int(memory), "created_at": now()})
    if pid is None:
        kernel_instance.free_memory(int(memory))
        return -1
    return int(pid)


def list_processes() -> list[dict]:
    """Return running processes."""
    return [_public(row) for row in execute_select("processes", {"state": "running"}, order_by="id")]


def get_process(pid: int) -> dict | None:
    """Return one process by PID."""
    rows = execute_select("processes", {"id": int(pid)})
    return _public(rows[0]) if rows else None


def terminate_process(pid: int) -> bool:
    """Terminate a process and free its memory."""
    process = get_process(pid)
    if process is None:
        return False
    deleted = execute_delete("processes", {"id": int(pid)}) > 0
    if deleted:
        kernel_instance.free_memory(int(process["memory_used"]))
    return deleted


def schedule_round_robin() -> dict | None:
    """Return the next process in a simplified Round Robin queue."""
    processes = list_processes()
    return processes[0] if processes else None


def schedule_fcfs() -> dict | None:
    """Return the oldest running process."""
    processes = list_processes()
    return processes[0] if processes else None


def process_count() -> int:
    """Return number of running processes."""
    return len(list_processes())


# Compatibility aliases used by earlier practical work.
def get_processes() -> list[dict]:
    """Compatibility alias for list_processes."""
    return list_processes()


def kill_process(pid: int) -> bool:
    """Compatibility alias for terminate_process."""
    return terminate_process(pid)
