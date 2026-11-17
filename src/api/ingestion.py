"""Knowledge base ingestion API: one endpoint per source of the knowledge base.

  POST /api/ingestion/serve-docs  build the Serve docs collection: crawl -> chunk ->
                                  embed -> deploy, to the collection
                                  QDRANT_SERVE_GUIDE_COLLECTION. Takes no data: the
                                  service crawls the docs site itself.
  POST /api/ingestion/tickets     build the history tickets collection: load -> chunk ->
                                  embed -> deploy, to the collection
                                  QDRANT_TICKETS_COLLECTION. Takes a zip file of masked
                                  tickets (one JSON file per ticket), uploaded with the
                                  request; on the API docs page (/docs), choose the
                                  file and press Execute.

Both return at once with 202 Accepted; the ingestion (see kb/ingestion.py) runs
in the background, because it takes longer than an HTTP request should wait. The
content of the uploaded zip is read before the response, because the upload is closed
when the response is sent; a file that is not a zip is refused with 400 Bad Request.
The tickets in the zip are loaded in the background (Step 1 of the tickets ingestion),
so a zip with a file that is not a valid ticket is reported in the log.

The ingestion is async and uses the app's shared async clients (see app.py): it runs
on the same event loop as the questions, and while it waits on the network the
questions are served as usual.

Only one ingestion runs at a time, of either source: a request while one is running
gets 409 Conflict. Progress, the result and any error are written to the log.
"""

import asyncio
import io
import logging
import zipfile

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile, status
from pydantic import BaseModel

from kb.ingestion import run_serve_docs_ingestion, run_tickets_ingestion

logger = logging.getLogger(__name__)

# TODO: protect these endpoints with an admin key. Now anyone who can reach the service
#  can start an ingestion, or upload made-up tickets that the assistant then answers
#  from. Fix: a secret in the settings (e.g. ADMIN_API_KEY) that the request must send
#  in a header (e.g. X-API-Key), checked by a dependency of this router; without it,
#  401 Unauthorized. POST /api/user-support stays open.
router = APIRouter(prefix="/ingestion", tags=["admin"])

# Held while an ingestion is running, so a second one cannot start.
# TODO: Nice to have: only needed once the User Support Assistant is deployed with more than one
#  replica (or uvicorn --workers > 1); with one process this lock is enough.
#  The lock lives in this process's memory, so it only stops a second ingestion in
#  the same process. With several replicas, two requests can reach two replicas
#  and start two ingestions at once. Fix with a lock that all replicas share (e.g. a
#  Redis key with an expiry time), or by sending the ingestion requests always to the
#  same replica.
ingestion_lock = asyncio.Lock()


class IngestionStarted(BaseModel):
    """Response of the ingestion endpoints."""

    status: str
    message: str


async def take_lock():
    """Take the ingestion lock, or raise 409 Conflict if an ingestion is running."""
    # No await between the check and the acquire, so no other request can take the
    # lock in between; the acquire of a free lock returns at once.
    if ingestion_lock.locked():
        raise HTTPException(status.HTTP_409_CONFLICT, "A knowledge base ingestion is already running.")
    await ingestion_lock.acquire()


async def run_in_background(run_ingestion, *args):
    """Run the ingestion function with its arguments, log the error if it fails, and
    release the lock when done."""
    try:
        await run_ingestion(*args)
    except Exception:
        logger.exception("Knowledge base ingestion failed")
    finally:
        ingestion_lock.release()


@router.post("/serve-docs", status_code=status.HTTP_202_ACCEPTED, response_model=IngestionStarted)
async def start_serve_docs_ingestion(request: Request, background_tasks: BackgroundTasks):
    """Start a Serve docs ingestion in the background
    (crawl -> chunk -> embed -> deploy)."""
    await take_lock()

    # The shared async clients, created at startup (see app.py).
    openai_client = request.app.state.openai_client
    qdrant_client = request.app.state.qdrant_client
    background_tasks.add_task(run_in_background, run_serve_docs_ingestion, openai_client, qdrant_client)
    logger.info("Serve docs ingestion started")
    return IngestionStarted(
        status="started",
        message="Serve docs ingestion started; progress and result are in the server log.",
    )


@router.post("/tickets", status_code=status.HTTP_202_ACCEPTED, response_model=IngestionStarted)
async def start_tickets_ingestion(request: Request, background_tasks: BackgroundTasks, file: UploadFile):
    """Start a history tickets ingestion in the background
    (load -> chunk -> embed -> deploy).

    file: a zip of the masked tickets, one JSON file per ticket (the "tickets" folder
    of a masking run, zipped)."""
    await take_lock()

    # Read the content of the uploaded zip into memory, before the response: the upload
    # is closed when the response is sent. The ingestion loads the tickets from it.
    try:
        zip_bytes = await file.read()
    except BaseException:
        ingestion_lock.release()
        raise
    if not zipfile.is_zipfile(io.BytesIO(zip_bytes)):
        ingestion_lock.release()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The uploaded file is not a zip file.")

    # The shared async clients, created at startup (see app.py).
    openai_client = request.app.state.openai_client
    qdrant_client = request.app.state.qdrant_client
    background_tasks.add_task(run_in_background, run_tickets_ingestion, zip_bytes, openai_client, qdrant_client)
    logger.info("History tickets ingestion started: %s (%d bytes)", file.filename, len(zip_bytes))
    return IngestionStarted(
        status="started",
        message="History tickets ingestion started; progress and result are in the server log.",
    )
