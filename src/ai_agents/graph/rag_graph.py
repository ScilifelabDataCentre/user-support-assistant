"""Graph builder of the RAG graph: adds the nodes (nodes.py), connects them and compiles.

build_rag_graph() is called once, at startup (see app.py), with the shared API clients
(clients.py); llm_chat.py runs the compiled graph for each question.
"""

from functools import partial

from langgraph.graph import END, START, StateGraph

import config
from ai_agents import nodes
from ai_agents.state import RagState


def build_rag_graph(openai_client, qdrant_client):
    """Build and compile the RAG graph (Steps 1-6 in two nodes); the API clients are
    bound to the nodes here."""
    config.require("EMBEDDING_MODEL", "LLM_MODEL", "QDRANT_COLLECTION")

    graph = StateGraph(RagState)

    # Nodes
    graph.add_node(
        "retrieve",
        partial(nodes.retrieve, openai_client=openai_client, qdrant_client=qdrant_client),
    )
    graph.add_node("generate_answer", partial(nodes.generate_answer, openai_client=openai_client))

    # Edges: retrieve (Steps 1-3) -> generate_answer (Steps 4-6)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()
