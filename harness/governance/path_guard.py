from __future__ import annotations

import os

from harness.models import GuardResult


class PathGuard:
    """Path boundary guard for the target directory subtree.

    Checks whether a given file path stays within the ``target_directory``
    subtree, blocking ``..`` traversal, absolute paths outside the target,
    and symlinks that escape the sandbox.
    """

    @staticmethod
    def check(path: str, target_directory: str) -> GuardResult:
        """Return ``ALLOW`` if *path* is inside *target_directory*, else ``DENY``.

        Path resolution failures (null bytes, non-existent target, type
        errors) also return ``DENY`` per SPEC §3.4.1.
        """
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
