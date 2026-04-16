from datetime import datetime
import json
import os
from pathlib import Path

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from .models import ReviewLog, User, UserSetting, VocabItem

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


def get_or_create_user_settings(db: Session, email: str = DEFAULT_EMAIL) -> UserSetting:
    user = get_or_create_user(db, email)
    setting = db.query(UserSetting).filter(UserSetting.user_id == user.id).first()
    if setting:
        return setting
    setting = UserSetting(user_id=user.id, daily_new_words=20, daily_review_limit=50)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def get_user_books(db: Session, user_id: int) -> list[dict]:
    results = (
        db.query(VocabItem.tags, func.count(VocabItem.id))
        .filter(VocabItem.user_id == user_id, VocabItem.tags.isnot(None))
        .group_by(VocabItem.tags)
        .all()
    )
    return [{"tag": tag, "count": count} for tag, count in results]


def import_json_lines(db: Session, file_paths: list[str], email: str = DEFAULT_EMAIL) -> dict:
    user = get_or_create_user(db, email)
    imported = 0
    skipped = 0

    # 获取当前用户的最大 study_order，新词从下一个序号开始
    max_order_row = (
        db.query(VocabItem)
        .filter(VocabItem.user_id == user.id)
        .order_by(VocabItem.study_order.desc())
        .first()
    )
    current_order = (max_order_row.study_order if max_order_row else 0) + 1

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
                      status="new",
                      mastery=0,
                      study_order=current_order,
                      next_review_at=None,
                  )
                  db.add(item)
                  current_order += 1
              else:
                  item.phonetic = phonetic or item.phonetic
                  item.meaning_zh = meaning_zh or item.meaning_zh
                  item.example = example or item.example
                  item.tags = source_tag
              imported += 1

    db.commit()
    unique_count = db.query(VocabItem).filter(VocabItem.user_id == user.id).count()
    return {"imported": imported, "skipped": skipped, "unique": unique_count}
