from __future__ import annotations

from app.modules.conversation.schemas import (
    BookingDetails,
    CallIntent,
    CallState,
)


class ConversationStateManager:
    """In-memory store for per-call conversation state.

    Every active call_id maps to a CallState instance.
    All channels (voice, WhatsApp, outbound) share this manager
    so state logic stays in one place.
    """

    def __init__(self) -> None:
        self._states: dict[str, CallState] = {}

    # -- lifecycle -----------------------------------------------------------

    def create(self, call_id: str, language: str = "en") -> CallState:
        state = CallState(call_id=call_id, language=language)
        self._states[call_id] = state
        return state

    def get(self, call_id: str) -> CallState | None:
        return self._states.get(call_id)

    def reset(self, call_id: str) -> CallState:
        language = "en"
        existing = self._states.get(call_id)
        if existing:
            language = existing.language
        return self.create(call_id, language=language)

    def remove(self, call_id: str) -> None:
        self._states.pop(call_id, None)

    # -- intent --------------------------------------------------------------

    def set_intent(self, call_id: str, intent: CallIntent) -> CallState:
        state = self._require(call_id)
        state.intent = intent
        return state

    # -- booking fields ------------------------------------------------------

    def update_booking(self, call_id: str, **fields: str | None) -> CallState:
        state = self._require(call_id)
        current = state.booking.model_dump()
        current.update({k: v for k, v in fields.items() if k in current})
        state.booking = BookingDetails(**current)
        return state

    # -- flags ---------------------------------------------------------------

    def mark_confirmed(self, call_id: str) -> CallState:
        state = self._require(call_id)
        state.confirmed = True
        return state

    def mark_escalated(self, call_id: str) -> CallState:
        state = self._require(call_id)
        state.escalated = True
        return state

    def set_language(self, call_id: str, language: str) -> CallState:
        state = self._require(call_id)
        state.language = language
        return state

    # -- internal ------------------------------------------------------------

    def _require(self, call_id: str) -> CallState:
        state = self._states.get(call_id)
        if state is None:
            raise KeyError(f"No conversation state for call_id={call_id!r}")
        return state
