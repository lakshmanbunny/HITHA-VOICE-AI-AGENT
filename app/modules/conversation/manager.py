from __future__ import annotations

from typing import Any

from app.modules.conversation.schemas import (
    CallIntent,
    CallState,
    REQUIRED_SLOTS,
)
from app.modules.conversation.state import ConversationStateManager


class ConversationManager:
    """High-level orchestrator that sits between channel I/O and state.

    Responsibilities:
      1. Accept structured extraction output (dict from LLM post-processing).
      2. Map it to atomic state updates.
      3. Determine the next missing slot so the voice/chat layer knows
         what question to ask next.

    This class contains ZERO LLM / STT / DB logic.
    """

    def __init__(self, state_mgr: ConversationStateManager | None = None) -> None:
        self.state = state_mgr or ConversationStateManager()

    # -- public API ----------------------------------------------------------

    def start_call(self, call_id: str, language: str = "en") -> CallState:
        return self.state.create(call_id, language=language)

    def end_call(self, call_id: str) -> None:
        self.state.remove(call_id)

    def apply_extraction(self, call_id: str, data: dict[str, Any]) -> CallState:
        """Apply a structured extraction payload to the call state.

        Expected keys (all optional):
            intent:   str matching a CallIntent value
            language: str like "en" or "te"
            booking:  dict of slot key/value pairs
        """
        if "intent" in data:
            try:
                intent = CallIntent(data["intent"])
            except ValueError:
                intent = CallIntent.UNKNOWN
            self.state.set_intent(call_id, intent)

        if "language" in data:
            self.state.set_language(call_id, data["language"])

        if "booking" in data and isinstance(data["booking"], dict):
            self.state.update_booking(call_id, **data["booking"])

        return self.state.get(call_id)  # type: ignore[return-value]

    def confirm(self, call_id: str) -> CallState:
        return self.state.mark_confirmed(call_id)

    def escalate(self, call_id: str) -> CallState:
        return self.state.mark_escalated(call_id)

    # -- slot resolution -----------------------------------------------------

    def next_missing_slot(self, call_id: str) -> str | None:
        """Return the name of the first unfilled required slot, or None."""
        state = self.state.get(call_id)
        if state is None:
            return None

        required = REQUIRED_SLOTS.get(state.intent, [])
        booking_data = state.booking.model_dump()

        for slot in required:
            if not booking_data.get(slot):
                return slot
        return None

    def all_slots_filled(self, call_id: str) -> bool:
        return self.next_missing_slot(call_id) is None

    def pending_slots(self, call_id: str) -> list[str]:
        """Return all unfilled required slots for the current intent."""
        state = self.state.get(call_id)
        if state is None:
            return []

        required = REQUIRED_SLOTS.get(state.intent, [])
        booking_data = state.booking.model_dump()
        return [s for s in required if not booking_data.get(s)]
