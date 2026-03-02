import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.database.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ConversationState(Base):
    __tablename__ = "conversation_states"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    call_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    telephony_call_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    livekit_room_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    language: Mapped[str] = mapped_column(String(10), default="en")
    intent: Mapped[str] = mapped_column(String(50), default="UNKNOWN")
    booking_data: Mapped[dict] = mapped_column(JSON, default=dict)

    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)

    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=_utcnow
    )

    __table_args__ = (
        Index("ix_conversation_states_call_id", "call_id"),
    )

    MUTABLE_FIELDS: frozenset[str] = frozenset({
        "telephony_call_id",
        "livekit_room_id",
        "language",
        "intent",
        "booking_data",
        "confirmed",
        "escalated",
    })
