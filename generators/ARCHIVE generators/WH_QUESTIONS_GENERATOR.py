"""
WH QUESTIONS GENERATOR
Small Wins Studio
Scarborough strand: Verbal Reasoning + Language Structures

Generates WH question cards (who/what/where/when/why/how) using book content.
Different from Yes/No — these require a constructed response, not just yes/no.

CARD DESIGN:
  ┌────────────────────────────────────────┐
  │  [WH word badge]  [Question icon]      │
  │                                        │
  │  "WHO does Stellaluna live with?"      │
  │                                        │
  │  [Icon clue]    ________________       │
  │                 ________________       │
  │                 ________________       │
  │                                        │
  │  L1: answer shown    L2: blank         │
  └────────────────────────────────────────┘

QUESTION TYPES PER WH WORD:
  WHO:   Characters, people, animals in the story
  WHAT:  Objects, events, actions
  WHERE: Settings, locations
  WHEN:  Time, sequence, beginning/middle/end
  WHY:   Cause/effect, character motivation
  HOW:   Process, manner, feeling

LEVELS:
  L1: Icon shown + answer provided (model/supported)
  L2: Icon shown, answer blank (guided)
  L3: No icon, text only (independent)

OUTPUT:
  4 cards per page × multiple pages
  6 question types × N questions each
  + Answer key + IEP tracker

QUESTIONS: AI-generated from book title + vocab, or uses template set.
           If Claude API available, generates book-specific questions.
           If not, uses template patterns with book vocab.

Usage:
  python WH_QUESTIONS_GENERATOR.py stellaluna Stellaluna STEL-WH
"""

from __future__ import annotations

import io
import json
import os
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

# ── Page / DPI ────────────────────────────────────────────────────────────────
PAGE_WIDTH_PT, PAGE_HEIGHT_PT = letter
DPI = 300
PAGE_W = int(PAGE_WIDTH_PT  * DPI / 72)
PAGE_H = int(PAGE_HEIGHT_PT * DPI / 72)

# ── SWS brand colours ─────────────────────────────────────────────────────────
SWS_TEAL  = "#31A8A0"
SWS_NAVY  = "#0D2545"
SWS_GOLD  = "#E1B42D"

LEVEL_COLORS = {1: "#7C3AED", 2: "#0284C7", 3: "#059669"}
PAGE_CREAM  = "#FDFCF8"
FOOTER_GREY = "#F5F5F2"

# WH word colours (one per question type)
WH_COLORS = {
    "WHO":   "#7C3AED",   # Violet
    "WHAT":  "#0284C7",   # Ocean
    "WHERE": "#059669",   # Emerald
    "WHEN":  "#E11D48",   # Rose
    "WHY":   "#D97706",   # Amber
    "HOW":   "#0891B2",   # Cyan
}

CARDS_PER_PAGE = 4


# ── Template question sets (fallback if no AI) ────────────────────────────────
# Format: (wh_word, question_template, answer_template, icon_hint)
# {title} = book title, {vocab_0} = first vocab word etc.

QUESTION_TEMPLATES = [
    ("WHO",   "Who is the main character in {title}?",
              "The main character is...", "character"),
    ("WHO",   "Who does the main character meet?",
              "The main character meets...", "friend"),
    ("WHO",   "Who helps solve the problem?",
              "The one who helps is...", "helper"),
    ("WHAT",  "What problem does the main character have?",
              "The problem is...", "problem"),
    ("WHAT",  "What happens at the beginning of {title}?",
              "At the beginning...", "beginning"),
    ("WHAT",  "What happens at the end of {title}?",
              "At the end...", "end"),
    ("WHERE", "Where does {title} take place?",
              "The story takes place in / at...", "setting"),
    ("WHERE", "Where does the main character go?",
              "The character goes to...", "location"),
    ("WHEN",  "When does the problem happen?",
              "The problem happens when...", "problem"),
    ("WHEN",  "When is the story resolved?",
              "The story is resolved at the...", "end"),
    ("WHY",   "Why does the main character have a problem?",
              "The character has a problem because...", "problem"),
    ("WHY",   "Why is {title} a good story to read?",
              "This is a good story because...", "book"),
    ("HOW",   "How does the main character feel at the start?",
              "At the start, the character feels...", "feelings"),
    ("HOW",   "How is the problem solved in {title}?",
              "The problem is solved by...", "solution"),
    ("HOW",   "How does the story end?",
              "The story ends with...", "end"),
]


def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def clean_label(word: str) -> str:
    if not word:
        return ""
    label = str(word).replace("_", " ").replace("-", " ").strip()
    label = re.sub(r'\s+\d+$', '', label)
    label = re.sub(r'_\d+$',   '', label)
    return label.strip().title()


def load_fonts(scale: float) -> dict:
    def best(size, bold=False):
        paths = (
            ["C:/Windows/Fonts/arialbd.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
            if bold else
            ["C:/Windows/Fonts/arial.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
        )
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
        return ImageFont.load_default()

    return {
        "title":       best(int(34 * scale), bold=True),
        "subtitle":    best(int(15 * scale)),
        "wh_badge":    best(int(22 * scale), bold=True),
        "question":    best(int(14 * scale), bold=True),
        "answer":      best(int(12 * scale)),
        "small":       best(int(9  * scale)),
        "footer":      best(int(10 * scale)),
        "copyright":   best(int(7  * scale)),
        "level_badge": best(int(10 * scale), bold=True),
        "hint":        best(int(10 * scale)),
    }


def _load_icon(slug: str, word: str) -> Image.Image | None:
    stems = [word.lower(), word.lower().replace(" ", "_")]
    for stem in stems:
        for folder in ["activity_images", "icons_colored", "icons"]:
            p = Path(__file__).resolve().parents[2] / "assets" / "themes" / slug / folder / f"{stem}.png"
            if p.exists():
                try:
                    return Image.open(p).convert("RGBA")
                except Exception:
                    pass
    return None


def _load_vocab(slug: str) -> list[str]:
    vp = Path(__file__).resolve().parents[2] / "assets" / "themes" / slug / "book_vocab.json"
    if vp.exists():
        try:
            data = json.loads(vp.read_text(encoding="utf-8", errors="ignore"))
            words = data.get("vocab_words", data.get("all_words", []))
            out = [str(w).strip().lower() for w in words if str(w).strip()]
            if out:
                return out
        except Exception:
            pass
    vp = Path(__file__).resolve().parents[2] / "assets" / "themes" / slug / "config" / "book_vocab.json"
    if vp.exists():
        try:
            data = json.loads(vp.read_text(encoding="utf-8", errors="ignore"))
            # Only return vocab words from config; do not return wh_questions here
            words = data.get("vocab_words", data.get("all_words", []))
            return [str(w).strip().lower() for w in words if str(w).strip()]
        except Exception:
            pass

    for folder in ["activity_images", "icons_colored", "icons"]:
        img_dir = Path(__file__).resolve().parents[2] / "assets" / "themes" / slug / folder
        if img_dir.exists():
            return [re.sub(r'_\d+$', '', f.stem.lower())
                    for f in sorted(img_dir.glob("*.png"))]
    return []


def _load_wh_from_config(slug: str) -> list[dict]:
    data = None
    # Prefer top-level book_vocab.json, fallback to config/book_vocab.json
    for vp in [
        Path(__file__).resolve().parents[2] / "assets" / "themes" / slug / "book_vocab.json",
        Path(__file__).resolve().parents[2] / "assets" / "themes" / slug / "config" / "book_vocab.json",
    ]:
        if not vp.exists():
            continue
        try:
            cand = json.loads(vp.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            cand = None
        if cand and cand.get("wh_questions"):
            data = cand
            break
    if not data:
        return []
    wh = data.get("wh_questions")
    if not wh:
        return []
    out: list[dict] = []
    for item in wh:
        if isinstance(item, dict):
            w = str(item.get("wh") or "").strip().upper()
            q = str(item.get("question") or "").strip()
            a = str(item.get("answer") or "").strip()
            ih = str(item.get("icon_hint") or item.get("icon") or "").strip()
            if q:
                out.append({"wh": (w or "WHAT"), "question": q, "answer": a, "icon_hint": ih})
        elif isinstance(item, str):
            q = item.strip()
            if q:
                out.append({"wh": "", "question": q, "answer": "", "icon_hint": ""})
    return out


def _allow_wh_ai() -> bool:
    v = os.getenv("SWS_ALLOW_WH_AI", "").strip().lower()
    return v in {"1", "true", "yes", "y"}


def _generate_questions_ai(book_title: str, vocab: list[str]) -> list[dict] | None:
    """Try to generate questions via Claude API."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""You are a special education teacher creating WH question cards for the book "{book_title}".
Vocabulary words from this book: {', '.join(vocab[:20])}

Generate exactly 18 WH questions (3 per WH word: WHO, WHAT, WHERE, WHEN, WHY, HOW).
Each question should be simple, clear, and answerable from the story.

Return ONLY valid JSON, no markdown:
[
  {{
    "wh": "WHO",
    "question": "Who is the main character?",
    "answer": "The main character is Stellaluna, a bat.",
    "icon_hint": "bat"
  }},
  ...18 total
]

Rules:
- Questions must be about THIS book specifically
- Answers should be 1-2 sentences, simple language
- icon_hint = one word from the vocabulary list that relates to the question
- No abstract questions — keep it concrete and book-specific
- WHO: characters and helpers
- WHAT: objects, events, problems
- WHERE: settings and places
- WHEN: time and sequence
- WHY: cause/effect, motivation
- HOW: process, feelings, resolution"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    except Exception as e:
        print(f"  AI question generation failed: {e}")
        return None


def _build_question_list(slug: str, book_title: str, vocab: list[str],
                          use_ai: bool = False) -> list[dict]:
    """Get WH question list — prefer grounded config; optional AI; else templates."""
    cfg = _load_wh_from_config(slug)
    if cfg:
        print(f"  ✓ Using grounded wh_questions from config: {len(cfg)} items")
        return cfg
    if use_ai and _allow_wh_ai():
        questions = _generate_questions_ai(book_title, vocab)
        if questions:
            print(f"  ✓ AI generated {len(questions)} questions")
            return questions

    # Template fallback
    print("  Using template questions (no AI / API key not set)")
    vocab_safe = vocab if vocab else ["the character", "the story"]
    questions  = []
    for wh, q_template, a_template, icon_hint in QUESTION_TEMPLATES:
        q = q_template.format(
            title=book_title,
            vocab_0=clean_label(vocab_safe[0]) if vocab_safe else "the character"
        )
        a = a_template
        icon = icon_hint if _load_icon(slug, icon_hint) else (vocab_safe[0] if vocab_safe else "")
        questions.append({
            "wh": wh, "question": q, "answer": a,
            "icon_hint": vocab_safe[0] if vocab_safe else ""
        })
    return questions


# ── Header / Footer ───────────────────────────────────────────────────────────

def draw_header(page, draw, fonts, scale, book_title, subtitle="", level=None):
    hh = int(80 * scale)
    draw.rectangle([0, 0, PAGE_W, hh], fill=hex_to_rgb(SWS_TEAL))
    draw.text((int(18 * scale), int(10 * scale)),
              f"{book_title}  ·  WH Questions",
              fill=(255, 255, 255), font=fonts["title"])
    if subtitle:
        draw.text((int(18 * scale), int(48 * scale)),
                  subtitle, fill=(210, 240, 238), font=fonts["subtitle"])

    if level is not None:
        lc      = hex_to_rgb(LEVEL_COLORS.get(level, SWS_TEAL))
        dot_r   = int(7 * scale)
        badge   = f"Level {level}"
        bb      = draw.textbbox((0, 0), badge, font=fonts["level_badge"])
        total_w = dot_r * 2 + int(6 * scale) + (bb[2] - bb[0])
        bx      = PAGE_W - int(20 * scale) - total_w
        dcx     = bx + dot_r
        dcy     = hh // 2
        draw.ellipse([dcx - dot_r, dcy - dot_r, dcx + dot_r, dcy + dot_r], fill=lc)
        draw.text((bx + dot_r * 2 + int(6 * scale), dcy - (bb[3] - bb[1]) // 2),
                  badge, fill=(255, 255, 255), font=fonts["level_badge"])
    return hh


def draw_footer(page, draw, fonts, scale,
                book_title, pack_code, page_num, total_pages, level=None):
    fh   = int(52 * scale)
    fy   = PAGE_H - fh
    lc   = hex_to_rgb(LEVEL_COLORS.get(level, SWS_TEAL)) if level else hex_to_rgb(SWS_TEAL)

    draw.rectangle([0, fy, PAGE_W, PAGE_H], fill=hex_to_rgb(FOOTER_GREY))
    draw.rectangle([0, fy, PAGE_W, fy + int(3 * scale)], fill=lc)
    y_mid = fy + fh // 2

    draw.text((int(14 * scale), y_mid - int(8 * scale)),
              "★", fill=hex_to_rgb(SWS_GOLD), font=fonts["subtitle"])

    cl1 = f"{book_title}  ·  WH Questions"
    cl2 = "PCS® symbols used under active Boardmaker licence  ·  © 2026 Small Wins Studio"
    for text, fk, col, dy in [
        (cl1, "footer",    (85, 85, 85),    -10),
        (cl2, "copyright", (170, 170, 170),   3),
    ]:
        bb = draw.textbbox((0, 0), text, font=fonts[fk])
        draw.text(((PAGE_W - (bb[2] - bb[0])) // 2, y_mid + int(dy * scale)),
                  text, fill=col, font=fonts[fk])

    pn = f"Page {page_num} of {total_pages}"
    pb = draw.textbbox((0, 0), pn, font=fonts["footer"])
    draw.text((PAGE_W - int(14 * scale) - (pb[2] - pb[0]),
               y_mid - int(7 * scale)),
              pn, fill=lc, font=fonts["footer"])
    return fh


# ── Single question card ──────────────────────────────────────────────────────

def _draw_question_card(page, draw, fonts, scale,
                         cx, cy, cw, ch,
                         question_data: dict,
                         slug: str, level: int, color: bool):
    """Draw one WH question card."""
    wh      = question_data["wh"]
    question= question_data["question"]
    answer  = question_data.get("answer", "")
    icon_hint= question_data.get("icon_hint", "")

    wh_color = hex_to_rgb(WH_COLORS.get(wh, SWS_TEAL))
    navy     = hex_to_rgb(SWS_NAVY)

    # Card background
    draw.rounded_rectangle(
        [cx, cy, cx + cw, cy + ch],
        radius=int(10 * scale),
        fill='white' if color else (248, 248, 248),
        outline=wh_color, width=int(3 * scale)
    )

    # WH badge top-left
    badge_w = int(cw * 0.25)
    badge_h = int(ch * 0.18)
    draw.rounded_rectangle(
        [cx + int(3 * scale), cy + int(3 * scale),
         cx + badge_w, cy + badge_h],
        radius=int(8 * scale), fill=wh_color
    )
    wb = draw.textbbox((0, 0), wh, font=fonts["wh_badge"])
    draw.text((cx + int(3 * scale) + (badge_w - int(3 * scale) - (wb[2] - wb[0])) // 2,
               cy + int(3 * scale) + (badge_h - int(3 * scale) - (wb[3] - wb[1])) // 2),
              wh, fill=(255, 255, 255), font=fonts["wh_badge"])

    # Icon (top right)
    icon_zone_w = int(cw * 0.28)
    icon_zone_h = int(ch * 0.42)
    icon_x = cx + cw - icon_zone_w - int(8 * scale)

    if icon_hint and level < 3:
        icon = _load_icon(slug, icon_hint)
        if icon:
            if not color:
                icon = icon.convert("L").convert("RGBA")
            ic = icon.copy()
            pad = int(8 * scale)
            ic.thumbnail((icon_zone_w - pad * 2, icon_zone_h - pad * 2),
                         Image.Resampling.LANCZOS)
            page.paste(ic,
                       (icon_x + (icon_zone_w - ic.width) // 2,
                        cy + int(8 * scale) + (icon_zone_h - ic.height) // 2),
                       ic)

    # Question text
    q_x   = cx + int(12 * scale)
    q_y   = cy + badge_h + int(10 * scale)
    q_w   = (cw - icon_zone_w - int(28 * scale)) if level < 3 else cw - int(24 * scale)

    words = question.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        bb   = draw.textbbox((0, 0), test, font=fonts["question"])
        if bb[2] - bb[0] <= q_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))

    lh = int(draw.textbbox((0, 0), "Ag", font=fonts["question"])[3]) + int(4 * scale)
    for line in lines:
        draw.text((q_x, q_y), line, fill=navy, font=fonts["question"])
        q_y += lh

    # Answer area
    ans_top = cy + int(ch * 0.50)
    draw.line([(cx + int(12 * scale), ans_top),
               (cx + cw - int(12 * scale), ans_top)],
              fill=(210, 210, 210), width=int(1 * scale))

    if level == 1 and answer:
        # Show answer
        ans_words = answer.split()
        ans_lines, cur = [], []
        ans_w = cw - int(24 * scale)
        for w in ans_words:
            test = " ".join(cur + [w])
            bb   = draw.textbbox((0, 0), test, font=fonts["answer"])
            if bb[2] - bb[0] <= ans_w:
                cur.append(w)
            else:
                if cur:
                    ans_lines.append(" ".join(cur))
                cur = [w]
        if cur:
            ans_lines.append(" ".join(cur))

        ay = ans_top + int(8 * scale)
        alh = int(draw.textbbox((0, 0), "Ag", font=fonts["answer"])[3]) + int(4 * scale)
        for aline in ans_lines[:3]:
            draw.text((cx + int(12 * scale), ay),
                      aline, fill=(80, 80, 80), font=fonts["answer"])
            ay += alh
    else:
        # Writing lines
        n_lines = max(2, int((ch - (ans_top - cy) - int(16 * scale)) / int(22 * scale)))
        line_y  = ans_top + int(12 * scale)
        line_h2 = int(22 * scale)
        for _ in range(min(n_lines, 3)):
            draw.line([(cx + int(16 * scale), line_y),
                       (cx + cw - int(16 * scale), line_y)],
                      fill=(190, 190, 190), width=int(1 * scale))
            line_y += line_h2

        if level == 1 and (not answer):
            warn = "Answer needed"
            tx = cx + int(16 * scale)
            ty = ans_top - int(14 * scale)
            draw.text((tx, ty), warn, fill=(180, 60, 60), font=fonts["small"])


# ── Page builder ──────────────────────────────────────────────────────────────

def _make_questions_page(slug, book_title, pack_code,
                          questions_chunk: list[dict],
                          level: int,
                          page_num: int, total_pages: int,
                          color: bool) -> Image.Image:
    scale = DPI / 72
    fonts = load_fonts(scale)

    level_subs = {
        1: "Supported — answer shown (model with student)",
        2: "Guided — write your answer",
        3: "Independent — text only, no picture clue",
    }

    page = Image.new("RGB", (PAGE_W, PAGE_H), PAGE_CREAM)
    draw = ImageDraw.Draw(page)

    hh = draw_header(page, draw, fonts, scale,
                     book_title,
                     subtitle=level_subs.get(level, ""),
                     level=level)
    fh = draw_footer(page, draw, fonts, scale,
                     book_title, pack_code, page_num, total_pages, level)

    content_top    = hh + int(12 * scale)
    content_bottom = PAGE_H - fh - int(12 * scale)
    margin         = int(24 * scale)
    gap            = int(12 * scale)
    inner_w        = PAGE_W - 2 * margin

    COLS = 2
    ROWS = 2
    card_w = (inner_w - gap) // COLS
    card_h = (content_bottom - content_top - gap) // ROWS

    for i, qdata in enumerate(questions_chunk[:CARDS_PER_PAGE]):
        col = i % COLS
        row = i // COLS
        cx  = margin + col * (card_w + gap)
        cy  = content_top + row * (card_h + gap)
        _draw_question_card(page, draw, fonts, scale,
                             cx, cy, card_w, card_h,
                             qdata, slug, level, color)

    return page


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_wh_questions(slug: str, book_title: str,
                            pack_code: str = "STEL-WH",
                            use_ai: bool = False) -> bool:
    """
    Generate WH Questions pack.

    Args:
        slug:       Book slug e.g. 'stellaluna'
        book_title: Display name e.g. 'Stellaluna'
        pack_code:  TPT product code e.g. 'STEL-WH'
        use_ai:     Try Claude API for question generation (default True)
    """
    print(f"\n{'='*70}")
    print(f"  WH QUESTIONS: {pack_code}  ({book_title})")
    print(f"{'='*70}\n")

    vocab     = _load_vocab(slug)
    if _load_wh_from_config(slug):
        questions = _load_wh_from_config(slug)
    elif use_ai and _allow_wh_ai():
        questions = _generate_questions_ai(book_title, vocab) or []
        if not questions:
            questions = _build_question_list(slug, book_title, vocab, use_ai=False)
    else:
        questions = _build_question_list(slug, book_title, vocab, use_ai=False)

    print(f"  Questions: {len(questions)}")
    for q in questions[:6]:
        print(f"    [{q['wh']:5}] {q['question'][:60]}")
    print()

    output_dir = Path("OUTPUT")
    output_dir.mkdir(exist_ok=True)

    import math
    LEVELS      = [1, 2, 3]
    pages_per_l = math.ceil(len(questions) / CARDS_PER_PAGE)
    TOTAL_PAGES = len(LEVELS) * pages_per_l + 1   # +1 IEP tracker

    def build(color: bool) -> list[Image.Image]:
        pages    = []
        page_num = 1
        for level in LEVELS:
            for i in range(pages_per_l):
                chunk = questions[i * CARDS_PER_PAGE:(i + 1) * CARDS_PER_PAGE]
                pages.append(_make_questions_page(
                    slug, book_title, pack_code, chunk,
                    level, page_num, TOTAL_PAGES, color
                ))
                page_num += 1

        # IEP tracker
        try:
            from IEP_TRACKER_PAGE import make_tracker_page
            pages.append(make_tracker_page(
                slug, book_title, "WH Questions", pack_code,
                level=None, page_num=page_num, total_pages=TOTAL_PAGES
            ))
        except ImportError:
            pages.append(Image.new("RGB", (PAGE_W, PAGE_H), PAGE_CREAM))

        return pages

    def to_pdf(pages, path, gray=False):
        c = rl_canvas.Canvas(str(path), pagesize=letter)
        for pg in pages:
            if gray:
                pg = pg.convert("L").convert("RGB")
            buf = io.BytesIO()
            pg.save(buf, format="PNG", dpi=(DPI, DPI))
            buf.seek(0)
            c.drawImage(ImageReader(buf), 0, 0,
                        width=PAGE_WIDTH_PT, height=PAGE_HEIGHT_PT)
            c.showPage()
        c.save()

    color_path = output_dir / f"{pack_code}_WHQuestions_COLOR.pdf"
    bw_path    = output_dir / f"{pack_code}_WHQuestions_BW.pdf"

    print(f"  {TOTAL_PAGES} pages total\n")

    print("  Writing COLOR PDF ...")
    to_pdf(build(color=True), color_path)
    print(f"  ✓  {color_path}")

    print("  Writing B&W PDF ...")
    to_pdf(build(color=False), bw_path, gray=True)
    print(f"  ✓  {bw_path}")

    print(f"\n{'='*70}")
    print(f"  WH QUESTIONS COMPLETE — {TOTAL_PAGES} pages")
    print(f"{'='*70}\n")
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python WH_QUESTIONS_GENERATOR.py <slug> <book_title> [pack_code] [--use-ai]")
        sys.exit(1)
    use_ai = "--use-ai" in sys.argv
    ok = generate_wh_questions(
        sys.argv[1], sys.argv[2],
        sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "WH",
        use_ai=use_ai
    )
    sys.exit(0 if ok else 1)
