"""Embed the chunks for the knowledge base (shared by the Serve docs and the history tickets).

embed_chunks() sends each chunk's "text" to EMBEDDING_MODEL through the OpenAI-compatible
API, BATCH_SIZE chunks per request, and returns the chunks with their vector added as
"vector".

Two kinds of failed requests are handled:

  Temporary errors (connection, timeout, rate limit, 5xx): the request is retried up to
    MAX_RETRIES times with exponential backoff.
  Text too long: the model takes at most 8192 tokens per text and refuses a longer one
    with an error (it does not cut the text itself). One too long text fails its whole
    batch, and the error does not say which text it was, so the texts of that batch are
    then sent one by one. A text that is still refused is cut to SHORTEN_RATIO (90%) of
    its length and sent again, up to MAX_SHORTEN_RETRIES times. The chunk's "text" is
    then replaced by the shortened text that was embedded, and "truncated" is set to
    True; its "content" stays whole.

Other errors (e.g. a wrong API key) are raised at once.

The async API client (AsyncOpenAI) is created by the caller (core.clients.openai_client())
and passed in; the model name comes from core/config.py. The requests and the waits
between retries are awaited, so the event loop serves other requests meanwhile.
"""

import asyncio
import logging
import random

import openai

from core import config

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

# Part of a too long text that is kept for the next try
SHORTEN_RATIO = 0.9
# Times a too long text is shortened; after 5 times about 59% of it is left
MAX_SHORTEN_RETRIES = 5
# How the API says that a text is too long: a 400 error with this in its message, e.g.
# "This model's maximum context length is 8192 tokens. However, your prompt contains ..."
TOO_LONG_MESSAGE = "maximum context length"


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


def is_too_long_error(error):
    """True if the API refused the request because a text has more tokens than the
    model takes."""
    return TOO_LONG_MESSAGE in str(error)


async def embed_batch(client, batch):
    """Return one vector per text of the batch, in the same order, from one request.
    Raises openai.BadRequestError if a text of the batch is too long."""
    response = await request_with_retry(client, batch)

    # Sort the results by index, so each vector matches its input text.
    results = sorted(response.data, key=lambda result: result.index)
    vectors = []
    for result in results:
        vectors.append(result.embedding)
    return vectors


async def embed_one_shortened(client, text):
    """Embed one text on its own. While the model refuses it as too long, cut it to
    SHORTEN_RATIO of its length and send it again, up to MAX_SHORTEN_RETRIES times.
    Return (vector, embedded_text), where embedded_text is the text that was embedded:
    the given text, or what is left of it."""
    # Start of the first line of the text, to name it in the log (a ticket's ID, a docs
    # page's heading path)
    first_line = text.split("\n")[0][:100]

    for attempt in range(MAX_SHORTEN_RETRIES + 1):
        try:
            vectors = await embed_batch(client, [text])
            return vectors[0], text
        except openai.BadRequestError as e:
            if not is_too_long_error(e):
                raise
            if attempt == MAX_SHORTEN_RETRIES:
                logger.error("Text is still too long for %s at %d chars, after shortening it %d times: %s",
                             config.EMBEDDING_MODEL, len(text), MAX_SHORTEN_RETRIES, first_line)
                raise
            new_length = int(len(text) * SHORTEN_RATIO)
            logger.warning("Text too long for %s, shortening %d/%d: %d -> %d chars: %s",
                           config.EMBEDDING_MODEL, attempt + 1, MAX_SHORTEN_RETRIES,
                           len(text), new_length, first_line)
            text = text[:new_length]


async def embed_texts(client, texts):
    """Return (vectors, embedded_texts): one vector per text, in the same order as
    texts, and the text each vector was made from (shortened if it was too long)."""
    config.require("EMBEDDING_MODEL")
    vectors = []
    embedded_texts = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start:start + BATCH_SIZE]
        try:
            # The usual case: the whole batch in one request.
            batch_vectors = await embed_batch(client, batch)
            vectors.extend(batch_vectors)
            embedded_texts.extend(batch)
        except openai.BadRequestError as e:
            if not is_too_long_error(e):
                raise
            # A text of this batch is too long, and the error does not say which one:
            # send the texts of this batch one by one, shortening the too long ones.
            logger.warning("A text in this batch is too long for %s; sending its %d texts one by one",
                           config.EMBEDDING_MODEL, len(batch))
            for text in batch:
                vector, embedded_text = await embed_one_shortened(client, text)
                vectors.append(vector)
                embedded_texts.append(embedded_text)
        logger.info("Embedded %d/%d", len(vectors), len(texts))
    return vectors, embedded_texts


async def embed_chunks(client, chunks):
    """Return a copy of every chunk with its vector added as "vector". A chunk whose
    text was shortened to fit the model gets the shortened text as "text" and
    "truncated" set to True."""
    texts = []
    for chunk in chunks:
        texts.append(chunk["text"])

    vectors, embedded_texts = await embed_texts(client, texts)

    embedded_chunks = []
    for chunk, vector, embedded_text in zip(chunks, vectors, embedded_texts):
        embedded_chunk = dict(chunk)
        embedded_chunk["vector"] = vector
        if embedded_text != chunk["text"]:
            embedded_chunk["text"] = embedded_text
            embedded_chunk["truncated"] = True
        embedded_chunks.append(embedded_chunk)
    return embedded_chunks
