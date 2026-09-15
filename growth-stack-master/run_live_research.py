"""Scheduled/live research runner."""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone

from research_loop import daily_loop
from tavily_provider import provider


def run() -> dict:
    limit = int(os.getenv("RESEARCH_BATCH_SIZE", "40"))
    report = daily_loop(provider=provider, limit=limit)
    stamp = datetime.now(timezone.utc).isoformat()
    print(json.dumps({"timestamp": stamp, **report}, indent=2))
    return report


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, indent=2))
        sys.exit(1)
