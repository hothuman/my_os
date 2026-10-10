from tests.helpers import reset_system
from src.db import execute_delete, execute_insert, execute_select, execute_update


def test_insert_select_update_delete():
    reset_system()
    uid = execute_insert('users', {'username': 'db_user', 'password_hash': 'x'*64, 'role': 'user', 'created_at': 'now'})
    assert isinstance(uid, int)
    rows = execute_select('users', {'username': 'db_user'})
    assert rows and rows[0]['role'] == 'user'
    assert execute_update('users', {'role': 'admin'}, {'username': 'db_user'}) == 1
    assert execute_select('users', {'username': 'db_user'})[0]['role'] == 'admin'
    assert execute_delete('users', {'username': 'db_user'}) == 1
    print('[PASS] db CRUD')


def test_select_all_and_duplicate():
    reset_system()
    users = execute_select('users')
    assert len(users) >= 3
    duplicate = execute_insert('users', {'username': 'admin', 'password_hash': 'x', 'role': 'admin', 'created_at': 'now'})
    assert duplicate is None
    print('[PASS] db select all and duplicate')


if __name__ == '__main__':
    test_insert_select_update_delete()
    test_select_all_and_duplicate()
    print('Все тесты test_db пройдены.')
