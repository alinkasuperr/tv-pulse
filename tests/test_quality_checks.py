import re
import sqlite3
from pathlib import Path

import pytest

from tv_pulse.gold.sql_runner import run_quality_checks

CHECKS_DIR = Path(__file__).resolve().parents[1] / "sql" / "checks"


def test_quality_check_pass_on_gold(gold_conn: sqlite3.Connection) -> None:

    run_quality_checks(gold_conn, CHECKS_DIR)


def test_quality_check_empty_dir(db_conn: sqlite3.Connection, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match=tmp_path.name):
        run_quality_checks(db_conn, tmp_path)


@pytest.mark.parametrize(
    ("corrupt_sql", "expected_check_name"),
    [
        (
            "delete from fact_show_snapshot where show_key = 1;",
            "01_fact_row_count_mismatch.sql",
        ),
        (
            "delete from dim_show where show_key = 1;",
            "02_silver_shows_missing_in_dim.sql",
        ),
        (
            "delete from bridge_show_genre where show_key = 1;",
            "03_bridge_row_count_mismatch.sql",
        ),
        (
            "update fact_show_snapshot set show_key = 999 where show_key = 1;",
            "04_fact_orphan_show_key.sql",
        ),
        (
            "update fact_show_snapshot set ended_date_key = 19000101 where show_key = 1;",
            "05_fact_orphan_date_keys.sql",
        ),
        (
            (
                "update bridge_show_genre set genre_key = 999 where "
                "rowid = (select min(rowid) from bridge_show_genre);"
            ),
            "06_bridge_orphan_keys.sql",
        ),
        (
            (
                "create table fact_copy as select * from fact_show_snapshot;"
                "drop table fact_show_snapshot;"
                "alter table fact_copy rename to fact_show_snapshot;"
                "insert into fact_show_snapshot select * from fact_show_snapshot limit 1;"
            ),
            "07_fact_grains_duplicates.sql",
        ),
    ],
    ids=[
        "fact_row_count",
        "silver_missing_in_dim",
        "bridge_row_count",
        "fact_orphan_show",
        "fact_orphan_date",
        "bridge_orphan_keys",
        "fact_grain_duplicates",
    ],
)
def test_quality_check_detect_violations(
    gold_conn: sqlite3.Connection, corrupt_sql: str, expected_check_name: str
) -> None:
    gold_conn.execute("PRAGMA foreign_keys = OFF")
    gold_conn.executescript(corrupt_sql)

    with pytest.raises(ValueError, match=re.escape(expected_check_name)):
        run_quality_checks(gold_conn, CHECKS_DIR)


def test_quality_check_empty_result_raises(db_conn: sqlite3.Connection, tmp_path: Path) -> None:
    (tmp_path / "empty_check.sql").write_text("select 1 where 1 = 0;", encoding="utf-8")

    with pytest.raises(ValueError, match="empty_check\\.sql"):
        run_quality_checks(db_conn, tmp_path)


def test_quality_check_aggregates_all_failures(gold_conn: sqlite3.Connection) -> None:
    gold_conn.execute("PRAGMA foreign_keys = OFF")
    gold_conn.execute("delete from dim_show where show_key = 1;")

    with pytest.raises(ValueError, match="Quality checks failed:") as exc_info:
        run_quality_checks(gold_conn, CHECKS_DIR)

    error_msg = str(exc_info.value)
    assert "02_silver_shows_missing_in_dim.sql: 1" in error_msg
    assert "04_fact_orphan_show_key.sql: 1" in error_msg
    assert "06_bridge_orphan_keys.sql: 2" in error_msg
