from datetime import datetime
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = Path(__file__).resolve().parents[1]
for p in (PROJECT_ROOT, API_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.core.database import Base, engine, run_migrations
from app.domains.intelligence import ai
from app.domains.learning import books, practice, review, stats, study, vocab
from app.domains.productivity import checkin, focus, tasks
from app.domains.system import system

STATIC_DIR = PROJECT_ROOT / "apps" / "web" / "dist"

Base.metadata.create_all(bind=engine)
run_migrations()

app = FastAPI(title="AI Vocab Agent Python", version="1.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core health endpoint
@app.get("/healthz")
def healthz():
    return {"ok": True, "time": datetime.utcnow().isoformat()}

# Business modules
app.include_router(vocab.router)
app.include_router(review.router)
app.include_router(practice.router)
app.include_router(stats.router)
app.include_router(books.router)

# Existing domain routers
app.include_router(focus.router)
app.include_router(tasks.router)
app.include_router(checkin.router)
app.include_router(ai.router)
app.include_router(system.router)
app.include_router(study.router)

# Frontend static files
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=False)

