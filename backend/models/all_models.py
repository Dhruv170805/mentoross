"""
MentorOS – Database Models (MongoDB via Beanie)
"""
from pydantic import BaseModel, Field
from beanie import Document, Indexed
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

# ─── Enums ────────────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING   = "pending"
    COMPLETED = "completed"
    ARCHIVED  = "archived"

class TaskPriority(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"

class TaskType(str, Enum):
    LEARNING  = "learning"
    PRACTICE  = "practice"
    REVISION  = "revision"
    MANUAL    = "manual"

class ResourceType(str, Enum):
    COURSE   = "course"
    BOOK     = "book"
    VIDEO    = "video"
    ARTICLE  = "article"
    TOOL     = "tool"
    PODCAST  = "podcast"
    REPO     = "repo"
    DOC      = "doc"

class Difficulty(str, Enum):
    VERY_EASY = "very_easy"
    EASY      = "easy"
    MEDIUM    = "medium"
    HARD      = "hard"
    VERY_HARD = "very_hard"

# ─── Document Base & Read Models ──────────────────────────────────────────────
# We don't define 'id' explicitly in Documents, beanie provides it as PydanticObjectId.
# But for readout/FastAPI JSON response, we want to cast id to string easily.

class BaseRead(BaseModel):
    id: str

# ─── User ─────────────────────────────────────────────────────────────────────

class User(Document):
    email: Indexed(str, unique=True)
    name: str = Field(max_length=100)
    hashed_password: str
    avatar_url: Optional[str] = None
    plan: str = "free"
    learning_goal: Optional[str] = None
    streak_days: int = 0
    last_active: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "users"

# ─── Task ─────────────────────────────────────────────────────────────────────

class Task(Document):
    user_id: str
    title: str = Field(max_length=500)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    type: TaskType = TaskType.MANUAL
    due_date: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tasks"

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    type: TaskType = TaskType.MANUAL
    due_date: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    type: Optional[TaskType] = None
    due_date: Optional[str] = None

class TaskRead(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    type: TaskType
    due_date: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

def map_task(task: Task) -> TaskRead:
    d = task.model_dump()
    d['id'] = str(d.pop('id'))
    return TaskRead(**d)

# ─── Note ─────────────────────────────────────────────────────────────────────

class Note(Document):
    user_id: str
    title: str = Field(default="Quick Note", max_length=200)
    content: str
    tags: Optional[str] = None
    embedded: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "notes"

class NoteCreate(BaseModel):
    title: str = "Quick Note"
    content: str
    tags: Optional[str] = None

class NoteRead(BaseModel):
    id: str
    user_id: str
    title: str
    content: str
    tags: Optional[str]
    embedded: bool
    created_at: datetime

def map_note(note: Note) -> NoteRead:
    d = note.model_dump()
    d['id'] = str(d.pop('id'))
    return NoteRead(**d)


# ─── Roadmap ──────────────────────────────────────────────────────────────────

class Roadmap(Document):
    user_id: str
    name: str = Field(max_length=200)
    description: Optional[str] = None
    goal: Optional[str] = None
    duration: str = "6 months"
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "roadmaps"

class RoadmapCreate(BaseModel):
    name: str
    description: Optional[str] = None
    goal: Optional[str] = None
    duration: str = "6 months"

class RoadmapRead(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    goal: Optional[str]
    duration: str
    created_at: datetime

def map_roadmap(r: Roadmap) -> RoadmapRead:
    d = r.model_dump()
    d['id'] = str(d.pop('id'))
    return RoadmapRead(**d)

class RoadmapPhase(Document):
    roadmap_id: str
    title: str = Field(max_length=200)
    duration: Optional[str] = None
    order_index: int = 0
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "roadmap_phases"

class PhaseCreate(BaseModel):
    title: str
    duration: Optional[str] = None
    topics: Optional[List[str]] = []

class RoadmapPhaseRead(BaseModel):
    id: str
    roadmap_id: str
    title: str
    duration: Optional[str]
    order_index: int
    created_at: datetime

def map_phase(p: RoadmapPhase) -> RoadmapPhaseRead:
    d = p.model_dump()
    d['id'] = str(d.pop('id'))
    return RoadmapPhaseRead(**d)

class RoadmapTopic(Document):
    phase_id: str
    name: str = Field(max_length=300)
    type: str = "learning"
    done: bool = False
    order_index: int = 0
    done_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "roadmap_topics"

class TopicCreate(BaseModel):
    name: str
    type: str = "learning"

class TopicUpdate(BaseModel):
    done: Optional[bool] = None
    name: Optional[str] = None

class RoadmapTopicRead(BaseModel):
    id: str
    phase_id: str
    name: str
    type: str
    done: bool
    order_index: int
    done_at: Optional[datetime]
    created_at: datetime

def map_topic(t: RoadmapTopic) -> RoadmapTopicRead:
    d = t.model_dump()
    d['id'] = str(d.pop('id'))
    return RoadmapTopicRead(**d)


# ─── Resource ─────────────────────────────────────────────────────────────────

class Resource(Document):
    user_id: str
    title: str = Field(max_length=300)
    url: str = Field(max_length=2048)
    type: ResourceType = ResourceType.ARTICLE
    description: Optional[str] = None
    tag: Optional[str] = None
    saved: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "resources"

class ResourceCreate(BaseModel):
    title: str
    url: str
    type: ResourceType = ResourceType.ARTICLE
    description: Optional[str] = None
    tag: Optional[str] = None

class ResourceUpdate(BaseModel):
    saved: Optional[bool] = None
    tag: Optional[str] = None

class ResourceRead(BaseModel):
    id: str; user_id: str; title: str; url: str; type: ResourceType
    description: Optional[str]; tag: Optional[str]; saved: bool; created_at: datetime

def map_resource(r: Resource) -> ResourceRead:
    d = r.model_dump()
    d['id'] = str(d.pop('id'))
    return ResourceRead(**d)


# ─── Daily Plan ───────────────────────────────────────────────────────────────

class DailyPlan(Document):
    user_id: str
    date: str
    topic: str
    title: str
    difficulty: Difficulty = Difficulty.MEDIUM
    steps: str = "[]"
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "daily_plans"

class DailyPlanCreate(BaseModel):
    topic: str; title: str
    difficulty: Difficulty = Difficulty.MEDIUM
    steps: str = "[]"

class DailyPlanRead(BaseModel):
    id: str; user_id: str; date: str; topic: str; title: str
    difficulty: Difficulty; steps: str; created_at: datetime

def map_plan(p: DailyPlan) -> DailyPlanRead:
    d = p.model_dump()
    d['id'] = str(d.pop('id'))
    return DailyPlanRead(**d)


# ─── AI Review ────────────────────────────────────────────────────────────────

class AIReview(Document):
    user_id: str
    score: int
    feedback: str
    weak_areas: str = "[]"
    tasks_input: str = ""
    notes_input: str = ""
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "ai_reviews"

class AIReviewRead(BaseModel):
    id: str; user_id: str; score: int; feedback: str
    weak_areas: str; tasks_input: str; notes_input: str; created_at: datetime

def map_review(r: AIReview) -> AIReviewRead:
    d = r.model_dump()
    d['id'] = str(d.pop('id'))
    return AIReviewRead(**d)


# ─── Study Session ────────────────────────────────────────────────────────────

class StudySession(Document):
    user_id: str
    date: str
    duration_minutes: int = 0
    topic: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "study_sessions"

class StudySessionRead(BaseModel):
    id: str; user_id: str; date: str; duration_minutes: int
    topic: Optional[str]; created_at: datetime

def map_session(s: StudySession) -> StudySessionRead:
    d = s.model_dump()
    d['id'] = str(d.pop('id'))
    return StudySessionRead(**d)

