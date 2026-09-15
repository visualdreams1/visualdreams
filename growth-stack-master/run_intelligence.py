"""Run live research then AI evidence analysis then monitoring."""
from __future__ import annotations
import json
from live_research import research_worldwide
from intelligence_engine import build_queue
from monitor import check

def main():
 research_worldwide(limit=250)
 intel=build_queue()
 monitor=check()
 print(json.dumps({"research":"complete","intelligence":intel,"monitor":monitor},indent=2))
if __name__=="__main__":main()
