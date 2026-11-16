"""Knowledge base ingestion: build the knowledge base from its two sources, the
SciLifeLab Serve docs and the masked history tickets.

Each source has its own ingestion and its own Qdrant collection. Steps 1-2 differ per
source; Steps 3-4 are the same code for both.

Serve docs ingestion (run_serve_docs_ingestion(), POST /api/ingestion/serve-docs):

  Step 1. Crawl (serve_docs/crawl.py): fetch every docs page as markdown.
  Step 2. Chunk (serve_docs/chunk.py): split the pages into chunks, by headings and
          FAQ questions.
  Steps 3-4. Embed and deploy (below), to the collection QDRANT_SERVE_GUIDE_COLLECTION.

History tickets ingestion (run_tickets_ingestion(), POST /api/ingestion/tickets):

  Step 1. Load (history_tickets/load.py): read the masked tickets from the uploaded
          zip, one JSON file per ticket.
  Step 2. Chunk (history_tickets/chunk.py): write every ticket as one text, one chunk
          per ticket.
  Steps 3-4. Embed and deploy (below), to the collection QDRANT_TICKETS_COLLECTION.

Shared by both ingestions (embed_deploy()):

  Step 3. Embed (embed.py): add a vector to every chunk with the embedding model.
  Step 4. Deploy (deploy.py): put the embedded chunks, with their metadata, into the
          source's Qdrant collection, replacing what was there. The collection names
          are set by hand in the settings (dev.env, see core/config.py); to keep the
          collection of an earlier ingestion, give a new name there (e.g. with the
          date, "serve_guide_20261116") and restart the app before the next ingestion.

Nothing is written to disk: the pages, tickets, chunks and vectors are passed on in
memory, and only the Qdrant collection keeps them. So no copy of the ticket texts is
left on the machine that runs the service; if the deploy fails, the ingestion is run again.

Async: an ingestion runs in the web service's event loop, next to the questions
(POST /api/user-support), with the app's shared async clients. While it waits on the
network (crawl, embed, deploy) the questions are served as usual. Load and chunk do not
wait on the network but compute, so they run in a worker thread (asyncio.to_thread);
run in the event loop, they would stop every question until done.
"""

import asyncio
import logging

from core import config
from kb_develop.deploy import deploy_chunks
from kb_develop.embed import embed_chunks
from kb_develop.history_tickets.chunk import chunk_tickets
from kb_develop.history_tickets.load import get_tickets
from kb_develop.serve_docs.chunk import chunk_pages
from kb_develop.serve_docs.crawl import crawl

logger = logging.getLogger(__name__)


# ------------------------- Serve docs: Steps 1-2, then 3-4 -------------------

async def run_serve_docs_ingestion(openai_client, qdrant_client):
    """Run the Serve docs ingestion (Steps 1-4) with the given async clients (see
    core/clients.py)."""
    # Step 1. Crawl
    logger.info("Step 1: crawl")
    pages = await crawl()
    logger.info("%d pages", len(pages))

    # Step 2. Chunk (in a worker thread: it computes, see the module docstring)
    logger.info("Step 2: chunk")
    chunks = await asyncio.to_thread(chunk_pages, pages)
    logger.info("%d chunks from %d pages", len(chunks), len(pages))

    # Steps 3-4. Embed and deploy
    await embed_deploy(chunks, config.QDRANT_SERVE_GUIDE_COLLECTION, openai_client, qdrant_client)


# ----------------------- History tickets: Steps 1-2, then 3-4 ----------------

async def run_tickets_ingestion(zip_bytes, openai_client, qdrant_client):
    """Run the history tickets ingestion (Steps 1-4) for the uploaded zip of masked
    tickets (zip_bytes is the content of the zip file), with the given async clients
    (see core/clients.py)."""
    config.require("QDRANT_TICKETS_COLLECTION")

    # Step 1. Load (in a worker thread: it unpacks the zip, see the module docstring)
    logger.info("Step 1: load")
    tickets = await asyncio.to_thread(get_tickets, zip_bytes)
    logger.info("%d tickets", len(tickets))
    if not tickets:
        raise ValueError("the zip holds no ticket (.json) files")

    # Step 2. Chunk (in a worker thread: it computes, see the module docstring)
    logger.info("Step 2: chunk")
    chunks = await asyncio.to_thread(chunk_tickets, tickets)
    logger.info("%d chunks from %d tickets", len(chunks), len(tickets))

    # Steps 3-4. Embed and deploy
    await embed_deploy(chunks, config.QDRANT_TICKETS_COLLECTION, openai_client, qdrant_client)


# ------------------------- Shared by both: Steps 3-4 -------------------------

async def embed_deploy(chunks, collection, openai_client, qdrant_client):
    """Run Steps 3-4 for the chunks of one source: embed them and deploy them to the
    given collection."""
    # Step 3. Embed
    logger.info("Step 3: embed")
    embedded_chunks = await embed_chunks(openai_client, chunks)

    # Step 4. Deploy
    # TODO: deploy without a gap, and without setting the collection names by hand.
    #  Now the deploy deletes the collection, recreates it and uploads the chunks, so
    #  for about a second it is missing or incomplete and a chat query in that moment
    #  finds nothing. To keep the old collection instead, its name must be changed by
    #  hand in the settings and the app restarted, and until the ingestion is done the
    #  chat then queries a collection that does not exist yet. Fix with a Qdrant alias:
    #  upload to a new collection named with the date and time of the ingestion (e.g.
    #  "serve_guide_<yyyymmdd-hhmmss>"), then switch an alias that the chat queries
    #  (e.g. "serve_guide_latest"; an alias cannot have the name of an existing
    #  collection) to it in one step, after the upload and the count check. Keep the
    #  previous collection (to go back to) and delete the older ones.
    logger.info("Step 4: deploy to %s", collection)
    await deploy_chunks(qdrant_client, embedded_chunks, collection)
    logger.info("Deployed %d chunks to collection %s", len(embedded_chunks), collection)
