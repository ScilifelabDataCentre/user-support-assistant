"""RAG graph for the user support API: answer a user's question from the knowledge base.

The RAG steps (Steps 0-6) and the graph are described in graph/rag_graph.py.

Files:

  graph/rag_graph.py           the list of all steps (Steps 0-6), and the graph
                               builder: build_rag_graph(), called once at startup
                               (app.py)
  state.py                     RagState: the data passed between the nodes
  nodes/guard.py               the guard node and its rules (Step 0)
  nodes/retrieve.py            the retrieve node and its steps (Steps 1-3)
  nodes/generate_answer.py     the generate_answer node and its steps (Steps 4-6)
  prompts/generate_answer_prompt.py
                               the system prompt, the user prompt templates and the
                               "Sources:" list format of generate_answer
  llm_chat.py                  the service the API calls: llm_chat() runs the graph
                               for one question

Calls: POST /api/user-support (api/user_support.py) -> llm_chat() -> the RAG graph;
llm_chat() then saves the request and the graph's result in Postgres (db/support_requests.py).
"""
