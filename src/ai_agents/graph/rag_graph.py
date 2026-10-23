"""Graph builder of the RAG graph: adds the nodes (nodes/), connects them and compiles.

build_rag_graph() is called once, at startup (see app.py), with the shared async API
clients (clients.py); llm_chat.py runs the compiled graph for each question with
ainvoke().
"""

import asyncio
from functools import partial

from langgraph.graph import END, START, StateGraph

import config
from ai_agents.nodes.generate_answer import generate_answer
from ai_agents.nodes.retrieve import retrieve
from ai_agents.state import RagState


def build_rag_graph(openai_client, qdrant_client):
    """Build and compile the RAG graph (Steps 1-6 in two nodes); the async API clients
    (AsyncOpenAI, AsyncQdrantClient) and the semaphore are bound to the nodes here."""
    config.require("EMBEDDING_MODEL", "LLM_MODEL", "QDRANT_COLLECTION")

    # Shared by all questions: at most OPENLLM_MAX_CONCURRENCY requests to the LLM /
    # embedding API at the same time (Steps 1 and 5)
    openllm_semaphore = asyncio.Semaphore(config.OPENLLM_MAX_CONCURRENCY)

    graph = StateGraph(RagState)

    # Nodes
    graph.add_node(
        "retrieve",
        partial(
            retrieve,
            openai_client=openai_client,
            qdrant_client=qdrant_client,
            openllm_semaphore=openllm_semaphore,
        ),
    )
    graph.add_node(
        "generate_answer",
        partial(generate_answer, openai_client=openai_client, openllm_semaphore=openllm_semaphore),
    )

    # Edges: retrieve (Steps 1-3) -> generate_answer (Steps 4-6)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()
