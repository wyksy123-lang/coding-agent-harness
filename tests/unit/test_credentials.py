from __future__ import annotations

import logging
from pathlib import Path

import pytest

from harness.credentials.manager import CredentialManager, KeyringBackend

KEY_NAME = "DEEPSEEK_API_KEY"
KEY_PREFIX = "sk" + "-"
FAKE_KEY = KEY_PREFIX + "unit-test-key-12345678"
UPDATED_KEY = KEY_PREFIX + "updated-unit-test-87654321"
SHORT_KEY = KEY_PREFIX + "abcd"


class FakeKeyring:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def get_password(self, service_name: str, username: str) -> str | None:
        return self.values.get((service_name, username))

    def set_password(self, service_name: str, username: str, password: str) -> None:
        self.values[(service_name, username)] = password

    def delete_password(self, service_name: str, username: str) -> None:
        del self.values[(service_name, username)]


class FailingKeyring:
    def get_password(self, service_name: str, username: str) -> str | None:
        raise RuntimeError("keyring unavailable")

    def set_password(self, service_name: str, username: str, password: str) -> None:
        raise RuntimeError("keyring unavailable")

    def delete_password(self, service_name: str, username: str) -> None:
        raise RuntimeError("keyring unavailable")


class StaleFailingKeyring:
    def __init__(self, key: str) -> None:
        self.key = key

    def get_password(self, service_name: str, username: str) -> str | None:
        return self.key

    def set_password(self, service_name: str, username: str, password: str) -> None:
        raise RuntimeError("keyring write failed")

    def delete_password(self, service_name: str, username: str) -> None:
        raise RuntimeError("keyring delete failed")


def _manager(tmp_path: Path, keyring_backend: KeyringBackend) -> CredentialManager:
    return CredentialManager(
        service_name="unit-test-service",
        env_file=tmp_path / ".env",
        keyring_backend=keyring_backend,
    )


def test_setup_stores_hidden_input_in_keyring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = FakeKeyring()
    manager = _manager(tmp_path, backend)
    monkeypatch.setattr("getpass.getpass", lambda prompt: FAKE_KEY)

    manager.setup()

    assert backend.values[("unit-test-service", KEY_NAME)] == FAKE_KEY
    assert manager.get_key() == FAKE_KEY


def test_status_masks_key_without_plaintext(tmp_path: Path) -> None:
    backend = FakeKeyring()
    backend.set_password("unit-test-service", KEY_NAME, FAKE_KEY)
    manager = _manager(tmp_path, backend)

    status = manager.status()

    assert status == KEY_PREFIX + "****...5678"
    assert FAKE_KEY not in status


def test_status_fully_masks_short_key(tmp_path: Path) -> None:
    backend = FakeKeyring()
    backend.set_password("unit-test-service", KEY_NAME, SHORT_KEY)
    manager = _manager(tmp_path, backend)

    status = manager.status()

    assert status == "****"
    assert SHORT_KEY not in status


def test_update_overwrites_existing_keyring_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = FakeKeyring()
    backend.set_password("unit-test-service", KEY_NAME, FAKE_KEY)
    manager = _manager(tmp_path, backend)
    monkeypatch.setattr("getpass.getpass", lambda prompt: UPDATED_KEY)

    manager.update()

    assert manager.get_key() == UPDATED_KEY


def test_update_uses_env_fallback_after_keyring_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _manager(tmp_path, StaleFailingKeyring(FAKE_KEY))
    monkeypatch.setattr("getpass.getpass", lambda prompt: UPDATED_KEY)

    manager.update()

    assert manager.get_key() == UPDATED_KEY


def test_clear_removes_keyring_key(tmp_path: Path) -> None:
    backend = FakeKeyring()
    backend.set_password("unit-test-service", KEY_NAME, FAKE_KEY)
    manager = _manager(tmp_path, backend)

    manager.clear()

    assert manager.get_key() is None


def test_clear_ignores_stale_keyring_after_delete_failure(tmp_path: Path) -> None:
    manager = _manager(tmp_path, StaleFailingKeyring(FAKE_KEY))

    manager.clear()

    assert manager.get_key() is None


def test_get_key_falls_back_to_env_when_keyring_unavailable(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(f"{KEY_NAME}={FAKE_KEY}\n", encoding="utf-8")
    manager = _manager(tmp_path, FailingKeyring())

    assert manager.get_key() == FAKE_KEY


def test_setup_falls_back_to_env_when_keyring_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    manager = _manager(tmp_path, FailingKeyring())
    monkeypatch.setattr("getpass.getpass", lambda prompt: FAKE_KEY)
    caplog.set_level(logging.WARNING, logger="harness.credentials.manager")

    manager.setup()

    env_contents = (tmp_path / ".env").read_text(encoding="utf-8")
    assert env_contents == f"{KEY_NAME}={FAKE_KEY}\n"
    assert manager.get_key() == FAKE_KEY
    assert "storing key in .env fallback" in caplog.text
    assert FAKE_KEY not in caplog.text


def test_clear_removes_env_key_when_keyring_unavailable(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"OTHER=value\nexport {KEY_NAME} = {FAKE_KEY}\n",
        encoding="utf-8",
    )
    manager = _manager(tmp_path, FailingKeyring())

    manager.clear()

    assert manager.get_key() is None
    assert env_file.read_text(encoding="utf-8") == "OTHER=value\n"


def test_get_key_reads_spaced_export_env_assignment(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(f"export {KEY_NAME} = {FAKE_KEY}\n", encoding="utf-8")
    manager = _manager(tmp_path, FailingKeyring())

    assert manager.get_key() == FAKE_KEY


def test_get_key_returns_none_when_missing(tmp_path: Path) -> None:
    manager = _manager(tmp_path, FakeKeyring())

    assert manager.get_key() is None
