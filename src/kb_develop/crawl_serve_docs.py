"""Crawl https://serve.scilifelab.se/docs/ into markdown, one entry per page (kept in memory).

Crawling steps (each function below says which step it implements):

  Step 1. List pages: read the docs directory page (/docs/_dir/) and collect the URL
          of every docs page.
  Step 2. Fetch: download the markdown source (<page>/_source/) and the title of each
          page, waiting DELAY seconds between requests. A page that fails is reported
          and skipped.
  Step 3. Fix links: turn relative links in the markdown into absolute URLs, so they
          still work outside the site. Code blocks and inline code are left untouched.
  Step 4. Breadcrumbs: once all titles are known, build each page's title path
          (its parent pages' titles + its own), e.g.
          ["User accounts", "Users with privileged rights"].

crawl() runs Steps 1-4 and returns [{"url", "breadcrumb", "markdown"}], one per page.

Async: the downloads and the waits between them are awaited (httpx.AsyncClient), so
the event loop serves other requests meanwhile; the HTML parsing (BeautifulSoup) runs
in a worker thread (asyncio.to_thread), so it does not stop them either.
"""

import asyncio
import logging
import re
from urllib.parse import urljoin, urlparse, urldefrag

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE = "https://serve.scilifelab.se"
DIR_URL = f"{BASE}/docs/_dir/"
# Seconds to wait between requests (Step 2)
DELAY = 1
# Seconds before a request is given up (Steps 1, 2)
TIMEOUT = 30

# Fenced code blocks and inline code spans; links inside them are not fixed (Step 3)
CODE_RE = re.compile(r"(^(?:```|~~~).*?^(?:```|~~~)[^\n]*$|`[^`\n]+`)", re.S | re.M)
# [text](url "title") and ![alt](url "title")
INLINE_LINK_RE = re.compile(r"(\]\()(\s*<?)([^)\s>]+)(>?)((?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\))")
# [id]: url
REF_LINK_RE = re.compile(r"^(\s{0,3}\[[^\]]+\]:\s*)(\S+)", re.M)
# The [toc] macro, which only renders on the site (Step 2)
TOC_RE = re.compile(r"^[ \t]*\[toc\][ \t]*\n?", re.I | re.M)
# A URL that starts with a scheme, e.g. "https:" or "mailto:"
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


# ---------------------------- Step 1: list pages -----------------------------

async def get_page_urls(http_client):
    """Step 1: return the URL of every docs page listed on the directory page."""
    response = await http_client.get(DIR_URL)
    return await asyncio.to_thread(parse_page_urls, response.text)


def parse_page_urls(html):
    """Step 1: the URLs of the docs pages linked from the directory page's HTML."""
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.find_all("a", href=True):
        url, _ = urldefrag(urljoin(DIR_URL, a["href"]))
        path = urlparse(url).path
        # Skip links to other sites
        if urlparse(url).netloc != urlparse(BASE).netloc:
            continue
        # Skip pages outside /docs/ and the wiki's own pages (/_dir/, /_source/, ...)
        if not path.startswith("/docs/") or "/_" in path:
            continue
        if not url.endswith("/"):
            url += "/"
        if url not in urls:
            urls.append(url)
    return urls


# ------------------------------- Step 2: fetch -------------------------------

async def fetch_markdown(http_client, page_url):
    """Step 2: download one page's markdown source and title; return (title, markdown)."""
    response = await http_client.get(page_url + "_source/")
    response.raise_for_status()
    return await asyncio.to_thread(parse_source, response.text)


def parse_source(html):
    """Step 2: the title and the markdown source in the HTML of a page's _source/ view;
    return (title, markdown)."""
    soup = BeautifulSoup(html, "html.parser")
    # The source is shown in <pre><code> (older versions used a <textarea>).
    node = soup.select_one("pre.highlight code") or soup.select_one("pre code") or soup.find("textarea")
    if node is None:
        raise ValueError("no source block found")
    markdown = node.get_text().replace("\r\n", "\n")
    markdown = TOC_RE.sub("", markdown).strip("\n") + "\n"

    title = ""
    h1 = soup.select_one("#article-title")
    if h1 is not None:
        # The title tag also holds small extra text (e.g. a status label); drop it.
        for small in h1.find_all("small"):
            small.decompose()
        title = " ".join(h1.get_text().split())
    return title, markdown


# ----------------------------- Step 3: fix links -----------------------------

def fix_url(url, page_url):
    """Step 3: return url as an absolute URL, resolved against page_url."""
    # "#section" -> link to a heading on the same page
    if url.startswith("#"):
        return page_url + url
    # Already absolute: http(s), mailto:, //host/...
    if SCHEME_RE.match(url) or url.startswith("//"):
        return url
    # "/docs/..." -> relative to the site
    if url.startswith("/"):
        return BASE + url
    # Other relative paths, e.g. "../shiny/"
    return urljoin(page_url, url)


def fix_links(markdown, page_url):
    """Step 3: make every link in the markdown absolute, except inside code."""

    def fix_inline_link(m):
        # Groups: "](", optional "<", the url, optional ">", optional title + ")"
        return m.group(1) + m.group(2) + fix_url(m.group(3), page_url) + m.group(4) + m.group(5)

    def fix_ref_link(m):
        # Groups: "[id]: ", the url
        return m.group(1) + fix_url(m.group(2), page_url)

    # Splitting on CODE_RE gives text and code alternately: even indexes are text,
    # odd indexes are code.
    parts = CODE_RE.split(markdown)
    fixed_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            part = INLINE_LINK_RE.sub(fix_inline_link, part)
            part = REF_LINK_RE.sub(fix_ref_link, part)
        fixed_parts.append(part)
    return "".join(fixed_parts)


# ---------------------------- Step 4: breadcrumbs ----------------------------

def breadcrumb(page_url, titles):
    """Step 4: titles of the page and its parent pages, e.g.
    ["User accounts", "Users with privileged rights"]. titles maps page URL -> title."""
    # URL path segments after /docs/, e.g. ["user-accounts", "privileged"]
    segments = []
    for segment in urlparse(page_url).path[len("/docs/"):].split("/"):
        if segment:
            segments.append(segment)

    # The docs start page itself (/docs/)
    if not segments:
        return [titles.get(page_url) or "index"]

    # One title per level: /docs/a/, /docs/a/b/, ... (the segment name if a title is missing)
    crumbs = []
    for i in range(1, len(segments) + 1):
        parent_url = f"{BASE}/docs/" + "/".join(segments[:i]) + "/"
        crumbs.append(titles.get(parent_url) or segments[i - 1])
    return crumbs


# --------------------------------- pipeline ----------------------------------

async def crawl():
    """Run Steps 1-4 and return [{"url", "breadcrumb", "markdown"}], one per page."""
    # Follows redirects like a browser; one client for all requests of this crawl.
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as http_client:
        # Step 1. List pages
        urls = await get_page_urls(http_client)
        logger.info("Found %d pages", len(urls))

        # page URL -> title, used in Step 4
        titles = {}
        # (url, markdown) of every fetched page
        fetched = []
        failed = []
        for i, url in enumerate(urls, 1):
            await asyncio.sleep(DELAY)

            # Step 2. Fetch
            try:
                title, markdown = await fetch_markdown(http_client, url)
            except Exception as e:
                logger.warning("[%d/%d] failed to fetch %s: %s", i, len(urls), url, e)
                failed.append(url)
                continue

            # Step 3. Fix links
            markdown = fix_links(markdown, url)

            titles[url] = title
            fetched.append((url, markdown))
            logger.info("[%d/%d] fetched %s", i, len(urls), url)

    logger.info("Crawl done: %d fetched, %d failed", len(fetched), len(failed))
    for url in failed:
        logger.warning("Not fetched: %s", url)

    # Step 4. Breadcrumbs (after the loop, so the titles of all parent pages are known)
    pages = []
    for url, markdown in fetched:
        page = {"url": url, "breadcrumb": breadcrumb(url, titles), "markdown": markdown}
        pages.append(page)
    return pages
