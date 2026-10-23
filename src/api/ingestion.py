"""Knowledge base ingestion API.

POST /api/ingestion starts a knowledge base ingestion (crawl -> chunk -> embed ->
save -> deploy, see kb_develop/ingestion.py) and returns at once with 202 Accepted; the ingestion runs
in the background, because it takes longer than an HTTP request should wait.

The ingestion is async and uses the app's shared async clients (see app.py): it runs
on the same event loop as the questions, and while it waits on the network the
questions are served as usual.

Only one ingestion runs at a time: a request while one is running gets 409 Conflict.
Progress, the result and any error are written to the log.
"""

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from pydantic import BaseModel

from kb_develop.ingestion import run_ingestion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingestion", tags=["admin"])

# Held while an ingestion is running, so a second one cannot start.
# TODO: Nice to have: only needed once the User Support Assistant is deployed with more than one
#  replica (or uvicorn --workers > 1); with one process this lock is enough.
#  The lock lives in this process's memory, so it only stops a second ingestion in
#  the same process. With several replicas, two requests can reach two replicas
#  and start two ingestions at once, which delete and rebuild the same Qdrant
#  collection in turn. Fix with a lock that all replicas share (e.g. a Redis key with
#  an expiry time), or by sending POST /api/ingestion always to the same replica.
ingestion_lock = asyncio.Lock()


class IngestionStarted(BaseModel):
    """Response of POST /api/ingestion."""

    status: str
    message: str


async def run_in_background(openai_client, qdrant_client):
    """Run the ingestion, log the error if it fails, and release the lock when done."""
    try:
        await run_ingestion(openai_client, qdrant_client)
    except Exception:
        logger.exception("Knowledge base ingestion failed")
    finally:
        ingestion_lock.release()


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=IngestionStarted)
async def start_ingestion(request: Request, background_tasks: BackgroundTasks):
    """Start a knowledge base ingestion in the background
    (crawl -> chunk -> embed -> save -> deploy)."""
    # No await between the check and the acquire, so no other request can take the
    # lock in between; the acquire of a free lock returns at once.
    if ingestion_lock.locked():
        raise HTTPException(status.HTTP_409_CONFLICT, "A knowledge base ingestion is already running.")
    await ingestion_lock.acquire()

    # The shared async clients, created at startup (see app.py).
    openai_client = request.app.state.openai_client
    qdrant_client = request.app.state.qdrant_client
    background_tasks.add_task(run_in_background, openai_client, qdrant_client)
    logger.info("Knowledge base ingestion started")
    return IngestionStarted(
        status="started",
        message="Knowledge base ingestion started; progress and result are in the server log.",
    )
