"""
MentorOS – Async Database Engine (MongoDB via Motor/Beanie)

Lazy-reconnect pattern for Vercel serverless:
- init_db() is called at startup AND on any request when db is not ready
- This ensures warm instances reconnect automatically after Atlas IP
  whitelist is updated or a transient network error clears
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
    Safe to call multiple times — idempotent.

    Vercel notes:
    - No tlsCAFile: system CA store on Vercel already trusts Atlas certs.
    - Passing certifi.where() causes TLSV1_ALERT_INTERNAL_ERROR.
    - mongodb+srv:// implies tls=True automatically.
    """
    try:
        # Close stale client if exists
        if mongodb.client:
            try:
                mongodb.client.close()
            except Exception:
                pass

        mongodb.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
            socketTimeoutMS=10000,
        )
        mongodb.db = mongodb.client[settings.DATABASE_NAME]
        await init_beanie(database=mongodb.db, document_models=DOCUMENT_MODELS)
        mongodb.ready = True
        log.info("database.initialised db=%s", settings.DATABASE_NAME)
    except Exception as exc:
        mongodb.ready = False
        safe_uri = (
            settings.MONGODB_URI.split("@")[-1]
            if "@" in settings.MONGODB_URI
            else "local (not set)"
        )
        log.error("database.init_failed host=%s error=%s", safe_uri, exc)


async def ensure_db() -> bool:
    """
    Lazy reconnect: try to connect if not already ready.
    Called at the start of each request so warm instances auto-recover.
    Returns True if DB is available, False otherwise.
    """
    if mongodb.ready:
        return True
    log.info("database.lazy_reconnect attempting...")
    await init_db()
    return mongodb.ready


async def get_db():
    """FastAPI dependency — yields the async Mongo DB instance."""
    ready = await ensure_db()
    if not ready:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check MONGODB_URI in Vercel env vars.",
        )
    yield mongodb.db
