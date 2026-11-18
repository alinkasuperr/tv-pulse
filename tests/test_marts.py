import sqlite3
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from tv_pulse.gold.sql_runner import run_sql_files

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


def test_marts_factory_builds_gold(
    make_gold_db: Callable[[pd.DataFrame, pd.DataFrame], sqlite3.Connection],
) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute("select count(*) from fact_show_snapshot").fetchone()[0]

    assert res == 10


def test_top_shows_by_genre_known_ranking(
    make_gold_db: Callable[[pd.DataFrame, pd.DataFrame], sqlite3.Connection],
) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute(
        "select name, rating_avg, top_shows from mart_top_shows_by_genre "
        "where genre= 'Horror' order by top_shows"
    ).fetchall()

    assert res == [
        ("Dark9", 9.0, 1),
        ("Dark7", 6.5, 2),
        ("Dark10", 3.2, 3),
    ]


def test_top_shows_by_genre_excludes_null_rating(
    make_gold_db: Callable[[pd.DataFrame, pd.DataFrame], sqlite3.Connection],
) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    res = conn.execute(
        "select count(*) from mart_top_shows_by_genre where show_id = 2"
    ).fetchone()[0]

    assert res == 0


def test_top_shows_by_genre_idempotency(
    make_gold_db: Callable[[pd.DataFrame, pd.DataFrame], sqlite3.Connection],
) -> None:
    conn = make_gold_db(marts_shows, marts_genre)
    marts_dir = Path(__file__).resolve().parents[1] / "sql" / "marts"

    run_sql_files(conn, marts_dir)
    run_sql_files(conn, marts_dir)
