"""MentorOS – Tasks Routes (Beanie)"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone
from core.security import get_current_user_id
from models.all_models import Task, TaskCreate, TaskUpdate, TaskRead, TaskStatus, map_task, utcnow
from beanie import PydanticObjectId

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("/", response_model=List[TaskRead])
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
):
    q = Task.find(Task.user_id == user_id)
    if status is not None:
        q = q.find(Task.status == status)
    if priority is not None:
        q = q.find(Task.priority == priority)
    
    tasks = await q.sort(-Task.created_at).skip(offset).limit(limit).to_list()
    return [map_task(t) for t in tasks]

@router.post("/", response_model=TaskRead, status_code=201)
async def create_task(
    task_in: TaskCreate,
    user_id: str = Depends(get_current_user_id),
):
    task = Task(**task_in.model_dump(), user_id=user_id)
    await task.insert()
    return map_task(task)

@router.get("/stats")
async def task_stats(user_id: str = Depends(get_current_user_id)):
    all_tasks = await Task.find(Task.user_id == user_id).to_list()
    total = len(all_tasks)
    done = len([t for t in all_tasks if t.status == TaskStatus.COMPLETED])
    pending = len([t for t in all_tasks if t.status == TaskStatus.PENDING])
    pct = round(done / total * 100) if total else 0

    from datetime import timedelta
    today = datetime.now(timezone.utc).date()
    weekly = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = len([t for t in all_tasks if t.status == TaskStatus.COMPLETED and t.completed_at and t.completed_at.date() == day])
        weekly.append({"date": day.isoformat(), "count": count, "label": day.strftime("%a")})
    return {"total": total, "done": done, "pending": pending, "completion_pct": pct, "weekly": weekly}

@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: str, user_id: str = Depends(get_current_user_id)):
    task = await Task.get(PydanticObjectId(task_id))
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return map_task(task)

@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: str,
    task_in: TaskUpdate,
    user_id: str = Depends(get_current_user_id),
):
    task = await Task.get(PydanticObjectId(task_id))
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    data = task_in.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(task, k, v)

    if task_in.status == TaskStatus.COMPLETED and not task.completed_at:
        task.completed_at = utcnow()
    elif task_in.status == TaskStatus.PENDING:
        task.completed_at = None

    task.updated_at = utcnow()
    await task.save()
    return map_task(task)

@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, user_id: str = Depends(get_current_user_id)):
    task = await Task.get(PydanticObjectId(task_id))
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")
    await task.delete()
