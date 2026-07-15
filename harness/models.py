from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any


class FailureType(StrEnum):
    ASSERTION = "ASSERTION"
    SYNTAX = "SYNTAX"
    IMPORT = "IMPORT"
    RUNTIME = "RUNTIME"
    TIMEOUT = "TIMEOUT"
    COLLECTION = "COLLECTION"


class RoundOutcome(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NO_TESTS = "NO_TESTS"
    HITL_DENIED = "HITL_DENIED"


class StopReason(Enum):
    PASS = "PASS"
    MAX_ROUNDS = "MAX_ROUNDS"
    STUCK = "STUCK"
    HITL_DENIED = "HITL_DENIED"
    LLM_ERROR = "LLM_ERROR"


class HITLStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    TIMEOUT = "TIMEOUT"


class GuardResult(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    PENDING = "PENDING"


_DEFAULT_ENABLED_TOOLS: list[str] = [
    "write_file",
    "read_file",
    "list_files",
    "run_tests",
    "run_command",
    "finish",
]

_DEFAULT_DANGEROUS_PATTERNS: list[str] = [
    r"rm\s+-rf",
    r"git\s+push",
    r"sudo\s+",
    r"curl\s+|wget\s+",
    r"docker\s+",
]


@dataclass
class Config:
    max_rounds: int = 10
    target_directory: str = "./workspace"
    test_command: str = "pytest --json-report --output=.harness/report.json"
    model: str = "deepseek-chat"
    temperature: float = 0.1
    memory_file: str = ".harness/memory.json"
    enabled_tools: list[str] = field(
        default_factory=lambda: list(_DEFAULT_ENABLED_TOOLS)
    )
    dangerous_command_patterns: list[str] = field(
        default_factory=lambda: list(_DEFAULT_DANGEROUS_PATTERNS)
    )
    hitl_timeout_seconds: int = 300
    llm_timeout: int = 60
    pytest_timeout: int = 60
    stuck_threshold: int = 3
    llm_retry_count: int = 3


@dataclass
class Action:
    tool_name: str
    args: dict[str, Any]
    raw_tool_call: Any | None = None


@dataclass
class Failure:
    type: FailureType
    test_name: str
    message: str
    file: str
    line: int
    expected: str
    actual: str


@dataclass
class TestResult:
    """Result of running the test suite.

    Note: ``__test__ = False`` tells pytest not to collect this
    dataclass as a test class (it starts with ``Test``).
    """

    __test__ = False

    status: str
    failures: list[Failure]
    summary: dict[str, Any]


@dataclass
class MemoryEntry:
    session_id: str
    round: int
    failure_type: FailureType
    test_name: str
    message: str
    strategy_used: str
    outcome: str


@dataclass
class FeedbackMessage:
    failure_type: FailureType
    details: str
    strategy_hint: str
    relevant_memory: list[MemoryEntry]


@dataclass
class RoundRecord:
    round_number: int
    actions: list[Action]
    failure_fingerprint: str
    strategy_used: str
    outcome: RoundOutcome


@dataclass
class HITLRequest:
    action: Action
    status: HITLStatus
    timestamp: datetime
    decision: str
    request_id: str = ""
