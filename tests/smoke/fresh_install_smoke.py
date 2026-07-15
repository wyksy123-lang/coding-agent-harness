from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import venv
from pathlib import Path


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_executable(venv_dir: Path, name: str) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / f"{name}.exe"
    return venv_dir / "bin" / name


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        print(f"command_failed={' '.join(command)}")
        print(f"exit_code={completed.returncode}")
        print(completed.stdout)
        completed.check_returncode()
    return completed


def _wait_for_http_200(url: str, timeout_seconds: float = 20.0) -> bytes:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return response.read()
        except Exception as exc:  # pragma: no cover - only used for retry diagnostics
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"{url} did not return HTTP 200 before timeout: {last_error}")


def run_smoke(wheel: Path) -> None:
    if not wheel.is_file():
        raise FileNotFoundError(f"wheel not found: {wheel}")
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError(f"fresh install smoke requires Python 3.11, got {sys.version}")

    temp_root = Path(tempfile.mkdtemp(prefix="coding-agent-harness-fresh-"))
    process: subprocess.Popen[str] | None = None
    try:
        venv_dir = temp_root / "venv"
        work_dir = temp_root / "outside-repo"
        work_dir.mkdir()

        venv.EnvBuilder(with_pip=True).create(venv_dir)
        python = _venv_python(venv_dir)
        harness = _venv_executable(venv_dir, "harness")

        _run([str(python), "-m", "pip", "install", str(wheel.resolve())], cwd=work_dir)
        _run(
            [
                str(python),
                "-c",
                (
                    "import harness, webui, demo; "
                    "print(harness.__name__, webui.__name__, demo.__name__)"
                ),
            ],
            cwd=work_dir,
        )
        _run([str(harness), "--help"], cwd=work_dir)
        _run([str(python), "-m", "demo.run_demo"], cwd=work_dir)
        _run([str(python), "-m", "pip", "check"], cwd=work_dir)

        process = subprocess.Popen(
            [
                str(python),
                "-m",
                "uvicorn",
                "webui.app:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8765",
            ],
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        root = _wait_for_http_200("http://127.0.0.1:8765/")
        style = _wait_for_http_200("http://127.0.0.1:8765/static/style.css")
        script = _wait_for_http_200("http://127.0.0.1:8765/static/app.js")

        if b"Coding Agent Harness" not in root:
            raise RuntimeError("installed WebUI root did not contain expected marker")
        if not style or not script:
            raise RuntimeError("installed WebUI static resources were empty")

        print(f"fresh_install_root_status=200 length={len(root)}")
        print(f"fresh_install_style_status=200 length={len(style)}")
        print(f"fresh_install_script_status=200 length={len(script)}")
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        shutil.rmtree(temp_root, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run fresh wheel install smoke checks.")
    parser.add_argument("--wheel", required=True, type=Path)
    args = parser.parse_args()
    run_smoke(args.wheel)


if __name__ == "__main__":
    main()
