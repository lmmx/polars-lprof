# tests/conftest.py
from pathlib import Path

import pytest


@pytest.fixture
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def profile_a_path(fixture_dir: Path) -> Path:
    return fixture_dir / "profile_output_a.txt"


@pytest.fixture
def profile_b_path(fixture_dir: Path) -> Path:
    return fixture_dir / "profile_output_b.txt"