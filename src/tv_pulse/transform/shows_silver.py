import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from tv_pulse.config import BRONZE_DIR, SILVER_DIR

logger = logging.getLogger(__name__)


def read_bronze(path: Path) -> list[dict[str, Any]]:
    logger.info("Start reading bronze shows: %s", path)
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    logger.info("Finish reading bronze shows: %s", path)
    return raw


def build_shows(raw: list[dict[str, Any]], ingested_at: date) -> pd.DataFrame:
    logger.info("Start building shows: %s", len(raw))
    shows = pd.json_normalize(raw)

    needed_cols = [
        "id",
        "name",
        "runtime",
        "rating.average",
        "network.name",
        "network.country.name",
        "weight",
        "type",
        "language",
        "status",
        "premiered",
        "ended",
        "url",
        "averageRuntime",
        "updated",
        "externals.imdb",
    ]

    shows = shows[needed_cols].copy()

    shows = shows.rename(
        columns={
            "id": "show_id",
            "runtime": "runtime_min",
            "rating.average": "rating_avg",
            "network.name": "network_name",
            "network.country.name": "network_country",
            "externals.imdb": "imdb_id",
            "updated": "updated_at",
            "averageRuntime": "average_runtime_min",
        },
        errors="raise",
    )

    cols_to_convert = {
        "show_id": "int64",
        "weight": "int64",
        "language": "category",
        "runtime_min": "Int64",
        "type": "category",
        "status": "category",
    }

    shows = shows.astype(cols_to_convert)

    cols_to_convert_date = ["premiered", "ended"]
    shows[cols_to_convert_date] = shows[cols_to_convert_date].apply(
        pd.to_datetime, errors="coerce"
    )
    shows["ingested_at"] = pd.Timestamp(ingested_at).as_unit("us")

    shows["updated_at"] = pd.to_datetime(shows["updated_at"], unit="s", errors="coerce")
    shows["updated_at"] = shows["updated_at"].astype("datetime64[us]")

    logger.info("Finish building shows: %s", shows.shape)

    return shows


def build_show_genre(raw: list[dict[str, Any]]) -> pd.DataFrame:
    logger.info("Start building show genre")
    shows = pd.DataFrame(raw)
    show_genre = shows[["id", "genres"]].copy()

    show_genre = show_genre.explode("genres")
    show_genre = show_genre.dropna(subset=["genres"]).drop_duplicates()

    show_genre = show_genre.rename(columns={"genres": "genre", "id": "show_id"}).reset_index(
        drop=True
    )
    logger.info("Finish building show genre: %s", show_genre.shape)

    return show_genre


def validate_silver(shows: pd.DataFrame, show_genre: pd.DataFrame, expected_rows: int) -> None:
    logger.info(
        "Start validating silver shows: %s. Show_genre: %s. Expected_rows: %s.",
        shows.shape,
        show_genre.shape,
        expected_rows,
    )

    if not shows.columns.is_unique:
        raise ValueError("DataFrame columns are not unique (duplicates found)")
    if not shows["show_id"].is_unique:
        raise ValueError("ID show non unique")
    if expected_rows != len(shows):
        raise ValueError(f"Issues: Expected {expected_rows} rows, but got {len(shows)}")
    if not shows["name"].notna().all():
        raise ValueError("Column 'name' contains missing (NaN) values")
    if not shows["ingested_at"].notna().all():
        raise ValueError("Column 'ingested_at' contains missing (NaN) values")
    if not shows["rating_avg"].dropna().between(0, 10).all():
        raise ValueError("Ratings out of range [0, 10] found")
    if show_genre.duplicated(subset=["show_id", "genre"]).sum() != 0:
        raise ValueError("Duplicate show-genre pairs found")
    if not show_genre["show_id"].isin(shows["show_id"]).all():
        raise ValueError("Show genre contains show_id values missing from shows")

    logger.info("Finish validating silver shows: %s", shows.shape)


def write_silver(shows: pd.DataFrame, show_genre: pd.DataFrame, silver_root: Path) -> None:
    logger.info(
        "Start writing silver shows: %s. Show_genre: %s. Silver_root: %s",
        shows.shape,
        show_genre.shape,
        silver_root,
    )
    silver_root.mkdir(parents=True, exist_ok=True)
    shows.to_parquet(silver_root / "shows.parquet", engine="pyarrow")
    show_genre.to_parquet(silver_root / "show_genre.parquet", engine="pyarrow")

    logger.info("Finish writing silver shows")


def parse_ingested_at(path: Path) -> date:
    file_name = path.stem
    if not file_name.startswith("ingested_at="):
        raise ValueError(f"Incorrect file name: {file_name}")

    date_str = file_name.removeprefix("ingested_at=")

    try:
        return date.fromisoformat(date_str)
    except ValueError as err:
        raise ValueError(f"Incorrect date format in file name: {file_name}") from err


def read_latest_bronze(bronze_root: Path) -> tuple[list[dict[str, Any]], date]:
    files = sorted((bronze_root / "shows").glob("page=*/ingested_at=*.json"))
    if not files:
        raise FileNotFoundError(
            f"No JSON files found in {bronze_root / 'shows'} matching 'page=*/ingested_at=*.json'"
        )

    file_dates = {f: parse_ingested_at(f) for f in files}
    latest_date = max(file_dates.values())
    latest_files = [f for f, d in file_dates.items() if d == latest_date]

    latest_files = sorted(
        latest_files,
        key=lambda f: int(f.parent.name.removeprefix("page=")),
    )

    page_numbers = [int(f.parent.name.removeprefix("page=")) for f in latest_files]
    expected_pages = set(range(len(page_numbers)))
    missing_pages = sorted(expected_pages - set(page_numbers))
    if missing_pages:
        raise ValueError(
            f"Missing page numbers for {latest_date}: {missing_pages} "
            f"(found pages: {page_numbers})"
        )

    # Ensure the latest snapshot contains all page directories seen across history
    all_pages = {f.parent.name for f in files}
    latest_pages = {f.parent.name for f in latest_files}
    if latest_pages != all_pages:
        raise ValueError(
            f"Page mismatch for {latest_date}: found {sorted(latest_pages)}, "
            f"but history has {sorted(all_pages)}. Re-run ingestion or remove old dates."
        )

    all_raw: list[dict[str, Any]] = []
    for f in latest_files:
        page_shows = read_bronze(f)
        all_raw.extend(page_shows)

    return all_raw, latest_date


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Starting main")

    raw, ingested_at = read_latest_bronze(BRONZE_DIR)
    expected_rows = len(raw)
    shows = build_shows(raw, ingested_at)
    show_genre = build_show_genre(raw)
    validate_silver(shows, show_genre, expected_rows)
    write_silver(shows, show_genre, SILVER_DIR)

    logger.info("Pipeline executed successfully")


if __name__ == "__main__":
    main()
