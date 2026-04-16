from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PracticeSession, ReviewLog, UserSetting, VocabItem
from app.services import get_or_create_user, get_or_create_user_settings
from app.sm2 import SrsState
from app.study_engine import evaluate_word

router = APIRouter(prefix="/api/study", tags=["study"])


class SettingsBody(BaseModel):
    daily_new_words: int = 20
    daily_review_limit: int = 50
    user_email: str = "local@ai-vocab-agent.dev"


class GradeBody(BaseModel):
    vocab_item_id: int
    response: str  # know, vague, forget
    session_type: str = "learn"  # learn, review, test
    user_email: str = "local@ai-vocab-agent.dev"


class TestGenerateBody(BaseModel):
    count: int = 10
    user_email: str = "local@ai-vocab-agent.dev"


@router.get("/settings")
def get_settings(user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    setting = get_or_create_user_settings(db, user_email)
    return {
        "success": True,
        "data": {
            "daily_new_words": setting.daily_new_words,
            "daily_review_limit": setting.daily_review_limit,
        },
    }


@router.post("/settings")
def update_settings(body: SettingsBody, db: Session = Depends(get_db)):
    setting = get_or_create_user_settings(db, body.user_email)
    setting.daily_new_words = max(1, min(body.daily_new_words, 200))
    setting.daily_review_limit = max(1, min(body.daily_review_limit, 500))
    db.commit()
    return {
        "success": True,
        "data": {
            "daily_new_words": setting.daily_new_words,
            "daily_review_limit": setting.daily_review_limit,
        },
    }


def _item_to_dict(item: VocabItem, is_new: bool) -> dict:
    return {
        "id": item.id,
        "word": item.word,
        "phonetic": item.phonetic,
        "meaning_zh": item.meaning_zh,
        "example": item.example,
        "status": item.status,
        "mastery": item.mastery,
        "is_new": is_new,
    }


@router.get("/today")
def get_today_queue(user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_email)
    setting = get_or_create_user_settings(db, user_email)
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    # 1. 即时复习词：1 小时内刚被 grade 为 vague/forget 且已到期的
    urgent_items = (
        db.query(VocabItem)
        .filter(
            and_(
                VocabItem.user_id == user.id,
                VocabItem.status != "new",
                or_(VocabItem.next_review_at.is_(None), VocabItem.next_review_at <= now),
                VocabItem.last_graded_at >= one_hour_ago,
            )
        )
        .order_by(VocabItem.next_review_at.asc())
        .limit(setting.daily_review_limit)
        .all()
    )

    # 2. 普通复习词（排除已放入 urgent 的）
    urgent_ids = {i.id for i in urgent_items}
    normal_review = (
        db.query(VocabItem)
        .filter(
            and_(
                VocabItem.user_id == user.id,
                VocabItem.status != "new",
                or_(VocabItem.next_review_at.is_(None), VocabItem.next_review_at <= now),
                ~VocabItem.id.in_(urgent_ids),
            )
        )
        .order_by(VocabItem.next_review_at.asc().nullsfirst(), VocabItem.mastery.asc())
        .limit(setting.daily_review_limit)
        .all()
    )

    # 3. 新词
    new_limit = max(0, setting.daily_new_words)
    new_items = (
        db.query(VocabItem)
        .filter(and_(VocabItem.user_id == user.id, VocabItem.status == "new"))
        .order_by(VocabItem.study_order.asc())
        .limit(new_limit)
        .all()
    )

    # 4. 交错混合：urgent -> 复习/新词 2:1 交错 -> 剩余
    queue = [_item_to_dict(i, False) for i in urgent_items]
    mixed = []
    r_idx, n_idx = 0, 0
    while r_idx < len(normal_review) or n_idx < len(new_items):
        # 每 2 个复习词插 1 个新词
        for _ in range(2):
            if r_idx < len(normal_review):
                mixed.append(_item_to_dict(normal_review[r_idx], False))
                r_idx += 1
        if n_idx < len(new_items):
            mixed.append(_item_to_dict(new_items[n_idx], True))
            n_idx += 1
    # 把剩余新词或复习词追加
    while r_idx < len(normal_review):
        mixed.append(_item_to_dict(normal_review[r_idx], False))
        r_idx += 1
    while n_idx < len(new_items):
        mixed.append(_item_to_dict(new_items[n_idx], True))
        n_idx += 1

    queue.extend(mixed)

    return {
        "success": True,
        "data": {
            "queue": queue,
            "urgent_count": len(urgent_items),
            "review_count": len(normal_review),
            "new_count": len(new_items),
        },
    }


@router.post("/grade")
def grade_word(body: GradeBody, db: Session = Depends(get_db)):
    if body.response not in {"know", "vague", "forget"}:
        raise HTTPException(status_code=400, detail="Invalid response")

    user = get_or_create_user(db, body.user_email)
    item = db.query(VocabItem).filter(
        and_(VocabItem.id == body.vocab_item_id, VocabItem.user_id == user.id)
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Vocab item not found")

    now = datetime.utcnow()
    result = evaluate_word(
        old_mastery=item.mastery,
        old_status=item.status,
        response=body.response,
        state=SrsState(ease_factor=item.ease_factor, interval_days=item.interval_days, repetitions=item.repetitions),
        now=now,
    )

    # 记录 ReviewLog（兼容旧表）
    db.add(
        ReviewLog(
            user_id=user.id,
            vocab_item_id=item.id,
            grade=body.response,
            old_interval=item.interval_days,
            new_interval=result["interval_days"],
            reviewed_at=now,
        )
    )

    # 首次学习记录时间
    if item.status == "new" and body.response != "forget":
        item.new_learned_at = now

    item.status = result["status"]
    item.mastery = result["mastery"]
    item.ease_factor = result["ease_factor"]
    item.interval_days = result["interval_days"]
    item.repetitions = result["repetitions"]
    item.next_review_at = result["next_review_at"]
    item.last_graded_at = now
    db.commit()

    return {"success": True, "data": result}


@router.post("/test/generate")
def generate_daily_test(body: TestGenerateBody, db: Session = Depends(get_db)):
    import random

    user = get_or_create_user(db, body.user_email)
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)

    # 候选池 1：今天新学的单词
    today_new = (
        db.query(VocabItem)
        .filter(
            and_(
                VocabItem.user_id == user.id,
                VocabItem.new_learned_at >= today_start,
            )
        )
        .all()
    )

    # 候选池 2：近 7 天易错题（mastery < 50 或最近被 forget/vague 的）
    week_ago = now - timedelta(days=7)
    weak_words = (
        db.query(VocabItem)
        .filter(
            and_(
                VocabItem.user_id == user.id,
                VocabItem.status != "new",
                VocabItem.mastery < 60,
                VocabItem.last_graded_at >= week_ago,
            )
        )
        .limit(30)
        .all()
    )

    pool = list({w.id: w for w in (today_new + weak_words)}.values())
    if len(pool) < 4:
        # 补充任意已学单词
        extra = (
            db.query(VocabItem)
            .filter(and_(VocabItem.user_id == user.id, VocabItem.status != "new"))
            .limit(20)
            .all()
        )
        pool = list({w.id: w for w in (pool + extra)}.values())

    count = max(1, min(body.count, 50, len(pool)))
    picked = random.sample(pool, count)

    questions = []
    all_words = db.query(VocabItem).filter(VocabItem.user_id == user.id).all()
    for idx, w in enumerate(picked):
        distractors = [x.word for x in all_words if x.id != w.id and x.word != w.word]
        choices = random.sample(distractors, min(3, len(distractors))) + [w.word]
        random.shuffle(choices)
        questions.append({
            "index": idx,
            "type": "mcq",
            "vocab_item_id": w.id,
            "prompt": w.meaning_zh or w.example or w.word,
            "choices": choices,
            "correct_answer": w.word,
        })

    session = PracticeSession(
        user_id=user.id,
        mode="mcq",
        session_type="daily_test",
        total_questions=len(questions),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {"success": True, "data": {"session_id": session.id, "questions": questions}}


@router.get("/stats/progress")
def get_progress(user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_email)

    total = db.query(VocabItem).filter(VocabItem.user_id == user.id).count()
    new_count = db.query(VocabItem).filter(and_(VocabItem.user_id == user.id, VocabItem.status == "new")).count()
    learning_count = db.query(VocabItem).filter(and_(VocabItem.user_id == user.id, VocabItem.status == "learning")).count()
    mastered_count = db.query(VocabItem).filter(and_(VocabItem.user_id == user.id, VocabItem.status == "mastered")).count()
    familiar_count = db.query(VocabItem).filter(and_(VocabItem.user_id == user.id, VocabItem.status == "familiar")).count()

    # 熟练度分布
    mastery_dist = {
        "0-20": 0,
        "21-40": 0,
        "41-60": 0,
        "61-80": 0,
        "81-100": 0,
    }
    items = db.query(VocabItem.mastery).filter(VocabItem.user_id == user.id).all()
    for (m,) in items:
        if m <= 20:
            mastery_dist["0-20"] += 1
        elif m <= 40:
            mastery_dist["21-40"] += 1
        elif m <= 60:
            mastery_dist["41-60"] += 1
        elif m <= 80:
            mastery_dist["61-80"] += 1
        else:
            mastery_dist["81-100"] += 1

    return {
        "success": True,
        "data": {
            "total": total,
            "new": new_count,
            "learning": learning_count,
            "mastered": mastered_count,
            "familiar": familiar_count,
            "mastery_distribution": mastery_dist,
        },
    }
