from tests.helpers import reset_system
from src import fs


def test_create_read_write_delete():
    reset_system()
    fid = fs.create_file('/a.txt', 'hello', 'admin')
    assert fid > 0
    assert fs.read_file('/a.txt') == 'hello'
    assert fs.write_file('/a.txt', 'new') is True
    assert fs.read_file('/a.txt') == 'new'
    assert fs.delete_file('/a.txt') is True
    assert fs.read_file('/a.txt') == ''
    print('[PASS] fs create/read/write/delete')


def test_duplicate_list_owner_info():
    reset_system(); fs.create_file('/b.txt', 'b', 'admin')
    assert fs.create_file('/b.txt', 'x', 'admin') == -1
    assert any(x['path'] == '/b.txt' for x in fs.list_files('/'))
    assert fs.get_owner('/b.txt') == 'admin'
    assert fs.get_file_info('/b.txt')['content'] == 'b'
    print('[PASS] fs duplicate/list/owner/info')


def test_directories_copy_move_tree():
    reset_system(); assert fs.create_dir('/docs', 'admin') > 0
    assert fs.create_file('/docs/a.txt', 'A', 'admin') > 0
    assert fs.copy_file('/docs/a.txt', '/docs/b.txt', 'admin') > 0
    assert fs.move_file('/docs/b.txt', '/b.txt') is True
    assert 'a.txt' in '\n'.join(fs.tree('/')) and '/b.txt' in [x['path'] for x in fs.list_files('/')]
    assert fs.delete_dir('/docs') is True
    print('[PASS] fs directories/copy/move/tree')


if __name__ == '__main__':
    test_create_read_write_delete(); test_duplicate_list_owner_info(); test_directories_copy_move_tree()
    print('Все тесты test_fs пройдены.')
