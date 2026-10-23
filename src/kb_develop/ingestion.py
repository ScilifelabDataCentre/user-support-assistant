"""Knowledge base ingestion: build the knowledge base from the SciLifeLab Serve docs.

Ingestion steps (always all of them, in this order; results are passed on in memory):

  Step 1. Crawl (crawl_serve_docs.py): fetch every docs page as markdown
          (see the steps in crawl_serve_docs.py).
  Step 2. Chunk (chunk.py): split the pages into chunks, by headings and FAQ questions
          (see the rules in chunk.py).
  Step 3. Embed (embed.py): add a vector to every chunk with the embedding model.
  Step 4. Save: write the embedded chunks to output/<yyyymmdd-hhmmss>/embeddings.jsonl,
          one chunk (its text, metadata and "vector") per line. Done before Deploy, so
          the embeddings are kept even if the deploy fails.
  Step 5. Deploy (deploy.py): put the embedded chunks, with their metadata, into the
          Qdrant collection "serve_guide", replacing what was there
          (see the steps in deploy.py).

Triggered through the API: POST /api/ingestion (see api/ingestion.py).

Async: the ingestion runs in the web service's event loop, next to the questions
(POST /api/user-support), with the app's shared async clients. While it waits on the
network (Steps 1, 3, 5) the questions are served as usual. Steps 2 and 4 do not wait
on the network but compute or write a file, so they run in a worker thread
(asyncio.to_thread); run in the event loop, they would stop every question until done.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from kb_develop.chunk import chunk_pages
from kb_develop.crawl_serve_docs import crawl
from kb_develop.deploy import deploy_chunks
from kb_develop.embed import embed_chunks

OUTPUT_ROOT = Path(__file__).parent / "output"

logger = logging.getLogger(__name__)


def save(chunks, output_root=OUTPUT_ROOT):
    """Step 4: write the embedded chunks to output_root/<yyyymmdd-hhmmss>/embeddings.jsonl
    and return that path."""
    run_dir = Path(output_root) / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True)
    path = run_dir / "embeddings.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    return path


async def run_ingestion(openai_client, qdrant_client):
    """Run Steps 1-5 with the given async clients (see core/clients.py) and return the path
    of the saved embeddings.jsonl."""
    # Step 1. Crawl
    logger.info("Step 1: crawl")
    pages = await crawl()

    # Step 2. Chunk (in a worker thread: it computes, see the module docstring)
    logger.info("Step 2: chunk")
    chunks = await asyncio.to_thread(chunk_pages, pages)
    logger.info("%d chunks from %d pages", len(chunks), len(pages))

    # Step 3. Embed
    logger.info("Step 3: embed")
    embedded_chunks = await embed_chunks(openai_client, chunks)

    # Step 4. Save (before Deploy, so the embeddings are kept even if the deploy fails;
    # in a worker thread: it writes a file, see the module docstring)
    logger.info("Step 4: save")
    path = await asyncio.to_thread(save, embedded_chunks)
    logger.info("%d embedded chunks -> %s", len(embedded_chunks), path)

    # Step 5. Deploy
    # TODO: deploy without a gap. Now the deploy deletes "serve_guide", recreates it and
    #  uploads the chunks, so for about a second the collection is missing or incomplete
    #  and a chat query in that moment finds nothing. Fix with a Qdrant alias: upload to
    #  a new collection (e.g. "serve_guide_<yyyymmdd-hhmmss>"), then switch the alias
    #  "serve_guide" to it in one step, then delete the old collection. Needed once the
    #  chat service queries the collection.
    logger.info("Step 5: deploy")
    await deploy_chunks(qdrant_client, embedded_chunks)
    return path
