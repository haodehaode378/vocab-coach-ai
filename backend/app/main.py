from datetime import datetime, timedelta
import random
from pathlib import Path
import sys

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
for p in (PROJECT_ROOT, BACKEND_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.database import Base, engine, get_db
from app.models import PracticeAnswer, PracticeSession, ReviewLog, VocabItem, FocusSession, Task, DailyCheckin
from app.services import get_or_create_user, import_json_lines
from app.routers.study import get_today_queue, grade_word, GradeBody as StudyGradeBody
from app.routers import checkin as checkin_router

STATIC_DIR = PROJECT_ROOT / "frontend" / "dist"

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Vocab Agent Python", version="1.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import focus, tasks, checkin, ai, system, study
app.include_router(focus.router)
app.include_router(tasks.router)
app.include_router(checkin.router)
app.include_router(ai.router)
app.include_router(system.router)
app.include_router(study.router)


class ImportBody(BaseModel):
    files: list[str] = Field(default_factory=lambda: ["CET4luan_2.json", "CET6_1.json"])
    user_email: str = "local@ai-vocab-agent.dev"


class ReviewBody(BaseModel):
    vocab_item_id: int
    grade: str
    user_email: str = "local@ai-vocab-agent.dev"


class PracticeGenerateBody(BaseModel):
    mode: str = "mcq"
    count: int = 10
    user_email: str = "local@ai-vocab-agent.dev"


class PracticeAnswerRow(BaseModel):
    vocab_item_id: int
    question_type: str
    user_answer: str | None = None
    correct_answer: str


class PracticeSubmitBody(BaseModel):
    session_id: int
    answers: list[PracticeAnswerRow]
    user_email: str = "local@ai-vocab-agent.dev"


@app.get("/healthz")
def healthz():
    return {"ok": True, "time": datetime.utcnow().isoformat()}


@app.get("/api/system/books")
def list_books():
    files = sorted([f.name for f in PROJECT_ROOT.glob("*.json") if f.is_file()])
    return {"success": True, "data": files}


@app.post("/api/vocab/import-json-files")
def import_vocab(body: ImportBody, db: Session = Depends(get_db)):
    files = [str((PROJECT_ROOT / f).resolve()) if not Path(f).is_absolute() else f for f in body.files]
    result = import_json_lines(db, files, body.user_email)
    return {"success": True, "data": result}


@app.get("/api/vocab/list")
def list_vocab(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    user_email: str = "local@ai-vocab-agent.dev",
    db: Session = Depends(get_db),
):
    user = get_or_create_user(db, user_email)
    query = db.query(VocabItem).filter(VocabItem.user_id == user.id)
    if keyword.strip():
        query = query.filter(VocabItem.word.contains(keyword.strip()))

    total = query.count()
    items = (
        query.order_by(VocabItem.word.asc())
        .offset((max(page, 1) - 1) * max(page_size, 1))
        .limit(max(page_size, 1))
        .all()
    )

    return {
        "success": True,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": i.id,
                    "word": i.word,
                    "phonetic": i.phonetic,
                    "meaning_zh": i.meaning_zh,
                    "example": i.example,
                    "tags": i.tags,
                    "next_review_at": i.next_review_at,
                }
                for i in items
            ],
        },
    }


def _grade_map(old_grade: str) -> str:
    mapping = {"again": "forget", "hard": "vague", "good": "know", "easy": "know"}
    return mapping.get(old_grade, "forget")


@app.get("/api/review/today")
def review_today(
    limit: int = 50,
    user_email: str = "local@ai-vocab-agent.dev",
    db: Session = Depends(get_db),
):
    """兼容旧接口：内部委托到 /api/study/today"""
    return get_today_queue(user_email=user_email, db=db)


@app.post("/api/review/grade")
def review_grade(body: ReviewBody, db: Session = Depends(get_db)):
    """兼容旧接口：内部委托到 /api/study/grade"""
    if body.grade not in {"again", "hard", "good", "easy"}:
        raise HTTPException(status_code=400, detail="Invalid grade")
    response = _grade_map(body.grade)
    study_body = StudyGradeBody(
        vocab_item_id=body.vocab_item_id,
        response=response,
        session_type="review",
        user_email=body.user_email,
    )
    return grade_word(body=study_body, db=db)


@app.post("/api/practice/generate")
def practice_generate(body: PracticeGenerateBody, db: Session = Depends(get_db)):
    if body.mode not in {"mcq", "spelling"}:
        raise HTTPException(status_code=400, detail="Invalid mode")

    user = get_or_create_user(db, body.user_email)
    words = db.query(VocabItem).filter(VocabItem.user_id == user.id).all()
    if len(words) < 4:
        raise HTTPException(status_code=400, detail="Need at least 4 words")

    count = max(1, min(body.count, 50))
    picked = random.sample(words, min(count, len(words)))

    questions = []
    for idx, item in enumerate(picked):
        if body.mode == "spelling":
            questions.append(
                {
                    "index": idx,
                    "type": "spelling",
                    "vocab_item_id": item.id,
                    "prompt": item.meaning_zh or item.example or "Spell this word",
                    "correct_answer": item.word,
                }
            )
        else:
            distractor_pool = [w.word for w in words if w.id != item.id]
            choices = random.sample(distractor_pool, 3) + [item.word]
            random.shuffle(choices)
            questions.append(
                {
                    "index": idx,
                    "type": "mcq",
                    "vocab_item_id": item.id,
                    "prompt": item.meaning_zh or item.example or item.word,
                    "choices": choices,
                    "correct_answer": item.word,
                }
            )

    session = PracticeSession(user_id=user.id, mode=body.mode, total_questions=len(questions))
    db.add(session)
    db.commit()
    db.refresh(session)

    return {"success": True, "data": {"session_id": session.id, "questions": questions}}


@app.post("/api/practice/submit")
def practice_submit(body: PracticeSubmitBody, db: Session = Depends(get_db)):
    user = get_or_create_user(db, body.user_email)
    session = db.query(PracticeSession).filter(and_(PracticeSession.id == body.session_id, PracticeSession.user_id == user.id)).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Practice session not found")

    now = datetime.utcnow()
    correct = 0
    wrong_items: list[int] = []

    for ans in body.answers:
        is_correct = (ans.user_answer or "").strip().lower() == ans.correct_answer.strip().lower()
        if is_correct:
            correct += 1
        else:
            wrong_items.append(ans.vocab_item_id)
            item = db.query(VocabItem).filter(and_(VocabItem.id == ans.vocab_item_id, VocabItem.user_id == user.id)).first()
            if item:
                item.next_review_at = now

        db.add(
            PracticeAnswer(
                user_id=user.id,
                session_id=session.id,
                vocab_item_id=ans.vocab_item_id,
                question_type=ans.question_type,
                user_answer=ans.user_answer,
                is_correct=is_correct,
            )
        )

    session.correct_count = correct
    session.ended_at = now
    db.commit()
    checkin_router.refresh_checkin_stats(db, user.id, datetime.utcnow())

    return {
        "success": True,
        "data": {
            "session_id": session.id,
            "total": len(body.answers),
            "correct_count": correct,
            "wrong_count": len(body.answers) - correct,
            "wrong_items": wrong_items,
        },
    }


@app.get("/api/stats/overview")
def stats_overview(user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_email)
    now = datetime.utcnow()
    start = datetime(now.year, now.month, now.day)

    vocab_count = db.query(VocabItem).filter(VocabItem.user_id == user.id).count()
    due_today = (
        db.query(VocabItem)
        .filter(and_(VocabItem.user_id == user.id, or_(VocabItem.next_review_at.is_(None), VocabItem.next_review_at <= now)))
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


@app.get("/api/stats/dashboard")
def stats_dashboard(user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_email)
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)

    vocab_count = db.query(VocabItem).filter(VocabItem.user_id == user.id).count()
    due_today = (
        db.query(VocabItem)
        .filter(and_(VocabItem.user_id == user.id, or_(VocabItem.next_review_at.is_(None), VocabItem.next_review_at <= now)))
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


# 前端静态文件挂载放在所有 API 路由之后，避免拦截 /api/* 请求
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=False)
