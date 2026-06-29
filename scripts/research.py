"""
research.py — retrieve real reference material so briefs are grounded, not invented.

Uses the Wikipedia REST/Action API (free, no key) to fetch the lead sections of the
most relevant articles for a topic. The brief then summarizes and analyzes THIS text
and cites it, instead of fabricating facts from the model's memory.

fetch_sources() returns a list of {title, url, extract}. On any failure it returns
[], and the generator falls back to a clearly-labeled "no external sources" mode that
avoids stating specific facts.
"""

import requests

WIKI_API = "https://en.wikipedia.org/w/api.php"
# A descriptive User-Agent is requested by Wikimedia's API etiquette.
HEADERS = {"User-Agent": "curiosity-daily/1.0 (personal learning tool; +https://github.com/Alexhieuvuong/curiosity-daily)"}


def fetch_sources(query, max_pages=3, max_chars=3500, timeout=30):
    """Return up to `max_pages` real Wikipedia sources for `query`."""
    titles = _search_titles(query, max_pages, timeout)
    sources = []
    for title in titles:
        src = _fetch_extract(title, max_chars, timeout)
        if src:
            sources.append(src)
    return sources


def _search_titles(query, limit, timeout):
    try:
        resp = requests.get(
            WIKI_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": limit,
                "srnamespace": 0,          # articles only
                "format": "json",
            },
            headers=HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
        hits = resp.json().get("query", {}).get("search", [])
        return [h["title"] for h in hits]
    except Exception as e:  # network/parse issues must not crash the run
        print(f"[research] search failed for {query!r}: {e}")
        return []


def _fetch_extract(title, max_chars, timeout):
    try:
        resp = requests.get(
            WIKI_API,
            params={
                "action": "query",
                "prop": "extracts|info",
                "inprop": "url",
                "explaintext": 1,
                "exintro": 1,              # lead section — the definition/overview
                "redirects": 1,
                "titles": title,
                "format": "json",
            },
            headers=HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        for _pid, page in pages.items():
            extract = (page.get("extract") or "").strip()
            if not extract:
                continue
            return {
                "title": page.get("title", title),
                "url": page.get("fullurl")
                or f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                "extract": extract[:max_chars],
            }
    except Exception as e:
        print(f"[research] extract failed for {title!r}: {e}")
    return None
