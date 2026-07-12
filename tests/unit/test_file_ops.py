from __future__ import annotations

import os

import pytest

from harness.tools.base import Tool, ToolResult
from harness.tools.file_ops import ListFilesTool, ReadFileTool, WriteFileTool


class TestWriteFileToolConstruction:
    """Verify WriteFileTool can be constructed and has the Tool API surface."""

    def test_can_construct_with_target_directory(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        assert isinstance(tool, WriteFileTool)

    def test_is_subclass_of_tool(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        assert isinstance(tool, Tool)

    def test_name_returns_write_file(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        assert tool.name == "write_file"

    def test_schema_returns_dict(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        schema = tool.schema
        assert isinstance(schema, dict)

    def test_schema_has_type_object(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        assert tool.schema["type"] == "object"

    def test_schema_has_properties(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        assert "properties" in tool.schema

    def test_schema_declares_path_property(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        assert "path" in tool.schema["properties"]

    def test_schema_declares_content_property(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        assert "content" in tool.schema["properties"]

    def test_schema_lists_required_fields(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        required = tool.schema.get("required", [])
        assert "path" in required
        assert "content" in required


class TestWriteFileToolWrites:
    """SPEC §3.2.1: write content to a file at target_directory/path."""

    def test_write_valid_relative_path_succeeds(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "hello.txt", "content": "hi"})
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.output == {"success": True}

    def test_write_persists_content_to_disk(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        tool.execute({"path": "hello.txt", "content": "hi there"})
        with open(os.path.join(tmp_workspace, "hello.txt"), encoding="utf-8") as f:
            assert f.read() == "hi there"

    def test_write_overwrites_existing_file(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        tool.execute({"path": "f.txt", "content": "first"})
        tool.execute({"path": "f.txt", "content": "second"})
        with open(os.path.join(tmp_workspace, "f.txt"), encoding="utf-8") as f:
            assert f.read() == "second"

    def test_write_to_nested_nonexistent_dir_auto_creates(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute(
            {"path": "subdir/deep/nested.txt", "content": "x"}
        )
        assert result.success is True
        assert os.path.isfile(os.path.join(tmp_workspace, "subdir", "deep", "nested.txt"))

    def test_write_to_deeply_nested_path_auto_creates_multiple_levels(
        self, tmp_workspace
    ):
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute(
            {"path": "a/b/c/d/e/f/file.txt", "content": "deep"}
        )
        assert result.success is True
        assert os.path.isfile(
            os.path.join(tmp_workspace, "a", "b", "c", "d", "e", "f", "file.txt")
        )

    def test_write_empty_content_succeeds(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "empty.txt", "content": ""})
        assert result.success is True
        with open(os.path.join(tmp_workspace, "empty.txt"), encoding="utf-8") as f:
            assert f.read() == ""

    def test_write_unicode_content_persists(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "u.txt", "content": "你好世界 🌍"})
        assert result.success is True
        with open(os.path.join(tmp_workspace, "u.txt"), encoding="utf-8") as f:
            assert f.read() == "你好世界 🌍"


class TestWriteFileToolBoundary:
    """SPEC §3.2.1: path out of bounds → PathGuard blocks → DENY error."""

    def test_write_dot_dot_traversal_blocked(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "../escape.txt", "content": "x"})
        assert result.success is False
        assert result.error == "path out of bounds"
        assert not os.path.exists(
            os.path.join(os.path.dirname(tmp_workspace), "escape.txt")
        )

    def test_write_double_dot_dot_traversal_blocked(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "../../etc/passwd", "content": "x"})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_write_absolute_path_outside_target_blocked(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "/etc/evil.txt", "content": "x"})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_write_absolute_path_inside_target_blocked(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        abs_path = os.path.join(tmp_workspace, "inside.txt")
        result = tool.execute({"path": abs_path, "content": "x"})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_write_subdir_dot_dot_escape_blocked(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute(
            {"path": "subdir/../../outside.txt", "content": "x"}
        )
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_write_blocked_path_does_not_create_file(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        tool.execute({"path": "../escape.txt", "content": "x"})
        assert not os.path.exists(
            os.path.join(os.path.dirname(tmp_workspace), "escape.txt")
        )


class TestReadFileToolConstruction:
    """Verify ReadFileTool can be constructed and has the Tool API surface."""

    def test_can_construct_with_target_directory(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        assert isinstance(tool, ReadFileTool)

    def test_is_subclass_of_tool(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        assert isinstance(tool, Tool)

    def test_name_returns_read_file(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        assert tool.name == "read_file"

    def test_schema_returns_dict(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        assert isinstance(tool.schema, dict)

    def test_schema_has_type_object(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        assert tool.schema["type"] == "object"

    def test_schema_has_properties(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        assert "properties" in tool.schema

    def test_schema_declares_path_property(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        assert "path" in tool.schema["properties"]

    def test_schema_lists_path_required(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        assert "path" in tool.schema.get("required", [])


class TestReadFileToolReads:
    """SPEC §3.2.2: read file content at target_directory/path."""

    def test_read_existing_file_returns_content(self, tmp_workspace):
        path = os.path.join(tmp_workspace, "data.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("hello world")
        tool = ReadFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "data.txt"})
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.output["content"] == "hello world"

    def test_read_content_matches_written_content(self, tmp_workspace):
        write_tool = WriteFileTool(target_directory=tmp_workspace)
        read_tool = ReadFileTool(target_directory=tmp_workspace)
        write_tool.execute({"path": "match.txt", "content": "round trip"})
        result = read_tool.execute({"path": "match.txt"})
        assert result.success is True
        assert result.output["content"] == "round trip"

    def test_read_nonexistent_file_returns_error(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "nope.txt"})
        assert result.success is False
        assert result.error == "file not found"

    def test_read_unicode_content(self, tmp_workspace):
        path = os.path.join(tmp_workspace, "u.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("你好 🌍")
        tool = ReadFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "u.txt"})
        assert result.success is True
        assert result.output["content"] == "你好 🌍"

    def test_read_empty_file_returns_empty_content(self, tmp_workspace):
        path = os.path.join(tmp_workspace, "empty.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
        tool = ReadFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "empty.txt"})
        assert result.success is True
        assert result.output["content"] == ""


class TestReadFileToolBoundary:
    """SPEC §3.2.2: path out of bounds → block."""

    def test_read_dot_dot_traversal_blocked(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "../escape.txt"})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_read_absolute_path_outside_target_blocked(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "/etc/passwd"})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_read_absolute_path_inside_target_blocked(self, tmp_workspace):
        path = os.path.join(tmp_workspace, "inside.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("data")
        tool = ReadFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": path})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_read_double_dot_dot_blocked(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "../../etc/shadow"})
        assert result.success is False
        assert result.error == "path out of bounds"


class TestListFilesToolConstruction:
    """Verify ListFilesTool can be constructed and has the Tool API surface."""

    def test_can_construct_with_target_directory(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        assert isinstance(tool, ListFilesTool)

    def test_is_subclass_of_tool(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        assert isinstance(tool, Tool)

    def test_name_returns_list_files(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        assert tool.name == "list_files"

    def test_schema_returns_dict(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        assert isinstance(tool.schema, dict)

    def test_schema_has_type_object(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        assert tool.schema["type"] == "object"

    def test_schema_has_properties(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        assert "properties" in tool.schema

    def test_schema_declares_path_property(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        assert "path" in tool.schema["properties"]


class TestListFilesToolLists:
    """SPEC §3.2.3: list files and subdirectories at target_directory/path."""

    def test_list_empty_directory_returns_empty_lists(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "."})
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.output["files"] == []
        assert result.output["dirs"] == []

    def test_list_directory_with_files_returns_files(self, tmp_workspace):
        with open(os.path.join(tmp_workspace, "a.txt"), "w") as f:
            f.write("a")
        with open(os.path.join(tmp_workspace, "b.txt"), "w") as f:
            f.write("b")
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "."})
        assert result.success is True
        assert sorted(result.output["files"]) == ["a.txt", "b.txt"]
        assert result.output["dirs"] == []

    def test_list_directory_with_subdirs_returns_dirs(self, tmp_workspace):
        os.makedirs(os.path.join(tmp_workspace, "sub1"))
        os.makedirs(os.path.join(tmp_workspace, "sub2"))
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "."})
        assert result.success is True
        assert sorted(result.output["dirs"]) == ["sub1", "sub2"]
        assert result.output["files"] == []

    def test_list_directory_with_files_and_dirs(self, tmp_workspace):
        with open(os.path.join(tmp_workspace, "file1.txt"), "w") as f:
            f.write("1")
        os.makedirs(os.path.join(tmp_workspace, "dir1"))
        os.makedirs(os.path.join(tmp_workspace, "dir2"))
        with open(os.path.join(tmp_workspace, "file2.py"), "w") as f:
            f.write("2")
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "."})
        assert result.success is True
        assert sorted(result.output["files"]) == ["file1.txt", "file2.py"]
        assert sorted(result.output["dirs"]) == ["dir1", "dir2"]

    def test_list_nested_subpath(self, tmp_workspace):
        os.makedirs(os.path.join(tmp_workspace, "parent", "child"))
        with open(os.path.join(tmp_workspace, "parent", "doc.md"), "w") as f:
            f.write("md")
        with open(os.path.join(tmp_workspace, "parent", "child", "nested.txt"), "w") as f:
            f.write("nested")
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "parent"})
        assert result.success is True
        assert sorted(result.output["files"]) == ["doc.md"]
        assert result.output["dirs"] == ["child"]

    def test_list_nonexistent_path_returns_empty_lists(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "does_not_exist"})
        assert result.success is True
        assert result.output["files"] == []
        assert result.output["dirs"] == []


class TestListFilesToolBoundary:
    """SPEC §3.2.3: path out of bounds → block."""

    def test_list_dot_dot_traversal_blocked(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": ".."})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_list_absolute_path_outside_target_blocked(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "/etc"})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_list_absolute_path_inside_target_blocked(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": tmp_workspace})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_list_double_dot_dot_blocked(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "../../"})
        assert result.success is False
        assert result.error == "path out of bounds"


class TestFileOpsIntegration:
    """Integration / edge cases across the file operation tools."""

    def test_write_then_read_round_trip(self, tmp_workspace):
        write_tool = WriteFileTool(target_directory=tmp_workspace)
        read_tool = ReadFileTool(target_directory=tmp_workspace)
        payload = "round trip content"
        write_result = write_tool.execute({"path": "rt.txt", "content": payload})
        assert write_result.success is True
        read_result = read_tool.execute({"path": "rt.txt"})
        assert read_result.success is True
        assert read_result.output["content"] == payload

    def test_write_nested_then_read_round_trip(self, tmp_workspace):
        write_tool = WriteFileTool(target_directory=tmp_workspace)
        read_tool = ReadFileTool(target_directory=tmp_workspace)
        payload = "nested round trip"
        write_result = write_tool.execute(
            {"path": "a/b/c/file.txt", "content": payload}
        )
        assert write_result.success is True
        read_result = read_tool.execute({"path": "a/b/c/file.txt"})
        assert read_result.success is True
        assert read_result.output["content"] == payload

    def test_write_then_list_shows_file(self, tmp_workspace):
        write_tool = WriteFileTool(target_directory=tmp_workspace)
        list_tool = ListFilesTool(target_directory=tmp_workspace)
        write_tool.execute({"path": "listed.txt", "content": "x"})
        result = list_tool.execute({"path": "."})
        assert result.success is True
        assert "listed.txt" in result.output["files"]

    def test_write_nested_then_list_shows_dir(self, tmp_workspace):
        write_tool = WriteFileTool(target_directory=tmp_workspace)
        list_tool = ListFilesTool(target_directory=tmp_workspace)
        write_tool.execute({"path": "newdir/file.txt", "content": "x"})
        result = list_tool.execute({"path": "."})
        assert result.success is True
        assert "newdir" in result.output["dirs"]

    def test_pathguard_blocks_out_of_bounds_write(self, tmp_workspace):
        """Verify PathGuard integration: out-of-bounds paths are rejected."""
        write_tool = WriteFileTool(target_directory=tmp_workspace)
        result = write_tool.execute({"path": "../outside.txt", "content": "x"})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_pathguard_blocks_out_of_bounds_read(self, tmp_workspace):
        read_tool = ReadFileTool(target_directory=tmp_workspace)
        result = read_tool.execute({"path": "../outside.txt"})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_pathguard_blocks_out_of_bounds_list(self, tmp_workspace):
        list_tool = ListFilesTool(target_directory=tmp_workspace)
        result = list_tool.execute({"path": ".."})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_all_three_tools_are_tool_subclasses(self, tmp_workspace):
        assert issubclass(WriteFileTool, Tool)
        assert issubclass(ReadFileTool, Tool)
        assert issubclass(ListFilesTool, Tool)

    def test_all_three_tools_have_distinct_names(self, tmp_workspace):
        w = WriteFileTool(target_directory=tmp_workspace)
        r = ReadFileTool(target_directory=tmp_workspace)
        lst = ListFilesTool(target_directory=tmp_workspace)
        names = {w.name, r.name, lst.name}
        assert names == {"write_file", "read_file", "list_files"}

    def test_write_unicode_then_read_unicode_round_trip(self, tmp_workspace):
        write_tool = WriteFileTool(target_directory=tmp_workspace)
        read_tool = ReadFileTool(target_directory=tmp_workspace)
        payload = "你好世界 — emoji 🚀 and accents café"
        write_tool.execute({"path": "unicode.txt", "content": payload})
        result = read_tool.execute({"path": "unicode.txt"})
        assert result.success is True
        assert result.output["content"] == payload


class TestFileOpsEdgeCases:
    """Edge cases: non-string path, list-on-file, symlink rejection."""

    def test_write_none_path_returns_boundary_error(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": None, "content": "x"})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_write_non_string_path_returns_boundary_error(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": 123, "content": "x"})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_read_none_path_returns_boundary_error(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": None})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_read_non_string_path_returns_boundary_error(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": 42})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_list_none_path_returns_boundary_error(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": None})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_list_non_string_path_returns_boundary_error(self, tmp_workspace):
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": 99})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_list_on_file_path_returns_empty_lists(self, tmp_workspace):
        """SPEC §3.2.3: path doesn't exist → return empty lists.
        A file path is not a listable directory, so return empty."""
        with open(os.path.join(tmp_workspace, "afile.txt"), "w") as f:
            f.write("data")
        tool = ListFilesTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "afile.txt"})
        assert result.success is True
        assert result.output["files"] == []
        assert result.output["dirs"] == []

    def test_write_missing_path_key_returns_boundary_error(self, tmp_workspace):
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute({"content": "x"})
        assert result.success is False
        assert result.error == "path out of bounds"

    def test_read_missing_path_key_returns_boundary_error(self, tmp_workspace):
        tool = ReadFileTool(target_directory=tmp_workspace)
        result = tool.execute({})
        assert result.success is False
        assert result.error == "path out of bounds"

    @pytest.mark.skipif(
        not hasattr(os, "symlink"),
        reason="Platform does not support symlinks",
    )
    def test_write_symlink_rejected_by_no_follow(self, tmp_workspace):
        """O_NOFOLLOW prevents writing through a symlink inside the target."""
        target = os.path.join(tmp_workspace, "real.txt")
        with open(target, "w", encoding="utf-8") as f:
            f.write("real")
        link = os.path.join(tmp_workspace, "link.txt")
        os.symlink(target, link)
        tool = WriteFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "link.txt", "content": "hijack"})
        assert result.success is False
        # The real file must not be modified
        with open(target, encoding="utf-8") as f:
            assert f.read() == "real"

    @pytest.mark.skipif(
        not hasattr(os, "symlink"),
        reason="Platform does not support symlinks",
    )
    def test_read_symlink_rejected_by_no_follow(self, tmp_workspace):
        """O_NOFOLLOW prevents reading through a symlink inside the target."""
        target = os.path.join(tmp_workspace, "real.txt")
        with open(target, "w", encoding="utf-8") as f:
            f.write("secret")
        link = os.path.join(tmp_workspace, "link.txt")
        os.symlink(target, link)
        tool = ReadFileTool(target_directory=tmp_workspace)
        result = tool.execute({"path": "link.txt"})
        assert result.success is False
