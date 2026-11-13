import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest

from tv_pulse.gold.sql_runner import run_sql_files

df_shows = pd.DataFrame(
    [
        {
            "show_id": 1,
            "name": "Stranger Things",
            "premiered": pd.Timestamp("2016-07-15"),
            "ended": pd.Timestamp("2022-03-11"),
            "ingested_at": pd.Timestamp("2026-10-28"),
            "runtime_min": 93,
            "rating_avg": 5.8,
            "network_name": "starlink",
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
            "network_name": "starlink",
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
    ]
)

df_show_genre = pd.DataFrame(
    [
        {"show_id": 1, "genre": "Drama"},
        {"show_id": 1, "genre": "Sci-Fi"},
        {"show_id": 2, "genre": "Sci-Fi"},
        {"show_id": 4, "genre": "Comedy"},
        {"show_id": 4, "genre": "Horror"},
    ]
)


@pytest.fixture
def db_conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def setup_silver_data(tmp_path: Path) -> Path:
    df_shows.to_parquet(tmp_path / "shows.parquet", index=False)
    df_show_genre.to_parquet(tmp_path / "show_genre.parquet", index=False)

    return tmp_path


@pytest.fixture
def gold_conn(db_conn: sqlite3.Connection) -> sqlite3.Connection:
    df_shows.to_sql("silver_shows", db_conn, index=False)
    df_show_genre.to_sql("silver_show_genre", db_conn, index=False)
    sql_dir = Path(__file__).resolve().parents[1] / "sql" / "gold"
    run_sql_files(db_conn, sql_dir)

    return db_conn


@pytest.fixture
def silver_shows_df() -> pd.DataFrame:
    return df_shows.copy()


@pytest.fixture
def silver_show_genre_df() -> pd.DataFrame:
    return df_show_genre.copy()
