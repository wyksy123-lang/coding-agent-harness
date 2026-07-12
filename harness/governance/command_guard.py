from __future__ import annotations

import re
from typing import Any

from harness.models import GuardResult


class CommandGuard:
    """Dangerous command pattern matcher for the run_command tool."""

    @staticmethod
    def check(cmd: Any, patterns: Any) -> GuardResult:
        """Return PENDING if *cmd* matches any dangerous pattern, else ALLOW."""
        if not isinstance(cmd, str):
            return GuardResult.ALLOW
        if not isinstance(patterns, list):
            return GuardResult.ALLOW
        for pattern in patterns:
            if not isinstance(pattern, str):
                continue
            try:
                compiled = re.compile(pattern)
            except re.error:
                continue
            if compiled.search(cmd):
                return GuardResult.PENDING
        return GuardResult.ALLOW
