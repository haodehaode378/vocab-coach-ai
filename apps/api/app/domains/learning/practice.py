import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import PracticeAnswer, PracticeSession, VocabItem
from app.domains.productivity import checkin as checkin_router
from app.core.services import get_or_create_user, get_or_create_user_settings

router = APIRouter(prefix="/api/practice", tags=["practice"])


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


@router.post("/generate")
def practice_generate(body: PracticeGenerateBody, db: Session = Depends(get_db)):
    if body.mode not in {"mcq", "spelling"}:
        raise HTTPException(status_code=400, detail="Invalid mode")

    user = get_or_create_user(db, body.user_email)
    setting = get_or_create_user_settings(db, body.user_email)
    base_filters = [VocabItem.user_id == user.id]
    if setting.current_book_tag:
        base_filters.append(VocabItem.tags == setting.current_book_tag)
    words = db.query(VocabItem).filter(and_(*base_filters)).all()
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


@router.post("/submit")
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

