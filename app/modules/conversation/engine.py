from __future__ import annotations

import logging
from typing import Any

from app.modules.conversation.schemas import (
    CallIntent,
    ConversationStateSchema,
    REQUIRED_SLOTS,
)
from app.modules.conversation.service import ConversationService
from app.modules.dashboard.doctors_data import get_available_slots
from app.modules.llm.base import BaseLLMAdapter
from app.modules.llm.extractor import run_extraction

logger = logging.getLogger(__name__)

_MAX_RETRIES = 1


class ConversationEngine:
    """Universal orchestrator for all conversation channels.

    Receives a transcript, runs LLM extraction, applies state
    updates via the service layer, and returns the next action
    for the channel to execute.

    No DB session management, no FastAPI, no telephony logic.
    """

    def __init__(
        self,
        service: ConversationService,
        adapter: BaseLLMAdapter,
    ) -> None:
        self._service = service
        self._adapter = adapter

    async def process_transcript(
        self,
        call_id: str,
        transcript: str,
    ) -> dict[str, Any]:
        state = await self._service.load_state(call_id)
        if state is None:
            raise ValueError(f"No conversation state found for call_id={call_id!r}")

        extraction = await self._extract_with_retry(call_id, transcript, state)
        if extraction is None:
            return {"action": "ESCALATE"}

        await self._apply_updates(call_id, state, extraction)

        state = await self._service.load_state(call_id)
        return self._determine_action(state)

    # -- extraction with retry -----------------------------------------------

    async def _extract_with_retry(
        self,
        call_id: str,
        transcript: str,
        state: ConversationStateSchema,
    ) -> dict | None:
        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                return await run_extraction(self._adapter, transcript, state)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Extraction attempt %d failed for %s: %s",
                    attempt + 1, call_id, exc,
                )

        logger.error(
            "All extraction attempts failed for %s, escalating: %s",
            call_id, last_error,
        )
        await self._service.mark_escalated(call_id)
        return None

    # -- state updates -------------------------------------------------------

    async def _apply_updates(
        self,
        call_id: str,
        old_state: ConversationStateSchema,
        extraction: dict,
    ) -> None:
        new_intent = CallIntent(extraction["intent"])
        intent_changed = (
            new_intent != old_state.intent
            and new_intent != CallIntent.UNKNOWN
        )

        if intent_changed:
            logger.info(
                "%s: intent changed %s -> %s, resetting flow",
                call_id, old_state.intent.value, new_intent.value,
            )
            await self._service.reset_flow(call_id)
            await self._service.update_intent(call_id, new_intent)

        if extraction["language"] != old_state.language:
            await self._service.update_language(call_id, extraction["language"])

        booking_updates = {
            k: v for k, v in extraction["booking"].items()
            if v is not None
        }
        if booking_updates:
            await self._service.update_booking_field(call_id, **booking_updates)

        if extraction["escalate"] and not old_state.escalated:
            await self._service.mark_escalated(call_id)

        if extraction["confirmed"] and not old_state.confirmed:
            await self._guard_confirmation(call_id, new_intent)

    async def _guard_confirmation(
        self, call_id: str, intent: CallIntent
    ) -> None:
        """Only mark confirmed if intent is actionable and all slots are filled."""
        if intent == CallIntent.UNKNOWN:
            logger.warning(
                "%s: ignoring confirmation — intent is UNKNOWN", call_id,
            )
            return

        state = await self._service.load_state(call_id)
        if state is None:
            return

        missing = _first_missing_slot(state)
        if missing is not None:
            logger.warning(
                "%s: ignoring confirmation — slot %r still missing",
                call_id, missing,
            )
            return

        await self._service.mark_confirmed(call_id)

    # -- action resolution ---------------------------------------------------

    @staticmethod
    def _determine_action(state: ConversationStateSchema) -> dict[str, Any]:
        if state.escalated:
            return {"action": "ESCALATE"}

        missing = _first_missing_slot(state)

        if state.confirmed and missing is None:
            return {"action": "FINALIZE_BOOKING"}

        if missing is not None:
            action: dict[str, Any] = {"action": "ASK_SLOT", "slot": missing}
            if missing == "preferred_time":
                doctor_name = state.booking.doctor
                action["available_slots"] = get_available_slots(doctor_name)
            return action

        if state.intent != CallIntent.UNKNOWN:
            booking = state.booking.model_dump()
            return {
                "action": "CONFIRM",
                "booking": {k: v for k, v in booking.items() if v},
            }

        return {"action": "CONTINUE"}


def _first_missing_slot(state: ConversationStateSchema) -> str | None:
    required = REQUIRED_SLOTS.get(state.intent, [])
    booking_data = state.booking.model_dump()
    for slot in required:
        if not booking_data.get(slot):
            return slot
    return None
