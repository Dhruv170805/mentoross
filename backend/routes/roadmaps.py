"""MentorOS – Roadmap Routes"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from core.security import get_current_user_id
from models.all_models import (
    Roadmap, RoadmapCreate,
    RoadmapPhase, PhaseCreate,
    RoadmapTopic, TopicCreate, TopicUpdate, utcnow,
)
from beanie import PydanticObjectId

router = APIRouter(prefix="/roadmaps", tags=["Roadmaps"])


@router.get("/", response_model=List[dict])
async def list_roadmaps(user_id: str = Depends(get_current_user_id)):
    roadmaps = await Roadmap.find({"user_id": user_id, "is_active": True}).sort("-created_at").to_list()
    result = []
    for rm in roadmaps:
        phases = await RoadmapPhase.find({"roadmap_id": str(rm.id)}).sort("order_index").to_list()
        all_topics = []
        phases_data = []
        for ph in phases:
            topics = await RoadmapTopic.find({"phase_id": str(ph.id)}).sort("order_index").to_list()
            all_topics.extend(topics)
            phases_data.append({
                "id": str(ph.id), "title": ph.title, "duration": ph.duration,
                "order_index": ph.order_index,
                "topics": [{"id": str(t.id), "name": t.name, "type": t.type,
                             "done": t.done, "order_index": t.order_index} for t in topics],
            })
        done  = len([t for t in all_topics if t.done])
        total = len(all_topics)
        d = rm.model_dump()
        d["id"] = str(d.pop("id"))
        result.append({
            **d, "phases": phases_data,
            "progress_pct": round(done / total * 100) if total else 0,
            "topics_done": done, "topics_total": total,
        })
    return result


@router.post("/", response_model=dict, status_code=201)
async def create_roadmap(rm_in: RoadmapCreate, user_id: str = Depends(get_current_user_id)):
    rm = Roadmap(**rm_in.model_dump(), user_id=user_id)
    await rm.insert()
    d = rm.model_dump()
    d["id"] = str(d.pop("id"))
    return {**d, "phases": [], "progress_pct": 0, "topics_done": 0, "topics_total": 0}


@router.delete("/{roadmap_id}", status_code=204)
async def delete_roadmap(roadmap_id: str, user_id: str = Depends(get_current_user_id)):
    rm = await Roadmap.get(PydanticObjectId(roadmap_id))
    if not rm or rm.user_id != user_id:
        raise HTTPException(status_code=404)
    rm.is_active = False
    await rm.save()


@router.post("/{roadmap_id}/phases", response_model=dict, status_code=201)
async def add_phase(roadmap_id: str, ph_in: PhaseCreate, user_id: str = Depends(get_current_user_id)):
    rm = await Roadmap.get(PydanticObjectId(roadmap_id))
    if not rm or rm.user_id != user_id:
        raise HTTPException(status_code=404)
    existing = await RoadmapPhase.find({"roadmap_id": roadmap_id}).to_list()
    order = len(existing)
    phase = RoadmapPhase(roadmap_id=roadmap_id, title=ph_in.title, duration=ph_in.duration, order_index=order)
    await phase.insert()
    topics_data = []
    for i, name in enumerate(ph_in.topics or []):
        if name.strip():
            t = RoadmapTopic(phase_id=str(phase.id), name=name.strip(), order_index=i)
            await t.insert()
            topics_data.append({"id": str(t.id), "name": name.strip(), "type": "learning", "done": False, "order_index": i})
    return {"id": str(phase.id), "title": phase.title, "duration": phase.duration,
            "order_index": phase.order_index, "topics": topics_data}


@router.delete("/phases/{phase_id}", status_code=204)
async def delete_phase(phase_id: str, user_id: str = Depends(get_current_user_id)):
    ph = await RoadmapPhase.get(PydanticObjectId(phase_id))
    if not ph:
        raise HTTPException(status_code=404)
    rm = await Roadmap.get(PydanticObjectId(ph.roadmap_id))
    if not rm or rm.user_id != user_id:
        raise HTTPException(status_code=403)
    topics = await RoadmapTopic.find({"phase_id": phase_id}).to_list()
    for t in topics:
        await t.delete()
    await ph.delete()


@router.post("/phases/{phase_id}/topics", response_model=dict, status_code=201)
async def add_topic(phase_id: str, topic_in: TopicCreate, user_id: str = Depends(get_current_user_id)):
    ph = await RoadmapPhase.get(PydanticObjectId(phase_id))
    if not ph:
        raise HTTPException(status_code=404)
    existing = await RoadmapTopic.find({"phase_id": phase_id}).to_list()
    topic = RoadmapTopic(phase_id=phase_id, name=topic_in.name, type=topic_in.type, order_index=len(existing))
    await topic.insert()
    return {"id": str(topic.id), "name": topic.name, "type": topic.type,
            "done": topic.done, "order_index": topic.order_index}


@router.patch("/topics/{topic_id}", response_model=dict)
async def update_topic(topic_id: str, data: TopicUpdate, user_id: str = Depends(get_current_user_id)):
    topic = await RoadmapTopic.get(PydanticObjectId(topic_id))
    if not topic:
        raise HTTPException(status_code=404)
    if data.done is not None:
        topic.done = data.done
        topic.done_at = utcnow() if data.done else None
    if data.name is not None:
        topic.name = data.name
    await topic.save()
    return {"id": str(topic.id), "name": topic.name, "type": topic.type, "done": topic.done}


@router.delete("/topics/{topic_id}", status_code=204)
async def delete_topic(topic_id: str, user_id: str = Depends(get_current_user_id)):
    topic = await RoadmapTopic.get(PydanticObjectId(topic_id))
    if not topic:
        raise HTTPException(status_code=404)
    await topic.delete()
