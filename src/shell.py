import os
import shlex

from src.config import OS_NAME, OS_VERSION
from src.db import init_db
from src.syscalls import (
    sys_copy_file, sys_create_file, sys_delete_file, sys_echo, sys_exec,
    sys_get_users, sys_kill, sys_list_files, sys_login, sys_logout,
    sys_logs, sys_mem_info, sys_mem_alloc, sys_mkdir, sys_move_file,
    sys_ps, sys_pwd, sys_read_file, sys_register, sys_rename_file,
    sys_rmdir, sys_shutdown, sys_tree, sys_whoami, sys_write_file,
)

HELP_TEXT = """
Команды StudentOS:
  help                         справка
  echo <текст>                 вывести текст
  register <login> <pass> [role] регистрация пользователя
  login [login password]       вход
  logout                       выход
  whoami                       текущий пользователь
  pwd                          текущий каталог
  cd <path>                    сменить каталог
  mkdir <path>                 создать каталог
  rmdir <path>                 удалить каталог рекурсивно
  touch <path> [text]          создать файл
  create                       создать файл с вводом пути и текста
  cat <path>                   прочитать файл
  write <path> <text>          записать текст
  rm/delete <path>             удалить файл
  rename <old> <new>           переименовать
  copy <src> <dst>             копировать
  move <src> <dst>             переместить
  ls [path]                    список файлов
  tree [path]                  дерево файлов
  run <name> [memory]          запустить процесс
  ps                           список процессов
  kill <pid>                   завершить процесс
  mem [size]                   память / выделить память
  users                        список пользователей
  logs [N]                     журнал системных вызовов
  clear                        очистить экран
  shutdown                     завершить ОС
  exit                         выйти
""".strip()


def norm(path, cwd):
    if not path:
        return cwd
    if path.startswith('/'):
        return path
    if cwd == '/':
        return '/' + path
    return cwd.rstrip('/') + '/' + path


def print_banner():
    print('=' * 48)
    print(f' {OS_NAME} {OS_VERSION} — учебная операционная система')
    print(' Python + SQLite')
    print('=' * 48)
    print('Введите help для списка команд.')


def print_files(files):
    if not files:
        print('(нет файлов)')
        return
    for item in files:
        kind = '<DIR>' if item.get('is_directory') else '     '
        print(f"{kind} {item['path']} [{item['owner']}]")


def print_processes(processes):
    if not processes:
        print('Процессов пока нет.')
        return
    for p in processes:
        print(f"PID={p['pid']} {p['name']} {p['state']} owner={p['owner']} mem={p['memory_used']} MB")


def print_logs(logs):
    if not logs:
        print('Журнал пуст.')
        return
    for row in logs:
        print(f"#{row['id']} {row['username']} {row['syscall_name']} {row['status']} {row['created_at']}")


def main():
    init_db()
    current_user = 'guest'
    cwd = '/'
    print_banner()
    while True:
        try:
            line = input(f'{current_user}@studyos:{cwd}$ ').strip()
            if not line:
                continue
            parts = shlex.split(line)
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd == 'help':
                print(HELP_TEXT)
            elif cmd == 'echo':
                print(sys_echo(' '.join(args), current_user))
            elif cmd == 'register':
                if len(args) < 2:
                    print('Использование: register <login> <password> [role]')
                else:
                    print(sys_register(args[0], args[1], args[2] if len(args) > 2 else 'user', current_user))
            elif cmd == 'login':
                login = args[0] if args else input('Логин: ').strip()
                password = args[1] if len(args) > 1 else input('Пароль: ').strip()
                if sys_login(login, password, current_user):
                    current_user = login
                    print(f'Вы вошли как {current_user}')
                else:
                    print('Ошибка входа')
            elif cmd == 'logout':
                sys_logout(current_user)
                current_user = 'guest'
                cwd = '/'
                print('Выход выполнен')
            elif cmd == 'whoami':
                print(sys_whoami(current_user))
            elif cmd == 'pwd':
                print(sys_pwd(cwd, current_user))
            elif cmd == 'cd':
                target = norm(args[0], cwd) if args else '/'
                info = sys_list_files(target, current_user)
                if target == '/' or (info and info[0].get('is_directory')):
                    cwd = target
                else:
                    print('Каталог не найден')
            elif cmd == 'mkdir':
                print('OK' if args and sys_mkdir(norm(args[0], cwd), current_user) else 'Не удалось создать каталог')
            elif cmd == 'rmdir':
                print('OK' if args and sys_rmdir(norm(args[0], cwd), current_user) else 'Не удалось удалить каталог')
            elif cmd in ('touch', 'create'):
                if cmd == 'create' and not args:
                    path = input('Путь: ').strip()
                    content = input('Содержимое: ')
                else:
                    if not args:
                        print('Укажите путь')
                        continue
                    path = norm(args[0], cwd)
                    content = ' '.join(args[1:])
                fid = sys_create_file(path, content, current_user)
                print(f'Создан файл с id={fid}' if fid != -1 else 'Файл с таким путём уже существует')
            elif cmd == 'cat':
                print(sys_read_file(norm(args[0], cwd), current_user) if args else 'Укажите путь')
            elif cmd == 'write':
                print('OK' if len(args) >= 2 and sys_write_file(norm(args[0], cwd), ' '.join(args[1:]), current_user) else 'Не удалось записать')
            elif cmd in ('rm', 'delete'):
                print('Файл удалён' if args and sys_delete_file(norm(args[0], cwd), current_user) else 'Не удалось удалить файл')
            elif cmd == 'rename':
                print('OK' if len(args) == 2 and sys_rename_file(norm(args[0], cwd), norm(args[1], cwd), current_user) else 'Не удалось переименовать')
            elif cmd == 'copy':
                print('OK' if len(args) == 2 and sys_copy_file(norm(args[0], cwd), norm(args[1], cwd), current_user) else 'Не удалось скопировать')
            elif cmd == 'move':
                print('OK' if len(args) == 2 and sys_move_file(norm(args[0], cwd), norm(args[1], cwd), current_user) else 'Не удалось переместить')
            elif cmd == 'ls':
                print_files(sys_list_files(norm(args[0], cwd) if args else cwd, current_user))
            elif cmd == 'tree':
                print(sys_tree(norm(args[0], cwd) if args else '/', current_user))
            elif cmd == 'run':
                if not args:
                    print('Укажите имя процесса')
                    continue
                pid = sys_exec(args[0], current_user, int(args[1]) if len(args) > 1 else 10)
                print(f'Запущен процесс с PID={pid}' if pid != -1 else 'Не удалось запустить процесс')
            elif cmd == 'ps':
                print_processes(sys_ps(current_user))
            elif cmd == 'kill':
                print(f"Процесс {args[0]} завершён" if args and sys_kill(int(args[0]), current_user) else 'Не удалось завершить процесс')
            elif cmd == 'mem':
                if args:
                    print('OK' if sys_mem_alloc(int(args[0]), current_user) != -1 else 'Недостаточно памяти')
                info = sys_mem_info(current_user)
                print(f"Использовано: {info['used']} / {info['limit']} МБ")
                print(f"Свободно: {info['free']} МБ")
            elif cmd == 'users':
                print(sys_get_users(current_user))
            elif cmd == 'logs':
                print_logs(sys_logs(int(args[0]) if args else 20, current_user))
            elif cmd == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
            elif cmd == 'shutdown':
                print('StudentOS завершает работу' if sys_shutdown(current_user) else 'Нет прав')
                break
            elif cmd == 'exit':
                print('Выход из оболочки.')
                break
            else:
                print('Неизвестная команда. Введите help.')
        except (KeyboardInterrupt, EOFError):
            print('\nВыход из оболочки.')
            break
        except Exception as error:
            print(f'Ошибка: {error}')


if __name__ == '__main__':
    main()
