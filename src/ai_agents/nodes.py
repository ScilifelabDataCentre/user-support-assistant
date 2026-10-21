"""Nodes of the RAG graph (see the steps in __init__.py).

One function per step (Steps 1-6), then the two nodes that run them in order:
retrieve (Steps 1-3) and generate_answer (Steps 4-6). Each node takes the RagState
(state.py) and returns the keys it adds; it also takes the API clients it needs,
which graph.py binds when it adds the node.
"""

import logging
import re

from qdrant_client.models import Document, Fusion, FusionQuery, Prefetch

import config
from ai_agents.prompts import (
    CHUNK_TEMPLATE,
    SOURCE_LINE_TEMPLATE,
    SOURCES_HEADER,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)
from kb_develop.deploy import BM25_MODEL, DENSE_VECTOR, SPARSE_VECTOR

logger = logging.getLogger(__name__)

# Candidates returned by each of the two searches, before fusion (Step 2)
PREFETCH_LIMIT = 20
# Chunks kept after fusion and given to the LLM (Steps 2, 3)
TOP_K = 5
# Retries of a failed embedding or LLM request; the openai client waits between them
# with exponential backoff (Steps 1, 5). Few, because the user is waiting.
MAX_RETRIES = 2
# Seconds before an LLM request is given up (Step 5)
LLM_TIMEOUT = 120.0
# Low temperature: answers stay close to the documentation (Step 5)
TEMPERATURE = 0.2
# Reasoning that some models (e.g. Qwen3) write before the answer; removed (Step 5)
THINK_RE = re.compile(r"<think>.*?</think>", re.S)
# A citation in the answer: [1], or several numbers in one bracket like [1, 3] (Step 6)
CITATION_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
# Chunk fields returned as a source's metadata (Step 6)
SOURCE_FIELDS = ("number", "page_title", "headings", "section_url", "source_url", "type")


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


# ---------------------------- Step 4: build prompt ---------------------------

def build_prompt(question, chunks):
    """Step 4: the chat messages: the system prompt, then the numbered chunks and the
    question."""
    chunk_texts = []
    for chunk in chunks:
        chunk_text = CHUNK_TEMPLATE.format(
            number=chunk["number"],
            title=chunk["title"],
            url=chunk["section_url"],
            text=chunk["text"],
        )
        chunk_texts.append(chunk_text)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        chunks="\n\n---\n\n".join(chunk_texts),
        question=question,
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    return messages


# ----------------------------- Step 5: call the LLM --------------------------

def call_llm(messages, openai_client):
    """Step 5: ask LLM_MODEL for the answer; remove any <think> reasoning from it."""
    client = openai_client.with_options(max_retries=MAX_RETRIES, timeout=LLM_TIMEOUT)
    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
        temperature=TEMPERATURE,
    )
    content = response.choices[0].message.content or ""
    answer = THINK_RE.sub("", content).strip()
    return answer


# ----------------------------- Step 6: add sources ---------------------------

def cited_numbers(answer):
    """Step 6: the chunk numbers the answer cites, e.g. {1, 3} for "... [1] ... [1, 3]"."""
    numbers = set()
    for match in CITATION_RE.finditer(answer):
        for number in match.group(1).split(","):
            numbers.add(int(number))
    return numbers


def add_sources(answer, chunks):
    """Step 6: keep the chunks the answer cites as its sources (metadata only), and
    append them to the answer as a "Sources:" list; return (answer, sources).
    Nothing cited: answer unchanged, no sources."""
    cited = cited_numbers(answer)

    sources = []
    source_lines = []
    for chunk in chunks:
        if chunk["number"] not in cited:
            continue
        source = {}
        for field in SOURCE_FIELDS:
            source[field] = chunk[field]
        sources.append(source)
        source_line = SOURCE_LINE_TEMPLATE.format(
            number=chunk["number"],
            title=chunk["title"],
            url=chunk["section_url"],
        )
        source_lines.append(source_line)

    if not sources:
        return answer, sources
    answer = answer + "\n\n" + SOURCES_HEADER + "\n" + "\n".join(source_lines)
    return answer, sources


# ----------------------------------- Nodes -----------------------------------

def retrieve(state, openai_client, qdrant_client):
    """Node: Steps 1-3, find the chunks for the question."""
    # Step 1. Embed the question
    question_vector = embed_question(state["question"], openai_client)

    # Step 2. Hybrid search
    hits = hybrid_search(state["question"], question_vector, qdrant_client)

    # Step 3. Select chunks
    chunks = select_chunks(hits)
    return {"chunks": chunks}


def generate_answer(state, openai_client):
    """Node: Steps 4-6, answer the question from the chunks, with its sources."""
    # Step 4. Build the prompt
    messages = build_prompt(state["question"], state["chunks"])

    # Step 5. Call the LLM
    answer = call_llm(messages, openai_client)

    # Step 6. Add sources
    answer, sources = add_sources(answer, state["chunks"])
    return {"answer": answer, "sources": sources}
