from tests.helpers import reset_system
from src.kernel import kernel_instance as k


def test_memory_allocate_free():
    reset_system()
    assert k.allocate_memory(100) is True
    assert k.memory_info()['used'] == 100
    assert k.free_memory(40) is True
    assert k.memory_info()['used'] == 60
    print('[PASS] kernel memory allocate/free')


def test_memory_limit():
    reset_system()
    assert k.allocate_memory(5000) is False
    assert k.memory_info()['used'] == 0
    print('[PASS] kernel memory limit')


def test_pid_and_reset():
    reset_system()
    assert k.issue_pid() == 1
    assert k.issue_pid() == 2
    k.reset()
    assert k.issue_pid() == 1
    print('[PASS] kernel pid/reset')


def test_current_user():
    reset_system()
    assert k.set_current_user('admin', 'admin')['role'] == 'admin'
    k.logout()
    assert k.username == 'guest'
    print('[PASS] kernel current user')


if __name__ == '__main__':
    test_memory_allocate_free(); test_memory_limit(); test_pid_and_reset(); test_current_user()
    print('Все тесты test_kernel пройдены.')
