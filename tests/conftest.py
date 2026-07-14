from __future__ import annotations

from pathlib import Path

import pytest

from harness.models import Config


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> str:
    return str(tmp_path)


@pytest.fixture
def mock_config() -> Config:
    return Config()
