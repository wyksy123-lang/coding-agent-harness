from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """Represents a single tool call requested by the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Represents the response returned by an LLM client."""

    content: str
    finish_reason: str
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMResponse:
        """Send a chat completion request to the LLM.

        Args:
            messages: A list of message dictionaries in OpenAI format.
            tools: A list of tool definitions in OpenAI format.

        Returns:
            An :class:`LLMResponse` containing the LLM's reply.
        """
