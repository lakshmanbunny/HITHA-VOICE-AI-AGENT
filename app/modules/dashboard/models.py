from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.database.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CallLog(Base):
    __tablename__ = "call_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    call_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    caller_name: Mapped[str] = mapped_column(String(255), default="Unknown")
    phone_number: Mapped[str] = mapped_column(String(50), default="")
    direction: Mapped[str] = mapped_column(String(20), default="inbound")
    languages: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="in-progress")
    transcript: Mapped[list] = mapped_column(JSON, default=list)
    appointment_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    __table_args__ = (
        Index("ix_call_logs_call_id", "call_id"),
        Index("ix_call_logs_started_at", "started_at"),
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    call_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    patient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), default="")
    doctor_name: Mapped[str] = mapped_column(String(255), default="")
    department: Mapped[str] = mapped_column(String(255), default="")
    date_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="confirmed")
    symptoms: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=_utcnow
    )

    __table_args__ = (
        Index("ix_appointments_call_id", "call_id"),
        Index("ix_appointments_date_time", "date_time"),
    )
