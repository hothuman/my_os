from src.db import reset_db, init_db
from src.kernel import kernel_instance


def reset_system():
    reset_db()
    init_db()
    kernel_instance.reset()
