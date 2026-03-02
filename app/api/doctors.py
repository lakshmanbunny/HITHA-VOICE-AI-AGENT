from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.modules.dashboard.doctors_data import (
    AVAILABLE_SLOTS,
    DEPARTMENTS,
    DOCTORS,
)

router = APIRouter(tags=["Doctors"])


@router.get("/api/doctors")
async def list_doctors(
    specialty: str | None = Query(default=None),
) -> list[dict]:
    if specialty:
        return [d for d in DOCTORS if d["specialty"].lower() == specialty.lower()]
    return DOCTORS


@router.get("/api/doctors/{doctor_id}/slots")
async def get_doctor_slots(
    doctor_id: str,
    date: str = Query(default="tomorrow"),
) -> dict:
    doc = next((d for d in DOCTORS if d["id"] == doctor_id), None)
    if doc is None:
        raise HTTPException(status_code=404, detail="Doctor not found")

    return {
        "doctor_id": doctor_id,
        "doctor_name": doc["name"],
        "date": date,
        "available_slots": AVAILABLE_SLOTS,
        "total_available": len(AVAILABLE_SLOTS),
    }


@router.get("/api/departments")
async def list_departments() -> list[str]:
    return DEPARTMENTS
