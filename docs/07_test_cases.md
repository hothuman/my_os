# Тест-кейсы

| ID | Название | Предусловия | Шаги | Ожидаемый результат | Факт | Статус |
|---|---|---|---|---|---|---|
| DB-01 | CRUD users | БД создана | insert/select/update/delete | данные корректны | PASS | PASS |
| K-01 | Память ядра | чистая БД | allocate/free | used меняется | PASS | PASS |
| A-01 | SHA-256 | auth доступен | hash_password | 64 символа | PASS | PASS |
| FS-01 | Файл | admin | create/read/write/delete | файл работает | PASS | PASS |
| SCH-01 | Процесс | admin | create/kill | процесс завершён | PASS | PASS |
| INT-01 | Сквозной сценарий | admin | login→file→run→kill | всё работает | PASS | PASS |
