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


def test_bridge_show_genre_count_rows(gold_conn: sqlite3.Connection) -> None:
    bridge_show_rows = gold_conn.execute("select count(*) from bridge_show_genre").fetchone()[0]
    silver_show_rows = gold_conn.execute("select count(*) from silver_show_genre").fetchone()[0]

    assert bridge_show_rows == silver_show_rows


def test_bridge_show_skips_shows_without_genres(gold_conn: sqlite3.Connection) -> None:
    res = gold_conn.execute(
        "select count(*) from bridge_show_genre b join dim_show s on s.show_key = b.show_key"
        " where s.show_id = 3"
    ).fetchone()[0]

    assert res == 0


def test_bridge_show_genre_duplicates(gold_conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        gold_conn.execute("insert into bridge_show_genre (show_key, genre_key) values (1, 2)")


@pytest.mark.parametrize(
    ("show_key", "genre_key"),
    [
        (999, 1),
        (1, 999),
    ],
    ids=["missing_show_key", "missing_genre_key"],
)
def test_bridge_show_genre_foreign_key(
    gold_conn: sqlite3.Connection, show_key: int, genre_key: int
) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        gold_conn.execute(
            "insert into bridge_show_genre (show_key, genre_key) values (?, ?)",
            (show_key, genre_key),
        )


@pytest.mark.parametrize(
    ("show_key", "genre_key"),
    [
        (None, 1),
        (1, None),
    ],
    ids=["null_show_key", "null_genre_key"],
)
def test_bridge_show_genre_not_null_constraint(
    gold_conn: sqlite3.Connection, show_key: int | None, genre_key: int | None
) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="NOT NULL"):
        gold_conn.execute(
            "insert into bridge_show_genre (show_key, genre_key) values (?, ?)",
            (show_key, genre_key),
        )


def test_fact_show_snapshot_count_rows(gold_conn: sqlite3.Connection) -> None:
    rows = gold_conn.execute("select count(*) from fact_show_snapshot").fetchone()[0]
    series = gold_conn.execute("select count(*) from silver_shows").fetchone()[0]

    assert rows == series


def test_fact_show_snapshot_duplicates(gold_conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        gold_conn.execute(
            "insert into fact_show_snapshot (show_key, snapshot_date_key, "
            "premiered_date_key, ended_date_key) values (1, 20261028, -1, -1)"
        )


def test_fact_show_snapshot_date_keys(gold_conn: sqlite3.Connection) -> None:
    ended_key = gold_conn.execute(
        "select ended_date_key from fact_show_snapshot f join dim_show s"
        " on f.show_key = s.show_key where s.show_id = 2"
    ).fetchone()[0]
    premiered_key = gold_conn.execute(
        "select premiered_date_key from fact_show_snapshot f join dim_show s "
        "on f.show_key = s.show_key where s.show_id = 4"
    ).fetchone()[0]

    assert ended_key == -1
    assert premiered_key == -1


def test_fact_show_snapshot_absence_of_rating(gold_conn: sqlite3.Connection) -> None:
    res = gold_conn.execute(
        "select rating_avg from fact_show_snapshot f join dim_show s "
        "on f.show_key = s.show_key where s.show_id = 2"
    ).fetchone()[0]

    assert res is None


def test_fact_show_snapshot_equal_key(gold_conn: sqlite3.Connection) -> None:
    snapshot_date_key = gold_conn.execute(
        "select snapshot_date_key from fact_show_snapshot f join dim_show s "
        "on f.show_key = s.show_key where s.show_id = 1"
    ).fetchone()[0]

    assert snapshot_date_key == 20261028


def test_fact_show_snapshot_measures_match_silver(gold_conn: sqlite3.Connection) -> None:
    fact_measures = gold_conn.execute(
        "select rating_avg, weight, runtime_min, average_runtime_min from fact_show_snapshot "
        "join dim_show on dim_show.show_key = fact_show_snapshot.show_key where show_id = 1"
    ).fetchone()
    silver_measures = gold_conn.execute(
        "select rating_avg, weight, runtime_min, average_runtime_min "
        "from silver_shows where show_id = 1"
    ).fetchone()

    assert fact_measures == silver_measures


def test_fact_show_snapshot_invalid_date_fk(gold_conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        gold_conn.execute(
            "insert into fact_show_snapshot (show_key, snapshot_date_key, "
            "premiered_date_key, ended_date_key) values (1, 19000101, -1, -1)"
        )


def test_fact_show_snapshot_role_playing_dates(gold_conn: sqlite3.Connection) -> None:
    row = gold_conn.execute(
        "select d_snap.full_date, d_prem.full_date, d_end.full_date "
        "from fact_show_snapshot f "
        "join dim_show s on f.show_key = s.show_key "
        "join dim_date d_snap on f.snapshot_date_key = d_snap.date_key "
        "join dim_date d_prem on f.premiered_date_key = d_prem.date_key "
        "join dim_date d_end on f.ended_date_key = d_end.date_key "
        "where s.show_id = 1"
    ).fetchone()

    assert row == ("2026-10-28", "2016-07-15", "2022-03-11")
