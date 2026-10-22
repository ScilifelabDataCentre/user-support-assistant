"""LLM chat service: what the user support API calls to answer a question.

llm_chat() runs the RAG graph (graph/rag_graph.py, built once at startup in app.py) for one
question and returns the answer with its sources, so the API does not need to know
the graph's state.
"""


def llm_chat(rag_graph, question):
    """Answer one question with the RAG graph; return (answer, sources): the full LLM
    answer followed by its "Sources:" list, and the metadata of the chunks it cites
    (empty when it cites none)."""
    final_state = rag_graph.invoke({"question": question})
    return final_state["answer"], final_state["sources"]
