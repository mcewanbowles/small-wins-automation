"""Update all book_vocab.json files with vocab_words, activity_images, and required_icons.

For each theme:
1. Adds `vocab_words` — the approved word list derived from fringe_12/fringe_11
   (so Word Wall and other generators don't fall back to scanning artifact PNGs)
2. Updates `activity_images` — the actual clean PNG stems in activity_images/
3. Adds `required_icons` — documents the max icons each activity needs
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
THEMES = ROOT / "assets" / "themes"

# Standard activity icon requirements (from the audit)
REQUIRED_ICONS = {
    "aac_board": {"min": 2, "max": 12, "note": "2 theme + 24 core + 10 global fringe"},
    "matching": {"min": 4, "max": 12, "note": "Min 4 approved stems, no hard cap"},
    "book_participation": {"min": 8, "max": 8, "note": "8 vocab + hero"},
    "sentence_strips": {"min": 8, "max": 12, "note": "8 theme items + 5 core words"},
    "sequencing": {"min": 4, "max": 10, "note": "Story sequence cards, capped at 10"},
    "yes_no": {"min": 4, "max": 12, "note": "Yes/No question cards, 4 per page"},
    "inferencing": {"min": 3, "max": 4, "note": "Exactly 4 reasoning cards"},
    "vocabulary_snap": {"min": 6, "max": 12, "note": "Vocab cards, cap 12 unique words"},
    "syllable_cards": {"min": 4, "max": 20, "note": "Syllable cards, expanded to 20"},
    "cvc_decode": {"min": 9, "max": 15, "note": "3-5 groups x 3 CVC words (phonics, not theme icons)"},
    "story_grammar": {"min": 1, "max": 1, "note": "Hero icon + 6 fixed story-element labels"},
    "word_search": {"min": 4, "max": 8, "note": "4-8 words, length <= 8 letters"},
    "bingo": {"min": 8, "max": 8, "note": "Exactly 8 calling cards"},
    "sorting": {"min": 6, "max": 12, "note": "6-12 sort items across 2 sets"},
    "print_detective": {"min": 5, "max": 8, "note": "5-8 first-sound picture pairs"},
}


def derive_vocab_words(data: dict) -> list[str]:
    """Derive the approved vocab word list from fringe_12 or fringe_11."""
    if "fringe_12" in data and isinstance(data["fringe_12"], list):
        return list(data["fringe_12"])
    if "fringe_11" in data and isinstance(data["fringe_11"], list):
        return list(data["fringe_11"])
    # Fallback: activity_images field
    ai = data.get("activity_images", [])
    if isinstance(ai, list) and ai:
        return list(ai)
    return []


def scan_activity_images(theme_dir: Path) -> list[str]:
    """Scan the activity_images folder for clean PNG stems."""
    ai_dir = theme_dir / "activity_images"
    if not ai_dir.exists():
        return []
    stems = []
    for p in sorted(ai_dir.glob("*.png")):
        name = p.stem
        # Skip artifact files with very long names (from aac_fringe_vocab dumps)
        if len(name) > 50 or name.startswith("word_"):
            continue
        stems.append(name)
    return stems


def update_theme(theme_dir: Path) -> bool:
    """Update a single theme's book_vocab.json. Returns True if changed."""
    vocab_path = theme_dir / "book_vocab.json"
    if not vocab_path.exists():
        return False

    try:
        data = json.loads(vocab_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"SKIP {theme_dir.name}: JSON parse error: {e}")
        return False

    changed = False

    # 1. Add vocab_words if missing or empty
    if not data.get("vocab_words"):
        words = derive_vocab_words(data)
        if words:
            data["vocab_words"] = words
            changed = True

    # 2. Update activity_images to match actual clean PNGs
    actual_icons = scan_activity_images(theme_dir)
    if actual_icons:
        current_ai = data.get("activity_images", [])
        if isinstance(current_ai, list):
            # Only update if the list differs
            if set(current_ai) != set(actual_icons):
                data["activity_images"] = actual_icons
                changed = True

    # 3. Add required_icons summary if missing
    if "required_icons" not in data:
        data["required_icons"] = REQUIRED_ICONS
        changed = True

    # 4. Add max_theme_icons if missing
    if "max_theme_icons" not in data:
        vocab = data.get("vocab_words", [])
        # Max unique theme icons needed = vocab_words count + 1 for hero
        max_icons = len(vocab) + 1 if vocab else 9
        data["max_theme_icons"] = max_icons
        changed = True

    if changed:
        vocab_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK   {theme_dir.name}")
    else:
        print(f"SKIP {theme_dir.name} (already up to date)")

    return changed


def main():
    updated = 0
    skipped = 0
    errors = 0

    for theme_dir in sorted(THEMES.iterdir()):
        if not theme_dir.is_dir():
            continue
        if theme_dir.name.startswith(".") or theme_dir.name in ("_archive", "global"):
            continue
        vocab_path = theme_dir / "book_vocab.json"
        try:
            if not vocab_path.exists():
                continue
        except Exception as e:
            print(f"ERR  {theme_dir.name}: cannot stat - {e}")
            errors += 1
            continue
        try:
            if update_theme(theme_dir):
                updated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"ERR  {theme_dir.name}: {e}")
            errors += 1

    print(f"\nDone: {updated} updated, {skipped} skipped, {errors} errors")


if __name__ == "__main__":
    main()
