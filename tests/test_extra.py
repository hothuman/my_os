from tests.helpers import reset_system
from src.auth import register_user, authenticate
from src.fs import create_dir, create_file, count_files, list_files, normalize_path, tree
from src.scheduler import create_process, process_count, terminate_process
from src.syscalls import sys_echo, sys_logs, sys_mem_info, sys_mkdir, sys_pwd, sys_register, sys_tree


def test_normalize_path():
    assert normalize_path('a/b') == '/a/b'
    print('[PASS] extra normalize path')


def test_count_files():
    reset_system(); create_file('/one.txt','1','admin')
    assert count_files() >= 1
    print('[PASS] extra count files')


def test_tree_root():
    reset_system(); create_dir('/x','admin'); create_file('/x/a.txt','a','admin')
    assert 'a.txt' in '\n'.join(tree('/'))
    print('[PASS] extra tree root')


def test_pwd_syscall():
    reset_system(); assert sys_pwd('/docs','admin') == '/docs'
    print('[PASS] extra pwd syscall')


def test_echo_syscall():
    reset_system(); assert sys_echo('hello','guest') == 'hello'
    print('[PASS] extra echo syscall')


def test_register_syscall():
    reset_system(); assert sys_register('extra','pass','user','admin') > 0
    assert authenticate('extra','pass') is not None
    print('[PASS] extra register syscall')


def test_process_count_after_create():
    reset_system(); create_process('x','admin',1)
    assert process_count() == 1
    print('[PASS] extra process count')


def test_process_count_after_kill():
    reset_system(); pid=create_process('x','admin',1); terminate_process(pid)
    assert process_count() == 0
    print('[PASS] extra process count after kill')


def test_memory_info_shape():
    reset_system(); info = sys_mem_info('admin')
    assert {'used','free','limit'} <= set(info)
    print('[PASS] extra memory info shape')


def test_logs_denied_for_user():
    reset_system(); assert sys_logs(5, 'student') == []
    print('[PASS] extra logs denied')


def test_mkdir_syscall():
    reset_system(); assert sys_mkdir('/mk','admin') > 0
    assert any(x['path']=='/mk' for x in list_files('/'))
    print('[PASS] extra mkdir syscall')


def test_tree_syscall():
    reset_system(); sys_mkdir('/tree','admin')
    assert 'tree' in '\n'.join(sys_tree('/','admin'))
    print('[PASS] extra tree syscall')


if __name__ == '__main__':
    for name, obj in sorted(globals().items()):
        if name.startswith('test_'):
            obj()
    print('Все дополнительные тесты пройдены.')
