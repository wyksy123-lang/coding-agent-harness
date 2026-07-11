from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class FailureType(str, Enum):
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


class HITLStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    TIMEOUT = "TIMEOUT"


class GuardResult(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    PENDING = "PENDING"


@dataclass
class Config:
    max_rounds: int = 10
    target_directory: str = "./workspace"
    test_command: str = "pytest --json-report --output=.harness/report.json"
    model: str = "deepseek-chat"
    temperature: float = 0.1
    memory_file: str = ".harness/memory.json"
    enabled_tools: list = field(default_factory=list)
    dangerous_command_patterns: list = field(default_factory=list)
    hitl_timeout_seconds: int = 300
    llm_timeout: int = 60
    pytest_timeout: int = 60
    stuck_threshold: int = 3
    llm_retry_count: int = 3


@dataclass
class Action:
    tool_name: str
    args: dict
    raw_tool_call: Optional[Any] = None


@dataclass
class TestResult:
    status: str
    failures: list
    summary: dict


@dataclass
class Failure:
    type: str
    test_name: str
    message: str
    file: str
    line: int
    expected: str
    actual: str


@dataclass
class FeedbackMessage:
    failure_type: str
    details: str
    strategy_hint: str
    relevant_memory: list


@dataclass
class RoundRecord:
    round_number: int
    actions: list
    failure_fingerprint: str
    strategy_used: str
    outcome: RoundOutcome


@dataclass
class HITLRequest:
    action: Action
    status: HITLStatus
    timestamp: datetime
    decision: str


@dataclass
class MemoryEntry:
    session_id: str
    round: int
    failure_type: str
    test_name: str
    message: str
    strategy_used: str
    outcome: str