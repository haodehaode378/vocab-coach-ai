from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import FocusSession, ReviewLog, Task, VocabItem
from app.core.services import get_or_create_user, get_or_create_user_settings

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def stats_overview(user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_email)
    setting = get_or_create_user_settings(db, user_email)
    now = datetime.utcnow()
    start = datetime(now.year, now.month, now.day)

    base_filters = [VocabItem.user_id == user.id]
    if setting.current_book_tag:
        base_filters.append(VocabItem.tags == setting.current_book_tag)

    vocab_count = db.query(VocabItem).filter(and_(*base_filters)).count()
    due_today = (
        db.query(VocabItem)
        .filter(and_(*base_filters, or_(VocabItem.next_review_at.is_(None), VocabItem.next_review_at <= now)))
        .count()
    )
    today_reviewed = (
        db.query(ReviewLog)
        .filter(and_(ReviewLog.user_id == user.id, ReviewLog.reviewed_at >= start))
        .count()
    )

    return {
        "success": True,
        "data": {
            "vocab_count": vocab_count,
            "due_today": due_today,
            "today_reviewed": today_reviewed,
        },
    }


@router.get("/dashboard")
def stats_dashboard(user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_email)
    setting = get_or_create_user_settings(db, user_email)
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)

    base_filters = [VocabItem.user_id == user.id]
    if setting.current_book_tag:
        base_filters.append(VocabItem.tags == setting.current_book_tag)

    vocab_count = db.query(VocabItem).filter(and_(*base_filters)).count()
    due_today = (
        db.query(VocabItem)
        .filter(and_(*base_filters, or_(VocabItem.next_review_at.is_(None), VocabItem.next_review_at <= now)))
        .count()
    )
    today_reviewed = (
        db.query(ReviewLog)
        .filter(and_(ReviewLog.user_id == user.id, ReviewLog.reviewed_at >= today_start))
        .count()
    )

    today_focus_minutes = (
        db.query(func.sum(FocusSession.duration_minutes))
        .filter(and_(FocusSession.user_id == user.id, FocusSession.is_completed == True, FocusSession.started_at >= today_start))
        .scalar() or 0
    )

    today_tasks_completed = (
        db.query(Task)
        .filter(and_(Task.user_id == user.id, Task.status == "done", Task.completed_at >= today_start))
        .count()
    )

    review_trend = []
    focus_trend = []
    for i in range(6, -1, -1):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        review_cnt = (
            db.query(ReviewLog)
            .filter(and_(ReviewLog.user_id == user.id, ReviewLog.reviewed_at >= day_start, ReviewLog.reviewed_at < day_end))
            .count()
        )
        focus_min = (
            db.query(func.sum(FocusSession.duration_minutes))
            .filter(and_(FocusSession.user_id == user.id, FocusSession.is_completed == True, FocusSession.started_at >= day_start, FocusSession.started_at < day_end))
            .scalar() or 0
        )
        review_trend.append({"date": day_start.strftime("%m-%d"), "count": review_cnt})
        focus_trend.append({"date": day_start.strftime("%m-%d"), "minutes": focus_min})

    return {
        "success": True,
        "data": {
            "vocab_count": vocab_count,
            "due_today": due_today,
            "today_reviewed": today_reviewed,
            "today_focus_minutes": today_focus_minutes,
            "today_tasks_completed": today_tasks_completed,
            "review_trend": review_trend,
            "focus_trend": focus_trend,
        },
    }

