"""Authentication and authorization helpers for StudentOS."""
from __future__ import annotations

import hashlib

from .db import execute_insert, execute_select, now


def hash_password(password: str) -> str:
    """Return SHA-256 hash of a password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(login: str, password: str, role: str = "user") -> int | None:
    """Register a user and return its id, or None when login is taken."""
    if role not in {"admin", "user", "guest"}:
        role = "user"
    return execute_insert(
        "users",
        {
            "username": login,
            "password_hash": hash_password(password),
            "role": role,
            "created_at": now(),
        },
    )


def authenticate(login: str, password: str) -> dict | None:
    """Return user dict if credentials are correct, otherwise None."""
    rows = execute_select("users", {"username": login})
    if not rows:
        return None
    user = rows[0]
    if user["password_hash"] != hash_password(password):
        return None
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


def get_role(username: str) -> str:
    """Return role for a username or guest for unknown users."""
    rows = execute_select("users", {"username": username}, columns=["role"])
    return rows[0]["role"] if rows else "guest"


def check_permission(current_user: str, action: str, target_owner: str | None = None) -> bool:
    """Check access rights for a protected action."""
    role = get_role(current_user)
    if role == "admin":
        return True
    if role == "guest":
        return action in {"echo", "whoami"}
    if action in {"create_file", "read_file", "write_file", "delete_file", "mkdir", "rmdir", "copy", "move", "rename"}:
        return target_owner in {None, current_user}
    if action == "run_process":
        return True
    if action == "kill_process":
        return target_owner == current_user
    if action == "view_logs":
        return False
    return False
