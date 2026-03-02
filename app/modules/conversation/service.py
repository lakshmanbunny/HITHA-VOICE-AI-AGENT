from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.conversation.repository import ConversationRepository
from app.modules.conversation.schemas import (
    BookingDetails,
    CallIntent,
    ConversationStateSchema,
)


class ConversationService:
    """Business-logic layer for persistent conversation state.

    Calls ConversationRepository only — no direct DB access, no LLM,
    no STT, no route logic.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = ConversationRepository(session)
        self._session = session

    # -- lifecycle -----------------------------------------------------------

    async def create_new_call(
        self,
        call_id: str,
        language: str = "en",
        telephony_call_id: str | None = None,
        livekit_room_id: str | None = None,
    ) -> ConversationStateSchema:
        row = await self._repo.create_state(
            call_id=call_id,
            language=language,
            telephony_call_id=telephony_call_id,
            livekit_room_id=livekit_room_id,
        )
        await self._session.commit()
        return ConversationStateSchema.from_orm_model(row)

    async def load_state(self, call_id: str) -> ConversationStateSchema | None:
        row = await self._repo.get_by_call_id(call_id)
        if row is None:
            return None
        return ConversationStateSchema.from_orm_model(row)

    async def delete_call(self, call_id: str) -> bool:
        deleted = await self._repo.delete_state(call_id)
        await self._session.commit()
        return deleted

    # -- intent --------------------------------------------------------------

    async def update_intent(
        self, call_id: str, intent: CallIntent
    ) -> ConversationStateSchema | None:
        row = await self._repo.update_state(call_id, intent=intent.value)
        if row is None:
            return None
        await self._session.commit()
        return ConversationStateSchema.from_orm_model(row)

    # -- booking fields ------------------------------------------------------

    async def update_booking_field(
        self, call_id: str, **fields: str | None
    ) -> ConversationStateSchema | None:
        row = await self._repo.get_by_call_id(call_id)
        if row is None:
            return None

        current_booking = dict(row.booking_data or {})
        valid_keys = set(BookingDetails.model_fields.keys())
        current_booking.update(
            {k: v for k, v in fields.items() if k in valid_keys}
        )
        updated = await self._repo.update_state(
            call_id, booking_data=current_booking
        )
        if updated is None:
            return None
        await self._session.commit()
        return ConversationStateSchema.from_orm_model(updated)

    # -- flags ---------------------------------------------------------------

    async def mark_confirmed(
        self, call_id: str
    ) -> ConversationStateSchema | None:
        row = await self._repo.update_state(call_id, confirmed=True)
        if row is None:
            return None
        await self._session.commit()
        return ConversationStateSchema.from_orm_model(row)

    async def mark_escalated(
        self, call_id: str
    ) -> ConversationStateSchema | None:
        row = await self._repo.update_state(call_id, escalated=True)
        if row is None:
            return None
        await self._session.commit()
        return ConversationStateSchema.from_orm_model(row)

    # -- language ------------------------------------------------------------

    async def update_language(
        self, call_id: str, language: str
    ) -> ConversationStateSchema | None:
        row = await self._repo.update_state(call_id, language=language)
        if row is None:
            return None
        await self._session.commit()
        return ConversationStateSchema.from_orm_model(row)

    # -- flow reset ----------------------------------------------------------

    async def reset_flow(
        self, call_id: str
    ) -> ConversationStateSchema | None:
        """Clear booking data, confirmed, and escalated flags.

        Called when intent changes — stale slots from a previous
        flow must not leak into the new one.
        """
        row = await self._repo.update_state(
            call_id,
            booking_data={},
            confirmed=False,
            escalated=False,
        )
        if row is None:
            return None
        await self._session.commit()
        return ConversationStateSchema.from_orm_model(row)
