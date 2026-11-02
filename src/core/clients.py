"""Shared API clients, built from the settings in config.py.

Create a client once at startup (see app.py) and pass it to the functions that need
it, so its connections are reused and missing settings are reported before any work
starts.

Both clients are async (AsyncOpenAI, AsyncQdrantClient) and shared by the whole app:
the RAG graph behind POST /api/user-support, which serves many questions at once (see
ai_agents/__init__.py), and the knowledge base ingestion (see kb_develop/ingestion.py).
Their calls must be awaited, and no sync client may be used next to them: a sync
network call would block every request in the process.

The Postgres connection pool (postgres_pool) is async too; db/ uses it to save each
question to POST /api/user-support.
"""

import warnings
from urllib.parse import urlparse

from openai import AsyncOpenAI
from psycopg_pool import AsyncConnectionPool
from qdrant_client import AsyncQdrantClient

from core import config

# Hosts that mean "this machine"; traffic to them never leaves the computer.
LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")
# Most Postgres connections one process keeps open; more requests wait for a free one.
POSTGRES_POOL_MAX_SIZE = 10
# Seconds before a Postgres connection attempt is given up
POSTGRES_CONNECT_TIMEOUT = 10


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


def postgres_pool():
    """Async connection pool for the Postgres database at POSTGRES_HOST:POSTGRES_PORT,
    where db/ saves the requests. Connections are reused instead of opened per request
    (opening one takes ~20 ms: TCP + password check).
    It is created closed: app.py opens it in its lifespan, on the running event loop.
    psycopg's async connections do not work with Windows' ProactorEventLoop; main.py
    makes uvicorn use the SelectorEventLoop there."""
    config.require("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")
    connection_settings = {
        "host": config.POSTGRES_HOST,
        "port": config.POSTGRES_PORT,
        "user": config.POSTGRES_USER,
        "password": config.POSTGRES_PASSWORD,
        "dbname": config.POSTGRES_DB,
        "connect_timeout": POSTGRES_CONNECT_TIMEOUT,
    }
    return AsyncConnectionPool(kwargs=connection_settings, max_size=POSTGRES_POOL_MAX_SIZE, open=False)
