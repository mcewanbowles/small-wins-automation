from __future__ import annotations

import asyncio
import re
import string
from urllib.parse import quote_plus

import httpx

from .models import KeywordResult

GOOGLE_SUGGEST_URL = "https://suggestqueries.google.com/complete/search?client=firefox&q={query}"
# TPT moved search results to /browse; /search 404s. The result count is
# available as the first "totalCount" value in the page JSON payload.
TPT_SEARCH_URL = "https://www.teacherspayteachers.com/browse?search={query}"
# NOTE: TPT no longer exposes a working public autocomplete endpoint; the
# function below fails gracefully to [] so Google remains the demand source.
TPT_AUTOCOMPLETE_URL = "https://www.teacherspayteachers.com/autocomplete?term={query}"
STORE_LEVEL_THRESHOLDS = {
    "new_store": 5,
    "growing": 25,
    "established": 100,
    "authority": 10**9,
}

# Buyer-intent modifiers used to expand a seed into long-tail variants.
# Each modifier becomes one extra autocomplete query (seed + modifier).
EXPANSION_MODIFIERS = [
    "activities",
    "worksheets",
    "printable",
    "free",
    "special education",
    "autism",
    "speech therapy",
    "bundle",
    "task cards",
    "lesson plan",
    "centers",
    "adapted book",
]

# Cap on how many phrases get the (expensive) TPT supply + review lookups.
MAX_SUPPLY_CHECKS = 30

SUPPLY_TARGETS = {
    "new_store": {"ideal": 40, "stretch": 120},
    "growing": {"ideal": 80, "stretch": 200},
    "established": {"ideal": 160, "stretch": 320},
    "authority": {"ideal": 320, "stretch": 600},
}


async def _google_autocomplete(seed: str) -> list[str]:
    query = quote_plus(seed)
    url = GOOGLE_SUGGEST_URL.format(query=query)
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, list) or len(payload) < 2:
        return []

    suggestions = payload[1]
    if not isinstance(suggestions, list):
        return []

    clean = []
    for item in suggestions:
        if isinstance(item, str):
            text = " ".join(item.split())
            if text and text.lower() not in {s.lower() for s in clean}:
                clean.append(text)
    return clean


async def _tpt_supply_count(phrase: str) -> int | None:
    query = quote_plus(phrase)
    url = TPT_SEARCH_URL.format(query=query)
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            },
        )

    if response.status_code >= 400:
        return None

    html = response.text

    patterns = [
        r'"totalCount"\s*:\s*"?(\d+)',  # first totalCount on /browse = results
        r"([\d,]+)\s+results",
        r"results\s*\(([\d,]+)\)",
        r"of\s*([\d,]+)\s*results",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except ValueError:
                continue

    return None


async def _tpt_review_metrics(phrase: str) -> tuple[float | None, int | None]:
    query = quote_plus(phrase)
    url = TPT_SEARCH_URL.format(query=query)
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            },
        )

    if response.status_code >= 400:
        return (None, None)

    html = response.text
    reviews = []

    patterns = [
        r"based on\s+([\d,]+)\s+reviews?",  # /browse listing cards
        r'"reviewCount"\s*:\s*"?(\d+)"?',
        r'"ratingCount"\s*:\s*"?(\d+)"?',
        r"(\d+)\s+ratings?",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, html, flags=re.IGNORECASE):
            try:
                value = int(match)
            except ValueError:
                continue
            if value >= 0:
                reviews.append(value)
            if len(reviews) >= 5:
                break
        if len(reviews) >= 5:
            break

    if not reviews:
        return (None, None)

    top5 = reviews[:5]
    avg = round(sum(top5) / len(top5), 1)
    low = min(top5)
    return (avg, low)


async def _tpt_autocomplete(seed: str) -> list[str]:
    query = quote_plus(seed)
    url = TPT_AUTOCOMPLETE_URL.format(query=query)
    timeout = httpx.Timeout(10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
                },
            )
    except Exception:
        return []

    if response.status_code >= 400:
        return []

    payload: object
    try:
        payload = response.json()
    except Exception:
        return []

    suggestions: list[str] = []
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, str):
                text = " ".join(item.split())
                if text:
                    suggestions.append(text)
            elif isinstance(item, dict):
                value = item.get("value")
                if isinstance(value, str):
                    text = " ".join(value.split())
                    if text:
                        suggestions.append(text)

    clean: list[str] = []
    seen = set()
    for text in suggestions:
        lowered = text.lower()
        if lowered not in seen:
            seen.add(lowered)
            clean.append(text)
    return clean[:15]


def _demand_label(score: int) -> str:
    if score >= 3:
        return "High"
    if score == 2:
        return "Medium"
    return "Low"


INTENT_MARKERS = [
    "bundle",
    "worksheets",
    "activities",
    "task cards",
    "no prep",
    "printable",
    "editable",
    "lesson",
]


def _tail_type(phrase: str) -> str:
    """Classify a phrase as short-tail (<=2 words), mid (3) or long-tail (4+)."""
    tokens = len([t for t in phrase.split() if t])
    if tokens <= 2:
        return "short"
    if tokens == 3:
        return "mid"
    return "long"


def _demand_score(
    phrase: str,
    seed: str,
    sources: set[str],
    best_rank: int | None,
    surface_count: int,
) -> int:
    """Demand proxy built from real search behaviour:

    - presence in BOTH Google and TPT autocomplete (cross-source = stronger)
    - autocomplete rank position (earlier suggestions = searched more often)
    - surface_count: how many distinct queries surfaced this phrase —
      phrases that appear under several expansions are reliably in demand
    - buyer-intent markers as a small nudge
    """
    text = phrase.lower()
    score = 1
    if len(sources) >= 2:
        score += 1
    if best_rank is not None and best_rank <= 3:
        score += 1
    if surface_count >= 2:
        score += 1
    if surface_count >= 4 or any(marker in text for marker in INTENT_MARKERS):
        score += 1
    return max(1, min(5, score))


def _is_winnable(avg_top5_reviews: float | None, store_level: str) -> bool:
    if avg_top5_reviews is None:
        return True
    threshold = STORE_LEVEL_THRESHOLDS.get(store_level, STORE_LEVEL_THRESHOLDS["new_store"])
    return avg_top5_reviews <= threshold


def _competition_score(supply_count: int | None, avg_top5_reviews: float | None, store_level: str) -> int:
    targets = SUPPLY_TARGETS.get(store_level, SUPPLY_TARGETS["new_store"])
    score = 60

    if supply_count is None:
        score = 42
    elif supply_count <= targets["ideal"]:
        score = 92
    elif supply_count <= targets["stretch"]:
        score = 74
    elif supply_count <= targets["stretch"] * 2:
        score = 52
    else:
        score = 28

    if avg_top5_reviews is None:
        return max(0, min(100, score))

    threshold = STORE_LEVEL_THRESHOLDS.get(store_level, STORE_LEVEL_THRESHOLDS["new_store"])
    ratio = avg_top5_reviews / max(1, threshold)
    if ratio <= 0.7:
        score += 10
    elif ratio <= 1.0:
        score += 4
    elif ratio <= 1.5:
        score -= 12
    else:
        score -= 24

    return max(0, min(100, score))


def _opportunity_score(demand_score: int, competition_score: int, winnable_now: bool, store_level: str) -> int:
    demand_weight = 18
    demand_component = demand_score * demand_weight
    score = demand_component + int(competition_score * 0.45)

    if winnable_now:
        score += 8
    elif store_level == "new_store":
        score -= 20
    else:
        score -= 8

    return max(0, min(100, score))


def _verdict(demand_score: int, supply_count: int | None, winnable_now: bool) -> str:
    if supply_count is None:
        return "WORTH_A_SHOT"
    if demand_score >= 1 and supply_count <= 50 and winnable_now:
        return "MAKE_THIS"
    if supply_count <= 200 and winnable_now:
        return "WORTH_A_SHOT"
    return "CROWDED"


def _recommendation(
    phrase: str,
    opportunity_score: int,
    winnable_now: bool,
    supply_count: int | None,
    store_level: str,
) -> tuple[str, str, list[str]]:
    label = "Possible Next"
    reason = "Balanced opportunity. Test with a focused niche-specific version first."

    if opportunity_score >= 78 and winnable_now:
        label = "Start Here"
        reason = "Strong demand-to-competition balance for your current store level."
    elif opportunity_score < 56 or not winnable_now:
        label = "Avoid for Now"
        reason = "Competition is likely too high for your current store stage."

    starter_format = "single-skill worksheet pack"
    if "bundle" in phrase.lower() or "task cards" in phrase.lower():
        starter_format = "small focused bundle"
    elif "social story" in phrase.lower():
        starter_format = "social story mini-pack"

    step_1 = f"Make a {starter_format} targeting '{phrase}' with one clear learner outcome."
    step_2 = "Use this exact phrase at the start of title and in first two lines of description."
    step_3 = "Publish, track clicks for 7 days, then expand to 2 adjacent long-tail phrases."

    if store_level == "new_store":
        step_3 = "Publish quickly, then duplicate this format into 2 related low-competition phrases."

    if supply_count is None:
        reason = "Market supply data is limited right now. Treat this as a test keyword with low-risk product scope."

    return label, reason, [step_1, step_2, step_3]


async def _expand_queries(seed: str, expand: bool, letters_expand: bool) -> list[str]:
    """Build the query set: seed + buyer-intent modifiers (+ optional a-z).

    Alphabet-soup expansion is the standard Publisher-Rocket technique, but it
    is 26x2 autocomplete calls, so it is opt-in via letters_expand.
    """
    queries = [seed]
    if expand:
        queries += [f"{seed} {m}" for m in EXPANSION_MODIFIERS]
    if letters_expand:
        queries += [f"{seed} {c}" for c in string.ascii_lowercase]
    return queries


async def _gather_suggestions(queries: list[str]) -> dict[str, dict]:
    """Query Google + TPT autocomplete for every query and aggregate per phrase.

    Returns {phrase_lower: {text, sources, best_rank, queries}} where best_rank
    is the best 1-based position the phrase held in any suggestion list and
    queries is the set of input queries that surfaced it (surface_count).
    Autocomplete ordering is popularity-ranked, so rank and repeat surfacing
    are the strongest free demand signals available.
    """
    found: dict[str, dict] = {}

    for query in queries:
        google, tpt = await asyncio.gather(
            _google_autocomplete(query),
            _tpt_autocomplete(query),
        )
        for source, suggestions in (("google", google), ("tpt", tpt)):
            for rank, raw in enumerate(suggestions, start=1):
                normalized = " ".join(raw.split()).strip()
                if not normalized:
                    continue
                key = normalized.lower()
                entry = found.setdefault(
                    key,
                    {"text": normalized, "sources": set(), "best_rank": None, "queries": set()},
                )
                entry["sources"].add(source)
                entry["queries"].add(query.lower())
                if entry["best_rank"] is None or rank < entry["best_rank"]:
                    entry["best_rank"] = rank
        # Be polite to the suggestion endpoints.
        await asyncio.sleep(0.3)

    return found


async def find_keywords(
    seed: str,
    gold_only: bool = False,
    store_level: str = "new_store",
    winnable_only: bool = True,
    expand: bool = True,
    letters_expand: bool = False,
) -> list[KeywordResult]:
    queries = await _expand_queries(seed, expand=expand, letters_expand=letters_expand)
    found = await _gather_suggestions(queries)

    # Pre-rank phrases so only the most promising get the expensive
    # supply/review lookups on TPT search pages.
    candidates = sorted(
        found.values(),
        key=lambda e: (-len(e["queries"]), e["best_rank"] or 99),
    )

    items: list[KeywordResult] = []
    checked = 0
    for entry in candidates:
        phrase = entry["text"]
        sources = entry["sources"]
        best_rank = entry["best_rank"]
        surface_count = len(entry["queries"])
        source_hits = sorted(sources)
        demand_score = _demand_score(
            phrase=phrase,
            seed=seed,
            sources=sources,
            best_rank=best_rank,
            surface_count=surface_count,
        )

        if checked < MAX_SUPPLY_CHECKS and (demand_score >= 2 or "tpt" in sources):
            supply_count = await _tpt_supply_count(phrase)
            avg_reviews, low_reviews = await _tpt_review_metrics(phrase)
            checked += 1
        else:
            supply_count, avg_reviews, low_reviews = None, None, None
        winnable_now = _is_winnable(avg_top5_reviews=avg_reviews, store_level=store_level)
        competition_score = _competition_score(
            supply_count=supply_count,
            avg_top5_reviews=avg_reviews,
            store_level=store_level,
        )
        opportunity_score = _opportunity_score(
            demand_score=demand_score,
            competition_score=competition_score,
            winnable_now=winnable_now,
            store_level=store_level,
        )
        verdict = _verdict(demand_score=demand_score, supply_count=supply_count, winnable_now=winnable_now)
        recommendation_label, recommendation_reason, next_steps = _recommendation(
            phrase=phrase,
            opportunity_score=opportunity_score,
            winnable_now=winnable_now,
            supply_count=supply_count,
            store_level=store_level,
        )

        if verdict == "MAKE_THIS" and recommendation_label != "Start Here":
            recommendation_label = "Start Here"

        item = KeywordResult(
            phrase=phrase,
            tail_type=_tail_type(phrase),
            demand_label=_demand_label(demand_score),
            demand_score=demand_score,
            opportunity_score=opportunity_score,
            source_hits=source_hits,
            surface_count=surface_count,
            best_rank=best_rank,
            tpt_supply_count=supply_count,
            avg_top5_reviews=avg_reviews,
            lowest_page1_reviews=low_reviews,
            winnable_now=winnable_now,
            verdict=verdict,
            recommendation_label=recommendation_label,
            recommendation_reason=recommendation_reason,
            next_steps=next_steps,
        )
        items.append(item)

    if winnable_only:
        items = [x for x in items if x.winnable_now]

    items.sort(key=lambda item: item.opportunity_score, reverse=True)

    if gold_only:
        return [x for x in items if x.verdict == "MAKE_THIS"]

    return items
