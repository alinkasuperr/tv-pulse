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
    MAX_ATTEMPTS,
    MAX_PAGES,
    REQUEST_PAUSE,
    REQUEST_TIMEOUT,
    RETRY_BASE_PAUSE,
    USER_AGENT,
)

logger = logging.getLogger(__name__)


class PageFetchError(Exception):
    def __init__(self, page: int, max_attempts: int, last_error: str) -> None:
        self.page = page
        self.max_retries = max_attempts
        self.last_error = last_error
        message = (
            f"Failed to fetch page {page} after {max_attempts} attempts (last error: {last_error})"
        )
        super().__init__(message)


def get_page(
    page: int,
    session: requests.Session,
    max_attempts: int = MAX_ATTEMPTS,
    base_pause: float = RETRY_BASE_PAUSE,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]] | None:
    if max_attempts < 1:
        raise ValueError(f"max_attempts must be at least 1, got {max_attempts}")

    logger.info("Starting to fetch show page: %s", page)
    last_error = "unknown"

    for attempt in range(max_attempts):
        try:
            response = session.get(f"{BASE_URL}/shows?page={page}", timeout=REQUEST_TIMEOUT)
        except (requests.Timeout, requests.ConnectionError) as err:
            last_error = str(err)
        else:
            if response.status_code == 404:
                return None
            if response.status_code == 429 or 500 <= response.status_code < 600:
                last_error = f"HTTP {response.status_code}"
            else:
                response.raise_for_status()
                data = response.json()
                logger.info(
                    "Successfully fetched page %s. Status: %s. Received %s shows.",
                    page,
                    response.status_code,
                    len(data),
                )
                return data

        logger.warning(
            "Failed to fetch page %s (attempt %s/%s): %s",
            page,
            attempt + 1,
            max_attempts,
            last_error,
        )
        if attempt < max_attempts - 1:
            sleep_fn(base_pause * (2**attempt))

    raise PageFetchError(page=page, max_attempts=max_attempts, last_error=last_error)


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
