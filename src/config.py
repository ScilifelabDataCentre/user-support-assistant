"""Project settings, read from environment variables.

Locally they are loaded from dev.env at the repo root (or the file named by ENV_FILE).
In deployment, set them as real environment variables; those take precedence over the file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(os.getenv("ENV_FILE", ROOT / "dev.env"))

# LLM / embedding API (OpenAI-compatible)
OPENLLM_API_KEY = os.getenv("OPENLLM_API_KEY")
OPENLLM_BASE_URL = os.getenv("OPENLLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


def require(*names):
    """Raise if any of the named settings is not set, e.g. require("OPENLLM_API_KEY")."""
    missing = [n for n in names if not globals().get(n)]
    if missing:
        raise RuntimeError(f"missing settings: {', '.join(missing)} (set them in dev.env or the environment)")
