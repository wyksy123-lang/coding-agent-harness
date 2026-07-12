from __future__ import annotations

import inspect
from dataclasses import is_dataclass

import pytest

from harness.llm.base import LLMClient, LLMResponse, ToolCall


class TestToolCall:
    def test_tool_call_instantiation(self):
        tc = ToolCall(id="call_1", name="write_file", arguments={"path": "a.py"})
        assert tc.id == "call_1"
        assert tc.name == "write_file"
        assert tc.arguments == {"path": "a.py"}

    def test_tool_call_is_dataclass(self):
        assert is_dataclass(ToolCall)

    def test_tool_call_field_types(self):
        tc = ToolCall(id="call_1", name="write_file", arguments={})
        assert isinstance(tc.id, str)
        assert isinstance(tc.name, str)
        assert isinstance(tc.arguments, dict)

    def test_tool_call_empty_arguments(self):
        tc = ToolCall(id="call_2", name="finish", arguments={})
        assert tc.arguments == {}

    def test_tool_call_complex_nested_arguments(self):
        args = {
            "path": "src/main.py",
            "content": "print('hi')",
            "nested": {"key": [1, 2, 3], "flag": True},
        }
        tc = ToolCall(id="call_3", name="write_file", arguments=args)
        assert tc.arguments == args
        assert tc.arguments["nested"]["key"] == [1, 2, 3]
        assert tc.arguments["nested"]["flag"] is True

    def test_tool_call_equality(self):
        tc1 = ToolCall(id="x", name="read_file", arguments={"path": "a"})
        tc2 = ToolCall(id="x", name="read_file", arguments={"path": "a"})
        assert tc1 == tc2

    def test_tool_call_inequality_different_id(self):
        tc1 = ToolCall(id="x", name="read_file", arguments={"path": "a"})
        tc2 = ToolCall(id="y", name="read_file", arguments={"path": "a"})
        assert tc1 != tc2

    def test_tool_call_inequality_different_name(self):
        tc1 = ToolCall(id="x", name="read_file", arguments={"path": "a"})
        tc2 = ToolCall(id="x", name="write_file", arguments={"path": "a"})
        assert tc1 != tc2

    def test_tool_call_inequality_different_arguments(self):
        tc1 = ToolCall(id="x", name="read_file", arguments={"path": "a"})
        tc2 = ToolCall(id="x", name="read_file", arguments={"path": "b"})
        assert tc1 != tc2

    def test_tool_call_repr(self):
        tc = ToolCall(id="r1", name="run_tests", arguments={})
        repr_str = repr(tc)
        assert "ToolCall" in repr_str
        assert "run_tests" in repr_str


class TestLLMResponse:
    def test_llm_response_instantiation(self):
        tc = ToolCall(id="c1", name="write_file", arguments={"path": "a.py"})
        resp = LLMResponse(
            content="hello",
            tool_calls=[tc],
            finish_reason="tool_calls",
        )
        assert resp.content == "hello"
        assert resp.tool_calls == [tc]
        assert resp.finish_reason == "tool_calls"

    def test_llm_response_is_dataclass(self):
        assert is_dataclass(LLMResponse)

    def test_llm_response_field_types(self):
        resp = LLMResponse(content="hi", tool_calls=[], finish_reason="stop")
        assert isinstance(resp.content, str)
        assert isinstance(resp.tool_calls, list)
        assert isinstance(resp.finish_reason, str)

    def test_llm_response_empty_tool_calls(self):
        resp = LLMResponse(content="done", tool_calls=[], finish_reason="stop")
        assert resp.tool_calls == []

    def test_llm_response_completely_empty(self):
        resp = LLMResponse(content="", tool_calls=[], finish_reason="stop")
        assert resp.content == ""
        assert resp.tool_calls == []
        assert resp.finish_reason == "stop"

    def test_llm_response_multiple_tool_calls(self):
        tc1 = ToolCall(id="c1", name="write_file", arguments={"path": "a"})
        tc2 = ToolCall(id="c2", name="read_file", arguments={"path": "b"})
        tc3 = ToolCall(id="c3", name="run_tests", arguments={})
        resp = LLMResponse(
            content="",
            tool_calls=[tc1, tc2, tc3],
            finish_reason="tool_calls",
        )
        assert len(resp.tool_calls) == 3
        assert resp.tool_calls[0] == tc1
        assert resp.tool_calls[1] == tc2
        assert resp.tool_calls[2] == tc3

    def test_llm_response_tool_calls_default_empty(self):
        resp = LLMResponse(content="hi", finish_reason="stop")
        assert resp.tool_calls == []

    def test_llm_response_tool_calls_default_isolated(self):
        r1 = LLMResponse(content="a", finish_reason="stop")
        r2 = LLMResponse(content="b", finish_reason="stop")
        assert r1.tool_calls is not r2.tool_calls
        r1.tool_calls.append(ToolCall(id="z", name="x", arguments={}))
        assert len(r2.tool_calls) == 0

    def test_llm_response_equality(self):
        tc = ToolCall(id="c1", name="write_file", arguments={"path": "a"})
        r1 = LLMResponse(content="hi", tool_calls=[tc], finish_reason="stop")
        r2 = LLMResponse(content="hi", tool_calls=[tc], finish_reason="stop")
        assert r1 == r2

    def test_llm_response_inequality_different_content(self):
        r1 = LLMResponse(content="hi", tool_calls=[], finish_reason="stop")
        r2 = LLMResponse(content="bye", tool_calls=[], finish_reason="stop")
        assert r1 != r2

    def test_llm_response_inequality_different_finish_reason(self):
        r1 = LLMResponse(content="hi", tool_calls=[], finish_reason="stop")
        r2 = LLMResponse(content="hi", tool_calls=[], finish_reason="tool_calls")
        assert r1 != r2

    def test_llm_response_inequality_different_tool_calls(self):
        tc = ToolCall(id="c1", name="write_file", arguments={"path": "a"})
        r1 = LLMResponse(content="hi", tool_calls=[tc], finish_reason="stop")
        r2 = LLMResponse(content="hi", tool_calls=[], finish_reason="stop")
        assert r1 != r2

    def test_llm_response_repr(self):
        resp = LLMResponse(content="hi", tool_calls=[], finish_reason="stop")
        repr_str = repr(resp)
        assert "LLMResponse" in repr_str
        assert "hi" in repr_str


class TestLLMClientABC:
    def test_llm_client_is_abstract(self):
        assert inspect.isabstract(LLMClient)

    def test_llm_client_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            LLMClient()

    def test_llm_client_subclass_without_chat_cannot_be_instantiated(self):
        class _IncompleteClient(LLMClient):
            pass

        with pytest.raises(TypeError):
            _IncompleteClient()

    def test_llm_client_subclass_with_chat_can_be_instantiated(self):
        class _CompleteClient(LLMClient):
            def chat(self, messages, tools):
                return LLMResponse(
                    content="ok", tool_calls=[], finish_reason="stop"
                )

        client = _CompleteClient()
        assert isinstance(client, LLMClient)

    def test_llm_client_chat_signature_has_messages_and_tools(self):
        sig = inspect.signature(LLMClient.chat)
        params = set(sig.parameters.keys())
        assert "messages" in params
        assert "tools" in params

    def test_llm_client_chat_returns_llm_response(self):
        class _CompleteClient(LLMClient):
            def chat(self, messages, tools):
                return LLMResponse(
                    content="ok", tool_calls=[], finish_reason="stop"
                )

        client = _CompleteClient()
        result = client.chat(
            messages=[{"role": "user", "content": "hi"}], tools=[]
        )
        assert isinstance(result, LLMResponse)

    def test_llm_client_chat_returns_tool_calls(self):
        tc = ToolCall(id="c1", name="write_file", arguments={"path": "a.py"})

        class _CompleteClient(LLMClient):
            def chat(self, messages, tools):
                return LLMResponse(
                    content="",
                    tool_calls=[tc],
                    finish_reason="tool_calls",
                )

        client = _CompleteClient()
        result = client.chat(messages=[], tools=[])
        assert result.tool_calls == [tc]
        assert result.finish_reason == "tool_calls"

    def test_llm_client_chat_accepts_openai_format_messages(self):
        class _CompleteClient(LLMClient):
            def chat(self, messages, tools):
                assert isinstance(messages, list)
                assert isinstance(tools, list)
                return LLMResponse(
                    content="ok", tool_calls=[], finish_reason="stop"
                )

        client = _CompleteClient()
        messages = [
            {"role": "system", "content": "You are a coding agent."},
            {"role": "user", "content": "Write a test for foo."},
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
        assert isinstance(result, LLMResponse)
