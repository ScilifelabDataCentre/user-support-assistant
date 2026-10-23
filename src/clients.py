"""Shared API clients, built from the settings in config.py.

Create a client once at startup (see app.py) and pass it to the functions that need
it, so its connections are reused and missing settings are reported before any work
starts.

Both clients are async (AsyncOpenAI, AsyncQdrantClient) and shared by the whole app:
the RAG graph behind POST /api/user-support, which serves many questions at once (see
ai_agents/__init__.py), and the knowledge base ingestion (see kb_develop/ingestion.py).
Their calls must be awaited, and no sync client may be used next to them: a sync
network call would block every request in the process.
"""

import warnings
from urllib.parse import urlparse

from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient

import config

# Hosts that mean "this machine"; traffic to them never leaves the computer.
LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")


def openai_client():
    """Async OpenAI-compatible client for the LLM / embedding API at OPENLLM_BASE_URL.
    Its built-in retries are off (max_retries=0): callers retry with their own
    backoff (see kb_develop/embed.py request_with_retry)."""
    config.require("OPENLLM_API_KEY", "OPENLLM_BASE_URL")
    return AsyncOpenAI(base_url=config.OPENLLM_BASE_URL, api_key=config.OPENLLM_API_KEY, max_retries=0)


def qdrant_client():
    """Async client for the Qdrant vector database at QDRANT_URL.
    It only connects on its first request, so the app can start while Qdrant is down.
    QDRANT_COLLECTION is checked here too, so a missing collection name stops the app
    at startup instead of failing at the end of an ingestion.
    cloud_inference=True makes the client send text documents (models.Document) to
    the Qdrant server (on our infrastructure), which turns them into BM25 vectors (see kb_develop/deploy.py);
    despite its name it works with any Qdrant server >= 1.15.2, not only Qdrant Cloud.
    Without it, the client would compute them itself and need the fastembed package."""
    config.require("QDRANT_URL", "QDRANT_API_KEY", "QDRANT_COLLECTION")

    # With an http:// URL, qdrant-client warns that the API key is sent unencrypted.
    # That only matters when Qdrant runs on another machine, so for a local Qdrant
    # the warning is hidden.
    if urlparse(config.QDRANT_URL).hostname in LOCAL_HOSTS:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Api key is used with an insecure connection")
            return AsyncQdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY, cloud_inference=True)
    return AsyncQdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY, cloud_inference=True)
