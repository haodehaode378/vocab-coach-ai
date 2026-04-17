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
    messages: list[dict]
    stream: bool = False
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
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


@router.post("/chat")
async def ai_chat(body: ChatBody, db: Session = Depends(get_db)):
    user = get_or_create_user(db, body.user_email)
    for m in body.messages:
        if m.get("role") in ("user", "assistant"):
            db.add(AIChatMessage(user_id=user.id, role=m["role"], content=m.get("content", "")))
    db.commit()

    if body.stream:
        async def event_generator():
            async for chunk in chat_stream(
                messages=body.messages,
                model=body.model,
                base_url=body.base_url,
                api_key=body.api_key,
            ):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    content = await chat_complete(
        messages=body.messages,
        model=body.model,
        base_url=body.base_url,
        api_key=body.api_key,
    )
    db.add(AIChatMessage(user_id=user.id, role="assistant", content=content))
    db.commit()
    return {"success": True, "data": {"content": content}}


@router.post("/generate-memory-tip")
async def generate_memory_tip(body: MemoryTipBody, db: Session = Depends(get_db)):
    user = get_or_create_user(db, body.user_email)
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
    user = get_or_create_user(db, body.user_email)
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

