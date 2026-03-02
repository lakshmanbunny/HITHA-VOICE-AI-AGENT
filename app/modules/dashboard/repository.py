from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.models import Appointment, CallLog


class CallLogRepository:
    """Pure data-access layer for call logs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **fields: Any) -> CallLog:
        row = CallLog(**fields)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_all(self) -> list[CallLog]:
        stmt = select(CallLog).order_by(CallLog.started_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_call_id(self, call_id: str) -> CallLog | None:
        stmt = select(CallLog).where(CallLog.call_id == call_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, log_id: str) -> CallLog | None:
        stmt = select(CallLog).where(CallLog.id == log_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, call_id: str, **fields: Any) -> CallLog | None:
        row = await self.get_by_call_id(call_id)
        if row is None:
            return None
        for key, value in fields.items():
            if hasattr(row, key) and value is not None:
                setattr(row, key, value)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def count(self) -> int:
        stmt = select(func.count()).select_from(CallLog)
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def count_by_status(self, status: str) -> int:
        stmt = (
            select(func.count())
            .select_from(CallLog)
            .where(CallLog.status == status)
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def count_today(self) -> int:
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        stmt = (
            select(func.count())
            .select_from(CallLog)
            .where(CallLog.started_at >= today_start)
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0


class AppointmentRepository:
    """Pure data-access layer for appointments."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **fields: Any) -> Appointment:
        row = Appointment(**fields)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_all(self) -> list[Appointment]:
        stmt = select(Appointment).order_by(Appointment.date_time.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, apt_id: str) -> Appointment | None:
        stmt = select(Appointment).where(Appointment.id == apt_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, apt_id: str, **fields: Any) -> Appointment | None:
        row = await self.get_by_id(apt_id)
        if row is None:
            return None
        for key, value in fields.items():
            if hasattr(row, key) and value is not None:
                setattr(row, key, value)
        row.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def delete(self, apt_id: str) -> bool:
        stmt = delete(Appointment).where(Appointment.id == apt_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return (result.rowcount or 0) > 0

    async def count(self) -> int:
        stmt = select(func.count()).select_from(Appointment)
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def count_by_status(self, status: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Appointment)
            .where(Appointment.status == status)
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def count_today(self) -> int:
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = today_start.replace(hour=23, minute=59, second=59)
        stmt = (
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.date_time >= today_start,
                Appointment.date_time <= today_end,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0
