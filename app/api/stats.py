from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.dashboard.service import DashboardService

router = APIRouter(tags=["Stats"])


@router.get("/api/stats")
async def get_stats(session: AsyncSession = Depends(get_db)) -> dict:
    svc = DashboardService(session)
    return await svc.compute_stats()
