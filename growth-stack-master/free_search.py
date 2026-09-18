"""Free web-search adapter for Growth Stack.

Uses a configurable SearXNG instance with a small current fallback pool.
No API key is required by SearXNG itself. A private/self-hosted instance can
always be supplied with SEARXNG_URL.
"""
from __future__ import annotations
import json, os, urllib.parse, urllib.request
from typing import Any

DEFAULT_SEARXNG_URLS = [
    "https://searxng.eshnetwork.space",
    "https://searx.linxx.net",
    "https://search.ethibox.fr",
]

def _search(base: str, q: str) -> dict[str, Any]:
    params = urllib.parse.urlencode({"q": q, "format": "json", "language": "en", "safesearch": 1})
    req = urllib.request.Request(
        f"{base.rstrip('/')}/search?{params}",
        headers={"Accept": "application/json", "User-Agent": "GrowthStackResearch/2.1"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

def web_search(query: dict[str, str]) -> dict[str, Any]:
    q = f"{query['market']} {query['sector']} {query['type']} AI business opportunity demand pricing customers 2026"
    configured = os.getenv("SEARXNG_URL", "").strip()
    bases = [configured] if configured else DEFAULT_SEARXNG_URLS
    last_error = None
    for base in bases:
        try:
            data = _search(base, q)
            evidence = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0),
                    "published_at": r.get("publishedDate", ""),
                }
                for r in data.get("results", [])[:8]
            ]
            return {**query, "evidence": evidence, "provider": "searxng", "provider_answer": ""}
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    raise RuntimeError(f"All configured SearXNG providers failed: {last_error}")
