from __future__ import annotations

import logging
from typing import Any

from app.modules.conversation.engine import ConversationEngine

logger = logging.getLogger(__name__)


class VoiceSession:
    """Per-call voice session that bridges the transport layer to the engine.

    Holds the call_id and room_id for the duration of a LiveKit session.
    All transcript events flow through here into the ConversationEngine.

    Only FINAL STT segments are forwarded to the engine.  Interim
    (partial) results are logged but never trigger extraction — sending
    half-formed text to the LLM would waste tokens and produce
    unreliable output.
    """

    def __init__(
        self,
        call_id: str,
        room_id: str,
        engine: ConversationEngine,
    ) -> None:
        self.call_id = call_id
        self.room_id = room_id
        self._engine = engine

    async def handle_transcript(
        self,
        text: str,
        *,
        is_final: bool = True,
    ) -> dict[str, Any] | None:
        """Process a transcript segment.

        Args:
            text: The transcribed text.
            is_final: Whether the STT segment is final.  Interim
                      (partial) results are logged and skipped.

        Returns:
            The engine action dict for final segments, or None for
            interim segments.
        """
        if not is_final:
            logger.debug("[%s] interim transcript (ignored): %s", self.call_id, text[:80])
            return None

        text = text.strip()
        if not text:
            return None

        logger.info("[%s] final transcript: %s", self.call_id, text[:120])

        action = await self._engine.process_transcript(self.call_id, text)

        logger.info("[%s] engine action: %s", self.call_id, action)
        return action
