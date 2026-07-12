from __future__ import annotations

import os

from harness.models import GuardResult


class PathGuard:
    @staticmethod
    def check(path: str, target_directory: str) -> GuardResult:
        try:
            if not path or not target_directory:
                return GuardResult.DENY
            if "\x00" in path or "\x00" in target_directory:
                return GuardResult.DENY
            if os.path.isabs(path) and path != target_directory:
                return GuardResult.DENY
            target_real = os.path.realpath(target_directory)
            if not os.path.isdir(target_real):
                return GuardResult.DENY
            joined = os.path.join(target_directory, path)
            path_real = os.path.realpath(joined)
            if path_real == target_real:
                return GuardResult.ALLOW
            common = os.path.commonpath([path_real, target_real])
            if common == target_real:
                return GuardResult.ALLOW
            return GuardResult.DENY
        except (ValueError, OSError, TypeError):
            return GuardResult.DENY
