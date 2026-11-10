import logging
import sqlite3
from contextlib import closing
from pathlib import Path

from tv_pulse.gold.load import load_silver_to_sqlite

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Start main")

    file_path = Path("data") / "gold" / "tv_pulse.db"
    dir_path = Path("data") / "gold"

    dir_path.mkdir(parents=True, exist_ok=True)

    silver_root = Path("data") / "silver"

    with closing(sqlite3.connect(file_path)) as conn:
        load_silver_to_sqlite(silver_root, conn)

    logger.info("Finish main")


if __name__ == "__main__":
    main()
