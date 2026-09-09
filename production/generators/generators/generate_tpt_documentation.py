#!/usr/bin/env python3
"""
Generate TPT Documentation Pages for Small Wins Studio.
Creates professional 1-page Terms of Use & Credits document.

Per the spec addendum, ALL support docs must use the standard
`apply_small_wins_frame` from `utils.sws_design`. This generator builds a
PIL Image page, wraps it in the standard Small Wins frame, and saves it via
a ReportLab canvas (`canvas.drawImage`) — the same pattern used by every
other generator.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# Bootstrap repo root so `utils.*` imports resolve.
# This file lives at <repo>/production/generators/generators/generate_tpt_documentation.py
# so parents[3] is the repo root.
_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[3]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from utils.UNIVERSAL_STANDARDS import COPYRIGHT_YEAR, SWS_NAVY
from utils.sws_design import (
    DPI,
    _brand_font_pt,
    _text_size,
    apply_small_wins_frame,
    hex_to_rgb,
)

# ---------------------------------------------------------------------------
# Page geometry (pixels at 300 DPI)
# ---------------------------------------------------------------------------
PAGE_W_PT, PAGE_H_PT = letter
PAGE_W = int(PAGE_W_PT * DPI / 72)
PAGE_H = int(PAGE_H_PT * DPI / 72)

# Content margins (in pixels)
LEFT = int(0.55 * DPI)
RIGHT = PAGE_W - int(0.55 * DPI)
MAX_W = RIGHT - LEFT

# Brand colours
GREEN = "#34A853"
RED = "#EA4335"
BLACK_RGB = (0, 0, 0)

# Configuration defaults (can be overridden via CLI)
BOOK_TITLE = "Brown Bear, Brown Bear, What Do You See?"
BOOK_AUTHOR = "Bill Martin Jr. and Eric Carle"
TPT_STORE_URL = "www.teacherspayteachers.com/Store/Small-Wins-Studio"


# ---------------------------------------------------------------------------
# Small PIL drawing helpers
# ---------------------------------------------------------------------------
def _font(pt: int, bold: bool = False):
    """Return a brand font at the given point size."""
    return _brand_font_pt(pt, bold=bold, brand="poppins")


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    """Word-wrap a line of text to fit within max_w pixels."""
    words = (text or "").split()
    if not words:
        return [""]
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        trial = f"{cur} {w}"
        if _text_size(draw, trial, font)[0] <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _draw_section_header(draw: ImageDraw.ImageDraw, y: int, title: str) -> int:
    """Draw a centered section header with an underline. Returns new y."""
    font = _font(13, bold=True)
    tw, th = _text_size(draw, title, font)
    draw.text((LEFT + (MAX_W - tw) // 2, y), title, fill=hex_to_rgb(SWS_NAVY), font=font)
    underline_y = y + th + 4
    draw.line([(LEFT, underline_y), (RIGHT, underline_y)], fill=hex_to_rgb(SWS_NAVY), width=2)
    return underline_y + int(0.12 * DPI)


def _draw_bullet(draw: ImageDraw.ImageDraw, x: int, y: int, text: str) -> int:
    """Draw a bullet point with wrapping. Returns new y."""
    font = _font(11, bold=False)
    draw.text((x, y), "•", fill=BLACK_RGB, font=font)
    indent = int(0.18 * DPI)
    for ln in _wrap(draw, text, font, MAX_W - indent):
        draw.text((x + indent, y), ln, fill=BLACK_RGB, font=font)
        _, th = _text_size(draw, ln, font)
        y += th + int(0.06 * DPI)
    return y


# ---------------------------------------------------------------------------
# Page builder
# ---------------------------------------------------------------------------
def _build_page(book_title: str, book_author: str, pack_code: str) -> Image.Image:
    """Build the single-page Terms of Use & Credits document as a PIL Image."""
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")

    # Standard Small Wins frame: border, teal accent strip with product title
    # and subtitle, plus the standard footer (with PCS line + copyright).
    apply_small_wins_frame(
        page,
        product_title="Terms of Use",
        subtitle="Small Wins Studio",
        pack_code=pack_code,
        page_num=1,
        total_pages=1,
        level=None,
        draw_footer=True,
        draw_pcs_line=True,
    )

    draw = ImageDraw.Draw(page)

    # Content starts below the accent strip / instruction area.
    y = int(1.55 * DPI)

    # ---- Terms of Use - Single-User License ----
    y = _draw_section_header(draw, y, "📋 Terms of Use - Single-User License")

    # YOU MAY
    may_font = _font(11, bold=True)
    draw.text((LEFT, y), "✓ YOU MAY:", fill=hex_to_rgb(GREEN), font=may_font)
    _, mh = _text_size(draw, "✓ YOU MAY:", may_font)
    y += mh + int(0.06 * DPI)

    for item in [
        "Use this resource for your own students • Print copies for classroom use",
        "Share with substitute teachers • Adapt materials for your students' needs",
    ]:
        y = _draw_bullet(draw, LEFT + int(0.10 * DPI), y, item)

    y += int(0.10 * DPI)

    # YOU MAY NOT
    maynot_font = _font(11, bold=True)
    draw.text((LEFT, y), "✗ YOU MAY NOT:", fill=hex_to_rgb(RED), font=maynot_font)
    _, nh = _text_size(draw, "✗ YOU MAY NOT:", maynot_font)
    y += nh + int(0.06 * DPI)

    for item in [
        "Share digital files with other teachers • Upload to school servers",
        "Resell or redistribute this resource • Claim this work as your own",
    ]:
        y = _draw_bullet(draw, LEFT + int(0.10 * DPI), y, item)

    y += int(0.16 * DPI)

    # ---- Important Book Disclaimer ----
    y = _draw_section_header(draw, y, "📚 Important Book Disclaimer")

    body_font = _font(11, bold=False)
    disclaimer_lines = [
        f"This product is designed to complement \"{book_title}\" by {book_author}. "
        f"This product is NOT affiliated with, endorsed by, or sponsored by the book's "
        f"publisher or authors. You will need to purchase the book separately.",
        "",
        "All book-related content is used under fair use for educational purposes. "
        "BoardMaker symbols are used under PCS Maker Personal License.",
    ]
    for line in disclaimer_lines:
        if line:
            for ln in _wrap(draw, line, body_font, MAX_W):
                draw.text((LEFT, y), ln, fill=BLACK_RGB, font=body_font)
                _, lh = _text_size(draw, ln, body_font)
                y += lh + int(0.05 * DPI)
        else:
            y += int(0.08 * DPI)

    y += int(0.12 * DPI)

    # ---- Credits & Acknowledgments ----
    y = _draw_section_header(draw, y, "🎨 Credits & Acknowledgments")

    label_font = _font(11, bold=True)
    text_font = _font(11, bold=False)
    label_w = int(0.42 * DPI)
    for label, text in [
        ("Symbols:", "PCS® symbols © Tobii Dynavox. Used with active PCS Maker Personal License."),
        ("Design:", "Small Wins Studio original design following accessibility best practices."),
    ]:
        draw.text((LEFT, y), label, fill=BLACK_RGB, font=label_font)
        for ln in _wrap(draw, text, text_font, MAX_W - label_w):
            draw.text((LEFT + label_w, y), ln, fill=BLACK_RGB, font=text_font)
            _, lh = _text_size(draw, ln, text_font)
            y += lh + int(0.05 * DPI)
        y += int(0.04 * DPI)

    y += int(0.16 * DPI)

    # ---- Feedback / store line ----
    combined_text = [
        "As a new TPT seller, your reviews and feedback mean everything! If you found",
        "this resource helpful, please consider leaving a rating.",
        "",
        f"Visit: {TPT_STORE_URL}",
    ]
    for line in combined_text:
        draw.text((LEFT, y), line, fill=BLACK_RGB, font=body_font)
        _, lh = _text_size(draw, line, body_font)
        y += lh + int(0.05 * DPI)

    return page


def _save_pdf(pdf_path: Path, page: Image.Image) -> None:
    """Save a PIL Image page to a one-page PDF via a ReportLab canvas."""
    pdf = canvas.Canvas(str(pdf_path), pagesize=letter)
    buffer = io.BytesIO()
    page.save(buffer, "PNG", dpi=(DPI, DPI))
    buffer.seek(0)
    pdf.drawImage(ImageReader(buffer), 0, 0, width=PAGE_W_PT, height=PAGE_H_PT)
    pdf.showPage()
    pdf.save()


def generate_tpt_documentation(pack_code: str, theme_name: str, output_dir: Path):
    """Generate the TPT Terms of Use PDF to OUTPUT/<pack_code>_Terms_of_Use.pdf."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{pack_code}_Terms_of_Use.pdf"
    # Use theme_name as the visible book title in the disclaimer
    page = _build_page(book_title=theme_name, book_author=BOOK_AUTHOR, pack_code=pack_code)
    _save_pdf(pdf_path, page)
    print(f"Generated: {pdf_path}")


if __name__ == '__main__':
    # CLI: python generate_tpt_documentation.py <pack_code> "<theme_name>" <output_dir>
    pack_code = sys.argv[1] if len(sys.argv) > 1 else "BB0ALL"
    theme_name = sys.argv[2] if len(sys.argv) > 2 else BOOK_TITLE.split(',')[0]
    out_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("OUTPUT")
    generate_tpt_documentation(pack_code, theme_name, out_dir)
