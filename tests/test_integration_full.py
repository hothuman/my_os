from tests.helpers import reset_system
from src.syscalls import *


def run():
    reset_system(); passed=0
    assert sys_login('admin','admin123','guest'); print('[PASS] full admin login'); passed+=1
    assert sys_mkdir('/docs','admin')>0; print('[PASS] full mkdir'); passed+=1
    assert sys_create_file('/docs/a.txt','A','admin')>0; print('[PASS] full create'); passed+=1
    assert sys_read_file('/docs/a.txt','admin')=='A'; print('[PASS] full read'); passed+=1
    assert sys_copy_file('/docs/a.txt','/docs/b.txt','admin'); print('[PASS] full copy'); passed+=1
    assert sys_move_file('/docs/b.txt','/b.txt','admin'); print('[PASS] full move'); passed+=1
    pid=sys_exec('demo','admin',10); assert pid>0; print('[PASS] full run'); passed+=1
    assert sys_mem_info('admin')['used']>=10; print('[PASS] full mem'); passed+=1
    assert sys_kill(pid,'admin'); print('[PASS] full kill'); passed+=1
    assert sys_delete_file('/docs/a.txt','student') is False; print('[PASS] full denied'); passed+=1
    print(f'Все интеграционные full тесты пройдены: {passed}')

if __name__ == '__main__': run()
