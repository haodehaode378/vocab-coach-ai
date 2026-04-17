from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.learning.study import GradeBody as StudyGradeBody, get_today_queue, grade_word

router = APIRouter(prefix="/api/review", tags=["review"])


class ReviewBody(BaseModel):
    vocab_item_id: int
    grade: str
    user_email: str = "local@ai-vocab-agent.dev"


def _grade_map(old_grade: str) -> str:
    mapping = {"again": "forget", "hard": "vague", "good": "know", "easy": "know"}
    return mapping.get(old_grade, "forget")


@router.get("/today")
def review_today(
    limit: int = 50,
    user_email: str = "local@ai-vocab-agent.dev",
    db: Session = Depends(get_db),
):
    _ = limit
    # 兼容旧接口：内部委托到 /api/study/today
    return get_today_queue(user_email=user_email, db=db)


@router.post("/grade")
def review_grade(body: ReviewBody, db: Session = Depends(get_db)):
    # 兼容旧接口：内部委托到 /api/study/grade
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

