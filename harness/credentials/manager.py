from __future__ import annotations

import getpass
import logging
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

DEFAULT_SERVICE_NAME = "coding-agent-harness"
DEFAULT_KEY_NAME = "DEEPSEEK_API_KEY"

logger = logging.getLogger(__name__)


class KeyringBackend(Protocol):
    def get_password(self, service_name: str, username: str) -> str | None: ...

    def set_password(self, service_name: str, username: str, password: str) -> None: ...

    def delete_password(self, service_name: str, username: str) -> None: ...


class CredentialManager:
    """Manage API keys through keyring with a plaintext .env fallback."""

    def __init__(
        self,
        service_name: str = DEFAULT_SERVICE_NAME,
        *,
        key_name: str = DEFAULT_KEY_NAME,
        env_file: str | Path = ".env",
        keyring_backend: KeyringBackend | None = None,
    ) -> None:
        self.service_name = service_name
        self.key_name = key_name
        self.env_file = Path(env_file)
        self._keyring = keyring_backend if keyring_backend is not None else _load_keyring_backend()

    def setup(self) -> None:
        """Prompt for an API key and store it."""
        self._store_key(self._prompt_key())

    def status(self) -> str:
        """Return masked credential status without exposing the plaintext key."""
        key = self.get_key()
        if key is None:
            return "not configured"
        return _mask_key(key)

    def update(self) -> None:
        """Prompt for an API key and overwrite the stored value."""
        self._store_key(self._prompt_key())

    def clear(self) -> None:
        """Clear the stored key from keyring and the fallback .env file."""
        self._delete_keyring_key()
        self._remove_env_key()

    def get_key(self) -> str | None:
        """Return the configured API key, preferring keyring over .env."""
        keyring_key = self._get_keyring_key()
        if keyring_key:
            return keyring_key
        return self._read_env_key()

    def _prompt_key(self) -> str:
        return getpass.getpass("DeepSeek API key: ")

    def _store_key(self, key: str) -> None:
        if self._set_keyring_key(key):
            return
        self._write_env_key(key)

    def _get_keyring_key(self) -> str | None:
        if self._keyring is None:
            logger.warning("Keyring backend unavailable; using .env fallback.")
            return None
        try:
            return self._keyring.get_password(self.service_name, self.key_name)
        except Exception:
            logger.warning("Keyring read failed; using .env fallback.")
            return None

    def _set_keyring_key(self, key: str) -> bool:
        if self._keyring is None:
            logger.warning("Keyring backend unavailable; storing key in .env fallback.")
            return False
        try:
            self._keyring.set_password(self.service_name, self.key_name, key)
        except Exception:
            logger.warning("Keyring write failed; storing key in .env fallback.")
            return False
        return True

    def _delete_keyring_key(self) -> None:
        if self._keyring is None:
            logger.warning("Keyring backend unavailable; clearing .env fallback.")
            return
        try:
            self._keyring.delete_password(self.service_name, self.key_name)
        except Exception:
            logger.warning("Keyring delete failed or key was absent; clearing .env fallback.")

    def _read_env_key(self) -> str | None:
        if not self.env_file.exists():
            return None
        for line in self.env_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            name, separator, value = stripped.partition("=")
            if separator and name == self.key_name:
                return value
        return None

    def _write_env_key(self, key: str) -> None:
        lines = self._env_lines_without_key()
        lines.append(f"{self.key_name}={key}")
        self.env_file.parent.mkdir(parents=True, exist_ok=True)
        self.env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _remove_env_key(self) -> None:
        if not self.env_file.exists():
            return
        lines = self._env_lines_without_key()
        if lines:
            self.env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            self.env_file.write_text("", encoding="utf-8")

    def _env_lines_without_key(self) -> list[str]:
        if not self.env_file.exists():
            return []
        kept_lines: list[str] = []
        for line in self.env_file.read_text(encoding="utf-8").splitlines():
            name, separator, _value = line.strip().partition("=")
            if separator and name == self.key_name:
                continue
            kept_lines.append(line)
        return kept_lines


def _load_keyring_backend() -> KeyringBackend | None:
    try:
        return cast(KeyringBackend, import_module("keyring"))
    except ImportError:
        return None


def _mask_key(key: str) -> str:
    if len(key) < 7:
        return "****"
    return f"{key[:3]}****...{key[-4:]}"
