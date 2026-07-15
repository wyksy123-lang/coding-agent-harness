from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

RENDER_PATH = Path("render.yaml")
DOCKERFILE_PATH = Path("Dockerfile")
README_PATH = Path("README.md")


def _load_render_config() -> dict[str, Any]:
    with RENDER_PATH.open(encoding="utf-8") as render_file:
        loaded = yaml.safe_load(render_file)
    assert isinstance(loaded, dict)
    return loaded


def _web_service() -> dict[str, Any]:
    config = _load_render_config()
    services = config.get("services")
    assert isinstance(services, list)
    assert len(services) == 1
    service = services[0]
    assert isinstance(service, dict)
    return service


def test_render_yaml_declares_free_docker_web_service() -> None:
    service = _web_service()

    assert service["type"] == "web"
    assert service["runtime"] == "docker"
    assert service["plan"] == "free"
    assert service["dockerfilePath"] == "./Dockerfile"
    assert service["dockerContext"] == "."
    assert service["healthCheckPath"] == "/"
    assert service["autoDeployTrigger"] == "checksPass"


def test_render_yaml_uses_environment_injection_without_plaintext_credentials() -> None:
    service = _web_service()
    env_vars = service.get("envVars")
    assert isinstance(env_vars, list)

    deepseek_key = next(
        env_var
        for env_var in env_vars
        if isinstance(env_var, dict) and env_var["key"] == "DEEPSEEK_API_KEY"
    )
    assert deepseek_key == {"key": "DEEPSEEK_API_KEY", "sync": False}

    raw_config = RENDER_PATH.read_text(encoding="utf-8")
    assert not re.search(r"(api[_-]?key|token|password|secret)\s*:\s*\S+", raw_config, re.I)
    assert "sk-" not in raw_config


def test_dockerfile_binds_webui_to_render_port_env_with_local_fallback() -> None:
    dockerfile = DOCKERFILE_PATH.read_text(encoding="utf-8")

    assert "--host" in dockerfile
    assert "0.0.0.0" in dockerfile
    assert "--port" in dockerfile
    assert "${PORT:-8000}" in dockerfile
    assert "webui.app:app" in dockerfile


def test_readme_documents_verified_render_url_without_final_acceptance_claims() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    readme_lower = readme.lower()

    assert "render deployment" in readme_lower
    assert "docker web service" in readme_lower
    assert "render.yaml" in readme_lower
    assert "checks pass" in readme_lower
    assert "https://coding-agent-harness-zq0k.onrender.com/" in readme
    assert "checked_at_utc=2026-07-15T03:05:17Z" in readme
    assert "GET / -> 200" in readme
    assert "text/html" in readme_lower
    assert "length 1647" in readme_lower
    assert "GET /static/style.css -> 200" in readme
    assert "text/css" in readme_lower
    assert "length 1453" in readme_lower
    assert "GET /static/app.js -> 200" in readme
    assert "application/javascript" in readme_lower
    assert "length 6538" in readme_lower
    assert "Coding Agent Harness" in readme
    assert "HITL" in readme
    assert "/static/style.css" in readme
    assert "/static/app.js" in readme
    assert "secret_pattern_match=False" in readme
    assert "live deployment pending" not in readme_lower
    assert "does not include a render service url" not in readme_lower
    assert "production deployment is live" not in readme_lower
    assert "all acceptance criteria pass" not in readme_lower
    assert "final acceptance complete" not in readme_lower
