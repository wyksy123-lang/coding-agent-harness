from __future__ import annotations

import json
from typing import Any

import httpx

from harness.llm.base import (
    LLMClient,
    LLMRequestError,
    LLMResponse,
    LLMResponseError,
    ToolCall,
)

_API_URL = "https://api.deepseek.com/chat/completions"
_PROVIDER = "deepseek"
_RETRY_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})
_NON_RETRY_STATUS_CODES = frozenset({400, 401, 402, 403, 404, 422})


class DeepSeekClient(LLMClient):
    """LLM client that communicates with the DeepSeek chat completions API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float,
        timeout: int,
        retry_count: int,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Initialize the DeepSeek client.

        Args:
            api_key: The DeepSeek API key (required, no default).
            model: The model identifier to use for completions.
            temperature: The sampling temperature.
            timeout: The request timeout in seconds, passed to httpx.Client.
            retry_count: Number of retries after the initial attempt.
            transport: Optional httpx transport for testing; when None a
                real httpx.Client is created.
        """
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._retry_count = retry_count
        if transport is None:
            self._client = httpx.Client(timeout=timeout)
        else:
            self._client = httpx.Client(transport=transport, timeout=timeout)

    def close(self) -> None:
        """Close the underlying httpx client and release connections."""
        self._client.close()

    def __enter__(self) -> DeepSeekClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self._client.close()

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> LLMResponse:
        """Send a chat completion request to the DeepSeek API.

        Args:
            messages: Chat messages in OpenAI format.
            tools: Tool definitions in OpenAI format.

        Returns:
            An :class:`LLMResponse` with the parsed reply.

        Raises:
            httpx.ConnectError: If the connection fails after all retries.
            httpx.ReadTimeout: If the read times out after all retries.
            httpx.HTTPStatusError: If the API returns a retriable status
                (500/429) after all retries, or any non-200 status that is
                not retried (e.g. 401, 403, 400).
        """
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "messages": messages,
            "tools": tools,
            "temperature": self._temperature,
        }
        if self._retry_count < 0:
            raise RuntimeError("retry_count must be non-negative")
        last_exception: LLMRequestError | None = None
        for _ in range(self._retry_count + 1):
            try:
                response = self._client.post(_API_URL, headers=headers, json=body)
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
                last_exception = _request_error(
                    kind="network_error",
                    safe_message=f"DeepSeek request failed: {exc.__class__.__name__}",
                    status_code=None,
                    retryable=True,
                )
                continue
            if response.status_code in _RETRY_STATUS_CODES:
                last_exception = _request_error_for_response(response, retryable=True)
                continue
            if response.status_code in _NON_RETRY_STATUS_CODES:
                raise _request_error_for_response(response, retryable=False)
            if response.status_code != 200:
                raise _request_error_for_response(response, retryable=False)
            return self._parse_response(response)
        if last_exception is None:
            raise RuntimeError(
                "retry loop exited without an exception; "
                "check that retry_count is non-negative"
            )
        raise last_exception

    @staticmethod
    def _parse_response(response: httpx.Response) -> LLMResponse:
        """Parse a successful DeepSeek API response into an LLMResponse.

        Args:
            response: The httpx response from the DeepSeek API (status 200).

        Returns:
            An :class:`LLMResponse` with content, finish reason, and tool calls.
        """
        try:
            data = response.json()
        except ValueError as exc:
            raise _response_error("response_json", "DeepSeek returned non-JSON response") from exc
        if not isinstance(data, dict):
            raise _response_error("response_shape", "DeepSeek response was not an object")
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise _response_error("response_choices", "DeepSeek response missing choices")
        choice = choices[0]
        if not isinstance(choice, dict):
            raise _response_error("response_choice", "DeepSeek response choice was invalid")
        message = choice.get("message")
        if not isinstance(message, dict):
            raise _response_error("response_message", "DeepSeek response missing message")
        content_value = message.get("content", "")
        content = "" if content_value is None else str(content_value)
        finish_reason_value = choice.get("finish_reason", "unknown")
        finish_reason = (
            finish_reason_value if isinstance(finish_reason_value, str) else "unknown"
        )
        tool_calls: list[ToolCall] = []
        raw_tool_calls = message.get("tool_calls", [])
        if raw_tool_calls is None:
            raw_tool_calls = []
        if not isinstance(raw_tool_calls, list):
            raise _response_error("tool_calls", "DeepSeek tool_calls was invalid")
        for tc in raw_tool_calls:
            if not isinstance(tc, dict):
                raise _response_error("tool_call", "DeepSeek tool call was invalid")
            call_id = tc.get("id")
            function = tc.get("function")
            if not isinstance(call_id, str) or not call_id:
                raise _response_error("tool_call_id", "DeepSeek tool call missing id")
            if not isinstance(function, dict):
                raise _response_error(
                    "tool_call_function",
                    "DeepSeek tool call missing function",
                )
            name = function.get("name")
            arguments_json = function.get("arguments")
            if not isinstance(name, str) or not name:
                raise _response_error(
                    "tool_call_name",
                    "DeepSeek tool call missing function.name",
                )
            if not isinstance(arguments_json, str):
                raise _response_error(
                    "tool_call_arguments",
                    "DeepSeek tool call missing function.arguments",
                )
            try:
                arguments = json.loads(arguments_json)
            except json.JSONDecodeError as exc:
                raise _response_error(
                    "tool_call_arguments_json",
                    "DeepSeek tool call arguments were invalid JSON",
                ) from exc
            if not isinstance(arguments, dict):
                raise _response_error(
                    "tool_call_arguments_object",
                    "DeepSeek tool call arguments were not an object",
                )
            tool_calls.append(
                ToolCall(
                    id=call_id,
                    name=name,
                    arguments=arguments,
                    raw_tool_call=tc,
                )
            )
        return LLMResponse(
            content=content,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
        )


def _request_error_for_response(
    response: httpx.Response,
    *,
    retryable: bool,
) -> LLMRequestError:
    message = _extract_error_message(response)
    status_code = response.status_code
    if status_code == 401:
        safe = "DeepSeek API credential rejected"
    elif status_code == 402:
        safe = "DeepSeek request failed: insufficient balance or quota"
    elif status_code == 429:
        safe = f"DeepSeek rate limit after retries: {message}"
    else:
        safe = f"DeepSeek rejected the request with HTTP {status_code}: {message}"
    return _request_error(
        kind=f"http_{status_code}",
        safe_message=_sanitize_message(safe),
        status_code=status_code,
        retryable=retryable,
    )


def _extract_error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.reason_phrase or "request failed"
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message:
                return _sanitize_message(message)
        if isinstance(error, str) and error:
            return _sanitize_message(error)
        message = data.get("message")
        if isinstance(message, str) and message:
            return _sanitize_message(message)
    return response.reason_phrase or "request failed"


def _request_error(
    *,
    kind: str,
    safe_message: str,
    status_code: int | None,
    retryable: bool,
) -> LLMRequestError:
    return LLMRequestError(
        kind=kind,
        safe_message=_sanitize_message(safe_message),
        status_code=status_code,
        retryable=retryable,
        provider=_PROVIDER,
    )


def _response_error(kind: str, safe_message: str) -> LLMResponseError:
    return LLMResponseError(
        kind=kind,
        safe_message=_sanitize_message(safe_message),
        status_code=None,
        retryable=False,
        provider=_PROVIDER,
    )


def _sanitize_message(message: str) -> str:
    redacted = message.replace("\r", " ").replace("\n", " ")
    if "Authorization" in redacted:
        redacted = redacted.replace("Authorization", "[redacted]")
    return redacted[:300]
