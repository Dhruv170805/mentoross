"""MentorOS – Notes Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from core.security import get_current_user_id
from models.all_models import Note, NoteCreate, NoteRead, map_note, utcnow
from beanie import PydanticObjectId

router = APIRouter(prefix="/notes", tags=["Notes"])


@router.get("/", response_model=List[NoteRead])
async def list_notes(
    limit: int = Query(50, le=200),
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
):
    notes = await Note.find({"user_id": user_id}).sort("-created_at").skip(offset).limit(limit).to_list()
    return [map_note(n) for n in notes]


@router.post("/", response_model=NoteRead, status_code=201)
async def create_note(note_in: NoteCreate, user_id: str = Depends(get_current_user_id)):
    note = Note(**note_in.model_dump(), user_id=user_id)
    await note.insert()
    # Attempt vector embedding — non-fatal
    try:
        from services.vector_store import add_to_vector_store
        await add_to_vector_store(
            text=note.content,
            metadata={"note_id": str(note.id), "user_id": user_id, "title": note.title},
        )
        note.embedded = True
        await note.save()
    except Exception:
        pass
    return map_note(note)


@router.get("/search")
async def search_notes(
    q: str = Query(..., min_length=2),
    k: int = Query(5, le=20),
    user_id: str = Depends(get_current_user_id),
):
    # Keyword search (always works; vector search is optional)
    notes = await Note.find({
        "user_id": user_id,
        "$or": [
            {"title": {"$regex": q, "$options": "i"}},
            {"content": {"$regex": q, "$options": "i"}},
        ],
    }).limit(k).to_list()
    results = [{
        "content": f"{n.title}: {n.content[:100]}...",
        "score": 1.0,
        "metadata": {"note_id": str(n.id), "title": n.title, "user_id": n.user_id},
    } for n in notes]
    return {"query": q, "results": results, "engine": "keyword"}


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: str, user_id: str = Depends(get_current_user_id)):
    note = await Note.get(PydanticObjectId(note_id))
    if not note or note.user_id != user_id:
        raise HTTPException(status_code=404, detail="Note not found")
    await note.delete()


@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(note_id: str, data: dict, user_id: str = Depends(get_current_user_id)):
    note = await Note.get(PydanticObjectId(note_id))
    if not note or note.user_id != user_id:
        raise HTTPException(status_code=404)
    for k, v in data.items():
        if k in {"title", "content", "tags"}:
            setattr(note, k, v)
    note.updated_at = utcnow()
    await note.save()
    return map_note(note)
