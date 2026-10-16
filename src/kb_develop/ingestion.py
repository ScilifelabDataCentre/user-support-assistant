"""Knowledge base ingestion: build the knowledge base from the SciLifeLab Serve docs.

Ingestion steps (always all of them, in this order; results are passed on in memory):

  Step 1. Crawl (crawl_serve_docs.py): fetch every docs page as markdown
          (see the steps in crawl_serve_docs.py).
  Step 2. Chunk (chunk.py): split the pages into chunks, by headings and FAQ questions
          (see the rules in chunk.py).
  Step 3. Embed (embed.py): add a vector to every chunk with the embedding model.
  Step 4. Save: write the embedded chunks to output/<yyyymmdd-hhmmss>/embeddings.jsonl,
          one chunk (its text, metadata and "vector") per line.

Run from src/:  python -m kb_develop.ingestion
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from clients import openai_client
from kb_develop.chunk import chunk_pages
from kb_develop.crawl_serve_docs import crawl
from kb_develop.embed import embed_chunks

OUTPUT_ROOT = Path(__file__).parent / "output"

# Not __name__: run with -m, that would be "__main__".
logger = logging.getLogger("kb_develop.ingestion")


class ColorFormatter(logging.Formatter):
    """Log formatter that colors the level name: INFO green, WARNING yellow, ERROR red."""

    # ANSI terminal color codes
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }
    RESET = "\033[0m"

    def format(self, record):
        # Color a copy of the record, so other handlers still get the plain level name.
        record = logging.makeLogRecord(record.__dict__)
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname:<7}{self.RESET}"
        return super().format(record)


def setup_logging():
    """Log INFO and above to the console, with time, level and module name.
    The level name is colored when the output is a terminal (not a file or a pipe)."""
    log_format = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler()
    if handler.stream.isatty():
        handler.setFormatter(ColorFormatter(log_format, date_format))
    else:
        handler.setFormatter(logging.Formatter(log_format, date_format))
    logging.basicConfig(level=logging.INFO, handlers=[handler])

    # The HTTP client used by openai logs every request at INFO; only show its warnings.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpx2").setLevel(logging.WARNING)


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


def main():
    setup_logging()

    # Create the API client up front, so missing settings fail before the crawl starts.
    client = openai_client()

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


if __name__ == "__main__":
    main()
