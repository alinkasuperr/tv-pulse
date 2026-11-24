import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from tv_pulse.transform.shows_silver import (
    build_show_genre,
    build_shows,
    parse_ingested_at,
    read_bronze,
    read_latest_bronze,
    validate_silver,
    write_silver,
)

RAW_SHOWS = [
    {
        "id": 1,
        "name": "Under the Dome",
        "runtime": 60,
        "rating": {"average": 6.5},
        "network": {"name": "CBS", "country": {"name": "United States"}},
        "weight": 98,
        "type": "Scripted",
        "language": "English",
        "status": "Ended",
        "premiered": "2013-06-24",
        "ended": "2015-09-10",
        "url": "https://tvmaze.com",
        "averageRuntime": 60,
        "updated": 1700000000,
        "externals": {"imdb": "tt1553656"},
        "genres": ["Drama", "Science-Fiction", "Thriller"],
    },
    {
        "id": 2,
        "name": "Person of Interest",
        "runtime": 45,
        "rating": {"average": None},
        "network": {"name": "CBS", "country": {"name": "United States"}},
        "weight": 95,
        "type": "Scripted",
        "language": "English",
        "status": "Ended",
        "premiered": "2011-09-22",
        "ended": "2016-06-21",
        "url": "https://tvmaze.com",
        "averageRuntime": 45,
        "updated": 1700000001,
        "externals": {"imdb": "tt1839578"},
        "genres": [],
    },
    {
        "id": 3,
        "name": "Хлопці",
        "runtime": 60,
        "rating": {"average": 8.7},
        "network": None,
        "weight": 99,
        "type": "Scripted",
        "language": "English",
        "status": "Running",
        "premiered": "2019-07-26",
        "ended": None,
        "url": "https://tvmaze.com",
        "averageRuntime": 60,
        "updated": 1700000002,
        "externals": {"imdb": "tt1190634"},
        "genres": ["Action", "Sci-Fi"],
    },
]


@pytest.fixture
def shows() -> pd.DataFrame:
    return build_shows(RAW_SHOWS, date(2026, 10, 28))


def test_build_shows_keeps_all_rows(shows: pd.DataFrame) -> None:
    assert len(shows) == 3


def test_build_shows_columns_are_unique(shows: pd.DataFrame) -> None:
    assert shows.columns.is_unique


def test_build_shows_column_types(shows: pd.DataFrame) -> None:
    assert str(shows["runtime_min"].dtype) == "Int64"
    assert str(shows["rating_avg"].dtype) == "float64"
    assert (shows[["type", "language", "status"]].dtypes == "category").all()
    assert (
        shows[["ended", "premiered", "updated_at"]]
        .apply(pd.api.types.is_datetime64_any_dtype)
        .all()
    )


def test_build_shows_missing_values_stay_missing(shows: pd.DataFrame) -> None:
    assert shows.loc[shows["show_id"] == 2, "rating_avg"].isna().item()
    assert shows.loc[shows["show_id"] == 3, "network_name"].isna().item()


def test_build_shows_id_is_unique(shows: pd.DataFrame) -> None:
    assert shows["show_id"].is_unique


def test_build_shows_converts_timestamp_correctly(shows: pd.DataFrame) -> None:
    actual_time = shows.loc[shows["show_id"] == 1, "updated_at"].item()
    expected_time = pd.Timestamp("2023-11-14 22:13:20")
    assert actual_time == expected_time


def test_build_shows_includes_ingested_at(shows: pd.DataFrame) -> None:
    assert "ingested_at" in shows.columns

    expected_timestamp = pd.Timestamp("2026-10-28")
    assert (shows["ingested_at"] == expected_timestamp).all()
    assert pd.api.types.is_datetime64_any_dtype(shows["ingested_at"])


def test_build_shows_all_data_the_same(shows: pd.DataFrame) -> None:
    cols = ["premiered", "ended", "updated_at", "ingested_at"]
    assert shows[cols].dtypes.nunique() == 1


@pytest.fixture
def show_genre() -> pd.DataFrame:
    return build_show_genre(RAW_SHOWS)


def test_build_show_genre_has_expected_columns(
    show_genre: pd.DataFrame,
) -> None:
    assert show_genre.columns.tolist() == ["show_id", "genre"]


def test_build_show_genre_has_one_row_per_pair(
    show_genre: pd.DataFrame,
) -> None:
    assert len(show_genre) == 5


def test_build_show_genre_skips_shows_without_genres(
    show_genre: pd.DataFrame,
) -> None:
    assert not show_genre["show_id"].isin([2]).any()


def test_build_show_genre_has_no_orphans(show_genre: pd.DataFrame, shows: pd.DataFrame) -> None:
    assert show_genre["show_id"].isin(shows["show_id"]).all()


def test_build_show_genre_removes_duplicate_genres() -> None:
    duplicate_raw = [{"id": 1, "genres": ["Drama", "Drama"]}]
    result_df = build_show_genre(duplicate_raw)
    assert len(result_df) == 1
    assert result_df.loc[0, "genre"] == "Drama"


def test_validate_silver_success(shows: pd.DataFrame, show_genre: pd.DataFrame) -> None:
    validate_silver(shows, show_genre, 3)


def test_validate_silver_duplicate_shows(shows: pd.DataFrame, show_genre: pd.DataFrame) -> None:
    shows_with_duplicate = pd.concat([shows, shows.iloc[[0]]], ignore_index=True)
    expected_rows = len(shows)
    with pytest.raises(ValueError, match="ID show non unique"):
        validate_silver(shows_with_duplicate, show_genre, expected_rows)


def test_validate_silver_invalid_rows_count(shows: pd.DataFrame, show_genre: pd.DataFrame) -> None:
    expected_rows = 4
    with pytest.raises(ValueError, match="Issues: Expected 4 rows"):
        validate_silver(shows, show_genre, expected_rows)


def test_validate_silver_invalid_show_id_in_genre(
    shows: pd.DataFrame, show_genre: pd.DataFrame
) -> None:
    orphan_row = pd.DataFrame({"show_id": 99, "genre": ["Sci-Fi"]})
    show_genre_with_orphan = pd.concat([show_genre, orphan_row], ignore_index=True)
    expected_error = "Show genre contains show_id values missing from shows"
    with pytest.raises(ValueError, match=expected_error):
        validate_silver(shows, show_genre_with_orphan, expected_rows=3)


@pytest.mark.parametrize(
    ("corrupt_fn", "expected_match"),
    [
        (
            lambda s, g: (s.assign(name=s["name"].mask(s.index == 0, None)), g),
            "contains missing",
        ),
        (
            lambda s, g: (s.assign(rating_avg=s["rating_avg"].mask(s.index == 0, 11.0)), g),
            "out of range",
        ),
        (
            lambda s, g: (s, pd.concat([g, g.iloc[[0]]], ignore_index=True)),
            "Duplicate show-genre pairs",
        ),
        (
            lambda s, g: (s.rename(columns={"url": "name"}), g),
            "columns are not unique",
        ),
        (
            lambda s, g: (s.assign(ingested_at=s["ingested_at"].mask(s.index == 0, None)), g),
            "ingested_at",
        ),
    ],
    ids=[
        "missing_name",
        "rating_out_of_range",
        "duplicate_genre_pair",
        "duplicate_columns",
        "missing_ingested_at",
    ],
)
def test_validate_silver_validation_errors(
    shows: pd.DataFrame,
    show_genre: pd.DataFrame,
    corrupt_fn,
    expected_match,
) -> None:
    corrupted_shows, corrupted_genre = corrupt_fn(shows.copy(), show_genre.copy())
    expected_rows = len(corrupted_shows)
    with pytest.raises(ValueError, match=expected_match):
        validate_silver(corrupted_shows, corrupted_genre, expected_rows)


def test_read_bronze(tmp_path: Path) -> None:
    file_path = tmp_path / "test_shows.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(RAW_SHOWS, f, ensure_ascii=False, indent=4)

    result = read_bronze(file_path)
    assert RAW_SHOWS == result
    assert result[2]["name"] == "Хлопці"


def test_write_silver(shows: pd.DataFrame, show_genre: pd.DataFrame, tmp_path: Path) -> None:
    write_silver(shows, show_genre, silver_root=tmp_path)
    shows_parquet_path = tmp_path / "shows.parquet"
    genre_parquet_path = tmp_path / "show_genre.parquet"

    assert shows_parquet_path.exists()
    assert genre_parquet_path.exists()

    imported_shows = pd.read_parquet(shows_parquet_path)
    imported_genre = pd.read_parquet(genre_parquet_path)

    pd.testing.assert_frame_equal(imported_shows, shows)
    pd.testing.assert_frame_equal(imported_genre, show_genre)


@pytest.mark.parametrize(
    ("invalid_path_str", "expected_match"),
    [
        ("data/shows.json", "shows"),
        ("data/ingested_at_2026-10-28.json", "ingested_at_2026-10-28"),
        ("data/ingested_at=abc.json", "ingested_at=abc"),
        ("data/ingested_at=2026-15-40.json", "ingested_at=2026-15-40"),
    ],
    ids=["no_prefix", "wrong_separator", "text_instead_of_date", "invalid_calendar_date"],
)
def test_parse_ingested_at_invalid_path(invalid_path_str: str, expected_match: str) -> None:
    invalid_path = Path(invalid_path_str)
    with pytest.raises(ValueError, match=expected_match):
        parse_ingested_at(invalid_path)


def test_parse_ingested_at() -> None:
    valid_path = Path("data/bronze/shows/page=0/ingested_at=2026-10-28.json")
    expected_date = date(2026, 10, 28)

    result = parse_ingested_at(valid_path)

    assert result == expected_date
    assert isinstance(result, date)


def _write_json(path: Path, payload: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_read_latest_bronze_merges_pages(tmp_path: Path) -> None:
    _write_json(tmp_path / "shows" / "page=0" / "ingested_at=2026-01-01.json", RAW_SHOWS[:2])
    _write_json(tmp_path / "shows" / "page=1" / "ingested_at=2026-01-01.json", RAW_SHOWS[2:])

    raw, ingested_at = read_latest_bronze(tmp_path)

    assert ingested_at == date(2026, 1, 1)
    assert raw == RAW_SHOWS


def test_read_latest_bronze_picks_latest_date(tmp_path: Path) -> None:
    _write_json(tmp_path / "shows" / "page=0" / "ingested_at=2026-01-01.json", RAW_SHOWS[:1])
    _write_json(tmp_path / "shows" / "page=0" / "ingested_at=2026-01-02.json", RAW_SHOWS[1:])

    raw, ingested_at = read_latest_bronze(tmp_path)

    assert ingested_at == date(2026, 1, 2)
    assert raw == RAW_SHOWS[1:]


def test_read_latest_bronze_sorts_pages_numerically(tmp_path: Path) -> None:
    for page_num in range(12):
        _write_json(
            tmp_path / "shows" / f"page={page_num}" / "ingested_at=2026-01-01.json",
            [{"id": page_num}],
        )

    raw, _ = read_latest_bronze(tmp_path)

    assert [row["id"] for row in raw] == list(range(12))


def test_read_latest_bronze_empty_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_latest_bronze(tmp_path)


def test_read_latest_bronze_raises_on_page_gap(tmp_path: Path) -> None:
    _write_json(tmp_path / "shows" / "page=0" / "ingested_at=2026-01-01.json", RAW_SHOWS[:1])
    _write_json(tmp_path / "shows" / "page=2" / "ingested_at=2026-01-01.json", RAW_SHOWS[1:2])

    with pytest.raises(ValueError, match=r"Missing page numbers.*\[1\]"):
        read_latest_bronze(tmp_path)


def test_read_latest_bronze_raises_on_incomplete_latest_date(tmp_path: Path) -> None:
    _write_json(tmp_path / "shows" / "page=0" / "ingested_at=2026-01-01.json", RAW_SHOWS[:2])
    _write_json(tmp_path / "shows" / "page=1" / "ingested_at=2026-01-01.json", RAW_SHOWS[2:])
    _write_json(tmp_path / "shows" / "page=0" / "ingested_at=2026-01-02.json", RAW_SHOWS[:2])

    with pytest.raises(ValueError, match="Page mismatch"):
        read_latest_bronze(tmp_path)


def test_validate_silver_raises_on_duplicate_id_across_pages(tmp_path: Path) -> None:
    _write_json(tmp_path / "shows" / "page=0" / "ingested_at=2026-01-01.json", RAW_SHOWS)
    _write_json(tmp_path / "shows" / "page=1" / "ingested_at=2026-01-01.json", RAW_SHOWS)

    raw, ingested_at = read_latest_bronze(tmp_path)
    built_shows = build_shows(raw, ingested_at)
    built_genre = build_show_genre(raw)

    with pytest.raises(ValueError, match="ID show non unique"):
        validate_silver(built_shows, built_genre, expected_rows=len(raw))
