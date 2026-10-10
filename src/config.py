"""Project configuration for StudentOS."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_DIR = PROJECT_ROOT / "db"
LOG_DIR = PROJECT_ROOT / "logs"
DB_PATH = DB_DIR / "os.sqlite"

OS_NAME = "StudentOS"
OS_VERSION = "10.0"
MAX_PROCESSES = 10
MAX_MEMORY_MB = 1024
DEFAULT_PROCESS_MEMORY = 10

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_STUDENT_USERNAME = "student"
DEFAULT_STUDENT_PASSWORD = "student123"
