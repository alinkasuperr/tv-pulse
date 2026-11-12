import sqlite3
from pathlib import Path

import pytest

from tv_pulse.gold.sql_runner import run_sql_files


def test_sql_runner_execution_order(db_conn: sqlite3.Connection, tmp_path: Path) -> None:
    (tmp_path / "01_first.sql").write_text("create table test_t (id integer);", encoding="utf-8")
    (tmp_path / "02_second.sql").write_text("insert into test_t values(1);", encoding="utf-8")

    result = run_sql_files(db_conn, tmp_path)
    exists = db_conn.execute("select exists (select id from test_t where id = 1)").fetchone()[0]

    assert result == ["01_first.sql", "02_second.sql"]
    assert exists, "Rows is not found"


def test_sql_runner_empty_dir(db_conn: sqlite3.Connection, tmp_path: Path) -> None:

    with pytest.raises(FileNotFoundError, match=str(tmp_path.name)):
        run_sql_files(db_conn, tmp_path)


def test_sql_runner_files_rerun(db_conn: sqlite3.Connection, tmp_path: Path) -> None:
    (tmp_path / "01_init.sql").write_text(
        "drop table if exists test_t; create table test_t (id integer);", encoding="utf-8"
    )

    first_run = run_sql_files(db_conn, tmp_path)
    second_run = run_sql_files(db_conn, tmp_path)

    result = db_conn.execute(
        'select count(*) from sqlite_master where type="table" AND name="test_t";'
    ).fetchone()[0]

    assert first_run == second_run
    assert result == 1


def test_sql_runner_enables_keys(db_conn: sqlite3.Connection, tmp_path: Path) -> None:
    (tmp_path / "random.sql").write_text("create table test_t (id integer);", encoding="utf-8")

    run_sql_files(db_conn, tmp_path)
    result = db_conn.execute("pragma foreign_keys;").fetchone()[0]

    assert result == 1
