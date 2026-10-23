"""LLM chat service: what the user support API calls to answer a question.

llm_chat() runs the RAG graph (graph/rag_graph.py, built once at startup in app.py) for one
question and returns the answer with its sources, so the API does not need to know
the graph's state.
"""

import logging
import time

logger = logging.getLogger(__name__)


async def llm_chat(rag_graph, question):
    """Answer one question with the RAG graph; return (answer, sources): the full LLM
    answer followed by its "Sources:" list, and the metadata of the chunks it cites
    (empty when it cites none). Async: while it waits on the network, the process
    serves other questions."""
    start = time.perf_counter()
    final_state = await rag_graph.ainvoke({"question": question})
    logger.info("Question answered in %.1fs", time.perf_counter() - start)
    return final_state["answer"], final_state["sources"]
