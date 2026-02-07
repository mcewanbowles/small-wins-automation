#!/usr/bin/env python3
"""
Universal Sorting Toolkit (Landscape + AAC Edge Strip) — Dual Mode

Generates landscape sorting mats with AAC core word prompts around the edges.
Supports 2-way, 3-way, and Yes/No sorting activities.

Author: Small Wins Studio
License: MIT
"""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageOps
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


# Page constants
PAGE_W, PAGE_H = landscape(A4)
MARGIN = 12 * mm
GUTTER = 6 * mm
FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


# AAC core words mapped to image filenames (16 buttons)
AAC_WORDS = [
    ("PUT", "put.png"),
    ("DIFFERENT", "different.png"),
    ("FINISHED", "finished.png"),
    ("AGAIN", "more.png"),  # Using "more" for "again"
    ("WAIT", "wait.png"),
    ("I THINK", "think.png"),
    ("SAME", "same.png"),
    ("HELP", "help.png"),
    ("STOP", "stop.png"),
    ("LIKE", "like.png"),
    ("DON'T LIKE", "dont_like.png"),
    ("FUNNY", "favorite.png"),  # Using "favorite" for "funny"
    ("UH-OH", "uh_oh.png"),
    ("WHOOPS", "uh_oh.png"),  # Reuse uh-oh
    ("MORE", "more.png"),
    ("YES", "yes.png"),
]


def image_to_grayscale(img: Image.Image) -> Image.Image:
    """Convert image to grayscale while preserving alpha."""
    if img.mode not in ("RGBA", "LA"):
        img = img.convert("RGBA")
    rgba = img.convert("RGBA")
    r, g, b, a = rgba.split()
    gray = ImageOps.grayscale(Image.merge("RGB", (r, g, b)))
    gray_rgb = Image.merge("RGB", (gray, gray, gray))
    return Image.merge("RGBA", (*gray_rgb.split(), a))


def load_aac_icon(icon_filename: str, mode: str, aac_dir: Path) -> Optional[Image.Image]:
    """
    Load an AAC icon from the aac_core directory.
    Returns None if not found.
    """
    icon_path = aac_dir / icon_filename
    if not icon_path.exists():
        return None
    
    img = Image.open(icon_path).convert("RGBA")
    if mode == "bw":
        img = image_to_grayscale(img)
    return img


def pil_to_imagereader(img: Image.Image) -> ImageReader:
    """Convert PIL Image to ReportLab ImageReader."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def create_page_canvas(out_path: Path, mode: str) -> canvas.Canvas:
    """Create a ReportLab canvas with standard settings."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_path), pagesize=landscape(A4))
    c.setTitle(f"Universal Sorting Mats + AAC ({mode})")
    c.setFont(FONT, 10)
    return c


def add_footer(c: canvas.Canvas, brand: str, mode: str, page_num: int) -> None:
    """Add footer to page."""
    c.setFont(FONT, 8)
    footer_y = 8 * mm
    c.drawString(MARGIN, footer_y, f"{brand} | Universal Sorting Mats + AAC | {mode.upper()}")
    c.drawRightString(PAGE_W - MARGIN, footer_y, f"Page {page_num}")
    c.setFont(FONT, 10)


def draw_header(c: canvas.Canvas, title: str, subtitle: str) -> None:
    """Draw page header."""
    c.setFont(FONT_BOLD, 16)
    c.drawString(MARGIN, PAGE_H - MARGIN, title)
    c.setFont(FONT, 11)
    c.drawString(MARGIN, PAGE_H - MARGIN - 8 * mm, subtitle)
    c.setFont(FONT, 10)


def default_categories() -> Dict:
    """Default sorting categories."""
    return {
        "two_way": [
            ["Flies", "Doesn't fly"],
            ["Swims", "Doesn't swim"],
            ["Big", "Small"],
            ["Same", "Different"],
            ["Happy", "Sad"]
        ],
        "three_way": [
            ["2 legs", "4 legs", "No legs"],
            ["Beginning", "Middle", "End"]
        ],
        "yes_no": [
            ["Is it green?"],
            ["Does it swim?"]
        ]
    }


def load_categories(path: Optional[Path]) -> Dict:
    """Load categories from JSON file or use defaults."""
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default_categories()


def draw_aac_edge_strip(c: canvas.Canvas, aac_dir: Path, mode: str) -> None:
    """
    Draw AAC buttons along top and bottom edges (8 + 8).
    Includes text labels and icons when available.
    """
    top_y = PAGE_H - MARGIN - 22 * mm
    bottom_y = MARGIN + 18 * mm

    btn_h = 18 * mm  # Taller for icons
    btn_gap = 3 * mm
    icon_size = 14 * mm

    # 8 buttons per row
    per_row = 8
    usable_w = PAGE_W - 2 * MARGIN
    btn_w = (usable_w - (per_row - 1) * btn_gap) / per_row

    c.setLineWidth(1.5)
    c.setFont(FONT, 8)

    for i in range(min(len(AAC_WORDS), 16)):
        row = 0 if i < 8 else 1
        col = i if i < 8 else i - 8

        y = top_y if row == 0 else bottom_y
        x = MARGIN + col * (btn_w + btn_gap)

        # Draw button box
        c.roundRect(x, y, btn_w, btn_h, 6)

        label, icon_file = AAC_WORDS[i]

        # Try to load and draw icon
        icon = load_aac_icon(icon_file, mode, aac_dir)
        if icon:
            # Scale icon proportionally
            w, h = icon.size
            scale = min(icon_size / w, icon_size / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            scaled = icon.resize((new_w, new_h), Image.LANCZOS)
            ir = pil_to_imagereader(scaled)

            # Center icon in top part of button
            icon_x = x + (btn_w - new_w) / 2
            icon_y = y + btn_h - new_h - 2 * mm
            c.drawImage(ir, icon_x, icon_y, width=new_w, height=new_h, mask="auto")

            # Text below icon
            c.drawCentredString(x + btn_w / 2, y + 2 * mm, label)
        else:
            # No icon - center text vertically
            c.drawCentredString(x + btn_w / 2, y + btn_h / 2 - 2 * mm, label)

    c.setFont(FONT, 10)


def draw_two_way_sort_area(c: canvas.Canvas, left: str, right: str) -> None:
    """
    Draw central 2-way sorting area, leaving space for AAC at top/bottom.
    """
    # Reserve edge space for AAC buttons
    edge_top = PAGE_H - MARGIN - 44 * mm
    edge_bottom = MARGIN + 40 * mm

    area_h = edge_top - edge_bottom
    area_w = PAGE_W - 2 * MARGIN
    col_w = (area_w - GUTTER) / 2

    x1 = MARGIN
    x2 = MARGIN + col_w + GUTTER
    y = edge_bottom

    # Column headings
    c.setFont(FONT_BOLD, 20)
    c.drawString(x1 + 4 * mm, edge_top + 8 * mm, left)
    c.drawString(x2 + 4 * mm, edge_top + 8 * mm, right)
    c.setFont(FONT, 10)

    # Sort boxes
    c.setLineWidth(3)
    c.setStrokeColorRGB(0.2, 0.3, 0.5)  # Navy blue
    c.roundRect(x1, y, col_w, area_h, 16)
    c.roundRect(x2, y, col_w, area_h, 16)
    c.setStrokeColorRGB(0, 0, 0)  # Reset to black

    # Instruction
    c.setFont(FONT, 9)
    c.drawString(MARGIN, y - 7 * mm, "Place cards inside the boxes. Model language using the AAC prompts above and below.")
    c.setFont(FONT, 10)


def draw_three_way_sort_area(c: canvas.Canvas, a: str, b: str, c_label: str) -> None:
    """Draw 3-way sorting area."""
    edge_top = PAGE_H - MARGIN - 44 * mm
    edge_bottom = MARGIN + 40 * mm

    area_h = edge_top - edge_bottom
    area_w = PAGE_W - 2 * MARGIN
    col_w = (area_w - 2 * GUTTER) / 3

    xs = [MARGIN, MARGIN + col_w + GUTTER, MARGIN + 2 * (col_w + GUTTER)]
    y = edge_bottom

    # Headings
    c.setFont(FONT_BOLD, 18)
    c.drawString(xs[0] + 4 * mm, edge_top + 8 * mm, a)
    c.drawString(xs[1] + 4 * mm, edge_top + 8 * mm, b)
    c.drawString(xs[2] + 4 * mm, edge_top + 8 * mm, c_label)
    c.setFont(FONT, 10)

    # Boxes
    c.setLineWidth(3)
    c.setStrokeColorRGB(0.2, 0.3, 0.5)
    for x in xs:
        c.roundRect(x, y, col_w, area_h, 14)
    c.setStrokeColorRGB(0, 0, 0)

    # Instruction
    c.setFont(FONT, 9)
    c.drawString(MARGIN, y - 7 * mm, "Sort cards into three categories. Use AAC to describe: I THINK, SAME, DIFFERENT, HELP.")
    c.setFont(FONT, 10)


def draw_yes_no_mat(c: canvas.Canvas, prompt: str) -> None:
    """Draw Yes/No sorting mat."""
    c.setFont(FONT_BOLD, 18)
    c.drawString(MARGIN, PAGE_H - MARGIN - 28 * mm, f"Prompt: {prompt}")
    c.setFont(FONT, 10)
    
    draw_two_way_sort_area(c, "YES", "NO")


def draw_instruction_page(c: canvas.Canvas, brand: str, mode: str) -> None:
    """Draw comprehensive instruction page."""
    draw_header(c, "Universal Sorting Mats + AAC Edge Strips", 
                "Landscape mats with AAC core word prompts for communication modeling")
    
    y = PAGE_H - MARGIN - 32 * mm
    c.setFont(FONT_BOLD, 12)
    c.drawString(MARGIN, y, "How to Use:")
    y -= 8 * mm
    
    c.setFont(FONT, 11)
    instructions = [
        "1. Choose a sorting mat (2-way, 3-way, or Yes/No)",
        "2. Add picture cards, word cards, or objects from your theme",
        "3. Model AAC: Use the core words around the edges during the activity",
        "   Examples: PUT, I THINK, SAME, DIFFERENT, HELP, FINISHED, AGAIN",
        "",
        "AAC Modeling Tips:",
        "• Point to core words as you speak",
        "• Pause to allow student response",
        "• Model simple phrases: 'I THINK... SAME' or 'PUT... DIFFERENT'",
        "• Encourage communication attempts",
        "",
        "Differentiation Levels:",
        "• Errorless: Pre-place one correct example in each box",
        "• Scaffolded: Provide verbal cues or gestures",
        "• Independent: Student sorts without help",
        "• Extension: Ask for reasoning: 'I THINK... because...'",
        "",
        "SPED/AAC Applications:",
        "• Build core vocabulary through repeated exposure",
        "• Practice expressive language during meaningful activities",
        "• Support visual learners with icon+text buttons",
        "• Encourage communication for all students",
    ]
    
    for line in instructions:
        c.drawString(MARGIN, y, line)
        y -= 6 * mm
        if y < MARGIN + 40 * mm:  # Leave room for footer
            break
    
    add_footer(c, brand, mode, 1)


def generate_mats_aac_pdf(out_path: Path, brand: str, mode: str, cats: Dict, aac_dir: Path) -> None:
    """Generate the sorting mats PDF with AAC edge strips."""
    c = create_page_canvas(out_path, mode)
    page_num = 1

    # Instruction page
    draw_instruction_page(c, brand, mode)
    c.showPage()
    page_num += 1

    # 2-way mats
    for left, right in cats.get("two_way", []):
        draw_header(c, "Sorting Mat — 2-Way", f"{left} / {right}")
        draw_aac_edge_strip(c, aac_dir, mode)
        draw_two_way_sort_area(c, left, right)
        add_footer(c, brand, mode, page_num)
        c.showPage()
        page_num += 1

    # 3-way mats
    for a, b, cc in cats.get("three_way", []):
        draw_header(c, "Sorting Mat — 3-Way", f"{a} / {b} / {cc}")
        draw_aac_edge_strip(c, aac_dir, mode)
        draw_three_way_sort_area(c, a, b, cc)
        add_footer(c, brand, mode, page_num)
        c.showPage()
        page_num += 1

    # Yes/No mats
    for (prompt,) in cats.get("yes_no", []):
        draw_header(c, "Sorting Mat — Yes/No", prompt)
        draw_aac_edge_strip(c, aac_dir, mode)
        draw_yes_no_mat(c, prompt)
        add_footer(c, brand, mode, page_num)
        c.showPage()
        page_num += 1

    c.save()


def generate_dual_mode(out_dir: Path, brand: str, categories_path: Optional[Path], aac_dir: Path) -> None:
    """Generate both color and B&W versions."""
    cats = load_categories(categories_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for mode in ("color", "bw"):
        out_path = out_dir / f"universal_sorting_mats_aac_{mode}.pdf"
        generate_mats_aac_pdf(out_path, brand, mode, cats, aac_dir)
        print(f"Generated: {out_path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate Universal Sorting Mats with AAC edge prompts (dual-mode)."
    )
    p.add_argument("--out_dir", required=True, type=str, help="Output folder for PDFs.")
    p.add_argument("--brand", default="Small Wins Studio", type=str, help="Footer brand text.")
    p.add_argument("--categories", default="", type=str, help="Optional JSON file of categories.")
    p.add_argument("--aac_dir", default="assets/global/aac_core", type=str, 
                   help="Directory containing AAC core word images.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    categories_path = Path(args.categories).expanduser().resolve() if args.categories else None
    aac_dir = Path(args.aac_dir).expanduser().resolve()
    
    if not aac_dir.exists():
        print(f"Warning: AAC directory not found: {aac_dir}")
        print("PDFs will be generated without AAC icons (text only)")
    
    generate_dual_mode(out_dir, args.brand, categories_path, aac_dir)
    print(f"\nDone! PDFs saved to: {out_dir}")


if __name__ == "__main__":
    main()
