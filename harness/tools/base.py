from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from harness.models import Action, Config


@dataclass
class ToolResult:
    """Result of executing a tool.

    Attributes:
        success: Whether the tool execution succeeded.
        output: The output data produced by the tool.
        error: An optional error message when execution failed.
    """

    success: bool
    output: dict[str, Any]
    error: str | None = None


class Tool(ABC):
    """Abstract base class for tools.

    Subclasses must implement the :attr:`name` and :attr:`schema`
    properties as well as the :meth:`execute` method.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the tool."""

    @property
    @abstractmethod
    def schema(self) -> dict[str, Any]:
        """Return the JSON schema describing the tool's arguments."""

    @abstractmethod
    def execute(self, args: dict[str, Any]) -> ToolResult:
        """Execute the tool with the given arguments.

        Args:
            args: The arguments to pass to the tool.

        Returns:
            A :class:`ToolResult` with the execution outcome.
        """


class ToolRegistry:
    """Registry for managing and dispatching tools.

    Args:
        config: The configuration containing the enabled tools whitelist.
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool.

        If a tool with the same name is already registered, it is
        overwritten.

        Args:
            tool: The tool to register.
        """
        self._tools[tool.name] = tool

    def is_enabled(self, tool_name: str) -> bool:
        """Check if a tool is in the enabled_tools whitelist.

        Args:
            tool_name: The name of the tool to check.

        Returns:
            True if the tool is enabled, False otherwise.
        """
        return tool_name in self._config.enabled_tools

    def dispatch(self, action: Action) -> ToolResult:
        """Dispatch an action to the registered tool.

        Only tools present in the ``enabled_tools`` whitelist may be
        dispatched.

        Args:
            action: The action to dispatch.

        Returns:
            The result of executing the tool.

        Raises:
            KeyError: If the tool is not registered.
            PermissionError: If the tool is registered but not enabled.
        """
        if action.tool_name not in self._tools:
            raise KeyError(action.tool_name)
        if not self.is_enabled(action.tool_name):
            raise PermissionError(f"Tool '{action.tool_name}' is not enabled")
        return self._tools[action.tool_name].execute(action.args)

    def get_schemas(self) -> list[dict[str, Any]]:
        """Return the schemas of all registered tools.

        Returns:
            A list of JSON schema dictionaries.
        """
        return [tool.schema for tool in self._tools.values()]
