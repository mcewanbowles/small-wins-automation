#!/usr/bin/env python3
"""Matching Cover Generator — Small Wins Design System.

Generates per-level cover pages using the shared Small Wins frame
(same layout as Bingo covers): artwork box with bear icon, tagline,
What's Included bullets, Quick Start bullets, Comic Sans throughout.

Output:
  production/final_products/brown_bear/matching/cover_level{N}_{mode}_FINAL.pdf
"""

from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# Ensure repo root is importable.
_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from utils.sws_design import (
    DPI,
    LEVEL_COLORS as SWS_LEVEL_COLORS,
    apply_small_wins_frame,
    hex_to_rgb,
)

# ---------- constants ----------
THEME = "brown_bear"
PRODUCT = "matching"
PAGE_WIDTH, PAGE_HEIGHT = letter

NAVY_BLUE = "#1E3A5F"
STEEL_BLUE = "#5B7AA0"

_FONT_COMIC = "C:/Windows/Fonts/comic.ttf"
_FONT_COMIC_BOLD = "C:/Windows/Fonts/comicbd.ttf"

OUTPUT_DIR = _REPO_ROOT / "production" / "final_products" / THEME / PRODUCT


def _load_matching_levels() -> dict[int, dict]:
    theme_path = _REPO_ROOT / "themes" / f"{THEME}.json"
    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)
    levels = theme["matching"]["levels"]
    out: dict[int, dict] = {}
    for i in range(1, 6):
        key = f"L{i}"
        out[i] = {
            "name": levels[key]["name"],
            "color": levels[key]["colour"],
        }
    return out


LEVELS = _load_matching_levels()


def _icon_path() -> Path:
    icons_colored = _REPO_ROOT / "assets" / "themes" / THEME / "icons_colored"
    legacy = _REPO_ROOT / "assets" / "themes" / THEME / "icons"
    d = icons_colored if icons_colored.exists() else legacy
    p = d / "Brown bear.png"
    if not p.exists():
        p = d / "Brown Bear.png"
    return p


def _load_fonts() -> dict:
    s = DPI / 72
    try:
        return {
            "heading": ImageFont.truetype(_FONT_COMIC_BOLD, int(14 * s)),
            "bullet": ImageFont.truetype(_FONT_COMIC, int(11 * s)),
            "tagline_path": _FONT_COMIC,
        }
    except Exception:
        f = ImageFont.load_default()
        return {"heading": f, "bullet": f, "tagline_path": None}


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def _fit_font(draw, text, *, font_path, max_px, min_px, max_w, max_h):
    for px in range(max_px, min_px - 1, -1):
        f = ImageFont.truetype(font_path, px)
        tw, th = _text_size(draw, text, f)
        if tw <= max_w and th <= max_h:
            return f
    return ImageFont.truetype(font_path, min_px)


def _make_near_white_transparent(img: Image.Image, *, threshold: int = 245) -> Image.Image:
    work = img.convert("RGBA")
    px = list(work.getdata())
    out = []
    for r, g, b, a in px:
        if r > threshold and g > threshold and b > threshold:
            out.append((r, g, b, 0))
        else:
            out.append((r, g, b, a))
    work.putdata(out)
    return work


def create_cover_page(level: int, output_path: str, *, grayscale: bool = False) -> None:
    """Create a Matching cover page using the Small Wins frame + Bingo-style layout."""
    mode = "bw" if grayscale else "color"
    level_info = LEVELS[level]
    accent_hex = "#808080" if grayscale else level_info["color"]
    pack_code = "BB03"
    theme_name = "Brown Bear"

    w = int(PAGE_WIDTH * DPI / 72)
    h = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(page)
    fonts = _load_fonts()

    # Load bear icon for header
    bear = None
    p = _icon_path()
    if p.exists():
        try:
            bear = Image.open(p).convert("RGBA")
            if grayscale:
                bear = bear.convert("L").convert("RGBA")
        except Exception:
            bear = None

    apply_small_wins_frame(
        page,
        product_title=f"{theme_name} Matching",
        subtitle=f"Level {level} — {level_info['name']}",
        pack_code=pack_code,
        page_num=1,
        total_pages=16,
        level=None,
        accent_color_hex=accent_hex,
        footer_title=f"{theme_name} Matching | Level {level}",
        header_left_icon=bear,
        header_left_icon_flip=False,
        footer_y_offset_px=int(0.08 * DPI),
        draw_subtitle=True,
        draw_footer=True,
    )

    # --- Artwork box with bear icon (same as Bingo) ---
    art_box = int(3.05 * DPI)
    art_x = (w - art_box) // 2
    art_y = int(2.35 * DPI)
    draw.rounded_rectangle(
        [art_x, art_y, art_x + art_box, art_y + art_box],
        radius=int(0.20 * DPI),
        outline=hex_to_rgb(accent_hex),
        width=max(1, int(4 * (DPI / 72))),
        fill="white",
    )

    if bear is not None:
        icon_work = _make_near_white_transparent(bear.copy())
        try:
            bbox = icon_work.split()[3].getbbox()
            if bbox:
                icon_work = icon_work.crop(bbox)
        except Exception:
            pass
        # Scale to fill 80% of art box (resize UP since source icons are small)
        target = int(art_box * 0.80)
        iw, ih = icon_work.size
        scale = min(target / iw, target / ih)
        icon_work = icon_work.resize((int(iw * scale), int(ih * scale)), Image.Resampling.LANCZOS)
        page.paste(
            icon_work,
            (art_x + (art_box - icon_work.width) // 2, art_y + (art_box - icon_work.height) // 2),
            icon_work,
        )

    # --- Layout below artwork box ---
    left = art_x
    right_limit = art_x + art_box
    text_width = right_limit - left
    heading_font = fonts["heading"]
    bullet_font = fonts["bullet"]

    # 1) Tagline
    y = art_y + art_box + int(0.18 * DPI)
    desc = "Print, play, and practice\u2014differentiated levels for SPED learners"
    fitted_desc = _fit_font(
        draw, desc,
        font_path=_FONT_COMIC,
        max_px=int(32 * (DPI / 72)),
        min_px=int(16 * (DPI / 72)),
        max_w=text_width,
        max_h=int(0.45 * DPI),
    )
    dw, dh = _text_size(draw, desc, fitted_desc)
    draw.text((left + (text_width - dw) // 2, y), desc, fill=hex_to_rgb(NAVY_BLUE), font=fitted_desc)
    y += dh + int(0.18 * DPI)

    # 2) "What's Included" heading — orange for Level 1, accent color for others
    heading = "What\u2019s Included"
    hw, hh = _text_size(draw, heading, heading_font)
    heading_color = hex_to_rgb("#F5A623") if (level == 1 and not grayscale) else hex_to_rgb(accent_hex)
    draw.text((left, y), heading, fill=heading_color, font=heading_font)
    y += hh + int(0.06 * DPI)

    # 3) Bullet list — always navy body text
    bullet_color = hex_to_rgb(NAVY_BLUE)
    bullets = [
        "12 activity pages per level",
        "Print-ready cutout pieces",
        "Storage labels",
        "Color + black & white",
        "Optional laminate for reuse",
    ]
    bullet_indent = left + int(0.12 * DPI)
    for b in bullets:
        line = f"\u2022  {b}"
        draw.text((bullet_indent, y), line, fill=bullet_color, font=bullet_font)
        y += int(0.19 * DPI)

    # 4) "Quick Start" heading
    y += int(0.10 * DPI)
    quick = "Quick Start"
    qw, qh = _text_size(draw, quick, heading_font)
    draw.text((left, y), quick, fill=hex_to_rgb(accent_hex), font=heading_font)
    y += qh + int(0.06 * DPI)

    # 5) Quick Start bullet points
    qs_bullets = [
        "Print activity pages and cutouts",
        "Cut pieces (optional laminate/Velcro)",
        "Match pieces to boards, then store with labels",
    ]
    qs_indent = left + int(0.12 * DPI)
    for qb in qs_bullets:
        qline = f"\u2022  {qb}"
        draw.text((qs_indent, y), qline, fill=hex_to_rgb(NAVY_BLUE), font=bullet_font)
        y += int(0.19 * DPI)

    # --- Save as single-page PDF ---
    buf = io.BytesIO()
    page.save(buf, format="PNG", dpi=(DPI, DPI))
    buf.seek(0)

    c = canvas.Canvas(output_path, pagesize=letter)
    c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
    c.showPage()
    c.save()
    print(f"OK Created cover: {output_path}")


def generate_all_covers() -> None:
    """Generate covers for all 5 levels — color + B&W."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("MATCHING COVER GENERATOR (Small Wins Design System)")
    print("=" * 60)

    for level in range(1, 6):
        color_path = OUTPUT_DIR / f"cover_level{level}_color_FINAL.pdf"
        create_cover_page(level, str(color_path), grayscale=False)

        bw_path = OUTPUT_DIR / f"cover_level{level}_bw_FINAL.pdf"
        create_cover_page(level, str(bw_path), grayscale=True)

    print()
    print("=" * 60)
    print("OK All Matching covers generated (5 color + 5 B&W)")
    print("=" * 60)


if __name__ == "__main__":
    generate_all_covers()
