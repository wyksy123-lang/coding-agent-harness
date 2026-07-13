from __future__ import annotations

from hashlib import sha256

from harness.models import Failure, RoundOutcome, RoundRecord, StopReason


class RoundTracker:
    """Track round history and decide when the agent loop should stop."""

    MAX_FINGERPRINT_MESSAGE_LENGTH = 220

    def __init__(self, max_rounds: int, stuck_threshold: int) -> None:
        self.max_rounds = max_rounds
        self.stuck_threshold = stuck_threshold
        self.history: list[RoundRecord] = []

    def update(self, round_record: RoundRecord) -> None:
        self.history.append(round_record)

    def detect_loop(self) -> bool:
        if self.stuck_threshold <= 0 or len(self.history) < self.stuck_threshold:
            return False

        recent = self.history[-self.stuck_threshold :]
        fingerprint = recent[0].failure_fingerprint
        if not fingerprint:
            return False
        return all(record.failure_fingerprint == fingerprint for record in recent)

    def should_stop(self) -> StopReason | None:
        if not self.history:
            return None

        latest = self.history[-1]
        if latest.outcome == RoundOutcome.PASS:
            return StopReason.PASS
        if latest.round_number >= self.max_rounds:
            return StopReason.MAX_ROUNDS
        if self.detect_loop():
            return StopReason.STUCK
        if latest.outcome == RoundOutcome.HITL_DENIED:
            return StopReason.HITL_DENIED
        return None

    @staticmethod
    def failure_fingerprint(failure: Failure) -> str:
        message_hash = sha256(failure.message.encode("utf-8")).hexdigest()
        message = _truncate_message(failure.message)
        return (
            f"{failure.type.value}|{failure.test_name}|"
            f"{message} [sha256:{message_hash}]"
        )


def _truncate_message(message: str) -> str:
    max_length = RoundTracker.MAX_FINGERPRINT_MESSAGE_LENGTH
    if len(message) <= max_length:
        return message
    return message[: max_length - 3].rstrip() + "..."
