import json
import logging
import time
from collections.abc import Callable, Iterator
from datetime import date
from functools import partial
from pathlib import Path
from typing import Any

import requests

from tv_pulse.config import (
    BASE_URL,
    BRONZE_DIR,
    MAX_PAGES,
    REQUEST_PAUSE,
    REQUEST_TIMEOUT,
    USER_AGENT,
)

logger = logging.getLogger(__name__)


def get_page(page: int, session: requests.Session) -> list[dict[str, Any]] | None:
    logger.info("Starting to fetch show page: %s", page)
    response = session.get(f"{BASE_URL}/shows?page={page}", timeout=REQUEST_TIMEOUT)
    # 404 indicates the end of pagination and returns None
    if response.status_code == 404:
        return None
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


def iter_pages(
    fetch_page: Callable[[int], list[dict[str, Any]] | None],
    max_pages: int = MAX_PAGES,
    pause: float = REQUEST_PAUSE,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Iterator[tuple[int, list[dict[str, Any]]]]:
    for page in range(max_pages):
        shows = fetch_page(page)
        # Stop on 404 (None) or an empty page ([]) to avoid unnecessary requests.
        if not shows:
            logger.info("No more pages after page %s", page)
            break
        yield page, shows
        if pause > 0 and page < max_pages - 1:
            sleep_fn(pause)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Loading page start")

    current_date = date.today()
    saved_count = 0
    with requests.Session() as session:
        session.headers.update({"User-Agent": USER_AGENT})
        for page, shows in iter_pages(partial(get_page, session=session)):
            save_page(data=shows, page=page, ingested_at=current_date, bronze_root=BRONZE_DIR)
            saved_count += 1
    logger.info("Pipeline executed successfully. Count of pages: %s", saved_count)


if __name__ == "__main__":
    main()
