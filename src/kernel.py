import hashlib

from .config import MAX_MEMORY_MB, MAX_PROCESSES
from .db import get_connection


class Kernel:
    """Простая учебная модель ядра StudentOS."""

    def __init__(self):
        self.current_user = {"username": "guest", "role": "guest"}
        self.shutdown_requested = False

    @property
    def username(self):
        return self.current_user["username"]

    @property
    def role(self):
        return self.current_user["role"]

    def login(self, username, password):
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        with get_connection() as connection:
            row = connection.execute(
                "SELECT username, role, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if row is None or row["password_hash"] != password_hash:
            raise ValueError("Неверное имя пользователя или пароль")

        self.current_user = {"username": row["username"], "role": row["role"]}
        return self.current_user.copy()

    def logout(self):
        self.current_user = {"username": "guest", "role": "guest"}

    def require_login(self):
        if self.username == "guest":
            raise PermissionError("Сначала выполните вход: login <логин> <пароль>")

    def require_admin(self):
        self.require_login()
        if self.role != "admin":
            raise PermissionError("Эта операция доступна только администратору")

    def can_manage_owner(self, owner):
        return self.role == "admin" or self.username == owner

    def process_count(self):
        with get_connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM processes WHERE state = 'running'"
            ).fetchone()
        return row["count"]

    def memory_used(self):
        with get_connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(memory), 0) AS total FROM processes WHERE state = 'running'"
            ).fetchone()
        return row["total"]

    def check_process_limit(self):
        if self.process_count() >= MAX_PROCESSES:
            raise RuntimeError(f"Достигнут лимит процессов: {MAX_PROCESSES}")

    def check_memory(self, additional_mb):
        if additional_mb < 0:
            raise ValueError("Объём памяти не может быть отрицательным")
        if self.memory_used() + additional_mb > MAX_MEMORY_MB:
            raise MemoryError(
                f"Недостаточно условной памяти. Лимит: {MAX_MEMORY_MB} МБ"
            )
