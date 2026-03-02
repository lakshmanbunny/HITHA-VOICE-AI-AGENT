from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any

TranscriptCallback = Callable[[str, bool], Coroutine[Any, Any, None]]


class BaseSTTAdapter(ABC):
    """Contract every streaming STT adapter must satisfy.

    Lifecycle:  set_transcript_callback → start → send_audio* → stop

    Implementations must NEVER call the conversation engine directly.
    The callback is the only way transcripts leave this layer.
    """

    @abstractmethod
    def set_transcript_callback(self, callback: TranscriptCallback) -> None:
        ...

    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def send_audio(self, chunk: bytes) -> None:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...
