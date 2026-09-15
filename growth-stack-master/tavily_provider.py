"""Live Tavily search provider for Growth Stack research.

Requires TAVILY_API_KEY in the runtime environment. No key is stored in the repo.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

API_URL = "https://api.tavily.com/search"


def search_tavily(query: str, max_results: int = 5) -> dict[str, Any]:
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key:
        raise RuntimeError("TAVILY_API_KEY is not configured")
    payload = {
        "query": query,
        "topic": "general",
        "search_depth": os.getenv("TAVILY_SEARCH_DEPTH", "basic"),
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "GrowthStackResearch/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def provider(query: dict[str, str]) -> dict[str, Any]:
    text = (
        f"{query['market']} {query['sector']} {query['type']} "
        "AI business opportunity customer demand pricing 2026"
    )
    data = search_tavily(text, max_results=5)
    results = data.get("results", [])
    evidence = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", "")[:1200],
            "score": r.get("score"),
        }
        for r in results
    ]
    return {
        **query,
        "evidence": evidence,
        "demand_signal": "RESEARCHED",
        "competition": "TO_BE_VERIFIED",
        "startup_cost": "TO_BE_VERIFIED",
        "recurring_revenue": "POSSIBLE",
        "ease_of_demo": "TO_BE_VERIFIED",
        "customer_access": "TO_BE_VERIFIED",
        "recommended_offer": f"Pilot {query['type']} for {query['sector']} in {query['market']}",
    }


if __name__ == "__main__":
    print(json.dumps(provider({"market": "Kenya", "sector": "hotels", "type": "AI customer support"}), indent=2))
