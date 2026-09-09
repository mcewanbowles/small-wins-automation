#!/usr/bin/env python3
"""Freebie Generator for Small Wins Studio TPT products.

Generates a freebie PDF with 1 sample page from each level, cutouts, and
color-coded storage labels.

Per the spec addendum, ALL support docs use the standard
``apply_small_wins_frame`` from ``utils.sws_design``. Page composition is done
with PIL (Pillow); ReportLab is used only for the final PDF save (one
``canvas.drawImage`` per PIL page), matching the pattern used by the other
generators in this codebase.
"""

from __future__ import annotations

import io
import os
from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from utils.UNIVERSAL_STANDARDS import SWS_NAVY, SWS_TEAL, SWS_TEAL_LT
from utils.sws_design import (
    DPI,
    _brand_font_pt,
    apply_small_wins_frame,
    hex_to_rgb,
    shrink_font_to_fit_with_pt,
)

# Letter page at 300 DPI
PAGE_W_PT, PAGE_H_PT = letter
PAGE_W = int(PAGE_W_PT * DPI / 72)
PAGE_H = int(PAGE_H_PT * DPI / 72)

# Level colours (1-4 mapped to the universal standard palette; 5 is a freebie-only
# "Real Photos" tier kept for backwards compatibility with the original generator).
LEVEL_COLORS = {
    1: "#7C3AED",  # Violet  - Supported / Errorless
    2: "#0284C7",  # Ocean   - Easy / Developing
    3: "#059669",  # Emerald - Medium / Independent
    4: "#E11D48",  # Rose    - Challenge / Extended
    5: "#DDA0DD",  # Plum    - Real Photos (freebie-only tier)
}

LEVEL_NAMES = {
    1: "Errorless",
    2: "Easy",
    3: "Medium",
    4: "Challenge",
    5: "Real Photos",
}

NAVY = hex_to_rgb(SWS_NAVY)
TEAL = hex_to_rgb(SWS_TEAL)
TEAL_LT = hex_to_rgb(SWS_TEAL_LT)
WHITE = (255, 255, 255)
LIGHT_GRAY = (153, 153, 153)


# ---------------------------------------------------------------------------
# Small helpers (mirror the conventions used by the other PIL generators)
# ---------------------------------------------------------------------------
def _font(pt: int, bold: bool = False):
    return _brand_font_pt(pt, bold=bold, brand="poppins" if bold else "nunito")


def _fit(text: str, pt: int, width: int, minimum: int = 10, bold: bool = True):
    return shrink_font_to_fit_with_pt(
        text, base_pt=pt, max_width_px=width, bold=bold,
        brand="poppins" if bold else "nunito", min_pt=minimum,
    )[0]


def _center(draw, box, text, font, fill):
    bounds = draw.textbbox((0, 0), text, font=font)
    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    x1, y1, x2, y2 = box
    draw.text(
        (x1 + (x2 - x1 - width) // 2 - bounds[0],
         y1 + (y2 - y1 - height) // 2 - bounds[1]),
        text, font=font, fill=fill,
    )


def _resolve_hero(theme_dir: str | os.PathLike | None) -> Image.Image | None:
    """Resolve the hero icon from ``theme_dir / "hero.png"`` (if present)."""
    if not theme_dir:
        return None
    hero_path = Path(theme_dir) / "hero.png"
    if not hero_path.exists():
        return None
    try:
        im = Image.open(hero_path)
        return im.convert("RGBA") if im.mode != "RGBA" else im
    except Exception:
        return None


def _page(product_title: str, subtitle: str, pack_code: str,
          page_num: int, total_pages: int, *,
          level: int | None = None, hero_img: Image.Image | None = None) -> Image.Image:
    """Create a white PIL page and apply the standard Small Wins frame."""
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    apply_small_wins_frame(
        page,
        product_title=product_title,
        subtitle=subtitle,
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=level,
        draw_footer=True,
        draw_pcs_line=True,
        draw_subtitle=True,
        header_left_icon=hero_img,
    )
    return page


def _save_pdf(out_path: str | os.PathLike, pages: list[Image.Image]) -> None:
    """Save a list of PIL pages to a single PDF via ReportLab (one image per page)."""
    pdf = canvas.Canvas(str(out_path), pagesize=letter)
    for page in pages:
        buf = io.BytesIO()
        page.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        pdf.drawImage(ImageReader(buf), 0, 0, width=PAGE_W_PT, height=PAGE_H_PT)
        pdf.showPage()
    pdf.save()


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------
def generate_freebie_cover(product_title: str, pack_code: str, total_pages: int,
                           hero_img: Image.Image | None = None) -> Image.Image:
    """Generate the freebie cover page."""
    page = _page("Free Sampler", product_title, pack_code, 1, total_pages, hero_img=hero_img)
    draw = ImageDraw.Draw(page)

    # "What's included" panel
    box_x1, box_y1 = 220, 1180
    box_x2, box_y2 = PAGE_W - 220, 2050
    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=42,
                           fill=TEAL_LT, outline=TEAL, width=4)
    _center(draw, (box_x1, box_y1 + 45, box_x2, box_y1 + 140),
            "What's Included:", _font(17, True), NAVY)

    items = [
        "1 sample activity page from EACH level (5 pages)",
        "Matching cutouts for each activity",
        "Color-coded storage labels",
        "Quick Start guide",
        "Terms of Use",
    ]
    y = box_y1 + 200
    body = _font(14)
    for item in items:
        _center(draw, (box_x1, y, box_x2, y + 80), item, body, NAVY)
        y += 110

    # Levels preview
    preview_y = box_y2 + 90
    _center(draw, (220, preview_y, PAGE_W - 220, preview_y + 80),
            "Preview All 5 Levels:", _font(16, True), NAVY)

    box_w, box_h = 360, 240
    gap = 40
    grid_w = 5 * box_w + 4 * gap
    start_x = (PAGE_W - grid_w) // 2
    row_y = preview_y + 110
    for level in range(1, 6):
        x = start_x + (level - 1) * (box_w + gap)
        color = hex_to_rgb(LEVEL_COLORS[level])
        draw.rounded_rectangle([x, row_y, x + box_w, row_y + box_h], radius=20,
                               fill=color, outline=NAVY, width=3)
        _center(draw, (x, row_y + 50, x + box_w, row_y + 130),
                f"Level {level}", _font(13, True), NAVY)
        _center(draw, (x, row_y + 140, x + box_w, row_y + 210),
                LEVEL_NAMES[level], _font(11), NAVY)

    # CTA pill
    cta_y = row_y + box_h + 90
    cta_x1 = (PAGE_W - 1500) // 2
    draw.rounded_rectangle([cta_x1, cta_y, cta_x1 + 1500, cta_y + 120], radius=60,
                           fill=TEAL)
    _center(draw, (cta_x1, cta_y, cta_x1 + 1500, cta_y + 120),
            "Love it? Get the Full Bundle!", _font(16, True), WHITE)

    return page


def generate_sample_activity_page(level: int, product_title: str, pack_code: str,
                                  page_num: int, total_pages: int,
                                  product_type: str = "Matching",
                                  hero_img: Image.Image | None = None) -> Image.Image:
    """Generate a sample activity page for a level."""
    subtitle = f"{product_title} - Level {level} Sample"
    page = _page("Free Sampler", subtitle, pack_code, page_num, total_pages,
                 level=level, hero_img=hero_img)
    draw = ImageDraw.Draw(page)

    level_color = hex_to_rgb(LEVEL_COLORS[level])
    level_name = LEVEL_NAMES[level]

    # Main content area placeholder
    content_x1, content_y1 = 220, 1180
    content_x2, content_y2 = PAGE_W - 220, 3300
    draw.rounded_rectangle([content_x1, content_y1, content_x2, content_y2], radius=24,
                           fill=(250, 250, 250), outline=level_color, width=5)

    _center(draw, (content_x1, (content_y1 + content_y2) // 2 - 80,
                   content_x2, (content_y1 + content_y2) // 2),
            f"[Sample {product_type} Activity Page]", _font(18), LIGHT_GRAY)
    _center(draw, (content_x1, (content_y1 + content_y2) // 2 + 10,
                   content_x2, (content_y1 + content_y2) // 2 + 90),
            f"Level {level}: {level_name}", _font(13), LIGHT_GRAY)

    return page


def generate_cutouts_page(level: int, product_title: str, pack_code: str,
                          page_num: int, total_pages: int,
                          hero_img: Image.Image | None = None) -> Image.Image:
    """Generate a cutouts page for a level."""
    subtitle = f"{product_title} - Level {level} Cutouts"
    page = _page("Free Sampler", subtitle, pack_code, page_num, total_pages,
                 level=level, hero_img=hero_img)
    draw = ImageDraw.Draw(page)

    level_color = hex_to_rgb(LEVEL_COLORS[level])

    cutout_size = 380
    cols, rows = 4, 5
    gap = 70
    grid_w = cols * cutout_size + (cols - 1) * gap
    margin_x = (PAGE_W - grid_w) // 2
    start_y = 1180

    for row in range(rows):
        for col in range(cols):
            x = margin_x + col * (cutout_size + gap)
            y = start_y + row * (cutout_size + gap)
            # PIL has no native dashed rounded-rect; draw a solid outline instead.
            draw.rounded_rectangle([x, y, x + cutout_size, y + cutout_size], radius=12,
                                   fill=WHITE, outline=level_color, width=3)
            _center(draw, (x, y, x + cutout_size, y + cutout_size),
                    "[Cutout]", _font(10), LIGHT_GRAY)

    return page


def generate_storage_labels_page(product_title: str, pack_code: str,
                                 page_num: int, total_pages: int,
                                 hero_img: Image.Image | None = None) -> Image.Image:
    """Generate color-coded storage labels page."""
    page = _page("Free Sampler", f"{product_title} - Storage Labels", pack_code,
                 page_num, total_pages, hero_img=hero_img)
    draw = ImageDraw.Draw(page)

    label_height = 300
    label_width = PAGE_W - 440
    start_y = 1180
    gap = 60

    for level in range(1, 6):
        level_color = hex_to_rgb(LEVEL_COLORS[level])
        level_name = LEVEL_NAMES[level]
        y = start_y + (level - 1) * (label_height + gap)
        draw.rounded_rectangle([220, y, 220 + label_width, y + label_height], radius=30,
                               fill=level_color, outline=NAVY, width=5)
        _center(draw, (220, y + 60, 220 + label_width, y + 160),
                f"Level {level}: {level_name}", _font(18, True), NAVY)
        _center(draw, (220, y + 170, 220 + label_width, y + 250),
                product_title, _font(13), NAVY)

    return page


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------
def generate_freebie(output_path, product_title, product_type='Matching',
                     pack_code: str = "FREE", theme_dir: str | os.PathLike | None = None):
    """Generate a complete freebie PDF.

    Parameters
    ----------
    output_path : str | os.PathLike
        Where to write the finished PDF.
    product_title : str
        The book/product title (e.g. "Brown Bear Matching"). Used as the frame
        subtitle and on storage labels.
    product_type : str
        Activity type label shown on sample pages (default "Matching").
    pack_code : str
        Pack code passed to ``apply_small_wins_frame`` (default "FREE").
    theme_dir : str | os.PathLike | None
        Theme folder used to resolve ``hero.png`` for the header icon.
    """
    hero_img = _resolve_hero(theme_dir)

    # 1 cover + 5 sample activities + 5 cutouts + 1 storage labels = 12 pages
    total_pages = 12
    pages: list[Image.Image] = []

    # Page 1: Cover
    pages.append(generate_freebie_cover(product_title, pack_code, total_pages, hero_img))

    # Pages 2-6: Sample activity from each level
    for level in range(1, 6):
        pages.append(generate_sample_activity_page(
            level, product_title, pack_code, len(pages) + 1, total_pages,
            product_type, hero_img))

    # Pages 7-11: Cutouts for each level
    for level in range(1, 6):
        pages.append(generate_cutouts_page(
            level, product_title, pack_code, len(pages) + 1, total_pages, hero_img))

    # Page 12: Storage labels
    pages.append(generate_storage_labels_page(
        product_title, pack_code, len(pages) + 1, total_pages, hero_img))

    _save_pdf(output_path, pages)
    return output_path


if __name__ == '__main__':
    output_dir = 'review_pdfs'
    os.makedirs(output_dir, exist_ok=True)

    # Resolve the Brown Bear theme dir relative to the repo root so the hero
    # icon can be picked up by the standard frame.
    _root = Path(__file__).resolve().parents[2]
    _theme_dir = _root / "assets" / "themes" / "brown_bear"

    output_path = os.path.join(output_dir, 'brown_bear_matching_freebie.pdf')
    generate_freebie(
        output_path, 'Brown Bear Matching', 'Matching',
        pack_code="BBM-FREE", theme_dir=_theme_dir,
    )

    print(f"Generated freebie: {output_path}")
