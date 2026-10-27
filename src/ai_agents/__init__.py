"""RAG graph for the user support API: answer a user's question from the knowledge base.

RAG steps, run by three LangGraph nodes: guard (Step 0), retrieve (Steps 1-3) and
generate_answer (Steps 4-6). Each node is one file in nodes/, with one function per step.

  Step 0. Guard: check the question against rules for the most obvious prompt
          injection attacks (override the rules, extract the system prompt, change
          the assistant's role, chat template tokens). On a match the graph ends
          with a fixed refusal, before any API call.
  Step 1. Embed the question: turn the question into a dense vector with
          EMBEDDING_MODEL, the same model the chunks were embedded with
          (see kb_develop/embed.py).
  Step 2. Hybrid search: one Qdrant query on QDRANT_COLLECTION that runs two searches
          and fuses their results with Reciprocal Rank Fusion (RRF, by rank only):
            - dense: the question vector against the chunks' dense vector (meaning);
            - sparse: the question as a BM25 document against the chunks' sparse
              vector (keywords); Qdrant computes its BM25 vector on the server.
          Each search returns PREFETCH_LIMIT candidates; the fused list keeps the best TOP_K.
  Step 3. Select chunks: keep each found chunk's text and metadata (title, headings,
          links, type), numbered 1..n in fused order; the LLM cites the chunks by
          these numbers.
  Step 4. Build the prompt: the system prompt (rules), then one user message with the
          numbered chunks and the question.
  Step 5. Call the LLM: LLM_MODEL answers in English from the chunks only, citing
          them as [1], [2], ... If the chunks do not answer the question, the system
          prompt tells it to say so and suggest contacting the SciLifeLab Serve team.
  Step 6. Add sources: keep the chunks the answer actually cites as its sources,
          renumbered 1..n; remove the [n] citations from the answer and append the
          sources to it as a "Sources:" list (number, title, link).

Graph:

  START -> guard (Step 0) -> retrieve (Steps 1-3) -> generate_answer (Steps 4-6) -> END
                  |
                  +-> END (question blocked: the answer is the refusal)

Async: the whole path is async (endpoint -> llm_chat() -> ainvoke() -> nodes ->
AsyncOpenAI / AsyncQdrantClient), so while one question waits on the network the
process serves others. Nothing on this path may block: a sync network call would
stop every request in the process (the knowledge base ingestion runs in the same
process with the same clients, see kb_develop/ingestion.py). At most OPENLLM_MAX_CONCURRENCY requests go to
the LLM / embedding API at the same time (Steps 1 and 5); more wait their turn.

Files:

  state.py                     RagState: the data passed between the nodes
  nodes/guard.py               the guard node and its rules (Step 0)
  nodes/retrieve.py            the retrieve node and its steps (Steps 1-3)
  nodes/generate_answer.py     the generate_answer node and its steps (Steps 4-6)
  prompts/generate_answer_prompt.py
                               the system prompt, the user prompt templates and the
                               "Sources:" list format of generate_answer
  graph/rag_graph.py           the graph builder: build_rag_graph(), called once at
                               startup (app.py)
  llm_chat.py                  the service the API calls: llm_chat() runs the graph
                               for one question

Calls: POST /api/user-support (api/user_support.py) -> llm_chat() -> the RAG graph.
"""
