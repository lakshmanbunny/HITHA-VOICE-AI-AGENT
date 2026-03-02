from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.conversation.models import ConversationState


class ConversationRepository:
    """Pure data-access layer. No business logic lives here."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_state(
        self,
        call_id: str,
        language: str = "en",
        telephony_call_id: str | None = None,
        livekit_room_id: str | None = None,
    ) -> ConversationState:
        row = ConversationState(
            call_id=call_id,
            language=language,
            telephony_call_id=telephony_call_id,
            livekit_room_id=livekit_room_id,
            booking_data={},
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_by_call_id(self, call_id: str) -> ConversationState | None:
        stmt = select(ConversationState).where(
            ConversationState.call_id == call_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_state(
        self, call_id: str, **fields: Any
    ) -> ConversationState | None:
        invalid = [k for k in fields if k not in ConversationState.MUTABLE_FIELDS]
        if invalid:
            raise ValueError(f"Invalid fields for ConversationState: {invalid}")

        row = await self.get_by_call_id(call_id)
        if row is None:
            return None

        for key, value in fields.items():
            if value is not None:
                setattr(row, key, value)

        row.version += 1
        row.updated_at = datetime.now(timezone.utc)

        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def delete_state(self, call_id: str) -> bool:
        stmt = delete(ConversationState).where(
            ConversationState.call_id == call_id
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return (result.rowcount or 0) > 0
