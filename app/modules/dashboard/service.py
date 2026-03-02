from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.models import Appointment, CallLog
from app.modules.dashboard.repository import AppointmentRepository, CallLogRepository

logger = logging.getLogger(__name__)

_LANG_DISPLAY = {"en": "English", "te": "Telugu", "hi": "Hindi"}


class DashboardService:
    """Business-logic layer for call logs, appointments, and stats."""

    def __init__(self, session: AsyncSession) -> None:
        self._calls = CallLogRepository(session)
        self._apts = AppointmentRepository(session)
        self._session = session

    # ── Call Logs ──────────────────────────────────────────────────

    async def create_call_log(
        self,
        call_id: str,
        caller_name: str = "Unknown",
        phone_number: str = "",
        direction: str = "inbound",
        languages: list[str] | None = None,
    ) -> CallLog:
        row = await self._calls.create(
            call_id=call_id,
            caller_name=caller_name,
            phone_number=phone_number,
            direction=direction,
            languages=languages or ["English"],
        )
        await self._session.commit()
        return row

    async def finalize_call_log(
        self,
        call_id: str,
        transcript: list[dict[str, str]],
        status: str,
        caller_name: str | None = None,
        languages: list[str] | None = None,
        appointment_id: str | None = None,
    ) -> CallLog | None:
        ended_at = datetime.now(timezone.utc)
        row = await self._calls.get_by_call_id(call_id)
        if row is None:
            return None

        duration = 0
        if row.started_at:
            started = row.started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            duration = int((ended_at - started).total_seconds())

        updates: dict[str, Any] = {
            "ended_at": ended_at,
            "duration_seconds": duration,
            "status": status,
            "transcript": transcript,
        }
        if caller_name:
            updates["caller_name"] = caller_name
        if languages:
            updates["languages"] = languages
        if appointment_id:
            updates["appointment_id"] = appointment_id

        row = await self._calls.update(call_id, **updates)
        await self._session.commit()
        return row

    async def get_all_call_logs(self) -> list[CallLog]:
        return await self._calls.get_all()

    async def get_call_log(self, call_id: str) -> CallLog | None:
        return await self._calls.get_by_call_id(call_id)

    # ── Appointments ──────────────────────────────────────────────

    async def create_appointment(self, **fields: Any) -> Appointment:
        row = await self._apts.create(**fields)
        await self._session.commit()
        return row

    async def create_appointment_from_booking(
        self,
        call_id: str,
        booking_data: dict,
    ) -> Appointment:
        """Convert the engine's booking_data into an Appointment record."""
        from dateutil import parser as dtparser

        raw_date = booking_data.get("preferred_date", "")
        raw_time = booking_data.get("preferred_time", "")
        try:
            dt = dtparser.parse(f"{raw_date} {raw_time}".strip())
        except Exception:
            dt = datetime.now(timezone.utc)

        row = await self._apts.create(
            call_id=call_id,
            patient_name=booking_data.get("patient_name", "Unknown"),
            phone_number=booking_data.get("phone_number", ""),
            doctor_name=booking_data.get("doctor", ""),
            department=booking_data.get("department", ""),
            date_time=dt,
            status="confirmed",
            symptoms=[],
        )
        await self._session.commit()
        logger.info("Appointment created for call_id=%s: %s", call_id, row.id)
        return row

    async def get_all_appointments(self) -> list[Appointment]:
        return await self._apts.get_all()

    async def get_appointment(self, apt_id: str) -> Appointment | None:
        return await self._apts.get_by_id(apt_id)

    async def update_appointment(
        self, apt_id: str, **fields: Any
    ) -> Appointment | None:
        row = await self._apts.update(apt_id, **fields)
        if row:
            await self._session.commit()
        return row

    async def cancel_appointment(self, apt_id: str) -> Appointment | None:
        row = await self._apts.update(apt_id, status="cancelled")
        if row:
            await self._session.commit()
        return row

    # ── Stats ─────────────────────────────────────────────────────

    async def compute_stats(self) -> dict[str, int]:
        total_calls = await self._calls.count()
        total_appointments = await self._apts.count()
        completed_calls = await self._calls.count_by_status("completed")
        missed_calls = await self._calls.count_by_status("no-answer")
        transferred_calls = await self._calls.count_by_status("transferred")
        cancelled_appointments = await self._apts.count_by_status("cancelled")
        calls_today = await self._calls.count_today()
        appointments_today = await self._apts.count_today()

        return {
            "totalCalls": total_calls,
            "totalAppointments": total_appointments,
            "completedCalls": completed_calls,
            "missedCalls": missed_calls,
            "transferredCalls": transferred_calls,
            "cancelledAppointments": cancelled_appointments,
            "callsToday": calls_today,
            "appointmentsToday": appointments_today,
        }

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def language_display(code: str) -> str:
        return _LANG_DISPLAY.get(code, code.capitalize())

    @staticmethod
    def format_duration(seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs:02d}s"
