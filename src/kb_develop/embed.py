"""Embed the chunks for the knowledge base.

embed_chunks() sends each chunk's "text" (heading path + content, see chunk.py Rule 6)
to EMBEDDING_MODEL through the OpenAI-compatible API, BATCH_SIZE chunks per request,
and returns the chunks with their vector added as "vector".

A request that fails with a temporary error (connection, timeout, rate limit, 5xx) is
retried up to MAX_RETRIES times with exponential backoff; other errors (e.g. a wrong
API key) are raised at once.

The async API client (AsyncOpenAI) is created by the caller (clients.openai_client())
and passed in; the model name comes from config.py. The requests and the waits
between retries are awaited, so the event loop serves other requests meanwhile.
"""

import asyncio
import logging
import random

import openai

import config

logger = logging.getLogger(__name__)

# Chunks per API request
BATCH_SIZE = 32
# Retries per request; the waits are about 1, 2, 4, 8, 16, 32, 59 seconds (~2 min in total)
MAX_RETRIES = 7
# Seconds before the first retry; doubled for each next retry
BASE_DELAY = 1.0
# Longest wait between two retries, in seconds (jitter included)
MAX_DELAY = 60.0
# Temporary errors worth retrying
RETRYABLE_ERRORS = (openai.APIConnectionError, openai.RateLimitError, openai.InternalServerError)


async def request_with_retry(client, batch):
    """Send one embeddings request for a batch of texts, retried with exponential
    backoff on temporary errors. The wait is BASE_DELAY * 2^attempt plus up to 1 s of
    random jitter, at most MAX_DELAY; after MAX_RETRIES failed retries the error is raised."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await client.embeddings.create(model=config.EMBEDDING_MODEL, input=batch)
        except RETRYABLE_ERRORS as e:
            if attempt == MAX_RETRIES:
                raise
            delay = BASE_DELAY * 2 ** attempt + random.uniform(0, 1)
            delay = min(delay, MAX_DELAY)
            logger.warning("Embedding request failed (%s), retry %d/%d in %.1fs",
                           type(e).__name__, attempt + 1, MAX_RETRIES, delay)
            await asyncio.sleep(delay)


async def embed_texts(client, texts):
    """Return one vector per text, in the same order as texts."""
    config.require("EMBEDDING_MODEL")
    vectors = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start:start + BATCH_SIZE]
        response = await request_with_retry(client, batch)

        # Sort the results by index, so each vector matches its input text.
        results = sorted(response.data, key=lambda result: result.index)
        for result in results:
            vectors.append(result.embedding)
        logger.info("Embedded %d/%d", len(vectors), len(texts))
    return vectors


async def embed_chunks(client, chunks):
    """Return a copy of every chunk with its vector added as "vector"."""
    texts = []
    for chunk in chunks:
        texts.append(chunk["text"])

    vectors = await embed_texts(client, texts)

    embedded_chunks = []
    for chunk, vector in zip(chunks, vectors):
        embedded_chunk = dict(chunk)
        embedded_chunk["vector"] = vector
        embedded_chunks.append(embedded_chunk)
    return embedded_chunks
