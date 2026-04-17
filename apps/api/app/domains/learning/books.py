from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["system"])

PROJECT_ROOT = Path(__file__).resolve().parents[5]
DATA_DIR = PROJECT_ROOT / "data"


@router.get("/books")
def list_books():
    excluded = {"ai_config.json"}
    files = sorted([f.name for f in DATA_DIR.glob("*.json") if f.is_file() and f.name not in excluded])
    return {"success": True, "data": files}

