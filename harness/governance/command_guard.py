from __future__ import annotations

import re

from harness.models import GuardResult


class CommandGuard:
    """Dangerous command pattern matcher for the ``run_command`` tool.

    Checks a shell command string against a list of dangerous regex
    patterns.  If any pattern matches, the command is flagged as
    ``PENDING`` (requires human approval).  Otherwise the command is
    ``ALLOW``-ed.  Per SPEC §3.4.2, invalid regex patterns are silently
    skipped.
    """

    @staticmethod
    def check(cmd: str, patterns: list[str]) -> GuardResult:
        """Return ``PENDING`` if *cmd* matches any dangerous pattern, else ``ALLOW``.

        Non-string inputs (``None``, ``int``, etc.) and non-list *patterns*
        are handled defensively by returning ``ALLOW`` — there is nothing
        to match.  Invalid regex patterns are skipped per SPEC §3.4.2.
        """
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
