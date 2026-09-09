"""Print Detective — print concepts + alphabet knowledge for LLRP.

Fills the suite's Scarborough Reading Rope gap in "Alphabetic Principle /
Print Concepts":

  Level 1  Letter or Not a Letter — sort letters vs symbols/numbers
  Level 2  Letter or Word        — sort single letters vs whole words
  Level 3  First Sound Match     — match letters to vocab icons by initial sound
  Level 4  Reading Detective     — directionality, concept of word, book parts

All content is theme-linked: sort words and L3 icons come from the reviewed
LLRP vocabulary (book_vocab.json) and activity_images icons. No book text is
reproduced; L4 uses an original practice sentence.

Outputs (theme OUTPUT dir):
  LLRP-PD-LAUNCH_PrintDetective_COLOR.pdf / _BW.pdf
  LLRP-PD-LAUNCH_PrintDetective_BuildResult.json
  Teacher Overview PDF + overview data JSON (for the suite packager)
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from Studioforge._TRUTH.generate_book_participation_pieces import (
    _activity_page,
    _center,
    _fit,
    _font,
    _save_pdf,
)
from utils.UNIVERSAL_STANDARDS import SWS_GOLD, SWS_NAVY, SWS_TEAL, SWS_TEAL_LT
from utils.sws_design import generate_teacher_cover_page
from utils.sws_design import DPI, hex_to_rgb

ROOT = Path(__file__).resolve().parents[2]
THEME = ROOT / "assets" / "themes" / "llama_llama_back_to_school"
ICONS = THEME / "activity_images"
OUTPUT = THEME / "OUTPUT"
OVERVIEW_DIR = ROOT / "Studioforge" / "_REVIEW" / "Teacher Overview Template 04-09" / "print_detective"
OVERVIEW_DATA = ROOT / "production" / "generators" / "teacher_overview_examples" / "print_detective.json"
PACK_CODE = "LLB01-PD-LAUNCH"

PAGE_W, PAGE_H = int(612 * DPI / 72), int(792 * DPI / 72)
CX0, CX1, CY0, CY1 = 260, PAGE_W - 260, 560, 2920

NAVY = hex_to_rgb(SWS_NAVY)
TEAL = hex_to_rgb(SWS_TEAL)
GOLD = hex_to_rgb(SWS_GOLD)
TEAL_LT = hex_to_rgb(SWS_TEAL_LT)
GRAY = (90, 105, 115)

LEVEL_COLORS = {1: hex_to_rgb("#7C3AED"), 2: hex_to_rgb("#0284C7"), 3: hex_to_rgb("#059669"), 4: hex_to_rgb("#E11D48")}


def _load_book_vocab(theme_dir: Path) -> list[str]:
    """Load the approved vocabulary word list from the theme's book_vocab.json.

    Returns the `vocab_words` list (e.g. 12-20 words).  Raises RuntimeError if
    the file is missing or empty so the generator can never silently fall back
    to hard-coded words from another book.
    """
    vocab_path = theme_dir / "book_vocab.json"
    if not vocab_path.is_file():
        raise RuntimeError(
            f"Print Detective guard: book_vocab.json not found at {vocab_path}. "
            "Cannot generate without the current book's approved vocabulary."
        )
    data = json.loads(vocab_path.read_text(encoding="utf-8"))
    words = data.get("vocab_words") or data.get("fringe_12") or []
    if not words:
        raise RuntimeError(
            f"Print Detective guard: vocab_words list is empty in {vocab_path}."
        )
    return [str(w) for w in words]


def _build_l3_pairs(vocab_words: list[str], icons_dir: Path, max_pairs: int = 7):
    """Build L3 first-sound pairs from the *current book's* approved vocab.

    Each pair is (uppercase_letter, icon_stem, display_word).
    Only words whose icon file exists are included, so the generator never
    references an icon from another book.
    """
    pairs = []
    seen_letters = set()
    for word in vocab_words:
        if len(pairs) >= max_pairs:
            break
        stem = word
        letter = word[0].upper()
        if letter in seen_letters:
            continue
        # Verify icon exists
        icon_path = icons_dir / f"{stem}.png"
        if not icon_path.is_file():
            continue
        # Human-readable label: replace underscores with spaces
        display = stem.replace("_", " ")
        pairs.append((letter, stem, display))
        seen_letters.add(letter)
    if len(pairs) < 4:
        raise RuntimeError(
            f"Print Detective guard: only {len(pairs)} L3 pairs could be built "
            f"from {icons_dir} (need at least 4). Check that activity_images "
            f"contains icons for the approved vocabulary."
        )
    return pairs


def _build_l2_words(vocab_words: list[str], max_words: int = 6) -> list[str]:
    """Pick short words from the approved vocab for the Letter-or-Word sort."""
    candidates = [w.replace("_", " ") for w in vocab_words if len(w) <= 8 and w[0].isalpha()]
    return candidates[:max_words]


def _build_l2_letters(l2_words: list[str], max_letters: int = 6) -> list[str]:
    """Pick first letters from the L2 words for the Letter-or-Word sort."""
    seen = []
    for w in l2_words:
        ch = w[0].lower()
        if ch not in seen:
            seen.append(ch)
        if len(seen) >= max_letters:
            break
    return seen


def _build_l4_sentence(vocab_words: list[str]) -> list[str]:
    """Build a short practice sentence from approved vocab words."""
    # Use up to 4 short words from the vocab
    short = [w.replace("_", " ") for w in vocab_words if len(w) <= 8 and w[0].isalpha()]
    return short[:4] if len(short) >= 4 else short[: len(short)]


# Letters vs non-letters (L1) — these are generic, not book-specific
L1_LETTERS = ["A", "L", "M", "P", "S", "T"]
L1_NON = ["3", "7", "?", "!", "&", "@"]

# L2/L3/L4 are loaded dynamically in generate_print_detective_pack()
L2_LETTERS: list[str] = []
L2_WORDS: list[str] = []
L3_PAIRS: list[tuple[str, str, str]] = []
L4_SENTENCE: list[str] = []


def _load_icon(stem: str, size: int) -> Image.Image | None:
    path = ICONS / f"{stem}.png"
    if not path.is_file():
        return None
    img = Image.open(path).convert("RGBA")
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    return img


def _card(draw: ImageDraw.ImageDraw, box, text: str, pt: int = 26, dashed: bool = False,
          fill=(255, 255, 255), outline=NAVY, text_fill=NAVY, icon: Image.Image | None = None):
    x1, y1, x2, y2 = box
    if dashed:
        draw.rounded_rectangle(box, radius=28, fill=fill, outline=outline, width=4)
        # dashed-look inner guide line
        inset = 26
        draw.rounded_rectangle((x1 + inset, y1 + inset, x2 - inset, y2 - inset),
                               radius=18, outline=outline, width=2)
    else:
        draw.rounded_rectangle(box, radius=28, fill=fill, outline=outline, width=5)
    if icon is not None:
        ix = x1 + (x2 - x1 - icon.width) // 2
        iy = y1 + 40
        draw._image.paste(icon, (ix, iy), icon)
        f = _fit(text, pt - 6, x2 - x1 - 60, bold=True)
        _center(draw, (x1, y2 - 170, x2, y2 - 50), text, f, text_fill)
    else:
        f = _fit(text, pt, x2 - x1 - 60, bold=True)
        _center(draw, box, text, f, text_fill)


def _level_badge(draw: ImageDraw.ImageDraw, level: int, label: str):
    badge_w = 1500
    badge_x1 = CX0 + ((CX1 - CX0) - badge_w) // 2
    box = (badge_x1, 420, badge_x1 + badge_w, 520)
    draw.rounded_rectangle(box, radius=50, fill=LEVEL_COLORS[level])
    _center(draw, box, f"LEVEL {level}  ·  {label}", _fit(f"LEVEL {level}  ·  {label}", 14, 1400, bold=True), (255, 255, 255))


def _sort_mat(level: int, title: str, subtitle: str, headers: list[str], page_num: int, total: int, direction: str) -> Image.Image:
    page = _activity_page(title, subtitle, PACK_CODE, page_num, total)
    draw = ImageDraw.Draw(page)
    _level_badge(draw, level, direction)
    col_w = (CX1 - CX0 - 120) // 2
    for i, head in enumerate(headers):
        x1 = CX0 + i * (col_w + 120)
        x2 = x1 + col_w
        draw.rounded_rectangle((x1, 640, x2, CY1 - 40), radius=40, outline=NAVY, width=6)
        pill = (x1 + 60, 700, x2 - 60, 840)
        draw.rounded_rectangle(pill, radius=60, fill=TEAL)
        _center(draw, pill, head, _fit(head, 20, pill[2] - pill[0] - 80, bold=True), (255, 255, 255))
        for r in range(3):
            slot = (x1 + 140, 960 + r * 640, x2 - 140, 960 + r * 640 + 560)
            draw.rounded_rectangle(slot, radius=28, outline=GRAY, width=4)
            _center(draw, slot, "place card", _font(12), (200, 205, 210))
    return page


def _card_sheet(level: int, title: str, subtitle: str, cards: list[str], page_num: int, total: int,
                note: str, icons: list[tuple[str, str]] | None = None) -> Image.Image:
    page = _activity_page(title, subtitle, PACK_CODE, page_num, total)
    draw = ImageDraw.Draw(page)
    _level_badge(draw, level, note)
    cols = 4
    gap = 80
    cw = (CX1 - CX0 - (cols - 1) * gap) // cols
    ch = 560 if icons is None else 640
    top = 680
    for i, text in enumerate(cards):
        r, c = divmod(i, cols)
        x1 = CX0 + c * (cw + gap)
        y1 = top + r * (ch + gap)
        icon = None
        if icons:
            stem = icons[i][0]
            icon = _load_icon(stem, ch - 300)
        _card(draw, (x1, y1, x1 + cw, y1 + ch), text, 26 if len(text) <= 2 else 18,
              dashed=True, fill=TEAL_LT if i % 2 == 0 else (255, 255, 255), icon=icon)
    return page


def _l3_mat(page_num: int, total: int) -> Image.Image:
    page = _activity_page("Print Detective", "First Sound Match", PACK_CODE, page_num, total)
    draw = ImageDraw.Draw(page)
    _level_badge(draw, 3, "MATCH THE LETTER TO THE PICTURE'S FIRST SOUND")
    cols = 4
    gap = 80
    cw = (CX1 - CX0 - (cols - 1) * gap) // cols
    top = 700
    for i, (letter, stem, word) in enumerate(L3_PAIRS):
        r, c = divmod(i, cols)
        x1 = CX0 + c * (cw + gap)
        y1 = top + r * (ch := 1050)
        # letter cell
        draw.rounded_rectangle((x1, y1, x1 + cw, y1 + 330), radius=30, fill=NAVY)
        _center(draw, (x1, y1, x1 + cw, y1 + 330), letter, _font(60, True), (255, 255, 255))
        # placement slot
        slot = (x1, y1 + 390, x1 + cw, y1 + ch)
        draw.rounded_rectangle(slot, radius=30, outline=GRAY, width=4)
        _center(draw, slot, "place picture card", _font(11), (200, 205, 210))
    note = _font(12)
    _center(draw, (CX0, CY1 - 120, CX1, CY1 - 30),
            "Say the picture name. Stretch the first sound. Match it to the letter.", note, GRAY)
    return page


def _l4_page(page_num: int, total: int) -> Image.Image:
    page = _activity_page("Print Detective", "Reading Detective", PACK_CODE, page_num, total)
    draw = ImageDraw.Draw(page)
    _level_badge(draw, 4, "DIRECTIONALITY · CONCEPT OF WORD · PARTS OF PRINT")
    f = _font(15)

    # Task 1: directionality strip
    y = 700
    draw.rounded_rectangle((CX0, y, CX1, y + 640), radius=40, outline=NAVY, width=6)
    _center(draw, (CX0, y + 40, CX1, y + 160), "Follow the arrow. Point to each word as you read.", _font(14), NAVY)
    strip_y = y + 240
    # arrow
    ax1, ax2 = CX0 + 120, CX1 - 120
    draw.line((ax1, strip_y, ax2 - 160, strip_y), fill=TEAL, width=22)
    draw.polygon([(ax2 - 160, strip_y - 70), (ax2 - 160, strip_y + 70), (ax2, strip_y)], fill=TEAL)
    # word dots under sentence
    wf = _font(30, True)
    spacing = (ax2 - ax1 - 300) // (len(L4_SENTENCE) - 1)
    for i, word in enumerate(L4_SENTENCE):
        wx = ax1 + i * spacing
        draw.text((wx, strip_y + 110), word, font=wf, fill=NAVY)
        draw.ellipse((wx + 30, strip_y + 60, wx + 110, strip_y + 140), outline=GOLD, width=6)
        _center(draw, (wx + 30, strip_y + 55, wx + 110, strip_y + 130), str(i + 1), _font(12, True), NAVY)

    # Task 2: find-and-mark checklist
    y2 = 1500
    draw.rounded_rectangle((CX0, y2, CX1, y2 + 700), radius=40, outline=NAVY, width=6)
    _center(draw, (CX0, y2 + 40, CX1, y2 + 160), "Detective checklist — use a crayon or dry-erase marker", _font(14), NAVY)
    tasks = [
        "Circle the FIRST word in the sentence above.",
        "Underline the LAST word.",
        "Draw a box around one SPACE between words.",
        "Put a star on a letter that is in your name.",
        "Count the words: the sentence has ___ words. (Answer: 4)",
    ]
    ty = y2 + 210
    for task in tasks:
        draw.rounded_rectangle((CX0 + 90, ty, CX0 + 160, ty + 70), radius=12, outline=TEAL, width=5)
        draw.text((CX0 + 210, ty + 8), task, font=f, fill=NAVY)
        ty += 96

    # Task 3: book parts mini-panel
    y3 = 2300
    draw.rounded_rectangle((CX0, y3, CX1, CY1 - 40), radius=40, fill=TEAL_LT, outline=TEAL, width=6)
    _center(draw, (CX0, y3 + 40, CX1, y3 + 160), "Book hunt — with any book, point to:", _font(14), NAVY)
    parts = ["the front cover", "the title", "a letter", "a word", "where to start reading"]
    px = CX0 + 90
    py = y3 + 220
    for i, part in enumerate(parts):
        col, row = divmod(i, 3)
        bx = CX0 + 90 + col * ((CX1 - CX0 - 260) // 3 + 20)
        by = py + row * 180
        pill = (bx, by, bx + (CX1 - CX0 - 260) // 3, by + 130)
        draw.rounded_rectangle(pill, radius=60, fill=(255, 255, 255), outline=TEAL, width=4)
        _center(draw, pill, part, _fit(part, 13, pill[2] - pill[0] - 60, bold=True), NAVY)
    return page


def _answer_key(page_num: int, total: int) -> Image.Image:
    page = _activity_page("Print Detective", "Answer Key", PACK_CODE, page_num, total)
    draw = ImageDraw.Draw(page)
    rows = [
        ("Level 1", "Letters: " + ", ".join(L1_LETTERS) + "   ·   Not letters: " + ", ".join(L1_NON)),
        ("Level 2", "Letters: " + ", ".join(L2_LETTERS) + "   ·   Words: " + ", ".join(L2_WORDS)),
        ("Level 3", "  ·  ".join(f"{l}\u2192{w}" for l, _, w in L3_PAIRS)),
        ("Level 4", f"Sentence has {len(L4_SENTENCE)} words: {' / '.join(L4_SENTENCE)}. First = {L4_SENTENCE[0]}, last = {L4_SENTENCE[-1]}."),
    ]
    y = 700
    for level, text in rows:
        box = (CX0, y, CX1, y + 480)
        draw.rounded_rectangle(box, radius=40, fill=TEAL_LT, outline=TEAL, width=4)
        _center(draw, (box[0] + 60, y + 60, box[0] + 620, y + 180), level, _font(16, True), NAVY)
        f = _fit(text, 13, box[2] - box[0] - 200, minimum=9, bold=False)
        _center(draw, (box[0] + 80, y + 200, box[2] - 80, y + 440), text, f, NAVY)
        y += 560
    return page


def _intro(page_num: int, total: int) -> Image.Image:
    page = _activity_page("Print Detective", "Letters · Words · First Sounds", PACK_CODE, page_num, total)
    draw = ImageDraw.Draw(page)
    box = (CX0 + 200, 800, CX1 - 200, 1900)
    draw.rounded_rectangle(box, radius=50, fill=TEAL_LT, outline=TEAL, width=5)
    head = _fit("Become a Print Detective!", 30, box[2] - box[0] - 160, bold=True)
    _center(draw, (box[0], box[1] + 90, box[2], box[1] + 260), "Become a Print Detective!", head, NAVY)
    items = [
        "Level 1  ·  Sort letters from symbols and numbers",
        "Level 2  ·  Tell letters from whole words",
        "Level 3  ·  Match letters to a picture's first sound",
        "Level 4  ·  Track print left to right, find word boundaries",
        "",
        "All pictures and words come from your book's",
        "approved vocabulary - the same icons students",
        "already know from the rest of this suite.",
    ]
    y = box[1] + 340
    for item in items:
        _center(draw, (box[0], y, box[2], y + 110), item, _font(14), NAVY)
        y += 125
    _center(draw, (CX0, 2350, CX1, 2500),
            "Scarborough's Reading Rope: Alphabetic Principle + Print Concepts",
            _font(13, True), NAVY)
    return page


def generate_print_detective_pack() -> dict:
    # ── Vocab guard: load from the current book's vocab file ──
    global L2_LETTERS, L2_WORDS, L3_PAIRS, L4_SENTENCE
    vocab_words = _load_book_vocab(THEME)
    L2_WORDS = _build_l2_words(vocab_words)
    L2_LETTERS = _build_l2_letters(L2_WORDS)
    L3_PAIRS = _build_l3_pairs(vocab_words, ICONS)
    L4_SENTENCE = _build_l4_sentence(vocab_words)
    # Verify every L3 word is in the vocab file
    vocab_lower = {w.lower() for w in vocab_words}
    for _letter, _stem, word in L3_PAIRS:
        if _stem.lower() not in vocab_lower:
            raise RuntimeError(
                f"Print Detective guard: word '{_stem}' is not in the current "
                f"book vocabulary file ({THEME / 'book_vocab.json'}). Aborting."
            )
    total = 8
    pages = [
        _sort_mat(1, "Print Detective", "Letter or Not a Letter", ["LETTER", "NOT A LETTER"], 1, total, "SORT THE CARDS"),
        _card_sheet(1, "Print Detective", "Sort Cards", L1_LETTERS + L1_NON, 2, total, "CUT · SORT · SAY 'LETTER' OR 'NOT A LETTER'"),
        _sort_mat(2, "Print Detective", "Letter or Word", ["LETTER", "WORD"], 3, total, "SORT THE CARDS"),
        _card_sheet(2, "Print Detective", "Sort Cards", L2_LETTERS + L2_WORDS, 4, total, "CUT · SORT · SAY 'LETTER' OR 'WORD'"),
        _l3_mat(5, total),
        _card_sheet(3, "Print Detective", "Picture Cards", [w for _, _, w in L3_PAIRS], 6, total,
                   "CUT · SAY THE NAME · MATCH THE FIRST SOUND",
                   icons=[(s, w) for _, s, w in L3_PAIRS]),
        _l4_page(7, total),
        _answer_key(8, total),
    ]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    color_pdf = OUTPUT / f"{PACK_CODE}_PrintDetective_COLOR.pdf"
    bw_pdf = OUTPUT / f"{PACK_CODE}_PrintDetective_BW.pdf"
    _save_pdf(color_pdf, pages)
    _save_pdf(bw_pdf, [p.convert("L").convert("RGB") for p in pages])

    # Thumbnails for marketing previews
    try:
        thumbs_dir = OUTPUT / "thumbnails"
        thumbs_dir.mkdir(parents=True, exist_ok=True)
        thumb_paths = []
        for i, p in enumerate(pages[:4], start=1):
            th = p.copy()
            th.thumbnail((500, 647), Image.Resampling.LANCZOS)
            tp = thumbs_dir / f"{PACK_CODE}_PrintDetective_thumb{i}.png"
            th.save(tp, "PNG")
            thumb_paths.append(str(tp))
    except Exception:
        thumb_paths = []

    # Teacher Overview (simple branded single page) + overview data for Quick Start.
    OVERVIEW_DIR.mkdir(parents=True, exist_ok=True)
    overview_pdf = OVERVIEW_DIR / f"{PACK_CODE}_Teacher_Overview.pdf"
    ov = _activity_page("Print Detective", "Teacher Overview", PACK_CODE, 1, 1)
    d = ImageDraw.Draw(ov)
    lines = [
        ("WHAT IT IS", "A 4-level print-concepts and alphabet-knowledge activity: sort letters from symbols, tell letters from words, match letters to first sounds, and practise left-to-right tracking with word boundaries."),
        ("READING ROPE", "Alphabetic Principle · Print Concepts (fills the suite gap between phonological awareness and decoding)."),
        ("LINKS TO SUITE", "All pictures and words reuse the reviewed book vocabulary and icons, so the activity reinforces the same word set as Matching, Sorting and Syllable Cards."),
        ("PREP", "Print, cut the two card sheets and the picture cards, laminate for reuse. Low prep: under 10 minutes."),
        ("ACCESS", "Students may point, place cards, circle with a marker, or respond via AAC ('letter', 'word', 'same sound')."),
    ]
    y = 640
    for head, body in lines:
        b = (CX0, y, CX1, y + 430)
        d.rounded_rectangle(b, radius=36, fill=TEAL_LT, outline=TEAL, width=4)
        _center(d, (b[0] + 40, y + 30, b[0] + 760, y + 120), head, _font(13, True), NAVY)
        _center(d, (b[0] + 80, y + 140, b[2] - 80, y + 400), body, _fit(body, 12, b[2] - b[0] - 200, minimum=9, bold=False), NAVY)
        y += 470
    _save_pdf(overview_pdf, [ov])

    overview_data = {
        "product_name": "Print Detective: Letters, Words & First Sounds",
        "preparation": {"label": "Print and cut", "materials": "cardstock, scissors, laminator (optional)", "time": "10 minutes"},
        "teaching_steps": [
            {"title": "Sort", "detail": "Levels 1-2: student sorts each card and says the rule aloud."},
            {"title": "Match", "detail": "Level 3: say the picture name, stretch the first sound, place it under the letter."},
            {"title": "Track", "detail": "Level 4: follow the arrow, touch each word, find word boundaries."},
            {"title": "Check", "detail": "Use the answer key; record accuracy on the IEP monitoring form."},
        ],
        "access": ["Point or place cards", "AAC: 'letter', 'word', 'same'", "Dry-erase marker for Level 4"],
        "best_for": ["print concepts", "letter knowledge", "emergent readers", "AAC users"],
    }
    OVERVIEW_DATA.parent.mkdir(parents=True, exist_ok=True)
    OVERVIEW_DATA.write_text(json.dumps(overview_data, indent=2), encoding="utf-8")

    manifest = {
        "schema_version": 1,
        "status": "pilot_review",
        "teacher_review_required": True,
        "product_id": "print_detective",
        "product_name": "Print Detective: Letters, Words & First Sounds",
        "pack_code": PACK_CODE,
        "page_count": total,
        "levels": 4,
        "reading_rope": ["Alphabetic Principle", "Print Concepts"],
        "l3_pairs": {l: w for l, _, w in L3_PAIRS},
        "files": {"color_pdf": str(color_pdf), "bw_pdf": str(bw_pdf),
                  "teacher_overview": str(overview_pdf), "overview_data": str(OVERVIEW_DATA),
                  "thumbnails": thumb_paths},
        "meta": {"warnings": []},
    }
    result = OUTPUT / f"{PACK_CODE}_PrintDetective_BuildResult.json"
    result.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"OK  {color_pdf}")
    print(f"OK  {bw_pdf}")
    print(f"OK  {overview_pdf}")
    return manifest


def generate_print_detective_pack_wrapper(icons_dir: str, pack_code: str, theme_name: str) -> bool:
    """Standard 3-arg build wrapper for the app's run_product_build.

    Overrides the hardcoded pack code and theme paths to match the calling book.
    """
    global PACK_CODE, THEME, ICONS, OUTPUT
    try:
        # Resolve theme dir from icons_dir
        icons_path = Path(icons_dir).resolve()
        if icons_path.name == "icons" and icons_path.parent.name == ".sf_build":
            theme_dir = icons_path.parent.parent
        else:
            theme_dir = icons_path.parent
        # Override globals so the generator writes to the correct book's OUTPUT
        THEME = theme_dir
        ICONS = theme_dir / "activity_images"
        OUTPUT = theme_dir / "OUTPUT"
        PACK_CODE = pack_code
        result = generate_print_detective_pack()
        return bool(result)
    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    generate_print_detective_pack()
