from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Base, SessionLocal, engine
from app.services import import_json_lines


def main() -> None:
    Base.metadata.create_all(bind=engine)

    args = sys.argv[1:] or ["CET4luan_2.json", "CET6_1.json"]
    paths = [str((ROOT / a).resolve()) for a in args]

    db = SessionLocal()
    try:
        result = import_json_lines(db, paths)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
