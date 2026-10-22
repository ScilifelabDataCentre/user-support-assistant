"""generate_answer node of the RAG graph: Steps 4-6 (see the steps in
ai_agents/__init__.py).

One function per step, then the node that runs them in order. The node takes the
RagState (state.py) and returns the keys it adds; it also takes the API client it
needs, which graph/rag_graph.py binds when it adds the node.
"""

import re

import config
from ai_agents.prompts.generate_answer_prompt import (
    CHUNK_TEMPLATE,
    SOURCE_LINE_TEMPLATE,
    SOURCES_HEADER,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)

# Retries of a failed LLM request; the openai client waits between them with
# exponential backoff (Step 5). Few, because the user is waiting.
MAX_RETRIES = 2
# Seconds before an LLM request is given up (Step 5)
LLM_TIMEOUT = 120.0
# Low temperature: answers stay close to the documentation (Step 5)
TEMPERATURE = 0.2
# Reasoning that some models (e.g. Qwen3) write before the answer; removed (Step 5)
THINK_RE = re.compile(r"<think>.*?</think>", re.S)
# A citation in the answer, with the spaces before it: " [1]", or several numbers in
# one bracket like " [1, 3]". Not right after a letter or digit, so code like x[1] is
# not a citation (Step 6)
CITATION_RE = re.compile(r"[ \t]*(?<!\w)\[(\d+(?:\s*,\s*\d+)*)\]")
# Chunk fields returned as a source's metadata, besides its new number (Step 6)
SOURCE_FIELDS = ("page_title", "headings", "section_url", "source_url", "type")


# ---------------------------- Step 4: build prompt ---------------------------

def build_prompt(question, chunks):
    """Step 4: the chat messages: the system prompt, then the numbered chunks and the
    question."""
    chunk_texts = []
    for chunk in chunks:
        chunk_text = CHUNK_TEMPLATE.format(
            number=chunk["number"],
            title=chunk["title"],
            url=chunk["section_url"],
            text=chunk["text"],
        )
        chunk_texts.append(chunk_text)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        chunks="\n\n---\n\n".join(chunk_texts),
        question=question,
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    return messages


# ----------------------------- Step 5: call the LLM --------------------------

def call_llm(messages, openai_client):
    """Step 5: ask LLM_MODEL for the answer; remove any <think> reasoning from it."""
    client = openai_client.with_options(max_retries=MAX_RETRIES, timeout=LLM_TIMEOUT)
    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
        temperature=TEMPERATURE,
    )
    content = response.choices[0].message.content or ""
    answer = THINK_RE.sub("", content).strip()
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


def add_sources(answer, chunks):
    """Step 6: keep the chunks the answer cites as its sources (metadata only),
    renumbered 1..n in fused order; remove the [n] citations from the answer and
    append the sources to it as a "Sources:" list; return (answer, sources).
    Nothing cited: no sources, no "Sources:" list."""
    cited = cited_numbers(answer)
    answer = remove_citations(answer)

    sources = []
    source_lines = []
    for chunk in chunks:
        if chunk["number"] not in cited:
            continue
        number = len(sources) + 1
        source = {"number": number}
        for field in SOURCE_FIELDS:
            source[field] = chunk[field]
        sources.append(source)
        source_line = SOURCE_LINE_TEMPLATE.format(
            number=number,
            title=chunk["title"],
            url=chunk["section_url"],
        )
        source_lines.append(source_line)

    if not sources:
        return answer, sources
    answer = answer + "\n\n" + SOURCES_HEADER + "\n" + "\n".join(source_lines)
    return answer, sources


# ------------------------------------ Node -----------------------------------

def generate_answer(state, openai_client):
    """Node: Steps 4-6, answer the question from the chunks, with its sources."""
    # Step 4. Build the prompt
    messages = build_prompt(state["question"], state["chunks"])

    # Step 5. Call the LLM
    answer = call_llm(messages, openai_client)

    # Step 6. Add sources
    answer, sources = add_sources(answer, state["chunks"])
    return {"answer": answer, "sources": sources}
