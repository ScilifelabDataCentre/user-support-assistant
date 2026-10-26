"""User support assistant: the FastAPI application.

Endpoints:
  GET  /health           health check (see api/health.py)
  POST /api/ingestion    start a knowledge base ingestion (see api/ingestion.py)
  POST /api/user-support answer a user's question with RAG (see api/user_support.py)
  GET  /demo             Gradio chat page to try the assistant (see demo/gradio_app.py;
                         off when ENABLE_DEMO=false)

Start it from the repo root with:  python main.py
API docs (to try the endpoints): http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from ai_agents.graph.rag_graph import build_rag_graph
from api import health, ingestion, user_support
from core import config
from core.clients import openai_client, qdrant_client
from core.logging_setup import new_request_id, request_id_var, setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app):
    """Create shared resources at startup and clean them up at shutdown."""
    # One async client of each for the whole app (the RAG graph and the ingestion), so
    # one process serves many requests at once; missing settings stop the app at startup.
    app.state.openai_client = openai_client()
    app.state.qdrant_client = qdrant_client()
    # The RAG graph behind POST /api/user-support, built once with the shared clients.
    app.state.rag_graph = build_rag_graph(app.state.openai_client, app.state.qdrant_client)
    yield
    await app.state.openai_client.close()
    await app.state.qdrant_client.close()


# The sections of the API docs page, in the order they are shown.
tags_metadata = [
    {"name": "user-support"},
    {"name": "admin"},
    {"name": "system"},
]

app = FastAPI(title="User Support Assistant", lifespan=lifespan, openapi_tags=tags_metadata)


@app.middleware("http")
async def add_request_id(request, call_next):
    """Give each request an id: every log line it writes shows it (see core/logging_setup.py),
    and the response returns it in the X-Request-ID header, so a user's report can be
    matched to its log lines."""
    request_id = new_request_id()
    token = request_id_var.set(request_id)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(health.router)
app.include_router(ingestion.router, prefix="/api")
app.include_router(user_support.router, prefix="/api")

if config.ENABLE_DEMO:
    # Imported only here, so the API also runs where Gradio is not installed.
    import gradio as gr

    from demo.gradio_app import build_demo

    # Mounted on this app, so the demo runs in the same process and keeps its lifespan.
    app = gr.mount_gradio_app(app, build_demo(app), path="/demo")
