"""
VOCABULARY WORD WALL GENERATOR
Small Wins Studio

Generates symbol-supported vocabulary display cards for classroom word walls.

OUTPUT (per book):
  Page 1+:  Word cards — 4 per page (landscape A5 size), full colour
  Final:    B&W version identical structure

CARD DESIGN (each card):
  ┌─────────────────────────────────┐
  │  ████  teal header strip        │  ← Book title + "Vocabulary"
  │                                 │
  │      [  BIG PCS IMAGE  ]        │  ← 60% of card height
  │                                 │
  │  ══════════════════════         │  ← divider line
  │                                 │
  │         WORD TEXT               │  ← large bold, 28pt+
  │                                 │
  │  ┌──────────────────────┐       │
  │  │ __ __ __ (syllables) │       │  ← dot per syllable
  │  └──────────────────────┘       │
  └─────────────────────────────────┘

VERSIONS:
  Full: image + word + syllable dots
  Word-only: word + syllable dots (no image) — for assessment

4 cards per A4 page, landscape, print-cut-laminate format.
Also outputs a "classroom banner" version (8 per page, smaller).

Usage:
  python VOCAB_WORD_WALL.py stellaluna Stellaluna STEL-VWW
  
  from VOCAB_WORD_WALL import generate_word_wall
  generate_word_wall("stellaluna", "Stellaluna", "STEL-VWW")
"""

from __future__ import annotations

import io
import json
import os
import re
from pathlib import Path
import importlib.util

from PIL import Image, ImageChops, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas
try:
    from utils.sws_design import apply_small_wins_frame, _brand_font_pt, generate_teacher_cover_page
except Exception:
    try:
        _alt = Path(__file__).resolve().parents[2] / "utils" / "sws_design.py"
        _spec = importlib.util.spec_from_file_location("_SWS_SWS_DESIGN", str(_alt))
        if _spec and _spec.loader:
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            apply_small_wins_frame = getattr(_mod, "apply_small_wins_frame")
            _brand_font_pt = getattr(_mod, "_brand_font_pt")
            generate_teacher_cover_page = getattr(_mod, "generate_teacher_cover_page")
        else:
            raise ImportError("sws_design spec loader not available")
    except Exception as _e:
        raise

# Absolute repo root for stable asset paths regardless of CWD
try:
    REPO_ROOT = Path(__file__).resolve().parents[2]
except Exception:
    REPO_ROOT = Path.cwd()

# ── Page / DPI ────────────────────────────────────────────────────────────────
# Word wall cards print landscape A4 — we use letter landscape
PAGE_W_PT, PAGE_H_PT = landscape(letter)   # 792 × 612 pt
DPI = 300
PAGE_W = int(PAGE_W_PT * DPI / 72)
PAGE_H = int(PAGE_H_PT * DPI / 72)
SNAP_W_PT, SNAP_H_PT = letter
SNAP_W = int(SNAP_W_PT * DPI / 72)
SNAP_H = int(SNAP_H_PT * DPI / 72)
SNAP_CARDS_PER_PAGE = 6
SNAP_CARD_RATIO = 1.42

# ── SWS brand colours ─────────────────────────────────────────────────────────
SWS_TEAL  = "#31A8A0"
SWS_NAVY  = "#0D2545"
SWS_GOLD  = "#E1B42D"

PAGE_CREAM  = "#FDFCF8"
FOOTER_GREY = "#F5F5F2"
CARD_BG     = "#FFFFFF"


# ── Helpers ───────────────────────────────────────────────────────────────────

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def clean_label(word: str) -> str:
    if not word:
        return ""
    label = str(word).replace("_", " ").replace("-", " ").strip()
    label = re.sub(r'\s+\d+$', '', label)
    label = re.sub(r'_\d+$',   '', label)
    label = label.strip()
    # Sentence case: capitalize first character, keep rest as-is
    return label[:1].upper() + label[1:]


def count_syllables(word: str) -> int:
    word = word.lower().strip()
    if not word:
        return 1
    vowels = "aeiouy"
    count, prev_v = 0, False
    for ch in word:
        iv = ch in vowels
        if iv and not prev_v:
            count += 1
        prev_v = iv
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def load_fonts(scale: float) -> dict:
    def best_pt(pt: int, bold: bool = False) -> ImageFont.ImageFont:
        try:
            return _brand_font_pt(pt, bold=bold, brand="poppins")
        except Exception:
            return ImageFont.load_default()

    return {
        "title":    best_pt(22, bold=True),
        "word":     best_pt(28, bold=True),
        "sub":      best_pt(10, bold=False),
        "footer":   best_pt(9,  bold=False),
        "copyright":best_pt(7,  bold=False),
        "banner_word": best_pt(18, bold=True),
    }


def _font_cover(pt: int, *, bold: bool = False) -> ImageFont.ImageFont:
    try:
        return _brand_font_pt(pt, bold=bold, brand="poppins")
    except Exception:
        return ImageFont.load_default()


def _build_cover_page(*, book_title: str, pack_code: str, page_count: int, hero_image_path: str | None = None, book_cover_path: str | None = None, bw: bool = False, header_left_icon_img: Image.Image | None = None) -> Image.Image:
    # Portrait cover
    COV_W_PT, COV_H_PT = letter
    COV_W = int(COV_W_PT * DPI / 72)
    COV_H = int(COV_H_PT * DPI / 72)
    page = Image.new("RGB", (COV_W, COV_H), "white")
    apply_small_wins_frame(
        page,
        product_title="Vocabulary Word Wall",
        subtitle=f"{book_title} • {page_count}+ pages",
        pack_code=pack_code,
        page_num=1,
        total_pages=1,
        level=None,
        draw_footer=True,
        draw_subtitle=True,
        header_left_icon=header_left_icon_img,
        header_height_px=int(0.92 * DPI),
        accent_margin_px=int(0.12 * DPI),
        footer_y_offset_px=int(0.08 * DPI),
    )
    d = ImageDraw.Draw(page)
    s = DPI / 72
    left = int(0.45 * DPI)
    top = int(1.60 * DPI)
    right = COV_W - int(0.45 * DPI)
    # Artwork box
    box_h = int(2.6 * DPI)
    d.rounded_rectangle([left, top, right, top + box_h], radius=int(14 * s), outline=hex_to_rgb(SWS_NAVY), width=int(3 * s), fill=(255, 255, 255))
    # Try to place a hero/cover image, if present
    art = None
    try:
        if book_cover_path and Path(book_cover_path).exists():
            art = Image.open(book_cover_path).convert("RGBA")
        elif hero_image_path and Path(hero_image_path).exists():
            art = Image.open(hero_image_path).convert("RGBA")
    except Exception:
        art = None
    if art is not None:
        if bw:
            art = art.convert("L").convert("RGBA")
        pad = int(0.18 * DPI)
        max_w = max(1, (right - left) - 2 * pad)
        max_h = max(1, box_h - 2 * pad)
        art.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        ax = left + (max_w - art.width) // 2
        ay = top + (box_h - art.height) // 2
        page.paste(art, (ax, ay), art)

    y = top + box_h + int(0.24 * DPI)
    heading = "What's included:"
    hf = _font_cover(14, bold=True)
    d.text((left, y), heading, fill=hex_to_rgb(SWS_NAVY), font=hf)
    y += d.textbbox((0, 0), heading, font=hf)[3] - d.textbbox((0, 0), heading, font=hf)[1] + int(0.10 * DPI)

    bullets = [
        "A–Z word wall cards",
        "Word wall banner (classroom strip)",
        "Colour and B&W versions",
    ]
    bf = _font_cover(11, bold=False)
    for b in bullets:
        line = f"• {b}"
        d.text((left + int(0.10 * DPI), y), line, fill=(30, 58, 95), font=bf)
        y += int(0.20 * DPI)
    return page


def _load_icon(slug: str, raw_stem: str) -> Image.Image | None:
    exts = ["png", "jpg", "jpeg", "webp"]
    stems = list(dict.fromkeys([raw_stem, raw_stem.lower(), re.sub(r"[\s-]+", "_", raw_stem.strip().lower())]))
    for folder in ["activity_images", "icons", "real_images", "characters"]:
        for stem in stems:
            for ex in exts:
                p = REPO_ROOT / "assets" / "themes" / slug / folder / f"{stem}.{ex}"
                if p.exists():
                    try:
                        return Image.open(p).convert("RGBA")
                    except Exception:
                        pass
    themes_dir = REPO_ROOT / "assets" / "themes"
    if os.environ.get("SWS_ALLOW_CROSS_THEME_ICONS") == "1" and themes_dir.exists():
        for other in themes_dir.iterdir():
            if not other.is_dir() or other.name == slug:
                continue
            for folder in ["activity_images", "icons", "real_images", "characters"]:
                for stem in stems:
                    for ex in exts:
                        p = other / folder / f"{stem}.{ex}"
                        if p.exists():
                            try:
                                return Image.open(p).convert("RGBA")
                            except Exception:
                                pass
    return None


def _load_vocab(slug: str) -> list[tuple[str, str]]:
    """Returns list of (raw_stem, display_label) tuples."""
    vp = REPO_ROOT / "assets" / "themes" / slug / "book_vocab.json"
    if vp.exists():
        try:
            import json
            data = json.loads(vp.read_text())
            cands: list[str] = []
            for key in ("vocab_words", "all_words", "activity_images", "fringe_11", "fringe_12"):
                v = data.get(key)
                if isinstance(v, list):
                    cands.extend([str(w) for w in v if isinstance(w, str)])
            wsw = data.get("word_search_words")
            if isinstance(wsw, list):
                for it in wsw:
                    if isinstance(it, dict) and isinstance(it.get("word"), str):
                        cands.append(it["word"]) 
            seen: set[str] = set()
            out: list[tuple[str, str]] = []
            for w in cands:
                raw = str(w).strip()
                if not raw:
                    continue
                key = raw.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append((raw, clean_label(raw)))
            if out:
                return out
        except Exception:
            pass

    items, seen = [], set()
    for folder in ["activity_images", "icons", "real_images", "characters"]:
        img_dir = REPO_ROOT / "assets" / "themes" / slug / folder
        if not img_dir.exists():
            continue
        for pat in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            for f in sorted(img_dir.glob(pat)):
                stem = re.sub(r'_\d+$', '', f.stem.strip())
                key = stem.lower()
                if key in seen or len(stem) < 2:
                    continue
                items.append((stem, clean_label(stem)))
                seen.add(key)
        if items:
            return items
    return []


# ── Single vocabulary card ────────────────────────────────────────────────────

def _trim_card_icon(icon: Image.Image) -> Image.Image:
    image = icon.convert("RGBA")
    edge = max(2, int(image.width * 0.02))
    image = image.crop((edge, edge, image.width - edge, image.height - edge))
    pixels = []
    source = image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()
    for red, green, blue, alpha in source:
        neutral = max(red, green, blue) - min(red, green, blue) < 12 and (red + green + blue) / 3 > 150
        pixels.append((red, green, blue, 0 if neutral else alpha))
    image.putdata(pixels)
    content_box = image.getchannel("A").getbbox()
    return image.crop(content_box) if content_box else image


def _draw_vocab_card(page, draw, fonts, scale,
                     x, y, w, h,
                     raw_stem: str, display_label: str,
                     slug: str, color: bool,
                     show_image: bool = True,
                     show_syllables: bool = True,
                     label_style: str = "plain"):
    """Draw one vocabulary card at position (x, y) with size (w, h)."""
    teal  = hex_to_rgb(SWS_TEAL)
    navy  = hex_to_rgb(SWS_NAVY)
    border_r = int(10 * scale)

    # Card background + border
    draw.rounded_rectangle(
        [x, y, x + w, y + h],
        radius=border_r,
        fill=(255, 255, 255),
        outline=navy, width=int(3 * scale)
    )

    # Floating teal header pill with padding
    approx_header_h = int(h * 0.14)
    pill_pad_x = int(12 * scale)
    pill_pad_y = int(8 * scale)
    pill_h = max(approx_header_h, int(fonts["title"].size * 1.8))
    pill_left   = x + pill_pad_x
    pill_right  = x + w - pill_pad_x
    pill_top    = y + pill_pad_y
    pill_bottom = pill_top + pill_h
    if label_style == "snap":
        draw.rounded_rectangle(
            [pill_left, pill_top, pill_right, pill_bottom],
            radius=border_r - int(2 * scale),
            fill=(232, 248, 248) if color else (255, 255, 255),
            outline=teal if color else navy,
            width=max(1, int(1.5 * scale)),
        )
    else:
        draw.line((pill_left, pill_bottom, pill_right, pill_bottom), fill=teal if color else navy, width=max(1, int(2 * scale)))

    # Word label in header (centered, sentence case)
    hb = draw.textbbox((0, 0), display_label, font=fonts["title"])
    hw = hb[2] - hb[0]; hth = hb[3] - hb[1]
    draw.text((x + (w - hw) // 2,
               pill_top + (pill_h - hth) // 2),
              display_label, fill=navy if color else (0, 0, 0), font=fonts["title"])

    content_top = pill_bottom + int(10 * scale)
    syllables   = count_syllables(display_label)

    # Syllable dot row at bottom (if enabled)
    syl_area_h = int(h * 0.16) if show_syllables else 0
    syl_top    = y + h - syl_area_h - int(8 * scale)

    # Image zone
    img_bottom = syl_top - int(8 * scale)
    img_zone_h = img_bottom - content_top

    if show_image:
        icon = _load_icon(slug, raw_stem)
        if icon:
            if not color:
                icon = icon.convert("L").convert("RGBA")
            ic = _trim_card_icon(icon)
            # Maximize icon within available zone
            pad = int(12 * scale)
            max_w = w - pad * 2
            max_h = img_zone_h - pad * 2
            icon_scale = min(max_w / max(1, ic.width), max_h / max(1, ic.height)) * 0.78
            ic = ic.resize((max(1, int(ic.width * icon_scale)), max(1, int(ic.height * icon_scale))), Image.Resampling.LANCZOS)
            ix = x + (w - ic.width)  // 2
            iy = content_top + (img_zone_h - ic.height) // 2
            page.paste(ic, (ix, iy), ic)
        else:
            # Placeholder
            ph = int(20 * scale)
            draw.rounded_rectangle(
                [x + ph, content_top + ph, x + w - ph, img_bottom - ph],
                radius=int(6 * scale),
                outline=(200, 200, 200), width=int(2 * scale)
            )

    # Divider line (kept subtle to avoid visual clutter)
    div_y = img_bottom
    draw.line([(x + int(16 * scale), div_y), (x + w - int(16 * scale), div_y)],
              fill=(220, 220, 220), width=int(1 * scale))

    # Syllable dots
    if show_syllables:
        dot_r   = int(7 * scale)
        dot_gap = int(8 * scale)
        total_dot_w = syllables * (dot_r * 2 + dot_gap) - dot_gap
        dot_sx  = x + (w - total_dot_w) // 2
        dot_cy  = syl_top + syl_area_h // 2

        for i in range(syllables):
            dx = dot_sx + i * (dot_r * 2 + dot_gap)
            draw.ellipse(
                [dx, dot_cy - dot_r, dx + dot_r * 2, dot_cy + dot_r],
                fill=teal if color else (80, 80, 80)
            )

        # Syllable count label
        sl_text = f"{syllables} syllable{'s' if syllables != 1 else ''}"
        slb = draw.textbbox((0, 0), sl_text, font=fonts["sub"])
        draw.text((x + (w - (slb[2] - slb[0])) // 2,
                   dot_cy + dot_r + int(4 * scale)),
                  sl_text, fill=(120, 120, 120), font=fonts["sub"])


# ── Page builders ─────────────────────────────────────────────────────────────

def _fit_snap_label(draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int, start_pt: int = 17, min_pt: int = 10):
    words = str(text or "").split()
    for pt in range(start_pt, min_pt - 1, -1):
        font = _brand_font_pt(pt, bold=True, brand="poppins")
        lines = [str(text or "")]
        if draw.textbbox((0, 0), lines[0], font=font)[2] > max_width and len(words) > 1:
            best = min(range(1, len(words)), key=lambda index: abs(len(" ".join(words[:index])) - len(" ".join(words[index:]))))
            lines = [" ".join(words[:best]), " ".join(words[best:])]
        box = draw.multiline_textbbox((0, 0), "\n".join(lines), font=font, spacing=4, align="center")
        if box[2] - box[0] <= max_width and box[3] - box[1] <= max_height:
            return font, lines, box
    font = _brand_font_pt(min_pt, bold=True, brand="poppins")
    lines = [str(text or "")]
    box = draw.multiline_textbbox((0, 0), lines[0], font=font, spacing=4, align="center")
    return font, lines, box


def _draw_snap_card(page: Image.Image, draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], slug: str, raw_stem: str, label: str, color: bool, variant: str) -> bool:
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    scale = DPI / 72
    navy = hex_to_rgb(SWS_NAVY) if color else (0, 0, 0)
    teal = hex_to_rgb(SWS_TEAL) if color else (255, 255, 255)
    pale = hex_to_rgb("#E8F8F8") if color else (255, 255, 255)
    radius = int(10 * scale)
    draw.rounded_rectangle(box, radius=radius, fill=(255, 255, 255), outline=navy, width=max(3, int(2 * scale)))
    inset = int(0.07 * DPI)
    icon = _load_icon(slug, raw_stem) if variant != "text_only" else None
    if variant == "symbol_text":
        pill_h = int(height * 0.17)
        pill = (x1 + inset, y1 + inset, x2 - inset, y1 + inset + pill_h)
        draw.rounded_rectangle(pill, radius=int(7 * scale), fill=pale, outline=hex_to_rgb(SWS_TEAL) if color else navy, width=max(2, int(1.2 * scale)))
        font, lines, bounds = _fit_snap_label(draw, label, pill[2] - pill[0] - 2 * inset, pill[3] - pill[1] - int(0.03 * DPI))
        text = "\n".join(lines)
        tw, th = bounds[2] - bounds[0], bounds[3] - bounds[1]
        tx = pill[0] + (pill[2] - pill[0] - tw) // 2 - bounds[0]
        ty = pill[1] + (pill[3] - pill[1] - th) // 2 - bounds[1]
        draw.multiline_text((tx, ty), text, font=font, fill=navy, spacing=4, align="center")
        icon_box = (x1 + inset, pill[3] + int(0.04 * DPI), x2 - inset, y2 - inset)
    elif variant == "symbol_only":
        icon_box = (x1 + inset, y1 + inset, x2 - inset, y2 - inset)
    else:
        text_box = (x1 + inset, y1 + inset, x2 - inset, y2 - inset)
        draw.rounded_rectangle(text_box, radius=int(8 * scale), fill=pale)
        font, lines, bounds = _fit_snap_label(draw, label, width - 4 * inset, height - 4 * inset, 25, 14)
        text = "\n".join(lines)
        tw, th = bounds[2] - bounds[0], bounds[3] - bounds[1]
        tx = x1 + (width - tw) // 2 - bounds[0]
        ty = y1 + (height - th) // 2 - bounds[1]
        draw.multiline_text((tx, ty), text, font=font, fill=navy, spacing=8, align="center")
        return True
    if icon is None:
        placeholder_font = _brand_font_pt(9, bold=True, brand="poppins")
        placeholder = "IMAGE TO REVIEW"
        bounds = draw.textbbox((0, 0), placeholder, font=placeholder_font)
        draw.text((x1 + (width - (bounds[2] - bounds[0])) // 2, y1 + height // 2), placeholder, font=placeholder_font, fill=(170, 80, 80))
        return False
    if not color:
        icon = icon.convert("L").convert("RGBA")
    icon = _trim_card_icon(icon)
    max_w = max(1, icon_box[2] - icon_box[0])
    max_h = max(1, icon_box[3] - icon_box[1])
    if icon.width > 0 and icon.height > 0:
        ratio = min(max_w / icon.width, max_h / icon.height) * 0.78
        icon = icon.resize((max(1, int(icon.width * ratio)), max(1, int(icon.height * ratio))), Image.Resampling.LANCZOS)
    page.paste(icon, (icon_box[0] + (max_w - icon.width) // 2, icon_box[1] + (max_h - icon.height) // 2), icon)
    return True


def _make_snap_page(slug: str, book_title: str, pack_code: str, cards: list[tuple[str, str]], page_num: int, total_pages: int, color: bool, variant: str, header_icon: Image.Image | None = None) -> tuple[Image.Image, list[str]]:
    page = Image.new("RGB", (SNAP_W, SNAP_H), PAGE_CREAM)
    draw = ImageDraw.Draw(page)
    apply_small_wins_frame(
        page,
        product_title=book_title,
        subtitle={"symbol_text": "Vocabulary & Snap Cards — Symbol + Text", "symbol_only": "Vocabulary & Snap Cards — Symbol Only", "text_only": "Vocabulary & Snap Cards — Text Only"}[variant],
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        draw_footer=True,
        header_left_icon=header_icon,
        header_height_px=int(0.92 * DPI),
        accent_margin_px=int(0.12 * DPI),
        footer_y_offset_px=int(0.08 * DPI),
    )
    margin_x = int(0.32 * DPI)
    gap_x = int(0.11 * DPI)
    gap_y = int(0.11 * DPI)
    content_top = int(1.48 * DPI)
    content_bottom = SNAP_H - int(0.82 * DPI)
    available_w = SNAP_W - 2 * margin_x
    card_w = (available_w - 2 * gap_x) // 3
    card_h = int(card_w * SNAP_CARD_RATIO)
    available_h = content_bottom - content_top
    if 2 * card_h + gap_y > available_h:
        card_h = (available_h - gap_y) // 2
        card_w = int(card_h / SNAP_CARD_RATIO)
    grid_w = 3 * card_w + 2 * gap_x
    start_x = (SNAP_W - grid_w) // 2
    start_y = content_top + max(0, (available_h - (2 * card_h + gap_y)) // 2)
    missing = []
    for index, (raw_stem, label) in enumerate(cards[:SNAP_CARDS_PER_PAGE]):
        row, col = divmod(index, 3)
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        if not _draw_snap_card(page, draw, (x, y, x + card_w, y + card_h), slug, raw_stem, label, color, variant):
            missing.append(raw_stem)
    return page, missing


def _footer_strip(draw, fonts, scale, book_title, pack_code, page_num, total_pages):
    """Thin footer at bottom of landscape page."""
    fy  = PAGE_H - int(28 * scale)
    lc  = hex_to_rgb(SWS_TEAL)
    draw.rectangle([0, fy, PAGE_W, PAGE_H], fill=hex_to_rgb(FOOTER_GREY))
    draw.rectangle([0, fy, PAGE_W, fy + int(2 * scale)], fill=lc)

    cl1 = f"{book_title}  ·  Vocabulary Word Wall  ·  {pack_code}"
    cl2 = f"© 2026 Small Wins Studio · PCS® symbols used with active PCS Maker Personal License.  ·  Page {page_num} of {total_pages}"
    for text, dx, col in [
        (cl1, 0,      (80, 80, 80)),
        (cl2, PAGE_W, (150, 150, 150)),
    ]:
        bb = draw.textbbox((0, 0), text, font=fonts["footer"])
        tw = bb[2] - bb[0]
        fx = int(20 * scale) if dx == 0 else PAGE_W - tw - int(20 * scale)
        draw.text((fx, fy + (int(28 * scale) - (bb[3] - bb[1])) // 2),
                  text, fill=col, font=fonts["footer"])


def _make_card_page(slug, book_title, pack_code,
                    vocab_chunk: list[tuple[str, str]],
                    page_num: int, total_pages: int,
                    color: bool, cards_per_row: int = 2,
                    header_left_icon_img: Image.Image | None = None) -> Image.Image:
    """
    One landscape page with up to 4 vocabulary cards (2×2 grid).
    """
    scale = DPI / 72
    fonts = load_fonts(scale)

    page = Image.new("RGB", (PAGE_W, PAGE_H), PAGE_CREAM)
    draw = ImageDraw.Draw(page)

    # Footer/border will be added by shared frame helper at the end

    margin  = int(24 * scale)
    gap     = int(16 * scale)
    COLS    = cards_per_row
    ROWS    = 2

    # Respect the universal frame header/footer safe area
    content_top    = int(1.70 * DPI)
    content_bottom = PAGE_H - int(1.10 * DPI)
    inner_w  = PAGE_W - 2 * margin
    inner_h  = max(0, (content_bottom - content_top) - 2 * margin)
    card_w   = (inner_w - gap * (COLS - 1)) // COLS
    card_h   = (inner_h - gap * (ROWS - 1)) // ROWS

    for i, (raw_stem, display_label) in enumerate(vocab_chunk[:COLS * ROWS]):
        row = i // COLS
        col = i % COLS
        cx  = margin + col * (card_w + gap)
        cy  = content_top + margin + row * (card_h + gap)
        _draw_vocab_card(page, draw, fonts, scale,
                         cx, cy, card_w, card_h,
                         raw_stem, display_label,
                         slug, color,
                         label_style="plain")

    try:
        apply_small_wins_frame(
            page,
            product_title=book_title,
            subtitle="Vocabulary Word Wall",
            pack_code=pack_code,
            page_num=page_num,
            total_pages=total_pages,
            level=None,
            draw_accent_strip=True,
            draw_header=True,
            draw_subtitle=True,
            draw_footer=True,
            header_left_icon=header_left_icon_img,
            header_height_px=int(0.92 * DPI),
            accent_margin_px=int(0.12 * DPI),
            footer_y_offset_px=int(0.08 * DPI),
        )
    except Exception:
        pass

    return page


def _make_banner_page(slug, book_title, pack_code,
                      vocab_chunk: list[tuple[str, str]],
                      page_num: int, total_pages: int,
                      color: bool,
                      header_left_icon_img: Image.Image | None = None,
                      subtitle_text: str = "Vocabulary Word Wall — Banner",
                      label_style: str = "plain") -> Image.Image:
    """
    Smaller banner-style cards — 4 per row, 2 rows = 8 per page.
    Good for a classroom word wall strip.
    """
    scale = DPI / 72
    fonts = load_fonts(scale)

    page = Image.new("RGB", (PAGE_W, PAGE_H), PAGE_CREAM)
    draw = ImageDraw.Draw(page)

    # Footer/border will be added by shared frame helper at the end

    margin   = int(20 * scale)
    gap      = int(10 * scale)
    COLS     = 4
    ROWS     = 2

    # Respect the universal frame header/footer safe area
    content_top    = int(1.70 * DPI)
    content_bottom = PAGE_H - int(1.10 * DPI)
    inner_w  = PAGE_W - 2 * margin
    inner_h  = max(0, (content_bottom - content_top) - 2 * margin)
    card_w   = (inner_w - gap * (COLS - 1)) // COLS
    card_h   = (inner_h - gap * (ROWS - 1)) // ROWS

    for i, (raw_stem, display_label) in enumerate(vocab_chunk[:COLS * ROWS]):
        row = i // COLS
        col = i % COLS
        cx  = margin + col * (card_w + gap)
        cy  = content_top + margin + row * (card_h + gap)
        _draw_vocab_card(page, draw, fonts, scale,
                         cx, cy, card_w, card_h,
                         raw_stem, display_label,
                         slug, color,
                         show_syllables=False,
                         label_style=label_style)

    try:
        apply_small_wins_frame(
            page,
            product_title=book_title,
            subtitle=subtitle_text,
            pack_code=pack_code,
            page_num=page_num,
            total_pages=total_pages,
            level=None,
            draw_accent_strip=True,
            draw_header=True,
            draw_subtitle=True,
            draw_footer=True,
            header_left_icon=header_left_icon_img,
            header_height_px=int(0.92 * DPI),
            accent_margin_px=int(0.12 * DPI),
            footer_y_offset_px=int(0.08 * DPI),
        )
    except Exception:
        pass

    return page


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_word_wall(slug: str, book_title: str,
                        pack_code: str = "STEL-VWW",
                        *,
                        snap_duplicates: int = 2,
                        card_duplicates: int = 3,
                        include_teacher_cover: bool = False) -> bool:
    """
    Generate Vocabulary Word Wall pack.

    OUTPUT:
      {pack_code}_WordWall_COLOR.pdf  — 4 cards/page, full colour, with syllable dots
      {pack_code}_WordWall_BW.pdf     — same, black & white
      {pack_code}_WordWall_Banner_COLOR.pdf — 8 cards/page, classroom strip format
      {pack_code}_WordSnap_SymbolText_COLOR/BW.pdf — paired Snap and identical-memory deck
      {pack_code}_WordSnap_SymbolOnly_COLOR/BW.pdf — receptive identification deck
      {pack_code}_WordSnap_TextOnly_COLOR/BW.pdf — sight-word and symbol-to-word deck
      {pack_code}_WordSnap_ExtraCopy_COLOR/BW.pdf — optional third-copy pages

    Args:
        slug:           Book slug e.g. 'stellaluna'
        book_title:     Display name e.g. 'Stellaluna'
        pack_code:      TPT product code e.g. 'STEL-VWW'
        card_duplicates: Number of copies of each word-wall card to generate
                        (default 3, so a whole class can each hold a card).
    """
    print(f"\n{'='*70}")
    print(f"  VOCAB WORD WALL: {pack_code}  ({book_title})")
    print(f"{'='*70}\n")

    vocab = _load_vocab(slug)
    if not vocab:
        print(f"  ERROR: No vocabulary found for slug '{slug}'")
        return False
    excluded_vocab = [label for raw_stem, label in vocab if _load_icon(slug, raw_stem) is None]
    vocab = [(raw_stem, label) for raw_stem, label in vocab if _load_icon(slug, raw_stem) is not None]
    if len(vocab) < 4:
        print(f"  ERROR: Only {len(vocab)} vocabulary items have approved local images")
        return False

    print(f"  Words ({len(vocab)}): {', '.join(lbl for _, lbl in vocab)}\n")

    output_dir = REPO_ROOT / "assets" / "themes" / slug / "OUTPUT"
    output_dir.mkdir(parents=True, exist_ok=True)

    CARDS_PER_PAGE = 4
    import math
    # Build the word-wall card deck with N copies of each word so multiple
    # students in a class can each hold a card simultaneously.
    card_duplicates = max(1, int(card_duplicates or 1))
    vocab_cards = [(raw_stem, display_label)
                   for raw_stem, display_label in vocab
                   for _ in range(card_duplicates)]
    n_card_pages   = math.ceil(len(vocab_cards) / CARDS_PER_PAGE)
    BANNER_PER_PAGE= 8
    n_banner_pages = math.ceil(len(vocab) / BANNER_PER_PAGE)

    # Prepare Snap deck using paired cards plus differentiated single-copy decks
    snap_duplicates = max(2, min(3, int(snap_duplicates or 2)))
    vocab_snap = [(raw_stem, display_label) for raw_stem, display_label in vocab for _ in range(snap_duplicates)]
    snap_decks = {
        "symbol_text": vocab_snap,
        "symbol_only": list(vocab),
        "text_only": list(vocab),
        "extra_copy": list(vocab),
    }

    def build_card_pages(color: bool) -> list[Image.Image]:
        pages = []
        for i in range(n_card_pages):
            chunk = vocab_cards[i * CARDS_PER_PAGE:(i + 1) * CARDS_PER_PAGE]
            pages.append(_make_card_page(
                slug, book_title, pack_code, chunk,
                i + 1, n_card_pages, color,
                header_left_icon_img=header_icon_img
            ))
        return pages

    def build_banner_pages(color: bool) -> list[Image.Image]:
        pages = []
        for i in range(n_banner_pages):
            chunk = vocab[i * BANNER_PER_PAGE:(i + 1) * BANNER_PER_PAGE]
            pages.append(_make_banner_page(
                slug, book_title, pack_code, chunk,
                i + 1, n_banner_pages, color,
                header_left_icon_img=header_icon_img,
                subtitle_text="Vocabulary Word Wall — Banner"
            ))
        return pages

    def build_snap_pages(color: bool, deck_key: str) -> tuple[list[Image.Image], list[str]]:
        cards = snap_decks[deck_key]
        variant = "symbol_text" if deck_key == "extra_copy" else deck_key
        total = math.ceil(len(cards) / SNAP_CARDS_PER_PAGE)
        pages = []
        missing = []
        for i in range(total):
            chunk = cards[i * SNAP_CARDS_PER_PAGE:(i + 1) * SNAP_CARDS_PER_PAGE]
            page, page_missing = _make_snap_page(slug, book_title, pack_code, chunk, i + 1, total, color, variant, header_icon_img)
            pages.append(page)
            missing.extend(page_missing)
        return pages, list(dict.fromkeys(missing))

    def to_pdf_mixed(pages, path, preview=False):
        c = rl_canvas.Canvas(str(path), pagesize=letter)
        for pg in pages:
            pw_px, ph_px = pg.size
            pw_pt = pw_px * 72.0 / DPI
            ph_pt = ph_px * 72.0 / DPI
            try:
                c.setPageSize((pw_pt, ph_pt))
            except Exception:
                pass
            buf = io.BytesIO()
            pg.save(buf, format="PNG", dpi=(DPI, DPI))
            buf.seek(0)
            c.drawImage(ImageReader(buf), 0, 0, width=pw_pt, height=ph_pt)
            if preview:
                c.saveState()
                c.setFont("Helvetica-Bold", 90)
                try:
                    c.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.25)
                except Exception:
                    c.setFillColorRGB(0.7, 0.7, 0.7)
                c.translate(pw_pt / 2, ph_pt / 2)
                c.rotate(42)
                c.drawCentredString(0, 0, "PREVIEW")
                c.restoreState()
            c.showPage()
        c.save()

    ls = landscape(letter)

    color_path  = output_dir / f"{pack_code}_WordWall_COLOR.pdf"
    bw_path     = output_dir / f"{pack_code}_WordWall_BW.pdf"
    banner_path = output_dir / f"{pack_code}_WordWall_Banner_COLOR.pdf"
    snap_paths = {
        ("symbol_text", True): output_dir / f"{pack_code}_WordSnap_SymbolText_COLOR.pdf",
        ("symbol_text", False): output_dir / f"{pack_code}_WordSnap_SymbolText_BW.pdf",
        ("symbol_only", True): output_dir / f"{pack_code}_WordSnap_SymbolOnly_COLOR.pdf",
        ("symbol_only", False): output_dir / f"{pack_code}_WordSnap_SymbolOnly_BW.pdf",
        ("text_only", True): output_dir / f"{pack_code}_WordSnap_TextOnly_COLOR.pdf",
        ("text_only", False): output_dir / f"{pack_code}_WordSnap_TextOnly_BW.pdf",
        ("extra_copy", True): output_dir / f"{pack_code}_WordSnap_ExtraCopy_COLOR.pdf",
        ("extra_copy", False): output_dir / f"{pack_code}_WordSnap_ExtraCopy_BW.pdf",
    }
    legacy_snap_path = output_dir / f"{pack_code}_WordSnap_COLOR.pdf"
    snap_preview_path = output_dir / f"{pack_code}_WordSnap_PREVIEW.pdf"

    print(f"  {n_card_pages} card pages ({len(vocab_cards)} cards, {card_duplicates}× each)  ·  {n_banner_pages} banner pages\n")

    # Resolve hero/book cover for portrait teacher cover page
    cov = None
    try:
        tdir = REPO_ROOT / "assets" / "themes" / slug
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
        cover_names = [
            "book_cover", "cover", "front_cover", "bookfront", "book", "cover_reference"
        ]
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
        header_icon_img = None
        try:
            if hero_path_str:
                _im = Image.open(hero_path_str)
                header_icon_img = _im.convert("RGBA") if _im.mode != "RGBA" else _im
        except Exception:
            header_icon_img = None
        cov = generate_teacher_cover_page(
            theme_name=book_title,
            pack_code=pack_code,
            product_name="Vocabulary Word Wall",
            page_count=(n_card_pages + n_banner_pages),
            level_count=None,
            hero_image=header_icon_img,
            hero_image_path=hero_path_str,
            book_cover_path=book_cover_path_str,
            top_tips=[
                "Display the A-Z cards on a classroom wall for daily reference.",
                "Use the word wall banner as a visual prompt during book reading.",
                "Match cards to book vocabulary for active recall.",
            ],
        )
    except Exception:
        cov = None
        header_icon_img = None

    print("  Writing COLOR PDF ...")
    pages_color = build_card_pages(color=True)
    if include_teacher_cover and cov is not None:
        pages_color = [cov] + pages_color
    to_pdf_mixed(pages_color, color_path)
    print(f"  ✓  {color_path}")
    # Save QA_OUT previews for external review
    try:
        qa_dir = output_dir / "QA_OUT"
        qa_dir.mkdir(parents=True, exist_ok=True)
        if pages_color:
            pages_color[0].save(qa_dir / f"{pack_code}_WordWall_cover.png", format="PNG", dpi=(DPI, DPI))
            idx = 1 if len(pages_color) > 1 else 0
            pages_color[idx].save(qa_dir / f"{pack_code}_WordWall_page1.png", format="PNG", dpi=(DPI, DPI))
    except Exception:
        pass

    print("  Writing B&W PDF ...")
    pages_bw = build_card_pages(color=False)
    if include_teacher_cover and cov is not None:
        try:
            cov_bw = cov.convert("L").convert("RGB")
        except Exception:
            cov_bw = cov
        pages_bw = [cov_bw] + pages_bw
    to_pdf_mixed(pages_bw, bw_path)
    print(f"  ✓  {bw_path}")

    print("  Writing Banner COLOR PDF ...")
    pages_banner = build_banner_pages(color=True)
    if include_teacher_cover and cov is not None:
        pages_banner = [cov] + pages_banner
    to_pdf_mixed(pages_banner, banner_path)
    print(f"  ✓  {banner_path}")

    # Differentiated Snap Cards
    snap_manifest = {
        "schema_version": 1,
        "status": "pilot_review",
        "product_name": "Vocabulary & Snap Cards",
        "theme": slug,
        "reading_rope": ["Vocabulary", "Sight Recognition"],
        "teacher_review_required": True,
        "pack_code": pack_code,
        "source": str(REPO_ROOT / "assets" / "themes" / slug / "book_vocab.json"),
        "orientation": "portrait",
        "cards_per_page": SNAP_CARDS_PER_PAGE,
        "card_ratio": SNAP_CARD_RATIO,
        "core_duplicates": snap_duplicates,
        "variants": {},
        "missing_icons": [],
        "excluded_vocab": excluded_vocab,
    }
    snap_thumbnails = []
    for deck_key in ("symbol_text", "symbol_only", "text_only", "extra_copy"):
        for color in (True, False):
            pages_snap, missing_icons = build_snap_pages(color, deck_key)
            output_path = snap_paths[(deck_key, color)]
            to_pdf_mixed(pages_snap, output_path)
            snap_manifest["variants"][f"{deck_key}_{'color' if color else 'bw'}"] = {
                "path": str(output_path),
                "pages": len(pages_snap),
                "cards": len(snap_decks[deck_key]),
            }
            snap_manifest["missing_icons"].extend(missing_icons)
            print(f"  ✓  {output_path}")
            if deck_key == "symbol_text" and color:
                to_pdf_mixed(pages_snap, legacy_snap_path)
                to_pdf_mixed(pages_snap[:min(3, len(pages_snap))], snap_preview_path, preview=True)
                thumb_dir = output_dir / "thumbnails"
                thumb_dir.mkdir(parents=True, exist_ok=True)
                snap_thumbnails = []
                for index, page in enumerate(pages_snap[:2], start=1):
                    thumb = page.copy()
                    thumb.thumbnail((500, 647), Image.Resampling.LANCZOS)
                    thumb_path = thumb_dir / f"{pack_code}_WordSnap_thumb{index}.png"
                    thumb.save(thumb_path, "PNG")
                    snap_thumbnails.append(str(thumb_path))
    snap_manifest["files"] = {"preview_pdf": str(snap_preview_path), "thumbnails": snap_thumbnails}
    snap_manifest["missing_icons"] = sorted(set(snap_manifest["missing_icons"]))
    manifest_path = output_dir / f"{pack_code}_WordSnap_BuildResult.json"
    manifest_path.write_text(json.dumps(snap_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*70}")
    print(f"  WORD WALL COMPLETE")
    print(f"{'='*70}\n")
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate Vocabulary Word Wall (+ Banner + Snap Cards)")
    parser.add_argument("slug", help="Theme/book slug, e.g., llama_llama_red_pajama")
    parser.add_argument("book_title", help="Display book title")
    parser.add_argument("pack_code", nargs="?", default="VWW", help="Pack code, e.g., STEL-VWW")
    parser.add_argument("--snap-dupes", type=int, default=2, choices=[2, 3], help="Copies per word in the main symbol+text Snap deck; the optional extra-copy deck is always separate")
    args = parser.parse_args()

    ok = generate_word_wall(args.slug, args.book_title, args.pack_code, snap_duplicates=args.snap_dupes)
    import sys as _sys
    _sys.exit(0 if ok else 1)
