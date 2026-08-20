from __future__ import annotations

import html
import re
from collections import Counter
from urllib.parse import quote_plus

import httpx

from .models import ReverseIntelListing, ReverseIntelResponse

TPT_SEARCH_URL = "https://www.teacherspayteachers.com/search?search={query}"

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "your",
}


def _normalize_title(text: str) -> str:
    cleaned = " ".join(text.split())
    cleaned = cleaned.replace("\u2019", "'")
    return cleaned.strip()


def _extract_titles(html_text: str, limit: int) -> list[str]:
    patterns = [
        r"\"title\"\s*:\s*\"([^\"]+)\"",
        r"data-title=\"([^\"]+)\"",
        r"aria-label=\"([^\"]+)\"",
        r"<h3[^>]*>([^<]+)</h3>",
    ]

    seen: set[str] = set()
    titles: list[str] = []

    for pattern in patterns:
        for match in re.finditer(pattern, html_text, flags=re.IGNORECASE):
            raw = match.group(1)
            if not raw:
                continue
            unescaped = html.unescape(raw)
            title = _normalize_title(unescaped)
            lowered = title.lower()
            if not title or lowered in seen:
                continue
            seen.add(lowered)
            titles.append(title)
            if len(titles) >= limit:
                return titles

    return titles[:limit]


def _tokenize(title: str) -> list[str]:
    text = title.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [token for token in text.split() if token and token not in _STOPWORDS]
    return tokens


def _extract_ngrams(tokens: list[str], n: int) -> list[str]:
    if len(tokens) < n:
        return []
    return [" ".join(tokens[i : i + n]) for i in range(0, len(tokens) - n + 1)]


def _angle_phrases(titles: list[str]) -> list[str]:
    counts: Counter[str] = Counter()

    for title in titles:
        tokens = _tokenize(title)
        for n in (2, 3, 4):
            counts.update(_extract_ngrams(tokens, n))

    candidates = [phrase for phrase, count in counts.items() if count >= 2]
    candidates.sort(key=lambda phrase: (counts[phrase], len(phrase)), reverse=True)

    chosen: list[str] = []
    for phrase in candidates:
        if any(phrase in existing or existing in phrase for existing in chosen):
            continue
        chosen.append(phrase)
        if len(chosen) >= 12:
            break

    return chosen


def _build_angles(keyword: str, phrases: list[str]) -> list[str]:
    if not phrases:
        return [
            f"Scan the top listings for '{keyword}' and note repeated grade/skill terms.",
            "Try adding a specific learner/format term (e.g., 'task cards', 'worksheets', 'no prep').",
        ]

    angles: list[str] = []
    for phrase in phrases[:8]:
        angles.append(f"Build a focused product around: {phrase}")

    angles.append("Match the wording: use 1 repeated phrase near the start of your title.")
    angles.append("Differentiate: keep the phrase but add one clear niche qualifier (grade, skill, audience).")

    return angles


async def reverse_seller_intel(keyword: str, limit: int = 18) -> ReverseIntelResponse:
    query = quote_plus(keyword)
    url = TPT_SEARCH_URL.format(query=query)

    timeout = httpx.Timeout(12.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            },
        )

    if response.status_code >= 400:
        raise RuntimeError(f"TPT request failed with status {response.status_code}")

    titles = _extract_titles(response.text, limit=limit)
    phrases = _angle_phrases(titles)
    angles = _build_angles(keyword=keyword, phrases=phrases)

    listings = [ReverseIntelListing(rank=index + 1, title=title) for index, title in enumerate(titles)]

    return ReverseIntelResponse(
        keyword=keyword,
        listings=listings,
        recurring_phrases=phrases,
        angles=angles,
    )
