from __future__ import annotations

import tempfile

import pytest

from harness.models import Config


@pytest.fixture
def tmp_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_config():
    return Config()
