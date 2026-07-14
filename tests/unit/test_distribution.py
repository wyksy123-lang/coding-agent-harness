from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any


PYPROJECT_PATH = Path("pyproject.toml")
DOCKERFILE_PATH = Path("Dockerfile")
DOCKERIGNORE_PATH = Path(".dockerignore")


def _load_pyproject() -> dict[str, Any]:
    with PYPROJECT_PATH.open("rb") as pyproject_file:
        loaded = tomllib.load(pyproject_file)
    assert isinstance(loaded, dict)
    return loaded


def test_pyproject_declares_build_backend_console_script_and_packages() -> None:
    pyproject = _load_pyproject()

    assert pyproject["build-system"]["build-backend"] == "setuptools.build_meta"
    assert "setuptools>=68" in pyproject["build-system"]["requires"]
    assert pyproject["project"]["requires-python"] == ">=3.11"
    assert pyproject["project"]["scripts"]["harness"] == "harness.cli:main"

    package_includes = set(pyproject["tool"]["setuptools"]["packages"]["find"]["include"])
    assert {"harness*", "webui*", "demo*"}.issubset(package_includes)


def test_pyproject_includes_webui_static_package_data() -> None:
    package_data = _load_pyproject()["tool"]["setuptools"]["package-data"]
    webui_patterns = set(package_data["webui"])

    assert "static/index.html" in webui_patterns
    assert "static/app.js" in webui_patterns
    assert "static/style.css" in webui_patterns


def test_dockerfile_builds_runtime_webui_without_baked_credentials() -> None:
    dockerfile = DOCKERFILE_PATH.read_text(encoding="utf-8")
    lower_dockerfile = dockerfile.lower()

    assert "FROM python:3.11-slim" in dockerfile
    assert "EXPOSE 8000" in dockerfile
    assert "--host" in dockerfile
    assert "0.0.0.0" in dockerfile
    assert "--port" in dockerfile
    assert "8000" in dockerfile
    assert "webui.app:app" in dockerfile
    assert "localhost" not in lower_dockerfile
    assert not re.search(r"(api[_-]?key|token|password|secret)\s*=", lower_dockerfile)
    assert "C:\\Users" not in dockerfile


def test_dockerignore_excludes_local_state_without_excluding_sources() -> None:
    dockerignore_lines = {
        line.strip()
        for line in DOCKERIGNORE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    required_excludes = {
        ".git",
        ".venv",
        "__pycache__",
        "*.py[cod]",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        "*.egg-info",
        ".env",
        ".env.*",
        "harness.yaml",
        "*.log",
    }
    assert required_excludes.issubset(dockerignore_lines)

    assert "harness" not in dockerignore_lines
    assert "webui" not in dockerignore_lines
    assert "webui/static" not in dockerignore_lines
    assert "demo" not in dockerignore_lines
    assert "pyproject.toml" not in dockerignore_lines
