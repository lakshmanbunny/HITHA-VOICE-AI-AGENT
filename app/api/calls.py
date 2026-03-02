from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.dashboard.service import DashboardService

router = APIRouter(tags=["Calls"])


def _call_log_to_dict(row, svc: DashboardService) -> dict:
    return {
        "id": row.call_id,
        "callerName": row.caller_name,
        "phoneNumber": row.phone_number,
        "direction": row.direction,
        "languages": row.languages or [],
        "timestamp": row.started_at.isoformat() if row.started_at else "",
        "duration": svc.format_duration(row.duration_seconds or 0),
        "status": row.status if row.status != "in-progress" else "completed",
        "transcript": row.transcript or [],
        "appointmentId": row.appointment_id,
    }


@router.get("/api/calls")
async def list_calls(session: AsyncSession = Depends(get_db)) -> list[dict]:
    svc = DashboardService(session)
    rows = await svc.get_all_call_logs()
    return [_call_log_to_dict(r, svc) for r in rows]


@router.get("/api/calls/{call_id}")
async def get_call(
    call_id: str, session: AsyncSession = Depends(get_db)
) -> dict:
    svc = DashboardService(session)
    row = await svc.get_call_log(call_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Call not found")
    return _call_log_to_dict(row, svc)
