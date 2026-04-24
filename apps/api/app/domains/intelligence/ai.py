import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.ai_client import chat_complete, chat_stream
from app.core.database import get_db
from app.core.models import AIChatMessage
from app.core.services import get_or_create_user

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatBody(BaseModel):
    messages: list[dict] = []
    stream: bool = False
    use_history: bool = True
    history_limit: int = 20
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    user_email: str = "local@ai-vocab-agent.dev"


class ChatClearBody(BaseModel):
    user_email: str = "local@ai-vocab-agent.dev"


class MemoryTipBody(BaseModel):
    word: str
    meaning_zh: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    user_email: str = "local@ai-vocab-agent.dev"


class DailyMotivationBody(BaseModel):
    stats_context: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    user_email: str = "local@ai-vocab-agent.dev"


def _normalize_messages(raw_messages: list[dict]) -> list[dict]:
    messages: list[dict] = []
    for m in raw_messages:
        role = (m.get("role") or "").strip()
        content = (m.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    return messages


def _fetch_history_messages(db: Session, user_id: int, limit: int) -> list[dict]:
    safe_limit = max(1, min(limit, 100))
    rows = (
        db.query(AIChatMessage)
        .filter(AIChatMessage.user_id == user_id)
        .order_by(AIChatMessage.created_at.desc(), AIChatMessage.id.desc())
        .limit(safe_limit)
        .all()
    )
    rows.reverse()
    return [{"role": row.role, "content": row.content} for row in rows if row.role in ("user", "assistant")]


@router.get("/chat/history")
def chat_history(limit: int = 50, user_email: str = "local@ai-vocab-agent.dev", db: Session = Depends(get_db)):
    user = get_or_create_user(db, user_email)
    safe_limit = max(1, min(limit, 200))
    rows = (
        db.query(AIChatMessage)
        .filter(AIChatMessage.user_id == user.id)
        .order_by(AIChatMessage.created_at.desc(), AIChatMessage.id.desc())
        .limit(safe_limit)
        .all()
    )
    rows.reverse()
    return {
        "success": True,
        "data": {
            "messages": [
                {"role": row.role, "content": row.content, "created_at": row.created_at.isoformat()}
                for row in rows
                if row.role in ("user", "assistant")
            ]
        },
    }


@router.post("/chat/clear")
def chat_clear(body: ChatClearBody, db: Session = Depends(get_db)):
    user = get_or_create_user(db, body.user_email)
    db.query(AIChatMessage).filter(AIChatMessage.user_id == user.id).delete()
    db.commit()
    return {"success": True, "data": {"cleared": True}}


@router.post("/chat")
async def ai_chat(body: ChatBody, db: Session = Depends(get_db)):
    user = get_or_create_user(db, body.user_email)
    incoming = _normalize_messages(body.messages)
    history = _fetch_history_messages(db, user.id, body.history_limit) if body.use_history else []
    llm_messages = history + incoming
    if not llm_messages:
        raise HTTPException(status_code=400, detail="No valid chat messages")

    latest_user = next((m for m in reversed(incoming) if m["role"] == "user"), None)
    if latest_user:
        db.add(AIChatMessage(user_id=user.id, role="user", content=latest_user["content"]))
        db.commit()

    if body.stream:

        async def event_generator():
            assistant_chunks: list[str] = []
            async for chunk in chat_stream(
                messages=llm_messages,
                model=body.model,
                base_url=body.base_url,
                api_key=body.api_key,
            ):
                assistant_chunks.append(chunk)
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            assistant_text = "".join(assistant_chunks).strip()
            if assistant_text:
                db.add(AIChatMessage(user_id=user.id, role="assistant", content=assistant_text))
                db.commit()
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    content = await chat_complete(
        messages=llm_messages,
        model=body.model,
        base_url=body.base_url,
        api_key=body.api_key,
    )
    db.add(AIChatMessage(user_id=user.id, role="assistant", content=content))
    db.commit()
    return {"success": True, "data": {"content": content}}


@router.post("/generate-memory-tip")
async def generate_memory_tip(body: MemoryTipBody, db: Session = Depends(get_db)):
    get_or_create_user(db, body.user_email)
    prompt = (
        f"请为单词 '{body.word}' 生成一个有趣的中文记忆技巧或联想口诀，"
        f"帮助学习者记住它。单词释义：{body.meaning_zh or '暂无'}。"
        "要求：简短、形象、不超过 80 字。"
    )
    content = await chat_complete(
        messages=[{"role": "user", "content": prompt}],
        model=body.model,
        base_url=body.base_url,
        api_key=body.api_key,
    )
    return {"success": True, "data": {"word": body.word, "tip": content}}


@router.post("/daily-motivation")
async def daily_motivation(body: DailyMotivationBody, db: Session = Depends(get_db)):
    get_or_create_user(db, body.user_email)
    ctx = body.stats_context or "今天也是努力学习的一天"
    prompt = (
        f"你是一位温暖的 AI 学习教练。根据以下学习数据，写一句 30 字以内的鼓励语：\n{ctx}\n"
        "要求：积极、真诚、有感染力。"
    )
    content = await chat_complete(
        messages=[{"role": "user", "content": prompt}],
        model=body.model,
        base_url=body.base_url,
        api_key=body.api_key,
    )
    return {"success": True, "data": {"message": content}}
