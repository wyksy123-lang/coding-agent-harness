from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from harness.llm.base import LLMClient, LLMResponse, ToolCall


@dataclass
class RecordedCall:
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]]


class MockLLMClient(LLMClient):
    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = list(responses)
        self._index = 0
        self.recorded_calls: list[RecordedCall] = []

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> LLMResponse:
        self.recorded_calls.append(RecordedCall(messages=messages, tools=tools))
        if self._index >= len(self._responses):
            raise StopIteration
        response = self._responses[self._index]
        self._index += 1
        return response

    @classmethod
    def from_tool_calls(
        cls, tool_call_lists: list[list[ToolCall]]
    ) -> MockLLMClient:
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
