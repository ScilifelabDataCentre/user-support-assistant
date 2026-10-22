"""State of the RAG graph: the data passed between the nodes (see nodes/)."""

from typing import TypedDict


class RagState(TypedDict, total=False):
    """The graph starts with "question"; each node adds its own keys."""

    # Input: the user's question
    question: str
    # retrieve (Steps 1-3): the selected chunks: {"number", "title", "page_title",
    # "headings", "section_url", "source_url", "type", "text"}
    chunks: list
    # generate_answer (Steps 4-6): the LLM's answer followed by its "Sources:" list
    answer: str
    # generate_answer (Step 6): metadata of the chunks the answer cites, renumbered 1..n
    sources: list
