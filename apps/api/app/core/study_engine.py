from datetime import datetime, timedelta

from app.core.sm2 import SrsState, apply_sm2


def map_response_to_grade(response: str) -> str:
    """将三档反馈映射到 SM-2 四档"""
    mapping = {
        "know": "good",
        "vague": "hard",
        "forget": "again",
    }
    return mapping.get(response, "again")


def update_mastery(old_mastery: int, response: str, interval_days: int, repetitions: int) -> int:
    if response == "know":
        # 间隔越长、次数越多，加分越多，但封顶
        delta = min(30, 10 + interval_days * 2 + repetitions)
    elif response == "vague":
        delta = -5 if old_mastery < 30 else -10
    else:  # forget
        delta = -15 if old_mastery < 50 else -20
    return max(0, min(100, old_mastery + delta))


def update_status(old_status: str, mastery: int, interval_days: int, repetitions: int) -> str:
    if mastery >= 90 and repetitions >= 4 and interval_days >= 14:
        return "familiar"
    if mastery >= 60 and repetitions >= 3 and interval_days >= 6:
        return "mastered"
    return "learning"


def compute_next_review_at(
    response: str,
    state: SrsState,
    now: datetime | None = None,
) -> datetime:
    """根据反馈计算下次复习时间"""
    now = now or datetime.utcnow()
    grade = map_response_to_grade(response)
    next_state = apply_sm2(state, grade)

    if response == "forget":
        # 5 分钟后即时复习，同时 SM-2 间隔重置为 1 天作为兜底
        return now + timedelta(minutes=5)
    elif response == "vague":
        # 10 分钟后即时复习
        return now + timedelta(minutes=10)
    else:
        # know：按 SM-2 间隔推进
        return now + timedelta(days=next_state.interval_days)


def evaluate_word(
    old_mastery: int,
    old_status: str,
    response: str,
    state: SrsState,
    now: datetime | None = None,
) -> dict:
    """综合计算一次评分后的所有状态变更"""
    grade = map_response_to_grade(response)
    next_state = apply_sm2(state, grade)
    new_mastery = update_mastery(old_mastery, response, state.interval_days, state.repetitions)
    new_status = update_status(old_status, new_mastery, next_state.interval_days, next_state.repetitions)
    next_review_at = compute_next_review_at(response, state, now)

    return {
        "mastery": new_mastery,
        "status": new_status,
        "ease_factor": next_state.ease_factor,
        "interval_days": next_state.interval_days,
        "repetitions": next_state.repetitions,
        "next_review_at": next_review_at,
    }

