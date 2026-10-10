from tests.helpers import reset_system
from src.auth import authenticate, check_permission, hash_password, register_user
from src.db import execute_select


def test_hash_password():
    assert len(hash_password('secret')) == 64
    assert hash_password('secret') != 'secret'
    print('[PASS] hash_password')


def test_register_and_authenticate():
    reset_system()
    uid = register_user('new_user', 'pass123', 'user')
    assert isinstance(uid, int)
    assert authenticate('new_user', 'pass123')['username'] == 'new_user'
    assert authenticate('new_user', 'wrong') is None
    print('[PASS] register/authenticate')


def test_duplicate_and_storage():
    reset_system()
    assert register_user('admin', 'x', 'admin') is None
    row = execute_select('users', {'username': 'admin'})[0]
    assert row['password_hash'] != 'admin123' and len(row['password_hash']) == 64
    print('[PASS] duplicate and hash storage')


def test_permissions():
    reset_system()
    assert check_permission('admin', 'delete_file', 'student') is True
    assert check_permission('student', 'delete_file', 'student') is True
    assert check_permission('student', 'delete_file', 'admin') is False
    assert check_permission('guest', 'delete_file', 'admin') is False
    print('[PASS] check_permission')


if __name__ == '__main__':
    test_hash_password(); test_register_and_authenticate(); test_duplicate_and_storage(); test_permissions()
    print('Все тесты test_auth пройдены.')
