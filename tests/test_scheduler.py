from tests.helpers import reset_system
from src.scheduler import create_process, get_process, list_processes, process_count, schedule_round_robin, terminate_process


def test_create_list_get():
    reset_system(); pid = create_process('app1', 'admin', 10)
    assert pid > 0
    assert get_process(pid)['name'] == 'app1'
    assert process_count() == 1
    assert list_processes()[0]['pid'] == pid
    print('[PASS] scheduler create/list/get')


def test_terminate_and_memory():
    reset_system(); pid = create_process('app2', 'admin', 20)
    assert terminate_process(pid) is True
    assert get_process(pid) is None
    assert process_count() == 0
    print('[PASS] scheduler terminate/memory')


def test_limit_and_round_robin():
    reset_system()
    assert create_process('huge', 'admin', 5000) == -1
    p1 = create_process('rr1', 'admin', 1); p2 = create_process('rr2', 'admin', 1)
    assert schedule_round_robin()['pid'] in (p1, p2)
    print('[PASS] scheduler limit/round_robin')


if __name__ == '__main__':
    test_create_list_get(); test_terminate_and_memory(); test_limit_and_round_robin()
    print('Все тесты test_scheduler пройдены.')
