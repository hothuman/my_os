"""Kernel state and resource management for StudentOS."""
from __future__ import annotations

from .config import MAX_MEMORY_MB, MAX_PROCESSES
from .db import execute_select, execute_update, init_db, now


class Kernel:
    """Central state holder for the educational OS."""

    def __init__(self) -> None:
        """Create kernel with guest user and configured memory limit."""
        self.current_user = {"username": "guest", "role": "guest"}
        self.memory_limit = MAX_MEMORY_MB
        self.memory_used = 0
        self.next_pid = 1
        self.shutdown_requested = False
        init_db()
        self.load_memory_state()

    @property
    def username(self) -> str:
        """Return current username."""
        return self.current_user["username"]

    @property
    def role(self) -> str:
        """Return current role."""
        return self.current_user["role"]

    def set_user(self, username: str, role: str) -> None:
        """Set current user after successful authentication."""
        self.current_user = {"username": username, "role": role}

    def logout(self) -> None:
        """Return the kernel to guest mode."""
        self.current_user = {"username": "guest", "role": "guest"}

    def require_login(self) -> None:
        """Raise PermissionError if current user is guest."""
        if self.username == "guest":
            raise PermissionError("Сначала выполните вход")

    def require_admin(self) -> None:
        """Raise PermissionError if current user is not admin."""
        self.require_login()
        if self.role != "admin":
            raise PermissionError("Требуется роль admin")

    def can_manage_owner(self, owner: str | None) -> bool:
        """Return True if current user can manage an object owner."""
        return self.role == "admin" or (owner is not None and self.username == owner)

    def issue_pid(self) -> int:
        """Return a new PID-like number for external simulations."""
        value = self.next_pid
        self.next_pid += 1
        return value

    def allocate_memory(self, amount_mb: int) -> bool:
        """Try to allocate memory and persist state."""
        amount = int(amount_mb)
        if amount < 0 or self.memory_used + amount > self.memory_limit:
            return False
        self.memory_used += amount
        self.save_memory_state()
        return True

    def free_memory(self, amount_mb: int) -> bool:
        """Free memory and persist state."""
        amount = max(0, int(amount_mb))
        self.memory_used = max(0, self.memory_used - amount)
        self.save_memory_state()
        return True

    def memory_info(self) -> dict[str, int]:
        """Return memory usage information."""
        self.load_memory_state()
        return {
            "used": self.memory_used,
            "free": self.memory_limit - self.memory_used,
            "limit": self.memory_limit,
        }

    def process_count(self) -> int:
        """Return number of running processes."""
        return len(execute_select("processes", {"state": "running"}))

    def check_process_limit(self) -> bool:
        """Return True if a new process can be started."""
        return self.process_count() < MAX_PROCESSES

    def save_memory_state(self) -> None:
        """Persist current memory state to SQLite."""
        execute_update(
            "memory_state",
            {"used": self.memory_used, "limit_mb": self.memory_limit, "updated_at": now()},
            {"id": 1},
        )

    def load_memory_state(self) -> dict[str, int]:
        """Load memory state from SQLite and return it."""
        rows = execute_select("memory_state", {"id": 1})
        if rows:
            self.memory_used = int(rows[0]["used"])
            self.memory_limit = int(rows[0].get("limit_mb", rows[0].get("limit", MAX_MEMORY_MB)))
        return self.memory_info_raw()

    def memory_info_raw(self) -> dict[str, int]:
        """Return memory info without another load call."""
        return {"used": self.memory_used, "free": self.memory_limit - self.memory_used, "limit": self.memory_limit}

    def reset(self) -> None:
        """Reset transient kernel state."""
        self.logout()
        self.memory_used = 0
        self.next_pid = 1
        self.shutdown_requested = False
        self.save_memory_state()


kernel_instance = Kernel()

def _kernel_set_current_user(self, username: str, role: str = "user"):
    """Set current user explicitly for tests and integration helpers."""
    self.current_user = {"username": username, "role": role}
    return self.current_user.copy()

Kernel.set_current_user = _kernel_set_current_user
