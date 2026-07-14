from __future__ import annotations

from pathlib import Path

from harness.models import StopReason

from demo.run_demo import (
    demonstrate_feedback_correction,
    demonstrate_governance_interception,
    demonstrate_stuck_detection,
    run_all_demonstrations,
)


def test_governance_demo_intercepts_rm_rf_with_hitl_pending(tmp_path: Path) -> None:
    result = demonstrate_governance_interception(tmp_path)

    assert result.name == "governance_interception"
    assert result.stop_reason == StopReason.HITL_DENIED
    assert result.evidence["intercepted"] is True
    assert result.evidence["command"] == "rm -rf .harness"
    assert result.evidence["hitl_status"] == "PENDING"
    assert result.evidence["first_round_outcome"] == "HITL_DENIED"


def test_feedback_demo_changes_action_after_injected_failure(tmp_path: Path) -> None:
    result = demonstrate_feedback_correction(tmp_path)

    assert result.name == "feedback_correction"
    assert result.stop_reason == StopReason.PASS
    assert result.evidence["feedback_seen"] is True
    assert result.evidence["changed_action"] is True
    assert result.evidence["actions_by_round"] == [
        ["run_tests"],
        ["write_file"],
        ["run_tests"],
    ]


def test_stuck_demo_stops_after_repeated_failure_fingerprint(tmp_path: Path) -> None:
    result = demonstrate_stuck_detection(tmp_path)

    assert result.name == "stuck_detection"
    assert result.stop_reason == StopReason.STUCK
    assert result.evidence["stuck_threshold"] == 2
    assert result.evidence["round_count"] == 2
    assert result.evidence["same_failure_fingerprint"] is True


def test_run_all_demonstrations_returns_three_successful_scenarios(
    tmp_path: Path,
) -> None:
    results = run_all_demonstrations(tmp_path)

    assert [result.name for result in results] == [
        "governance_interception",
        "feedback_correction",
        "stuck_detection",
    ]
    assert [result.stop_reason for result in results] == [
        StopReason.HITL_DENIED,
        StopReason.PASS,
        StopReason.STUCK,
    ]
