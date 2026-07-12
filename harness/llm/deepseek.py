from __future__ import annotations

import json
from typing import Any

import httpx

from harness.llm.base import LLMClient, LLMResponse, ToolCall


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
            httpx.HTTPStatusError: If the API returns 500/429 after all retries.
        """
        url = "https://api.deepseek.com/chat/completions"
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
        last_exception: Exception | None = None
        for _ in range(self._retry_count + 1):
            try:
                response = self._client.post(url, headers=headers, json=body)
            except (httpx.ConnectError, httpx.ReadTimeout) as exc:
                last_exception = exc
                continue
            if response.status_code in (500, 429):
                last_exception = httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response,
                )
                continue
            return self._parse_response(response)
        assert last_exception is not None
        raise last_exception

    @staticmethod
    def _parse_response(response: httpx.Response) -> LLMResponse:
        """Parse a successful DeepSeek API response into an LLMResponse.

        Args:
            response: The httpx response from the DeepSeek API.

        Returns:
            An :class:`LLMResponse` with content, finish reason, and tool calls.
        """
        data = response.json()
        choice = data["choices"][0]
        message = choice["message"]
        content = message.get("content", "")
        finish_reason = choice["finish_reason"]
        tool_calls: list[ToolCall] = []
        for tc in message.get("tool_calls", []):
            tool_calls.append(
                ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=json.loads(tc["function"]["arguments"]),
                )
            )
        return LLMResponse(
            content=content,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
        )
