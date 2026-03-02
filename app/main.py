import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.appointments import router as appointments_router
from app.api.calls import router as calls_router
from app.api.doctors import router as doctors_router
from app.api.health import router as health_router
from app.api.stats import router as stats_router
from app.api.token import router as token_router
from app.config.settings import settings
from app.core.logging import setup_logging
from app.modules.database.session import close_engine, init_db

_STATIC_DIR = Path(__file__).parent / "static"

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    logger.info("Starting %s", settings.APP_NAME)
    await init_db()
    logger.info("Database initialised")
    yield
    await close_engine()
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(token_router)
app.include_router(stats_router)
app.include_router(calls_router)
app.include_router(appointments_router)
app.include_router(doctors_router)


@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(_STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
