import json
import os
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parents[3] / "data" / "ai_config.json"


def _ensure_file():
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text("{}", encoding="utf-8")


def load_ai_config() -> dict:
    _ensure_file()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        data = {}
    return {
        "base_url": data.get("base_url") or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        "api_key": data.get("api_key") or os.getenv("LLM_API_KEY", ""),
        "model": data.get("model") or os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
    }


def save_ai_config(base_url: str | None, api_key: str | None, model: str | None) -> dict:
    _ensure_file()
    cfg = load_ai_config()
    if base_url is not None:
        cfg["base_url"] = base_url
    if api_key is not None:
        cfg["api_key"] = api_key
    if model is not None:
        cfg["model"] = model
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return cfg


def get_public_ai_config() -> dict:
    cfg = load_ai_config()
    return {
        "base_url": cfg["base_url"],
        "model": cfg["model"],
    }

