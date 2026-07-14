from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

GITLAB_CI_PATH = Path(".gitlab-ci.yml")


def _load_gitlab_ci() -> dict[str, Any]:
    with GITLAB_CI_PATH.open(encoding="utf-8") as gitlab_ci_file:
        loaded = yaml.safe_load(gitlab_ci_file)
    assert isinstance(loaded, dict)
    return loaded


def test_gitlab_ci_defines_unit_test_job() -> None:
    config = _load_gitlab_ci()

    assert "unit-test" in config
    assert isinstance(config["unit-test"], dict)


def test_gitlab_ci_unit_test_uses_python_image_and_pip_cache() -> None:
    job = _load_gitlab_ci()["unit-test"]

    assert job["image"] == "python:3.11"
    assert job["variables"]["PIP_CACHE_DIR"] == "$CI_PROJECT_DIR/.cache/pip"
    assert ".cache/pip" in job["cache"]["paths"]


def test_gitlab_ci_unit_test_installs_dependencies_and_runs_make_test() -> None:
    job = _load_gitlab_ci()["unit-test"]

    assert job["before_script"] == [
        "python -m pip install --upgrade pip",
        "python -m pip install -e .",
    ]
    assert job["script"] == ["make test"]
