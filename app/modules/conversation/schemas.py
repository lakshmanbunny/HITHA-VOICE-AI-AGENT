from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CallIntent(str, Enum):
    BOOK = "BOOK"
    RESCHEDULE = "RESCHEDULE"
    CANCEL = "CANCEL"
    REMINDER_CONFIRM = "REMINDER_CONFIRM"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

class BookingDetails(BaseModel):
    department: Optional[str] = None
    doctor: Optional[str] = None
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    patient_name: Optional[str] = None


REQUIRED_SLOTS: dict[CallIntent, list[str]] = {
    CallIntent.BOOK: [
        "department",
        "doctor",
        "preferred_date",
        "preferred_time",
        "patient_name",
    ],
    CallIntent.RESCHEDULE: [
        "patient_name",
        "preferred_date",
        "preferred_time",
    ],
    CallIntent.CANCEL: [
        "patient_name",
    ],
    CallIntent.REMINDER_CONFIRM: [],
    CallIntent.UNKNOWN: [],
}


# ---------------------------------------------------------------------------
# In-memory state (used by real-time voice pipeline)
# ---------------------------------------------------------------------------

class CallState(BaseModel):
    call_id: str
    language: str = Field(default="en")
    intent: CallIntent = Field(default=CallIntent.UNKNOWN)
    booking: BookingDetails = Field(default_factory=BookingDetails)
    confirmed: bool = False
    escalated: bool = False


# ---------------------------------------------------------------------------
# Persistent state schema (mirrors the DB model for API / service use)
# ---------------------------------------------------------------------------

class ConversationStateCreate(BaseModel):
    call_id: str
    telephony_call_id: Optional[str] = None
    livekit_room_id: Optional[str] = None
    language: str = "en"


class ConversationStateUpdate(BaseModel):
    telephony_call_id: Optional[str] = None
    livekit_room_id: Optional[str] = None
    language: Optional[str] = None
    intent: Optional[CallIntent] = None
    booking_data: Optional[dict] = None
    confirmed: Optional[bool] = None
    escalated: Optional[bool] = None


class ConversationStateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    call_id: str
    telephony_call_id: Optional[str] = None
    livekit_room_id: Optional[str] = None
    language: str
    intent: CallIntent
    booking: BookingDetails = Field(default_factory=BookingDetails)
    confirmed: bool
    escalated: bool
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_model(cls, obj: object) -> ConversationStateSchema:
        """Build schema from the SQLAlchemy model, unpacking booking_data JSON."""
        raw = {
            "id": obj.id,  # type: ignore[attr-defined]
            "call_id": obj.call_id,  # type: ignore[attr-defined]
            "telephony_call_id": obj.telephony_call_id,  # type: ignore[attr-defined]
            "livekit_room_id": obj.livekit_room_id,  # type: ignore[attr-defined]
            "language": obj.language,  # type: ignore[attr-defined]
            "intent": obj.intent,  # type: ignore[attr-defined]
            "booking": BookingDetails(**(obj.booking_data or {})),  # type: ignore[attr-defined]
            "confirmed": obj.confirmed,  # type: ignore[attr-defined]
            "escalated": obj.escalated,  # type: ignore[attr-defined]
            "version": obj.version,  # type: ignore[attr-defined]
            "created_at": obj.created_at,  # type: ignore[attr-defined]
            "updated_at": obj.updated_at,  # type: ignore[attr-defined]
        }
        return cls(**raw)
