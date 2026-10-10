from tests.helpers import reset_system
from src.fs import create_file
from src.scheduler import create_process, get_process
from src.syscalls import sys_delete_file, sys_kill


def test_guest_cannot_delete_admin_file():
    reset_system(); create_file('/admin_file.txt', 'x', 'admin')
    assert sys_delete_file('/admin_file.txt', 'guest') is False
    assert get_process(999) is None
    print('[PASS] TC-02: guest не может удалить файл admin')


def test_admin_can_delete_user_file():
    reset_system(); create_file('/user_file.txt', 'x', 'student')
    assert sys_delete_file('/user_file.txt', 'admin') is True
    print('[PASS] admin может удалить файл user')


def test_guest_cannot_kill_process():
    reset_system(); pid = create_process('guest_test', 'admin')
    assert sys_kill(pid, 'guest') is False
    assert get_process(pid)['state'] == 'running'
    print('[PASS] guest не может убить процесс')


def test_admin_can_kill_process():
    reset_system(); pid = create_process('admin_test', 'student')
    assert sys_kill(pid, 'admin') is True
    assert get_process(pid) is None
    print('[PASS] admin может убить процесс')


if __name__ == '__main__':
    test_guest_cannot_delete_admin_file(); test_admin_can_delete_user_file(); test_guest_cannot_kill_process(); test_admin_can_kill_process()
    print('Все тесты пройдены.')
