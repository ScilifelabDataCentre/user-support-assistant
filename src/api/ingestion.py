"""Knowledge base ingestion API.

POST /api/ingestion starts a knowledge base ingestion (crawl -> chunk -> embed ->
save -> deploy, see kb_develop/ingestion.py) and returns at once with 202 Accepted; the ingestion runs
in the background, because it takes longer than an HTTP request should wait.

Only one ingestion runs at a time: a request while one is running gets 409 Conflict.
Progress, the result and any error are written to the log.
"""

import logging
import threading

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from pydantic import BaseModel

from kb_develop.ingestion import run_ingestion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

# Held while an ingestion is running, so a second one cannot start.
ingestion_lock = threading.Lock()


class IngestionStarted(BaseModel):
    """Response of POST /api/ingestion."""

    status: str
    message: str


def run_in_background(openai_client, qdrant_client):
    """Run the ingestion, log the error if it fails, and release the lock when done."""
    try:
        run_ingestion(openai_client, qdrant_client)
    except Exception:
        logger.exception("Knowledge base ingestion failed")
    finally:
        ingestion_lock.release()


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=IngestionStarted)
def start_ingestion(request: Request, background_tasks: BackgroundTasks):
    """Start a knowledge base ingestion in the background
    (crawl -> chunk -> embed -> save -> deploy)."""
    if not ingestion_lock.acquire(blocking=False):
        raise HTTPException(status.HTTP_409_CONFLICT, "A knowledge base ingestion is already running.")

    # The shared clients, created at startup (see app.py).
    openai_client = request.app.state.openai_client
    qdrant_client = request.app.state.qdrant_client
    background_tasks.add_task(run_in_background, openai_client, qdrant_client)
    logger.info("Knowledge base ingestion started")
    return IngestionStarted(
        status="started",
        message="Knowledge base ingestion started; progress and result are in the server log.",
    )
