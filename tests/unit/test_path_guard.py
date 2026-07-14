from __future__ import annotations

import os
import sys

import pytest

from harness.governance.path_guard import PathGuard
from harness.models import GuardResult


class TestPathGuardExistence:
    """Verify PathGuard is importable and has the expected API surface."""

    def test_path_guard_is_class(self):
        assert isinstance(PathGuard, type)

    def test_path_guard_has_check_method(self):
        assert hasattr(PathGuard, "check")

    def test_check_is_callable(self):
        assert callable(getattr(PathGuard, "check", None))


class TestPathGuardLegitimatePaths:
    """Legitimate paths within target_directory must be ALLOWed."""

    def test_simple_relative_path_allowed(self, tmp_workspace):
        result = PathGuard.check("file.txt", tmp_workspace)
        assert result == GuardResult.ALLOW

    def test_nested_relative_path_allowed(self, tmp_workspace):
        result = PathGuard.check("subdir/file.txt", tmp_workspace)
        assert result == GuardResult.ALLOW

    def test_deeply_nested_relative_path_allowed(self, tmp_workspace):
        result = PathGuard.check("a/b/c/d/file.txt", tmp_workspace)
        assert result == GuardResult.ALLOW

    def test_path_with_nonexistent_subdir_allowed(self, tmp_workspace):
        result = PathGuard.check("does_not_exist/file.txt", tmp_workspace)
        assert result == GuardResult.ALLOW

    def test_filename_only_allowed(self, tmp_workspace):
        result = PathGuard.check("readme.md", tmp_workspace)
        assert result == GuardResult.ALLOW

    def test_dot_slash_relative_path_allowed(self, tmp_workspace):
        result = PathGuard.check("./file.txt", tmp_workspace)
        assert result == GuardResult.ALLOW

    def test_dot_path_allowed(self, tmp_workspace):
        result = PathGuard.check(".", tmp_workspace)
        assert result == GuardResult.ALLOW

    def test_target_directory_itself_allowed(self, tmp_workspace):
        result = PathGuard.check(tmp_workspace, tmp_workspace)
        assert result == GuardResult.ALLOW

    def test_trailing_slash_path_allowed(self, tmp_workspace):
        result = PathGuard.check("subdir/", tmp_workspace)
        assert result == GuardResult.ALLOW

    def test_internal_dot_dot_staying_inside_allowed(self, tmp_workspace):
        os.makedirs(os.path.join(tmp_workspace, "subdir"), exist_ok=True)
        result = PathGuard.check("subdir/../other.txt", tmp_workspace)
        assert result == GuardResult.ALLOW


class TestPathGuardOutOfBounds:
    """Out-of-bounds paths must be DENYed."""

    def test_dot_dot_traversal_denied(self, tmp_workspace):
        result = PathGuard.check("../secret.txt", tmp_workspace)
        assert result == GuardResult.DENY

    def test_double_dot_dot_traversal_denied(self, tmp_workspace):
        result = PathGuard.check("../../etc/passwd", tmp_workspace)
        assert result == GuardResult.DENY

    def test_absolute_path_outside_target_denied(self, tmp_workspace):
        result = PathGuard.check("/etc/passwd", tmp_workspace)
        assert result == GuardResult.DENY

    def test_absolute_path_inside_target_denied(self, tmp_workspace):
        abs_path = os.path.join(tmp_workspace, "file.txt")
        result = PathGuard.check(abs_path, tmp_workspace)
        assert result == GuardResult.DENY

    def test_subdir_dot_dot_escape_denied(self, tmp_workspace):
        result = PathGuard.check("subdir/../../outside.txt", tmp_workspace)
        assert result == GuardResult.DENY

    def test_leading_slash_denied(self, tmp_workspace):
        result = PathGuard.check("/tmp/secret.txt", tmp_workspace)
        assert result == GuardResult.DENY

    def test_dot_dot_with_prefix_denied(self, tmp_workspace):
        result = PathGuard.check("a/../../../etc/shadow", tmp_workspace)
        assert result == GuardResult.DENY

    def test_absolute_path_to_root_denied(self, tmp_workspace):
        result = PathGuard.check("/", tmp_workspace)
        assert result == GuardResult.DENY

    def test_parent_directory_denied(self, tmp_workspace):
        parent = os.path.dirname(tmp_workspace)
        result = PathGuard.check(parent, tmp_workspace)
        assert result == GuardResult.DENY

    def test_sibling_directory_denied(self, tmp_workspace):
        parent = os.path.dirname(tmp_workspace)
        sibling = os.path.join(parent, "sibling_dir")
        result = PathGuard.check(sibling, tmp_workspace)
        assert result == GuardResult.DENY


class TestPathGuardEdgeCases:
    """Edge cases and error handling."""

    def test_empty_path_denied(self, tmp_workspace):
        result = PathGuard.check("", tmp_workspace)
        assert result == GuardResult.DENY

    def test_none_path_denied(self, tmp_workspace):
        result = PathGuard.check(None, tmp_workspace)
        assert result == GuardResult.DENY

    def test_none_target_directory_denied(self, tmp_workspace):
        result = PathGuard.check("file.txt", None)
        assert result == GuardResult.DENY

    def test_null_byte_in_path_denied(self, tmp_workspace):
        result = PathGuard.check("file\x00.txt", tmp_workspace)
        assert result == GuardResult.DENY

    def test_nonexistent_target_directory_denied(self):
        result = PathGuard.check("file.txt", "/nonexistent/path/does/not/exist")
        assert result == GuardResult.DENY

    def test_empty_target_directory_denied(self):
        result = PathGuard.check("file.txt", "")
        assert result == GuardResult.DENY

    def test_path_with_only_dot_dot_denied(self, tmp_workspace):
        result = PathGuard.check("..", tmp_workspace)
        assert result == GuardResult.DENY

    def test_path_with_only_slashes_denied(self, tmp_workspace):
        result = PathGuard.check("///", tmp_workspace)
        assert result == GuardResult.DENY

    def test_relative_path_resolves_outside_denied(self, tmp_workspace):
        result = PathGuard.check("a/b/c/../../../../../../etc/passwd", tmp_workspace)
        assert result == GuardResult.DENY


class TestPathGuardSymlinkHandling:
    """Symlinks pointing outside target_directory must be DENYed."""

    @pytest.mark.skipif(
        not hasattr(os, "symlink") or sys.platform == "win32",
        reason="symlink not supported on this platform",
    )
    def test_symlink_pointing_outside_denied(self, tmp_workspace):
        outside_dir = os.path.dirname(tmp_workspace)
        outside_file = os.path.join(outside_dir, "outside_secret.txt")
        try:
            with open(outside_file, "w") as f:
                f.write("secret")
            link_path = os.path.join(tmp_workspace, "link_to_outside.txt")
            os.symlink(outside_file, link_path)
            result = PathGuard.check("link_to_outside.txt", tmp_workspace)
            assert result == GuardResult.DENY
        finally:
            if os.path.exists(outside_file):
                os.remove(outside_file)

    @pytest.mark.skipif(
        not hasattr(os, "symlink") or sys.platform == "win32",
        reason="symlink not supported on this platform",
    )
    def test_symlink_pointing_inside_allowed(self, tmp_workspace):
        target_file = os.path.join(tmp_workspace, "real_target.txt")
        with open(target_file, "w") as f:
            f.write("content")
        link_path = os.path.join(tmp_workspace, "link_to_inside.txt")
        os.symlink(target_file, link_path)
        result = PathGuard.check("link_to_inside.txt", tmp_workspace)
        assert result == GuardResult.ALLOW

    @pytest.mark.skipif(
        not hasattr(os, "symlink") or sys.platform == "win32",
        reason="symlink not supported on this platform",
    )
    def test_symlink_directory_pointing_outside_denied(self, tmp_workspace):
        outside_dir = os.path.dirname(tmp_workspace)
        link_dir = os.path.join(tmp_workspace, "evil_dir")
        os.symlink(outside_dir, link_dir)
        result = PathGuard.check("evil_dir/file.txt", tmp_workspace)
        assert result == GuardResult.DENY


class TestPathGuardReturnType:
    """The check method must return a GuardResult enum value."""

    def test_returns_guard_result_enum(self, tmp_workspace):
        result = PathGuard.check("file.txt", tmp_workspace)
        assert isinstance(result, GuardResult)

    def test_returns_guard_result_for_denied(self, tmp_workspace):
        result = PathGuard.check("../escape.txt", tmp_workspace)
        assert isinstance(result, GuardResult)

    def test_allow_and_deny_are_distinct(self, tmp_workspace):
        allowed = PathGuard.check("file.txt", tmp_workspace)
        denied = PathGuard.check("../escape.txt", tmp_workspace)
        assert allowed == GuardResult.ALLOW
        assert denied == GuardResult.DENY
        assert allowed != denied
