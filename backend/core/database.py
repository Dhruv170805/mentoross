"""
MentorOS – Async Database Engine (MongoDB via Motor/Beanie)
Resilient: startup never crashes — errors surface at request time as 503.
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
from beanie import init_beanie
from core.config import settings
from models.all_models import (
    User, Task, Note, Roadmap, RoadmapPhase, RoadmapTopic,
    Resource, DailyPlan, AIReview, StudySession,
)

log = logging.getLogger("mentoross.db")

DOCUMENT_MODELS = [
    User, Task, Note, Roadmap, RoadmapPhase, RoadmapTopic,
    Resource, DailyPlan, AIReview, StudySession,
]


class MongoDB:
    client: AsyncIOMotorClient = None
    db = None
    ready: bool = False


mongodb = MongoDB()


async def init_db() -> None:
    """
    Connect to MongoDB and initialise Beanie ODM.
    On serverless (Vercel): a connection failure logs a warning but does NOT
    crash the process — requests that need the DB will return 503.
    """
    try:
        mongodb.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=8000,   # 8 s — generous for cold starts
            connectTimeoutMS=8000,
            socketTimeoutMS=10000,
        )
        mongodb.db = mongodb.client[settings.DATABASE_NAME]

        await init_beanie(database=mongodb.db, document_models=DOCUMENT_MODELS)
        mongodb.ready = True
        log.info("database.initialised db=%s", settings.DATABASE_NAME)
    except Exception as exc:
        safe_uri = settings.MONGODB_URI.split("@")[-1] if "@" in settings.MONGODB_URI else "local"
        log.error("database.init_failed host=%s error=%s", safe_uri, exc)
        # Do NOT re-raise — let the app start; requests will fail with 503


async def get_db():
    """FastAPI dependency — yields the async Mongo DB instance."""
    if not mongodb.ready:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database not available. Check backend configuration.")
    yield mongodb.db
