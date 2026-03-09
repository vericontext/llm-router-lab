"""Abstract base class for all router providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from llm_router_lab.types import LLMRequest, LLMResponse


class RouterProvider(ABC):
    """Base class that all router adapters must implement."""

    name: str

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Send a completion request and return the full response."""
        ...

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Send a streaming completion request, yielding content chunks."""
        ...

    async def close(self) -> None:
        """Clean up resources. Override if the provider holds connections."""
        pass

    def resolve_model(self, model: str) -> str:
        """Map a canonical model name to the provider-specific name.

        Override to apply provider-specific model name mappings.
        """
        return model
