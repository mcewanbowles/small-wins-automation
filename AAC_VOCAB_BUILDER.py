"""
AAC_VOCAB_BUILDER.py — PATCHED per Aug 2026 vocab-guardrails brief
Small Wins Studio — AI-Powered Vocab Identification + Ambiguity Checker

DROP THIS FILE IN:
    D:\\Seagate\\small-wins-automation\\
    (replaces the old AAC_VOCAB_BUILDER.py — same location, same name)

REQUIRES: pip install anthropic

═══════════════════════════════════════════════════════════════════════════
WHAT CHANGED FROM THE OLD VERSION — READ THIS FIRST
═══════════════════════════════════════════════════════════════════════════

1. MODEL FIXED: was hardcoded to claude-sonnet-4-6. Now uses claude-sonnet-5,
   the locked/confirmed model everywhere else in StudioForge.

2. NO MORE DIRECT WRITES TO book_vocab.json. The old script overwrote your
   real vocab file the instant the API call returned, with no human ever
   looking at it first. This version writes to a separate per-book file:
       assets/themes/{slug}/needs_review_vocab.json
   book_vocab.json (and the master BoardReady file) are ONLY touched when
   you explicitly run this script again with --promote <slug> or
   --promote-all, after you've reviewed the content. Nothing gets promoted
   silently, ever.

3. FOUR NEW GUARDRAIL FIELDS, because "grounded: true" alone doesn't tell
   you whether the vocabulary is actually right for the book — it just
   tells you a search happened.
     a) book_summary       — 2–3 sentence plot summary from the search
                              results. You already know most of these
                              books; a wrong/generic summary is instantly
                              obvious and costs you 3 seconds to catch.
     b) author + pub_year  — shown next to the summary. Wrong author =
                              wrong book got searched, immediately visible.
     c) fringe_justifications — one line per fringe word explaining why
                              it's in THIS book (tied to a scene/character/
                              object), not just a bare word list.
     d) confidence_flag    — "grounded: true" is now necessary but not
                              sufficient. See PRE-FLIGHT IDENTITY CHECK
                              below for the cheap way to catch a
                              wrong-book-entirely search before spending a
                              full vocab call on it.

4. PRE-FLIGHT IDENTITY CHECK — new, separate, cheap mode. Run this FIRST on
   any batch of new/unfamiliar titles (worth it especially for the
   behaviour/back-to-school books sourced from outside lists, since a few
   of those titles are obscure enough that grounding could latch onto the
   wrong book entirely). It does one lightweight search-only call per book
   — title/author/year/one-line-summary — and writes a single skimmable
   report. No vocab, no icons, no full API cost. Catch a misidentified book
   before spending a real vocab-generation call on it.

USAGE:
    # Step 0 (recommended for new/unfamiliar titles) — cheap identity pass
    python AAC_VOCAB_BUILDER.py --identity-check --missing-only

    # Step 1 — generate vocab into the REVIEW file (never touches real vocab)
    python AAC_VOCAB_BUILDER.py --missing-only
    python AAC_VOCAB_BUILDER.py --book personal_space_camp
    python AAC_VOCAB_BUILDER.py --dry-run
    python AAC_VOCAB_BUILDER.py --overwrite     # re-run even if reviewed vocab exists

    # Step 2 — YOU read AAC_VOCAB_REPORT.md and/or the per-book
    #          needs_review_vocab.json files. Check: does the summary match
    #          the real book? Is the author right? Do the fringe words and
    #          their justifications make sense?

    # Step 3 — only after you're satisfied, promote into the real vocab file
    python AAC_VOCAB_BUILDER.py --promote personal_space_camp
    python AAC_VOCAB_BUILDER.py --promote-all      # promotes every book that
                                                    # currently has a
                                                    # needs_review_vocab.json

COST: ~$0.02-0.05 per book for full vocab (Claude Sonnet, cached).
      ~$0.005-0.01 per book for the identity-check-only pass.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime


def configure_safe_stdio():
    """Make status output non-fatal on Windows consoles using cp1252."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(errors="backslashreplace")
            except (AttributeError, ValueError):
                pass


configure_safe_stdio()

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed.")
    print("Run: pip install anthropic")
    sys.exit(1)

# ─── PATHS ────────────────────────────────────────────────────────────────────

ROOT        = Path(__file__).resolve().parent
REPO_ROOT   = ROOT if (ROOT / "assets").exists() else ROOT.parent
THEMES_DIR  = REPO_ROOT / "assets" / "themes"
VOCAB_FILE  = REPO_ROOT / "BoardReady" / "boardready" / "vocab" / "book_vocab.json"
SYMBOLS_PNG = REPO_ROOT / "assets" / "symbols" / "png"
GLOBAL_CORE = REPO_ROOT / "assets" / "global" / "aac_core"

REPORT_FILE          = ROOT / "AAC_VOCAB_REPORT.md"
IDENTITY_REPORT_FILE = ROOT / "AAC_IDENTITY_CHECK.md"
REVIEW_FILENAME      = "needs_review_vocab.json"   # per-book, NOT book_vocab.json

# GUARDRAIL: this is the confirmed/locked model everywhere else in
# StudioForge. Do not change without updating every other generator too.
MODEL_NAME = "claude-sonnet-5"

# ─── ANTHROPIC CLIENT ─────────────────────────────────────────────────────────

def get_client():
    api_key = (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("CLAUDE_API_KEY")
        or os.environ.get("ANTHROPIC_KEY")
        or ""
    )
    if not api_key:
        for env_path in [ROOT / ".env", REPO_ROOT / ".env"]:
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    k, _, v = line.partition("=")
                    if k.strip() in ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_KEY"):
                        api_key = v.strip().strip('"').strip("'")
                        break
                if api_key:
                    break
    if not api_key:
        print("ERROR: No ANTHROPIC_API_KEY found.")
        print("Set it as an environment variable or add to .env file:")
        print("  ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


# ─── SYMBOL LIBRARY SCAN ──────────────────────────────────────────────────────

def get_available_symbols(max_sample=2000):
    symbols = set()
    for p in list(SYMBOLS_PNG.glob("*.png"))[:500]:
        symbols.add(p.stem.lower())
    alpha = SYMBOLS_PNG / "Alpha"
    if alpha.exists():
        count = 0
        for sub in sorted(alpha.iterdir()):
            if sub.is_dir():
                for p in sub.glob("*.png"):
                    symbols.add(p.stem.lower())
                    count += 1
                    if count >= max_sample:
                        break
    return sorted(symbols)[:max_sample]


# ─── LOAD EXISTING VOCAB ──────────────────────────────────────────────────────

def load_boardready_vocab():
    if VOCAB_FILE.exists():
        try:
            with open(VOCAB_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def load_theme_vocab(slug, master_entry=None):
    """Return master metadata overlaid with the more accurate per-theme record."""
    merged = dict(master_entry or {})
    path = THEMES_DIR / slug / "book_vocab.json"
    if path.exists():
        try:
            local = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(local, dict):
                raise ValueError("book_vocab.json must contain a JSON object")
            merged.update(local)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"  WARNING: could not load {path}: {exc}", file=sys.stderr)
    return merged


def get_existing_icons(slug):
    ai_dir = THEMES_DIR / slug / "activity_images"
    if not ai_dir.exists():
        return []
    return [p.stem for p in sorted(ai_dir.glob("*.png"))]


def get_book_title_from_slug(slug):
    return slug.replace("_", " ").title()


def load_review_file(slug):
    """Load this book's needs_review_vocab.json if it exists."""
    p = THEMES_DIR / slug / REVIEW_FILENAME
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


# ─── CLAUDE API CALLS ──────────────────────────────────────────────────────────

FULL_SYSTEM_PROMPT = """You are a specialist in AAC (Augmentative and Alternative Communication)
for children with autism and SPED. You help identify vocabulary for AAC communication boards
that accompany children's picture books used in classrooms.

CRITICAL — GROUNDING REQUIREMENT:
Before generating any vocabulary, you MUST use the web_search tool to confirm this specific
book's actual plot, characters, and content. Do NOT rely on your training data alone, even if
you believe you already know the book well — well-known titles and obscure titles are equally
in scope for this rule. Search for the book title + author, and if the first result doesn't
give a clear scene-by-scene or character-by-character account, search again with a different
query (e.g. "[title] summary", "[title] characters list", "[title] read aloud").

Only after search results confirm the book's real content should you generate vocabulary.
If search results are thin, contradictory, or you remain unsure of specific details (e.g. the
exact sequence of characters/animals in the book), you MUST still return your best answer, but
set "grounded": false and explain what's uncertain in "grounding_note". Never silently guess
and report full confidence — a flagged uncertain answer is far more useful than an unflagged
wrong one.

IMPORTANT — "grounded: true" means a search happened, NOT that the vocabulary is guaranteed
correct. A search can return the wrong book entirely (a same-named book, a movie tie-in, a
different edition). This is why you must ALSO return book_summary, author, and pub_year — a
human reviewer who knows the real book can catch a misidentified book from the summary alone,
even when grounded is technically true.

BOARD FORMAT (US Letter landscape, 6 columns × 6 rows = 36 cells):
  Row 1: I / you / want / see / YES / NO          ← fixed core
  Row 2: same / different / more / help / like / don't like  ← fixed core
  Row 3: HERO + fringe words 1-5                  ← HERO always in slot 1
  Row 4: fringe words 6-11                        ← remaining fringe
  Row 5: go / stop / choose / colour / read / think  ← fixed core
  Row 6: uh oh / what / where / why / I don't know / finished  ← fixed core

Fringe = 1 hero image + 11 book-specific words = 12 total.
Fringe words CAN include colours and descriptive nouns where relevant to the book.

You respond ONLY with valid JSON. No preamble, no explanation, no markdown fences."""


def build_full_user_prompt(slug, title, author, existing_icons, existing_vocab, existing_extras, symbol_sample):
    icons_str  = ", ".join(existing_icons) if existing_icons else "none found"
    vocab_str  = ", ".join(existing_vocab) if existing_vocab else "not set"
    extras_str = ", ".join(existing_extras) if existing_extras else "not set"
    sample_str = ", ".join(symbol_sample[:300]) if symbol_sample else "unknown"

    return f"""Book: "{title}" by {author}
Slug: {slug}

EXISTING DATA:
- Icons already in activity_images/: {icons_str}
- Existing activity_images vocab: {vocab_str}
- Existing aac_extras: {extras_str}

AVAILABLE SYMBOL FILENAMES (sample from PNG library):
{sample_str}

TASK:
Generate the complete AAC board vocabulary for this book's communication board.
The board fringe zone is exactly 12 slots: slot 1 = HERO, slots 2-12 = book words (11 words).

Return JSON with this exact structure:
{{
  "title": "Full book title",
  "author": "Author name",
  "pub_year": "Year first published, or your best estimate if uncertain — never leave blank",
  "book_summary": "2-3 sentence plot summary confirmed via web search. This is a guardrail field — a human reviewer who knows the book should be able to read this and instantly confirm or reject that you found the right book.",
  "hero": {{
    "name": "Pete the Cat",
    "description": "Blue cat with white shoes, distinctive Eric Litwin character",
    "search_term": "pete cat",
    "needs_sourcing": true,
    "source_note": "Named character — source from Creative Fabrica or TPT clip art"
  }},
  "fringe_11": [
    "word1", "word2", "word3", "word4", "word5", "word6",
    "word7", "word8", "word9", "word10", "word11"
  ],
  "fringe_12": [
    "Pete the Cat", "word1", "word2", "word3", "word4", "word5",
    "word6", "word7", "word8", "word9", "word10", "word11"
  ],
  "fringe_justifications": {{
    "word1": "One sentence tying this word to a specific scene, character, or object in the book — not a generic reason. E.g. \\"bed - Baby Llama can't sleep and repeatedly gets out of bed, this is a central recurring image\\"."
  }},
  "ambiguous": [
    {{
      "word": "fly",
      "issue": "Could mean insect (noun) or action (verb)",
      "preferred": "fly insect",
      "reason": "Book is about animals, insect meaning is correct"
    }}
  ],
  "character_images_needed": ["character name if needs sourced PNG, else empty list"],
  "icon_search_terms": {{
    "word1": "best search term to find PNG in Boardmaker library",
    "word2": "search term"
  }},
  "grounded": true,
  "grounding_note": "Confirmed via search: [what you found]. OR if grounded=false: [what remains uncertain and why]",
  "notes": "Any important notes about this book's vocabulary or special considerations"
}}

RULES for book_summary:
- Must be specific to THIS book — named characters, the actual central conflict/event.
- A generic summary that could describe several different books is a red flag; if search
  results are too thin for a specific summary, say so in grounding_note rather than padding
  with vague language.

RULES for fringe_justifications:
- Every word in fringe_11 must have an entry here.
- Reference a specific scene, character, or object — "used throughout the book" is too vague.
- If you cannot justify a word this specifically, replace it with a word you can justify.

RULES for hero:
- EVERY book must have a hero — the main character a SPED student will recognise from the cover
- If the hero is a NAMED/DISTINCTIVE character (Pete the Cat, Stellaluna, The Very Hungry Caterpillar,
  Elmer, The Gruffalo, David from No David): set needs_sourcing=true — generic Boardmaker won't match
- If the hero is a GENERIC animal that Boardmaker covers well (a brown bear, a frog, a duck):
  set needs_sourcing=false and give a specific search_term like "brown bear" or "frog"
- For books where colour is part of the character (Brown Bear = brown, Elmer = patchwork):
  note this in description and set needs_sourcing=true if Boardmaker generic won't match

RULES for fringe_11 (the 11 book-specific words, NOT including hero):
- Return exactly 11 unique, nonblank words; fringe_12 must be exactly the nonblank hero name followed by those same 11 words in the same order.
- Choose the 11 MOST USEFUL story-specific words: concrete nouns, clearly picturable actions, picturable descriptors, and central emotions are allowed.
- Colours and descriptors ARE allowed only where central to the story
  (e.g. "red" for Red Bird in Brown Bear, "striped" for Aliens Love Underpants).
- Central emotions such as sad, worried, angry, proud, or scared are allowed when tied to a specific scene or conflict.
- Avoid ALL fixed core words: I, you, want, see, yes, no, same, different, more, help,
  like, don't like, go, stop, choose, colour, read, think, uh oh, what, where, why,
  I don't know, finished.
- NEVER select function words: prepositions/locatives/position words, pronouns,
  articles, conjunctions, auxiliary verbs, or determiners (including between, there,
  here, under, over, above, below, next to, behind, in front of, through, around,
  and, but, or, the, a, an, it, this, that, these, those).
- Reject vague abstractions and generic filler such as thing, stuff, something, feel,
  good, nice, fun, idea, way, time, do, make, get, have, be, or special. Every selection must
  map to one clear image and a specific scene, character, object, action, descriptor,
  or central emotion in THIS story.
- fringe_justifications and icon_search_terms must contain a nonblank, story-specific
  value for every fringe word. Generic claims such as "important in the story" fail.

RULES for ambiguous:
- Flag ANY word that could map to multiple very different images
- Examples: fly (insect vs action), bat (animal vs sport), fall (season vs action),
  light (lamp vs adjective), bear (animal vs verb), glasses (eyewear vs drinking),
  duck (bird vs action), bark (tree vs dog sound), wave (water vs greeting),
  crane (bird vs machine), pitcher (jug vs baseball), pool (swimming vs billiards)
- For each ambiguous word, state which meaning is correct for THIS book and the preferred search term

RULES for character_images_needed:
- List every character where needs_sourcing=true from the hero field
- Also list any secondary named characters that appear on the fringe (e.g. "Mama Bear" in Brown Bear)
- Generic animals do NOT go here"""


IDENTITY_SYSTEM_PROMPT = """You confirm the identity of children's picture books for an AAC
product catalogue. You MUST use the web_search tool at least once — do not answer from memory
alone, even for a book you're confident you know.

Respond ONLY with valid JSON, no preamble, no markdown fences:
{
  "slug_guess_correct": true,
  "title": "Confirmed full title",
  "author": "Confirmed author",
  "pub_year": "Year, or best estimate",
  "one_line_summary": "One sentence: the central character and central event/conflict.",
  "confidence": "high | medium | low",
  "concern": "Empty string if none, otherwise a short note — e.g. 'Multiple books share this title, confirmed via [detail] that this is the [author] version' or 'Could not find this exact title, closest match was X'."
}"""


def _extract_text(response):
    return "\n".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    ).strip()


def _parse_json_response(response):
    raw = _extract_text(response)
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    return json.loads(raw, strict=False)


def call_claude_full(client, slug, title, author, existing_icons, existing_vocab, existing_extras, symbol_sample):
    """Full vocab generation call. Returns (parsed_json_dict, error_string_or_None)."""
    prompt = build_full_user_prompt(
        slug, title, author, existing_icons, existing_vocab, existing_extras, symbol_sample
    )
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=16000,
            system=FULL_SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2}],
            messages=[{"role": "user", "content": prompt}],
        )
        parsed = _parse_json_response(response)

        searches_used = sum(
            1 for block in response.content
            if getattr(block, "type", None) == "server_tool_use" and getattr(block, "name", None) == "web_search"
        )
        parsed["_searches_used"] = searches_used
        if searches_used == 0:
            print(f"\n    ⚠️  NO SEARCHES PERFORMED — Claude answered without grounding despite instructions")
            parsed["grounded"] = False
            parsed["grounding_note"] = (parsed.get("grounding_note", "") + " [No web_search calls detected]").strip()
        elif not parsed.get("grounded", False):
            print(f"\n    ⚠️  UNGROUNDED — {parsed.get('grounding_note', 'no reason given')}")

        return parsed, None

    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"
    except Exception as e:
        return None, f"API error: {e}"


def call_claude_identity(client, slug, title_guess, author_guess="Unknown"):
    """Cheap identity-only call. Returns (parsed_json_dict, error_string_or_None)."""
    prompt = (
        f'Book slug: "{slug}"\nGuessed title: "{title_guess}"\n'
        f'Supplied author: "{author_guess or "Unknown"}"\n\n'
        "Confirm this book's real identity via web search, using the supplied author to disambiguate it."
    )
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=500,
            system=IDENTITY_SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2}],
            messages=[{"role": "user", "content": prompt}],
        )
        parsed = _parse_json_response(response)
        searches_used = sum(
            1 for block in response.content
            if getattr(block, "type", None) == "server_tool_use" and getattr(block, "name", None) == "web_search"
        )
        parsed["_searches_used"] = searches_used
        return parsed, None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"
    except Exception as e:
        return None, f"API error: {e}"


# ─── VALIDATION GUARDRAILS ────────────────────────────────────────────────────

FUNCTION_WORD_BLOCKLIST = {
    "between", "there", "here", "under", "over", "above", "below",
    "next to", "behind", "in front of", "through", "around", "across",
    "beside", "inside", "outside", "near", "far", "up", "down", "and",
    "but", "or", "nor", "so", "yet", "the", "a", "an", "it", "this",
    "that", "these", "those", "he", "she", "they", "we", "me", "him",
    "her", "them", "us", "my", "your", "his", "their", "our", "of",
    "to", "for", "with", "at", "by", "on", "in", "from", "as", "if",
    "is", "am", "are", "was", "were", "be", "been", "being", "has",
    "had", "does", "did", "can", "could", "would", "should", "will",
}

FIXED_CORE_WORDS = {
    "i", "you", "want", "see", "yes", "no", "same", "different", "more",
    "help", "like", "don't like", "dont like", "go", "stop", "choose",
    "colour", "color", "read", "think", "uh oh", "what", "where", "why",
    "i don't know", "i dont know", "don't know", "dont know", "finished",
}

VAGUE_FILLER_BLOCKLIST = {
    "thing", "things", "stuff", "something", "anything", "everything",
    "feel", "feeling", "good", "nice", "fun", "idea", "way", "time",
    "do", "make", "get", "have", "very", "really", "special",
}


def _clean_word(word):
    return " ".join(str(word).strip().lower().replace("’", "'").split())


def validate_fringe_words(result):
    """Return locally banned fringe words; concrete actions/emotions remain valid."""
    banned = FUNCTION_WORD_BLOCKLIST | FIXED_CORE_WORDS | VAGUE_FILLER_BLOCKLIST
    return [w for w in result.get("fringe_11", []) if _clean_word(w) in banned]


def _is_story_specific_justification(value):
    text = " ".join(str(value).strip().lower().split())
    generic_phrases = ("important in the story", "used throughout the book", "used in the story")
    return len(text) >= 20 and not any(phrase in text for phrase in generic_phrases)


def validate_vocab_structure(result, require_support=False):
    """Validate the deterministic parts of the 12-slot fringe contract."""
    errors = []
    fringe_11 = result.get("fringe_11")
    fringe_12 = result.get("fringe_12")
    hero = result.get("hero") if isinstance(result.get("hero"), dict) else {}
    hero_name = str(hero.get("name", "")).strip()
    if not hero_name:
        errors.append("hero name is blank")
    if not isinstance(fringe_11, list) or len(fringe_11) != 11:
        errors.append("fringe_11 must contain exactly 11 words")
        fringe_11 = fringe_11 if isinstance(fringe_11, list) else []
    if any(not str(word).strip() for word in fringe_11):
        errors.append("fringe_11 contains a blank word")
    cleaned = [_clean_word(word) for word in fringe_11]
    if len(cleaned) != len(set(cleaned)):
        errors.append("fringe_11 contains duplicate words")
    banned = validate_fringe_words({"fringe_11": fringe_11})
    if banned:
        errors.append(f"fringe_11 contains banned core/function/filler words: {banned}")
    expected_12 = [hero_name] + fringe_11
    if not isinstance(fringe_12, list) or len(fringe_12) != 12:
        errors.append("fringe_12 must contain exactly hero + 11 words")
    elif fringe_12 != expected_12:
        errors.append("fringe_12 must be the hero name followed by fringe_11 in order")
    if require_support:
        justifications = result.get("fringe_justifications", {})
        search_terms = result.get("icon_search_terms", {})
        if not isinstance(justifications, dict):
            justifications = {}
        if not isinstance(search_terms, dict):
            search_terms = {}
        for word in fringe_11:
            if not _is_story_specific_justification(justifications.get(word, "")):
                errors.append(f"missing story-specific justification for '{word}'")
            if not str(search_terms.get(word, "")).strip():
                errors.append(f"missing icon search term for '{word}'")
    return errors


def validate_guardrail_fields(result):
    """GUARDRAIL: flag missing research/support fields without blocking a draft."""
    warnings = []
    if not str(result.get("book_summary", "")).strip():
        warnings.append("missing book_summary")
    if not str(result.get("author", "")).strip() or result.get("author") == "Unknown":
        warnings.append("missing/unknown author")
    if not str(result.get("pub_year", "")).strip():
        warnings.append("missing pub_year")
    justifications = result.get("fringe_justifications", {})
    search_terms = result.get("icon_search_terms", {})
    for word in result.get("fringe_11", []):
        if not isinstance(justifications, dict) or not _is_story_specific_justification(justifications.get(word, "")):
            warnings.append(f"no story-specific justification for fringe word '{word}'")
        if not isinstance(search_terms, dict) or not str(search_terms.get(word, "")).strip():
            warnings.append(f"no icon search term for fringe word '{word}'")
    return warnings


def validate_review_entry(entry):
    """Return all reasons a needs-review entry cannot be promoted."""
    errors = validate_vocab_structure(entry, require_support=True)
    if entry.get("grounded") is not True:
        errors.append("entry is not grounded")
    try:
        searches_used = int(entry.get("searches_used", 0))
    except (TypeError, ValueError):
        searches_used = 0
    if searches_used < 1:
        errors.append("searches_used must be at least 1")
    if entry.get("guardrail_warnings"):
        errors.append("guardrail_warnings must be resolved before promotion")
    return errors


# ─── SAVE TO REVIEW FILE (never touches real book_vocab.json) ────────────────

def save_needs_review(slug, result, existing_entry):
    """
    GUARDRAIL: writes ONLY to assets/themes/{slug}/needs_review_vocab.json.
    Does NOT touch book_vocab.json or the master BoardReady file.
    Use --promote / --promote-all to move reviewed content into real vocab.
    """
    hero = result.get("hero", {})
    fringe_display = result.get("fringe_12", [])

    # Begin with the local record so campaign, rights/research, schema, slug,
    # demand-candidate, and production-blocking metadata survive regeneration.
    entry = dict(existing_entry)
    entry.update({
        "title":            existing_entry.get("title") or result.get("title", get_book_title_from_slug(slug)),
        "author":           existing_entry.get("author") or result.get("author", ""),
        "pub_year":         result.get("pub_year", ""),
        "book_summary":     result.get("book_summary", ""),
        "hero": {
            "name":           hero.get("name", ""),
            "description":    hero.get("description", ""),
            "search_term":    hero.get("search_term", ""),
            "needs_sourcing": hero.get("needs_sourcing", False),
            "source_note":    hero.get("source_note", ""),
        },
        "fringe_12":              fringe_display,
        "fringe_11":              result.get("fringe_11", []),
        "fringe_justifications":  result.get("fringe_justifications", {}),
        "activity_images":        fringe_display[1:7],
        "aac_extras":             fringe_display[7:],
        "ambiguous":              result.get("ambiguous", []),
        "character_images_needed": result.get("character_images_needed", []),
        "icon_search_terms":      result.get("icon_search_terms", {}),
        "notes":                  existing_entry.get("notes") or result.get("notes", ""),
        "characters":             existing_entry.get("characters", []),
        "code":                   existing_entry.get("code", ""),
        "board_format":           "6x6_LETTER_hero_fringe",
        "vocab_generated":        datetime.now().strftime("%Y-%m-%d"),
        "grounded":               result.get("grounded", False),
        "grounding_note":         result.get("grounding_note", ""),
        "searches_used":          result.get("_searches_used", 0),
        "guardrail_warnings":     validate_guardrail_fields(result),
        "vocab_status":           "pending_human_review",
    })

    review_path = THEMES_DIR / slug / REVIEW_FILENAME
    review_path.parent.mkdir(parents=True, exist_ok=True)
    with open(review_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)

    return entry


# ─── PROMOTE — the only path that writes real book_vocab.json ───────────────

def promote_book(slug):
    """
    Copy assets/themes/{slug}/needs_review_vocab.json into the real
    book_vocab.json (per-book AND master file). This is the ONLY function
    in this whole script that touches real vocab. Only call it after you've
    personally reviewed the review file / report.
    """
    review_path = THEMES_DIR / slug / REVIEW_FILENAME
    if not review_path.exists():
        print(f"  ⏭  {slug:45s} no needs_review_vocab.json found, skipping")
        return False

    try:
        review_entry = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"  REFUSED {slug:45s} invalid review JSON: {exc}")
        return False
    errors = validate_review_entry(review_entry)
    if errors:
        print(f"  REFUSED {slug:45s} review validation failed:")
        for error in errors:
            print(f"    - {error}")
        return False

    # Re-read the current local record so metadata added after draft generation
    # is also retained. Only review-owned vocab/research fields may replace it.
    current_local = load_theme_vocab(slug)
    review_owned_fields = {
        "pub_year", "book_summary", "hero", "fringe_12", "fringe_11",
        "fringe_justifications", "activity_images", "aac_extras", "ambiguous",
        "character_images_needed", "icon_search_terms", "characters", "code",
        "board_format", "vocab_generated", "grounded", "grounding_note",
        "searches_used", "guardrail_warnings",
    }
    entry = dict(review_entry)
    for key, value in current_local.items():
        if key not in review_owned_fields:
            entry[key] = value
    # Never clear a production block as a side effect of vocab approval.
    if current_local.get("production_blocked") is True or review_entry.get("production_blocked") is True:
        entry["production_blocked"] = True
    entry["vocab_status"] = "human_approved"
    entry["promoted_date"] = datetime.now().strftime("%Y-%m-%d")

    # 1. Per-book real vocab file
    book_vocab_path = THEMES_DIR / slug / "book_vocab.json"
    with open(book_vocab_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)

    # 2. Master BoardReady vocab file
    if VOCAB_FILE.exists():
        try:
            with open(VOCAB_FILE, encoding="utf-8") as f:
                all_vocab = json.load(f)
        except Exception:
            all_vocab = {}
    else:
        VOCAB_FILE.parent.mkdir(parents=True, exist_ok=True)
        all_vocab = {}
    all_vocab[slug] = entry
    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(all_vocab, f, indent=2, ensure_ascii=False)

    print(f"  ✅ {slug:45s} promoted to real book_vocab.json")
    return True


# ─── DISCOVER BOOKS ───────────────────────────────────────────────────────────

def discover_books():
    if not THEMES_DIR.exists():
        print(f"❌ Themes folder not found: {THEMES_DIR}")
        sys.exit(1)
    return sorted(
        [d for d in THEMES_DIR.iterdir()
         if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")],
        key=lambda x: x.name.lower()
    )


def focus_books(books, manifest_path):
    """Filter discovered theme directories to a validated focus manifest's order."""
    path = Path(manifest_path)
    if not path.is_file():
        raise FileNotFoundError(f"focus manifest not found: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid focus manifest {path}: {exc}") from exc
    records = manifest.get("focus_books") if isinstance(manifest, dict) else None
    if not isinstance(records, list) or not records:
        raise ValueError(f"invalid focus manifest {path}: focus_books must be a non-empty list")
    slugs = []
    for index, record in enumerate(records):
        slug = record.get("slug") if isinstance(record, dict) else None
        if not isinstance(slug, str) or not slug.strip():
            raise ValueError(f"invalid focus manifest {path}: focus_books[{index}].slug is required")
        slug = slug.strip()
        if slug in slugs:
            raise ValueError(f"invalid focus manifest {path}: duplicate slug '{slug}'")
        slugs.append(slug)
    by_slug = {book.name: book for book in books}
    missing = [slug for slug in slugs if slug not in by_slug]
    return [by_slug[slug] for slug in slugs if slug in by_slug], missing


def has_real_vocab(slug, all_vocab):
    """Has this book already been PROMOTED to real vocab? (needs_review doesn't count)"""
    if slug in all_vocab and all_vocab[slug].get("fringe_12"):
        return True
    per_book = THEMES_DIR / slug / "book_vocab.json"
    if per_book.exists():
        try:
            data = json.loads(per_book.read_text(encoding="utf-8"))
            return bool(data.get("fringe_12"))
        except Exception:
            pass
    return False


def has_pending_review(slug):
    return (THEMES_DIR / slug / REVIEW_FILENAME).exists()


# ─── IDENTITY CHECK MODE ──────────────────────────────────────────────────────

def run_identity_check(client, books, all_vocab=None):
    print(f"\nRunning pre-flight identity check on {len(books)} books...")
    print("(cheap, no vocab generated, nothing written to any book folder)\n")

    results = []
    for i, book_dir in enumerate(books, 1):
        slug = book_dir.name
        metadata = load_theme_vocab(slug, (all_vocab or {}).get(slug, {}))
        title_guess = metadata.get("title") or get_book_title_from_slug(slug)
        author_guess = metadata.get("author") or "Unknown"
        print(f"[{i:3d}/{len(books)}] {slug:45s} checking...", end="", flush=True)
        result, error = call_claude_identity(client, slug, title_guess, author_guess)
        if error or not result:
            print(f" ❌ {error}")
            results.append({"slug": slug, "error": error})
            continue
        flag = "✅" if result.get("confidence") == "high" and not result.get("concern") else "⚠️"
        print(f" {flag} {result.get('title', '?')} ({result.get('confidence', '?')})")
        result["slug"] = slug
        results.append(result)
        time.sleep(0.2)

    # Write skimmable report
    lines = [
        "# AAC Vocab — Pre-Flight Identity Check",
        f"**Generated:** {datetime.now().strftime('%d %b %Y %H:%M')}",
        f"**Books checked:** {len(results)}",
        "",
        "Read this BEFORE running full vocab generation. Anything not marked",
        "✅ high confidence with no concern should be checked by hand — a",
        "wrong book identified here means every word generated from it later",
        "is wrong too.",
        "",
        "| Slug | Title found | Author | Year | Confidence | Concern |",
        "|------|-------------|--------|------|------------|---------|",
    ]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['slug']} | ❌ FAILED | — | — | — | {r['error']} |")
            continue
        conf = r.get("confidence", "?")
        badge = "✅" if conf == "high" and not r.get("concern") else "⚠️"
        lines.append(
            f"| {r['slug']} | {badge} {r.get('title','?')} | {r.get('author','?')} | "
            f"{r.get('pub_year','?')} | {conf} | {r.get('concern','') or '—'} |"
        )
    lines.append("")
    lines.append("## One-line summaries (for a quick sanity read)")
    lines.append("")
    for r in results:
        if "error" in r:
            continue
        lines.append(f"- **{r.get('title','?')}** (`{r['slug']}`): {r.get('one_line_summary','')}")

    IDENTITY_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📄 Identity check report: {IDENTITY_REPORT_FILE}")
    n_concerns = sum(1 for r in results if r.get("concern") or r.get("confidence") != "high")
    print(f"   {n_concerns} book(s) flagged for a manual look before generating vocab.\n")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book",            help="Single book slug")
    ap.add_argument("--focus-file",      metavar="PATH", help="Process only focus_books slugs from a JSON manifest")
    ap.add_argument("--missing-only",    action="store_true", help="Only books with no PROMOTED vocab yet")
    ap.add_argument("--dry-run",         action="store_true", help="Show plan, no API calls")
    ap.add_argument("--overwrite",       action="store_true", help="Re-run even if a review/promoted vocab exists")
    ap.add_argument("--identity-check",  action="store_true", help="Cheap pre-flight title/author/year check only")
    ap.add_argument("--promote",         metavar="SLUG",       help="Promote one book's reviewed vocab to real book_vocab.json")
    ap.add_argument("--promote-all",     action="store_true",  help="Promote every book with a pending needs_review_vocab.json")
    args = ap.parse_args()

    print("\n" + "=" * 65)
    print("  Small Wins Studio — AAC Vocab Builder (patched, review-gated)")
    print(f"  {datetime.now().strftime('%d %b %Y %H:%M')}")
    print("=" * 65 + "\n")

    # ── PROMOTE MODES — don't need the API at all ──
    if args.promote:
        return 0 if promote_book(args.promote) else 1
    if args.promote_all:
        pending = [b.name for b in discover_books() if has_pending_review(b.name)]
        print(f"Found {len(pending)} book(s) with pending review vocab.\n")
        outcomes = [promote_book(slug) for slug in pending]
        return 0 if all(outcomes) else 1

    # Everything below this point needs the API
    all_vocab = load_boardready_vocab()
    print(f"Loaded existing PROMOTED vocab: {len(all_vocab)} books\n")

    all_books = discover_books()
    if args.focus_file:
        try:
            all_books, missing_focus_slugs = focus_books(all_books, args.focus_file)
        except (FileNotFoundError, ValueError) as exc:
            ap.error(str(exc))
        print(f"Filtered to focus manifest books: {len(all_books)}")
        if missing_focus_slugs:
            print("Missing focus slugs (no discovered theme directory):")
            for slug in missing_focus_slugs:
                print(f"  - {slug}")
        print()
    if args.book:
        all_books = [b for b in all_books if b.name == args.book]
        if not all_books:
            print(f"❌ Book not found: {args.book}")
            sys.exit(1)

    if args.missing_only and not args.overwrite:
        all_books = [b for b in all_books if not has_real_vocab(b.name, all_vocab)]
        print(f"Filtered to books with no PROMOTED vocab: {len(all_books)}\n")

    if args.identity_check:
        if args.dry_run:
            print("DRY RUN — would identity-check these books:")
            for b in all_books:
                print(f"  {b.name}")
            return
        client = get_client()
        run_identity_check(client, all_books, all_vocab)
        return

    print("Scanning symbol library...", end="", flush=True)
    symbol_sample = get_available_symbols()
    print(f" {len(symbol_sample)} symbols found\n")

    print(f"Books to process: {len(all_books)}")
    if args.dry_run:
        print("DRY RUN — no API calls will be made\n")
        for b in all_books:
            existing = load_theme_vocab(b.name, all_vocab.get(b.name, {}))
            icons = get_existing_icons(b.name)
            has_v = has_real_vocab(b.name, all_vocab)
            pending = has_pending_review(b.name)
            status = "✅ promoted" if has_v else ("📝 pending review" if pending else "⚪ needs vocab")
            print(f"  {b.name:45s} {status} | {len(icons)} icons")
        print(f"\nEstimated API cost: ~${len(all_books) * 0.03:.2f}")
        return

    est_cost = len(all_books) * 0.03
    print(f"Estimated API cost: ~${est_cost:.2f}")
    if len(all_books) > 10 and not args.book and not args.focus_file:
        confirm = input(f"Process all {len(all_books)} books? (y/n): ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return
    print()

    client = get_client()

    results_ok    = []
    results_fail  = []
    all_ambiguous = []

    for i, book_dir in enumerate(all_books, 1):
        slug = book_dir.name
        existing_entry  = load_theme_vocab(slug, all_vocab.get(slug, {}))
        existing_icons  = get_existing_icons(slug)
        existing_vocab  = existing_entry.get("activity_images", [])
        existing_extras = existing_entry.get("aac_extras", [])

        title  = existing_entry.get("title",  get_book_title_from_slug(slug))
        author = existing_entry.get("author", "Unknown")

        if has_real_vocab(slug, all_vocab) and not args.overwrite:
            print(f"[{i:3d}/{len(all_books)}] {slug:45s} ⏭  skipped (already promoted)")
            continue
        if has_pending_review(slug) and not args.overwrite:
            print(f"[{i:3d}/{len(all_books)}] {slug:45s} ⏭  skipped (review file already pending — use --overwrite to regenerate)")
            continue

        print(f"[{i:3d}/{len(all_books)}] {slug:45s} 🤖 calling Claude...", end="", flush=True)

        result, error = call_claude_full(
            client, slug, title, author,
            existing_icons, existing_vocab, existing_extras,
            symbol_sample
        )

        if error or not result:
            print(f" ❌ {error}")
            results_fail.append((slug, error))
            time.sleep(1)
            continue

        structural_errors = validate_vocab_structure(result)
        if structural_errors:
            reason = "; ".join(structural_errors)
            print(f" REJECTED — {reason}")
            results_fail.append((slug, reason))
            time.sleep(1)
            continue

        saved_entry = save_needs_review(slug, result, existing_entry)
        warnings = saved_entry.get("guardrail_warnings", [])

        for amb in result.get("ambiguous", []):
            all_ambiguous.append({
                "slug": slug, "title": title,
                "word": amb.get("word", ""), "issue": amb.get("issue", ""),
                "preferred": amb.get("preferred", ""), "reason": amb.get("reason", ""),
            })

        n_fringe    = len(result.get("fringe_11", []))
        n_ambiguous = len(result.get("ambiguous", []))
        hero        = result.get("hero", {})
        hero_flag   = "🎭 source hero" if hero.get("needs_sourcing") else "✅ hero from PCS"
        flags = [hero_flag, "📝 NEEDS REVIEW"]
        if not result.get("grounded", False): flags.append("🚨 UNGROUNDED")
        if n_ambiguous: flags.append(f"⚠️ {n_ambiguous} ambiguous")
        if warnings: flags.append(f"🛑 {len(warnings)} guardrail warning(s)")
        flag_str = " | " + ", ".join(flags)

        print(f" ✅ hero={hero.get('name','?')} + {n_fringe} words{flag_str}")
        results_ok.append((slug, result, saved_entry))
        time.sleep(0.3)

    # ─── WRITE REPORT ─────────────────────────────────────────────────────────

    report = [
        "# AAC Vocab Builder Report — NEEDS_REVIEW batch",
        f"**Generated:** {datetime.now().strftime('%d %b %Y %H:%M')}",
        f"**Books processed:** {len(results_ok)}",
        f"**Failed:** {len(results_fail)}",
        f"**Total ambiguous words flagged:** {len(all_ambiguous)}",
        "",
        "⚠️ **Nothing here has been written to real book_vocab.json.** Every book",
        "below is sitting in its own `needs_review_vocab.json`. Read this report,",
        "spot-check the summaries against books you know, then run:",
        "`python AAC_VOCAB_BUILDER.py --promote <slug>` (or `--promote-all`)",
        "for the ones you're happy with.",
        "",
    ]

    # GUARDRAIL WARNINGS — surfaced first, these are structural gaps
    with_warnings = [(slug, r, e) for slug, r, e in results_ok if e.get("guardrail_warnings")]
    if with_warnings:
        report += [
            "## 🛑 Guardrail Warnings — Missing Required Fields",
            "",
            "These books are missing a summary, author, year, or a per-word",
            "justification. Treat these as lower-confidence than the rest.",
            "",
        ]
        for slug, r, e in with_warnings:
            report.append(f"- **{r.get('title', slug)}** (`{slug}`): {', '.join(e['guardrail_warnings'])}")
        report.append("")

    ungrounded = [
        (slug, r.get("title", slug), r.get("grounding_note", ""), r.get("_searches_used", 0))
        for slug, r, e in results_ok if not r.get("grounded", False)
    ]
    if ungrounded:
        report += [
            "## 🚨 UNGROUNDED — Verify Before Use",
            "",
            "| Book | Searches performed | Reason |",
            "|------|---------------------|--------|",
        ]
        for slug, title, note, n_searches in ungrounded:
            report.append(f"| {title} | {n_searches} | {note or 'no reason given'} |")
        report.append("")

    if all_ambiguous:
        report += [
            "## ⚠️ Ambiguous Words — Review These",
            "",
            "| Book | Word | Issue | Preferred Icon | Reason |",
            "|------|------|-------|----------------|--------|",
        ]
        for a in sorted(all_ambiguous, key=lambda x: x["word"]):
            report.append(f"| {a['title']} | **{a['word']}** | {a['issue']} | `{a['preferred']}` | {a['reason']} |")
        report.append("")

    heroes_to_source = [
        (r.get("title", slug), slug, r.get("hero", {}))
        for slug, r, e in results_ok if r.get("hero", {}).get("needs_sourcing")
    ]
    if heroes_to_source:
        report += [
            "## 🎭 Hero Images to Source — PRIORITY",
            "",
            "| Book | Hero Character | Search Term | Notes |",
            "|------|---------------|-------------|-------|",
        ]
        for title, slug, hero in sorted(heroes_to_source, key=lambda x: x[2].get("name", "")):
            report.append(f"| {title} | **{hero.get('name','')}** | `{hero.get('search_term','')}` | {hero.get('source_note','')} |")
        report.append("")

    # PER-BOOK — summary/author/year FIRST, so the identity check is the
    # first thing you read for every book, then fringe + justifications.
    report += ["## 📚 Full Vocab by Book (all NEEDS_REVIEW)", ""]
    for slug, r, e in sorted(results_ok, key=lambda x: x[0]):
        title  = r.get("title", slug)
        author = r.get("author", "?")
        year   = r.get("pub_year", "?")
        hero   = r.get("hero", {})
        fringe = r.get("fringe_11", [])
        justs  = r.get("fringe_justifications", {})
        summary = r.get("book_summary", "(no summary returned)")
        hero_flag = "⚠️ needs sourcing" if hero.get("needs_sourcing") else "✅ from PCS"

        report.append(f"### {title}")
        report.append(f"**Slug:** `{slug}` | **Author:** {author} | **Year:** {year}")
        report.append(f"**Summary (check this first):** {summary}")
        report.append(f"**Hero (slot 1):** {hero.get('name','?')} — search `{hero.get('search_term','')}` [{hero_flag}]")
        report.append("**Fringe words + why (slots 2–12):**")
        for w in fringe:
            just = justs.get(w, "⚠️ no justification given")
            report.append(f"  - **{w}** — {just}")
        amb = r.get("ambiguous", [])
        if amb:
            for a in amb:
                report.append(f"**⚠️ Ambiguous:** `{a['word']}` → use `{a['preferred']}` ({a['reason']})")
        if r.get("notes"):
            report.append(f"**Notes:** {r['notes']}")
        report.append("")

    if results_fail:
        report += [
            "## ❌ Failed or Rejected — Needs Re-run",
            "",
        ]
        for slug, err in results_fail:
            report.append(f"- **{slug}**: {err}")
        report.append("")

    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")

    print("\n" + "=" * 65)
    print("  COMPLETE — nothing written to real book_vocab.json")
    print("=" * 65)
    n_ungrounded = sum(1 for _, r, e in results_ok if not r.get("grounded", False))
    n_warnings   = sum(len(e.get("guardrail_warnings", [])) for _, r, e in results_ok)
    print(f"  ✅ Vocab generated (needs review): {len(results_ok)}")
    print(f"  ❌ Failed:                         {len(results_fail)}")
    print(f"  🚨 UNGROUNDED (verify!):           {n_ungrounded}")
    print(f"  🛑 Guardrail warnings:             {n_warnings}")
    print(f"  ⚠️  Ambiguous words found:          {len(all_ambiguous)}")
    print(f"\n  📄 Report: {REPORT_FILE}")
    print(f"  📄 Per-book review files: assets/themes/<slug>/{REVIEW_FILENAME}")
    print(f"\n  Next step: read the report, then run --promote <slug> or --promote-all")
    print()


if __name__ == "__main__":
    raise SystemExit(main())
