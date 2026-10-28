import json
from datetime import date
from pathlib import Path

from tv_pulse.ingest.shows import save_page

test_data = [
    {
        "id": 1,
        "url": "https://www.tvmaze.com/shows/1/under-the-dome",
        "name": "Ключ",
    },
    {"id": 2, "name": "Under the Dome", "type": "Scripted", "language": "English"},
]
test_date = date(2026, 1, 1)


def test_path(tmp_path: Path) -> None:
    saved_path = save_page(data=test_data, page=3, ingested_at=test_date, bronze_root=tmp_path)
    expected_path = tmp_path / "shows" / "page=3" / "ingested_at=2026-01-01.json"

    assert saved_path.exists()
    assert saved_path == expected_path


def test_content(tmp_path: Path) -> None:
    saved_path = save_page(data=test_data, page=3, ingested_at=test_date, bronze_root=tmp_path)

    with open(saved_path, encoding="utf-8") as f:
        loaded_data = json.load(f)

    assert loaded_data == test_data


def test_idempotence(tmp_path: Path) -> None:
    save_page(data=test_data, page=3, ingested_at=test_date, bronze_root=tmp_path)
    save_page(data=test_data, page=3, ingested_at=test_date, bronze_root=tmp_path)

    json_files = list(tmp_path.glob("**/*.json"))

    assert len(json_files) == 1
