import importlib

MODULES = [
    'tests.test_db', 'tests.test_kernel', 'tests.test_auth', 'tests.test_permissions',
    'tests.test_fs', 'tests.test_scheduler', 'tests.test_integration',
    'tests.test_kernel_unit', 'tests.test_auth_unit',
    'tests.test_fs_functional', 'tests.test_scheduler_functional',
    'tests.test_syscalls_functional', 'tests.test_integration_full', 'tests.test_stress', 'tests.test_extra',
]


def main():
    passed = 0
    failed = 0
    for name in MODULES:
        print(f'\n=== {name} ===')
        module = importlib.import_module(name)
        functions = [getattr(module, item) for item in dir(module) if item.startswith('test_')]
        if hasattr(module, 'run'):
            functions.append(module.run)
        for fn in functions:
            try:
                fn(); passed += 1
            except Exception as error:
                failed += 1
                print(f'[FAIL] {name}.{fn.__name__}: {error}')
    print('\nИТОГОВАЯ СВОДКА')
    print(f'Пройдено: {passed}')
    print(f'Провалено: {failed}')
    if failed:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
