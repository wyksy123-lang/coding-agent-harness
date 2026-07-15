from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from httpx import MockTransport

import harness.llm.base as llm_base
from harness.llm.base import LLMClient, LLMResponse, ToolCall
from harness.llm.deepseek import DeepSeekClient

FAKE_API_KEY = "sk-fake-test-key-not-real"


def _make_api_response(
    content: str = "Hello!",
    finish_reason: str = "stop",
    tool_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": finish_reason,
            }
        ],
    }


def _make_tool_call_dict(
    call_id: str = "call_abc",
    name: str = "write_file",
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if arguments is None:
        arguments = {"path": "test.py"}
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments),
        },
    }


def _make_client(
    transport: httpx.BaseTransport | None = None,
    *,
    api_key: str = FAKE_API_KEY,
    model: str = "deepseek-chat",
    temperature: float = 0.1,
    timeout: int = 60,
    retry_count: int = 3,
) -> DeepSeekClient:
    return DeepSeekClient(
        api_key=api_key,
        model=model,
        temperature=temperature,
        timeout=timeout,
        retry_count=retry_count,
        transport=transport,
    )


class TestDeepSeekClientConstruction:
    def test_can_be_constructed_with_all_parameters(self):
        client = DeepSeekClient(
            api_key=FAKE_API_KEY,
            model="deepseek-chat",
            temperature=0.1,
            timeout=60,
            retry_count=3,
        )
        assert client is not None

    def test_is_subclass_of_llm_client(self):
        assert issubclass(DeepSeekClient, LLMClient)

    def test_instance_is_llm_client(self):
        client = _make_client()
        assert isinstance(client, LLMClient)

    def test_can_be_constructed_with_transport(self):
        transport = MockTransport(
            lambda req: httpx.Response(200, json=_make_api_response())
        )
        client = DeepSeekClient(
            api_key=FAKE_API_KEY,
            model="deepseek-chat",
            temperature=0.1,
            timeout=60,
            retry_count=3,
            transport=transport,
        )
        assert client is not None

    def test_transport_parameter_is_optional(self):
        sig = inspect.signature(DeepSeekClient.__init__)
        transport_param = sig.parameters.get("transport")
        assert transport_param is not None
        assert transport_param.default is None


class TestDeepSeekClientRequestConstruction:
    def test_sends_post_request(self):
        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["method"] = request.method
            return httpx.Response(200, json=_make_api_response())

        client = _make_client(transport=MockTransport(handler))
        client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert captured["method"] == "POST"

    def test_request_url_is_deepseek_chat_completions(self):
        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            return httpx.Response(200, json=_make_api_response())

        client = _make_client(transport=MockTransport(handler))
        client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        url = captured["url"]
        assert "deepseek.com" in url
        assert "chat/completions" in url

    def test_request_has_authorization_header_with_bearer_token(self):
        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["auth"] = request.headers.get("authorization")
            return httpx.Response(200, json=_make_api_response())

        client = _make_client(transport=MockTransport(handler))
        client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert captured["auth"] == f"Bearer {FAKE_API_KEY}"

    def test_request_body_contains_model(self):
        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=_make_api_response())

        client = _make_client(transport=MockTransport(handler), model="deepseek-chat")
        client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert captured["body"]["model"] == "deepseek-chat"

    def test_request_body_contains_messages(self):
        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=_make_api_response())

        messages = [
            {"role": "system", "content": "You are a coding agent."},
            {"role": "user", "content": "Write a test."},
        ]
        client = _make_client(transport=MockTransport(handler))
        client.chat(messages=messages, tools=[])
        assert captured["body"]["messages"] == messages

    def test_request_body_contains_tools(self):
        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=_make_api_response())

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
        client = _make_client(transport=MockTransport(handler))
        client.chat(messages=[{"role": "user", "content": "hi"}], tools=tools)
        assert captured["body"]["tools"] == tools

    def test_request_body_contains_temperature(self):
        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=_make_api_response())

        client = _make_client(transport=MockTransport(handler), temperature=0.7)
        client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert captured["body"]["temperature"] == 0.7

    def test_request_body_contains_all_expected_fields(self):
        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=_make_api_response())

        messages = [{"role": "user", "content": "hi"}]
        tools = [{"type": "function", "function": {"name": "write_file"}}]
        client = _make_client(
            transport=MockTransport(handler),
            model="deepseek-chat",
            temperature=0.1,
        )
        client.chat(messages=messages, tools=tools)
        body = captured["body"]
        assert body["model"] == "deepseek-chat"
        assert body["messages"] == messages
        assert body["tools"] == tools
        assert body["temperature"] == 0.1


class TestDeepSeekClientResponseParsingNoToolCalls:
    def test_returns_llm_response_instance(self):
        transport = MockTransport(
            lambda req: httpx.Response(200, json=_make_api_response())
        )
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert isinstance(result, LLMResponse)

    def test_returns_correct_content(self):
        api_response = _make_api_response(content="Hello, world!")
        transport = MockTransport(lambda req: httpx.Response(200, json=api_response))
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert result.content == "Hello, world!"

    def test_returns_correct_finish_reason_stop(self):
        api_response = _make_api_response(content="Done.", finish_reason="stop")
        transport = MockTransport(lambda req: httpx.Response(200, json=api_response))
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert result.finish_reason == "stop"

    def test_returns_empty_tool_calls_when_none_in_response(self):
        api_response = _make_api_response(content="No tools needed.")
        transport = MockTransport(lambda req: httpx.Response(200, json=api_response))
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert result.tool_calls == []


class TestDeepSeekClientResponseParsingWithToolCalls:
    def test_returns_tool_call_with_correct_id(self):
        api_response = _make_api_response(
            content="",
            finish_reason="tool_calls",
            tool_calls=[_make_tool_call_dict(call_id="call_123")],
        )
        transport = MockTransport(lambda req: httpx.Response(200, json=api_response))
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].id == "call_123"

    def test_returns_tool_call_with_correct_name(self):
        api_response = _make_api_response(
            content="",
            finish_reason="tool_calls",
            tool_calls=[_make_tool_call_dict(name="write_file")],
        )
        transport = MockTransport(lambda req: httpx.Response(200, json=api_response))
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert result.tool_calls[0].name == "write_file"

    def test_parses_tool_call_arguments_from_json_string_to_dict(self):
        api_response = _make_api_response(
            content="",
            finish_reason="tool_calls",
            tool_calls=[
                _make_tool_call_dict(
                    arguments={"path": "test.py", "content": "print('hi')"}
                )
            ],
        )
        transport = MockTransport(lambda req: httpx.Response(200, json=api_response))
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert result.tool_calls[0].arguments == {
            "path": "test.py",
            "content": "print('hi')",
        }

    def test_tool_call_arguments_is_dict_not_string(self):
        api_response = _make_api_response(
            content="",
            finish_reason="tool_calls",
            tool_calls=[_make_tool_call_dict(arguments={"path": "test.py"})],
        )
        transport = MockTransport(lambda req: httpx.Response(200, json=api_response))
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert isinstance(result.tool_calls[0].arguments, dict)

    def test_returns_correct_finish_reason_tool_calls(self):
        api_response = _make_api_response(
            content="",
            finish_reason="tool_calls",
            tool_calls=[_make_tool_call_dict()],
        )
        transport = MockTransport(lambda req: httpx.Response(200, json=api_response))
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert result.finish_reason == "tool_calls"

    def test_tool_call_is_tool_call_instance(self):
        api_response = _make_api_response(
            content="",
            finish_reason="tool_calls",
            tool_calls=[_make_tool_call_dict()],
        )
        transport = MockTransport(lambda req: httpx.Response(200, json=api_response))
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert isinstance(result.tool_calls[0], ToolCall)


class TestDeepSeekClientResponseParsingMultipleToolCalls:
    def test_parses_multiple_tool_calls(self):
        api_response = _make_api_response(
            content="",
            finish_reason="tool_calls",
            tool_calls=[
                _make_tool_call_dict(
                    call_id="c1", name="write_file", arguments={"path": "a.py"}
                ),
                _make_tool_call_dict(
                    call_id="c2", name="read_file", arguments={"path": "b.py"}
                ),
                _make_tool_call_dict(
                    call_id="c3", name="run_tests", arguments={}
                ),
            ],
        )
        transport = MockTransport(lambda req: httpx.Response(200, json=api_response))
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert len(result.tool_calls) == 3
        assert result.tool_calls[0].id == "c1"
        assert result.tool_calls[0].name == "write_file"
        assert result.tool_calls[0].arguments == {"path": "a.py"}
        assert result.tool_calls[1].id == "c2"
        assert result.tool_calls[1].name == "read_file"
        assert result.tool_calls[1].arguments == {"path": "b.py"}
        assert result.tool_calls[2].id == "c3"
        assert result.tool_calls[2].name == "run_tests"
        assert result.tool_calls[2].arguments == {}

    def test_parses_two_tool_calls_with_different_arguments(self):
        api_response = _make_api_response(
            content="",
            finish_reason="tool_calls",
            tool_calls=[
                _make_tool_call_dict(
                    call_id="c1",
                    name="write_file",
                    arguments={"path": "src/main.py", "content": "x = 1"},
                ),
                _make_tool_call_dict(
                    call_id="c2",
                    name="write_file",
                    arguments={"path": "src/utils.py", "content": "y = 2"},
                ),
            ],
        )
        transport = MockTransport(lambda req: httpx.Response(200, json=api_response))
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert result.tool_calls[0].arguments == {
            "path": "src/main.py",
            "content": "x = 1",
        }
        assert result.tool_calls[1].arguments == {
            "path": "src/utils.py",
            "content": "y = 2",
        }

    def test_preserves_order_of_multiple_tool_calls(self):
        api_response = _make_api_response(
            content="",
            finish_reason="tool_calls",
            tool_calls=[
                _make_tool_call_dict(call_id="first", name="write_file"),
                _make_tool_call_dict(call_id="second", name="read_file"),
                _make_tool_call_dict(call_id="third", name="run_tests"),
            ],
        )
        transport = MockTransport(lambda req: httpx.Response(200, json=api_response))
        client = _make_client(transport=transport)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        ids = [tc.id for tc in result.tool_calls]
        assert ids == ["first", "second", "third"]


class TestDeepSeekClientMalformedResponses:
    def test_non_json_success_response_raises_structured_response_error(self):
        transport = MockTransport(lambda req: httpx.Response(200, content=b"not-json"))
        client = _make_client(transport=transport)

        with pytest.raises(llm_base.LLMResponseError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])

        assert exc_info.value.provider == "deepseek"
        assert exc_info.value.retryable is False
        assert "response" in exc_info.value.kind
        assert FAKE_API_KEY not in exc_info.value.safe_message

    def test_missing_choices_raises_response_error_not_key_error(self):
        transport = MockTransport(lambda req: httpx.Response(200, json={"id": "bad"}))
        client = _make_client(transport=transport)

        with pytest.raises(llm_base.LLMResponseError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])

        assert not isinstance(exc_info.value.__cause__, KeyError)
        assert exc_info.value.retryable is False

    def test_empty_choices_raises_response_error_not_index_error(self):
        transport = MockTransport(lambda req: httpx.Response(200, json={"choices": []}))
        client = _make_client(transport=transport)

        with pytest.raises(llm_base.LLMResponseError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])

        assert not isinstance(exc_info.value.__cause__, IndexError)

    def test_invalid_tool_arguments_raise_response_error_not_json_decode_error(self):
        bad_call = {
            "id": "call_bad",
            "type": "function",
            "function": {"name": "write_file", "arguments": "{not-json"},
        }
        transport = MockTransport(
            lambda req: httpx.Response(
                200,
                json=_make_api_response(
                    content=None,
                    finish_reason="tool_calls",
                    tool_calls=[bad_call],
                ),
            )
        )
        client = _make_client(transport=transport)

        with pytest.raises(llm_base.LLMResponseError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])

        assert "arguments" in exc_info.value.safe_message.lower()

    def test_content_null_is_parsed_as_empty_string_for_valid_response(self):
        transport = MockTransport(
            lambda req: httpx.Response(200, json=_make_api_response(content=None))
        )
        client = _make_client(transport=transport)

        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])

        assert result.content == ""

    def test_missing_tool_call_id_raises_response_error(self):
        bad_call = {
            "type": "function",
            "function": {"name": "write_file", "arguments": "{}"},
        }
        transport = MockTransport(
            lambda req: httpx.Response(
                200,
                json=_make_api_response(
                    content="",
                    finish_reason="tool_calls",
                    tool_calls=[bad_call],
                ),
            )
        )
        client = _make_client(transport=transport)

        with pytest.raises(llm_base.LLMResponseError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])

        assert "tool call" in exc_info.value.safe_message.lower()


class TestDeepSeekClientRetryLogic:
    def test_retries_on_connect_error_then_raises(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectError("connection failed")

        transport = MockTransport(handler)
        client = _make_client(transport=transport, retry_count=3)
        with pytest.raises(llm_base.LLMRequestError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert call_count == 4
        assert exc_info.value.retryable is True

    def test_retries_on_read_timeout_then_raises(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            raise httpx.ReadTimeout("read timed out")

        transport = MockTransport(handler)
        client = _make_client(transport=transport, retry_count=2)
        with pytest.raises(llm_base.LLMRequestError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert call_count == 3
        assert exc_info.value.retryable is True

    def test_retries_on_http_500_then_raises(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(500, json={"error": {"message": "server error"}})

        transport = MockTransport(handler)
        client = _make_client(transport=transport, retry_count=2)
        with pytest.raises(llm_base.LLMRequestError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert call_count == 3
        assert exc_info.value.status_code == 500
        assert exc_info.value.retryable is True

    def test_retries_on_http_429_then_raises(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(429, json={"error": {"message": "rate limited"}})

        transport = MockTransport(handler)
        client = _make_client(transport=transport, retry_count=3)
        with pytest.raises(llm_base.LLMRequestError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert call_count == 4
        assert exc_info.value.status_code == 429
        assert exc_info.value.retryable is True

    def test_no_retries_when_retry_count_is_zero(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectError("connection failed")

        transport = MockTransport(handler)
        client = _make_client(transport=transport, retry_count=0)
        with pytest.raises(llm_base.LLMRequestError):
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert call_count == 1

    def test_retry_count_one_means_one_retry(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectError("connection failed")

        transport = MockTransport(handler)
        client = _make_client(transport=transport, retry_count=1)
        with pytest.raises(llm_base.LLMRequestError):
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert call_count == 2

    def test_succeeds_after_retry_on_connect_error(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("connection failed")
            return httpx.Response(200, json=_make_api_response(content="success"))

        transport = MockTransport(handler)
        client = _make_client(transport=transport, retry_count=3)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert result.content == "success"
        assert call_count == 3

    def test_succeeds_after_retry_on_http_500(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return httpx.Response(500, json={"error": "server error"})
            return httpx.Response(200, json=_make_api_response(content="recovered"))

        transport = MockTransport(handler)
        client = _make_client(transport=transport, retry_count=3)
        result = client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert result.content == "recovered"
        assert call_count == 2

    def test_does_not_retry_on_success(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(200, json=_make_api_response(content="ok"))

        transport = MockTransport(handler)
        client = _make_client(transport=transport, retry_count=3)
        client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert call_count == 1


class TestDeepSeekClientTimeout:
    def test_timeout_value_passed_to_httpx_client(self, monkeypatch):
        captured: dict[str, Any] = {}
        original_init = httpx.Client.__init__

        def capturing_init(self, *args: Any, **kwargs: Any) -> None:
            captured.update(kwargs)
            original_init(self, *args, **kwargs)

        monkeypatch.setattr(httpx.Client, "__init__", capturing_init)

        DeepSeekClient(
            api_key=FAKE_API_KEY,
            model="deepseek-chat",
            temperature=0.1,
            timeout=42,
            retry_count=3,
        )
        assert captured.get("timeout") == 42

    def test_different_timeout_values_passed_to_httpx_client(self, monkeypatch):
        captured: dict[str, Any] = {}
        original_init = httpx.Client.__init__

        def capturing_init(self, *args: Any, **kwargs: Any) -> None:
            captured.update(kwargs)
            original_init(self, *args, **kwargs)

        monkeypatch.setattr(httpx.Client, "__init__", capturing_init)

        for timeout_val in (10, 30, 60, 120):
            captured.clear()
            DeepSeekClient(
                api_key=FAKE_API_KEY,
                model="deepseek-chat",
                temperature=0.1,
                timeout=timeout_val,
                retry_count=3,
            )
            assert captured.get("timeout") == timeout_val

    def test_timeout_passed_to_httpx_client_with_transport(self, monkeypatch):
        captured: dict[str, Any] = {}
        original_init = httpx.Client.__init__

        def capturing_init(self, *args: Any, **kwargs: Any) -> None:
            captured.update(kwargs)
            original_init(self, *args, **kwargs)

        monkeypatch.setattr(httpx.Client, "__init__", capturing_init)

        transport = MockTransport(
            lambda req: httpx.Response(200, json=_make_api_response())
        )
        DeepSeekClient(
            api_key=FAKE_API_KEY,
            model="deepseek-chat",
            temperature=0.1,
            timeout=99,
            retry_count=3,
            transport=transport,
        )
        assert captured.get("timeout") == 99


class TestDeepSeekClientNoHardcodedApiKey:
    def test_api_key_has_no_default_value(self):
        sig = inspect.signature(DeepSeekClient.__init__)
        api_key_param = sig.parameters.get("api_key")
        assert api_key_param is not None
        assert api_key_param.default is inspect.Parameter.empty

    def test_source_file_contains_no_hardcoded_api_key(self):
        source_path = (
            Path(__file__).resolve().parents[2]
            / "harness"
            / "llm"
            / "deepseek.py"
        )
        source = source_path.read_text()
        assert "sk-" not in source


class TestDeepSeekClientNonRetriableErrors:
    def test_http_401_raises_safe_request_error(self):
        transport = MockTransport(
            lambda req: httpx.Response(401, json={"error": {"message": "unauthorized"}})
        )
        client = _make_client(transport=transport, retry_count=3)
        with pytest.raises(llm_base.LLMRequestError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert exc_info.value.status_code == 401
        assert exc_info.value.retryable is False
        assert "credential" in exc_info.value.safe_message.lower()

    def test_http_403_raises_safe_request_error(self):
        transport = MockTransport(
            lambda req: httpx.Response(403, json={"error": {"message": "forbidden"}})
        )
        client = _make_client(transport=transport, retry_count=3)
        with pytest.raises(llm_base.LLMRequestError):
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])

    def test_http_400_raises_safe_request_error_without_retry(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(
                400,
                json={"error": {"message": "invalid tool schema"}},
            )

        transport = MockTransport(handler)
        client = _make_client(transport=transport, retry_count=3)
        with pytest.raises(llm_base.LLMRequestError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert call_count == 1
        assert exc_info.value.status_code == 400
        assert exc_info.value.retryable is False
        assert "invalid tool schema" in exc_info.value.safe_message

    def test_http_402_mentions_quota_without_retry(self):
        transport = MockTransport(
            lambda req: httpx.Response(402, json={"error": {"message": "balance low"}})
        )
        client = _make_client(transport=transport, retry_count=3)
        with pytest.raises(llm_base.LLMRequestError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert exc_info.value.status_code == 402
        assert "quota" in exc_info.value.safe_message.lower()

    def test_non_retriable_error_does_not_retry(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(401, json={"error": {"message": "unauthorized"}})

        transport = MockTransport(handler)
        client = _make_client(transport=transport, retry_count=3)
        with pytest.raises(llm_base.LLMRequestError):
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
        assert call_count == 1

    def test_timeout_retries_then_raises_request_error(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            raise httpx.ReadTimeout("read timed out")

        transport = MockTransport(handler)
        client = _make_client(transport=transport, retry_count=2)

        with pytest.raises(llm_base.LLMRequestError) as exc_info:
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])

        assert call_count == 3
        assert exc_info.value.retryable is True
        assert exc_info.value.status_code is None


class TestDeepSeekClientResourceCleanup:
    def test_close_method_exists(self):
        client = _make_client()
        assert hasattr(client, "close")
        assert callable(client.close)

    def test_close_does_not_raise(self):
        transport = MockTransport(
            lambda req: httpx.Response(200, json=_make_api_response())
        )
        client = _make_client(transport=transport)
        client.close()

    def test_context_manager_protocol(self):
        transport = MockTransport(
            lambda req: httpx.Response(200, json=_make_api_response())
        )
        with _make_client(transport=transport) as client:
            result = client.chat(
                messages=[{"role": "user", "content": "hi"}], tools=[]
            )
            assert isinstance(result, LLMResponse)

    def test_context_manager_closes_client(self):
        transport = MockTransport(
            lambda req: httpx.Response(200, json=_make_api_response())
        )
        client = _make_client(transport=transport)
        client.__enter__()
        client.__exit__(None, None, None)
        assert client._client.is_closed


class TestDeepSeekClientNegativeRetryCount:
    def test_negative_retry_count_raises_runtime_error(self):
        transport = MockTransport(
            lambda req: httpx.Response(200, json=_make_api_response())
        )
        client = _make_client(transport=transport, retry_count=-1)
        with pytest.raises(RuntimeError):
            client.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
