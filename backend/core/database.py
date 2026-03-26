"""
MentorOS – Async Database Engine (MongoDB via Motor/Beanie)
Resilient: startup never crashes — errors surface at request time as 503.
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient
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
    Connect to MongoDB Atlas and initialise Beanie ODM.

    TLS notes for Vercel (Python 3.12 on Amazon Linux 2):
    - Do NOT pass tlsCAFile — Vercel's system CA store already trusts Atlas.
    - Passing certifi.where() causes TLSV1_ALERT_INTERNAL_ERROR because
      certifi's bundle conflicts with the system OpenSSL CA negotiation.
    """
    try:
        mongodb.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
            socketTimeoutMS=10000,
            # tls=True is implied by the mongodb+srv:// scheme
            # tlsCAFile intentionally omitted — let the system CA store handle it
        )
        mongodb.db = mongodb.client[settings.DATABASE_NAME]

        await init_beanie(database=mongodb.db, document_models=DOCUMENT_MODELS)
        mongodb.ready = True
        log.info("database.initialised db=%s", settings.DATABASE_NAME)
    except Exception as exc:
        safe_uri = (
            settings.MONGODB_URI.split("@")[-1]
            if "@" in settings.MONGODB_URI
            else "local"
        )
        log.error("database.init_failed host=%s error=%s", safe_uri, exc)
        # Do NOT re-raise — let the app start; requests return 503 gracefully


async def get_db():
    """FastAPI dependency — yields the async Mongo DB instance."""
    if not mongodb.ready:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Database not available. Check MONGODB_URI in Vercel env vars.",
        )
    yield mongodb.db
