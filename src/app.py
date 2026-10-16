"""User support assistant: the FastAPI application.

Endpoints:
  GET  /health           health check (see api/health.py)
  POST /api/ingestion    start a knowledge base ingestion (see api/ingestion.py)

Start it from the repo root with:  python main.py
API docs (to try the endpoints): http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import health, ingestion
from clients import openai_client, qdrant_client
from logging_setup import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app):
    """Create shared resources at startup and clean them up at shutdown."""
    # One client of each for the whole app; missing settings stop the app at startup.
    app.state.openai_client = openai_client()
    app.state.qdrant_client = qdrant_client()
    yield
    app.state.openai_client.close()
    app.state.qdrant_client.close()


app = FastAPI(title="User Support Assistant", lifespan=lifespan)
app.include_router(health.router)
app.include_router(ingestion.router, prefix="/api")
