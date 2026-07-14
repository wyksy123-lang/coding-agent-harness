from __future__ import annotations

from pathlib import Path

README_PATH = Path("README.md")

REQUIRED_HEADINGS = [
    "## 项目简介",
    "## 安装",
    "## 运行",
    "## 分发命令",
    "## 目录结构",
    "## 安全边界",
    "## 第三方许可证",
    "## 已知限制",
]

REQUIRED_SNIPPETS = [
    "pip install coding-agent-harness",
    "docker pull <registry>/coding-agent-harness",
    "harness key setup",
    "harness key status",
    "harness key update",
    "harness key clear",
    'harness run "',
    "python -m pip install build twine",
    "docker build -t coding-agent-harness .",
    "docker run -p 8000:8000",
    "harness.yaml.example",
    "keyring",
    ".env",
    "PathGuard",
    "CommandGuard",
    "HITL",
    "httpx",
    "pyyaml",
    "fastapi",
    "uvicorn",
    "websockets",
    "pytest",
    "pytest-json-report",
    "ruff",
    "mypy",
]


def _read_readme() -> str:
    return README_PATH.read_text(encoding="utf-8")


def test_readme_contains_required_sections() -> None:
    readme = _read_readme()

    for heading in REQUIRED_HEADINGS:
        assert heading in readme


def test_readme_documents_install_run_distribution_security_and_licenses() -> None:
    readme = _read_readme()
    readme_lower = readme.lower()

    for snippet in REQUIRED_SNIPPETS:
        assert snippet.lower() in readme_lower


def test_readme_documents_distribution_prerequisites_and_cross_platform_mounts() -> None:
    readme = _read_readme()
    readme_lower = readme.lower()

    assert "python -m pip install build twine" in readme_lower
    assert readme_lower.index("python -m pip install build twine") < readme_lower.index(
        "python -m build"
    )
    assert "${PWD}\\workspace:/app/workspace" in readme
    assert "$(pwd)/workspace:/app/workspace" in readme


def test_readme_does_not_claim_unverified_t28_or_t29_outcomes() -> None:
    readme_lower = _read_readme().lower()

    forbidden_claims = [
        "docker build passed",
        "docker run verified",
        "docker run -e deepseek_api_key",
        "render url:",
        "production deployment is live",
        "published to pypi",
        "published to docker hub",
        "all acceptance criteria pass",
        "ac1-ac25 pass",
        "final acceptance complete",
    ]
    for claim in forbidden_claims:
        assert claim not in readme_lower
