-- Tables of the Postgres database (POSTGRES_DB in dev.env).
-- Run at every startup by db/support_requests.py create_table(), so each statement
-- must be safe to run again (IF NOT EXISTS).

-- One row per question to POST /api/user-support: the request, what the RAG graph did
-- with it and the suggested response.
CREATE TABLE IF NOT EXISTS support_requests (
    id                 BIGSERIAL PRIMARY KEY,
    -- Ticket ID from the ticketing system (NULL if the caller sent none)
    ticket_id          TEXT,
    -- Original user question
    user_request       TEXT NOT NULL,
    -- true if the guard blocked the question
    guardrail_blocked  BOOLEAN NOT NULL,
    -- Query after rewriting (NULL if blocked, or while there is no rewriter)
    rewritten_query    TEXT,
    -- All chunks given to the LLM with the prompt, best first: an array of {rank,
    -- score, page_title, headings, section_url, source_url, type, content}
    -- (NULL if blocked). A copy of the text, not Qdrant ids: a redeploy rebuilds the
    -- collection.
    retrieved_chunks   JSONB,
    -- Generated response, or the refusal if blocked
    suggested_response TEXT NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Find the records of one ticket
CREATE INDEX IF NOT EXISTS support_requests_ticket_id_idx ON support_requests (ticket_id);
