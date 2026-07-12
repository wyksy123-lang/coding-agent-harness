from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from harness.llm.base import LLMClient, LLMResponse, ToolCall


@dataclass
class RecordedCall:
    """A record of a single ``chat()`` call's input parameters."""

    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]]


class MockLLMClient(LLMClient):
    """LLM client that returns preset responses for offline deterministic testing.

    Responses are returned in the order provided. Once all responses are
    exhausted, subsequent calls raise :class:`StopIteration`. Each call's
    messages and tools are recorded in :attr:`recorded_calls` for test
    assertions.
    """

    def __init__(self, responses: list[LLMResponse]) -> None:
        """Initialize with a list of preset responses.

        Args:
            responses: The ordered list of responses to return. The list is
                copied so external mutations do not affect the client.
        """
        self._responses = list(responses)
        self._index = 0
        self.recorded_calls: list[RecordedCall] = []

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> LLMResponse:
        """Return the next preset response and record the call parameters.

        Args:
            messages: Chat messages in OpenAI format.
            tools: Tool definitions in OpenAI format.

        Returns:
            The next preset :class:`LLMResponse`.

        Raises:
            StopIteration: If all preset responses have been exhausted.
        """
        self.recorded_calls.append(
            RecordedCall(messages=list(messages), tools=list(tools))
        )
        if self._index >= len(self._responses):
            raise StopIteration
        response = self._responses[self._index]
        self._index += 1
        return response

    @classmethod
    def from_tool_calls(
        cls, tool_call_lists: list[list[ToolCall]]
    ) -> MockLLMClient:
        """Create a MockLLMClient from a list of tool call lists.

        Each inner list becomes the ``tool_calls`` of one
        :class:`LLMResponse`. Responses with tool calls use
        ``finish_reason="tool_calls"``; empty ones use ``finish_reason="stop"``.

        Args:
            tool_call_lists: A list where each element is a list of
                :class:`ToolCall` objects for one response.

        Returns:
            A :class:`MockLLMClient` preloaded with the constructed responses.
        """
        responses: list[LLMResponse] = []
        for tool_calls in tool_call_lists:
            if tool_calls:
                responses.append(
                    LLMResponse(
                        content="",
                        finish_reason="tool_calls",
                        tool_calls=list(tool_calls),
                    )
                )
            else:
                responses.append(
                    LLMResponse(content="", finish_reason="stop", tool_calls=[])
                )
        return cls(responses)
