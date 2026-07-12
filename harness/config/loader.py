from __future__ import annotations

from pathlib import Path

import yaml

from harness.models import Config


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""


_INT_FIELDS: set[str] = {
    "max_rounds",
    "hitl_timeout_seconds",
    "llm_timeout",
    "pytest_timeout",
    "stuck_threshold",
    "llm_retry_count",
}

_FLOAT_FIELDS: set[str] = {"temperature"}

_STR_FIELDS: set[str] = {
    "target_directory",
    "test_command",
    "model",
    "memory_file",
}

_STR_LIST_FIELDS: set[str] = {
    "enabled_tools",
    "dangerous_command_patterns",
}

_VALID_FIELDS = _INT_FIELDS | _FLOAT_FIELDS | _STR_FIELDS | _STR_LIST_FIELDS


class ConfigLoader:
    """Loads and validates a YAML configuration file into a :class:`Config` object."""

    @staticmethod
    def load(path: str | Path) -> Config:
        """Parse *path* as YAML, validate field types, and return a ``Config``.

        Missing fields are filled with defaults; unknown fields are ignored.
        Any I/O or parse error is wrapped in :class:`ConfigError`.
        """
        path = Path(path)
        try:
            with open(path, encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise ConfigError(f"Config file not found: {path}") from e
        except OSError as e:
            raise ConfigError(f"Cannot read config file {path}: {e}") from e
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML parse error in {path}: {e}") from e

        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise ConfigError(f"Config root must be a YAML mapping, got {type(raw).__name__}")

        config = Config()
        for field_name, value in raw.items():
            if field_name not in _VALID_FIELDS:
                continue
            if field_name in _INT_FIELDS:
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ConfigError(
                        f"{field_name} must be an integer, got {type(value).__name__}"
                    )
                setattr(config, field_name, value)
            elif field_name in _FLOAT_FIELDS:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ConfigError(
                        f"{field_name} must be a number, got {type(value).__name__}"
                    )
                setattr(config, field_name, float(value))
            elif field_name in _STR_FIELDS:
                if not isinstance(value, str):
                    raise ConfigError(
                        f"{field_name} must be a string, got {type(value).__name__}"
                    )
                setattr(config, field_name, value)
            elif field_name in _STR_LIST_FIELDS:
                if not isinstance(value, list):
                    raise ConfigError(
                        f"{field_name} must be a list, got {type(value).__name__}"
                    )
                for item in value:
                    if not isinstance(item, str):
                        raise ConfigError(
                            f"{field_name} must be a list of strings, "
                            f"got element of type {type(item).__name__}"
                        )
                setattr(config, field_name, list(value))
        return config
