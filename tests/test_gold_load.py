import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from tv_pulse.gold.load import load_silver_to_sqlite

df_shows = pd.DataFrame(
    [
        {
            "show_id": 1,
            "name": "Stranger Things",
            "premiered": pd.Timestamp("2016-07-15"),
            "ended": pd.Timestamp("2022-03-11"),
            "ingested_at": pd.Timestamp("2026-10-28"),
        },
        {
            "show_id": 2,
            "name": "Дивні дива",
            "premiered": pd.Timestamp("2019-07-04"),
            "ended": pd.NaT,
            "ingested_at": pd.Timestamp("2026-10-28"),
        },
        {
            "show_id": 3,
            "name": "Dark",
            "premiered": pd.Timestamp("2017-12-01"),
            "ended": pd.Timestamp("2020-06-27"),
            "ingested_at": pd.Timestamp("2026-10-28"),
        },
    ]
)

df_show_genre = pd.DataFrame(
    [
        {"show_id": 1, "genre": "Drama"},
        {"show_id": 1, "genre": "Sci-Fi"},
        {"show_id": 2, "genre": "Drama"},
        {"show_id": 3, "genre": "Mystery"},
    ]
)


def test_load_silver_to_sqlite_table_exists(
    setup_silver_data: Path, db_conn: sqlite3.Connection
) -> None:
    load_silver_to_sqlite(silver_root=setup_silver_data, conn=db_conn)

    shows_table = db_conn.execute(
        "select name from sqlite_master where type='table' and name='silver_shows'"
    ).fetchone()
    show_genre_table = db_conn.execute(
        "select name from sqlite_master where type='table' and name='silver_show_genre'"
    ).fetchone()
    assert shows_table is not None
    assert show_genre_table is not None


def test_load_silver_to_sqlite_count_rows(
    setup_silver_data: Path, db_conn: sqlite3.Connection
) -> None:
    load_silver_to_sqlite(silver_root=setup_silver_data, conn=db_conn)

    shows_count = db_conn.execute("select count(*) from silver_shows").fetchone()[0]
    show_genre_count = db_conn.execute("select count(*) from silver_show_genre").fetchone()[0]
    assert shows_count == 4
    assert show_genre_count == 5


def test_load_silver_to_sqlite_cyrillic(
    setup_silver_data: Path, db_conn: sqlite3.Connection
) -> None:
    load_silver_to_sqlite(silver_root=setup_silver_data, conn=db_conn)

    cyrillic_name = db_conn.execute("select name from silver_shows where show_id = 2").fetchone()[
        0
    ]
    assert cyrillic_name == "Дивні дива"


def test_load_silver_to_sqlite_missing_date_becomes_null(
    setup_silver_data: Path, db_conn: sqlite3.Connection
) -> None:
    load_silver_to_sqlite(silver_root=setup_silver_data, conn=db_conn)

    ended_date = db_conn.execute("select ended from silver_shows where show_id = 2").fetchone()[0]
    assert ended_date is None


def test_load_silver_to_sqlite_idempotency(
    setup_silver_data: Path, db_conn: sqlite3.Connection
) -> None:
    load_silver_to_sqlite(silver_root=setup_silver_data, conn=db_conn)
    load_silver_to_sqlite(silver_root=setup_silver_data, conn=db_conn)
    load_silver_to_sqlite(silver_root=setup_silver_data, conn=db_conn)

    shows_count = db_conn.execute("SELECT COUNT(*) FROM silver_shows").fetchone()[0]
    assert shows_count == 4

    show_genre_count = db_conn.execute("select count(*) from silver_show_genre").fetchone()[0]
    assert show_genre_count == 5


def test_load_silver_to_sqlite_missing_file(tmp_path: Path, db_conn: sqlite3.Connection) -> None:
    df_shows.to_parquet(tmp_path / "shows.parquet", index=False)

    with pytest.raises(FileNotFoundError, match=r"show_genre\.parquet"):
        load_silver_to_sqlite(silver_root=tmp_path, conn=db_conn)


def test_load_silver_to_sqlite_date(setup_silver_data: Path, db_conn: sqlite3.Connection) -> None:
    load_silver_to_sqlite(silver_root=setup_silver_data, conn=db_conn)

    shows_date = db_conn.execute(
        "select premiered from silver_shows where show_id = 1"
    ).fetchone()[0]
    assert shows_date == "2016-07-15 00:00:00"
