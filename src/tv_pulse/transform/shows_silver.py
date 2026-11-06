import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def read_bronze(path: Path) -> list[dict[str, Any]]:
    logger.info("Start reading bronze shows: %s", path)
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    logger.info("Finish reading bronze shows: %s", path)
    return raw


def build_shows(raw: list[dict[str, Any]]) -> pd.DataFrame:
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
        "show_id": "Int64",
        "weight": "Int64",
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


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Starting main")

    bronze_root = Path("data") / "bronze" / "shows" / "page=0"
    files = sorted(bronze_root.glob("ingested_at=*.json"))
    if len(files) == 0:
        raise FileNotFoundError(
            f"No JSON files found in {bronze_root} matching 'ingested_at=*.json'"
        )
    path = files[-1]

    silver_root = Path("data") / "silver"
    raw = read_bronze(path)
    expected_rows = len(raw)
    shows = build_shows(raw)
    show_genre = build_show_genre(raw)
    validate_silver(shows, show_genre, expected_rows)
    write_silver(shows, show_genre, silver_root)

    logger.info("Pipeline executed successfully")


if __name__ == "__main__":
    main()
