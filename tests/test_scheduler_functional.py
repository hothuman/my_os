from tests.helpers import reset_system
from src.scheduler import create_process, get_process, list_processes, process_count, schedule_round_robin, terminate_process


def run():
    reset_system(); passed=0
    p1=create_process('p1','admin',5); assert p1>0; print('[PASS] scheduler create'); passed+=1
    p2=create_process('p2','admin',5); assert p2>0; print('[PASS] scheduler second create'); passed+=1
    assert len(list_processes())==2; print('[PASS] scheduler list'); passed+=1
    assert get_process(p1)['name']=='p1'; print('[PASS] scheduler get'); passed+=1
    assert process_count()==2; print('[PASS] scheduler count'); passed+=1
    assert schedule_round_robin()['pid'] in (p1,p2); print('[PASS] scheduler round robin'); passed+=1
    assert terminate_process(p1) is True; print('[PASS] scheduler terminate'); passed+=1
    assert get_process(p1) is None; print('[PASS] scheduler terminated hidden'); passed+=1
    assert create_process('huge','admin',5000)==-1; print('[PASS] scheduler memory limit'); passed+=1
    print(f'Все функциональные тесты scheduler пройдены: {passed}')

if __name__ == '__main__': run()
