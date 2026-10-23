"""Start the User Support Assistant service.

Run from the repo root:  python main.py
Then open the API docs:  http://127.0.0.1:8000/docs

The application code is in src/ (the FastAPI app is src/app.py). Host, port and
auto-reload come from src/core/config.py (HOST, PORT, RELOAD in dev.env).
"""

import sys
from pathlib import Path

import uvicorn

SRC_DIR = Path(__file__).resolve().parent / "src"

# Let Python find the modules in src/ (config, app, api, kb_develop, ...).
sys.path.insert(0, str(SRC_DIR))

from core import config  # noqa: E402  (needs src/ on the path first)

if __name__ == "__main__":
    uvicorn.run("app:app", app_dir=str(SRC_DIR), host=config.HOST, port=config.PORT, reload=config.RELOAD)
