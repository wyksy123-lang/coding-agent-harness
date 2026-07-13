from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterator

from harness.models import FailureType, MemoryEntry, RoundOutcome, RoundRecord

logger = logging.getLogger(__name__)


class MemoryRetriever:
    """Read structured memory entries from a JSON memory file."""

    def __init__(self, memory_file: str | Path = ".harness/memory.json") -> None:
        self.memory_file = Path(memory_file)

    def retrieve_relevant(
        self, failure_type: str | FailureType, limit: int = 3
    ) -> list[MemoryEntry]:
        if limit <= 0 or not self.memory_file.exists():
            return []

        target_type = _normalize_failure_type(failure_type)
        entries: list[MemoryEntry] = []
        for item in _iter_failure_history(self.memory_file):
            entry = _entry_from_mapping(item)
            if entry is not None and entry.failure_type == target_type:
                entries.append(entry)
            if len(entries) >= limit:
                break
        return entries

    def get_conventions(self) -> dict[str, Any]:
        data = self._read_memory()
        if not data:
            return {}
        conventions = data.get("project_conventions", {})
        return conventions if isinstance(conventions, dict) else {}

    def _read_memory(self) -> dict[str, Any]:
        if not self.memory_file.exists():
            return {}
        try:
            raw = self.memory_file.read_text(encoding="utf-8")
            if not raw.strip():
                return {}
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to read memory file %s: %s", self.memory_file, exc)
            return {}
        return data if isinstance(data, dict) else {}


class MemoryRecorder:
    """Append round outcomes to the JSON memory file."""

    def __init__(self, memory_file: str | Path = ".harness/memory.json") -> None:
        self.memory_file = Path(memory_file)

    def record(self, round_record: RoundRecord) -> None:
        data = MemoryRetriever(self.memory_file)._read_memory()
        history = data.get("failure_history")
        if not isinstance(history, list):
            history = []
            data["failure_history"] = history

        history.append(_entry_from_round(round_record))

        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            self.memory_file.write_text(
                json.dumps(data, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Failed to write memory file %s: %s", self.memory_file, exc)


def _normalize_failure_type(failure_type: str | FailureType) -> FailureType:
    if isinstance(failure_type, FailureType):
        return failure_type
    try:
        return FailureType(str(failure_type))
    except ValueError:
        return FailureType.RUNTIME


def _entry_from_mapping(item: Any) -> MemoryEntry | None:
    if not isinstance(item, dict):
        return None
    return MemoryEntry(
        session_id=str(item.get("session_id", "")),
        round=int(item.get("round", 0)),
        failure_type=_normalize_failure_type(str(item.get("failure_type", ""))),
        test_name=str(item.get("test_name", "")),
        message=str(item.get("message", "")),
        strategy_used=str(item.get("strategy_used", "")),
        outcome=str(item.get("outcome", "unresolved")),
    )


def _iter_failure_history(memory_file: Path) -> Iterator[Any]:
    decoder = json.JSONDecoder()
    buffer = ""
    position = 0
    in_history = False
    chunk_size = 4096

    try:
        with memory_file.open("r", encoding="utf-8") as stream:
            while True:
                if not in_history:
                    while '"failure_history"' not in buffer:
                        chunk = stream.read(chunk_size)
                        if chunk == "":
                            return
                        buffer += chunk
                    position = buffer.index('"failure_history"') + len(
                        '"failure_history"'
                    )

                    while True:
                        position = _skip_whitespace(buffer, position)
                        if position >= len(buffer):
                            chunk = stream.read(chunk_size)
                            if chunk == "":
                                return
                            buffer += chunk
                            continue
                        if buffer[position] != ":":
                            return
                        position += 1
                        break

                    while True:
                        position = _skip_whitespace(buffer, position)
                        if position >= len(buffer):
                            chunk = stream.read(chunk_size)
                            if chunk == "":
                                return
                            buffer += chunk
                            continue
                        if buffer[position] != "[":
                            return
                        position += 1
                        in_history = True
                        break

                position = _skip_array_separator(buffer, position)
                while position >= len(buffer):
                    chunk = stream.read(chunk_size)
                    if chunk == "":
                        return
                    buffer += chunk
                    position = _skip_array_separator(buffer, position)

                if buffer[position] == "]":
                    return

                while True:
                    try:
                        item, next_position = decoder.raw_decode(buffer, position)
                    except json.JSONDecodeError:
                        chunk = stream.read(chunk_size)
                        if chunk == "":
                            logger.warning("Failed to read memory file %s", memory_file)
                            return
                        buffer += chunk
                        continue

                    yield item
                    position = next_position
                    if position > chunk_size:
                        buffer = buffer[position:]
                        position = 0
                    break
    except OSError as exc:
        logger.warning("Failed to read memory file %s: %s", memory_file, exc)


def _skip_whitespace(buffer: str, position: int) -> int:
    while position < len(buffer) and buffer[position].isspace():
        position += 1
    return position


def _skip_array_separator(buffer: str, position: int) -> int:
    while position < len(buffer) and (
        buffer[position].isspace() or buffer[position] == ","
    ):
        position += 1
    return position


def _entry_from_round(round_record: RoundRecord) -> dict[str, Any]:
    failure_type, test_name, message = _parse_fingerprint(
        round_record.failure_fingerprint
    )
    return {
        "session_id": "",
        "round": round_record.round_number,
        "failure_type": failure_type.value,
        "test_name": test_name,
        "message": message,
        "strategy_used": round_record.strategy_used,
        "outcome": (
            "resolved"
            if round_record.outcome == RoundOutcome.PASS
            else "unresolved"
        ),
    }


def _parse_fingerprint(fingerprint: str) -> tuple[FailureType, str, str]:
    parts = fingerprint.split("|", 2)
    if len(parts) != 3:
        return FailureType.RUNTIME, "", fingerprint
    return _normalize_failure_type(parts[0]), parts[1], parts[2]
