from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import VocabItem
from app.core.services import get_or_create_user, import_json_lines

router = APIRouter(prefix="/api/vocab", tags=["vocab"])

PROJECT_ROOT = Path(__file__).resolve().parents[5]


class ImportBody(BaseModel):
    files: list[str] = Field(default_factory=lambda: ["data/CET4luan_2.json", "data/CET6_1.json"])
    user_email: str = "local@ai-vocab-agent.dev"


@router.post("/import-json-files")
def import_vocab(body: ImportBody, db: Session = Depends(get_db)):
    files: list[str] = []
    for f in body.files:
        if Path(f).is_absolute():
            files.append(f)
            continue
        primary = (PROJECT_ROOT / f).resolve()
        if primary.exists():
            files.append(str(primary))
            continue
        # Backward compatibility: old clients may pass bare file names like CET4luan_2.json.
        fallback = (PROJECT_ROOT / "data" / f).resolve()
        files.append(str(fallback))
    result = import_json_lines(db, files, body.user_email)
    return {"success": True, "data": result}


@router.get("/list")
def list_vocab(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    book_tag: str = "",
    user_email: str = "local@ai-vocab-agent.dev",
    db: Session = Depends(get_db),
):
    user = get_or_create_user(db, user_email)
    query = db.query(VocabItem).filter(VocabItem.user_id == user.id)
    if book_tag.strip():
        query = query.filter(VocabItem.tags == book_tag.strip())
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

