import os
import shlex

from .config import OS_NAME, OS_VERSION
from .db import init_db
from .kernel import Kernel
from .syscalls import (
    sys_alloc,
    sys_create,
    sys_echo,
    sys_exec,
    sys_get_users,
    sys_kill,
    sys_login,
    sys_logout,
    sys_logs,
    sys_mem,
    sys_ps,
    sys_read,
    sys_shutdown,
    sys_whoami,
    sys_write,
)


HELP_TEXT = """
Доступные команды:
  help                         показать справку
  echo <текст>                 вывести текст
  users                        показать пользователей
  login <логин> <пароль>       войти в систему
  logout                       выйти из учётной записи
  whoami                       показать текущего пользователя
  touch <путь> [текст]         создать учебный файл
  cat <путь>                   прочитать учебный файл
  write <путь> <текст>         изменить учебный файл
  run <имя> [память_МБ]        запустить учебный процесс
  ps                           показать процессы
  kill <pid>                   завершить процесс
  mem [pid] [МБ]               показать память или выделить память процессу
  logs [количество]            журнал системных вызовов (admin)
  clear                        очистить экран
  shutdown                     завершить StudentOS (admin)
  exit                         выйти из оболочки
""".strip()


def print_banner():
    print("=" * 46)
    print(f" {OS_NAME} {OS_VERSION} — учебная модель ОС")
    print(" Python + SQLite | монолитная архитектура")
    print("=" * 46)
    print("Введите help для списка команд.")


def _print_users(users):
    print(f"{'ID':<4} {'USERNAME':<16} {'ROLE':<10} CREATED")
    for user in users:
        print(f"{user['id']:<4} {user['username']:<16} {user['role']:<10} {user['created_at']}")


def _print_processes(processes):
    if not processes:
        print("Процессов пока нет.")
        return
    print(f"{'PID':<5} {'NAME':<18} {'STATE':<12} {'OWNER':<12} {'MEM':>5}")
    for process in processes:
        print(
            f"{process['id']:<5} {process['name']:<18} {process['state']:<12} "
            f"{process['owner']:<12} {process['memory']:>4}M"
        )


def _print_logs(logs):
    for item in reversed(logs):
        print(
            f"#{item['id']} {item['created_at']} | {item['username']} | "
            f"{item['syscall_name']} | {item['status']} | {item['arguments']}"
        )


def handle_command(kernel, line):
    parts = shlex.split(line)
    if not parts:
        return True

    command = parts[0].lower()
    args = parts[1:]

    if command == "help":
        print(HELP_TEXT)
    elif command == "echo":
        print(sys_echo(" ".join(args), kernel))
    elif command == "users":
        _print_users(sys_get_users(kernel))
    elif command == "login":
        if len(args) != 2:
            print("Использование: login <логин> <пароль>")
        else:
            user = sys_login(kernel, args[0], args[1])
            print(f"Вход выполнен: {user['username']} ({user['role']})")
    elif command == "logout":
        old_user = sys_logout(kernel)
        print(f"Пользователь {old_user} вышел из системы.")
    elif command == "whoami":
        user = sys_whoami(kernel)
        print(f"{user['username']} ({user['role']})")
    elif command == "touch":
        if not args:
            print("Использование: touch <путь> [текст]")
        else:
            content = " ".join(args[1:]) if len(args) > 1 else ""
            print(f"Создан файл: {sys_create(kernel, args[0], content)}")
    elif command == "cat":
        if len(args) != 1:
            print("Использование: cat <путь>")
        else:
            print(sys_read(kernel, args[0]))
    elif command == "write":
        if len(args) < 2:
            print("Использование: write <путь> <текст>")
        else:
            sys_write(kernel, args[0], " ".join(args[1:]))
            print(f"Файл изменён: {args[0]}")
    elif command == "run":
        if not args:
            print("Использование: run <имя> [память_МБ]")
        else:
            memory = args[1] if len(args) > 1 else 16
            pid = sys_exec(kernel, args[0], memory)
            print(f"Процесс запущен. PID={pid}")
    elif command == "ps":
        _print_processes(sys_ps(kernel))
    elif command == "kill":
        if len(args) != 1:
            print("Использование: kill <pid>")
        else:
            print(f"Процесс {sys_kill(kernel, args[0])} завершён.")
    elif command == "mem":
        if not args:
            info = sys_mem(kernel)
            print(f"Память: {info['used']} МБ занято, {info['free']} МБ свободно, всего {info['total']} МБ")
        elif len(args) == 2:
            new_memory = sys_alloc(kernel, args[0], args[1])
            print(f"Теперь процесс использует {new_memory} МБ.")
        else:
            print("Использование: mem ИЛИ mem <pid> <МБ>")
    elif command == "logs":
        limit = args[0] if args else 20
        _print_logs(sys_logs(kernel, limit))
    elif command == "clear":
        os.system("cls" if os.name == "nt" else "clear")
    elif command == "shutdown":
        print(sys_shutdown(kernel))
        return False
    elif command == "exit":
        print("Выход из оболочки.")
        return False
    else:
        print(f"Неизвестная команда: {command}. Введите help.")

    return True


def main():
    init_db()
    kernel = Kernel()
    print_banner()

    running = True
    while running and not kernel.shutdown_requested:
        try:
            line = input(f"{kernel.username}@studentos> ")
            running = handle_command(kernel, line)
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из оболочки.")
            break
        except Exception as error:
            print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()
