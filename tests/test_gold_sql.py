import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from tv_pulse.gold.sql_runner import run_sql_files


def test_dim_genre_row_count(gold_conn: sqlite3.Connection) -> None:
    query = "select count(*) from dim_genre"
    result = gold_conn.execute(query).fetchone()[0]

    assert result == 4


def test_dim_genre_keys_sequential(gold_conn: sqlite3.Connection) -> None:
    query = "select genre_key from dim_genre order by genre_key"
    result = gold_conn.execute(query).fetchall()
    res = [row[0] for row in result]

    assert res == [1, 2, 3, 4]


def test_dim_genre_alphabet_order(gold_conn: sqlite3.Connection) -> None:
    query = "select genre from dim_genre order by genre_key"
    result = gold_conn.execute(query).fetchall()

    res = [row[0] for row in result]

    assert res == ["Comedy", "Drama", "Horror", "Sci-Fi"]


def test_dim_genre_unique_constraint(gold_conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        gold_conn.execute("insert into dim_genre (genre_key, genre) values (99, 'Drama')")


def test_dim_show_row_count(gold_conn: sqlite3.Connection) -> None:
    result = gold_conn.execute("select count(*) from dim_show").fetchone()[0]
    result_silver = gold_conn.execute("select count(*) from silver_shows").fetchone()[0]

    assert result == result_silver


def test_dim_show_id_unique(gold_conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="show_id"):
        gold_conn.execute(
            "insert into dim_show (show_id, show_key, name, network_name, "
            "network_country, imdb_id) "
            "values (1, 99, 'Test', 'Net', 'Country', 'tt000')"
        )


def test_dim_show_keys_sequential(gold_conn: sqlite3.Connection) -> None:
    result = gold_conn.execute("select show_key from dim_show order by show_id").fetchall()
    res = [row[0] for row in result]

    assert res == [1, 2, 3, 4]


def test_dim_show_missing_nulls(gold_conn: sqlite3.Connection) -> None:
    result_network = gold_conn.execute(
        "select network_name from dim_show where show_id = 2"
    ).fetchone()[0]
    result_country = gold_conn.execute(
        "select network_country from dim_show where show_id = 2"
    ).fetchone()[0]
    result_imdb = gold_conn.execute("select imdb_id from dim_show where show_id = 3").fetchone()[0]
    result = gold_conn.execute(
        "select count(*) from dim_show where network_name is null or network_country"
        " is null or imdb_id is null"
    ).fetchone()[0]

    assert result_network == "no network"
    assert result_country == "no country"
    assert result_imdb == "no imdb"
    assert result == 0


def test_dim_show_cyrillic(gold_conn: sqlite3.Connection) -> None:
    result = gold_conn.execute("select name from dim_show where show_id = 2").fetchone()[0]

    assert result == "Дивні дива"


def test_dim_show_not_null_constraint(gold_conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="network_name"):
        gold_conn.execute(
            "insert into dim_show (show_key, show_id, name, network_name"
            ", network_country, imdb_id) values (99, 999, 'Test'"
            ", null, 'Country', 'tt000')"
        )


def test_dim_date_no_gaps(gold_conn: sqlite3.Connection, silver_shows_df: pd.DataFrame) -> None:
    cols = ["premiered", "ended", "ingested_at"]
    all_dates = pd.concat([silver_shows_df[c] for c in cols]).dropna()
    # 1 to include both boundary dates inclusively, and 1 for the dummy row with key 1
    expected_rows = (all_dates.max() - all_dates.min()).days + 2
    result = gold_conn.execute("select count(*) from dim_date").fetchone()[0]

    assert result == expected_rows


def test_dim_date_known_date_attributes(gold_conn: sqlite3.Connection) -> None:
    expected_date = gold_conn.execute(
        "select full_date, year, month, quarter, decade, day_name"
        " from dim_date where date_key = 20160715"
    ).fetchone()

    assert expected_date == ("2016-07-15", 2016, 7, 3, 2010, "Friday")


def test_dim_date_contains_all_silver_date(
    gold_conn: sqlite3.Connection, silver_shows_df: pd.DataFrame
) -> None:
    cols = ["premiered", "ended", "ingested_at"]
    all_series = pd.concat([silver_shows_df[c] for c in cols]).dropna()
    silver_dates = set(all_series.dt.strftime("%Y-%m-%d"))

    rows = gold_conn.execute(
        "select full_date from dim_date where full_date is not null"
    ).fetchall()
    gold_dates = {row[0] for row in rows}

    assert silver_dates - gold_dates == set()


def test_dim_date_unknown_key_exist(gold_conn: sqlite3.Connection) -> None:
    res = gold_conn.execute(
        "select date_key, full_date from dim_date where date_key = -1"
    ).fetchone()

    assert res is not None
    assert res == (-1, None)


@pytest.mark.parametrize(
    ("full_date", "expected"),
    [
        ("2020-02-29", (2020, 2, 1, 2020, "Saturday")),
        ("2017-12-31", (2017, 12, 4, 2010, "Sunday")),
        ("2019-12-31", (2019, 12, 4, 2010, "Tuesday")),
        ("2020-01-01", (2020, 1, 1, 2020, "Wednesday")),
        ("2020-06-28", (2020, 6, 2, 2020, "Sunday")),
    ],
)
def test_dim_date_boundary_dates(
    gold_conn: sqlite3.Connection, full_date: str, expected: tuple[int, int, int, int, str]
) -> None:
    row = gold_conn.execute(
        "select year, month, quarter, decade, day_name from dim_date where full_date = ?",
        (full_date,),
    ).fetchone()

    assert row == expected


def test_dim_date_full_date_unique(gold_conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="full_date"):
        gold_conn.execute(
            "insert into dim_date (date_key, full_date) values (99999999, '2016-07-15')"
        )


def test_gold_sql_idempotency(gold_conn: sqlite3.Connection) -> None:
    sql_dir = Path(__file__).resolve().parents[1] / "sql" / "gold"

    before = (
        gold_conn.execute("select count(*) from dim_genre").fetchone()[0],
        gold_conn.execute("select count(*) from dim_show").fetchone()[0],
        gold_conn.execute("select count(*) from dim_date").fetchone()[0],
    )

    run_sql_files(gold_conn, sql_dir)

    after = (
        gold_conn.execute("select count(*) from dim_genre").fetchone()[0],
        gold_conn.execute("select count(*) from dim_show").fetchone()[0],
        gold_conn.execute("select count(*) from dim_date").fetchone()[0],
    )

    assert after == before
