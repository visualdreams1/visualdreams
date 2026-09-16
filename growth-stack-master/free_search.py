"""Free web-search adapter for Growth Stack.

Uses a configurable SearXNG instance. No API key is required by SearXNG itself.
Set SEARXNG_URL to a trusted instance URL. The adapter returns the same evidence
shape used by the existing intelligence pipeline.
"""
from __future__ import annotations
import json, os, urllib.parse, urllib.request
from typing import Any

DEFAULT_SEARXNG_URL = "https://search.bus-hit.me"

def web_search(query: dict[str, str]) -> dict[str, Any]:
    base = os.getenv("SEARXNG_URL", DEFAULT_SEARXNG_URL).rstrip("/")
    q = f"{query['market']} {query['sector']} {query['type']} AI business opportunity demand pricing customers 2026"
    params = urllib.parse.urlencode({"q": q, "format": "json", "language": "en", "safesearch": 1})
    req = urllib.request.Request(
        f"{base}/search?{params}",
        headers={"Accept": "application/json", "User-Agent": "GrowthStackResearch/2.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    evidence = []
    for r in data.get("results", [])[:8]:
        evidence.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0),
            "published_at": r.get("publishedDate", ""),
        })
    return {**query, "evidence": evidence, "provider": "searxng", "provider_answer": ""}
