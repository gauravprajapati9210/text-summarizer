"""Compatibility entry point for the canonical FastAPI application.

The maintained implementation lives in ``backend/main.py``. This wrapper
keeps ``python app.py`` working without maintaining a second API.
"""

from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from main import app  # noqa: E402


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
