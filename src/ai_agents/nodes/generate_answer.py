"""generate_answer node of the RAG graph: Steps 4-6 (see the steps in
graph/rag_graph.py).

One function per step, then the node that runs them in order. The node takes the
RagState (state.py) and returns the keys it adds; it also takes the async API client
and the semaphore it needs, which graph/rag_graph.py binds when it adds the node.
Step 5 is async (it waits on the network); Steps 4 and 6 only compute.
"""

import logging
import re
import time

from ai_agents.prompts.generate_answer_prompt import (
    CHUNK_SEPARATOR,
    NO_CHUNKS,
    SERVE_DOCS_CHUNK_TEMPLATE,
    SERVE_DOCS_SOURCE_LINE_TEMPLATE,
    SOURCES_HEADER,
    SYSTEM_PROMPT,
    TICKET_CHUNK_TEMPLATE,
    TICKET_SOURCE_LINE_TEMPLATE,
    USER_PROMPT_TEMPLATE,
)
from ai_agents.nodes.retrieve import CHUNK_METADATA_FIELDS, SERVE_DOCS
from core import config

logger = logging.getLogger(__name__)

# Retries of a failed LLM request; the openai client waits between them with
# exponential backoff. Few, because the user is waiting.
MAX_RETRIES = 2
# Seconds before an LLM request is given up
LLM_TIMEOUT = 120.0
# Low temperature: answers stay close to the chunks
TEMPERATURE = 0.2
# Reasoning that some models (e.g. Qwen3) write before the answer; removed
THINK_RE = re.compile(r"<think>.*?</think>", re.S)
# A citation in the answer, with the spaces before it: " [1]", or several numbers in
# one bracket like " [1, 3]". Not right after a letter or digit, so code like x[1] is
# not a citation
CITATION_RE = re.compile(r"[ \t]*(?<!\w)\[(\d+(?:\s*,\s*\d+)*)\]")


# ---------------------------- Step 4: build prompt ---------------------------

def format_chunk(chunk):
    """Step 4: one chunk as it is written in the user message: its number and title
    (a Serve docs chunk also its link), then its text."""
    if chunk["source"] == SERVE_DOCS:
        return SERVE_DOCS_CHUNK_TEMPLATE.format(
            number=chunk["number"],
            title=chunk["title"],
            url=chunk["section_url"],
            text=chunk["text"],
        )
    return TICKET_CHUNK_TEMPLATE.format(
        number=chunk["number"],
        title=chunk["title"],
        text=chunk["text"],
    )


def join_chunks(chunk_texts):
    """Step 4: the chunks of one section of the user message, or NO_CHUNKS if the
    section has none."""
    if not chunk_texts:
        return NO_CHUNKS
    return CHUNK_SEPARATOR.join(chunk_texts)


def build_prompt(question, chunks):
    """Step 4: the chat messages: the system prompt, then the numbered chunks (the
    Serve docs chunks and the history tickets in separate sections) and the question."""
    serve_docs_texts = []
    ticket_texts = []
    for chunk in chunks:
        chunk_text = format_chunk(chunk)
        if chunk["source"] == SERVE_DOCS:
            serve_docs_texts.append(chunk_text)
        else:
            ticket_texts.append(chunk_text)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        serve_docs_chunks=join_chunks(serve_docs_texts),
        ticket_chunks=join_chunks(ticket_texts),
        question=question,
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    return messages


# ----------------------------- Step 5: call the LLM --------------------------

async def call_llm(messages, openai_client, openllm_semaphore):
    """Step 5: ask LLM_MODEL for the answer; remove any <think> reasoning from it."""
    client = openai_client.with_options(max_retries=MAX_RETRIES, timeout=LLM_TIMEOUT)
    async with openllm_semaphore:
        start = time.perf_counter()
        response = await client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            temperature=TEMPERATURE,
        )
        elapsed = time.perf_counter() - start
    content = response.choices[0].message.content or ""
    answer = THINK_RE.sub("", content).strip()
    logger.info("LLM answered in %.1fs (%d chars)", elapsed, len(answer))
    return answer


# ----------------------------- Step 6: add sources ---------------------------

def cited_numbers(answer):
    """Step 6: the chunk numbers the answer cites, e.g. {1, 3} for "... [1] ... [1, 3]"."""
    numbers = set()
    for match in CITATION_RE.finditer(answer):
        for number in match.group(1).split(","):
            numbers.add(int(number))
    return numbers


def remove_citations(answer):
    """Step 6: the answer without its [n] citations; the user sees only the "Sources:"
    list."""
    return CITATION_RE.sub("", answer)


def format_source_line(chunk, number):
    """Step 6: one line of the "Sources:" list: the source's new number and the
    chunk's title; a Serve docs chunk also its link. A history ticket has no link:
    its title names the ticket ID, subject and subcategory."""
    if chunk["source"] == SERVE_DOCS:
        return SERVE_DOCS_SOURCE_LINE_TEMPLATE.format(
            number=number,
            title=chunk["title"],
            url=chunk["section_url"],
        )
    return TICKET_SOURCE_LINE_TEMPLATE.format(number=number, title=chunk["title"])


def add_sources(answer, chunks):
    """Step 6: keep the chunks the answer cites as its sources (metadata only),
    renumbered 1..n in chunk order (Serve docs first, then history tickets); remove
    the [n] citations from the answer and append the sources to it as a "Sources:"
    list; return (answer, sources). Nothing cited: no sources, no "Sources:" list."""
    cited = cited_numbers(answer)
    logger.info("Answer cites chunks %s", sorted(cited))
    answer = remove_citations(answer)

    sources = []
    source_lines = []
    for chunk in chunks:
        if chunk["number"] not in cited:
            continue
        number = len(sources) + 1
        source = {"number": number, "source": chunk["source"]}
        for field in CHUNK_METADATA_FIELDS[chunk["source"]]:
            source[field] = chunk[field]
        sources.append(source)
        source_lines.append(format_source_line(chunk, number))
        if chunk["source"] == SERVE_DOCS:
            headings = " > ".join(chunk["headings"])
            logger.info("Source [%d] = chunk [%d]: Serve docs: %s | %s", number, chunk["number"],
                        chunk["page_title"], headings)
        else:
            logger.info("Source [%d] = chunk [%d]: Ticket: %s", number, chunk["number"],
                        chunk["incident_id"])

    if not sources:
        logger.warning("Answer cites no chunks: no sources")
        return answer, sources
    answer = answer + "\n\n" + SOURCES_HEADER + "\n" + "\n".join(source_lines)
    return answer, sources


# ------------------------------------ Node -----------------------------------

async def generate_answer(state, openai_client, openllm_semaphore):
    """Node: Steps 4-6, answer the question from the chunks, with its sources."""
    # Step 4. Build the prompt
    logger.info("Step 4: build the prompt (%d chunks)", len(state["chunks"]))
    messages = build_prompt(state["question"], state["chunks"])
    if config.SHOW_PROMPT:
        for message in messages:
            logger.info("Prompt (%s):\n%s", message["role"], message["content"])

    # Step 5. Call the LLM
    logger.info("Step 5: call the LLM (%s)", config.LLM_MODEL)
    answer = await call_llm(messages, openai_client, openllm_semaphore)

    # Step 6. Add sources
    logger.info("Step 6: add sources")
    answer, sources = add_sources(answer, state["chunks"])
    return {"answer": answer, "sources": sources}
