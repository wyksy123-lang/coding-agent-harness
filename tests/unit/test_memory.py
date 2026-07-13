from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.memory.retriever import MemoryRecorder, MemoryRetriever
from harness.models import FailureType, MemoryEntry, RoundOutcome, RoundRecord


def _write_memory(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _entry(
    *,
    session_id: str,
    round_number: int,
    failure_type: str,
    test_name: str = "tests/test_sample.py::test_example",
    message: str = "assert 1 == 2",
    strategy_used: str = "fix_assertion",
    outcome: str = "resolved",
) -> dict:
    return {
        "session_id": session_id,
        "round": round_number,
        "failure_type": failure_type,
        "test_name": test_name,
        "message": message,
        "strategy_used": strategy_used,
        "outcome": outcome,
    }


class TestMemoryRetriever:
    def test_retrieve_relevant_filters_by_failure_type(self, tmp_path: Path):
        memory_file = tmp_path / "memory.json"
        _write_memory(
            memory_file,
            {
                "failure_history": [
                    _entry(session_id="s1", round_number=1, failure_type="ASSERTION"),
                    _entry(session_id="s2", round_number=2, failure_type="IMPORT"),
                    _entry(session_id="s3", round_number=3, failure_type="ASSERTION"),
                ]
            },
        )

        results = MemoryRetriever(memory_file).retrieve_relevant("ASSERTION")

        assert [entry.session_id for entry in results] == ["s1", "s3"]
        assert all(entry.failure_type == FailureType.ASSERTION for entry in results)
        assert all(isinstance(entry, MemoryEntry) for entry in results)

    def test_limit_truncates_matching_results(self, tmp_path: Path):
        memory_file = tmp_path / "memory.json"
        _write_memory(
            memory_file,
            {
                "failure_history": [
                    _entry(session_id="s1", round_number=1, failure_type="ASSERTION"),
                    _entry(session_id="s2", round_number=2, failure_type="ASSERTION"),
                    _entry(session_id="s3", round_number=3, failure_type="ASSERTION"),
                ]
            },
        )

        results = MemoryRetriever(memory_file).retrieve_relevant("ASSERTION", limit=2)

        assert [entry.session_id for entry in results] == ["s1", "s2"]

    def test_missing_memory_file_returns_empty_list(self, tmp_path: Path):
        results = MemoryRetriever(tmp_path / "missing.json").retrieve_relevant("ASSERTION")

        assert results == []

    @pytest.mark.parametrize("content", ["", "{ not valid json"])
    def test_empty_or_invalid_memory_file_returns_empty_list(
        self,
        tmp_path: Path,
        content: str,
    ):
        memory_file = tmp_path / "memory.json"
        memory_file.write_text(content, encoding="utf-8")

        results = MemoryRetriever(memory_file).retrieve_relevant("ASSERTION")

        assert results == []

    def test_non_full_load_behavior_returns_only_limited_matching_entries(
        self,
        tmp_path: Path,
    ):
        memory_file = tmp_path / "memory.json"
        _write_memory(
            memory_file,
            {
                "failure_history": [
                    _entry(session_id="s1", round_number=1, failure_type="ASSERTION"),
                    _entry(session_id="s2", round_number=2, failure_type="IMPORT"),
                    _entry(session_id="s3", round_number=3, failure_type="ASSERTION"),
                    _entry(session_id="s4", round_number=4, failure_type="RUNTIME"),
                    _entry(session_id="s5", round_number=5, failure_type="ASSERTION"),
                ]
            },
        )

        results = MemoryRetriever(memory_file).retrieve_relevant("ASSERTION", limit=2)

        assert len(results) == 2
        assert len(results) < 5
        assert all(entry.failure_type == FailureType.ASSERTION for entry in results)

    def test_get_conventions_returns_project_conventions(self, tmp_path: Path):
        memory_file = tmp_path / "memory.json"
        conventions = {"test_style": "pytest", "no_network": True}
        _write_memory(
            memory_file,
            {
                "project_conventions": conventions,
                "failure_history": [],
            },
        )

        result = MemoryRetriever(memory_file).get_conventions()

        assert result == conventions

    @pytest.mark.parametrize("content", [None, "", "{ not valid json"])
    def test_get_conventions_returns_empty_dict_when_missing_empty_or_invalid(
        self,
        tmp_path: Path,
        content: str | None,
    ):
        memory_file = tmp_path / "memory.json"
        if content is not None:
            memory_file.write_text(content, encoding="utf-8")

        result = MemoryRetriever(memory_file).get_conventions()

        assert result == {}


class TestMemoryRecorder:
    def test_record_appends_entry_retrievable_by_failure_type(self, tmp_path: Path):
        memory_file = tmp_path / "memory.json"
        round_record = RoundRecord(
            round_number=1,
            actions=[],
            failure_fingerprint=(
                "ASSERTION|tests/test_sample.py::test_example|assert 1 == 2"
            ),
            strategy_used="fix_assertion",
            outcome=RoundOutcome.FAIL,
        )

        MemoryRecorder(memory_file).record(round_record)
        results = MemoryRetriever(memory_file).retrieve_relevant("ASSERTION")

        assert len(results) == 1
        assert results[0].round == 1
        assert results[0].failure_type == FailureType.ASSERTION
        assert results[0].test_name == "tests/test_sample.py::test_example"
        assert results[0].message == "assert 1 == 2"
        assert results[0].strategy_used == "fix_assertion"
        assert results[0].outcome == "unresolved"

    def test_record_preserves_existing_failure_history(self, tmp_path: Path):
        memory_file = tmp_path / "memory.json"
        _write_memory(
            memory_file,
            {
                "failure_history": [
                    _entry(session_id="existing", round_number=1, failure_type="IMPORT")
                ]
            },
        )
        round_record = RoundRecord(
            round_number=2,
            actions=[],
            failure_fingerprint=(
                "ASSERTION|tests/test_sample.py::test_example|assert 1 == 2"
            ),
            strategy_used="fix_assertion",
            outcome=RoundOutcome.PASS,
        )

        MemoryRecorder(memory_file).record(round_record)

        import_results = MemoryRetriever(memory_file).retrieve_relevant("IMPORT")
        assertion_results = MemoryRetriever(memory_file).retrieve_relevant("ASSERTION")
        assert [entry.session_id for entry in import_results] == ["existing"]
        assert len(assertion_results) == 1
        assert assertion_results[0].outcome == "resolved"
