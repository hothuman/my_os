from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_DIR = PROJECT_ROOT / "db"
LOG_DIR = PROJECT_ROOT / "logs"
DB_PATH = DB_DIR / "os.sqlite"

OS_NAME = "StudentOS"
OS_VERSION = "1.0"
MAX_PROCESSES = 10
MAX_MEMORY_MB = 256

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_STUDENT_USERNAME = "student"
DEFAULT_STUDENT_PASSWORD = "student123"
