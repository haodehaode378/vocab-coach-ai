import asyncio
import json
import random
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.ai_client import chat_complete
from app.core.config_store import load_ai_config
from app.core.database import get_db
from app.core.models import PracticeAnswer, PracticeSession, VocabItem
from app.core.services import get_or_create_user, get_or_create_user_settings
from app.domains.productivity import checkin as checkin_router

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


class PracticeSubmitOneBody(BaseModel):
    session_id: int
    answer: PracticeAnswerRow
    user_email: str = "local@ai-vocab-agent.dev"


def _normalize_sentence(text: str | None, fallback_word: str) -> str:
    raw = (text or "").replace("\n", " ").strip()
    if not raw:
        raw = f"{fallback_word.capitalize()} is useful in college study."
    if raw[-1] not in ".!?":
        raw += "."
    return raw


def _mask_target_word(text: str | None, target_word: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""
    pattern = re.compile(rf"\b{re.escape(target_word)}\b", flags=re.IGNORECASE)
    return pattern.sub("it", raw)


def _local_context_passage(target_word: str, example: str | None) -> str:
    lead = _mask_target_word(_normalize_sentence(example, target_word), target_word)
    if not lead:
        lead = "The paragraph describes a useful academic concept in college life."
    follow = "From the context, infer the best matching word."
    return f"{lead} {follow}"


async def _ai_context_passage(target_word: str, meaning_zh: str | None, example: str | None) -> str | None:
    cfg = load_ai_config()
    if not (cfg.get("api_key") or "").strip():
        return None

    messages = [
        {
            "role": "system",
            "content": "You are an English vocabulary exercise writer. Return strict JSON only.",
        },
        {
            "role": "user",
            "content": (
                "Generate one natural English paragraph (2-4 sentences) for a context-inference vocab question. "
                "The paragraph must center on target word "
                f"'{target_word}', but NEVER include this exact word in the paragraph text. "
                "Keep B1-B2 difficulty and avoid niche topics. "
                f"Chinese meaning hint: {meaning_zh or 'N/A'}. "
                f"Reference example: {example or 'N/A'}. "
                'Return JSON: {"passage":"..."}'
            ),
        },
    ]

    try:
        raw = await asyncio.wait_for(chat_complete(messages=messages, model=cfg.get("model")), timeout=8)
    except asyncio.TimeoutError:
        return None

    if not raw or raw.startswith("[AI "):
        return None

    try:
        data = json.loads(raw)
        passage = (data.get("passage") or "").strip()
        if passage:
            return passage
    except json.JSONDecodeError:
        return None

    return None


async def _build_context_infer_questions(words: list[VocabItem], count: int) -> list[dict]:
    picked = random.sample(words, min(count, len(words)))
    ai_tasks = [asyncio.create_task(_ai_context_passage(item.word, item.meaning_zh, item.example)) for item in picked]
    ai_results = await asyncio.gather(*ai_tasks, return_exceptions=True)

    questions: list[dict] = []
    for idx, item in enumerate(picked):
        distractor_pool = [w.word for w in words if w.id != item.id]
        choices = random.sample(distractor_pool, 3) + [item.word]
        random.shuffle(choices)

        ai_candidate = ai_results[idx]
        passage = ai_candidate if isinstance(ai_candidate, str) else None
        passage = _mask_target_word(passage or _local_context_passage(item.word, item.example), item.word)
        questions.append(
            {
                "index": idx,
                "type": "context_infer_mcq",
                "vocab_item_id": item.id,
                "prompt": f"Read the paragraph and infer the target word:\n\n{passage}",
                "choices": choices,
                "correct_answer": item.word,
            }
        )
    return questions


def _upsert_answer(
    db: Session,
    *,
    user_id: int,
    session_id: int,
    row: PracticeAnswerRow,
    now: datetime,
) -> bool:
    is_correct = (row.user_answer or "").strip().lower() == row.correct_answer.strip().lower()
    existed = (
        db.query(PracticeAnswer)
        .filter(
            and_(
                PracticeAnswer.user_id == user_id,
                PracticeAnswer.session_id == session_id,
                PracticeAnswer.vocab_item_id == row.vocab_item_id,
                PracticeAnswer.question_type == row.question_type,
            )
        )
        .first()
    )
    if existed:
        existed.user_answer = row.user_answer
        existed.is_correct = is_correct
    else:
        db.add(
            PracticeAnswer(
                user_id=user_id,
                session_id=session_id,
                vocab_item_id=row.vocab_item_id,
                question_type=row.question_type,
                user_answer=row.user_answer,
                is_correct=is_correct,
            )
        )

    if not is_correct:
        item = db.query(VocabItem).filter(and_(VocabItem.id == row.vocab_item_id, VocabItem.user_id == user_id)).first()
        if item:
            item.next_review_at = now

    return is_correct


def _compute_session_result(db: Session, *, user_id: int, session: PracticeSession) -> tuple[int, int]:
    rows = (
        db.query(PracticeAnswer)
        .filter(and_(PracticeAnswer.user_id == user_id, PracticeAnswer.session_id == session.id))
        .order_by(PracticeAnswer.id.desc())
        .all()
    )
    latest_by_question: dict[tuple[int, str], PracticeAnswer] = {}
    for row in rows:
        key = (row.vocab_item_id, row.question_type)
        if key not in latest_by_question:
            latest_by_question[key] = row
    answered_count = len(latest_by_question)
    correct_count = sum(1 for row in latest_by_question.values() if row.is_correct)
    return answered_count, correct_count


def _build_explanation(item: VocabItem | None, *, question_type: str) -> str:
    if item is None:
        return "可结合语境和词性判断，再对照词义进行排除。"

    meaning = (item.meaning_zh or "").strip()
    example = (item.example or "").strip()
    parts: list[str] = []
    if meaning:
        parts.append(f"词义：{meaning}")
    if example:
        parts.append(f"例句：{example}")
    if question_type == "spelling":
        parts.append("拼写题建议：先按音节拆分再拼写，并注意常见字母组合。")
    else:
        parts.append("语境题建议：先抓句子主旨与搭配，再排除语义不匹配的干扰项。")
    return "；".join(parts)


@router.post("/generate")
async def practice_generate(body: PracticeGenerateBody, db: Session = Depends(get_db)):
    if body.mode not in {"mcq", "spelling", "context_infer"}:
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

    if body.mode == "context_infer":
        questions = await _build_context_infer_questions(words, count)
    else:
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
    wrong_items: list[int] = []
    wrong_details: list[dict] = []

    for ans in body.answers:
        is_correct = _upsert_answer(db, user_id=user.id, session_id=session.id, row=ans, now=now)
        if not is_correct:
            wrong_items.append(ans.vocab_item_id)
            item = db.query(VocabItem).filter(and_(VocabItem.id == ans.vocab_item_id, VocabItem.user_id == user.id)).first()
            wrong_details.append(
                {
                    "vocab_item_id": ans.vocab_item_id,
                    "question_type": ans.question_type,
                    "correct_answer": ans.correct_answer,
                    "explanation": _build_explanation(item, question_type=ans.question_type),
                }
            )

    answered_count, correct_count = _compute_session_result(db, user_id=user.id, session=session)
    session.correct_count = correct_count
    session.ended_at = now if answered_count >= session.total_questions else None
    db.commit()
    checkin_router.refresh_checkin_stats(db, user.id, datetime.utcnow())

    return {
        "success": True,
        "data": {
            "session_id": session.id,
            "total": session.total_questions,
            "answered_count": answered_count,
            "correct_count": correct_count,
            "wrong_count": answered_count - correct_count,
            "wrong_items": wrong_items,
            "wrong_details": wrong_details,
        },
    }


@router.post("/submit-one")
def practice_submit_one(body: PracticeSubmitOneBody, db: Session = Depends(get_db)):
    user = get_or_create_user(db, body.user_email)
    session = db.query(PracticeSession).filter(and_(PracticeSession.id == body.session_id, PracticeSession.user_id == user.id)).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Practice session not found")

    now = datetime.utcnow()
    is_correct = _upsert_answer(db, user_id=user.id, session_id=session.id, row=body.answer, now=now)
    item = db.query(VocabItem).filter(and_(VocabItem.id == body.answer.vocab_item_id, VocabItem.user_id == user.id)).first()
    explanation = _build_explanation(item, question_type=body.answer.question_type)
    answered_count, correct_count = _compute_session_result(db, user_id=user.id, session=session)
    session.correct_count = correct_count
    session.ended_at = now if answered_count >= session.total_questions else None
    db.commit()
    checkin_router.refresh_checkin_stats(db, user.id, datetime.utcnow())

    return {
        "success": True,
        "data": {
            "session_id": session.id,
            "is_correct": is_correct,
            "correct_answer": body.answer.correct_answer,
            "explanation": explanation,
            "total_questions": session.total_questions,
            "answered_count": answered_count,
            "correct_count": correct_count,
            "wrong_count": answered_count - correct_count,
        },
    }
