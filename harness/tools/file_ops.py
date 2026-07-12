from __future__ import annotations

import os
from typing import Any

from harness.governance.path_guard import PathGuard
from harness.models import GuardResult
from harness.tools.base import Tool, ToolResult


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
        if os.path.isabs(path):
            return ToolResult(success=False, output={}, error="path out of bounds")
        if PathGuard.check(path, self._target_directory) == GuardResult.DENY:
            return ToolResult(success=False, output={}, error="path out of bounds")
        full = os.path.join(self._target_directory, path)
        try:
            parent = os.path.dirname(full)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(full, "w", encoding="utf-8") as f:
                f.write(content)
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
        if os.path.isabs(path):
            return ToolResult(success=False, output={}, error="path out of bounds")
        if PathGuard.check(path, self._target_directory) == GuardResult.DENY:
            return ToolResult(success=False, output={}, error="path out of bounds")
        full = os.path.join(self._target_directory, path)
        if not os.path.isfile(full):
            return ToolResult(success=False, output={}, error="file not found")
        try:
            with open(full, "r", encoding="utf-8") as f:
                content = f.read()
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
        if os.path.isabs(path):
            return ToolResult(success=False, output={}, error="path out of bounds")
        if PathGuard.check(path, self._target_directory) == GuardResult.DENY:
            return ToolResult(success=False, output={}, error="path out of bounds")
        full = os.path.join(self._target_directory, path)
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
