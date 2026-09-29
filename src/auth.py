import hashlib

from src.db import get_connection


def hash_password(password: str) -> str:
    """Возвращает SHA-256 хэш пароля."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def authenticate(login: str, password: str):
    """Проверяет логин и пароль пользователя."""
    password_hash = hash_password(password)

    connection = get_connection()
    try:
        user = connection.execute(
            """
            SELECT id, username, role, password_hash
            FROM users
            WHERE username = ?
            """,
            (login,),
        ).fetchone()

        if user is None:
            return None

        if user["password_hash"] != password_hash:
            return None

        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        }
    finally:
        connection.close()