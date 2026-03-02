from __future__ import annotations

import logging
from typing import Any

from app.modules.conversation.schemas import (
    CallIntent,
    ConversationStateSchema,
)
from app.modules.llm.base import BaseLLMAdapter
from app.modules.llm.prompts import VALID_BOOKING_KEYS

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when post-validation of LLM extraction fails."""


async def run_extraction(
    adapter: BaseLLMAdapter,
    transcript: str,
    state: ConversationStateSchema,
) -> dict[str, Any]:
    """Firewall between LLM output and the rest of the system.

    Calls the adapter, then applies a second round of defensive
    validation/normalisation before anything touches state or DB.

    Returns a clean dict safe for ConversationManager.apply_extraction().
    """
    current_state = {
        "intent": state.intent.value,
        "language": state.language,
        "booking": state.booking.model_dump(),
        "confirmed": state.confirmed,
        "escalated": state.escalated,
    }

    raw = await adapter.extract_structured(
        transcript=transcript,
        current_state=current_state,
        language=state.language,
    )

    return _sanitise(raw)


def _sanitise(raw: dict) -> dict[str, Any]:
    """Normalise and re-validate the adapter output.

    No auto-filling. No guessing. Only cleaning.
    """
    intent_str = raw.get("intent", "UNKNOWN")
    try:
        intent = CallIntent(intent_str)
    except ValueError:
        logger.warning("LLM returned unmapped intent %r, forcing UNKNOWN", intent_str)
        intent = CallIntent.UNKNOWN

    language = raw.get("language")
    if not isinstance(language, str) or not language.strip():
        raise ExtractionError(f"Invalid language value from LLM: {language!r}")
    language = language.strip().lower()

    raw_booking = raw.get("booking", {})
    if not isinstance(raw_booking, dict):
        raise ExtractionError(f"'booking' is not a dict: {type(raw_booking).__name__}")

    booking: dict[str, str | None] = {}
    for key in VALID_BOOKING_KEYS:
        value = raw_booking.get(key)
        if value is None or value == "":
            booking[key] = None
        elif isinstance(value, str):
            booking[key] = value.strip()
        else:
            raise ExtractionError(
                f"Booking field {key!r} must be string or null, got {type(value).__name__}"
            )

    confirmed = raw.get("confirmed")
    if not isinstance(confirmed, bool):
        raise ExtractionError(f"'confirmed' must be bool, got {type(confirmed).__name__}")

    escalate = raw.get("escalate")
    if not isinstance(escalate, bool):
        raise ExtractionError(f"'escalate' must be bool, got {type(escalate).__name__}")

    return {
        "intent": intent.value,
        "language": language,
        "booking": booking,
        "confirmed": confirmed,
        "escalate": escalate,
    }
