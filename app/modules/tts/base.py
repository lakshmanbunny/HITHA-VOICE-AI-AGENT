from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any

AudioCallback = Callable[[bytes], Coroutine[Any, Any, None]]


class BaseTTSAdapter(ABC):
    """Contract every streaming TTS adapter must satisfy.

    Lifecycle:  set_audio_callback → start → speak* → stop

    Implementations must NEVER call the conversation engine directly.
    Audio leaves this layer only via the registered callback.
    """

    @abstractmethod
    def set_audio_callback(self, callback: AudioCallback) -> None:
        ...

    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def speak(self, text: str, language: str) -> None:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...
