import os

from src.db import init_db
from src.syscalls import (
    sys_create_file,
    sys_delete_file,
    sys_echo,
    sys_exec,
    sys_get_users,
    sys_kill,
    sys_list_files,
    sys_login,
    sys_logout,
    sys_logs,
    sys_mem_alloc,
    sys_ps,
    sys_read_file,
    sys_shutdown,
    sys_whoami,
)


HELP_TEXT = """
Доступные команды:

  help       показать список команд
  whoami     показать текущего пользователя
  login      войти в систему
  logout     выйти из учётной записи

  create     создать учебный файл
  ls         показать список файлов
  cat        прочитать учебный файл
  delete     удалить учебный файл

  run        запустить учебный процесс
  ps         показать процессы
  kill       завершить процесс
  mem        выделить условную память

  echo       вывести текст
  users      показать пользователей
  logs       показать журнал системных вызовов

  clear      очистить экран
  shutdown   завершить StudentOS
  exit       выйти из оболочки
""".strip()


def print_banner():
    print("=" * 46)
    print(" StudentOS — учебная операционная система")
    print(" Python + SQLite")
    print("=" * 46)
    print("Введите help для списка команд.")


def print_files(files):
    if not files:
        print("Файлов пока нет.")
        return

    print(f"{'ID':<5} {'PATH':<25} {'OWNER':<12}")

    for item in files:
        print(
            f"{item['id']:<5} "
            f"{item['path']:<25} "
            f"{item['owner']:<12}"
        )


def print_processes(processes):
    if not processes:
        print("Процессов пока нет.")
        return

    for process in processes:
        print(process)


def print_logs(logs):
    if not logs:
        print("Журнал пуст.")
        return

    for item in reversed(logs):
        print(
            f"#{item['id']} | "
            f"{item['username']} | "
            f"{item['syscall_name']} | "
            f"{item['status']} | "
            f"{item['created_at']}"
        )


def main():
    init_db()

    current_user = "guest"

    print_banner()

    while True:
        try:
            command = input(f"{current_user}@studentos> ").strip().lower()

            if not command:
                continue

            if command == "help":
                print(HELP_TEXT)

            elif command == "whoami":
                print(sys_whoami(current_user))

            elif command == "login":
                login = input("Логин: ").strip()
                password = input("Пароль: ").strip()

                if sys_login(login, password, current_user):
                    current_user = login
                    print("Вход выполнен")
                    print(f"Вы вошли как {current_user}")
                else:
                    print("Неверный логин или пароль")

            elif command == "logout":
                sys_logout(current_user)
                current_user = "guest"
                print("Выход выполнен")

            elif command == "create":
                path = input("Путь: ").strip()
                content = input("Содержимое: ")

                file_id = sys_create_file(
                    path,
                    content,
                    current_user,
                )

                print(f"Создан файл с id={file_id}")

            elif command == "ls":
                files = sys_list_files("/", current_user)
                print_files(files)

            elif command == "cat":
                path = input("Путь: ").strip()
                content = sys_read_file(path, current_user)
                print(content)

            elif command == "delete":
                path = input("Путь: ").strip()

                if sys_delete_file(path, current_user):
                    print("Файл удалён")
                else:
                    print("Не удалось удалить файл")

            elif command == "run":
                name = input("Имя процесса: ").strip()
                pid = sys_exec(name, current_user)
                print(f"Процесс запущен. PID={pid}")

            elif command == "ps":
                processes = sys_ps(current_user)
                print_processes(processes)

            elif command == "kill":
                pid = int(input("PID: "))

                if sys_kill(pid, current_user):
                    print("Процесс завершён")
                else:
                    print("Не удалось завершить процесс")

            elif command == "mem":
                size = int(input("Размер памяти: "))
                result = sys_mem_alloc(size, current_user)
                print(f"Выделено памяти: {result} МБ")

            elif command == "echo":
                message = input("Текст: ")
                print(sys_echo(message, current_user))

            elif command == "users":
                users = sys_get_users(current_user)

                for user in users:
                    print(
                        f"{user['id']} | "
                        f"{user['username']} | "
                        f"{user['role']}"
                    )

            elif command == "logs":
                limit_text = input(
                    "Количество записей [20]: "
                ).strip()

                limit = int(limit_text) if limit_text else 20

                logs = sys_logs(limit, current_user)
                print_logs(logs)

            elif command == "clear":
                os.system("cls" if os.name == "nt" else "clear")

            elif command == "shutdown":
                if sys_shutdown(current_user):
                    print("StudentOS завершает работу")
                    break

            elif command == "exit":
                print("Выход из оболочки.")
                break

            else:
                print(
                    "Неизвестная команда. "
                    "Введите help для списка команд."
                )

        except ValueError:
            print("Ошибка: введено неверное числовое значение.")

        except Exception as error:
            print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()