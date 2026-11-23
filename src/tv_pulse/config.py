from pathlib import Path

# Assumes an editable install (pip install -e .), where __file__ resolves inside src/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DB_PATH = DATA_DIR / "gold" / "tv_pulse.db"
SQL_DIR = PROJECT_ROOT / "sql"
GOLD_SQL_DIR = SQL_DIR / "gold"
CHECKS_SQL_DIR = SQL_DIR / "checks"
MARTS_SQL_DIR = SQL_DIR / "marts"

BASE_URL = "https://api.tvmaze.com"
REQUEST_TIMEOUT = 10
REQUEST_PAUSE = 0.5
MAX_PAGES = 5
