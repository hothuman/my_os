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
        
def check_permission(current_user: str, action: str, target_owner=None) -> bool:
    """
    Проверяет права пользователя на действие.

    Правила:
    - admin имеет полный доступ;
    - обычный пользователь может удалить только свой файл;
    - guest не может удалять файлы;
    - завершать процессы может только admin;
    - неизвестные действия запрещены.
    """
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT role
            FROM users
            WHERE username = ?
            """,
            (current_user,),
        ).fetchone()
    finally:
        connection.close()

    role = row["role"] if row is not None else "guest"

    # Администратору разрешены все действия.
    if role == "admin":
        return True

    # Обычный пользователь может удалить только собственный файл.
    if action == "delete_file":
        return (
            role == "user"
            and target_owner is not None
            and target_owner == current_user
        )

    # Завершать процессы может только администратор.
    if action == "kill_process":
        return False

    # Неизвестное действие запрещаем.
    return False       