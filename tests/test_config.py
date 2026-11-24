import subprocess
import sys
from pathlib import Path

import pytest

from tv_pulse.config import (
    BRONZE_DIR,
    CHECKS_SQL_DIR,
    GOLD_DB_PATH,
    GOLD_SQL_DIR,
    MARTS_SQL_DIR,
    PROJECT_ROOT,
    SILVER_DIR,
)


def test_config_project_root_contains_pyproject() -> None:
    assert (PROJECT_ROOT / "pyproject.toml").is_file()


@pytest.mark.parametrize(
    "path",
    [
        PROJECT_ROOT,
        BRONZE_DIR,
        SILVER_DIR,
        GOLD_DB_PATH,
        GOLD_SQL_DIR,
        CHECKS_SQL_DIR,
        MARTS_SQL_DIR,
    ],
)
def test_config_paths_are_absolute(path: Path) -> None:
    assert path.is_absolute()


def test_config_independence_in_subprocess(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from tv_pulse.config import GOLD_SQL_DIR; print(GOLD_SQL_DIR.is_dir())",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "True"


@pytest.mark.parametrize("sql_dir", [GOLD_SQL_DIR, CHECKS_SQL_DIR, MARTS_SQL_DIR])
def test_config_sql_dirs_exist_and_not_empty(sql_dir: Path) -> None:
    assert sql_dir.is_dir()
    assert any(sql_dir.glob("*.sql"))
