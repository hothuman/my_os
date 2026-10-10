from tests.helpers import reset_system
from src.syscalls import *


def test_many_files():
    reset_system()
    for i in range(50): assert sys_create_file(f'/stress_{i}.txt', str(i), 'admin') > 0
    assert len(sys_list_files('/', 'admin')) >= 50
    print('[PASS] stress 50 files')


def test_many_processes():
    reset_system(); pids=[]
    for i in range(10): pids.append(sys_exec(f'p{i}', 'admin', 5))
    assert len([p for p in sys_ps('admin') if p['name'].startswith('p')]) == 10
    for pid in pids: assert sys_kill(pid, 'admin') is True
    print('[PASS] stress 10 processes')


def test_many_syscalls():
    reset_system()
    for _ in range(100): assert sys_whoami('admin') == 'admin'
    assert len(sys_logs(100, 'admin')) >= 50
    print('[PASS] stress 100 syscalls')


def test_memory_limit():
    reset_system(); assert sys_exec('huge', 'admin', 5000) == -1
    assert sys_mem_info('admin')['used'] == 0
    print('[PASS] stress memory limit')

if __name__ == '__main__':
    test_many_files(); test_many_processes(); test_many_syscalls(); test_memory_limit()
    print('Все стресс-тесты пройдены.')
