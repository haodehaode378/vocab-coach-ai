from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DailyCheckin, FocusSession, ReviewLog, Task
from app.services import get_or_create_user

router = APIRouter(prefix="/api/checkin", tags=["checkin"])


@router.get("/calendar")
def calendar(year: int | None = None, month: int | None = None, user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_email)
    now = datetime.utcnow()
    y = year or now.year
    m = month or now.month
    start = datetime(y, m, 1)
    if m == 12:
        end = datetime(y + 1, 1, 1)
    else:
        end = datetime(y, m + 1, 1)

    checkins = (
        db.query(DailyCheckin)
        .filter(and_(DailyCheckin.user_id == user.id, DailyCheckin.date >= start, DailyCheckin.date < end))
        .all()
    )

    records = {c.date.strftime("%Y-%m-%d"): {
        "checked_in": c.checked_in,
        "review_count": c.review_count,
        "focus_minutes": c.focus_minutes,
        "tasks_completed": c.tasks_completed,
        "streak": c.streak,
    } for c in checkins}

    return {"success": True, "data": {"year": y, "month": m, "records": records}}


@router.get("/streak")
def streak(user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_email)
    latest = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == user.id)
        .order_by(DailyCheckin.date.desc())
        .first()
    )
    current_streak = latest.streak if latest else 0
    return {"success": True, "data": {"current_streak": current_streak}}


def ensure_checkin(db: Session, user_id: int, dt: datetime):
    date_key = datetime(dt.year, dt.month, dt.day)
    checkin = db.query(DailyCheckin).filter(
        and_(DailyCheckin.user_id == user_id, DailyCheckin.date == date_key)
    ).first()
    if not checkin:
        prev = db.query(DailyCheckin).filter(
            and_(DailyCheckin.user_id == user_id, DailyCheckin.date < date_key)
        ).order_by(DailyCheckin.date.desc()).first()
        streak_val = (prev.streak + 1) if prev and prev.checked_in else 1
        checkin = DailyCheckin(
            user_id=user_id,
            date=date_key,
            checked_in=True,
            streak=streak_val,
        )
        db.add(checkin)
    else:
        checkin.checked_in = True
    return checkin


def refresh_checkin_stats(db: Session, user_id: int, dt: datetime):
    date_key = datetime(dt.year, dt.month, dt.day)
    checkin = ensure_checkin(db, user_id, dt)

    review_count = (
        db.query(ReviewLog)
        .filter(
            and_(
                ReviewLog.user_id == user_id,
                ReviewLog.reviewed_at >= date_key,
                ReviewLog.reviewed_at < date_key + timedelta(days=1),
            )
        )
        .count()
    )

    focus_minutes = (
        db.query(func.sum(FocusSession.duration_minutes))
        .filter(
            and_(
                FocusSession.user_id == user_id,
                FocusSession.is_completed == True,
                FocusSession.started_at >= date_key,
                FocusSession.started_at < date_key + timedelta(days=1),
            )
        )
        .scalar() or 0
    )

    tasks_completed = (
        db.query(Task)
        .filter(
            and_(
                Task.user_id == user_id,
                Task.status == "done",
                Task.completed_at >= date_key,
                Task.completed_at < date_key + timedelta(days=1),
            )
        )
        .count()
    )

    checkin.review_count = review_count
    checkin.focus_minutes = focus_minutes
    checkin.tasks_completed = tasks_completed
    db.commit()
    return checkin
