"""Central syscall logging module."""
from __future__ import annotations

from .db import execute_insert, now


def log_syscall(name: str, args: str = "", user: str = "system", status: str = "OK") -> None:
    """Write a syscall event to syscalls_log."""
    execute_insert(
        "syscalls_log",
        {
            "syscall_name": name,
            "arguments": str(args),
            "username": user,
            "status": status,
            "created_at": now(),
        },
    )
