import logging
import sqlite3
from contextlib import closing
from pathlib import Path

from tv_pulse.gold.load import load_silver_to_sqlite
from tv_pulse.gold.sql_runner import run_quality_checks, run_sql_files

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Start main")

    file_path = Path("data") / "gold" / "tv_pulse.db"

    dir_path = Path("data") / "gold"
    dir_path.mkdir(parents=True, exist_ok=True)

    sql_dir = Path("sql") / "gold"
    silver_root = Path("data") / "silver"
    checks_dir = Path("sql") / "checks"
    marts_dir = Path("sql") / "marts"

    with closing(sqlite3.connect(file_path)) as conn:
        load_silver_to_sqlite(silver_root, conn)
        run_sql_files(conn, sql_dir)
        run_quality_checks(conn, checks_dir)
        run_sql_files(conn, marts_dir)

    logger.info("Finish main")


if __name__ == "__main__":
    main()
