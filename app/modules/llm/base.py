from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLMAdapter(ABC):
    """Contract every LLM adapter must satisfy.

    Implementations must return a raw dict whose shape matches
    the extraction JSON schema defined in prompts.py.
    No business logic belongs here.
    """

    @abstractmethod
    async def extract_structured(
        self,
        transcript: str,
        current_state: dict,
        language: str,
    ) -> dict:
        ...
