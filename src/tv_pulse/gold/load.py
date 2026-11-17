import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_silver_to_sqlite(silver_root: Path, conn: sqlite3.Connection) -> None:
    logger.info("Loading silver to sqlite")

    path_shows = silver_root / "shows.parquet"
    path_show_genre = silver_root / "show_genre.parquet"

    if not path_shows.exists():
        raise FileNotFoundError(f"Missing required silver file: {path_shows}")
    if not path_show_genre.exists():
        raise FileNotFoundError(f"Missing required silver file: {path_show_genre}")

    shows = pd.read_parquet(path_shows)
    show_genre = pd.read_parquet(path_show_genre)

    shows.to_sql("silver_shows", con=conn, if_exists="replace", index=False)
    show_genre.to_sql("silver_show_genre", con=conn, if_exists="replace", index=False)

    logger.info(
        "Load silver to sqlite is finished. Loaded rows: shows=%s, genres=%s",
        shows.shape[0],
        show_genre.shape[0],
    )
