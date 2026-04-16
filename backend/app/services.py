from datetime import datetime
import json
import os
from pathlib import Path

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from .models import ReviewLog, User, VocabItem

DEFAULT_EMAIL = "local@ai-vocab-agent.dev"


def get_or_create_user(db: Session, email: str = DEFAULT_EMAIL) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(email=email, name="Local User")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def import_json_lines(db: Session, file_paths: list[str], email: str = DEFAULT_EMAIL) -> dict:
    user = get_or_create_user(db, email)
    imported = 0
    skipped = 0

    for fp in file_paths:
      path = Path(fp)
      if not path.exists():
          skipped += 1
          continue

      source_tag = path.stem
      with path.open("r", encoding="utf-8") as f:
          for line in f:
              line = line.strip()
              if not line:
                  continue
              try:
                  obj = json.loads(line)
              except json.JSONDecodeError:
                  skipped += 1
                  continue

              word = (obj.get("headWord") or "").strip()
              if not word:
                  skipped += 1
                  continue

              content = ((obj.get("content") or {}).get("word") or {}).get("content") or {}
              phonetic = content.get("usphone") or content.get("ukphone")

              trans = content.get("trans") or []
              meaning_zh = trans[0].get("tranCn") if trans else None

              sentences = (content.get("sentence") or {}).get("sentences") or []
              example = sentences[0].get("sContent") if sentences else None

              item = (
                  db.query(VocabItem)
                  .filter(and_(VocabItem.user_id == user.id, func.lower(VocabItem.word) == word.lower()))
                  .first()
              )

              if item is None:
                  item = VocabItem(
                      user_id=user.id,
                      word=word,
                      phonetic=phonetic,
                      meaning_zh=meaning_zh,
                      example=example,
                      tags=source_tag,
                      next_review_at=datetime.utcnow(),
                  )
                  db.add(item)
              else:
                  item.phonetic = phonetic or item.phonetic
                  item.meaning_zh = meaning_zh or item.meaning_zh
                  item.example = example or item.example
                  item.tags = source_tag
              imported += 1

    db.commit()
    unique_count = db.query(VocabItem).filter(VocabItem.user_id == user.id).count()
    return {"imported": imported, "skipped": skipped, "unique": unique_count}
