"""
Puppet Characters Generator (Dual Mode: Colour + B/W)

Generates 5 types of puppet resources from Boardmaker icons:
1. Stick Puppets with handle strips
2. Finger Puppets with fold tabs
3. Velcro Character Cards with bold outlines
4. Story Mat with WH prompts + character strip
5. Lanyard Characters with hole-punch indicators

Outputs both color and B/W versions of all resources.

Usage:
    python generators/puppet_characters/puppet_characters.py \
        --icons_dir "assets/themes/brown_bear/icons" \
        --out_dir "OUTPUT/puppets" \
        --theme "Brown Bear" \
        --brand "Small Wins Studio"

Dependencies:
    pip install reportlab pillow
"""

from __future__ import annotations

import argparse
import io
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

from PIL import Image, ImageOps, ImageFilter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# =========================
# Constants / Config
# =========================

PAGE_W, PAGE_H = A4  # points
MARGIN = 12 * mm
GUTTER = 6 * mm
FONT_NAME = "Helvetica"

WH_PROMPTS = ["WHO?", "WHAT?", "WHERE?", "WHEN?", "WHY?", "HOW?"]


# =========================
# Utilities: filenames
# =========================

def safe_filename(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"[^a-z0-9]+", "_", t)
    t = re.sub(r"_+", "_", t).strip("_")
    return t or "output"


# =========================
# Utilities: images
# =========================

def image_to_grayscale(img: Image.Image) -> Image.Image:
    """
    Convert an image to grayscale while preserving alpha if present.
    """
    if img.mode not in ("RGBA", "LA"):
        img = img.convert("RGBA")
    rgba = img.convert("RGBA")
    r, g, b, a = rgba.split()
    gray = ImageOps.grayscale(Image.merge("RGB", (r, g, b)))
    gray_rgb = Image.merge("RGB", (gray, gray, gray))
    return Image.merge("RGBA", (*gray_rgb.split(), a))


def scale_image_proportional(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Proportionally scale image to fit inside (target_w, target_h), keeping aspect ratio.
    """
    if target_w <= 0 or target_h <= 0:
        raise ValueError("target_w/target_h must be positive")

    if img.mode not in ("RGBA", "RGB", "LA", "L"):
        img = img.convert("RGBA")

    w, h = img.size
    if w == 0 or h == 0:
        raise ValueError("Image has invalid size")

    scale = min(target_w / w, target_h / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return img.resize((new_w, new_h), Image.LANCZOS)


def center_image_in_box(box_x: float, box_y: float, box_w: float, box_h: float,
                        img_w: float, img_h: float) -> Tuple[float, float]:
    """
    Given a box (x,y,w,h) and image (w,h), return (x,y) to center image in box.
    Coordinates are reportlab points; (x,y) is lower-left.
    """
    x = box_x + (box_w - img_w) / 2.0
    y = box_y + (box_h - img_h) / 2.0
    return x, y


def add_bold_outline(img: Image.Image, outline_px: int = 6) -> Image.Image:
    """
    Adds a bold outline around non-transparent pixels.
    Works best with transparent PNGs.
    """
    rgba = img.convert("RGBA")
    alpha = rgba.split()[-1]

    # Thicken alpha mask to create an outline region
    # (Use MaxFilter repeatedly to "dilate" the mask)
    mask = alpha
    for _ in range(max(1, outline_px // 2)):
        mask = mask.filter(ImageFilter.MaxFilter(5))

    # Create black outline layer
    outline = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    outline.putalpha(mask)

    # Composite: outline underneath, original on top
    out = Image.alpha_composite(outline, rgba)
    return out


def pil_to_imagereader(img: Image.Image) -> ImageReader:
    """
    Convert PIL Image to a ReportLab ImageReader without writing to disk.
    """
    buf = io.BytesIO()
    # PNG preserves transparency
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


# =========================
# Utilities: PDF layout
# =========================

def create_page_canvas(out_path: Path, mode: str) -> canvas.Canvas:
    """
    Create a reportlab Canvas with standard settings.
    mode: "color" or "bw"
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_path), pagesize=A4)
    c.setAuthor("Small Wins Studio")
    c.setTitle(f"Puppet Characters ({mode})")
    c.setFont(FONT_NAME, 10)
    return c


def add_footer(c: canvas.Canvas, brand: str, theme: str, mode: str, page_num: int) -> None:
    """
    Standard footer for all pages.
    """
    footer_y = 8 * mm
    c.setFont(FONT_NAME, 8)
    left = MARGIN
    right = PAGE_W - MARGIN

    c.drawString(left, footer_y, f"{brand} | {theme} | {mode.upper()} | Print & Go")
    c.drawRightString(right, footer_y, f"Page {page_num}")
    c.setFont(FONT_NAME, 10)


def draw_title(c: canvas.Canvas, theme: str, subtitle: str) -> None:
    c.setFont(FONT_NAME, 16)
    c.drawString(MARGIN, PAGE_H - MARGIN + 2 * mm, f"{theme} — {subtitle}")
    c.setFont(FONT_NAME, 10)


def draw_cut_label(c: canvas.Canvas, x: float, y: float, text: str) -> None:
    c.setFont(FONT_NAME, 7)
    c.drawString(x, y, text)
    c.setFont(FONT_NAME, 10)


# =========================
# Model
# =========================

@dataclass(frozen=True)
class CharacterAsset:
    name: str
    path: Path


def load_character_assets(icons_dir: Path) -> List[CharacterAsset]:
    if not icons_dir.exists():
        raise FileNotFoundError(f"icons_dir not found: {icons_dir}")

    exts = {".png", ".jpg", ".jpeg", ".webp"}
    files = [p for p in icons_dir.iterdir() if p.is_file() and p.suffix.lower() in exts]
    files.sort(key=lambda p: p.name.lower())

    assets: List[CharacterAsset] = []
    for p in files:
        name = p.stem
        assets.append(CharacterAsset(name=name, path=p))
    if not assets:
        raise ValueError(f"No image files found in: {icons_dir}")

    return assets


def open_character_image(asset: CharacterAsset, mode: str, add_outline: bool = False) -> Image.Image:
    img = Image.open(asset.path).convert("RGBA")
    if mode == "bw":
        img = image_to_grayscale(img)
    if add_outline:
        img = add_bold_outline(img, outline_px=8)
    return img


# =========================
# Generators (5 types)
# =========================

def generate_stick_puppets(c: canvas.Canvas, assets: List[CharacterAsset], theme: str, brand: str, mode: str) -> None:
    """
    Stick puppets laid out in a 2x3 grid per page.
    Each cell: character + handle strip below (cut + tape).
    """
    cols, rows = 2, 3
    usable_w = PAGE_W - 2 * MARGIN
    usable_h = PAGE_H - 2 * MARGIN - 14 * mm  # space for title + footer
    cell_w = (usable_w - (cols - 1) * GUTTER) / cols
    cell_h = (usable_h - (rows - 1) * GUTTER) / rows

    handle_h = 22 * mm
    img_box_h = cell_h - handle_h - 4 * mm

    page_num = 1
    i = 0

    while i < len(assets):
        c.setFont(FONT_NAME, 10)
        draw_title(c, theme, "Stick Puppets (cut + tape handle)")
        y_top = PAGE_H - MARGIN - 18 * mm

        for r in range(rows):
            for col in range(cols):
                if i >= len(assets):
                    break

                x = MARGIN + col * (cell_w + GUTTER)
                y = y_top - (r + 1) * cell_h - r * GUTTER

                # Image box
                box_x = x
                box_y = y + handle_h + 2 * mm
                box_w = cell_w
                box_h = img_box_h

                img = open_character_image(assets[i], mode=mode, add_outline=False)
                scaled = scale_image_proportional(img, int(box_w), int(box_h))
                ir = pil_to_imagereader(scaled)

                img_x, img_y = center_image_in_box(box_x, box_y, box_w, box_h, scaled.width, scaled.height)
                c.drawImage(ir, img_x, img_y, width=scaled.width, height=scaled.height, mask="auto")

                # Handle strip (simple)
                strip_x = x + cell_w * 0.2
                strip_w = cell_w * 0.6
                strip_y = y + 2 * mm
                strip_h = handle_h - 4 * mm

                c.setLineWidth(1)
                c.rect(strip_x, strip_y, strip_w, strip_h)

                # Tape line indicator (dashed) at top of strip
                c.setDash(3, 3)
                c.line(strip_x, strip_y + strip_h, strip_x + strip_w, strip_y + strip_h)
                c.setDash()

                draw_cut_label(c, x, y + cell_h - 6 * mm, assets[i].name)

                i += 1

            if i >= len(assets):
                break

        add_footer(c, brand, theme, mode, page_num)
        c.showPage()
        page_num += 1


def generate_finger_puppets(c: canvas.Canvas, assets: List[CharacterAsset], theme: str, brand: str, mode: str) -> None:
    """
    Finger puppets with fold tabs, 3x2 per page.
    """
    cols, rows = 3, 2
    usable_w = PAGE_W - 2 * MARGIN
    usable_h = PAGE_H - 2 * MARGIN - 14 * mm
    cell_w = (usable_w - (cols - 1) * GUTTER) / cols
    cell_h = (usable_h - (rows - 1) * GUTTER) / rows

    tab_h = 14 * mm
    img_box_h = cell_h - tab_h - 6 * mm

    page_num = 1
    i = 0

    while i < len(assets):
        draw_title(c, theme, "Finger Puppets (cut + fold tabs)")
        y_top = PAGE_H - MARGIN - 18 * mm

        for r in range(rows):
            for col in range(cols):
                if i >= len(assets):
                    break

                x = MARGIN + col * (cell_w + GUTTER)
                y = y_top - (r + 1) * cell_h - r * GUTTER

                # Outer puppet shape
                c.setLineWidth(1.2)
                c.rect(x, y, cell_w, cell_h)

                # Fold line (dashed) above tabs
                c.setDash(3, 3)
                c.line(x, y + tab_h, x + cell_w, y + tab_h)
                c.setDash()

                # Tabs: simple left/right small rectangles
                tab_w = cell_w * 0.25
                c.rect(x, y, tab_w, tab_h)
                c.rect(x + cell_w - tab_w, y, tab_w, tab_h)

                # Image box above fold line
                box_x = x + 3 * mm
                box_y = y + tab_h + 3 * mm
                box_w = cell_w - 6 * mm
                box_h = img_box_h - 6 * mm

                img = open_character_image(assets[i], mode=mode, add_outline=False)
                scaled = scale_image_proportional(img, int(box_w), int(box_h))
                ir = pil_to_imagereader(scaled)

                img_x, img_y = center_image_in_box(box_x, box_y, box_w, box_h, scaled.width, scaled.height)
                c.drawImage(ir, img_x, img_y, width=scaled.width, height=scaled.height, mask="auto")

                draw_cut_label(c, x, y + cell_h - 6 * mm, assets[i].name)
                i += 1

            if i >= len(assets):
                break

        add_footer(c, brand, theme, mode, page_num)
        c.showPage()
        page_num += 1


def generate_velcro_cards(c: canvas.Canvas, assets: List[CharacterAsset], theme: str, brand: str, mode: str) -> None:
    """
    Velcro character cards with bold outlines, 3x3 per page.
    """
    cols, rows = 3, 3
    usable_w = PAGE_W - 2 * MARGIN
    usable_h = PAGE_H - 2 * MARGIN - 14 * mm
    cell_w = (usable_w - (cols - 1) * GUTTER) / cols
    cell_h = (usable_h - (rows - 1) * GUTTER) / rows

    page_num = 1
    i = 0

    while i < len(assets):
        draw_title(c, theme, "Velcro Character Cards (bold outline)")
        y_top = PAGE_H - MARGIN - 18 * mm

        for r in range(rows):
            for col in range(cols):
                if i >= len(assets):
                    break

                x = MARGIN + col * (cell_w + GUTTER)
                y = y_top - (r + 1) * cell_h - r * GUTTER

                # Card border (bold)
                c.setLineWidth(3)
                c.rect(x, y, cell_w, cell_h)

                # Image with optional outline
                box_x = x + 5 * mm
                box_y = y + 8 * mm
                box_w = cell_w - 10 * mm
                box_h = cell_h - 16 * mm

                img = open_character_image(assets[i], mode=mode, add_outline=True)
                scaled = scale_image_proportional(img, int(box_w), int(box_h))
                ir = pil_to_imagereader(scaled)

                img_x, img_y = center_image_in_box(box_x, box_y, box_w, box_h, scaled.width, scaled.height)
                c.drawImage(ir, img_x, img_y, width=scaled.width, height=scaled.height, mask="auto")

                draw_cut_label(c, x, y + cell_h - 6 * mm, assets[i].name)
                i += 1

            if i >= len(assets):
                break

        add_footer(c, brand, theme, mode, page_num)
        c.showPage()
        page_num += 1


def generate_story_mat(c: canvas.Canvas, assets: List[CharacterAsset], theme: str, brand: str, mode: str) -> None:
    """
    One story mat per mode:
    - 6 WH prompt boxes
    - Character strip along bottom (mini icons)
    """
    page_num = 1
    draw_title(c, theme, "Story Mat (WH prompts)")

    # Prompt grid (3x2)
    cols, rows = 3, 2
    top_y = PAGE_H - MARGIN - 26 * mm
    grid_h = 95 * mm
    grid_w = PAGE_W - 2 * MARGIN
    cell_w = (grid_w - (cols - 1) * GUTTER) / cols
    cell_h = (grid_h - (rows - 1) * GUTTER) / rows

    idx = 0
    for r in range(rows):
        for col in range(cols):
            x = MARGIN + col * (cell_w + GUTTER)
            y = top_y - (r + 1) * cell_h - r * GUTTER

            c.setLineWidth(2)
            c.rect(x, y, cell_w, cell_h)

            c.setFont(FONT_NAME, 14)
            c.drawString(x + 6 * mm, y + cell_h - 12 * mm, WH_PROMPTS[idx])
            c.setFont(FONT_NAME, 10)
            idx += 1

    # Character strip area
    strip_y = MARGIN + 22 * mm
    strip_h = 40 * mm
    c.setLineWidth(2)
    c.rect(MARGIN, strip_y, PAGE_W - 2 * MARGIN, strip_h)
    c.setFont(FONT_NAME, 11)
    c.drawString(MARGIN + 4 * mm, strip_y + strip_h + 4 * mm, "Characters:")

    # Place mini icons across the strip
    if assets:
        padding = 6 * mm
        available_w = (PAGE_W - 2 * MARGIN) - 2 * padding
        max_icons = min(len(assets), 10)  # keep printable/clean
        spacing = available_w / max_icons
        icon_box = 28 * mm

        for i in range(max_icons):
            asset = assets[i]
            img = open_character_image(asset, mode=mode, add_outline=False)
            scaled = scale_image_proportional(img, int(icon_box), int(icon_box))
            ir = pil_to_imagereader(scaled)

            box_x = MARGIN + padding + i * spacing
            box_y = strip_y + (strip_h - icon_box) / 2.0
            img_x, img_y = center_image_in_box(box_x, box_y, icon_box, icon_box, scaled.width, scaled.height)
            c.drawImage(ir, img_x, img_y, width=scaled.width, height=scaled.height, mask="auto")

    add_footer(c, brand, theme, mode, page_num)
    c.showPage()


def generate_lanyard_characters(c: canvas.Canvas, assets: List[CharacterAsset], theme: str, brand: str, mode: str) -> None:
    """
    Lanyard cards with hole-punch indicator, 3x2 per page.
    """
    cols, rows = 3, 2
    usable_w = PAGE_W - 2 * MARGIN
    usable_h = PAGE_H - 2 * MARGIN - 14 * mm
    cell_w = (usable_w - (cols - 1) * GUTTER) / cols
    cell_h = (usable_h - (rows - 1) * GUTTER) / rows

    page_num = 1
    i = 0

    hole_r = 4 * mm

    while i < len(assets):
        draw_title(c, theme, "Lanyard Characters (hole-punch indicator)")
        y_top = PAGE_H - MARGIN - 18 * mm

        for r in range(rows):
            for col in range(cols):
                if i >= len(assets):
                    break

                x = MARGIN + col * (cell_w + GUTTER)
                y = y_top - (r + 1) * cell_h - r * GUTTER

                # Card border
                c.setLineWidth(2)
                c.roundRect(x, y, cell_w, cell_h, 10)

                # Hole punch indicator
                hole_x = x + cell_w / 2.0
                hole_y = y + cell_h - 10 * mm
                c.setLineWidth(1.5)
                c.circle(hole_x, hole_y, hole_r)

                # Image box
                box_x = x + 6 * mm
                box_y = y + 10 * mm
                box_w = cell_w - 12 * mm
                box_h = cell_h - 26 * mm  # leave space for hole area

                img = open_character_image(assets[i], mode=mode, add_outline=False)
                scaled = scale_image_proportional(img, int(box_w), int(box_h))
                ir = pil_to_imagereader(scaled)

                img_x, img_y = center_image_in_box(box_x, box_y, box_w, box_h, scaled.width, scaled.height)
                c.drawImage(ir, img_x, img_y, width=scaled.width, height=scaled.height, mask="auto")

                draw_cut_label(c, x, y + cell_h - 6 * mm, assets[i].name)
                i += 1

            if i >= len(assets):
                break

        add_footer(c, brand, theme, mode, page_num)
        c.showPage()
        page_num += 1


# =========================
# Dual-mode wrapper
# =========================

def generate_puppet_characters_for_mode(
    assets: List[CharacterAsset],
    out_dir: Path,
    theme: str,
    brand: str,
    mode: str,
) -> None:
    """
    Generates all 5 puppet resource PDFs for a given mode.
    mode: "color" or "bw"
    """
    base = safe_filename(theme)

    # 1) Stick puppets
    out_path = out_dir / f"{base}_stick_puppets_{mode}.pdf"
    c = create_page_canvas(out_path, mode=mode)
    generate_stick_puppets(c, assets, theme, brand, mode)
    c.save()
    print(f"  ✓ Generated: {out_path}")

    # 2) Finger puppets
    out_path = out_dir / f"{base}_finger_puppets_{mode}.pdf"
    c = create_page_canvas(out_path, mode=mode)
    generate_finger_puppets(c, assets, theme, brand, mode)
    c.save()
    print(f"  ✓ Generated: {out_path}")

    # 3) Velcro cards
    out_path = out_dir / f"{base}_velcro_cards_{mode}.pdf"
    c = create_page_canvas(out_path, mode=mode)
    generate_velcro_cards(c, assets, theme, brand, mode)
    c.save()
    print(f"  ✓ Generated: {out_path}")

    # 4) Story mat
    out_path = out_dir / f"{base}_story_mat_{mode}.pdf"
    c = create_page_canvas(out_path, mode=mode)
    generate_story_mat(c, assets, theme, brand, mode)
    c.save()
    print(f"  ✓ Generated: {out_path}")

    # 5) Lanyard characters
    out_path = out_dir / f"{base}_lanyard_characters_{mode}.pdf"
    c = create_page_canvas(out_path, mode=mode)
    generate_lanyard_characters(c, assets, theme, brand, mode)
    c.save()
    print(f"  ✓ Generated: {out_path}")


def generate_puppet_characters_dual_mode(
    icons_dir: Path,
    out_dir: Path,
    theme: str,
    brand: str,
) -> None:
    """
    Generates both colour and B/W outputs.
    """
    assets = load_character_assets(icons_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"  Puppet Characters Generator - {theme}")
    print(f"  Found {len(assets)} character icons")
    print(f"{'='*70}\n")

    for mode in ("color", "bw"):
        print(f"Generating {mode.upper()} mode PDFs...")
        generate_puppet_characters_for_mode(
            assets=assets,
            out_dir=out_dir,
            theme=theme,
            brand=brand,
            mode=mode,
        )
        print()

    print(f"{'='*70}")
    print(f"  All Done! PDFs saved to: {out_dir}")
    print(f"{'='*70}\n")


# =========================
# CLI
# =========================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate Puppet Character resources (dual-mode) from Boardmaker icons.")
    p.add_argument("--icons_dir", type=str, required=True, help="Folder of character icons (PNG recommended).")
    p.add_argument("--out_dir", type=str, required=True, help="Output folder for PDFs.")
    p.add_argument("--theme", type=str, required=True, help="Theme name (used in titles + filenames).")
    p.add_argument("--brand", type=str, default="Small Wins Studio", help="Brand name for footer.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    icons_dir = Path(args.icons_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()

    generate_puppet_characters_dual_mode(
        icons_dir=icons_dir,
        out_dir=out_dir,
        theme=args.theme,
        brand=args.brand,
    )


if __name__ == "__main__":
    main()
