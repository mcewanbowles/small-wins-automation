"""
Adapted Reader Generator (Dual Mode: Color + B/W)

Creates two reading levels:
- Level A: Errorless (read + point to target word icon)
- Level B: Cloze (fill in blank, choose from 3-4 icons)

Inputs:
- Folder of Boardmaker icons (PNG recommended)
- Optional: JSON manifest with sentences, target words, distractors

Outputs (per level, per mode):
- Level A Color/BW PDFs
- Level B Color/BW PDFs

Usage:
python generators/adapted_reader/adapted_reader.py \
    --icons_dir "assets/themes/brown_bear/icons" \
    --out_dir "OUTPUT/readers" \
    --theme "Brown Bear"

With manifest:
python generators/adapted_reader/adapted_reader.py \
    --icons_dir "assets/themes/brown_bear/icons" \
    --out_dir "OUTPUT/readers" \
    --theme "Brown Bear" \
    --manifest "templates/adapted_reader_manifest.json"

Dependencies:
pip install reportlab pillow
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Dict

from PIL import Image, ImageOps, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# =========================
# Constants / Config
# =========================

PAGE_W, PAGE_H = A4  # points
MARGIN = 15 * mm
FONT_NAME = "Helvetica"
FONT_NAME_BOLD = "Helvetica-Bold"


# =========================
# Utilities: filenames
# =========================

def safe_filename(text: str) -> str:
    """Convert text to safe filename."""
    t = text.strip().lower()
    t = re.sub(r"[^a-z0-9]+", "_", t)
    t = re.sub(r"_+", "_", t).strip("_")
    return t or "output"


# =========================
# Utilities: images
# =========================

def image_to_grayscale(img: Image.Image) -> Image.Image:
    """Convert image to grayscale while preserving alpha."""
    if img.mode not in ("RGBA", "LA"):
        img = img.convert("RGBA")
    rgba = img.convert("RGBA")
    r, g, b, a = rgba.split()
    gray = ImageOps.grayscale(Image.merge("RGB", (r, g, b)))
    gray_rgb = Image.merge("RGB", (gray, gray, gray))
    return Image.merge("RGBA", (*gray_rgb.split(), a))


def scale_image_proportional(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Proportionally scale image to fit inside target dimensions."""
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
    """Calculate position to center image in box."""
    x = box_x + (box_w - img_w) / 2.0
    y = box_y + (box_h - img_h) / 2.0
    return x, y


def pil_to_imagereader(img: Image.Image) -> ImageReader:
    """Convert PIL Image to ReportLab ImageReader."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


# =========================
# Utilities: PDF layout
# =========================

def create_page_canvas(out_path: Path, mode: str) -> canvas.Canvas:
    """Create a reportlab Canvas with standard settings."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_path), pagesize=A4)
    c.setAuthor("Small Wins Studio")
    c.setTitle(f"Adapted Reader ({mode})")
    c.setFont(FONT_NAME, 10)
    return c


def add_footer(c: canvas.Canvas, brand: str, theme: str, level: str, mode: str, page_num: int) -> None:
    """Standard footer for all pages."""
    footer_y = 8 * mm
    c.setFont(FONT_NAME, 8)
    left = MARGIN
    right = PAGE_W - MARGIN

    c.drawString(left, footer_y, f"{brand} | {theme} | {level} | {mode.upper()}")
    c.drawRightString(right, footer_y, f"Page {page_num}")
    c.setFont(FONT_NAME, 10)


def draw_title(c: canvas.Canvas, theme: str, level: str) -> float:
    """Draw title and return y position after title."""
    y = PAGE_H - MARGIN - 5 * mm
    c.setFont(FONT_NAME_BOLD, 18)
    c.drawString(MARGIN, y, f"{theme}")
    
    y -= 8 * mm
    c.setFont(FONT_NAME_BOLD, 14)
    c.drawString(MARGIN, y, level)
    
    c.setFont(FONT_NAME, 10)
    return y - 8 * mm


# =========================
# Model
# =========================

@dataclass(frozen=True)
class IconAsset:
    """Represents an icon file."""
    name: str
    display_name: str
    path: Path


@dataclass
class ReaderPage:
    """Represents one page of adapted reader."""
    sentence: str
    target_word: str
    target_icon: str
    distractors: List[str]  # For Level B only


def load_icon_assets(icons_dir: Path) -> Dict[str, IconAsset]:
    """Load all icon assets from directory."""
    if not icons_dir.exists():
        raise FileNotFoundError(f"icons_dir not found: {icons_dir}")

    exts = {".png", ".jpg", ".jpeg", ".webp"}
    files = [p for p in icons_dir.iterdir() if p.is_file() and p.suffix.lower() in exts]

    assets: Dict[str, IconAsset] = {}
    for p in files:
        name = p.stem.lower().replace(" ", "_")
        display_name = p.stem.replace("_", " ").title()
        assets[name] = IconAsset(name=name, display_name=display_name, path=p)

    if not assets:
        raise ValueError(f"No image files found in: {icons_dir}")

    return assets


def load_manifest(manifest_path: Path) -> List[ReaderPage]:
    """Load reader pages from JSON manifest."""
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    pages = []
    for page_data in data.get("pages", []):
        pages.append(ReaderPage(
            sentence=page_data["sentence"],
            target_word=page_data["target_word"],
            target_icon=page_data["target_icon"],
            distractors=page_data.get("distractors", [])
        ))
    
    return pages


def generate_default_pages(assets: Dict[str, IconAsset]) -> List[ReaderPage]:
    """Generate default reader pages from available icons."""
    pages = []
    
    # Brown Bear story sequence if available
    brown_bear_sequence = [
        ("red_bird", "Red Bird", ["yellow_duck", "blue_horse"]),
        ("yellow_duck", "Yellow Duck", ["red_bird", "green_frog"]),
        ("blue_horse", "Blue Horse", ["yellow_duck", "purple_cat"]),
        ("green_frog", "Green Frog", ["blue_horse", "white_dog"]),
        ("purple_cat", "Purple Cat", ["green_frog", "black_sheep"]),
        ("white_dog", "White Dog", ["purple_cat", "goldfish"]),
        ("black_sheep", "Black Sheep", ["white_dog", "teacher"]),
        ("goldfish", "Goldfish", ["black_sheep", "children"]),
        ("teacher", "Teacher", ["goldfish", "children"]),
        ("children", "Children", ["teacher", "red_bird"]),
    ]
    
    # Try to use Brown Bear sequence
    for icon_name, display_name, distractors in brown_bear_sequence:
        if icon_name in assets:
            sentence = f"I see a {display_name}."
            available_distractors = [d for d in distractors if d in assets]
            pages.append(ReaderPage(
                sentence=sentence,
                target_word=display_name,
                target_icon=icon_name,
                distractors=available_distractors[:2]  # Use up to 2 distractors
            ))
    
    # If no pages created, create generic pages
    if not pages:
        icon_list = list(assets.values())[:10]  # Use first 10 icons
        for i, asset in enumerate(icon_list):
            # Create simple sentence
            sentence = f"This is a {asset.display_name}."
            
            # Pick random distractors
            other_icons = [a for a in icon_list if a.name != asset.name]
            distractors = [a.name for a in other_icons[:2]]
            
            pages.append(ReaderPage(
                sentence=sentence,
                target_word=asset.display_name,
                target_icon=asset.name,
                distractors=distractors
            ))
    
    return pages


def open_icon_image(asset: IconAsset, mode: str) -> Image.Image:
    """Open and process icon image."""
    img = Image.open(asset.path).convert("RGBA")
    if mode == "bw":
        img = image_to_grayscale(img)
    return img


# =========================
# Level A: Errorless (Read + Point)
# =========================

def generate_level_a_page(c: canvas.Canvas, page: ReaderPage, assets: Dict[str, IconAsset],
                          mode: str, page_num: int, y_start: float) -> None:
    """Generate one Level A page (errorless reading)."""
    
    # Instruction
    y = y_start - 10 * mm
    c.setFont(FONT_NAME_BOLD, 12)
    c.drawString(MARGIN, y, f"Read the sentence. Point to the {page.target_word}.")
    
    # Sentence box
    y -= 15 * mm
    sentence_box_h = 30 * mm
    c.setLineWidth(2)
    c.setStrokeColorRGB(0.2, 0.3, 0.5)  # Navy blue
    c.rect(MARGIN, y - sentence_box_h, PAGE_W - 2 * MARGIN, sentence_box_h)
    
    # Sentence text with icon inline
    c.setFont(FONT_NAME, 16)
    text_y = y - sentence_box_h / 2 - 3 * mm
    
    # Replace target word with [ICON]
    sentence_parts = page.sentence.replace(page.target_word, "[ICON]").split("[ICON]")
    
    text_x = MARGIN + 10 * mm
    if len(sentence_parts) > 0:
        c.drawString(text_x, text_y, sentence_parts[0])
        text_x += c.stringWidth(sentence_parts[0], FONT_NAME, 16)
    
    # Draw icon inline
    if page.target_icon in assets:
        asset = assets[page.target_icon]
        img = open_icon_image(asset, mode)
        icon_size = 20 * mm
        scaled = scale_image_proportional(img, int(icon_size), int(icon_size))
        ir = pil_to_imagereader(scaled)
        
        icon_y = text_y - 3 * mm
        c.drawImage(ir, text_x, icon_y, width=scaled.width, height=scaled.height, mask="auto")
        text_x += scaled.width + 5 * mm
    
    if len(sentence_parts) > 1:
        c.drawString(text_x, text_y, sentence_parts[1])
    
    # Large target icon below
    y -= sentence_box_h + 20 * mm
    icon_box_size = 80 * mm
    
    if page.target_icon in assets:
        asset = assets[page.target_icon]
        img = open_icon_image(asset, mode)
        scaled = scale_image_proportional(img, int(icon_box_size), int(icon_box_size))
        ir = pil_to_imagereader(scaled)
        
        box_x = (PAGE_W - icon_box_size) / 2
        box_y = y - icon_box_size
        
        # Border around icon
        c.setLineWidth(3)
        c.setStrokeColorRGB(0.2, 0.3, 0.5)
        c.rect(box_x, box_y, icon_box_size, icon_box_size)
        
        img_x, img_y = center_image_in_box(box_x, box_y, icon_box_size, icon_box_size,
                                           scaled.width, scaled.height)
        c.drawImage(ir, img_x, img_y, width=scaled.width, height=scaled.height, mask="auto")
        
        # Label below
        y = box_y - 8 * mm
        c.setFont(FONT_NAME_BOLD, 14)
        label_w = c.stringWidth(page.target_word, FONT_NAME_BOLD, 14)
        c.drawString((PAGE_W - label_w) / 2, y, page.target_word)


def generate_level_a(c: canvas.Canvas, pages: List[ReaderPage], assets: Dict[str, IconAsset],
                     theme: str, brand: str, mode: str) -> None:
    """Generate complete Level A PDF."""
    
    for page_num, page in enumerate(pages, 1):
        y_start = draw_title(c, theme, "Level A - Errorless Reading (Point to the word)")
        generate_level_a_page(c, page, assets, mode, page_num, y_start)
        add_footer(c, brand, theme, "Level A", mode, page_num)
        c.showPage()


# =========================
# Level B: Cloze (Fill in blank)
# =========================

def generate_level_b_page(c: canvas.Canvas, page: ReaderPage, assets: Dict[str, IconAsset],
                          mode: str, page_num: int, y_start: float) -> None:
    """Generate one Level B page (cloze with choices)."""
    
    # Instruction
    y = y_start - 10 * mm
    c.setFont(FONT_NAME_BOLD, 12)
    c.drawString(MARGIN, y, "Read the sentence. Choose the correct word to fill in the blank.")
    
    # Sentence box with blank
    y -= 15 * mm
    sentence_box_h = 30 * mm
    c.setLineWidth(2)
    c.setStrokeColorRGB(0.2, 0.3, 0.5)
    c.rect(MARGIN, y - sentence_box_h, PAGE_W - 2 * MARGIN, sentence_box_h)
    
    # Sentence text with blank
    c.setFont(FONT_NAME, 16)
    text_y = y - sentence_box_h / 2 - 3 * mm
    
    sentence_with_blank = page.sentence.replace(page.target_word, "_________")
    text_x = MARGIN + 10 * mm
    c.drawString(text_x, text_y, sentence_with_blank)
    
    # Choice icons (3-4 icons including target + distractors)
    y -= sentence_box_h + 15 * mm
    
    choices = [page.target_icon] + page.distractors[:2]  # Target + up to 2 distractors
    # Shuffle for Level B (but keep deterministic for testing)
    random.seed(page_num)  # Deterministic shuffle based on page number
    random.shuffle(choices)
    
    choice_count = len(choices)
    icon_size = 60 * mm
    spacing = 15 * mm
    total_w = choice_count * icon_size + (choice_count - 1) * spacing
    start_x = (PAGE_W - total_w) / 2
    
    for i, choice_name in enumerate(choices):
        if choice_name not in assets:
            continue
        
        asset = assets[choice_name]
        img = open_icon_image(asset, mode)
        scaled = scale_image_proportional(img, int(icon_size), int(icon_size))
        ir = pil_to_imagereader(scaled)
        
        box_x = start_x + i * (icon_size + spacing)
        box_y = y - icon_size
        
        # Border
        c.setLineWidth(2)
        c.setStrokeColorRGB(0.2, 0.3, 0.5)
        c.rect(box_x, box_y, icon_size, icon_size)
        
        img_x, img_y = center_image_in_box(box_x, box_y, icon_size, icon_size,
                                           scaled.width, scaled.height)
        c.drawImage(ir, img_x, img_y, width=scaled.width, height=scaled.height, mask="auto")
        
        # Label below
        label_y = box_y - 6 * mm
        c.setFont(FONT_NAME, 11)
        label_w = c.stringWidth(asset.display_name, FONT_NAME, 11)
        c.drawString(box_x + (icon_size - label_w) / 2, label_y, asset.display_name)


def generate_level_b(c: canvas.Canvas, pages: List[ReaderPage], assets: Dict[str, IconAsset],
                     theme: str, brand: str, mode: str) -> None:
    """Generate complete Level B PDF."""
    
    for page_num, page in enumerate(pages, 1):
        y_start = draw_title(c, theme, "Level B - Cloze Reading (Fill in the blank)")
        generate_level_b_page(c, page, assets, mode, page_num, y_start)
        add_footer(c, brand, theme, "Level B", mode, page_num)
        c.showPage()


# =========================
# Dual-mode wrapper
# =========================

def generate_adapted_reader_for_mode(
    pages: List[ReaderPage],
    assets: Dict[str, IconAsset],
    out_dir: Path,
    theme: str,
    brand: str,
    mode: str,
) -> None:
    """Generate both Level A and Level B PDFs for a given mode."""
    base = safe_filename(theme)
    
    # Level A
    out_path = out_dir / f"{base}_adapted_reader_level_a_{mode}.pdf"
    c = create_page_canvas(out_path, mode=mode)
    generate_level_a(c, pages, assets, theme, brand, mode)
    c.save()
    print(f"  ✓ Generated: {out_path.name}")
    
    # Level B
    out_path = out_dir / f"{base}_adapted_reader_level_b_{mode}.pdf"
    c = create_page_canvas(out_path, mode=mode)
    generate_level_b(c, pages, assets, theme, brand, mode)
    c.save()
    print(f"  ✓ Generated: {out_path.name}")


def generate_adapted_reader_dual_mode(
    icons_dir: Path,
    out_dir: Path,
    theme: str,
    brand: str,
    manifest_path: Optional[Path] = None,
) -> None:
    """Generate both color and B/W outputs for both levels."""
    
    # Load icons
    assets = load_icon_assets(icons_dir)
    print(f"Loaded {len(assets)} icons from {icons_dir}")
    
    # Load or generate pages
    if manifest_path and manifest_path.exists():
        pages = load_manifest(manifest_path)
        print(f"Loaded {len(pages)} pages from manifest: {manifest_path}")
    else:
        pages = generate_default_pages(assets)
        print(f"Generated {len(pages)} default pages from icons")
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate both modes
    for mode in ("color", "bw"):
        print(f"\nGenerating {mode.upper()} mode:")
        generate_adapted_reader_for_mode(
            pages=pages,
            assets=assets,
            out_dir=out_dir,
            theme=theme,
            brand=brand,
            mode=mode,
        )


# =========================
# CLI
# =========================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate Adapted Reader resources (dual-mode, two levels) from Boardmaker icons."
    )
    p.add_argument("--icons_dir", type=str, required=True,
                   help="Folder of icon images (PNG recommended).")
    p.add_argument("--out_dir", type=str, required=True,
                   help="Output folder for PDFs.")
    p.add_argument("--theme", type=str, required=True,
                   help="Theme name (e.g., 'Brown Bear').")
    p.add_argument("--brand", type=str, default="Small Wins Studio",
                   help="Brand name for footer.")
    p.add_argument("--manifest", type=str, default=None,
                   help="Optional JSON manifest with page definitions.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    icons_dir = Path(args.icons_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else None
    
    print(f"\n{'='*70}")
    print(f"  ADAPTED READER GENERATOR")
    print(f"{'='*70}")
    print(f"Theme: {args.theme}")
    print(f"Icons: {icons_dir}")
    print(f"Output: {out_dir}")
    if manifest_path:
        print(f"Manifest: {manifest_path}")
    print(f"{'='*70}\n")
    
    generate_adapted_reader_dual_mode(
        icons_dir=icons_dir,
        out_dir=out_dir,
        theme=args.theme,
        brand=args.brand,
        manifest_path=manifest_path,
    )
    
    print(f"\n{'='*70}")
    print(f"  ✓ COMPLETE!")
    print(f"  PDFs saved to: {out_dir}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
