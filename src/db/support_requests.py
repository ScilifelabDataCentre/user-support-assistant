"""support_requests table: one row per question to POST /api/user-support.

  Step 1. Create the table: run schema.sql at startup (see app.py); it only creates
          what does not exist yet, so existing rows are kept.
  Step 2. Save a request: insert one row with the question, what the RAG graph did
          with it and the suggested response (called by ai_agents/llm_chat.py).

Every function takes the app's async connection pool (core/clients.py postgres_pool)
and is async, so a slow database never blocks the other requests.
"""

from pathlib import Path

from psycopg.types.json import Jsonb

SCHEMA_FILE = Path(__file__).with_name("schema.sql")

INSERT_SQL = """
    INSERT INTO support_requests
        (ticket_id, user_request, guardrail_blocked, rewritten_query, retrieved_chunks, suggested_response)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id
"""


# ---------------------------- Step 1: create the table -----------------------

async def create_table(pool):
    """Step 1: create the tables and indexes in schema.sql that do not exist yet."""
    schema = SCHEMA_FILE.read_text(encoding="utf-8")
    # Leaving the block commits the transaction
    async with pool.connection() as conn:
        await conn.execute(schema)


# ---------------------------- Step 2: save a request -------------------------

async def save_request(pool, ticket_id, user_request, guardrail_blocked, rewritten_query,
                       retrieved_chunks, suggested_response):
    """Step 2: insert one request; return the new row's id. retrieved_chunks is a list
    of dicts (stored as JSONB), or None if the question was blocked."""
    chunks_json = None
    if retrieved_chunks is not None:
        chunks_json = Jsonb(retrieved_chunks)
    values = (ticket_id, user_request, guardrail_blocked, rewritten_query, chunks_json, suggested_response)
    async with pool.connection() as conn:
        cur = await conn.execute(INSERT_SQL, values)
        row = await cur.fetchone()
    return row[0]
