"""retrieve node of the RAG graph: Steps 1-3 (see the steps in ai_agents/__init__.py).

One function per step, then the node that runs them in order. The node takes the
RagState (state.py) and returns the keys it adds; it also takes the API clients it
needs, which graph/rag_graph.py binds when it adds the node.
"""

import logging

from qdrant_client.models import Document, Fusion, FusionQuery, Prefetch

import config
from kb_develop.deploy import BM25_MODEL, DENSE_VECTOR, SPARSE_VECTOR

logger = logging.getLogger(__name__)

# Candidates returned by each of the two searches, before fusion (Step 2)
PREFETCH_LIMIT = 20
# Chunks kept after fusion and given to the LLM (Steps 2, 3)
TOP_K = 5
# Retries of a failed embedding request; the openai client waits between them with
# exponential backoff (Step 1). Few, because the user is waiting.
MAX_RETRIES = 2


# ------------------------- Step 1: embed the question ------------------------

def embed_question(question, openai_client):
    """Step 1: embed the question with EMBEDDING_MODEL; return its dense vector."""
    client = openai_client.with_options(max_retries=MAX_RETRIES)
    response = client.embeddings.create(model=config.EMBEDDING_MODEL, input=[question])
    return response.data[0].embedding


# ---------------------------- Step 2: hybrid search --------------------------

def hybrid_search(question, question_vector, qdrant_client):
    """Step 2: dense + sparse (BM25) search in one Qdrant query, fused with RRF;
    return the found points (Qdrant ScoredPoint, best first)."""
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
    response = qdrant_client.query_points(
        collection_name=config.QDRANT_COLLECTION,
        prefetch=[dense_search, sparse_search],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=TOP_K,
        with_payload=True,
    )
    logger.info("Hybrid search found %d chunks", len(response.points))
    return response.points


# ---------------------------- Step 3: select chunks --------------------------

def select_chunks(hits):
    """Step 3: number the found chunks and keep their text and metadata."""
    chunks = []
    for hit in hits:
        payload = hit.payload
        title = " > ".join(payload["breadcrumb"] + payload["headings"])
        chunk = {
            "number": len(chunks) + 1,
            "title": title,
            "page_title": payload["page_title"],
            "headings": payload["headings"],
            "section_url": payload["section_url"],
            "source_url": payload["source_url"],
            "type": payload["type"],
            "text": payload["content"],
        }
        chunks.append(chunk)
    return chunks


# ------------------------------------ Node -----------------------------------

def retrieve(state, openai_client, qdrant_client):
    """Node: Steps 1-3, find the chunks for the question."""
    # Step 1. Embed the question
    question_vector = embed_question(state["question"], openai_client)

    # Step 2. Hybrid search
    hits = hybrid_search(state["question"], question_vector, qdrant_client)

    # Step 3. Select chunks
    chunks = select_chunks(hits)
    return {"chunks": chunks}
