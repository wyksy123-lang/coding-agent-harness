from __future__ import annotations

from pathlib import Path

import pytest

from harness.config.loader import ConfigError, ConfigLoader
from harness.models import Config

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _write_yaml(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


FULL_VALID_YAML = """\
max_rounds: 5
target_directory: /tmp/test
test_command: "pytest -x"
model: "gpt-4"
temperature: 0.5
memory_file: "custom.json"
enabled_tools:
  - write_file
  - read_file
dangerous_command_patterns:
  - "rm"
  - "sudo"
hitl_timeout_seconds: 60
llm_timeout: 30
pytest_timeout: 30
stuck_threshold: 5
llm_retry_count: 2
"""


class TestConfigError:
    def test_config_error_is_exception_subclass(self):
        assert issubclass(ConfigError, Exception)

    def test_config_error_can_be_raised(self):
        with pytest.raises(ConfigError):
            raise ConfigError("test error")

    def test_config_error_carries_message(self):
        err = ConfigError("something went wrong")
        assert "something went wrong" in str(err)

    def test_config_error_is_distinct_from_value_error(self):
        assert ConfigError is not ValueError
        assert ConfigError is not KeyError


class TestConfigLoaderLoadValid:
    def test_load_returns_config_instance(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", FULL_VALID_YAML)
        config = ConfigLoader.load(str(path))
        assert isinstance(config, Config)

    def test_load_parses_all_thirteen_fields(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", FULL_VALID_YAML)
        config = ConfigLoader.load(str(path))
        assert config.max_rounds == 5
        assert config.target_directory == "/tmp/test"
        assert config.test_command == "pytest -x"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.memory_file == "custom.json"
        assert config.enabled_tools == ["write_file", "read_file"]
        assert config.dangerous_command_patterns == ["rm", "sudo"]
        assert config.hitl_timeout_seconds == 60
        assert config.llm_timeout == 30
        assert config.pytest_timeout == 30
        assert config.stuck_threshold == 5
        assert config.llm_retry_count == 2

    def test_load_accepts_pathlib_path(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", FULL_VALID_YAML)
        config = ConfigLoader.load(path)
        assert isinstance(config, Config)

    def test_load_with_string_values(self, tmp_path):
        yaml_content = 'model: "claude-3"\ntarget_directory: /custom/dir\n'
        path = _write_yaml(tmp_path / "harness.yaml", yaml_content)
        config = ConfigLoader.load(str(path))
        assert config.model == "claude-3"
        assert config.target_directory == "/custom/dir"


class TestConfigLoaderDefaults:
    def test_single_field_set_others_default(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "max_rounds: 20\n")
        config = ConfigLoader.load(str(path))
        assert config.max_rounds == 20
        assert config.target_directory == "./workspace"
        assert config.test_command == "pytest --json-report --output=.harness/report.json"
        assert config.model == "deepseek-chat"
        assert config.temperature == 0.1
        assert config.memory_file == ".harness/memory.json"
        assert config.enabled_tools == [
            "write_file",
            "read_file",
            "list_files",
            "run_tests",
            "run_command",
            "finish",
        ]
        assert config.dangerous_command_patterns == [
            r"rm\s+-rf",
            r"git\s+push",
            r"sudo\s+",
            r"curl\s+|wget\s+",
            r"docker\s+",
        ]
        assert config.hitl_timeout_seconds == 300
        assert config.llm_timeout == 60
        assert config.pytest_timeout == 60
        assert config.stuck_threshold == 3
        assert config.llm_retry_count == 3

    def test_empty_yaml_returns_all_defaults(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "")
        config = ConfigLoader.load(str(path))
        default = Config()
        assert config.max_rounds == default.max_rounds
        assert config.target_directory == default.target_directory
        assert config.test_command == default.test_command
        assert config.model == default.model
        assert config.temperature == default.temperature
        assert config.memory_file == default.memory_file
        assert config.enabled_tools == default.enabled_tools
        assert config.dangerous_command_patterns == default.dangerous_command_patterns
        assert config.hitl_timeout_seconds == default.hitl_timeout_seconds
        assert config.llm_timeout == default.llm_timeout
        assert config.pytest_timeout == default.pytest_timeout
        assert config.stuck_threshold == default.stuck_threshold
        assert config.llm_retry_count == default.llm_retry_count

    def test_partial_fields_fill_remaining_defaults(self, tmp_path):
        yaml_content = 'model: "gpt-4"\ntemperature: 0.7\n'
        path = _write_yaml(tmp_path / "harness.yaml", yaml_content)
        config = ConfigLoader.load(str(path))
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_rounds == 10
        assert config.llm_retry_count == 3

    def test_yaml_with_only_document_separator_returns_defaults(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "---\n")
        config = ConfigLoader.load(str(path))
        assert config.max_rounds == 10
        assert config.model == "deepseek-chat"


class TestConfigLoaderUnknownFields:
    def test_unknown_fields_are_ignored(self, tmp_path):
        yaml_content = "max_rounds: 15\nunknown_field: some_value\nanother_unknown: 42\n"
        path = _write_yaml(tmp_path / "harness.yaml", yaml_content)
        config = ConfigLoader.load(str(path))
        assert config.max_rounds == 15

    def test_unknown_fields_do_not_attach_to_config(self, tmp_path):
        yaml_content = "max_rounds: 15\nunknown_field: some_value\n"
        path = _write_yaml(tmp_path / "harness.yaml", yaml_content)
        config = ConfigLoader.load(str(path))
        assert not hasattr(config, "unknown_field")

    def test_unknown_nested_fields_are_ignored(self, tmp_path):
        yaml_content = "max_rounds: 15\nextra:\n  nested: value\n  deep: 1\n"
        path = _write_yaml(tmp_path / "harness.yaml", yaml_content)
        config = ConfigLoader.load(str(path))
        assert config.max_rounds == 15


class TestConfigLoaderInvalidYaml:
    def test_invalid_yaml_raises_config_error(self, tmp_path):
        yaml_content = "max_rounds: [1, 2, 3\n"
        path = _write_yaml(tmp_path / "harness.yaml", yaml_content)
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))

    def test_yaml_with_tab_indentation_raises_config_error(self, tmp_path):
        yaml_content = "max_rounds: 10\n\tbad_indent: oops\n"
        path = _write_yaml(tmp_path / "harness.yaml", yaml_content)
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))

    def test_file_not_found_raises_config_error(self, tmp_path):
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(tmp_path / "nonexistent.yaml"))


class TestConfigLoaderTypeValidation:
    def test_max_rounds_as_string_raises_config_error(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", 'max_rounds: "ten"\n')
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))

    def test_temperature_as_string_raises_config_error(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", 'temperature: "warm"\n')
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))

    def test_hitl_timeout_as_string_raises_config_error(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", 'hitl_timeout_seconds: "fast"\n')
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))

    def test_enabled_tools_as_string_raises_config_error(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "enabled_tools: not_a_list\n")
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))

    def test_dangerous_patterns_as_int_raises_config_error(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "dangerous_command_patterns: 42\n")
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))

    def test_enabled_tools_with_non_string_element_raises_config_error(self, tmp_path):
        yaml_content = "enabled_tools:\n  - write_file\n  - 123\n"
        path = _write_yaml(tmp_path / "harness.yaml", yaml_content)
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))

    def test_dangerous_patterns_with_non_string_element_raises_config_error(self, tmp_path):
        yaml_content = "dangerous_command_patterns:\n  - \"rm\"\n  - 99\n"
        path = _write_yaml(tmp_path / "harness.yaml", yaml_content)
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))

    def test_bool_for_int_field_raises_config_error(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "max_rounds: true\n")
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))

    def test_bool_for_float_field_raises_config_error(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "temperature: true\n")
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))

    def test_null_value_for_int_field_raises_config_error(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "max_rounds: null\n")
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))


class TestConfigLoaderNonDictRoot:
    def test_list_root_raises_config_error(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "- a\n- b\n")
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))

    def test_scalar_root_raises_config_error(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "42\n")
        with pytest.raises(ConfigError):
            ConfigLoader.load(str(path))


class TestConfigLoaderCoercionAndIsolation:
    def test_int_temperature_coerced_to_float(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "temperature: 1\n")
        config = ConfigLoader.load(str(path))
        assert isinstance(config.temperature, float)
        assert config.temperature == 1.0

    def test_list_values_are_copied_not_aliased(self, tmp_path):
        yaml_content = "enabled_tools:\n  - write_file\n  - read_file\n"
        path = _write_yaml(tmp_path / "harness.yaml", yaml_content)
        config = ConfigLoader.load(str(path))
        config.enabled_tools.append("run_tests")
        # Re-load to verify the original was not mutated
        config2 = ConfigLoader.load(str(path))
        assert "run_tests" not in config2.enabled_tools


class TestConfigLoaderFieldTypes:
    def test_dangerous_command_patterns_is_list_of_strings(self, tmp_path):
        yaml_content = 'dangerous_command_patterns:\n  - "rm"\n  - "sudo"\n'
        path = _write_yaml(tmp_path / "harness.yaml", yaml_content)
        config = ConfigLoader.load(str(path))
        assert isinstance(config.dangerous_command_patterns, list)
        assert all(isinstance(p, str) for p in config.dangerous_command_patterns)

    def test_enabled_tools_is_list_of_strings(self, tmp_path):
        yaml_content = "enabled_tools:\n  - write_file\n  - read_file\n"
        path = _write_yaml(tmp_path / "harness.yaml", yaml_content)
        config = ConfigLoader.load(str(path))
        assert isinstance(config.enabled_tools, list)
        assert all(isinstance(t, str) for t in config.enabled_tools)

    def test_max_rounds_is_int(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "max_rounds: 7\n")
        config = ConfigLoader.load(str(path))
        assert isinstance(config.max_rounds, int)
        assert not isinstance(config.max_rounds, bool)

    def test_temperature_is_float(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "temperature: 0.5\n")
        config = ConfigLoader.load(str(path))
        assert isinstance(config.temperature, float)

    def test_default_dangerous_patterns_are_regex_strings(self, tmp_path):
        path = _write_yaml(tmp_path / "harness.yaml", "")
        config = ConfigLoader.load(str(path))
        for pattern in config.dangerous_command_patterns:
            assert isinstance(pattern, str)


class TestHarnessYamlExample:
    def test_example_file_exists(self):
        example_path = REPO_ROOT / "harness.yaml.example"
        assert example_path.exists(), (
            f"harness.yaml.example not found at {example_path}"
        )

    def test_example_file_can_be_loaded(self):
        example_path = REPO_ROOT / "harness.yaml.example"
        config = ConfigLoader.load(str(example_path))
        assert isinstance(config, Config)

    def test_example_file_contains_all_thirteen_fields(self):
        example_path = REPO_ROOT / "harness.yaml.example"
        config = ConfigLoader.load(str(example_path))
        assert isinstance(config.max_rounds, int)
        assert isinstance(config.target_directory, str)
        assert isinstance(config.test_command, str)
        assert isinstance(config.model, str)
        assert isinstance(config.temperature, (int, float))
        assert isinstance(config.memory_file, str)
        assert isinstance(config.enabled_tools, list)
        assert isinstance(config.dangerous_command_patterns, list)
        assert isinstance(config.hitl_timeout_seconds, int)
        assert isinstance(config.llm_timeout, int)
        assert isinstance(config.pytest_timeout, int)
        assert isinstance(config.stuck_threshold, int)
        assert isinstance(config.llm_retry_count, int)

    def test_example_file_enabled_tools_are_strings(self):
        example_path = REPO_ROOT / "harness.yaml.example"
        config = ConfigLoader.load(str(example_path))
        assert all(isinstance(t, str) for t in config.enabled_tools)

    def test_example_file_dangerous_patterns_are_strings(self):
        example_path = REPO_ROOT / "harness.yaml.example"
        config = ConfigLoader.load(str(example_path))
        assert all(isinstance(p, str) for p in config.dangerous_command_patterns)
