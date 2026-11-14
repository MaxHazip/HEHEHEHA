"""Точка входа FastAPI-приложения."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_module.providers.speech_provider import speech_status
from ai_module.providers.tts_provider import tts_status
from ai_module.providers.vision_provider import vision_status
from backend.api.routes import (
    ai,
    attachments,
    calls,
    telephony,
    tickets,
    users,
    voice,
)
from backend.core.database import create_session_maker, init_db
from backend.core.settings import settings
from backend.services.ari_service import ari_runner
from backend.services.seed import seed_demo_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    async with create_session_maker() as session:
        await seed_demo_data(session)

    ari_runner.start()

    logger.info(
        "Backend готов: DB=%s, AI_PROVIDER=%s, OLLAMA_MODEL=%s, ARI=%s",
        settings.DATABASE_URL.split("://")[0],
        settings.AI_PROVIDER,
        settings.OLLAMA_MODEL,
        "вкл" if settings.ARI_ENABLED else "выкл",
    )
    yield

    await ari_runner.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)
app.include_router(attachments.router)
app.include_router(calls.router)
app.include_router(telephony.router)
app.include_router(ai.router)
app.include_router(users.router)
app.include_router(voice.router)


@app.get("/", tags=["system"])
async def root() -> dict:
    return {"message": "OK", "app": settings.APP_NAME}


@app.get("/api/health", tags=["system"])
async def health() -> dict:
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "database": settings.DATABASE_URL.split("://")[0],
        "ai_provider": settings.AI_PROVIDER,
        "ai_model": settings.OLLAMA_MODEL,
        "speech": speech_status(),
        "vision": vision_status(),
        "tts": tts_status(),
        "telephony": {
            "sip_webhook_enabled": bool(settings.SIP_WEBHOOK_TOKEN),
            "ari": ari_runner.status(),
        },
    }
