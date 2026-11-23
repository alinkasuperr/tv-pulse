import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

import requests

from tv_pulse.config import BASE_URL, BRONZE_DIR, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


def get_page(page: int) -> list[dict[str, Any]]:
    logger.info("Starting to fetch show page: %s", page)
    response = requests.get(f"{BASE_URL}/shows?page={page}", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    logger.info(
        "Successfully fetched page %s. Status: %s. Received %s shows.",
        page,
        response.status_code,
        len(data),
    )
    return data


def save_page(data: list[dict[str, Any]], page: int, ingested_at: date, bronze_root: Path) -> Path:
    logger.info("Saving page start")
    dir_path = bronze_root / "shows" / f"page={page}"
    file_path = dir_path / f"ingested_at={ingested_at}.json"
    dir_path.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    logger.info("Successfully saved page %s to path: %s", page, file_path)
    return file_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Loading page start")

    current_date = date.today()
    show = get_page(0)
    saved_path = save_page(data=show, page=0, ingested_at=current_date, bronze_root=BRONZE_DIR)
    logger.info("Pipeline executed successfully. Output saved to: %s", saved_path)


if __name__ == "__main__":
    main()
