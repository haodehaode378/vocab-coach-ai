from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config_store import get_public_ai_config, save_ai_config

router = APIRouter(prefix="/api/system", tags=["system"])


class AIConfigBody(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None


@router.get("/ai-config")
def get_ai_config():
    return {"success": True, "data": get_public_ai_config()}


@router.post("/ai-config")
def set_ai_config(body: AIConfigBody):
    save_ai_config(base_url=body.base_url, api_key=body.api_key, model=body.model)
    return {"success": True, "data": get_public_ai_config()}

