from tests.helpers import reset_system
from src.syscalls import *


def test_file_flow():
    reset_system(); assert sys_create_file('/int.txt','data','admin') > 0
    assert sys_read_file('/int.txt','admin') == 'data'
    assert sys_write_file('/int.txt','new','admin') is True
    assert sys_read_file('/int.txt','admin') == 'new'
    print('[PASS] integration file flow')


def test_permission_delete():
    reset_system(); sys_create_file('/secret.txt','x','admin')
    assert sys_delete_file('/secret.txt','student') is False
    assert sys_delete_file('/secret.txt','admin') is True
    print('[PASS] integration permission delete')


def test_process_flow():
    reset_system(); pid = sys_exec('browser','admin',10)
    assert pid > 0 and any(p['pid'] == pid for p in sys_ps('admin'))
    assert sys_kill(pid,'admin') is True
    print('[PASS] integration process flow')


def test_logs_and_auth():
    reset_system(); assert sys_login('admin','admin123','guest') is True
    logs = sys_logs(10,'admin')
    assert any(x['syscall_name'] == 'sys_login' for x in logs)
    assert sys_logs(10,'student') == []
    print('[PASS] integration logs/auth')


def test_directories():
    reset_system(); assert sys_mkdir('/folder','admin') > 0
    assert sys_create_file('/folder/a.txt','a','admin') > 0
    assert 'a.txt' in '\n'.join(sys_tree('/','admin'))
    assert sys_rmdir('/folder','admin') is True
    print('[PASS] integration directories')


def test_user_registration():
    reset_system(); assert sys_register('ivan','1234','user','admin') > 0
    assert sys_login('ivan','1234','guest') is True
    print('[PASS] integration register/login')


def test_error_handling():
    reset_system(); assert sys_read_file('/missing.txt','admin') == ''
    assert sys_kill(999,'admin') is False
    assert sys_delete_file('/missing.txt','admin') is False
    print('[PASS] integration error handling')


if __name__ == '__main__':
    test_file_flow(); test_permission_delete(); test_process_flow(); test_logs_and_auth(); test_directories(); test_user_registration(); test_error_handling()
    print('Все тесты test_integration пройдены.')
