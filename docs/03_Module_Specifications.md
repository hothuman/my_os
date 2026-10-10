# Спецификации модулей StudentOS

## 1. Модуль `db.py`
### Назначение
Работа с SQLite: подключение, создание таблиц, универсальные CRUD-функции.
### Публичный интерфейс
`get_connection`, `init_db`, `reset_db`, `execute_insert`, `execute_select`, `execute_update`, `execute_delete`.
### Внутренние зависимости
`sqlite3`, `hashlib`, `datetime`, `pathlib`, `config.py`.
### Обработка ошибок
`IntegrityError` и `OperationalError` возвращают безопасные значения (`None`, `0`, `[]`).
### Побочные эффекты
Создаёт `db/os.sqlite`, таблицы `roles`, `users`, `files`, `processes`, `memory_state`, `syscalls_log`.

## 2. Модуль `kernel.py`
### Назначение
Хранит состояние ядра: текущий пользователь, PID, память и лимит.
### Публичный интерфейс
`Kernel`, `kernel_instance`, `issue_pid`, `allocate_memory`, `free_memory`, `memory_info`, `save_memory_state`, `load_memory_state`, `reset`.
### Внутренние зависимости
`config.py`, `db.py`.
### Обработка ошибок
При нехватке памяти возвращает `False`, не повреждая состояние.
### Побочные эффекты
Обновляет таблицу `memory_state`.

## 3. Модуль `auth.py`
### Назначение
Регистрация, вход и проверка прав доступа.
### Публичный интерфейс
`hash_password`, `register_user`, `authenticate`, `get_role`, `check_permission`.
### Внутренние зависимости
`hashlib`, `db.py`.
### Обработка ошибок
Дубликат пользователя возвращает `None`, неверный пароль возвращает `None`.
### Побочные эффекты
Создаёт записи в `users`.

## 4. Модуль `logger.py`
### Назначение
Единое журналирование системных вызовов.
### Публичный интерфейс
`log_syscall`, `get_logs`.
### Внутренние зависимости
`datetime`, `db.py`.
### Обработка ошибок
Ошибки записи в лог не прерывают работу верхних модулей.
### Побочные эффекты
Добавляет строки в `syscalls_log`.

## 5. Модуль `fs.py`
### Назначение
Иерархическая файловая система в SQLite.
### Публичный интерфейс
`create_file`, `read_file`, `write_file`, `delete_file`, `list_files`, `get_owner`, `get_file_info`, `create_directory`, `delete_directory`, `rename_file`, `copy_file`, `move_file`, `tree`, `count_files`.
### Внутренние зависимости
`db.py`, `datetime`, `pathlib`.
### Обработка ошибок
Дубликат пути возвращает `-1`, отсутствие файла — пустую строку или `False`.
### Побочные эффекты
Изменяет таблицу `files`.

## 6. Модуль `scheduler.py`
### Назначение
Управление процессами и памятью процессов.
### Публичный интерфейс
`create_process`, `list_processes`, `get_process`, `terminate_process`, `schedule_round_robin`, `process_count`.
### Внутренние зависимости
`kernel.py`, `db.py`, `datetime`.
### Обработка ошибок
Недостаток памяти возвращает `-1`, неизвестный PID возвращает `False`.
### Побочные эффекты
Изменяет `processes` и состояние памяти ядра.

## 7. Модуль `syscalls.py`
### Назначение
Единый API системных вызовов для оболочки и тестов.
### Публичный интерфейс
`sys_login`, `sys_logout`, `sys_whoami`, `sys_register`, `sys_create_file`, `sys_read_file`, `sys_write_file`, `sys_delete_file`, `sys_list_files`, `sys_mkdir`, `sys_rmdir`, `sys_rename_file`, `sys_copy_file`, `sys_move_file`, `sys_tree`, `sys_exec`, `sys_ps`, `sys_kill`, `sys_mem_info`, `sys_mem_alloc`, `sys_logs`, `sys_shutdown`.
### Внутренние зависимости
`auth.py`, `fs.py`, `scheduler.py`, `kernel.py`, `logger.py`.
### Обработка ошибок
Отказ прав даёт `False`/`-1` и статус `DENIED`; отсутствие объекта даёт `NOT_FOUND`; успех даёт `OK`.
### Побочные эффекты
Все защищённые действия журналируются в `syscalls_log`.

## 8. Модуль `shell.py`
### Назначение
Командная оболочка StudentOS.
### Публичный интерфейс
`main`, `print_banner`, `print_files`, `print_processes`, `print_logs`.
### Внутренние зависимости
`syscalls.py`, `db.py`, `os`, `shlex`.
### Обработка ошибок
Некорректный ввод перехватывается и выводится сообщением без падения оболочки.
### Побочные эффекты
Принимает ввод, печатает результат, вызывает системные вызовы.

# Матрица трассируемости требований

| Требование | Модули | Проверка |
|---|---|---|
| P-1: syscall ≤ 50 мс | syscalls, logger, db | TC-01, sys_whoami 100 раз |
| P-2: 10 процессов | scheduler, kernel | stress 10 processes |
| P-3: запуск shell ≤ 2 сек | shell, db | импорт и запуск help-сценария |
| P-4: 100 записей журнала ≤ 1 сек | logger, db | sys_logs(100) |
| P-5: повторный init_db ≤ 1 сек | db | test_db |
| R-1: ошибка команды не роняет shell | shell | ручной сценарий SS-04 |
| R-2: ошибка процесса не роняет систему | scheduler, syscalls | sys_kill(999) |
| R-3: init_db не удаляет данные | db | test_db |
| R-4: отсутствующий файл безопасен | fs, syscalls | sys_read_file('/missing') |
| R-5: лимит памяти не портит БД | kernel, scheduler | test_stress |
| S-1: пароли SHA-256 | auth, db | test_auth |
| S-2: user не удаляет чужой файл | auth, syscalls, fs | test_permissions |
| S-3: каждый syscall логируется | logger, syscalls | test_syscalls_functional |
| S-4: журнал доступен admin | auth, syscalls | test_extra |
| S-5: пароль не попадает в лог | syscalls, auth | проверка arguments |
| M-1: ≥5 модулей | src | структура проекта |
| M-2: модули ≤300 строк | src | wc -l src/*.py |
| M-3: понятные имена | src | ревью кода |
| M-4: общий механизм логов | logger | log_syscall |
| M-5: pathlib для путей | config, fs | ревью кода |
| U-1: Python 3.10+ | весь проект | python --version |
| U-2: без внешней СУБД | db | sqlite3 |
| U-3: один SQLite-файл | db | db/os.sqlite |
| U-4: нет сторонних пакетов | весь проект | requirements.txt |
| U-5: лимит памяти | kernel, config | test_stress |

# Тест-кейсы

## TC-01: Производительность системного вызова
Шаги: вызвать `sys_whoami('admin')` 100 раз, измерить среднее время.
Ожидаемый результат: ≤ 50 мс. Фактический результат: проходит. Статус: PASS.

## TC-02: Разграничение прав
Шаги: создать файл admin, вызвать удаление от guest. Ожидаемый результат: `False`, статус `DENIED`. Фактический результат: проходит. Статус: PASS.

## TC-03: Размер модулей
Шаги: `wc -l src/*.py`. Ожидаемый результат: модули в учебном размере, без превышения 300 строк. Статус: PASS.

## TC-04: Журналирование
Шаги: выполнить syscall и проверить `syscalls_log`. Ожидаемый результат: запись со статусом `OK`. Статус: PASS.

## TC-05: Повторная инициализация БД
Шаги: создать данные, вызвать `init_db`, проверить сохранность. Статус: PASS.

# Итоги дня 3
Созданы спецификации восьми модулей, матрица трассируемости, тест-кейсы, проверка прав доступа и диаграмма последовательности `03_sequence_permissions.png`.
