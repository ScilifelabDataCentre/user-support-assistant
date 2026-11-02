"""LLM chat service: what the user support API calls to answer a question.

llm_chat() runs the RAG graph (graph/rag_graph.py, built once at startup in app.py) for one
question and returns the answer with its sources, so the API does not need to know
the graph's state. Given the Postgres pool, it also saves the request and what the
graph did with it as one row of the support_requests table (db/support_requests.py).
"""

import logging
import time

from db.support_requests import save_request

logger = logging.getLogger(__name__)

# Chunk fields stored in support_requests.retrieved_chunks as they are
STORED_CHUNK_FIELDS = ("score", "page_title", "headings", "section_url", "source_url", "type")


def retrieved_chunks_record(final_state):
    """All chunks given to the LLM with the prompt, as stored in
    support_requests.retrieved_chunks: best first, each with its rank and a copy of
    its text; None if the question was blocked (nothing was retrieved)."""
    if final_state["blocked"]:
        return None
    records = []
    for chunk in final_state["chunks"]:
        record = {"rank": chunk["number"]}
        for field in STORED_CHUNK_FIELDS:
            record[field] = chunk[field]
        record["content"] = chunk["text"]
        records.append(record)
    return records


async def save_chat(postgres_pool, ticket_id, question, final_state):
    """Save the request and its answer as one support_requests row. A database error
    is logged, not raised: the user still gets the answer."""
    try:
        row_id = await save_request(
            postgres_pool,
            ticket_id=ticket_id,
            user_request=question,
            guardrail_blocked=final_state["blocked"],
            # TODO: set from the graph state once the query rewriter node exists
            rewritten_query=None,
            retrieved_chunks=retrieved_chunks_record(final_state),
            suggested_response=final_state["answer"],
        )
    except Exception:
        logger.exception("Could not save the request to Postgres")
        return
    logger.info("Request saved as support_requests id %d", row_id)


async def llm_chat(rag_graph, question, postgres_pool=None, ticket_id=None):
    """Answer one question with the RAG graph; return (answer, sources): the full LLM
    answer followed by its "Sources:" list, and the metadata of the chunks it cites
    (empty when it cites none). With postgres_pool, the request is saved too.
    Async: while it waits on the network, the process serves other questions."""
    start = time.perf_counter()
    final_state = await rag_graph.ainvoke({"question": question})
    logger.info("Question answered in %.1fs", time.perf_counter() - start)
    if postgres_pool is not None:
        await save_chat(postgres_pool, ticket_id, question, final_state)
    return final_state["answer"], final_state["sources"]
