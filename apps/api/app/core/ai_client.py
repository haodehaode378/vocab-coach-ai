import os
from typing import AsyncIterable

from openai import AsyncOpenAI

from app.core.config_store import load_ai_config

DEFAULT_MODEL = "gpt-3.5-turbo"


def get_ai_client(base_url: str | None = None, api_key: str | None = None) -> AsyncOpenAI:
    cfg = load_ai_config()
    url = base_url or cfg.get("base_url") or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    key = api_key or cfg.get("api_key") or os.getenv("LLM_API_KEY", "")
    return AsyncOpenAI(base_url=url, api_key=key)


async def chat_stream(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    base_url: str | None = None,
    api_key: str | None = None,
) -> AsyncIterable[str]:
    client = get_ai_client(base_url, api_key)
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content or "" if chunk.choices else ""
            if delta:
                yield delta
    except Exception as e:
        yield f"\n[AI 请求出错: {e}]"


async def chat_complete(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    base_url: str | None = None,
    api_key: str | None = None,
) -> str:
    client = get_ai_client(base_url, api_key)
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        return f"[AI 请求出错: {e}]"

