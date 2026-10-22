"""User support assistant: the FastAPI application.

Endpoints:
  GET  /health           health check (see api/health.py)
  POST /api/ingestion    start a knowledge base ingestion (see api/ingestion.py)
  POST /api/user-support answer a user's question with RAG (see api/user_support.py)

Start it from the repo root with:  python main.py
API docs (to try the endpoints): http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from ai_agents.graph.rag_graph import build_rag_graph
from api import health, ingestion, user_support
from clients import openai_client, qdrant_client
from logging_setup import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app):
    """Create shared resources at startup and clean them up at shutdown."""
    # One client of each for the whole app; missing settings stop the app at startup.
    app.state.openai_client = openai_client()
    app.state.qdrant_client = qdrant_client()
    # The RAG graph behind POST /api/user-support, built once with the shared clients.
    app.state.rag_graph = build_rag_graph(app.state.openai_client, app.state.qdrant_client)
    yield
    app.state.openai_client.close()
    app.state.qdrant_client.close()


# The sections of the API docs page, in the order they are shown.
tags_metadata = [
    {"name": "user-support"},
    {"name": "admin"},
    {"name": "system"},
]

app = FastAPI(title="User Support Assistant", lifespan=lifespan, openapi_tags=tags_metadata)
app.include_router(health.router)
app.include_router(ingestion.router, prefix="/api")
app.include_router(user_support.router, prefix="/api")
