"""
Jina AI Reader Module
Reads discovered URLs via the Jina Reader API (https://r.jina.ai/<TARGET_URL>).
Replaces all browser/Playwright/Crawl4AI page-rendering logic.

Architecture:
    Discovered URL → Jina Reader API → raw text/markdown content
    → content adapter → PageContent (passed to existing extractor)

Environment variables:
    JINA_API_KEY          — optional; enables authenticated mode (higher rate limits)
    JINA_READER_BASE_URL  — optional; default https://r.jina.ai
    JINA_CONCURRENCY      — optional; default 3 (max simultaneous requests)
"""

import asyncio
import logging
import os
import re
import time
from typing import List, Optional

import httpx

try:
    from .crawler import PageContent, extract_page_elements
except ImportError:
    from crawler import PageContent, extract_page_elements

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

DEFAULT_JINA_BASE_URL = "https://r.jina.ai"
DEFAULT_CONCURRENCY = 3
DEFAULT_TIMEOUT_SECONDS = 30.0

# Retry settings for transient failures
MAX_RETRIES = 2
RETRY_BASE_DELAY = 2.0   # seconds; multiplied by attempt number

# HTTP status codes that should NOT be retried (permanent errors)
PERMANENT_ERROR_CODES = {400, 401, 403, 404, 410, 422, 451}


def _get_jina_config() -> dict:
    """Read Jina configuration from environment variables at call time."""
    return {
        "base_url": os.getenv("JINA_READER_BASE_URL", DEFAULT_JINA_BASE_URL).rstrip("/"),
        "api_key": os.getenv("JINA_API_KEY", "").strip(),
        "concurrency": int(os.getenv("JINA_CONCURRENCY", str(DEFAULT_CONCURRENCY))),
    }


def _build_headers(api_key: str) -> dict:
    """Build request headers for the Jina Reader API."""
    headers = {
        "Accept": "text/plain",
        # Request plain-text markdown output — best for extraction
        "X-Respond-With": "markdown",
        # Retain links as text-only (no noise in URL-heavy pages)
        "X-Retain-Links": "none",
        # Drop images — we only need textual content for extraction
        "X-Retain-Images": "none",
        "User-Agent": "CompanyDomainCrawler/2.0 (company identity research)",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _is_transient_error(status_code: int) -> bool:
    """Return True if the error code is worth retrying."""
    return status_code in {429, 500, 502, 503, 504}


def log_print(msg: str):
    """Print and flush immediately for SSE visibility."""
    print(msg, flush=True)


class JinaReader:
    """
    Fetches page content for discovered URLs using the Jina Reader API.

    Returns the same List[PageContent] shape that the existing extractor
    expects, ensuring zero changes to downstream extraction code.
    """

    def __init__(self):
        # Config is read fresh at instantiation so env vars set after import work.
        cfg = _get_jina_config()
        self.base_url = cfg["base_url"]
        self.api_key = cfg["api_key"]
        self.concurrency = max(1, cfg["concurrency"])
        self._headers = _build_headers(self.api_key)

        mode = "authenticated" if self.api_key else "keyless"
        log_print(
            f"      [Jina] Reader initialised — base: {self.base_url} | "
            f"concurrency: {self.concurrency} | mode: {mode}"
        )

    def _jina_url_for(self, target_url: str) -> str:
        """Construct the Jina Reader URL for a given target URL."""
        return f"{self.base_url}/{target_url}"

    async def _fetch_single(
        self,
        client: httpx.AsyncClient,
        target_url: str,
        idx: int,
        total: int,
    ) -> Optional[PageContent]:
        """
        Fetch one URL via Jina Reader with retry/backoff for transient errors.

        Returns PageContent on success, None on permanent failure or empty content.
        """
        jina_url = self._jina_url_for(target_url)
        last_error: Optional[Exception] = None
        last_status: Optional[int] = None

        for attempt in range(1, MAX_RETRIES + 2):  # attempts: 1, 2, 3
            try:
                resp = await client.get(jina_url, headers=self._headers)
                last_status = resp.status_code

                if resp.status_code == 200:
                    raw_text = resp.text.strip()
                    if not raw_text:
                        log_print(
                            f"      [{idx}/{total}] ⚠ Jina returned empty body for: {target_url}"
                        )
                        return None

                    page = _adapt_jina_response(target_url, raw_text)
                    log_print(
                        f"      [{idx}/{total}] ✓ Jina read {len(raw_text):,} chars: {target_url}"
                    )
                    return page

                elif resp.status_code in PERMANENT_ERROR_CODES:
                    log_print(
                        f"      [{idx}/{total}] ✗ Jina permanent error HTTP {resp.status_code} "
                        f"for: {target_url} — skipping."
                    )
                    return None

                elif _is_transient_error(resp.status_code):
                    if attempt <= MAX_RETRIES:
                        delay = RETRY_BASE_DELAY * attempt
                        log_print(
                            f"      [{idx}/{total}] ↻ Jina transient HTTP {resp.status_code} "
                            f"for: {target_url} — retry {attempt}/{MAX_RETRIES} in {delay:.0f}s"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        log_print(
                            f"      [{idx}/{total}] ✗ Jina gave HTTP {resp.status_code} after "
                            f"{MAX_RETRIES} retries for: {target_url} — skipping."
                        )
                        return None

                else:
                    log_print(
                        f"      [{idx}/{total}] ✗ Jina unexpected HTTP {resp.status_code} "
                        f"for: {target_url} — skipping."
                    )
                    return None

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt <= MAX_RETRIES:
                    delay = RETRY_BASE_DELAY * attempt
                    log_print(
                        f"      [{idx}/{total}] ↻ Jina network error ({type(e).__name__}) "
                        f"for: {target_url} — retry {attempt}/{MAX_RETRIES} in {delay:.0f}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    log_print(
                        f"      [{idx}/{total}] ✗ Jina network error after {MAX_RETRIES} retries "
                        f"for: {target_url}: {e}"
                    )
                    return None

            except Exception as e:
                log_print(
                    f"      [{idx}/{total}] ✗ Jina unexpected exception for {target_url}: "
                    f"{type(e).__name__}: {e}"
                )
                return None

        log_print(f"      [{idx}/{total}] ✗ Jina exhausted retries for: {target_url}")
        return None

    async def read_pages(self, urls: List[str]) -> List[PageContent]:
        """
        Read all provided URLs via Jina Reader API concurrently.

        Maintains concurrency at self.concurrency to respect rate limits.
        Failed/empty URLs are logged and skipped; the crawl never crashes
        due to a single URL failure.
        """
        total = len(urls)
        log_print(f"\n[3/5] Reading {total} pages via Jina Reader API...")

        results: List[PageContent] = []
        semaphore = asyncio.Semaphore(self.concurrency)

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS),
            follow_redirects=True,
        ) as client:

            async def _guarded_fetch(idx: int, url: str) -> Optional[PageContent]:
                async with semaphore:
                    return await self._fetch_single(client, url, idx, total)

            tasks = [_guarded_fetch(i + 1, url) for i, url in enumerate(urls)]
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        failed = 0
        for res in raw_results:
            if isinstance(res, Exception):
                logger.error(f"Unexpected gather exception: {res}")
                failed += 1
            elif res is not None:
                results.append(res)
            else:
                failed += 1

        log_print(
            f"      Successfully read {len(results)}/{total} pages via Jina "
            f"({failed} failed/empty)."
        )
        return results


# ── Content Adapter ────────────────────────────────────────────────────────────

# Jina returns plain markdown with a standard header block like:
#   Title: <title>
#   URL Source: <url>
#   Markdown Content:
#   <body>
#
# We parse the header metadata and wrap the body in minimal HTML so the
# existing parser (parse_page_structure → BeautifulSoup) can extract
# title, meta, headings, and text without any changes.

_TITLE_RE = re.compile(r"^Title:\s*(.+)$", re.MULTILINE)
_URL_RE = re.compile(r"^URL Source:\s*(.+)$", re.MULTILINE)
_DESCRIPTION_RE = re.compile(r"^Description:\s*(.+)$", re.MULTILINE)
_MARKDOWN_SPLIT_RE = re.compile(r"^Markdown Content:\s*$", re.MULTILINE)


def _parse_jina_header(raw: str) -> dict:
    """
    Extract the metadata block that Jina prepends to every response.

    Returns a dict with keys: title, url_source, description, body.
    """
    meta: dict = {"title": None, "url_source": None, "description": None, "body": raw}

    # Split at the "Markdown Content:" separator if present
    parts = _MARKDOWN_SPLIT_RE.split(raw, maxsplit=1)
    header_block = parts[0] if len(parts) == 2 else ""
    body = parts[1].strip() if len(parts) == 2 else raw

    meta["body"] = body

    if header_block:
        tm = _TITLE_RE.search(header_block)
        if tm:
            meta["title"] = tm.group(1).strip()

        um = _URL_RE.search(header_block)
        if um:
            meta["url_source"] = um.group(1).strip()

        dm = _DESCRIPTION_RE.search(header_block)
        if dm:
            meta["description"] = dm.group(1).strip()

    return meta


def _markdown_to_html_fragment(md: str) -> str:
    """
    Convert the markdown body returned by Jina into an HTML fragment.

    This is intentionally a lightweight, dependency-free conversion that
    preserves the structural signals the existing extractor relies on:
    headings, paragraphs, key-value text, contact blocks, and body text.
    We do NOT need pixel-perfect rendering; we need extractable text.
    """
    lines = md.split("\n")
    html_lines = []

    for line in lines:
        # ATX headings: # ## ### ####
        h_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if h_match:
            level = min(len(h_match.group(1)), 6)
            text = h_match.group(2).strip()
            # Strip inline markdown from heading text
            text = _strip_inline_md(text)
            html_lines.append(f"<h{level}>{text}</h{level}>")
            continue

        # Horizontal rules
        if re.match(r"^[-*_]{3,}\s*$", line):
            html_lines.append("<hr>")
            continue

        # Empty lines → paragraph break (we'll close/open in post-process)
        if not line.strip():
            html_lines.append("")
            continue

        # List items (unordered)
        li_match = re.match(r"^[\-\*\+]\s+(.*)", line)
        if li_match:
            html_lines.append(f"<li>{_strip_inline_md(li_match.group(1))}</li>")
            continue

        # Ordered list items
        ol_match = re.match(r"^\d+\.\s+(.*)", line)
        if ol_match:
            html_lines.append(f"<li>{_strip_inline_md(ol_match.group(1))}</li>")
            continue

        # Default: wrap in paragraph
        html_lines.append(f"<p>{_strip_inline_md(line)}</p>")

    return "\n".join(html_lines)


def _strip_inline_md(text: str) -> str:
    """Remove inline markdown formatting (bold, italic, code, links) from a string."""
    # Links: [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    # Images: ![alt](url) → alt
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # Bold/italic: ***text***, **text**, *text*, __text__, _text_
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", text)
    # Inline code
    text = re.sub(r"`([^`]*)`", r"\1", text)
    return text


def _adapt_jina_response(target_url: str, raw_text: str) -> PageContent:
    """
    Convert Jina Reader plain-text/markdown response into a PageContent object
    compatible with the existing CompanyDataExtractor.

    Strategy:
      1. Parse Jina's metadata header to extract title/description.
      2. Convert markdown body to a minimal HTML fragment.
      3. Wrap in a full HTML document and feed to extract_page_elements()
         (the existing parser path) so all downstream code is unchanged.
      4. Attach raw markdown as page.markdown for any future use.
    """
    meta = _parse_jina_header(raw_text)
    title = meta["title"] or ""
    description = meta["description"] or ""
    body_md = meta["body"]

    # Build a minimal HTML document the existing parser can work with
    html_body = _markdown_to_html_fragment(body_md)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    {"" if not description else f'<meta name="description" content="{description}">'}
</head>
<body>
{html_body}
</body>
</html>"""

    # Run through the existing HTML parser (parse_page_structure → PageContent)
    page = extract_page_elements(target_url, html)
    page.markdown = body_md

    # If the parser couldn't extract a title (very rare with our wrapper), set it directly
    if not page.title and title:
        page.title = title
    if not page.meta_description and description:
        page.meta_description = description

    # Also store the raw markdown as the page text for any regex-based extractors
    # This ensures text-scan patterns in extractor.py see the full readable content
    if body_md and (not page.text or len(body_md) > len(page.text)):
        page.text = body_md

    return page
