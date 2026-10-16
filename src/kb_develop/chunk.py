"""Split the crawled markdown pages into chunks for the knowledge base.

Chunking rules (each function below says which rule it implements):

  Rule 1. Clean the page: drop wiki macros ([image:..], [article_list ..]) and <img>
          tags, turn <a href> tags into markdown links.
  Rule 2. One chunk per heading section (##, ###, ####), keeping its heading path.
          '#' lines inside code blocks are comments, not headings.
  Rule 3. FAQ sections: one chunk per question + answer.
  Rule 4. Sections shorter than MIN_CHARS are merged into the next section, or into the
          previous one if the next is too big. FAQ items are never merged.
  Rule 5. Sections longer than MAX_CHARS are split between paragraphs. Code blocks are
          never cut, and a lead-in line ending with ":" stays with what it introduces.
  Rule 6. Each chunk's text starts with the page breadcrumb and heading path, e.g.
          "Application hosting > Shiny app hosting > Step-by-step guide > Step 2. ...",
          and the chunk links to its section on the site (section_url).

chunk_pages() applies Rules 1-6 to all pages and returns one list of chunks.
"""

import re
import uuid
from dataclasses import dataclass

# Longest section kept whole, ~750 tokens (Rule 5)
MAX_CHARS = 3000
# Sections shorter than this are merged into a neighbour (Rule 4)
MIN_CHARS = 300

# Start or end of a fenced code block: ``` or ~~~
FENCE_RE = re.compile(r"^ {0,3}(```|~~~)")
# A markdown heading: "## Title"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
# **bold** or __bold__, removed from heading titles
EMPHASIS_RE = re.compile(r"(?:\*\*|__)(.+?)(?:\*\*|__)")
# FAQ questions are whole bold lines: "**Can I ...?**"
QUESTION_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
FAQ_HEADING_RE = re.compile(r"frequently asked questions|\bfaq\b", re.I)
# Wiki macros that only render on the site, e.g. [image:5 size:large]
MACRO_RE = re.compile(r"^[ \t]*\[(?:image|article_list)\b[^\]\n]*\][ \t]*$", re.M)
IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
A_RE = re.compile(r"<a\b[^>]*?\bhref=\"([^\"]*)\"[^>]*>(.*?)</a>", re.I | re.S)


@dataclass
class Section:
    # Heading path, e.g. ["Step-by-step guide", "Step 1. ..."]
    headings: list
    # Markdown level of the last heading (0 = page intro, before any heading)
    level: int
    # Markdown body, without its own heading line
    text: str
    # True for one FAQ question + answer
    faq: bool = False


# ------------------------------- Rule 1: clean -------------------------------

def a_tag_to_link(m):
    """Rule 1: <a href="url">text</a> -> [text](url); a link without text is dropped."""
    url = m.group(1)
    text = m.group(2).strip()
    if not text:
        return ""
    return f"[{text}]({url})"


def clean(md):
    """Rule 1: drop wiki macros and <img> tags, turn <a href> tags into markdown links."""
    md = IMG_RE.sub("", md)
    md = A_RE.sub(a_tag_to_link, md)
    md = MACRO_RE.sub("", md)

    # Remove trailing spaces, then collapse runs of blank lines.
    lines = []
    for line in md.split("\n"):
        lines.append(line.rstrip())
    md = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", md).strip()


def iter_lines(md):
    """Helper for Rules 2, 3, 5: yield (line, in_code), where in_code is True for
    the lines of a fenced code block, fences included."""
    in_code = False
    for line in md.split("\n"):
        if FENCE_RE.match(line):
            yield line, True
            in_code = not in_code
        else:
            yield line, in_code


# ------------------------- Rule 2: split by headings -------------------------

def split_by_headings(md):
    """Rule 2: split a page into sections at its headings, ignoring '#' in code blocks."""
    sections = []
    # Headings above the current line, e.g. [(2, "Step-by-step guide"), (3, "Step 1. ...")]
    heading_stack = []
    # Body lines of the current section
    body_lines = []

    def close_section():
        text = "\n".join(body_lines).strip()
        body_lines.clear()
        if not text and not heading_stack:
            return
        headings = []
        for _, title in heading_stack:
            headings.append(title)
        if heading_stack:
            level = heading_stack[-1][0]
        else:
            level = 0
        sections.append(Section(headings, level, text))

    for line, in_code in iter_lines(md):
        heading = None
        if not in_code:
            heading = HEADING_RE.match(line)
        if heading is None:
            body_lines.append(line)
            continue

        # A new heading: close the current section, then update the heading path.
        close_section()
        level = len(heading.group(1))
        title = EMPHASIS_RE.sub(r"\1", heading.group(2))
        # Drop headings at the same or a deeper level; they are siblings, not parents.
        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        heading_stack.append((level, title))
    close_section()
    return sections


# ----------------------------- Rule 3: FAQ items -----------------------------

def split_faq(sections):
    """Rule 3: one section per FAQ question + answer.
    Most pages write questions as bold lines under the FAQ heading (split here);
    some give each question its own heading (already split by Rule 2, only marked)."""
    result = []
    for section in sections:
        # An FAQ section: split it at its bold questions.
        if section.headings and FAQ_HEADING_RE.search(section.headings[-1]):
            result.extend(split_bold_questions(section))
            continue
        # A heading directly under an FAQ heading is a question.
        if len(section.headings) > 1 and FAQ_HEADING_RE.search(section.headings[-2]):
            section.faq = True
        result.append(section)
    return result


def split_bold_questions(section):
    """Rule 3: split an FAQ section at its bold question lines."""
    items = []
    question = None
    answer_lines = []

    def close_item():
        text = "\n".join(answer_lines).strip()
        answer_lines.clear()
        if question:
            items.append(Section(section.headings + [question], section.level, text, faq=True))
        elif text:
            # Text before the first question: keep it as a normal section.
            items.append(Section(section.headings, section.level, text))

    for line, in_code in iter_lines(section.text):
        match = None
        if not in_code:
            match = QUESTION_RE.match(line)
        if match:
            close_item()
            question = match.group(1).strip()
        else:
            answer_lines.append(line)
    close_item()
    return items


# ------------------------- Rule 4: merge small ones --------------------------

def can_merge(target, section):
    """Rule 4: FAQ items are never merged, and the result must fit in MAX_CHARS."""
    if target.faq or section.faq:
        return False
    return len(target.text) + len(section.text) <= MAX_CHARS


def merge(target, section):
    """Rule 4: append section, with its heading line, to target."""
    heading_line = "#" * section.level + " " + section.headings[-1]
    target.text = f"{target.text}\n\n{heading_line}\n\n{section.text}".strip()


def merge_small(sections):
    """Rule 4: merge sections shorter than MIN_CHARS into a neighbour (FAQ items stay)."""
    # 4a. A small section takes in the next one.
    merged = []
    for section in sections:
        if merged and len(merged[-1].text) < MIN_CHARS and can_merge(merged[-1], section):
            merge(merged[-1], section)
        else:
            merged.append(section)

    # 4b. Still small (the next was too big, or it is the last one): into the previous one.
    result = []
    for section in merged:
        if result and len(section.text) < MIN_CHARS and can_merge(result[-1], section):
            merge(result[-1], section)
        else:
            result.append(section)
    return result


# -------------------------- Rule 5: split long ones --------------------------

def split_paragraphs(text):
    """Rule 5 helper: paragraphs separated by blank lines; a code block is one paragraph."""
    paragraphs = []
    lines = []
    for line, in_code in iter_lines(text):
        if line.strip() or in_code:
            lines.append(line)
        elif lines:
            paragraphs.append("\n".join(lines))
            lines = []
    if lines:
        paragraphs.append("\n".join(lines))
    return paragraphs


def split_long(text):
    """Rule 5: split text longer than MAX_CHARS between paragraphs, never inside a code
    block (a single paragraph or code block longer than MAX_CHARS is kept whole)."""
    if len(text) <= MAX_CHARS:
        return [text]

    parts = []
    # Paragraphs of the part being built
    current = []
    for paragraph in split_paragraphs(text):
        if current and len("\n\n".join(current + [paragraph])) > MAX_CHARS:
            # Keep a lead-in like "insert the code below:" with what it introduces.
            carry = []
            if len(current) > 1 and current[-1].endswith(":"):
                carry.append(current.pop())
            parts.append("\n\n".join(current))
            current = carry
        current.append(paragraph)
    parts.append("\n\n".join(current))
    return parts


# --------------------- Rule 6: context header and links ----------------------

def slugify(text):
    """Rule 6: anchor of a heading on the site (#wiki-toc-<slug>)."""
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def make_chunk(section, text, part, n_parts, page):
    """Rule 6: build one chunk: the text prefixed with breadcrumb + heading path,
    plus metadata and a link to the section on the site."""
    url = page["url"]
    crumbs = page["breadcrumb"]

    # The heading to link to. FAQ questions are not anchors on the site,
    # so an FAQ item links to the FAQ heading.
    if section.faq:
        anchor = section.headings[-2]
    elif section.headings:
        anchor = section.headings[-1]
    else:
        anchor = None
    if anchor:
        section_url = f"{url}#wiki-toc-{slugify(anchor)}"
    else:
        section_url = url

    # Only number the parts when a section was split by Rule 5.
    if n_parts == 1:
        part = None

    header = " > ".join(crumbs + section.headings)
    return {
        "page_title": crumbs[-1],
        "breadcrumb": crumbs,
        "headings": section.headings,
        "type": "faq" if section.faq else "section",
        "part": part,
        "source_url": url,
        "section_url": section_url,
        "content": text,
        "text": f"{header}\n\n{text}".strip(),
    }


# --------------------------------- pipeline ----------------------------------

def chunk_page(page):
    """Apply Rules 1-6 to one crawled page ({"url", "breadcrumb", "markdown"})
    and return its chunks."""
    # Rule 1. Clean
    markdown = clean(page["markdown"])
    # Rule 2. Split by headings
    sections = split_by_headings(markdown)
    # Rule 3. FAQ items
    sections = split_faq(sections)
    # Rule 4. Merge small sections
    sections = merge_small(sections)

    chunks = []
    for section in sections:
        # Skip a bare heading that could not be merged.
        if not section.text and not section.faq:
            continue
        # Rule 5. Split long sections
        parts = split_long(section.text)
        # Rule 6. One chunk per part, with its context header and link
        for i, text in enumerate(parts):
            chunks.append(make_chunk(section, text, i, len(parts), page))

    # Number the chunks within the page; the id stays the same as long as the page
    # URL and the chunk's position do not change.
    for i, chunk in enumerate(chunks):
        chunk["chunk_index"] = i
        chunk["id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{page['url']}#{i}"))
        chunk["n_chars"] = len(chunk["text"])
    return chunks


def chunk_pages(pages):
    """Apply Rules 1-6 to every crawled page and return all chunks in one list."""
    all_chunks = []
    for page in pages:
        page_chunks = chunk_page(page)
        all_chunks.extend(page_chunks)
    return all_chunks
