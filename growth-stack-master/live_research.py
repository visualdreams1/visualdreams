"""Live worldwide web research adapter for Growth Stack Master.

Uses a configurable HTTP search endpoint instead of hard-wiring a vendor. The model
layer can turn each search result into structured opportunity evidence. No external
message, purchase, login, or payment action is performed here.

Environment variables:
  RESEARCH_SEARCH_URL  - search endpoint URL
  RESEARCH_API_KEY     - private key for the endpoint, if required

Expected endpoint contract (provider adapter can transform this):
  GET/POST request containing query, market and category and returning JSON results.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any

from research_loop import run_research

SEARCH_URL = os.getenv("RESEARCH_SEARCH_URL", "")
API_KEY = os.getenv("RESEARCH_API_KEY", "")


def web_search(query: dict[str, str]) -> dict[str, Any]:
    if not SEARCH_URL:
        raise RuntimeError("RESEARCH_SEARCH_URL is not configured")

    params = urllib.parse.urlencode({
        "q": f"{query['market']} {query['sector']} {query['type']} AI business opportunity 2026",
        "market": query["market"],
        "sector": query["sector"],
        "type": query["type"],
    })
    url = SEARCH_URL + ("&" if "?" in SEARCH_URL else "?") + params
    request = urllib.request.Request(url, headers={"User-Agent": "GrowthStackResearch/1.0"})
    if API_KEY:
        request.add_header("Authorization", f"Bearer {API_KEY}")
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    # Keep raw provider output small and transparent; adapters may map richer fields.
    return {
        **query,
        "evidence": data.get("results", data.get("evidence", [])),
        "demand_signal": data.get("demand_signal", "RESEARCHED"),
        "competition": data.get("competition", "UNKNOWN"),
        "startup_cost": data.get("startup_cost", "UNKNOWN"),
        "recurring_revenue": data.get("recurring_revenue", "UNKNOWN"),
        "ease_of_demo": data.get("ease_of_demo", "UNKNOWN"),
        "customer_access": data.get("customer_access", "UNKNOWN"),
        "recommended_offer": data.get("recommended_offer", ""),
    }


def research_worldwide(limit: int | None = None) -> list[dict[str, Any]]:
    return run_research(provider=web_search, limit=limit)


if __name__ == "__main__":
    items = research_worldwide(limit=100)
    print(json.dumps({"researched": len(items), "top": items[:10]}, indent=2))
