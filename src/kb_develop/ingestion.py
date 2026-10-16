"""Knowledge base ingestion: crawl the SciLifeLab Serve docs, then chunk the latest crawl.

The latest directory in output/ (yyyymmdd-hhmmss) is the one used for the knowledge base:
  output/<run>/source/*.md            pages from the crawler
  output/<run>/chunks/chunks.jsonl    chunks
"""

import argparse

from chunk import chunk_run, latest_run_dir, write_chunks
from crawl_serve_docs import OUTPUT_ROOT, crawl


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-crawl", action="store_true", help="reuse the latest crawl in output/")
    args = ap.parse_args()

    if not args.skip_crawl:
        crawl(OUTPUT_ROOT)
    run_dir = latest_run_dir(OUTPUT_ROOT)
    print(f"Using crawl {run_dir.name}")

    chunks = chunk_run(run_dir)
    out = write_chunks(chunks, run_dir)
    print(f"{len(chunks)} chunks -> {out}")


if __name__ == "__main__":
    main()
