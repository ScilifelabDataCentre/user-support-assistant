"""retrieve node of the RAG graph: Steps 1-3 (see the steps in graph/rag_graph.py).

One function per step, then the node that runs them in order. The node takes the
RagState (state.py) and returns the keys it adds; it also takes the async API clients
and the semaphore it needs, which graph/rag_graph.py binds when it adds the node.
Steps 1 and 2 are async (they wait on the network); Step 3 only computes.
"""

import asyncio
import logging

from qdrant_client.models import Document, Fusion, FusionQuery, Prefetch

from core import config
from kb.deploy import BM25_MODEL, DENSE_VECTOR, SPARSE_VECTOR

logger = logging.getLogger(__name__)

# The two sources of the knowledge base, as the "source" of a selected chunk
SERVE_DOCS = "serve_docs"
HISTORY_TICKETS = "history_tickets"
# Metadata fields kept with a selected chunk, per source. Also read by
# generate_answer.py (the metadata returned with a source, Step 6) and llm_chat.py
# (the metadata stored with the request).
CHUNK_METADATA_FIELDS = {
    SERVE_DOCS: ("page_title", "headings", "section_url", "source_url", "type"),
    HISTORY_TICKETS: ("incident_id", "subcategory", "subject"),
}

# Candidates returned by each of the two searches (dense, sparse) in one collection,
# before fusion
PREFETCH_LIMIT = 20
# Chunks kept after fusion and given to the LLM, per collection
SERVE_DOCS_TOP_K = 5
TICKETS_TOP_K = 5
# Retries of a failed embedding request; the openai client waits between them with
# exponential backoff. Few, because the user is waiting.
MAX_RETRIES = 2


# ------------------------- Step 1: embed the question ------------------------

async def embed_question(question, openai_client, openllm_semaphore):
    """Step 1: embed the question with EMBEDDING_MODEL; return its dense vector."""
    client = openai_client.with_options(max_retries=MAX_RETRIES)
    async with openllm_semaphore:
        response = await client.embeddings.create(model=config.EMBEDDING_MODEL, input=[question])
    return response.data[0].embedding


# ---------------------------- Step 2: hybrid search --------------------------

async def hybrid_search(question, question_vector, qdrant_client, collection, limit):
    """Step 2: dense + sparse (BM25) search in one Qdrant query on the given
    collection, fused with RRF; return the best `limit` points (Qdrant ScoredPoint,
    best first)."""
    dense_search = Prefetch(
        query=question_vector,
        using=DENSE_VECTOR,
        limit=PREFETCH_LIMIT,
    )
    sparse_search = Prefetch(
        query=Document(text=question, model=BM25_MODEL),
        using=SPARSE_VECTOR,
        limit=PREFETCH_LIMIT,
    )
    response = await qdrant_client.query_points(
        collection_name=collection,
        prefetch=[dense_search, sparse_search],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=limit,
        with_payload=True,
    )
    logger.info("Hybrid search in %s found %d chunks", collection, len(response.points))
    return response.points


async def search_docs_and_tickets(question, question_vector, qdrant_client):
    """Step 2: run the hybrid search in the Serve docs collection and in the history
    tickets collection at the same time; return (serve_docs_hits, ticket_hits). The two
    results are not merged into one ranking: an RRF score only says how a chunk ranks
    within its own collection."""
    serve_docs_search = hybrid_search(
        question, question_vector, qdrant_client,
        config.QDRANT_SERVE_GUIDE_COLLECTION, SERVE_DOCS_TOP_K,
    )
    tickets_search = hybrid_search(
        question, question_vector, qdrant_client,
        config.QDRANT_TICKETS_COLLECTION, TICKETS_TOP_K,
    )
    serve_docs_hits, ticket_hits = await asyncio.gather(serve_docs_search, tickets_search)
    return serve_docs_hits, ticket_hits


# ---------------------------- Step 3: select chunks --------------------------

def serve_docs_title(payload):
    """Step 3: the title of a Serve docs chunk: its breadcrumb and headings, e.g.
    "Application hosting > Shiny app hosting > Step 6. Create an app"."""
    return " > ".join(payload["breadcrumb"] + payload["headings"])


def ticket_title(payload):
    """Step 3: the title of a history ticket: its ID, subject and subcategory, e.g.
    "Ticket KTH-INC-4492487: App fails to start after update (Shiny)". A missing
    subject or subcategory is left out."""
    title = f"Ticket {payload['incident_id']}"
    if payload["subject"]:
        title += f": {payload['subject']}"
    if payload["subcategory"]:
        title += f" ({payload['subcategory']})"
    return title


def select_chunk(hit, source, number):
    """Step 3: one found chunk with the given number: its source, title, text and the
    metadata fields of its source."""
    payload = hit.payload
    if source == SERVE_DOCS:
        title = serve_docs_title(payload)
    else:
        title = ticket_title(payload)

    chunk = {
        "number": number,
        "source": source,
        "title": title,
        "text": payload["content"],
        "score": hit.score,
    }
    for field in CHUNK_METADATA_FIELDS[source]:
        chunk[field] = payload[field]
    return chunk


def select_chunks(serve_docs_hits, ticket_hits):
    """Step 3: number the found chunks, the Serve docs chunks first and then the
    history tickets, and keep their text and metadata."""
    chunks = []
    for hit in serve_docs_hits:
        chunk = select_chunk(hit, SERVE_DOCS, len(chunks) + 1)
        headings = " > ".join(chunk["headings"])
        logger.info("[%d] Serve docs: %s | %s (%s, RRF score %.3f)", chunk["number"],
                    chunk["page_title"], headings, chunk["type"], chunk["score"])
        chunks.append(chunk)

    for hit in ticket_hits:
        chunk = select_chunk(hit, HISTORY_TICKETS, len(chunks) + 1)
        # Only the ticket ID and subcategory are logged, not the ticket's subject or text
        logger.info("[%d] Ticket: %s (%s, RRF score %.3f)", chunk["number"],
                    chunk["incident_id"], chunk["subcategory"], chunk["score"])
        chunks.append(chunk)
    return chunks


# ------------------------------------ Node -----------------------------------

async def retrieve(state, openai_client, qdrant_client, openllm_semaphore):
    """Node: Steps 1-3, find the chunks for the question."""
    # Step 1. Embed the question
    logger.info("Question: %s", state["question"])
    logger.info("Step 1: embed the question (%s)", config.EMBEDDING_MODEL)
    question_vector = await embed_question(state["question"], openai_client, openllm_semaphore)

    # Step 2. Hybrid search, in both collections of serve docs and history tickets, in parallel; return the hits from each collection。
    logger.info("Step 2: hybrid search in %s and %s",
                config.QDRANT_SERVE_GUIDE_COLLECTION, config.QDRANT_TICKETS_COLLECTION)
    serve_docs_hits, ticket_hits = await search_docs_and_tickets(state["question"], question_vector, qdrant_client)

    # Step 3. Select chunks
    logger.info("Step 3: select chunks")
    chunks = select_chunks(serve_docs_hits, ticket_hits)
    return {"chunks": chunks}
