from __future__ import annotations

import pytest

from harness.llm.base import LLMClient, LLMResponse, ToolCall
from harness.llm.mock import MockLLMClient


def _make_response(content: str = "hello", finish_reason: str = "stop") -> LLMResponse:
    return LLMResponse(content=content, tool_calls=[], finish_reason=finish_reason)


class TestMockLLMClientConstruction:
    def test_construct_with_list_of_llm_responses(self):
        responses = [
            LLMResponse(content="first", tool_calls=[], finish_reason="stop"),
            LLMResponse(content="second", tool_calls=[], finish_reason="stop"),
        ]
        client = MockLLMClient(responses)
        assert client is not None

    def test_is_subclass_of_llm_client(self):
        assert issubclass(MockLLMClient, LLMClient)

    def test_instance_is_llm_client(self):
        client = MockLLMClient([_make_response()])
        assert isinstance(client, LLMClient)

    def test_can_be_constructed_with_empty_list(self):
        client = MockLLMClient([])
        assert client is not None


class TestMockLLMClientReturnsResponsesInOrder:
    def test_first_call_returns_first_response(self):
        r1 = LLMResponse(content="first", tool_calls=[], finish_reason="stop")
        r2 = LLMResponse(content="second", tool_calls=[], finish_reason="stop")
        client = MockLLMClient([r1, r2])
        result = client.chat(messages=[], tools=[])
        assert result == r1

    def test_second_call_returns_second_response(self):
        r1 = LLMResponse(content="first", tool_calls=[], finish_reason="stop")
        r2 = LLMResponse(content="second", tool_calls=[], finish_reason="stop")
        client = MockLLMClient([r1, r2])
        client.chat(messages=[], tools=[])
        result = client.chat(messages=[], tools=[])
        assert result == r2

    def test_calls_return_responses_in_exact_order(self):
        r1 = LLMResponse(content="first", tool_calls=[], finish_reason="stop")
        r2 = LLMResponse(content="second", tool_calls=[], finish_reason="stop")
        client = MockLLMClient([r1, r2])
        assert client.chat(messages=[], tools=[]) == r1
        assert client.chat(messages=[], tools=[]) == r2

    def test_ordering_with_three_responses(self):
        r1 = LLMResponse(content="first", tool_calls=[], finish_reason="stop")
        r2 = LLMResponse(content="second", tool_calls=[], finish_reason="stop")
        r3 = LLMResponse(content="third", tool_calls=[], finish_reason="stop")
        client = MockLLMClient([r1, r2, r3])
        assert client.chat(messages=[], tools=[]) == r1
        assert client.chat(messages=[], tools=[]) == r2
        assert client.chat(messages=[], tools=[]) == r3

    def test_returns_response_with_tool_calls(self):
        tc = ToolCall(id="c1", name="write_file", arguments={"path": "a.py"})
        r1 = LLMResponse(content="", tool_calls=[tc], finish_reason="tool_calls")
        client = MockLLMClient([r1])
        result = client.chat(messages=[], tools=[])
        assert result.tool_calls == [tc]
        assert result.finish_reason == "tool_calls"


class TestMockLLMClientExhaustion:
    def test_call_after_exhaustion_raises_exception(self):
        r1 = LLMResponse(content="first", tool_calls=[], finish_reason="stop")
        r2 = LLMResponse(content="second", tool_calls=[], finish_reason="stop")
        client = MockLLMClient([r1, r2])
        client.chat(messages=[], tools=[])
        client.chat(messages=[], tools=[])
        with pytest.raises(StopIteration):
            client.chat(messages=[], tools=[])

    def test_single_response_first_call_succeeds_second_raises(self):
        r1 = LLMResponse(content="only", tool_calls=[], finish_reason="stop")
        client = MockLLMClient([r1])
        result = client.chat(messages=[], tools=[])
        assert result == r1
        with pytest.raises(StopIteration):
            client.chat(messages=[], tools=[])


class TestMockLLMClientFromToolCalls:
    def test_from_tool_calls_creates_client_from_tool_call_lists(self):
        tc1 = ToolCall(id="c1", name="write_file", arguments={"path": "a"})
        tc2 = ToolCall(id="c2", name="read_file", arguments={"path": "b"})
        client = MockLLMClient.from_tool_calls([[tc1], [tc2]])
        assert isinstance(client, MockLLMClient)
        assert isinstance(client, LLMClient)

    def test_each_response_has_correct_tool_calls(self):
        tc1 = ToolCall(id="c1", name="write_file", arguments={"path": "a"})
        tc2 = ToolCall(id="c2", name="read_file", arguments={"path": "b"})
        client = MockLLMClient.from_tool_calls([[tc1], [tc2]])
        first = client.chat(messages=[], tools=[])
        second = client.chat(messages=[], tools=[])
        assert first.tool_calls == [tc1]
        assert second.tool_calls == [tc2]

    def test_created_responses_have_sensible_defaults(self):
        tc = ToolCall(id="c1", name="write_file", arguments={"path": "a"})
        client = MockLLMClient.from_tool_calls([[tc], []])
        with_tool_calls = client.chat(messages=[], tools=[])
        without_tool_calls = client.chat(messages=[], tools=[])
        assert isinstance(with_tool_calls.content, str)
        assert with_tool_calls.finish_reason == "tool_calls"
        assert isinstance(without_tool_calls.content, str)
        assert without_tool_calls.finish_reason == "stop"

    def test_from_tool_calls_with_empty_tool_call_lists(self):
        client = MockLLMClient.from_tool_calls([[], []])
        first = client.chat(messages=[], tools=[])
        second = client.chat(messages=[], tools=[])
        assert first.tool_calls == []
        assert second.tool_calls == []

    def test_from_tool_calls_with_multiple_tool_calls_per_response(self):
        tc1 = ToolCall(id="c1", name="write_file", arguments={"path": "a"})
        tc2 = ToolCall(id="c2", name="read_file", arguments={"path": "b"})
        tc3 = ToolCall(id="c3", name="run_tests", arguments={})
        client = MockLLMClient.from_tool_calls([[tc1, tc2], [tc3]])
        first = client.chat(messages=[], tools=[])
        second = client.chat(messages=[], tools=[])
        assert first.tool_calls == [tc1, tc2]
        assert second.tool_calls == [tc3]

    def test_from_tool_calls_returns_mock_with_correct_count(self):
        tc = ToolCall(id="c1", name="write_file", arguments={"path": "a"})
        client = MockLLMClient.from_tool_calls([[tc], [tc], [tc]])
        client.chat(messages=[], tools=[])
        client.chat(messages=[], tools=[])
        client.chat(messages=[], tools=[])
        with pytest.raises(StopIteration):
            client.chat(messages=[], tools=[])


class TestMockLLMClientRecordsCalls:
    def test_recorded_calls_starts_empty(self):
        client = MockLLMClient([_make_response()])
        assert client.recorded_calls == []

    def test_messages_are_recorded_after_chat(self):
        client = MockLLMClient([_make_response()])
        messages = [{"role": "user", "content": "hello"}]
        client.chat(messages=messages, tools=[])
        assert len(client.recorded_calls) == 1
        assert client.recorded_calls[0].messages == messages

    def test_tools_are_recorded_after_chat(self):
        client = MockLLMClient([_make_response()])
        tools = [{"type": "function", "function": {"name": "write_file"}}]
        client.chat(messages=[], tools=tools)
        assert len(client.recorded_calls) == 1
        assert client.recorded_calls[0].tools == tools

    def test_multiple_calls_recorded_in_order(self):
        r1 = _make_response("first")
        r2 = _make_response("second")
        client = MockLLMClient([r1, r2])
        m1 = [{"role": "user", "content": "first"}]
        m2 = [{"role": "user", "content": "second"}]
        client.chat(messages=m1, tools=[])
        client.chat(messages=m2, tools=[])
        assert len(client.recorded_calls) == 2
        assert client.recorded_calls[0].messages == m1
        assert client.recorded_calls[1].messages == m2

    def test_recorded_messages_match_passed_messages(self):
        client = MockLLMClient([_make_response()])
        messages = [
            {"role": "system", "content": "You are a coding agent."},
            {"role": "user", "content": "Write a test for foo."},
        ]
        client.chat(messages=messages, tools=[])
        assert client.recorded_calls[0].messages == messages

    def test_recorded_tools_match_passed_tools(self):
        client = MockLLMClient([_make_response()])
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write a file",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
        client.chat(messages=[], tools=tools)
        assert client.recorded_calls[0].tools == tools

    def test_call_recorded_even_when_exhausted(self):
        r1 = LLMResponse(content="only", tool_calls=[], finish_reason="stop")
        client = MockLLMClient([r1])
        client.chat(messages=[], tools=[])
        with pytest.raises(StopIteration):
            client.chat(messages=[], tools=[])
        assert len(client.recorded_calls) == 2

    def test_recorded_messages_isolated_from_caller_mutations(self):
        client = MockLLMClient([_make_response()])
        messages = [{"role": "user", "content": "hello"}]
        client.chat(messages=messages, tools=[])
        messages.append({"role": "user", "content": "mutated"})
        assert len(client.recorded_calls[0].messages) == 1

    def test_recorded_tools_isolated_from_caller_mutations(self):
        client = MockLLMClient([_make_response()])
        tools = [{"type": "function", "function": {"name": "write_file"}}]
        client.chat(messages=[], tools=tools)
        tools.append({"type": "function", "function": {"name": "read_file"}})
        assert len(client.recorded_calls[0].tools) == 1


class TestMockLLMClientEdgeCases:
    def test_empty_response_list_raises_on_first_call(self):
        client = MockLLMClient([])
        with pytest.raises(StopIteration):
            client.chat(messages=[], tools=[])

    def test_accepts_openai_format_messages(self):
        r1 = LLMResponse(content="ok", tool_calls=[], finish_reason="stop")
        client = MockLLMClient([r1])
        messages = [
            {"role": "system", "content": "You are a coding agent."},
            {"role": "user", "content": "Write a test for foo."},
            {"role": "assistant", "content": "Sure, here is a test."},
            {"role": "tool", "tool_call_id": "c1", "content": "result"},
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write a file",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
        result = client.chat(messages=messages, tools=tools)
        assert result == r1
        assert client.recorded_calls[0].messages == messages
        assert client.recorded_calls[0].tools == tools

    def test_mutable_default_isolation(self):
        r1 = LLMResponse(content="first", tool_calls=[], finish_reason="stop")
        responses = [r1]
        client = MockLLMClient(responses)
        responses.append(
            LLMResponse(content="injected", tool_calls=[], finish_reason="stop")
        )
        result = client.chat(messages=[], tools=[])
        assert result == r1
        with pytest.raises(StopIteration):
            client.chat(messages=[], tools=[])

    def test_chat_returns_llm_response_instance(self):
        r1 = LLMResponse(content="hi", tool_calls=[], finish_reason="stop")
        client = MockLLMClient([r1])
        result = client.chat(messages=[], tools=[])
        assert isinstance(result, LLMResponse)

    def test_from_tool_calls_with_empty_list_raises_on_first_chat(self):
        client = MockLLMClient.from_tool_calls([])
        with pytest.raises(StopIteration):
            client.chat(messages=[], tools=[])
