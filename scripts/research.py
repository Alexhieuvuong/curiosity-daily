"""
research.py — retrieve real reference material so briefs are grounded, not invented.

Two reputable, free, no-key sources, reachable from CI:
- Wikipedia (Action API) — encyclopedic overview / definitions.
- OpenAlex (https://openalex.org) — peer-reviewed scholarly works (abstracts).

fetch_sources() returns a merged list of {title, url, extract, kind}. Each fetch is
independent and fails soft (returns []), so a brief still gets whatever was reachable;
if both are empty, generate.py falls back to a labeled "no external sources" mode.
"""

import requests

WIKI_API = "https://en.wikipedia.org/w/api.php"
OPENALEX_API = "https://api.openalex.org/works"
# Wikimedia API etiquette asks for a descriptive UA; OpenAlex's "polite pool" asks for mailto.
HEADERS = {"User-Agent": "curiosity-daily/1.0 (personal learning tool; +https://github.com/Alexhieuvuong/curiosity-daily)"}
MAILTO = "hieudinhvuong@gmail.com"


def fetch_sources(query, wiki_pages=3, openalex_works=2):
    """Merged reputable sources: Wikipedia overview first, then academic papers."""
    return fetch_wikipedia(query, max_pages=wiki_pages) + fetch_openalex(query, max_works=openalex_works)


def sources_prompt_block(sources):
    """Numbered SOURCE MATERIAL block shared by the brief writer and the supervisor."""
    return "\n\n".join(
        f"[{i}] {s['title']} — {s.get('kind', 'source')} ({s['url']})\n{s['extract']}"
        for i, s in enumerate(sources, start=1)
    )


# --------------------------------------------------------------------------- Wikipedia

def fetch_wikipedia(query, max_pages=3, max_chars=3500, timeout=30):
    titles = _wiki_search_titles(query, max_pages, timeout)
    sources = []
    for title in titles:
        src = _wiki_fetch_extract(title, max_chars, timeout)
        if src:
            sources.append(src)
    return sources


def _wiki_search_titles(query, limit, timeout):
    try:
        resp = requests.get(
            WIKI_API,
            params={"action": "query", "list": "search", "srsearch": query,
                    "srlimit": limit, "srnamespace": 0, "format": "json"},
            headers=HEADERS, timeout=timeout,
        )
        resp.raise_for_status()
        return [h["title"] for h in resp.json().get("query", {}).get("search", [])]
    except Exception as e:
        print(f"[research] Wikipedia search failed for {query!r}: {e}")
        return []


def _wiki_fetch_extract(title, max_chars, timeout):
    try:
        resp = requests.get(
            WIKI_API,
            params={"action": "query", "prop": "extracts|info", "inprop": "url",
                    "explaintext": 1, "exintro": 1, "redirects": 1,
                    "titles": title, "format": "json"},
            headers=HEADERS, timeout=timeout,
        )
        resp.raise_for_status()
        for _pid, page in resp.json().get("query", {}).get("pages", {}).items():
            extract = (page.get("extract") or "").strip()
            if not extract:
                continue
            return {
                "title": page.get("title", title),
                "url": page.get("fullurl") or f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                "extract": extract[:max_chars],
                "kind": "Wikipedia",
            }
    except Exception as e:
        print(f"[research] Wikipedia extract failed for {title!r}: {e}")
    return None


# --------------------------------------------------------------------------- OpenAlex

def fetch_openalex(query, max_works=2, max_chars=1600, timeout=30):
    """Top relevant scholarly works with abstracts for `query`, as cited sources."""
    try:
        resp = requests.get(
            OPENALEX_API,
            params={
                "search": query,
                "filter": "has_abstract:true",
                "per-page": max_works,
                "select": "title,abstract_inverted_index,doi,id,publication_year,primary_location",
                "mailto": MAILTO,
            },
            headers=HEADERS, timeout=timeout,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except Exception as e:
        print(f"[research] OpenAlex search failed for {query!r}: {e}")
        return []

    sources = []
    for w in results:
        abstract = _reconstruct_abstract(w.get("abstract_inverted_index"))
        if not abstract:
            continue
        title = w.get("title") or "Untitled work"
        year = w.get("publication_year")
        url = (w.get("doi")
               or (w.get("primary_location") or {}).get("landing_page_url")
               or w.get("id"))
        sources.append({
            "title": f"{title} ({year})" if year else title,
            "url": url,
            "extract": abstract[:max_chars],
            "kind": "academic paper",
        })
    return sources


def _reconstruct_abstract(inverted_index):
    """OpenAlex stores abstracts as {word: [positions]} — rebuild the plain text."""
    if not inverted_index:
        return ""
    positions = {}
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))
