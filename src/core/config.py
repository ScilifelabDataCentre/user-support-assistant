"""Project settings, read from environment variables.

Locally they are loaded from dev.env at the repo root (or the file named by ENV_FILE).
In deployment, set them as real environment variables; those take precedence over the file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(os.getenv("ENV_FILE", ROOT / "dev.env"))

# LLM / embedding API (OpenAI-compatible)
OPENLLM_API_KEY = os.getenv("OPENLLM_API_KEY")
OPENLLM_BASE_URL = os.getenv("OPENLLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
# Most requests one process sends to the LLM / embedding API at the same time while
# answering questions; more wait in the process, so the API is not overloaded
OPENLLM_MAX_CONCURRENCY = int(os.getenv("OPENLLM_MAX_CONCURRENCY", "20"))
# Log the full prompt sent to the LLM; set SHOW_PROMPT=true in dev.env for debugging
SHOW_PROMPT = os.getenv("SHOW_PROMPT", "false").lower() == "true"

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
# Collection that holds the knowledge base chunks
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")

# Web server (used by main.py at the repo root)
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
# Restart the server when code changes; set RELOAD=true in dev.env for development
RELOAD = os.getenv("RELOAD", "false").lower() == "true"
# Serve the Gradio demo page at /demo (see src/demo/gradio_app.py); set ENABLE_DEMO=false to turn it off
ENABLE_DEMO = os.getenv("ENABLE_DEMO", "true").lower() == "true"


def require(*names):
    """Raise if any of the named settings is not set, e.g. require("OPENLLM_API_KEY")."""
    missing = []
    for name in names:
        if not globals().get(name):
            missing.append(name)
    if missing:
        raise RuntimeError(f"missing settings: {', '.join(missing)} (set them in dev.env or the environment)")
