from tests.helpers import reset_system
from src import fs


def run():
    reset_system(); passed=0
    checks = []
    checks.append(('create', lambda: fs.create_file('/f1.txt','1','admin') > 0))
    checks.append(('read', lambda: fs.read_file('/f1.txt') == '1'))
    checks.append(('write', lambda: fs.write_file('/f1.txt','2') and fs.read_file('/f1.txt') == '2'))
    checks.append(('duplicate', lambda: fs.create_file('/f1.txt','x','admin') == -1))
    checks.append(('owner', lambda: fs.get_owner('/f1.txt') == 'admin'))
    checks.append(('info', lambda: fs.get_file_info('/f1.txt')['path'] == '/f1.txt'))
    checks.append(('mkdir', lambda: fs.create_dir('/dir','admin') > 0))
    checks.append(('copy', lambda: fs.copy_file('/f1.txt','/dir/copy.txt','admin') > 0 and fs.read_file('/dir/copy.txt') == '2'))
    checks.append(('move', lambda: fs.move_file('/dir/copy.txt','/moved.txt') and fs.read_file('/moved.txt') == '2'))
    checks.append(('delete', lambda: fs.delete_file('/moved.txt') and fs.read_file('/moved.txt') == ''))
    for name, fn in checks:
        assert fn(), name
        passed += 1; print(f'[PASS] fs functional {name}')
    print(f'Все функциональные тесты fs пройдены: {passed}')

if __name__ == '__main__': run()
