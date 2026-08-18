"""
WORD SEARCH GENERATOR — 4 LEVELS
Small Wins Studio

OUTPUT (5 pages):
  Level 1 — Short words (≤4 letters), symbol padding, H/V only   — EASIEST
  Level 2 — Medium words (4-6 letters), letter padding, H/V only
  Level 3 — Longer words (5-8 letters), letter padding, diagonals
  Level 4 — All/longest words, letter padding, diagonals          — HARDEST
  Answer Key — 4 mini grids with highlights

WORD SELECTION — different words per level:
  Each level picks words from the full vocab by length bracket.
  Short words appear in easy levels; long words in harder levels.
  Minimum 3 words, maximum 8 words per level.
  If vocab has fewer words than the bracket, nearest words are used.

  Word source priority:
    1. book_vocab.json → "word_search_words" (explicit per-level override)
    2. book_vocab.json → "vocab_words" / "all_words" (auto-sorted by length)
    3. activity_images/ folder stems (auto-sorted by length)

ICON DISPLAY — image shown next to each word in the word list below the grid.
  Loads from activity_images/ → icons_colored/ → icons/
  If no icon found for a word, shows word text only (no crash).

FIXED (vs old generator):
  - Different words per level (not same 4 words on all pages)
  - Uses ALL available icons, not hardcoded [:4]
  - New SWS brand colours (#31A8A0 teal, #0D2545 navy)
  - Standard draw_header() / draw_footer()
  - Signature: generate_word_search(slug, book_title, pack_code)
  - clean_label() strips _2 dedup suffixes
  - Output to OUTPUT/ folder
"""

import io
import random
import re
import string
from pathlib import Path
try:
    REPO_ROOT = Path(__file__).resolve().parents[2]
except Exception:
    REPO_ROOT = Path.cwd()

from PIL import Image, ImageDraw, ImageFont
from utils.sws_design import generate_teacher_cover_page, apply_small_wins_frame
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

# ── Page / DPI ────────────────────────────────────────────────────────────────
PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

# ── SWS brand colours ─────────────────────────────────────────────────────────
SWS_TEAL   = "#31A8A0"
SWS_NAVY   = "#0D2545"
SWS_GOLD   = "#E1B42D"

LEVEL_COLORS = {
    1: "#7C3AED",
    2: "#0284C7",
    3: "#059669",
    4: "#E11D48",
}

PAGE_CREAM      = "#FDFCF8"
FOOTER_GREY     = "#F5F5F2"
GRID_LINE       = "#AAAAAA"
HIGHLIGHT_YELLOW= "#FFE066"
PADDING_SYMBOLS = ['●', '■', '▲', '★', '♦', '○', '□', '△']


# ── Helpers ───────────────────────────────────────────────────────────────────

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip('#')
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
        "title":      best(int(26 * scale), bold=True),
        "subtitle":   best(int(15 * scale)),
        "level":      best(int(13 * scale), bold=True),
        "grid":       best(int(17 * scale), bold=True),
        "grid_small": best(int(13 * scale), bold=True),
        "word_list":  best(int(13 * scale), bold=True),
        "label":      best(int(11 * scale)),
        "footer":     best(int(10 * scale)),
        "copyright":  best(int(7  * scale)),
        "level_badge":best(int(10 * scale), bold=True),
    }


# ── Header / Footer ───────────────────────────────────────────────────────────

def draw_header(page, draw, fonts, scale, img_w, img_h,
                book_title, product_name, subtitle="", level=None):
    # Deprecated: unified via apply_small_wins_frame below
    return int(1.8 * DPI)


def draw_footer(page, draw, fonts, scale, img_w, img_h,
                book_title, product_name, page_num, total_pages, level=None):
    # Deprecated: unified via apply_small_wins_frame below
    return int(1.0 * DPI)


# ── Word selection per level ──────────────────────────────────────────────────

def select_words_for_level(all_words: list[str], level: int) -> list[str]:
    """
    Pick appropriate words for each level based on word length.

    Level 1 — EASIEST: shortest words (≤4 letters). 3–5 words.
    Level 2 — EASY:    medium words (4–6 letters).  4–6 words.
    Level 3 — MEDIUM:  longer words (5–8 letters).  4–6 words.
    Level 4 — HARD:    all words, longest first.    5–8 words.

    If a bracket doesn't have enough words, we fill with nearest-length words.
    Single-letter words are always excluded.
    Words are deduplicated and at least 2 characters long.
    """
    # Clean: lowercase, deduplicate, min 2 chars
    clean = []
    seen  = set()
    for w in all_words:
        w2 = w.lower().strip()
        if len(w2) >= 2 and w2 not in seen:
            clean.append(w2)
            seen.add(w2)

    if not clean:
        return []

    sorted_by_len = sorted(clean, key=len)

    brackets = {
        1: (2, 4,  3, 5),   # min_len, max_len, min_words, max_words
        2: (4, 6,  4, 6),
        3: (5, 8,  4, 6),
        4: (2, 20, 5, 8),   # all lengths, longest first for L4
    }

    min_len, max_len, min_words, max_words = brackets[level]

    # Primary selection: words within length bracket
    primary = [w for w in sorted_by_len if min_len <= len(w) <= max_len]

    if level == 4:
        # Hardest level: sort longest-first
        primary = sorted(primary, key=len, reverse=True)

    # If not enough words in bracket, fill from nearest
    if len(primary) < min_words:
        extras = [w for w in sorted_by_len if w not in primary]
        if level == 4:
            extras = sorted(extras, key=len, reverse=True)
        primary += extras

    # Trim to max
    selected = primary[:max_words]

    # Ensure at least 3 words
    if len(selected) < 3 and len(clean) >= 3:
        selected = sorted_by_len[:3]

    return selected


# ── Grid builder ──────────────────────────────────────────────────────────────

def build_grid(words: list[str], grid_size: int,
               use_symbols: bool, allow_diagonal: bool,
               isolate: bool = False) -> tuple[list, dict]:
    """Place words in grid, fill remaining cells with padding."""
    grid = [[None] * grid_size for _ in range(grid_size)]
    positions = {}

    def adjacent_has_letter(r, c):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0<=nr<grid_size and 0<=nc<grid_size:
                if grid[nr][nc] and grid[nr][nc] not in PADDING_SYMBOLS:
                    return True
        return False

    # Sort longest word first to maximise placement success
    for word in sorted(words, key=len, reverse=True):
        wu = word.upper()
        placed = False
        for _ in range(600):
            if allow_diagonal:
                direction = random.randint(0, 3)
            else:
                direction = random.randint(0, 1)

            if direction == 0:    # horizontal
                if len(wu) > grid_size: continue
                r  = random.randint(0, grid_size - 1)
                c  = random.randint(0, grid_size - len(wu))
                dr, dc = 0, 1
            elif direction == 1:  # vertical
                if len(wu) > grid_size: continue
                r  = random.randint(0, grid_size - len(wu))
                c  = random.randint(0, grid_size - 1)
                dr, dc = 1, 0
            elif direction == 2:  # diagonal ↘
                span = len(wu)
                if span > grid_size: continue
                r  = random.randint(0, grid_size - span)
                c  = random.randint(0, grid_size - span)
                dr, dc = 1, 1
            else:                 # diagonal ↗
                span = len(wu)
                if span > grid_size: continue
                r  = random.randint(span - 1, grid_size - 1)
                c  = random.randint(0, grid_size - span)
                dr, dc = -1, 1

            ok = True
            cells = []
            for i, letter in enumerate(wu):
                nr, nc = r + i*dr, c + i*dc
                if not (0 <= nr < grid_size and 0 <= nc < grid_size):
                    ok = False; break
                existing = grid[nr][nc]
                if existing is not None and existing != letter:
                    ok = False; break
                if isolate and existing is None and adjacent_has_letter(nr, nc):
                    ok = False; break
                cells.append((nr, nc))

            if ok:
                for i, (nr, nc) in enumerate(cells):
                    grid[nr][nc] = wu[i]
                positions[word] = cells
                placed = True
                break

        if not placed:
            print(f"  WARN: Could not place '{word}' — try a larger grid")

    # Fill empty cells
    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] is None:
                grid[r][c] = (random.choice(PADDING_SYMBOLS) if use_symbols
                              else random.choice(string.ascii_uppercase))

    return grid, positions


# ── Icon loader ───────────────────────────────────────────────────────────────

def load_icon(slug: str, raw_stem: str) -> Image.Image | None:
    for folder in ["activity_images", "icons_colored", "icons"]:
        p = REPO_ROOT / "assets" / "themes" / slug / folder / f"{raw_stem}.png"
        if p.exists():
            try:
                return Image.open(p).convert("RGBA")
            except Exception:
                pass
    return None


# ── Vocab loader ──────────────────────────────────────────────────────────────

def load_vocab(slug: str) -> list[str]:
    """
    Returns list of raw word stems (lowercase, for grid + image lookup).
    Priority: book_vocab.json word_search_words → vocab_words → activity_images/
    """
    # Try book_vocab.json
    vp = REPO_ROOT / "assets" / "themes" / slug / "book_vocab.json"
    if vp.exists():
        try:
            import json
            data = json.loads(vp.read_text())
            # Explicit word_search override takes priority
            ws_words = data.get("word_search_words", [])
            if isinstance(ws_words, list) and ws_words:
                # Support objects with a 'word' key or plain strings
                out: list[str] = []
                for w in ws_words:
                    if isinstance(w, dict):
                        val = str(w.get("word", "")).strip().lower()
                    else:
                        val = str(w).strip().lower()
                    if val:
                        out.append(val)
                if out:
                    return out
            # Fall back to general vocab
            general = data.get("vocab_words", data.get("all_words", []))
            if general:
                return [str(w).strip().lower() for w in general if str(w).strip()]
        except Exception:
            pass

    # Fall back to activity_images/ stems
    for folder in ["activity_images", "icons_colored", "icons"]:
        img_dir = REPO_ROOT / "assets" / "themes" / slug / folder
        if img_dir.exists():
            stems = []
            seen  = set()
            for f in sorted(img_dir.glob("*.png")):
                stem = f.stem.lower()
                # Strip dedup suffixes like _2
                stem = re.sub(r'_\d+$', '', stem)
                if stem not in seen and len(stem) >= 2:
                    stems.append(stem)
                    seen.add(stem)
            if stems:
                return stems

    return []


# ── Word search page ──────────────────────────────────────────────────────────

def create_word_search_page(slug, book_title, words_raw, level,
                            page_num, total_pages, pack_code,
                            grid_size, use_symbols, allow_diagonal,
                            fonts, scale) -> tuple:
    """
    One word search page.
    words_raw: list of lowercase word stems (used for grid AND icon lookup)
    Returns (page_image, grid, positions)
    """
    img_w = int(PAGE_WIDTH  * DPI / 72)
    img_h = int(PAGE_HEIGHT * DPI / 72)
    page  = Image.new('RGB', (img_w, img_h), PAGE_CREAM)
    draw  = ImageDraw.Draw(page)

    level_colour = hex_to_rgb(LEVEL_COLORS.get(level, SWS_TEAL))

    level_descs = {
        1: "Symbols only  ·  Horizontal & Vertical",
        2: "Letters  ·  Horizontal & Vertical",
        3: "Letters  ·  Includes Diagonal",
        4: "Letters  ·  Full Diagonal  ·  Longest Words",
    }
    subtitle = level_descs.get(level, f"Level {level}")

    # Apply standard Small Wins frame for consistent header/branding —
    # STEL_MATCH standard: product in header, theme as subtitle
    apply_small_wins_frame(
        page,
        product_title="Word Search",
        subtitle=book_title,
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=level,
        show_data_strip=False,
    )

    # Reserve space similar to other generators using the frame
    hh = int(1.8 * DPI)
    fh = int(1.0 * DPI)

    content_top    = hh + int(10 * scale)
    content_bottom = img_h - fh - int(10 * scale)

    # "Find these words:" instruction
    inst = "Find the hidden words!"
    ib   = draw.textbbox((0, 0), inst, font=fonts["label"])
    draw.text(((img_w - (ib[2] - ib[0])) // 2, content_top),
              inst, fill=hex_to_rgb(SWS_NAVY), font=fonts["label"])
    content_top += (ib[3] - ib[1]) + int(10 * scale)

    # Build grid
    grid, positions = build_grid(
        words_raw, grid_size, use_symbols, allow_diagonal,
        isolate=(use_symbols)   # isolate words on L1 so they stand out
    )

    # ── Draw grid ─────────────────────────────────────────────────────────────
    # Allocate ~60% of content height to grid, 40% to word list
    grid_area_h = int((content_bottom - content_top) * 0.58)
    cell_size   = min(grid_area_h // grid_size, int(img_w * 0.85) // grid_size)
    grid_px_w   = cell_size * grid_size
    grid_px_h   = cell_size * grid_size
    grid_x      = (img_w - grid_px_w) // 2
    grid_y      = content_top

    grid_font = fonts["grid"] if cell_size >= int(40 * scale) else fonts["grid_small"]

    # Outer border
    bw = int(3 * scale)
    draw.rectangle(
        [grid_x - bw, grid_y - bw, grid_x + grid_px_w + bw, grid_y + grid_px_h + bw],
        outline=level_colour, width=bw
    )

    # Cells
    for row in range(grid_size):
        for col in range(grid_size):
            cx = grid_x + col * cell_size
            cy = grid_y + row * cell_size
            draw.rectangle([cx, cy, cx + cell_size, cy + cell_size],
                           outline=hex_to_rgb(GRID_LINE),
                           fill='white', width=1)
            ch = grid[row][col]
            cb = draw.textbbox((0, 0), ch, font=grid_font)
            cw = cb[2] - cb[0]; cht = cb[3] - cb[1]
            colour = (160, 160, 160) if ch in PADDING_SYMBOLS else hex_to_rgb(SWS_NAVY)
            draw.text((cx + (cell_size - cw) // 2, cy + (cell_size - cht) // 2 - int(1 * scale)),
                      ch, fill=colour, font=grid_font)

    # ── Word list below grid ───────────────────────────────────────────────────
    wl_top    = grid_y + grid_px_h + int(18 * scale)
    wl_bottom = content_bottom

    # Label
    lbl = "Find these words:"
    lb  = draw.textbbox((0, 0), lbl, font=fonts["label"])
    draw.text(((img_w - (lb[2] - lb[0])) // 2, wl_top),
              lbl, fill=hex_to_rgb(SWS_NAVY), font=fonts["label"])
    wl_top += (lb[3] - lb[1]) + int(8 * scale)

    # Word entries: icon + word text, 2 columns
    n        = len(words_raw)
    COLS     = 2
    icon_sz  = int(38 * scale)
    entry_h  = icon_sz + int(6 * scale)
    entry_w  = (img_w - int(60 * scale)) // COLS
    margin_x = int(30 * scale)

    for i, word in enumerate(words_raw):
        col = i % COLS
        row = i // COLS
        ex  = margin_x + col * entry_w
        ey  = wl_top + row * entry_h

        if ey + entry_h > wl_bottom:
            break   # no room — skip overflow words

        # Checkbox
        cb_sz = int(14 * scale)
        cb_y  = ey + (icon_sz - cb_sz) // 2
        draw.rectangle([ex, cb_y, ex + cb_sz, cb_y + cb_sz],
                       outline=hex_to_rgb(SWS_NAVY), fill='white', width=2)

        # Icon
        icon = load_icon(slug, word)
        icon_x = ex + cb_sz + int(6 * scale)
        if icon:
            ic = icon.copy()
            ic.thumbnail((icon_sz, icon_sz), Image.Resampling.LANCZOS)
            page.paste(ic, (icon_x, ey + (icon_sz - ic.height) // 2), ic)

        # Word text
        display = clean_label(word)
        wt_x = icon_x + icon_sz + int(8 * scale)
        wt_bb = draw.textbbox((0, 0), display.upper(), font=fonts["word_list"])
        draw.text((wt_x, ey + (icon_sz - (wt_bb[3] - wt_bb[1])) // 2),
                  display.upper(), fill=hex_to_rgb(SWS_NAVY), font=fonts["word_list"])

    return page, grid, positions


# ── Answer key page ───────────────────────────────────────────────────────────

def create_answer_key_page(all_words_per_level, all_grids, all_positions,
                           book_title, pack_code, total_pages,
                           fonts, scale) -> Image.Image:
    """4 mini grids side-by-side with highlighted answer cells."""
    img_w = int(PAGE_WIDTH  * DPI / 72)
    img_h = int(PAGE_HEIGHT * DPI / 72)
    page  = Image.new('RGB', (img_w, img_h), PAGE_CREAM)
    draw  = ImageDraw.Draw(page)

    apply_small_wins_frame(
        page,
        product_title="Word Search",
        subtitle=book_title,
        pack_code=pack_code,
        page_num=total_pages,
        total_pages=total_pages,
        level=None,
        footer_title="Word Search — Answer Key (all 4 levels)",
        show_data_strip=False,
    )
    hh = int(1.8 * DPI)
    fh = int(1.0 * DPI)

    content_top    = hh + int(15 * scale)
    content_bottom = img_h - fh - int(15 * scale)

    # 2×2 grid of mini grids
    h_gap = int(20 * scale)
    v_gap = int(30 * scale)
    target_sz = (img_w - int(60 * scale) - h_gap) // 2
    grid_top  = content_top

    for level_idx, (grid, positions) in enumerate(zip(all_grids, all_positions)):
        gs   = len(grid)
        cell = target_sz // gs
        actual_px = cell * gs

        col = level_idx % 2
        row = level_idx // 2
        gx  = int(30 * scale) + col * (target_sz + h_gap)
        gy  = grid_top + row * (target_sz + v_gap)

        # Level label
        lbl   = f"Level {level_idx + 1}"
        lc    = hex_to_rgb(LEVEL_COLORS.get(level_idx + 1, SWS_TEAL))
        lb    = draw.textbbox((0, 0), lbl, font=fonts["level"])
        draw.text((gx + (target_sz - (lb[2] - lb[0])) // 2, gy - int(20 * scale)),
                  lbl, fill=lc, font=fonts["level"])

        # Highlight set
        highlighted = {pos for pos_list in positions.values() for pos in pos_list}

        # Border
        draw.rectangle([gx - 2, gy - 2, gx + actual_px + 2, gy + actual_px + 2],
                       outline=lc, width=2)

        # Cells
        for r in range(gs):
            for c in range(gs):
                cx = gx + c * cell
                cy = gy + r * cell
                fill = hex_to_rgb(HIGHLIGHT_YELLOW) if (r, c) in highlighted else (255, 255, 255)
                draw.rectangle([cx, cy, cx + cell, cy + cell],
                               outline=hex_to_rgb(GRID_LINE), fill=fill, width=1)
                ch = grid[r][c]
                if ch not in PADDING_SYMBOLS:
                    fs = max(6, cell // 7)
                    try:
                        sf = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(fs * scale))
                    except Exception:
                        try:
                            sf = ImageFont.truetype(
                                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                                int(fs * scale))
                        except Exception:
                            sf = fonts["grid_small"]
                    cb  = draw.textbbox((0, 0), ch, font=sf)
                    draw.text(
                        (cx + (cell - (cb[2]-cb[0])) // 2,
                         cy + (cell - (cb[3]-cb[1])) // 2),
                        ch, fill=hex_to_rgb(SWS_NAVY), font=sf
                    )

        # Word list below each mini grid
        words_txt = "  ·  ".join(w.upper() for w in all_words_per_level[level_idx])
        wb = draw.textbbox((0, 0), words_txt, font=fonts["copyright"])
        draw.text((gx + (target_sz - (wb[2]-wb[0])) // 2,
                   gy + actual_px + int(4 * scale)),
                  words_txt, fill=hex_to_rgb(SWS_NAVY), font=fonts["copyright"])

    return page


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_word_search(slug: str, book_title: str,
                         pack_code: str = "STEL-WS") -> bool:
    """
    Generate Word Search pack (4 activity pages + answer key).

    Words are selected per level by length:
      L1: shortest words (easiest to find)
      L2: medium words
      L3: longer words + diagonals
      L4: all/longest words + full diagonals

    Args:
        slug:       Book slug e.g. 'stellaluna'
        book_title: Display name e.g. 'Stellaluna'
        pack_code:  TPT product code e.g. 'STEL-WS'
    """
    print(f"\n{'='*70}")
    print(f"  WORD SEARCH GENERATOR: {pack_code}  ({book_title})")
    print(f"{'='*70}\n")

    # ── Load vocabulary ───────────────────────────────────────────────────────
    all_words = load_vocab(slug)

    if not all_words:
        print(f"  ERROR: No vocabulary found for slug '{slug}'")
        return False

    print(f"  Full vocab ({len(all_words)} words): {', '.join(all_words)}\n")

    # ── Per-level word selection ──────────────────────────────────────────────
    levels_config = [
        {"level": 1, "grid_size": 8,  "use_symbols": True,  "allow_diagonal": False},
        {"level": 2, "grid_size": 9,  "use_symbols": False, "allow_diagonal": False},
        {"level": 3, "grid_size": 10, "use_symbols": False, "allow_diagonal": True},
        {"level": 4, "grid_size": 11, "use_symbols": False, "allow_diagonal": True},
    ]

    words_per_level = []
    for cfg in levels_config:
        lvl_words = select_words_for_level(all_words, cfg["level"])
        words_per_level.append(lvl_words)
        print(f"  Level {cfg['level']} words ({len(lvl_words)}): "
              f"{', '.join(w.upper() for w in lvl_words)}")

    print()

    output_dir = Path("OUTPUT")
    output_dir.mkdir(exist_ok=True)

    scale  = DPI / 72
    fonts  = load_fonts(scale)
    TOTAL  = 6   # cover + 4 levels + answer key

    saved_pages     = []
    all_grids       = []
    all_positions   = []

    # ── Insert universal teacher cover (Page 1) ──────────────────────────────
    try:
        repo_root = Path(__file__).resolve().parents[1]
        tdir = repo_root / "assets" / "themes" / slug
        hero_path_str = None
        book_cover_path_str = None
        hero_candidates = [
            tdir / "hero_header.png",
            tdir / "heroes" / "hero_header.png",
            tdir / "characters" / "hero_header.png",
            tdir / "hero.png",
            tdir / "heroes" / "hero.png",
            tdir / "characters" / "hero.png",
            tdir / "header_icon.png",
        ]
        for hp in hero_candidates:
            if hp.exists():
                hero_path_str = str(hp)
                break
        cover_names = ["book_cover", "cover", "front_cover", "bookfront", "book", "cover_reference"]
        cover_subdirs = [tdir, tdir / "covers", tdir / "images", tdir / "marketing", tdir / "book"]
        exts = ["png", "jpg", "jpeg", "webp"]
        for sd in cover_subdirs:
            for nm in cover_names:
                for ex in exts:
                    fp = sd / f"{nm}.{ex}"
                    if fp.exists():
                        book_cover_path_str = str(fp)
                        break
                if book_cover_path_str:
                    break
            if book_cover_path_str:
                break
        cov = generate_teacher_cover_page(
            theme_name=book_title,
            pack_code=pack_code,
            product_name="Word Search",
            page_count=5,  # 4 levels + answer key
            level_count=4,
            hero_image=None,
            hero_image_path=hero_path_str,
            book_cover_path=book_cover_path_str,
            draw_footer=False,
            whats_included=[
                "4 differentiated levels",
                "Icon list below grids",
                "Answer key included",
                "Colour + B&W versions",
            ],
            also_included=[
                "Quick Start Guide",
                "Terms of Use",
                "B&W version",
            ],
            top_tips=[
                "Start at Level 1 and progress to diagonals.",
                "Model scanning left-to-right and top-to-bottom.",
                "Use icons to support early readers.",
            ],
            rope_strand="Word Recognition",
            rope_skills="Decoding · Sight Words · Orthographic Mapping",
            render_chips=False,
        )
        saved_pages.append(cov)
    except Exception:
        pass

    # ── Generate 4 level pages ────────────────────────────────────────────────
    for i, cfg in enumerate(levels_config):
        level     = cfg["level"]
        words_raw = words_per_level[i]
        print(f"  Generating Level {level} ...")

        page, grid, positions = create_word_search_page(
            slug, book_title, words_raw, level,
            i + 2, TOTAL, pack_code,
            cfg["grid_size"], cfg["use_symbols"], cfg["allow_diagonal"],
            fonts, scale
        )
        saved_pages.append(page)
        all_grids.append(grid)
        all_positions.append(positions)

    # ── Answer key ────────────────────────────────────────────────────────────
    print("  Generating Answer Key ...")
    answer = create_answer_key_page(
        words_per_level, all_grids, all_positions,
        book_title, pack_code, TOTAL, fonts, scale
    )
    saved_pages.append(answer)

    print(f"\n  {len(saved_pages)} pages total\n")

    # ── Write PDFs ────────────────────────────────────────────────────────────
    def to_pdf(pages, path, gray=False):
        c = rl_canvas.Canvas(str(path), pagesize=letter)
        for pg in pages:
            if gray:
                pg = pg.convert("L").convert("RGB")
            buf = io.BytesIO()
            pg.save(buf, format="PNG", dpi=(DPI, DPI))
            buf.seek(0)
            c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
            c.showPage()
        c.save()

    color_path = output_dir / f"{pack_code}_WordSearch_COLOR.pdf"
    bw_path    = output_dir / f"{pack_code}_WordSearch_BW.pdf"

    print("  Writing COLOR PDF ...")
    to_pdf(saved_pages, color_path)
    print(f"  ✓  {color_path}")

    print("  Writing B&W PDF ...")
    to_pdf(saved_pages, bw_path, gray=True)
    print(f"  ✓  {bw_path}")

    # Preview (Level 1 page only)
    preview_path = output_dir / f"{pack_code}_WordSearch_PREVIEW.pdf"
    c_prev = rl_canvas.Canvas(str(preview_path), pagesize=letter)
    buf = io.BytesIO()
    saved_pages[0].save(buf, format="PNG", dpi=(DPI, DPI))
    buf.seek(0)
    c_prev.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
    c_prev.saveState()
    c_prev.setFont("Helvetica-Bold", 140)
    c_prev.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
    c_prev.translate(PAGE_WIDTH / 2, PAGE_HEIGHT / 2)
    c_prev.rotate(45)
    c_prev.drawCentredString(0, 0, "PREVIEW")
    c_prev.restoreState()
    c_prev.showPage()
    c_prev.save()
    print(f"  ✓  {preview_path}")

    print(f"\n{'='*70}")
    print(f"  WORD SEARCH COMPLETE — {len(saved_pages)} pages")
    print(f"{'='*70}\n")
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python WORD_SEARCH_GENERATOR.py <slug> <book_title> [pack_code]")
        print("  e.g. python WORD_SEARCH_GENERATOR.py stellaluna Stellaluna STEL-WS")
        sys.exit(1)

    slug       = sys.argv[1]
    book_title = sys.argv[2]
    pack_code  = sys.argv[3] if len(sys.argv) > 3 else "WS"

    ok = generate_word_search(slug, book_title, pack_code)
    sys.exit(0 if ok else 1)
