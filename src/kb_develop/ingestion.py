"""Knowledge base ingestion: build the knowledge base from the SciLifeLab Serve docs.

Ingestion steps (always all of them, in this order; results are passed on in memory):

  Step 1. Crawl (crawl_serve_docs.py): fetch every docs page as markdown
          (see the steps in crawl_serve_docs.py).
  Step 2. Chunk (chunk.py): split the pages into chunks, by headings and FAQ questions
          (see the rules in chunk.py).
  Step 3. Embed (embed.py): add a vector to every chunk with the embedding model.
  Step 4. Save: write the embedded chunks to output/<yyyymmdd-hhmmss>/embeddings.jsonl,
          one chunk (its text, metadata and "vector") per line.

Triggered through the API: POST /api/ingestion (see api/ingestion.py).
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from kb_develop.chunk import chunk_pages
from kb_develop.crawl_serve_docs import crawl
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


def run_ingestion(client):
    """Run Steps 1-4 with the given API client (clients.openai_client()) and return
    the path of the saved embeddings.jsonl."""
    # Step 1. Crawl
    logger.info("Step 1: crawl")
    pages = crawl()

    # Step 2. Chunk
    logger.info("Step 2: chunk")
    chunks = chunk_pages(pages)
    logger.info("%d chunks from %d pages", len(chunks), len(pages))

    # Step 3. Embed
    logger.info("Step 3: embed")
    embedded_chunks = embed_chunks(client, chunks)

    # Step 4. Save
    logger.info("Step 4: save")
    path = save(embedded_chunks)
    logger.info("%d embedded chunks -> %s", len(embedded_chunks), path)
    return path
