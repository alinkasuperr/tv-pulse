import logging
import sqlite3
from contextlib import closing

from tv_pulse.config import CHECKS_SQL_DIR, GOLD_DB_PATH, GOLD_SQL_DIR, MARTS_SQL_DIR, SILVER_DIR
from tv_pulse.gold.load import load_silver_to_sqlite
from tv_pulse.gold.sql_runner import run_quality_checks, run_sql_files

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Start main")

    GOLD_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(GOLD_DB_PATH)) as conn:
        load_silver_to_sqlite(SILVER_DIR, conn)
        run_sql_files(conn, GOLD_SQL_DIR)
        run_quality_checks(conn, CHECKS_SQL_DIR)
        run_sql_files(conn, MARTS_SQL_DIR)

    logger.info("Finish main")


if __name__ == "__main__":
    main()
