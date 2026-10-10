# Архитектура StudentOS

## Модули
- `shell.py` — команды пользователя.
- `syscalls.py` — API системных вызовов.
- `kernel.py` — состояние ядра, PID и память.
- `auth.py` — пользователи, пароли, права.
- `fs.py` — иерархическая файловая система.
- `scheduler.py` — процессы.
- `logger.py` — журналирование.
- `db.py` — SQLite и CRUD.

## Направление вызовов
`shell → syscalls → kernel/auth/fs/scheduler/logger → db`.

## Основные системные вызовы
`sys_login`, `sys_logout`, `sys_whoami`, `sys_register`, `sys_create_file`, `sys_read_file`, `sys_write_file`, `sys_delete_file`, `sys_list_files`, `sys_mkdir`, `sys_rmdir`, `sys_exec`, `sys_ps`, `sys_kill`, `sys_mem_info`, `sys_logs`, `sys_shutdown`.

## Контракты
- `sys_login`: принимает логин и пароль, возвращает `True/False`, пишет лог.
- `sys_delete_file`: проверяет владельца и права, возвращает `True/False`, пишет `DENIED` при отказе.
- `sys_kill`: завершает процесс только при наличии прав, освобождает память.

## Структуры данных
`user`, `file`, `process`, `log`, `memory_state`, `role` представлены строками SQLite и словарями Python.
