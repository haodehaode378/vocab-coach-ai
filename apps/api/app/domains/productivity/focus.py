from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import FocusSession
from app.core.services import get_or_create_user

router = APIRouter(prefix="/api/focus", tags=["focus"])


class FocusStartBody(BaseModel):
    duration_minutes: int = 25
    task_id: int | None = None
    user_email: str = "local@ai-vocab-agent.dev"


class FocusEndBody(BaseModel):
    focus_session_id: int
    is_completed: bool = True
    user_email: str = "local@ai-vocab-agent.dev"


@router.post("/start")
def focus_start(body: FocusStartBody, db: Session = Depends(get_db)):
    user = get_or_create_user(db, body.user_email)
    session = FocusSession(
        user_id=user.id,
        task_id=body.task_id,
        duration_minutes=body.duration_minutes,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"success": True, "data": {"focus_session_id": session.id, "started_at": session.started_at}}


@router.post("/end")
def focus_end(body: FocusEndBody, db: Session = Depends(get_db)):
    user = get_or_create_user(db, body.user_email)
    session = db.query(FocusSession).filter(
        and_(FocusSession.id == body.focus_session_id, FocusSession.user_id == user.id)
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Focus session not found")
    session.ended_at = datetime.utcnow()
    session.is_completed = body.is_completed
    db.commit()
    return {"success": True, "data": {"focus_session_id": session.id, "ended_at": session.ended_at, "is_completed": session.is_completed}}


@router.get("/history")
def focus_history(limit: int = 50, offset: int = 0, user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_email)
    sessions = (
        db.query(FocusSession)
        .filter(FocusSession.user_id == user.id)
        .order_by(FocusSession.started_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "task_id": s.task_id,
                "duration_minutes": s.duration_minutes,
                "started_at": s.started_at,
                "ended_at": s.ended_at,
                "is_completed": s.is_completed,
            }
            for s in sessions
        ],
    }

