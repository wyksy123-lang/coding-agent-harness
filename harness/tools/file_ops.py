from __future__ import annotations

import os
import stat
from typing import Any

from harness.governance.path_guard import PathGuard
from harness.models import GuardResult
from harness.tools.base import Tool, ToolResult

_BOUNDARY_ERROR = "path out of bounds"
_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


def _resolve_safe_path(path: Any, target_directory: str) -> str | None:
    """Resolve *path* against *target_directory*, enforcing boundary rules.

    Returns the full filesystem path if the path is a non-absolute
    relative path inside *target_directory* (as confirmed by
    :class:`PathGuard`), or ``None`` if the path is out of bounds,
    non-string, or rejected by the guard.
    """
    if not isinstance(path, str):
        return None
    if os.path.isabs(path):
        return None
    if PathGuard.check(path, target_directory) == GuardResult.DENY:
        return None
    return os.path.join(target_directory, path)


def _is_reparse_point(path: str) -> bool:
    try:
        attrs = os.lstat(path).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _is_link_like(path: str) -> bool:
    return os.path.islink(path) or _is_reparse_point(path)


class WriteFileTool(Tool):
    """Tool for writing content to a file inside the target directory."""

    def __init__(self, target_directory: str) -> None:
        self._target_directory = target_directory

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        }

    def execute(self, args: dict[str, Any]) -> ToolResult:
        path = args.get("path", "")
        content = args.get("content", "")
        full = _resolve_safe_path(path, self._target_directory)
        if full is None:
            return ToolResult(success=False, output={}, error=_BOUNDARY_ERROR)
        try:
            parent = os.path.dirname(full)
            if parent:
                os.makedirs(parent, exist_ok=True)
            if _O_NOFOLLOW == 0 and _is_link_like(full):
                return ToolResult(success=False, output={}, error="refusing symlink")
            fd = os.open(
                full,
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC | _O_NOFOLLOW,
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                try:
                    os.close(fd)
                except OSError:
                    pass
                raise
        except OSError as e:
            return ToolResult(success=False, output={}, error=str(e))
        return ToolResult(success=True, output={"success": True})


class ReadFileTool(Tool):
    """Tool for reading file content from inside the target directory."""

    def __init__(self, target_directory: str) -> None:
        self._target_directory = target_directory

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        }

    def execute(self, args: dict[str, Any]) -> ToolResult:
        path = args.get("path", "")
        full = _resolve_safe_path(path, self._target_directory)
        if full is None:
            return ToolResult(success=False, output={}, error=_BOUNDARY_ERROR)
        if not os.path.isfile(full):
            return ToolResult(success=False, output={}, error="file not found")
        try:
            if _O_NOFOLLOW == 0 and _is_link_like(full):
                return ToolResult(success=False, output={}, error="refusing symlink")
            fd = os.open(full, os.O_RDONLY | _O_NOFOLLOW)
            try:
                with os.fdopen(fd, encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                try:
                    os.close(fd)
                except OSError:
                    pass
                raise
        except OSError as e:
            return ToolResult(success=False, output={}, error=str(e))
        return ToolResult(success=True, output={"content": content})


class ListFilesTool(Tool):
    """Tool for listing files and subdirectories inside the target directory."""

    def __init__(self, target_directory: str) -> None:
        self._target_directory = target_directory

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        }

    def execute(self, args: dict[str, Any]) -> ToolResult:
        path = args.get("path", "")
        full = _resolve_safe_path(path, self._target_directory)
        if full is None:
            return ToolResult(success=False, output={}, error=_BOUNDARY_ERROR)
        if not os.path.isdir(full):
            return ToolResult(success=True, output={"files": [], "dirs": []})
        files: list[str] = []
        dirs: list[str] = []
        try:
            for entry in os.listdir(full):
                entry_path = os.path.join(full, entry)
                if os.path.isfile(entry_path):
                    files.append(entry)
                elif os.path.isdir(entry_path):
                    dirs.append(entry)
        except OSError as e:
            return ToolResult(success=False, output={}, error=str(e))
        return ToolResult(success=True, output={"files": files, "dirs": dirs})
