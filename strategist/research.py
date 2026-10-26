"""Market research hooks — keep the backlog aimed at demand.

Two modes:
- API mode: if SERPER_API_KEY (or TAVILY_API_KEY) is in the environment,
  pull live search results for TPT product topics.
- Manual mode: emit a 15-minute guided checklist the user can do in a
  browser. Never blocks the plan — research is a task, not a dependency.

Output lands in state["research"]["findings"] so trends accumulate.
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import date

MANUAL_CHECKLIST = [
    "Search TPT for this week's season hook; sort by 'Most Recent' AND 'Best Sellers' — note the top 5.",
    "For each: price, page count, preview style, # of reviews. Where's the gap (format, age band, AAC)?",
    "Check TPT's own homepage/newsletter for pushed themes (e.g. new policy pushes, featured categories).",
    "Glance at Etsy + Amazon KDP for the same niche — what formats sell there that TPT lacks?",
    "Write ONE line in strategist_state.json → research.findings: what to build next and why.",
]


def api_available() -> str | None:
    for key in ("SERPER_API_KEY", "TAVILY_API_KEY"):
        if os.environ.get(key):
            return key
    return None


def _serper(query: str, key: str, n: int = 5) -> list[dict]:
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=json.dumps({"q": query, "num": n}).encode(),
        headers={"X-API-KEY": key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    return [
        {"title": o.get("title"), "link": o.get("link"), "snippet": o.get("snippet")}
        for o in data.get("organic", [])[:n]
    ]


def _tavily(query: str, key: str, n: int = 5) -> list[dict]:
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=json.dumps({"query": query, "max_results": n}).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    return [
        {"title": o.get("title"), "link": o.get("url"), "snippet": o.get("content", "")[:200]}
        for o in data.get("results", [])[:n]
    ]


def scan(topic: str, state: dict) -> dict:
    """Run one market scan. Returns {'mode': ..., 'results'|'checklist': ...}."""
    provider = api_available()
    findings: dict = {"date": date.today().isoformat(), "topic": topic}
    if provider == "SERPER_API_KEY":
        results = _serper(f"site:teacherspayteachers.com {topic}", os.environ[provider])
        findings["mode"] = "api"
        findings["results"] = results
    elif provider == "TAVILY_API_KEY":
        results = _tavily(f"teacherspayteachers {topic} best selling", os.environ[provider])
        findings["mode"] = "api"
        findings["results"] = results
    else:
        findings["mode"] = "manual"
        findings["checklist"] = MANUAL_CHECKLIST
    state["research"]["last_run"] = findings["date"]
    state["research"]["findings"] = (state["research"]["findings"] + [findings])[-52:]
    return findings
