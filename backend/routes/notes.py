"""MentorOS – Notes Routes (Beanie)"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from core.security import get_current_user_id
from models.all_models import Note, NoteCreate, NoteRead, map_note, utcnow
from services.vector_store import add_to_vector_store, semantic_search
from beanie import PydanticObjectId

router = APIRouter(prefix="/notes", tags=["Notes"])

@router.get("/", response_model=List[NoteRead])
async def list_notes(
    limit: int = Query(50, le=200),
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
):
    notes = await Note.find(Note.user_id == user_id).sort(-Note.created_at).skip(offset).limit(limit).to_list()
    return [map_note(n) for n in notes]

@router.post("/", response_model=NoteRead, status_code=201)
async def create_note(
    note_in: NoteCreate,
    user_id: str = Depends(get_current_user_id),
):
    note = Note(**note_in.model_dump(), user_id=user_id)
    await note.insert()

    try:
        await add_to_vector_store(text=note.content, metadata={"note_id": str(note.id), "user_id": user_id, "title": note.title})
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
    results = await semantic_search(q, k=k, user_id=user_id)
    return {"query": q, "results": results}

@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: str, user_id: str = Depends(get_current_user_id)):
    note = await Note.get(PydanticObjectId(note_id))
    if not note or note.user_id != user_id:
        raise HTTPException(status_code=404, detail="Note not found")
    await note.delete()

@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: str,
    data: dict,
    user_id: str = Depends(get_current_user_id),
):
    note = await Note.get(PydanticObjectId(note_id))
    if not note or note.user_id != user_id:
        raise HTTPException(status_code=404)
    allowed = {"title", "content", "tags"}
    for k, v in data.items():
        if k in allowed:
            setattr(note, k, v)
    note.updated_at = utcnow()
    await note.save()
    return map_note(note)
