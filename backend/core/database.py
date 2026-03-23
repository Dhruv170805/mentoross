"""
MentorOS – Async Database Engine (MongoDB via Motor/Beanie)
"""
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
from beanie import init_beanie
from core.config import settings
import structlog
from models.all_models import (
    User, Task, Note, Roadmap, RoadmapPhase, RoadmapTopic, Resource, DailyPlan, AIReview, StudySession
)

log = structlog.get_logger()

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

mongodb = MongoDB()

async def init_db() -> None:
    """Connect to MongoDB and initialize Beanie ODM with improved resilience."""
    try:
        # Add a timeout for server selection to prevent hangs on cold starts/misconfigs
        mongodb.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000  # 5 second timeout for connection
        )
        mongodb.db = mongodb.client[settings.DATABASE_NAME]
        
        await init_beanie(
            database=mongodb.db,
            document_models=[
                User, Task, Note, Roadmap, RoadmapPhase, RoadmapTopic, Resource, DailyPlan, AIReview, StudySession
            ]
        )
        log.info("database.initialized", db=settings.DATABASE_NAME)
    except Exception as e:
        log.error("database.init_failed", error=str(e), uri=settings.MONGODB_URI.split("@")[-1] if "@" in settings.MONGODB_URI else "local")
        raise RuntimeError(f"Failed to connect to database: {str(e)}") from e

async def get_db():
    """FastAPI dependency: yields the async Mongo DB instance."""
    yield mongodb.db
