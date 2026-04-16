from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task
from app.services import get_or_create_user

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreateBody(BaseModel):
    title: str
    description: str | None = None
    priority: str = "medium"
    due_date: datetime | None = None
    user_email: str = "local@ai-vocab-agent.dev"


class TaskUpdateBody(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    due_date: datetime | None = None
    status: str | None = None
    user_email: str = "local@ai-vocab-agent.dev"


@router.get("")
def list_tasks(status: str = "", user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_email)
    query = db.query(Task).filter(Task.user_id == user.id)
    if status:
        query = query.filter(Task.status == status)
    tasks = query.order_by(Task.created_at.desc()).all()
    return {"success": True, "data": tasks}


@router.post("")
def create_task(body: TaskCreateBody, db: Session = Depends(get_db)):
    user = get_or_create_user(db, body.user_email)
    task = Task(
        user_id=user.id,
        title=body.title,
        description=body.description,
        priority=body.priority,
        due_date=body.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"success": True, "data": task}


@router.put("/{task_id}")
def update_task(task_id: int, body: TaskUpdateBody, db: Session = Depends(get_db)):
    user = get_or_create_user(db, body.user_email)
    task = db.query(Task).filter(and_(Task.id == task_id, Task.user_id == user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if body.title is not None:
        task.title = body.title
    if body.description is not None:
        task.description = body.description
    if body.priority is not None:
        task.priority = body.priority
    if body.due_date is not None:
        task.due_date = body.due_date
    if body.status is not None:
        task.status = body.status
        if body.status == "done" and not task.completed_at:
            task.completed_at = datetime.utcnow()
        elif body.status != "done":
            task.completed_at = None
    db.commit()
    db.refresh(task)
    return {"success": True, "data": task}


@router.delete("/{task_id}")
def delete_task(task_id: int, user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_email)
    task = db.query(Task).filter(and_(Task.id == task_id, Task.user_id == user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"success": True, "data": {"deleted": task_id}}
