"""Crawl https://serve.scilifelab.se/docs/ into markdown files (one per page)."""

import argparse
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

BASE = "https://serve.scilifelab.se"
DIR_URL = f"{BASE}/docs/_dir/"
DELAY = 1  # seconds between requests

# Fenced code blocks and inline code spans are left untouched.
CODE_RE = re.compile(r"(^(?:```|~~~).*?^(?:```|~~~)[^\n]*$|`[^`\n]+`)", re.S | re.M)
# [text](url "title") and ![alt](url "title")
INLINE_LINK_RE = re.compile(r"(\]\()(\s*<?)([^)\s>]+)(>?)((?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\))")
# [id]: url
REF_LINK_RE = re.compile(r"^(\s{0,3}\[[^\]]+\]:\s*)(\S+)", re.M)
TOC_RE = re.compile(r"^[ \t]*\[toc\][ \t]*\n?", re.I | re.M)
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def fix_url(url, page_url):
    if url.startswith("#"):
        return page_url + url
    if SCHEME_RE.match(url) or url.startswith("//"):
        return url  # absolute http(s), mailto:, etc.
    if url.startswith("/"):
        return BASE + url
    return urljoin(page_url, url)  # other relative paths


def fix_links(text, page_url):
    def fix_chunk(chunk):
        chunk = INLINE_LINK_RE.sub(
            lambda m: m.group(1) + m.group(2) + fix_url(m.group(3), page_url) + m.group(4) + m.group(5),
            chunk,
        )
        return REF_LINK_RE.sub(lambda m: m.group(1) + fix_url(m.group(2), page_url), chunk)

    parts = CODE_RE.split(text)  # odd indexes are code segments
    return "".join(p if i % 2 else fix_chunk(p) for i, p in enumerate(parts))


def get_page_urls(session):
    html = session.get(DIR_URL, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.find_all("a", href=True):
        url, _ = urldefrag(urljoin(DIR_URL, a["href"]))
        path = urlparse(url).path
        if urlparse(url).netloc != urlparse(BASE).netloc:
            continue
        if not path.startswith("/docs/") or "/_" in path:
            continue
        if not url.endswith("/"):
            url += "/"
        if url not in urls:
            urls.append(url)
    return urls


def fetch_markdown(session, page_url):
    r = session.get(page_url + "_source/", timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # The source is shown in <pre><code> (older versions used a <textarea>).
    node = soup.select_one("pre.highlight code") or soup.select_one("pre code") or soup.find("textarea")
    if node is None:
        raise ValueError("no source block found")
    text = node.get_text().replace("\r\n", "\n")
    text = TOC_RE.sub("", text).strip("\n") + "\n"
    h1 = soup.select_one("#article-title")
    title = ""
    if h1 is not None:
        for small in h1.find_all("small"):
            small.decompose()
        title = " ".join(h1.get_text().split())
    return title, fix_links(text, page_url)


def clean(name):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")


def filename_for(page_url, titles, used):
    """Titles of the page and its parent pages joined by "-", e.g.
    "User accounts-Users with privileged rights.md"."""
    segs = urlparse(page_url).path[len("/docs/"):].strip("/").split("/")
    segs = [s for s in segs if s]
    if not segs:
        parts = [titles.get(page_url) or "index"]
    else:
        parts = []
        for i in range(1, len(segs) + 1):
            prefix = f"{BASE}/docs/" + "/".join(segs[:i]) + "/"
            parts.append(titles.get(prefix) or segs[i - 1])
    base = "-".join(clean(p) for p in parts)
    name, n = base, 2
    while name.lower() in used:  # two pages with the same title
        name = f"{base} ({n})"
        n += 1
    used.add(name.lower())
    return name + ".md"


OUTPUT_ROOT = Path(__file__).parent / "output"


def crawl(output_root=OUTPUT_ROOT):
    """Crawl all pages into output_root/yyyymmdd-hhmmss/source/ and return the
    run directory (output_root/yyyymmdd-hhmmss/)."""
    run_dir = Path(output_root) / datetime.now().strftime("%Y%m%d-%H%M%S")
    out = run_dir / "source"
    out.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    urls = get_page_urls(session)
    print(f"Found {len(urls)} pages")

    failed = []
    titles, pages = {}, []  # page url -> title; (url, markdown)
    for i, url in enumerate(urls, 1):
        time.sleep(DELAY)
        try:
            title, md = fetch_markdown(session, url)
        except Exception as e:
            print(f"[{i}/{len(urls)}] FAILED {url}: {e}")
            failed.append(url)
            continue
        titles[url] = title
        pages.append((url, md))
        print(f"[{i}/{len(urls)}] fetched {url}")

    # Name files after all titles are known, so parent titles can be used.
    used = set()
    for url, md in pages:
        name = filename_for(url, titles, used)
        (out / name).write_text(f"{url}\n\n{md}", encoding="utf-8")
        print("saved", name)

    print(f"Done: {len(urls) - len(failed)} saved, {len(failed)} failed")
    for u in failed:
        print("  failed:", u)
    return run_dir


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--output", default=str(OUTPUT_ROOT))
    args = ap.parse_args()
    crawl(args.output)


if __name__ == "__main__":
    main()
