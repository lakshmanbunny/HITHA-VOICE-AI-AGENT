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

    Accumulates a full transcript (patient + assistant turns) that can
    be persisted to the call log when the session ends.
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
        self._transcript: list[dict[str, str]] = []

    def add_assistant_turn(self, text: str) -> None:
        """Record an assistant response in the transcript."""
        self._transcript.append({"speaker": "Assistant", "text": text})

    def get_transcript(self) -> list[dict[str, str]]:
        """Return a copy of the accumulated transcript."""
        return list(self._transcript)

    async def handle_transcript(
        self,
        text: str,
        *,
        is_final: bool = True,
    ) -> dict[str, Any] | None:
        if not is_final:
            logger.debug("[%s] interim transcript (ignored): %s", self.call_id, text[:80])
            return None

        text = text.strip()
        if not text:
            return None

        logger.info("[%s] final transcript: %s", self.call_id, text[:120])

        self._transcript.append({"speaker": "Patient", "text": text})

        action = await self._engine.process_transcript(self.call_id, text)

        logger.info("[%s] engine action: %s", self.call_id, action)
        return action
