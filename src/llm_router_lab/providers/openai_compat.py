"""Generic OpenAI-compatible API adapter.

Any router that exposes an OpenAI-compatible /chat/completions endpoint
can be used via YAML config alone, without writing a custom adapter.
"""

from __future__ import annotations

from typing import AsyncIterator

from openai import AsyncOpenAI

from llm_router_lab.config import RouterConfig
from llm_router_lab.providers.base import RouterProvider
from llm_router_lab.types import (
    LLMRequest,
    LLMResponse,
    TokenUsage,
)


class OpenAICompatProvider(RouterProvider):
    """Adapter for any OpenAI API-compatible endpoint."""

    def __init__(self, config: RouterConfig) -> None:
        self.config = config
        self.name = config.name
        self._client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key or "dummy",
        )

    def resolve_model(self, model: str) -> str:
        return self.config.model_map.get(model, model)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        resolved_model = self.resolve_model(request.model)
        messages = [m.model_dump(exclude_none=True) for m in request.messages]

        kwargs: dict = {
            "model": resolved_model,
            "messages": messages,
            "temperature": request.temperature,
            **self.config.default_params,
        }
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        if request.tools:
            kwargs["tools"] = [t.model_dump() for t in request.tools]

        try:
            response = await self._client.chat.completions.create(**kwargs)
            choice = response.choices[0]

            tool_calls = None
            if choice.message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ]

            usage = TokenUsage()
            if response.usage:
                usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )

            return LLMResponse(
                content=choice.message.content,
                tool_calls=tool_calls,
                usage=usage,
                model=response.model,
                raw=response.model_dump(),
            )
        except Exception as e:
            return LLMResponse(error=str(e))

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        resolved_model = self.resolve_model(request.model)
        messages = [m.model_dump(exclude_none=True) for m in request.messages]

        kwargs: dict = {
            "model": resolved_model,
            "messages": messages,
            "temperature": request.temperature,
            "stream": True,
            **self.config.default_params,
        }
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens

        response = await self._client.chat.completions.create(**kwargs)
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def close(self) -> None:
        await self._client.close()
