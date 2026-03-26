"""MentorOS – Resources, Daily Plans, Analytics, AI Agent Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import calendar
import json
from core.security import get_current_user_id
from models.all_models import (
    Resource, ResourceCreate, ResourceUpdate, ResourceRead, map_resource,
    DailyPlan, DailyPlanCreate, map_plan,
    AIReview, StudySession, utcnow, Task, Note, TaskStatus,
)
from services.ai_agents import generate_plan, run_review, explain_concept
from core.constants import SUBJECT_MAP, SUBJECT_COLORS
from beanie import PydanticObjectId

res_router = APIRouter(tags=["Resources"])


@res_router.get("/", response_model=List[ResourceRead])
async def list_resources(
    tag: Optional[str] = None,
    type: Optional[str] = None,
    saved: Optional[bool] = None,
    user_id: str = Depends(get_current_user_id),
):
    query: dict = {"user_id": user_id}
    if tag is not None:
        query["tag"] = tag
    if type is not None:
        query["type"] = type
    if saved is not None:
        query["saved"] = saved
    resources = await Resource.find(query).sort("-created_at").to_list()
    return [map_resource(r) for r in resources]


@res_router.post("/", response_model=ResourceRead, status_code=201)
async def create_resource(res_in: ResourceCreate, user_id: str = Depends(get_current_user_id)):
    res = Resource(**res_in.model_dump(), user_id=user_id)
    await res.insert()
    return map_resource(res)


@res_router.patch("/{res_id}", response_model=ResourceRead)
async def update_resource(res_id: str, data: ResourceUpdate, user_id: str = Depends(get_current_user_id)):
    res = await Resource.get(PydanticObjectId(res_id))
    if not res or res.user_id != user_id:
        raise HTTPException(404)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(res, k, v)
    await res.save()
    return map_resource(res)


@res_router.delete("/{res_id}", status_code=204)
async def delete_resource(res_id: str, user_id: str = Depends(get_current_user_id)):
    res = await Resource.get(PydanticObjectId(res_id))
    if not res or res.user_id != user_id:
        raise HTTPException(404)
    await res.delete()


@res_router.get("/tags")
async def list_tags(user_id: str = Depends(get_current_user_id)):
    resources = await Resource.find({"user_id": user_id}).to_list()
    tags = list({r.tag for r in resources if r.tag})
    return {"tags": tags}


# ── Plans ─────────────────────────────────────────────────────────────────────

plan_router = APIRouter(tags=["Plans"])


@plan_router.get("/today")
async def get_today_plan(user_id: str = Depends(get_current_user_id)):
    today = datetime.now(timezone.utc).date().isoformat()
    plan = await DailyPlan.find_one({"user_id": user_id, "date": today})
    if not plan:
        return None
    d = map_plan(plan).model_dump()
    return {**d, "steps": json.loads(plan.steps)}


@plan_router.post("/", status_code=201)
async def save_plan(plan_in: DailyPlanCreate, user_id: str = Depends(get_current_user_id)):
    today = datetime.now(timezone.utc).date().isoformat()
    existing = await DailyPlan.find_one({"user_id": user_id, "date": today})
    if existing:
        for k, v in plan_in.model_dump().items():
            setattr(existing, k, v)
        await existing.save()
        plan = existing
    else:
        plan = DailyPlan(**plan_in.model_dump(), user_id=user_id, date=today)
        await plan.insert()
    d = map_plan(plan).model_dump()
    return {**d, "steps": json.loads(plan.steps)}


@plan_router.post("/generate")
async def ai_generate_plan(user_id: str = Depends(get_current_user_id)):
    notes = await Note.find({"user_id": user_id}).sort("-created_at").limit(5).to_list()
    tasks = await Task.find({"user_id": user_id, "status": TaskStatus.COMPLETED.value}).sort("-created_at").limit(10).to_list()
    history = f"Recent notes: {[n.content[:100] for n in notes]}. Completed tasks: {[t.title for t in tasks]}"
    return await generate_plan(history)


# ── AI Review ─────────────────────────────────────────────────────────────────

review_router = APIRouter(tags=["AI Review"])


@review_router.post("/evaluate")
async def evaluate(user_id: str = Depends(get_current_user_id)):
    tasks = await Task.find({"user_id": user_id, "status": TaskStatus.COMPLETED.value}).limit(20).to_list()
    notes = await Note.find({"user_id": user_id}).sort("-created_at").limit(10).to_list()
    tasks_str = ", ".join(t.title for t in tasks) or "No tasks completed yet"
    notes_str = " | ".join(n.content[:100] for n in notes) or "No notes yet"
    result = await run_review(tasks_str, notes_str)
    review = AIReview(
        user_id=user_id, score=result["score"],
        feedback=result["feedback"],
        weak_areas=json.dumps(result.get("weak_areas", [])),
        tasks_input=tasks_str, notes_input=notes_str,
    )
    await review.insert()
    return result


@review_router.get("/history")
async def review_history(limit: int = 10, user_id: str = Depends(get_current_user_id)):
    reviews = await AIReview.find({"user_id": user_id}).sort("-created_at").limit(limit).to_list()
    return [{"id": str(r.id), "score": r.score, "feedback": r.feedback,
             "weak_areas": json.loads(r.weak_areas), "created_at": r.created_at} for r in reviews]


# ── AI Teacher ────────────────────────────────────────────────────────────────

teacher_router = APIRouter(tags=["AI Teacher"])

from pydantic import BaseModel as PydanticBase


class ExplainReq(PydanticBase):
    topic: str
    level: str = "intermediate"


@teacher_router.post("/explain")
async def explain(req: ExplainReq, user_id: str = Depends(get_current_user_id)):
    return await explain_concept(req.topic, req.level)


# ── Analytics ─────────────────────────────────────────────────────────────────

analytics_router = APIRouter(tags=["Analytics"])


@analytics_router.get("/overview")
async def analytics_overview(user_id: str = Depends(get_current_user_id)):
    today = datetime.now(timezone.utc).date()
    tasks = await Task.find({"user_id": user_id}).to_list()
    notes = await Note.find({"user_id": user_id}).to_list()

    done  = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    total = len(tasks)
    comp  = len(done)
    mastery = round(comp / total * 100) if total else 0

    weekly = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = len([t for t in done if t.completed_at and t.completed_at.date() == day])
        weekly.append({"date": day.isoformat(), "label": day.strftime("%a"), "count": count})

    heatmap = []
    for i in range(90, -1, -1):
        day = today - timedelta(days=i)
        day_done  = len([t for t in done  if t.completed_at and t.completed_at.date() == day])
        day_notes = len([n for n in notes if n.created_at.date() == day])
        heatmap.append({"date": day.isoformat(), "level": min(day_done + day_notes, 4)})

    days_in_month = calendar.monthrange(today.year, today.month)[1]
    streak_cal = []
    for d in range(1, days_in_month + 1):
        day = today.replace(day=d)
        streak_cal.append({"day": d, "active": day <= today and (
            any(t.completed_at and t.completed_at.date() == day for t in done) or
            any(n.created_at.date() == day for n in notes)
        )})

    subjects_results = []
    for subj, keywords in SUBJECT_MAP.items():
        subj_tasks = [t for t in tasks if any(k in t.title.lower() for k in keywords)]
        color = SUBJECT_COLORS.get(subj, "var(--a1)")
        if not subj_tasks:
            subjects_results.append({"name": subj, "pct": 0, "color": color})
            continue
        subj_done = [t for t in subj_tasks if t.status == TaskStatus.COMPLETED]
        pct = round(len(subj_done) / len(subj_tasks) * 100)
        subjects_results.append({"name": subj, "pct": pct, "color": color})

    return {
        "mastery": mastery,
        "tasks_total": total, "tasks_done": comp, "notes_total": len(notes),
        "weekly": weekly, "heatmap": heatmap,
        "streak_cal": streak_cal, "subjects": subjects_results,
    }


# ── Reminders ─────────────────────────────────────────────────────────────────

reminder_router = APIRouter(tags=["Reminders"])


@reminder_router.get("/active")
async def get_active_reminders(user_id: str = Depends(get_current_user_id)):
    return []
