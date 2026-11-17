"""Prompts and the "Sources:" list format of the generate_answer node
(used by nodes/generate_answer.py).

The prompt as the LLM sees it: two chat messages, the system message (SYSTEM_PROMPT,
the first block) and then the user message (USER_PROMPT_TEMPLATE, the second block).

    You are the user support assistant of SciLifeLab Serve, ...

    Answer the user's question using only the chunks in the user message. ...

    Rules:
    - Always answer in English, ...
    - ...

    Documentation chunks:

    [1] <breadcrumb> > <headings>
    Link: <section_url>

    <docs chunk text>

    ---

    [2] ...

    ===

    Past support tickets:

    [6] Ticket <incident_id>: <subject> (<subcategory>)

    <ticket text: header, then every email>

    ---

    [7] ...

    ===

    Question: <the user's question>

Chunks are separated by "---" (CHUNK_SEPARATOR), the sections and the question by
"===", so the end of a long ticket is not taken for the question. A section with no
chunks says NO_CHUNKS instead.
"""

# The rules the LLM follows for every answer.
# TODO: say which source wins when the documentation and a past ticket disagree (e.g.
#  the documentation, because a ticket can be out of date). Now the prompt gives no
#  rule, so the LLM decides by itself.
SYSTEM_PROMPT = """\
You are the user support assistant of SciLifeLab Serve, a platform for hosting \
applications, models and other services for life science research.

Answer the user's question using only the chunks in the user message. There are two \
kinds of chunks: documentation chunks, from the SciLifeLab Serve documentation, and \
past support tickets, which are earlier e-mail conversations between users and the \
SciLifeLab Serve support team.

Rules:
- Always answer in English, whatever language the question is in.
- Use only the information in the chunks. Do not add facts, steps, settings or \
links that are not in them.
- Cite the chunks you use with their numbers in square brackets, e.g. [1] or [2][3], \
right after the sentences they support.
- If the chunks do not answer the question, say that you could not find the answer \
and suggest contacting the SciLifeLab Serve team. Do not guess.
- The past support tickets are anonymised: names, e-mail addresses and other personal \
details are replaced by placeholders. Never copy a placeholder or a personal detail \
into the answer, and do not mention the people in the tickets or that another user \
had the same problem; give only the solution.
- Be concise. Use numbered steps for procedures, and keep code, commands, field names \
and button labels exactly as they are in the chunks."""

# One documentation chunk in the user message.
SERVE_DOCS_CHUNK_TEMPLATE = """\
[{number}] {title}
Link: {url}

{text}"""

# One past support ticket in the user message.
TICKET_CHUNK_TEMPLATE = """\
[{number}] {title}

{text}"""

# Between two chunks of a section of the user message.
CHUNK_SEPARATOR = "\n\n---\n\n"

# In a section of the user message that has no chunks.
NO_CHUNKS = "(none found)"

# The user message: the numbered chunks of both sources, then the question.
USER_PROMPT_TEMPLATE = """\
Documentation chunks:

{serve_docs_chunks}

===

Past support tickets:

{ticket_chunks}

===

Question: {question}"""

# The list of cited chunks appended to the answer (the [n] citations are
# removed from the answer; the sources are renumbered 1..n), e.g.
#   Sources:
#   [1] Application hosting > Shiny app hosting > Step 6. Create an app: https://...
#   [2] Ticket KTH-INC-4492487: App fails to start after update (Shiny)
SOURCES_HEADER = "Sources:"
SERVE_DOCS_SOURCE_LINE_TEMPLATE = "[{number}] {title}: {url}"
TICKET_SOURCE_LINE_TEMPLATE = "[{number}] {title}"
