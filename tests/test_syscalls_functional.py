from tests.helpers import reset_system
from src.syscalls import *


def run():
    reset_system(); passed=0
    assert sys_login('admin','admin123','guest') is True; print('[PASS] syscall login'); passed+=1
    assert sys_whoami('admin') == 'admin'; print('[PASS] syscall whoami'); passed+=1
    assert sys_create_file('/s.txt','text','admin') > 0; print('[PASS] syscall create'); passed+=1
    assert sys_read_file('/s.txt','admin') == 'text'; print('[PASS] syscall read'); passed+=1
    assert sys_write_file('/s.txt','new','admin') is True; print('[PASS] syscall write'); passed+=1
    assert any(f['path']=='/s.txt' for f in sys_list_files('/','admin')); print('[PASS] syscall list'); passed+=1
    pid=sys_exec('app','admin',10); assert pid>0; print('[PASS] syscall exec'); passed+=1
    assert any(p['pid']==pid for p in sys_ps('admin')); print('[PASS] syscall ps'); passed+=1
    assert sys_kill(pid,'admin') is True; print('[PASS] syscall kill'); passed+=1
    assert sys_delete_file('/s.txt','admin') is True; print('[PASS] syscall delete'); passed+=1
    assert any(l['syscall_name']=='sys_delete_file' for l in sys_logs(30,'admin')); print('[PASS] syscall logs'); passed+=1
    print(f'Все функциональные тесты syscalls пройдены: {passed}')

if __name__ == '__main__': run()
