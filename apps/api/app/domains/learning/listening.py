import random
import re
import json
import asyncio
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

router = APIRouter(prefix="/api/listening", tags=["listening"])


class ListeningGenerateBody(BaseModel):
    mode: str = "listen_mcq"
    count: int = 10
    user_email: str = "local@ai-vocab-agent.dev"


class ListeningAnswerRow(BaseModel):
    vocab_item_id: int
    question_type: str
    user_answer: str | None = None
    correct_answer: str


class ListeningSubmitBody(BaseModel):
    session_id: int
    answers: list[ListeningAnswerRow]
    user_email: str = "local@ai-vocab-agent.dev"


def _build_fill_prompt(example: str | None, word: str) -> tuple[str, str]:
    if example and word:
        pattern = re.compile(rf"\b{re.escape(word)}\b", flags=re.IGNORECASE)
        if pattern.search(example):
            return pattern.sub("____", example, count=1), example
    return "Listen and type the word you hear.", word


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
        lead = "The speaker introduces a term students often meet in class discussions."
    follow = "From the context, listeners should infer the missing academic term."
    return f"{lead} {follow}"


async def _ai_context_passage(target_word: str, meaning_zh: str | None, example: str | None) -> str | None:
    cfg = load_ai_config()
    # No key configured: skip remote generation and use local fallback immediately.
    if not (cfg.get("api_key") or "").strip():
        return None
    messages = [
        {
            "role": "system",
            "content": (
                "You are an English listening item writer. "
                "Return strict JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                "Generate 2-4 natural English sentences for a college listening question. "
                "The passage must center on target word "
                f"'{target_word}', but NEVER include this exact word in the passage text. "
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


async def _build_passage_questions(
    learned_words: list[VocabItem], passage_count: int
) -> list[dict]:
    questions: list[dict] = []
    picked = random.sample(learned_words, min(passage_count, len(learned_words)))
    ai_tasks = [asyncio.create_task(_ai_context_passage(item.word, item.meaning_zh, item.example)) for item in picked]
    ai_results = await asyncio.gather(*ai_tasks, return_exceptions=True)
    for idx, target in enumerate(picked):
        distractor_pool = [w.word for w in learned_words if w.id != target.id]
        choices = random.sample(distractor_pool, 3) + [target.word]
        random.shuffle(choices)

        ai_candidate = ai_results[idx]
        ai_passage = ai_candidate if isinstance(ai_candidate, str) else None
        listen_text = ai_passage or _local_context_passage(target.word, target.example)
        listen_text = _mask_target_word(listen_text, target.word)
        questions.append(
            {
                "index": idx,
                "type": "listen_passage_context_mcq",
                "vocab_item_id": target.id,
                "prompt": "Listen to the short passage. Which word best matches the context?",
                "listen_text": listen_text,
                "choices": choices,
                "correct_answer": target.word,
            }
        )
    return questions


@router.post("/generate")
async def listening_generate(body: ListeningGenerateBody, db: Session = Depends(get_db)):
    if body.mode not in {"listen_mcq", "listen_fill", "listen_passage"}:
        raise HTTPException(status_code=400, detail="Invalid mode")

    user = get_or_create_user(db, body.user_email)
    setting = get_or_create_user_settings(db, body.user_email)

    base_filters = [VocabItem.user_id == user.id, VocabItem.status != "new"]
    if setting.current_book_tag:
        base_filters.append(VocabItem.tags == setting.current_book_tag)

    learned_words = db.query(VocabItem).filter(and_(*base_filters)).all()
    if len(learned_words) < 4:
        raise HTTPException(status_code=400, detail="Need at least 4 learned words")

    questions = []
    if body.mode == "listen_passage":
        passage_count = max(1, min(body.count, 10))
        questions = await _build_passage_questions(learned_words, passage_count)
    else:
        count = max(1, min(body.count, 50))
        picked = random.sample(learned_words, min(count, len(learned_words)))
        for idx, item in enumerate(picked):
            if body.mode == "listen_fill":
                prompt, listen_text = _build_fill_prompt(item.example, item.word)
                questions.append(
                    {
                        "index": idx,
                        "type": "listen_fill",
                        "vocab_item_id": item.id,
                        "prompt": prompt,
                        "listen_text": listen_text,
                        "correct_answer": item.word,
                    }
                )
                continue

            distractor_pool = [w.word for w in learned_words if w.id != item.id]
            choices = random.sample(distractor_pool, 3) + [item.word]
            random.shuffle(choices)
            questions.append(
                {
                    "index": idx,
                    "type": "listen_mcq",
                    "vocab_item_id": item.id,
                    "prompt": "Listen and choose the word you hear.",
                    "listen_text": item.word,
                    "choices": choices,
                    "correct_answer": item.word,
                }
            )

    session = PracticeSession(
        user_id=user.id,
        mode=body.mode,
        session_type="listening",
        total_questions=len(questions),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {"success": True, "data": {"session_id": session.id, "questions": questions}}


@router.post("/submit")
def listening_submit(body: ListeningSubmitBody, db: Session = Depends(get_db)):
    user = get_or_create_user(db, body.user_email)
    session = (
        db.query(PracticeSession)
        .filter(and_(PracticeSession.id == body.session_id, PracticeSession.user_id == user.id))
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Listening session not found")

    now = datetime.utcnow()
    correct = 0
    wrong_items: list[int] = []

    for ans in body.answers:
        is_correct = (ans.user_answer or "").strip().lower() == ans.correct_answer.strip().lower()
        if is_correct:
            correct += 1
        else:
            wrong_items.append(ans.vocab_item_id)
            item = (
                db.query(VocabItem)
                .filter(and_(VocabItem.id == ans.vocab_item_id, VocabItem.user_id == user.id))
                .first()
            )
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
