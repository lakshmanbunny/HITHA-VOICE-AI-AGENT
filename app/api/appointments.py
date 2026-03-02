from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.dashboard.service import DashboardService

router = APIRouter(tags=["Appointments"])


def _apt_to_dict(row) -> dict:
    return {
        "id": row.id,
        "callId": row.call_id,
        "patientName": row.patient_name,
        "phoneNumber": row.phone_number,
        "doctorName": row.doctor_name,
        "department": row.department,
        "dateTime": row.date_time.isoformat() if row.date_time else "",
        "status": row.status,
        "symptoms": row.symptoms or [],
    }


class AppointmentCreate(BaseModel):
    patientName: str
    phoneNumber: str = ""
    doctorName: str = ""
    department: str = ""
    dateTime: str
    symptoms: list[str] = []


class AppointmentUpdate(BaseModel):
    patientName: Optional[str] = None
    phoneNumber: Optional[str] = None
    doctorName: Optional[str] = None
    department: Optional[str] = None
    dateTime: Optional[str] = None
    status: Optional[str] = None
    symptoms: Optional[list[str]] = None


@router.get("/api/appointments")
async def list_appointments(
    session: AsyncSession = Depends(get_db),
) -> list[dict]:
    svc = DashboardService(session)
    rows = await svc.get_all_appointments()
    return [_apt_to_dict(r) for r in rows]


@router.post("/api/appointments")
async def create_appointment(
    body: AppointmentCreate,
    session: AsyncSession = Depends(get_db),
) -> dict:
    from dateutil import parser as dtparser

    try:
        dt = dtparser.parse(body.dateTime)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid dateTime format")

    svc = DashboardService(session)
    row = await svc.create_appointment(
        patient_name=body.patientName,
        phone_number=body.phoneNumber,
        doctor_name=body.doctorName,
        department=body.department,
        date_time=dt,
        status="confirmed",
        symptoms=body.symptoms,
    )
    return _apt_to_dict(row)


@router.put("/api/appointments/{apt_id}")
async def update_appointment(
    apt_id: str,
    body: AppointmentUpdate,
    session: AsyncSession = Depends(get_db),
) -> dict:
    updates: dict = {}
    if body.patientName is not None:
        updates["patient_name"] = body.patientName
    if body.phoneNumber is not None:
        updates["phone_number"] = body.phoneNumber
    if body.doctorName is not None:
        updates["doctor_name"] = body.doctorName
    if body.department is not None:
        updates["department"] = body.department
    if body.status is not None:
        updates["status"] = body.status
    if body.symptoms is not None:
        updates["symptoms"] = body.symptoms
    if body.dateTime is not None:
        from dateutil import parser as dtparser

        try:
            updates["date_time"] = dtparser.parse(body.dateTime)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid dateTime format")

    svc = DashboardService(session)
    row = await svc.update_appointment(apt_id, **updates)
    if row is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return _apt_to_dict(row)


@router.delete("/api/appointments/{apt_id}")
async def cancel_appointment(
    apt_id: str,
    session: AsyncSession = Depends(get_db),
) -> dict:
    svc = DashboardService(session)
    row = await svc.cancel_appointment(apt_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment cancelled", "appointment": _apt_to_dict(row)}
