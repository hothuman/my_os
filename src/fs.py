"""Hierarchical SQLite-backed file system for StudentOS."""
from __future__ import annotations

import posixpath

from .db import execute_delete, execute_insert, execute_select, execute_update, now


def normalize_path(path: str, cwd: str = "/") -> str:
    """Return normalized absolute virtual path."""
    if not path:
        return cwd or "/"
    base = path if path.startswith("/") else posixpath.join(cwd or "/", path)
    normalized = posixpath.normpath(base)
    return "/" if normalized == "." else normalized


def _name(path: str) -> str:
    """Return basename for virtual path."""
    return "/" if path == "/" else posixpath.basename(path)


def _parent_path(path: str) -> str:
    """Return parent directory path."""
    return "/" if path == "/" else posixpath.dirname(path) or "/"


def _record(path: str) -> dict | None:
    """Return raw file record or None."""
    rows = execute_select("files", {"path": normalize_path(path)})
    return rows[0] if rows else None


def _parent_id(path: str) -> int | None:
    """Return parent id if parent directory exists."""
    parent = _record(_parent_path(path))
    if parent is None or not parent["is_directory"]:
        return None
    return int(parent["id"])


def create_directory(path: str, owner: str) -> int:
    """Create a directory and return id, or -1 on conflict/error."""
    path = normalize_path(path)
    if path == "/" or _record(path) is not None:
        return -1
    parent_id = _parent_id(path)
    if parent_id is None:
        return -1
    return execute_insert("files", {
        "path": path, "name": _name(path), "content": "", "owner": owner,
        "is_directory": 1, "parent_id": parent_id, "created_at": now(), "updated_at": now(),
    }) or -1


def create_file(path: str, content: str, owner: str) -> int:
    """Create a file and return id, or -1 if it cannot be created."""
    path = normalize_path(path)
    if path == "/" or _record(path) is not None:
        return -1
    parent_id = _parent_id(path)
    if parent_id is None:
        return -1
    return execute_insert("files", {
        "path": path, "name": _name(path), "content": content, "owner": owner,
        "is_directory": 0, "parent_id": parent_id, "created_at": now(), "updated_at": now(),
    }) or -1


def read_file(path: str) -> str:
    """Read file content, returning empty string for missing directories/files."""
    row = _record(path)
    if row is None or row["is_directory"]:
        return ""
    return row["content"]


def write_file(path: str, content: str) -> bool:
    """Rewrite file content."""
    row = _record(path)
    if row is None or row["is_directory"]:
        return False
    return execute_update("files", {"content": content, "updated_at": now()}, {"id": row["id"]}) > 0


def delete_file(path: str) -> bool:
    """Delete a non-directory file."""
    row = _record(path)
    if row is None or row["is_directory"]:
        return False
    return execute_delete("files", {"id": row["id"]}) > 0


def delete_directory(path: str) -> bool:
    """Delete a directory recursively except for root."""
    row = _record(path)
    if row is None or not row["is_directory"] or row["path"] == "/":
        return False
    children = execute_select("files", {"parent_id": row["id"]})
    for child in children:
        delete_directory(child["path"]) if child["is_directory"] else delete_file(child["path"])
    return execute_delete("files", {"id": row["id"]}) > 0


def list_files(path: str = "/") -> list[dict]:
    """List direct children of a directory."""
    directory = _record(path)
    if directory is None or not directory["is_directory"]:
        return []
    rows = execute_select("files", {"parent_id": directory["id"]}, order_by="path")
    return [_public(row) for row in rows]


def get_owner(path: str) -> str | None:
    """Return owner of a file or directory."""
    row = _record(path)
    return row["owner"] if row else None


def get_file_info(path: str) -> dict | None:
    """Return public metadata for a path."""
    row = _record(path)
    return _public(row) if row else None


def exists(path: str) -> bool:
    """Return True if path exists."""
    return _record(path) is not None


def is_directory(path: str) -> bool:
    """Return True if path is a directory."""
    row = _record(path)
    return bool(row and row["is_directory"])


def rename_file(old_path: str, new_path: str) -> bool:
    """Rename or move a path and update child paths recursively."""
    old_path, new_path = normalize_path(old_path), normalize_path(new_path)
    row = _record(old_path)
    if row is None or _record(new_path) is not None or _parent_id(new_path) is None:
        return False
    descendants = execute_select("files", order_by="path")
    execute_update("files", {"path": new_path, "name": _name(new_path), "parent_id": _parent_id(new_path), "updated_at": now()}, {"id": row["id"]})
    prefix = old_path.rstrip("/") + "/"
    for child in descendants:
        if child["path"].startswith(prefix):
            new_child_path = new_path.rstrip("/") + child["path"][len(old_path):]
            execute_update("files", {"path": new_child_path, "updated_at": now()}, {"id": child["id"]})
    return True


def copy_file(source: str, destination: str, owner: str) -> int:
    """Copy a file or directory recursively."""
    source, destination = normalize_path(source), normalize_path(destination)
    row = _record(source)
    if row is None or _record(destination) is not None:
        return -1
    if row["is_directory"]:
        new_id = create_directory(destination, owner)
        if new_id == -1:
            return -1
        for child in list_files(source):
            copy_file(child["path"], posixpath.join(destination, child["name"]), owner)
        return new_id
    return create_file(destination, row["content"], owner)


def move_file(source: str, destination: str) -> bool:
    """Move or rename a path."""
    return rename_file(source, destination)


def tree(path: str = "/") -> list[str]:
    """Return formatted tree lines for a directory."""
    path = normalize_path(path)
    row = _record(path)
    if row is None:
        return []
    lines = [_name(path)]
    def walk(parent_path: str, prefix: str = "") -> None:
        children = list_files(parent_path)
        for index, child in enumerate(children):
            last = index == len(children) - 1
            marker = "└── " if last else "├── "
            lines.append(prefix + marker + child["name"] + ("/" if child["is_directory"] else ""))
            if child["is_directory"]:
                walk(child["path"], prefix + ("    " if last else "│   "))
    walk(path)
    return lines


def count_files() -> int:
    """Return number of non-directory files."""
    return len(execute_select("files", {"is_directory": 0}))


def _public(row: dict) -> dict:
    """Convert database row to public metadata dict."""
    return {
        "id": row["id"], "path": row["path"], "name": row.get("name") or _name(row["path"]),
        "owner": row["owner"], "is_directory": bool(row["is_directory"]),
        "created_at": row["created_at"], "updated_at": row.get("updated_at"),
        "content": row.get("content", ""),
    }

# Compatibility aliases used by practice tasks and tests.
def create_dir(path: str, owner: str) -> int:
    """Alias for create_directory."""
    return create_directory(path, owner)


def delete_dir(path: str) -> bool:
    """Alias for delete_directory."""
    return delete_directory(path)
