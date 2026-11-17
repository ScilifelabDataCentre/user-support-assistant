"""State of the RAG graph: the data passed between the nodes (see nodes/)."""

from typing import TypedDict


class RagState(TypedDict, total=False):
    """The graph starts with "question"; each node adds its own keys."""

    # The user's question
    question: str

    # True if the question is blocked as prompt injection; the graph then ends
    blocked: bool

    # The chunks given to the LLM, numbered 1..n: Serve docs first, then history tickets
    chunks: list

    # The answer, followed by its "Sources:" list
    answer: str

    # Metadata of the chunks the answer cites, renumbered 1..n
    sources: list
