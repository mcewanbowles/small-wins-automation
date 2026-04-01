from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic

from .models import (
    AuditListingRequest,
    AuditListingResponse,
    GenerateListingRequest,
    GenerateListingResponse,
)
from .settings import settings

TPT_TITLE_LIMIT = 80
TPT_TAG_LIMIT = 20
PLATFORM_RULES = {
    "tpt": {"label": "Teachers Pay Teachers", "title_limit": 80, "tag_limit": 20, "tag_char_limit": 0},
    "etsy": {"label": "Etsy", "title_limit": 140, "tag_limit": 13, "tag_char_limit": 20},
    "gumroad": {"label": "Gumroad", "title_limit": 140, "tag_limit": 0, "tag_char_limit": 0},
}

AUDIT_KEYWORDS = {
    "tpt": ["teacher", "grade", "worksheet", "printable", "intervention", "classroom", "resource"],
    "etsy": ["digital", "download", "template", "printable", "editable", "planner", "bundle"],
    "gumroad": ["creator", "instant", "download", "guide", "toolkit", "bundle", "template"],
}

AUDIT_TITLE_SIGNALS = {
    "tpt": ["activities", "worksheets", "task cards", "social stories"],
    "etsy": ["digital", "printable", "template", "editable"],
    "gumroad": ["toolkit", "bundle", "template", "guide"],
}


def _build_prompt(payload: GenerateListingRequest) -> tuple[str, str]:
    platform_key = payload.platform.lower()
    rules = PLATFORM_RULES.get(platform_key, PLATFORM_RULES["tpt"])
    platform_label = rules["label"]
    title_limit = rules["title_limit"]
    tag_limit = rules["tag_limit"]

    system = (
        f"You are an expert SEO copywriter specialising in {platform_label} listings for "
        f"{payload.niche} resources targeting {payload.buyer_type}. "
        f"Seller stage: {payload.product_stage}. Seller confidence: {payload.seller_confidence}. "
        f"You understand {platform_label} search behavior and what buyers search for. "
        "Always output valid JSON only."
    )

    user = (
        f"Generate an optimised {platform_label} listing for this product:\n\n"
        f"{payload.product_description}\n\n"
        "Return JSON with these fields:\n"
        f"- title: string (max {title_limit} characters, include top keywords near the start)\n"
        f"- tags: array of {tag_limit} strings (use empty array if platform has no tags)\n"
        "- description_opener: string (2-3 sentences, hook + main benefit + call to action)\n"
        "- description_snippet: string (first 180 chars, keyword-rich and benefit-led)\n"
        "- full_description: string (scannable listing body with short sections or bullets)\n"
        "- keyword_angles: array of 5 long-tail keyword phrases this product should target\n"
        "- gap_opportunities: array of 3 underserved angles competitors are missing"
    )

    return system, user


def _safe_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def _clip_title(title: str, title_limit: int) -> str:
    if len(title) <= title_limit:
        return title
    return title[: title_limit - 1].rstrip() + "…"


def _normalize_tags(tags: list[str], tag_limit: int, tag_char_limit: int) -> list[str]:
    if tag_limit <= 0:
        return []

    clean = []
    seen = set()

    for raw in tags:
        tag = " ".join(raw.split()).strip().lower()
        if tag_char_limit > 0:
            tag = tag[:tag_char_limit].strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        clean.append(tag)

    while len(clean) < tag_limit:
        clean.append(f"keyword {len(clean) + 1}")

    return clean[:tag_limit]


def _description_snippet(text: str) -> str:
    clean = " ".join(text.split()).strip()
    return clean[:180]


def _as_list(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(x) for x in raw]
    return []


def _suggest_audit_title(title: str, tags: list[str], title_limit: int, platform_key: str) -> tuple[str, str]:
    clean_title = " ".join(title.split()).strip()
    if not clean_title:
        clean_title = "high-converting listing title"

    preferred_phrase_map = {
        "tpt": ["social stories", "task cards", "worksheets", "activities"],
        "etsy": ["digital download", "printable", "editable template", "bundle"],
        "gumroad": ["creator toolkit", "template bundle", "instant download", "guide"],
    }
    preferred_phrases = preferred_phrase_map.get(platform_key, preferred_phrase_map["tpt"])

    lower_title = clean_title.lower()
    selected_phrase = ""
    for phrase in preferred_phrases:
        if phrase in lower_title:
            selected_phrase = phrase
            break

    if not selected_phrase:
        for tag in tags:
            for phrase in preferred_phrases:
                if phrase in tag.lower():
                    selected_phrase = phrase
                    break
            if selected_phrase:
                break

    if selected_phrase and selected_phrase not in lower_title:
        clean_title = f"{selected_phrase.title()} {clean_title}".strip()

    suggested = _clip_title(clean_title, title_limit=title_limit)

    if len(title) > title_limit:
        reason = "Shortened to fit platform title limits while keeping key search wording near the front."
    elif suggested.lower() != title.lower():
        reason = "Reordered for clearer buyer intent and stronger keyword coverage at the start."
    else:
        reason = "Your title is already solid. Use this as your current benchmark version."

    return suggested, reason


def audit_listing(payload: AuditListingRequest) -> AuditListingResponse:
    platform_key = payload.platform.lower()
    rules = PLATFORM_RULES.get(platform_key)
    if rules is None:
        raise ValueError("Unsupported platform.")

    title_limit = rules["title_limit"]
    tag_limit = rules["tag_limit"]
    title = " ".join(payload.title.split()).strip()
    tags = [" ".join(t.split()).strip().lower() for t in payload.tags if str(t).strip()]
    description = " ".join(payload.description.split()).strip()
    suggested_title, suggested_title_reason = _suggest_audit_title(title, tags, title_limit=title_limit, platform_key=platform_key)

    title_score = 0
    if len(title) <= title_limit:
        title_score += 10
    if len(title.split()) >= 4:
        title_score += 8
    title_signals = AUDIT_TITLE_SIGNALS.get(platform_key, AUDIT_TITLE_SIGNALS["tpt"])
    if any(token in title.lower() for token in title_signals):
        title_score += 7

    description_score = 0
    snippet = _description_snippet(description).lower()
    if len(description) >= 280:
        description_score += 10
    if any(token in snippet for token in ["includes", "help", "students", "teachers"]):
        description_score += 8
    if any(marker in payload.description for marker in ["-", "•", "\n"]):
        description_score += 7

    tags_score = 0
    unique_tags = list(dict.fromkeys(tags))
    if tag_limit > 0:
        if len(unique_tags) >= tag_limit:
            tags_score += 15
        elif len(unique_tags) >= max(1, int(tag_limit * 0.75)):
            tags_score += 10
        elif len(unique_tags) >= max(1, int(tag_limit * 0.5)):
            tags_score += 6
        if any(" " in t for t in unique_tags):
            tags_score += 10
    else:
        if len(unique_tags) == 0:
            tags_score = 25
        else:
            tags_score = 10

    seo_coverage_score = 0
    keyword_hits = 0
    tokens = AUDIT_KEYWORDS.get(platform_key, AUDIT_KEYWORDS["tpt"])
    for token in tokens:
        in_title = token in title.lower()
        in_tags = any(token in t for t in unique_tags)
        in_desc = token in description.lower()
        if in_title or in_tags or in_desc:
            keyword_hits += 1
    if keyword_hits >= 6:
        seo_coverage_score = 25
    elif keyword_hits >= 4:
        seo_coverage_score = 18
    elif keyword_hits >= 2:
        seo_coverage_score = 10
    else:
        seo_coverage_score = 4

    score_total = max(0, min(100, title_score + description_score + tags_score + seo_coverage_score))

    fixes = []
    if len(title) > title_limit:
        fixes.append(f"Shorten title to {title_limit} characters or less.")
    if tag_limit > 0 and len(unique_tags) < tag_limit:
        fixes.append(f"Use all {tag_limit} tags to avoid leaving SEO capacity unused.")
    if tag_limit == 0 and unique_tags:
        fixes.append("This platform does not use tags in this workflow. Focus title + description quality.")
    if len(description) < 280:
        fixes.append("Expand description with bullet points and clear what-is-included details.")
    if tag_limit > 0 and not any(" " in t for t in unique_tags):
        fixes.append("Use more long-tail multi-word tags, not only single-word tags.")
    if not fixes:
        fixes.append("Strong listing foundation. Test one higher-intent keyword near the start of title.")

    return AuditListingResponse(
        score_total=score_total,
        title_score=title_score,
        description_score=description_score,
        tags_score=tags_score,
        seo_coverage_score=seo_coverage_score,
        suggested_title=suggested_title,
        suggested_title_reason=suggested_title_reason,
        top_fixes=fixes[:5],
    )


def generate_listing(payload: GenerateListingRequest) -> GenerateListingResponse:
    platform_key = payload.platform.lower()
    rules = PLATFORM_RULES.get(platform_key)
    if rules is None:
        raise ValueError("Unsupported platform.")

    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is missing. Add it to backend/.env.")

    system, user = _build_prompt(payload)

    client = Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    text_chunks = []
    for block in message.content:
        maybe_text = getattr(block, "text", None)
        if maybe_text:
            text_chunks.append(maybe_text)

    data = _safe_json("\n".join(text_chunks))

    title = _clip_title(str(data.get("title", "")), title_limit=rules["title_limit"])
    tags = _normalize_tags(
        _as_list(data.get("tags", [])),
        tag_limit=rules["tag_limit"],
        tag_char_limit=rules["tag_char_limit"],
    )
    description_opener = str(data.get("description_opener", "")).strip()
    description_snippet = str(data.get("description_snippet", "")).strip()
    if not description_snippet:
        description_snippet = _description_snippet(description_opener)
    full_description = str(data.get("full_description", "")).strip()
    if not full_description:
        full_description = description_opener
    keyword_angles = _as_list(data.get("keyword_angles", []))[:5]
    gap_opportunities = _as_list(data.get("gap_opportunities", []))[:3]

    return GenerateListingResponse(
        title=title,
        title_chars=len(title),
        title_limit=rules["title_limit"],
        tags=tags,
        tags_count=len(tags),
        tags_limit=rules["tag_limit"],
        description_opener=description_opener,
        description_snippet=description_snippet,
        full_description=full_description,
        keyword_angles=keyword_angles,
        gap_opportunities=gap_opportunities,
    )
