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
"""

import argparse
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

MAX_CHARS = 3000  # ~750 tokens (Rule 5)
MIN_CHARS = 300  # (Rule 4)

RUN_DIR_RE = re.compile(r"^\d{8}-\d{6}$")  # output/yyyymmdd-hhmmss/
FENCE_RE = re.compile(r"^ {0,3}(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
EMPHASIS_RE = re.compile(r"(?:\*\*|__)(.+?)(?:\*\*|__)")
QUESTION_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")  # FAQ questions are bold lines
FAQ_HEADING_RE = re.compile(r"frequently asked questions|\bfaq\b", re.I)
MACRO_RE = re.compile(r"^[ \t]*\[(?:image|article_list)\b[^\]\n]*\][ \t]*$", re.M)
IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
A_RE = re.compile(r"<a\b[^>]*?\bhref=\"([^\"]*)\"[^>]*>(.*?)</a>", re.I | re.S)


@dataclass
class Section:
    headings: list  # heading path, e.g. ["Step-by-step guide", "Step 1. ..."]
    level: int  # markdown level of the last heading (0 = page intro)
    text: str  # markdown body, without its own heading line
    faq: bool = False


# ------------------------------- Rule 1: clean -------------------------------

def clean(md):
    """Rule 1: drop wiki macros and <img> tags, turn <a href> tags into markdown links."""
    md = IMG_RE.sub("", md)
    md = A_RE.sub(lambda m: f"[{m.group(2).strip()}]({m.group(1)})" if m.group(2).strip() else "", md)
    md = MACRO_RE.sub("", md)
    md = "\n".join(line.rstrip() for line in md.split("\n"))
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
    sections, path, lines = [], [], []  # path: [(level, title)] of the current section

    def close_section():
        text = "\n".join(lines).strip()
        if text or path:
            sections.append(Section([t for _, t in path], path[-1][0] if path else 0, text))
        lines.clear()

    for line, in_code in iter_lines(md):
        m = None if in_code else HEADING_RE.match(line)
        if not m:
            lines.append(line)
            continue
        close_section()
        level = len(m.group(1))
        while path and path[-1][0] >= level:
            path.pop()
        path.append((level, EMPHASIS_RE.sub(r"\1", m.group(2))))
    close_section()
    return sections


# ----------------------------- Rule 3: FAQ items -----------------------------

def split_faq(sections):
    """Rule 3: one section per FAQ question + answer.
    Most pages write questions as bold lines under the FAQ heading (split here);
    some give each question its own heading (already split by Rule 2, only marked)."""
    out = []
    for s in sections:
        if s.headings and FAQ_HEADING_RE.search(s.headings[-1]):
            out.extend(split_bold_questions(s))
        else:
            s.faq = len(s.headings) > 1 and bool(FAQ_HEADING_RE.search(s.headings[-2]))
            out.append(s)
    return out


def split_bold_questions(section):
    """Rule 3: split an FAQ section at its bold question lines."""
    items, question, lines = [], None, []

    def close_item():
        text = "\n".join(lines).strip()
        if question:
            items.append(Section(section.headings + [question], section.level, text, faq=True))
        elif text:  # text before the first question
            items.append(Section(section.headings, section.level, text))
        lines.clear()

    for line, in_code in iter_lines(section.text):
        m = None if in_code else QUESTION_RE.match(line)
        if m:
            close_item()
            question = m.group(1).strip()
        else:
            lines.append(line)
    close_item()
    return items


# ------------------------- Rule 4: merge small ones --------------------------

def merge_small(sections):
    """Rule 4: merge sections shorter than MIN_CHARS into a neighbour (FAQ items stay)."""
    def can_merge(a, b):
        return not a.faq and not b.faq and len(a.text) + len(b.text) <= MAX_CHARS

    def merge(a, b):  # append b, with its heading line, to a
        a.text = f"{a.text}\n\n{'#' * b.level} {b.headings[-1]}\n\n{b.text}".strip()

    # 4a. A small section goes into the next one.
    merged = []
    for s in sections:
        if merged and len(merged[-1].text) < MIN_CHARS and can_merge(merged[-1], s):
            merge(merged[-1], s)
        else:
            merged.append(s)
    # 4b. Still small (the next was too big, or it is the last one): into the previous one.
    out = []
    for s in merged:
        if out and len(s.text) < MIN_CHARS and can_merge(out[-1], s):
            merge(out[-1], s)
        else:
            out.append(s)
    return out


# -------------------------- Rule 5: split long ones --------------------------

def split_paragraphs(text):
    """Rule 5 helper: paragraphs separated by blank lines; a code block is one paragraph."""
    paragraphs, lines = [], []
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
    parts, current = [], []
    for para in split_paragraphs(text):
        if current and len("\n\n".join(current + [para])) > MAX_CHARS:
            # Keep a lead-in like "insert the code below:" with what it introduces.
            carry = [current.pop()] if len(current) > 1 and current[-1].endswith(":") else []
            parts.append("\n\n".join(current))
            current = carry
        current.append(para)
    parts.append("\n\n".join(current))
    return parts


# --------------------- Rule 6: context header and links ----------------------

def breadcrumb(stem, url):
    """Rule 6: page titles from the file name, e.g. "Application hosting-Shiny app hosting"
    -> ["Application hosting", "Shiny app hosting"]. The crawler joins titles with "-",
    so the URL depth tells how many titles there are (a title may contain "-" itself)."""
    depth = len([s for s in urlparse(url).path[len("/docs/"):].split("/") if s])
    titles = stem.split("-")
    return titles if depth > 1 and len(titles) == depth else [stem]


def slugify(text):
    """Rule 6: anchor of a heading on the site (#wiki-toc-<slug>)."""
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def make_chunk(section, text, part, n_parts, crumbs, url):
    """Rule 6: prefix the text with breadcrumb + heading path, link to the section."""
    # FAQ questions are not anchors on the site, so link to the FAQ heading.
    anchor = section.headings[-2] if section.faq else (section.headings or [None])[-1]
    header = " > ".join(crumbs + section.headings)
    return {
        "page_title": crumbs[-1],
        "breadcrumb": crumbs,
        "headings": section.headings,
        "type": "faq" if section.faq else "section",
        "part": part if n_parts > 1 else None,
        "source_url": url,
        "section_url": f"{url}#wiki-toc-{slugify(anchor)}" if anchor else url,
        "content": text,
        "text": f"{header}\n\n{text}".strip(),
    }


# --------------------------------- pipeline ----------------------------------

def chunk_page(path):
    """Apply Rules 1-6 to one crawled page (its first line is the page URL)."""
    url, _, md = path.read_text(encoding="utf-8").partition("\n")
    url = url.strip()
    if not url.startswith("http"):
        raise ValueError(f"{path.name}: first line is not the page URL")
    crumbs = breadcrumb(path.stem, url)

    sections = split_by_headings(clean(md))  # Rules 1, 2
    sections = split_faq(sections)  # Rule 3
    sections = merge_small(sections)  # Rule 4

    chunks = []
    for s in sections:
        if not s.text and not s.faq:  # a bare heading that could not be merged
            continue
        parts = split_long(s.text)  # Rule 5
        chunks.extend(make_chunk(s, text, i, len(parts), crumbs, url)  # Rule 6
                      for i, text in enumerate(parts))

    for i, c in enumerate(chunks):
        c["chunk_index"] = i
        c["id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{url}#{i}"))
        c["n_chars"] = len(c["text"])
    return chunks


def chunk_run(run_dir):
    """Chunk every page in run_dir/source/."""
    return [c for path in sorted((Path(run_dir) / "source").glob("*.md")) for c in chunk_page(path)]


def latest_run_dir(output_root):
    runs = sorted(p for p in Path(output_root).iterdir() if p.is_dir() and RUN_DIR_RE.match(p.name))
    if not runs:
        raise FileNotFoundError(f"no crawl output in {output_root}")
    return runs[-1]


def write_chunks(chunks, run_dir):
    """Write the chunks to run_dir/chunks/chunks.jsonl and return that path."""
    path = Path(run_dir) / "chunks" / "chunks.jsonl"
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", nargs="?", help="crawl run directory (default: latest in output/)")
    args = ap.parse_args()
    run_dir = Path(args.run_dir) if args.run_dir else latest_run_dir(Path(__file__).parent / "output")
    chunks = chunk_run(run_dir)
    out = write_chunks(chunks, run_dir)
    print(f"{len(chunks)} chunks from {run_dir.name} -> {out}")


if __name__ == "__main__":
    main()
