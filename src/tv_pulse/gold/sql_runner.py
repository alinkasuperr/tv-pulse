import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


def run_sql_files(conn: sqlite3.Connection, sql_dir: Path) -> list[str]:
    logger.info("Running sql files in %s", sql_dir)
    file_names: list[str] = []

    sql_files = sorted(sql_dir.glob("*.sql"))

    if len(sql_files) == 0:
        raise FileNotFoundError(f"No .sql files found in {sql_dir}")

    conn.execute("PRAGMA foreign_keys = ON")

    for file in sql_files:
        sql_text = file.read_text(encoding="utf-8")
        conn.executescript(sql_text)
        file_names.append(file.name)

    logger.info("Finished running sql files in %s", sql_dir)

    return file_names
