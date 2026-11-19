import sqlite3
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from tv_pulse.gold.sql_runner import run_sql_files

GoldDbFactory = Callable[[pd.DataFrame, pd.DataFrame], sqlite3.Connection]

marts_shows = pd.DataFrame(
    [
        {
            "show_id": 1,
            "name": "Stranger Things",
            "premiered": pd.Timestamp("2016-07-15"),
            "ended": pd.Timestamp("2022-03-11"),
            "ingested_at": pd.Timestamp("2026-10-28"),
            "runtime_min": 93,
            "rating_avg": 5.8,
            "network_name": "HBO",
            "network_country": "United States",
            "weight": 240,
            "type": "Scripted",
            "language": "English",
            "status": "Ended",
            "url": "https://tvmaze.com",
            "average_runtime_min": 60,
            "updated_at": pd.Timestamp("2023-11-14 22:13:20"),
            "imdb_id": "tt1553656",
        },
        {
            "show_id": 2,
            "name": "Дивні дива",
            "premiered": pd.Timestamp("2019-07-04"),
            "ended": pd.NaT,
            "ingested_at": pd.Timestamp("2026-10-28"),
            "runtime_min": 180,
            "rating_avg": None,
            "network_name": None,
            "network_country": None,
            "weight": 230,
            "type": "Scripted",
            "language": "Polish",
            "status": "Running",
            "url": "https://tvmaze.com",
            "average_runtime_min": 100,
            "updated_at": pd.Timestamp("2023-11-14 22:13:20"),
            "imdb_id": "tt1553626",
        },
        {
            "show_id": 3,
            "name": "Dark",
            "premiered": pd.Timestamp("2017-12-01"),
            "ended": pd.Timestamp("2020-06-27"),
            "ingested_at": pd.Timestamp("2026-10-28"),
            "runtime_min": 55,
            "rating_avg": 7.7,
            "network_name": "kyivstar",
            "network_country": "Australia",
            "weight": 155,
            "type": "Scripted",
            "language": "English",
            "status": "Ended",
            "url": "https://tvmaze.com",
            "average_runtime_min": 60,
            "updated_at": pd.Timestamp("2023-11-14 22:13:20"),
            "imdb_id": None,
        },
        {
            "show_id": 4,
            "name": "Dark2",
            "premiered": pd.NaT,
            "ended": pd.Timestamp("2023-07-20"),
            "ingested_at": pd.Timestamp("2026-10-28"),
            "runtime_min": 40,
            "rating_avg": 3.2,
            "network_name": "HBO",
            "network_country": "United States",
            "weight": 88,
            "type": "Scripted",
            "language": "English",
            "status": "Unknown",
            "url": "https://tvmaze.com",
            "average_runtime_min": 40,
            "updated_at": pd.Timestamp("2023-11-14 22:13:20"),
            "imdb_id": "tt1553646",
        },
        {
            "show_id": 5,
            "name": "Dark5",
            "premiered": pd.Timestamp("2021-04-11"),
            "ended": pd.Timestamp("2024-09-05"),
            "ingested_at": pd.Timestamp("2026-10-28"),
            "runtime_min": 75,
            "rating_avg": 1,
            "network_name": "HBO",
            "network_country": "United States",
            "weight": 135,
            "type": "Scripted",
            "language": "English",
            "status": "Running",
            "url": "https://tvmaze.com",
            "average_runtime_min": 70,
            "updated_at": pd.Timestamp("2023-11-14 22:13:20"),
            "imdb_id": "tt1553546",
        },
        {
            "show_id": 6,
            "name": "Dark6",
            "premiered": pd.Timestamp("2019-06-18"),
            "ended": pd.Timestamp("2023-07-29"),
            "ingested_at": pd.Timestamp("2026-10-28"),
            "runtime_min": 15,
            "rating_avg": 6.6,
            "network_name": "starlink",
            "network_country": "Japan",
            "weight": 30,
            "type": "Scripted",
            "language": "Spanish",
            "status": "Unknown",
            "url": "https://tvmaze.com",
            "average_runtime_min": 5,
            "updated_at": pd.Timestamp("2023-11-14 22:13:20"),
            "imdb_id": "tt1553446",
        },
        {
            "show_id": 7,
            "name": "Dark7",
            "premiered": pd.Timestamp("2020-11-08"),
            "ended": pd.Timestamp("2023-03-14"),
            "ingested_at": pd.Timestamp("2026-10-28"),
            "runtime_min": 909,
            "rating_avg": 6.5,
            "network_name": "RareTV",
            "network_country": "Maldives",
            "weight": 1020,
            "type": "Scripted",
            "language": "German",
            "status": "Running",
            "url": "https://tvmaze.com",
            "average_runtime_min": 500,
            "updated_at": pd.Timestamp("2023-11-14 22:13:20"),
            "imdb_id": "tt1553346",
        },
        {
            "show_id": 8,
            "name": "Dark8",
            "premiered": pd.Timestamp("2024-02-02"),
            "ended": pd.Timestamp("2024-08-02"),
            "ingested_at": pd.Timestamp("2026-10-28"),
            "runtime_min": 150,
            "rating_avg": 9,
            "network_name": "kyivstar",
            "network_country": "Ukraine",
            "weight": 280,
            "type": "Scripted",
            "language": "English",
            "status": "Ended",
            "url": "https://tvmaze.com",
            "average_runtime_min": 100,
            "updated_at": pd.Timestamp("2023-11-14 22:13:20"),
            "imdb_id": "tt1553246",
        },
        {
            "show_id": 9,
            "name": "Dark9",
            "premiered": pd.Timestamp("2024-01-13"),
            "ended": pd.Timestamp("2024-09-25"),
            "ingested_at": pd.Timestamp("2026-10-28"),
            "runtime_min": 44,
            "rating_avg": 9,
            "network_name": "kyivstar",
            "network_country": "Ukraine",
            "weight": 88,
            "type": "Scripted",
            "language": "English",
            "status": "Ended",
            "url": "https://tvmaze.com",
            "average_runtime_min": 32,
            "updated_at": pd.Timestamp("2023-11-14 22:13:20"),
            "imdb_id": "tt1553146",
        },
        {
            "show_id": 10,
            "name": "Dark10",
            "premiered": pd.Timestamp("2024-03-12"),
            "ended": pd.Timestamp("2024-08-24"),
            "ingested_at": pd.Timestamp("2026-10-28"),
            "runtime_min": 67,
            "rating_avg": 3.2,
            "network_name": "starlink",
            "network_country": "Ukraine",
            "weight": 101,
            "type": "Scripted",
            "language": "German",
            "status": "Ended",
            "url": "https://tvmaze.com",
            "average_runtime_min": 47,
            "updated_at": pd.Timestamp("2023-11-14 22:13:20"),
            "imdb_id": "tt1553046",
        },
    ]
)

marts_genre = pd.DataFrame(
    [
        {"show_id": 1, "genre": "Drama"},
        {"show_id": 1, "genre": "Sci-Fi"},
        {"show_id": 2, "genre": "Documentary"},
        {"show_id": 2, "genre": "Sci-Fi"},
        {"show_id": 4, "genre": "Comedy"},
        {"show_id": 4, "genre": "Horror"},
        {"show_id": 5, "genre": "Action"},
        {"show_id": 5, "genre": "Horror"},
        {"show_id": 6, "genre": "Comedy"},
        {"show_id": 7, "genre": "Horror"},
        {"show_id": 7, "genre": "Romance"},
        {"show_id": 8, "genre": "Fantasy"},
        {"show_id": 9, "genre": "Fantasy"},
        {"show_id": 9, "genre": "Horror"},
        {"show_id": 10, "genre": "Horror"},
    ]
)


@pytest.fixture
def make_gold_db(
    db_conn: sqlite3.Connection,
) -> Callable[[pd.DataFrame, pd.DataFrame], sqlite3.Connection]:
    def _build(shows_df: pd.DataFrame, genre_df: pd.DataFrame) -> sqlite3.Connection:
        shows_df.to_sql("silver_shows", db_conn, index=False, if_exists="replace")
        genre_df.to_sql("silver_show_genre", db_conn, index=False, if_exists="replace")
        sql_dir = Path(__file__).resolve().parents[1] / "sql" / "gold"
        run_sql_files(db_conn, sql_dir)
        marts_dir = Path(__file__).resolve().parents[1] / "sql" / "marts"
        run_sql_files(db_conn, marts_dir)

        return db_conn

    return _build


def test_marts_factory_builds_gold(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute("select count(*) from fact_show_snapshot").fetchone()[0]

    assert res == 10


def test_top_shows_by_genre_known_ranking(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute(
        "select name, rating_avg, rank_in_genre from mart_top_shows_by_genre "
        "where genre= 'Horror' order by rank_in_genre"
    ).fetchall()

    assert res == [
        ("Dark9", 9.0, 1),
        ("Dark7", 6.5, 2),
        ("Dark10", 3.2, 3),
    ]


def test_top_shows_by_genre_excludes_null_rating(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute(
        "select count(*) from mart_top_shows_by_genre where show_id = 2"
    ).fetchone()[0]

    assert res == 0


def test_top_shows_by_genre_idempotency(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    marts_dir = Path(__file__).resolve().parents[1] / "sql" / "marts"
    before = conn.execute("select count(*) from mart_top_shows_by_genre").fetchone()

    run_sql_files(conn, marts_dir)
    run_sql_files(conn, marts_dir)

    after = conn.execute("select count(*) from mart_top_shows_by_genre").fetchone()

    assert before == after


def test_top_shows_by_genre_tie_breaker(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute(
        "select name, rank_in_genre from mart_top_shows_by_genre "
        'where genre="Fantasy" order by rank_in_genre'
    ).fetchall()

    assert res == [("Dark8", 1), ("Dark9", 2)]


def test_top_shows_by_genre_fewer_than_three(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute(
        "select name, rank_in_genre from mart_top_shows_by_genre "
        'where genre="Comedy" order by rank_in_genre'
    ).fetchall()

    assert res == [("Dark6", 1), ("Dark2", 2)]


def test_top_shows_by_genre_excludes_genreless_show(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute(
        "select count(*) from mart_top_shows_by_genre where show_id = 3"
    ).fetchone()[0]

    assert res == 0


def test_genre_vs_overall_overall_avg_ignores_genre_duplication(
    make_gold_db: GoldDbFactory,
) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute("select overall_avg from mart_genre_vs_overall").fetchone()[0]

    assert res == 5.78


def test_genre_vs_overall_for_genre(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res_avg = conn.execute(
        'select overall_avg, genre_avg, diff_avg from mart_genre_vs_overall where genre="Fantasy"'
    ).fetchall()
    res_genre = conn.execute(
        'select shows_count from mart_genre_vs_overall where genre="Fantasy"'
    ).fetchone()[0]

    assert res_avg == [(5.78, 9.00, 3.22)]
    assert res_genre == 2


def test_genre_vs_overall_null_genre(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute(
        "select genre from mart_genre_vs_overall where genre='Documentary'"
    ).fetchone()

    assert res is None


def test_genre_vs_overall_ignores_null_rating(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute(
        'select genre_avg, shows_count from mart_genre_vs_overall where genre="Sci-Fi" '
    ).fetchall()

    assert res == [(5.8, 1)]


def test_genre_vs_overall_count_and_sorting(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute(
        "select genre, shows_count from mart_genre_vs_overall order by genre_avg desc"
    ).fetchall()

    assert len(res) == 7
    assert res[0] == ("Fantasy", 2)

    counts = dict(res)
    assert counts["Horror"] == 5


def test_yearly_trend_known_values_and_lag_gap(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res_prev = conn.execute(
        "select prev_year from mart_yearly_trend where year=2016 or year=2019 order by year"
    ).fetchall()
    res_rolling = conn.execute(
        "select rolling_avg from mart_yearly_trend where year=2021"
    ).fetchone()[0]

    assert res_prev == [(None,), (2017,)]
    assert res_rolling == 4.7


def test_yearly_trend_range_frame_skips_empty_years(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res_2024_rolling = conn.execute(
        "select rolling_avg from mart_yearly_trend where year=2024"
    ).fetchone()[0]
    res_2024_diff = conn.execute(
        "select diff_year_rating from mart_yearly_trend where year=2024"
    ).fetchone()[0]
    res_2019 = conn.execute(
        "select rolling_avg from mart_yearly_trend where year=2019"
    ).fetchone()[0]
    res_2016 = conn.execute(
        "select diff_year_rating from mart_yearly_trend where year=2016"
    ).fetchone()[0]

    assert res_2024_rolling == 7.07
    assert res_2024_diff == 6.07
    assert res_2019 == 7.15
    assert res_2016 is None


def test_yearly_trend_excludes_unknown_dates_and_nulls(make_gold_db: GoldDbFactory) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute("select sum(shows_count) from mart_yearly_trend").fetchone()[0]

    assert res == 8


def test_yearly_trend_weighted_rolling_avg(make_gold_db: GoldDbFactory) -> None:
    custom_shows = marts_shows.copy()
    custom_shows.loc[custom_shows["show_id"] == 5, "premiered"] = pd.Timestamp("2023-04-11")

    conn = make_gold_db(custom_shows, marts_genre)
    res = conn.execute("select rolling_avg from mart_yearly_trend where year=2024").fetchone()[0]

    assert res == 5.55
