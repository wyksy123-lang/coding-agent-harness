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
    raw_tool_call: dict[str, Any] | None = None


@dataclass
class LLMResponse:
    """Represents the response returned by an LLM client."""

    content: str
    finish_reason: str
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMError(Exception):
    """Base class for safe, displayable LLM errors."""

    def __init__(
        self,
        *,
        kind: str,
        safe_message: str,
        status_code: int | None,
        retryable: bool,
        provider: str,
    ) -> None:
        super().__init__(safe_message)
        self.kind = kind
        self.safe_message = safe_message
        self.status_code = status_code
        self.retryable = retryable
        self.provider = provider


class LLMRequestError(LLMError):
    """Raised when the provider request fails or is rejected."""


class LLMResponseError(LLMError):
    """Raised when a successful provider response cannot be parsed safely."""


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
