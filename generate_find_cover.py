#!/usr/bin/env python3
"""
Generate Find & Cover Level PDFs for Brown Bear theme.
Produces all 4 levels in both color and BW versions.
Uses Matching Product Spec design elements.
"""

import os
import sys
import json
import io
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import random

# Try to register Comic Sans MS (Windows). Fall back to Helvetica if unavailable.
try:
    pdfmetrics.registerFont(TTFont('Comic-Sans-MS', 'C:/Windows/Fonts/comic.ttf'))
    pdfmetrics.registerFont(TTFont('Comic-Sans-MS-Bold', 'C:/Windows/Fonts/comicbd.ttf'))
    TITLE_FONT = 'Comic-Sans-MS-Bold'
    BODY_FONT = 'Comic-Sans-MS'
except Exception:
    TITLE_FONT = 'Helvetica-Bold'
    BODY_FONT = 'Helvetica'

# Page settings
PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.5 * inch

# Matching Product Spec Colors
LIGHT_BLUE_BORDER = '#A0C4E8'  # Light blue border for pages
NAVY_BORDER = '#1E3A5F'  # Navy border for target and boxes
WHITE = '#FFFFFF'
BLACK = '#000000'

_THEME_ID = "brown_bear"


def _theme_path() -> Path:
    return Path(__file__).parent / "themes" / f"{_THEME_ID}.json"


def _load_find_cover_theme_levels() -> dict[int, dict]:
    p = _theme_path()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        levels = (data.get("find_cover") or {}).get("levels") or {}
        out: dict[int, dict] = {}
        for k, v in levels.items():
            if isinstance(k, str) and k.upper().startswith("L"):
                try:
                    n = int(k[1:])
                except Exception:
                    continue
                if isinstance(v, dict):
                    out[n] = v
        return out
    except Exception:
        return {}


_FIND_COVER_THEME_LEVELS = _load_find_cover_theme_levels()


def _level_name(level: int) -> str:
    meta = _FIND_COVER_THEME_LEVELS.get(level) or {}
    name = meta.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return {1: "Errorless", 2: "Supported", 3: "Independent", 4: "Generalisation", 5: "Extension"}.get(
        level, f"Level {level}"
    )


def _level_colour(level: int) -> str:
    meta = _FIND_COVER_THEME_LEVELS.get(level) or {}
    colour = meta.get("colour")
    if isinstance(colour, str) and colour.strip().startswith("#") and len(colour.strip()) == 7:
        return colour.strip()
    return {1: "#F4B400", 2: "#4285F4", 3: "#34A853", 4: "#8C06F2", 5: "#EA4335"}.get(level, "#F4B400")


_COLOUR_PREFIXES = {
    'black', 'white', 'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown', 'grey', 'gray'
}


def _strip_colour_prefix(label: str) -> str:
    parts = [p for p in str(label).strip().split() if p]
    if len(parts) >= 2 and parts[0].lower() in _COLOUR_PREFIXES:
        return " ".join(parts[1:])
    return " ".join(parts)

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def load_brown_bear_icons():
    """Load all Brown Bear icons."""
    theme_root = Path(__file__).parent / 'assets' / 'themes' / 'brown_bear'
    icons_colored = theme_root / 'icons_colored'
    legacy_icons = theme_root / 'icons'
    icon_folder = icons_colored if icons_colored.exists() else legacy_icons
    icons = []
    
    if not icon_folder.exists():
        print(f"Warning: Icon folder not found: {icon_folder}")
        return icons
    
    for png_file in sorted(icon_folder.glob('*.png')):
        if png_file.name.startswith('.'):
            continue
        name = png_file.stem.replace('_', ' ').title()
        icons.append({
            'path': str(png_file),
            'name': name
        })
    
    return icons


def generate_cutout_pieces_page(c, icons, level, page_num, total_pages, mode='color', pack_code="BB-FC", page_number=1, icons_on_page=None):
    """Generate a cutout pieces page matching the Matching cutout style.

    Layout: 6 columns x 5 rows = 30 boxes per page.
    Each column contains 5 copies of the same icon.
    ``icons_on_page`` is a list of icon dicts for the 6 icons on this page.
    """
    if icons_on_page is None:
        icons_on_page = icons[:6]

    width, height = letter
    c.setPageSize(letter)

    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, width, height, fill=True, stroke=False)

    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin

    r, g, b = hex_to_rgb(LIGHT_BLUE_BORDER)
    c.setStrokeColorRGB(r, g, b)
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)

    # Accent stripe
    accent_margin = 0.08 * inch
    accent_height = 1.0 * inch
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin

    if mode == 'bw':
        c.setFillColorRGB(0.7, 0.7, 0.7)
    else:
        c.setFillColorRGB(*hex_to_rgb(_level_colour(level)))
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)

    # Title
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))
    c.setFont(TITLE_FONT, 28)
    title_y = accent_y + accent_height / 2 + 10
    c.drawCentredString(width / 2, title_y, "Cut Out Find & Cover Pieces")

    # Subtitle
    c.setFont(BODY_FONT, 20)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawCentredString(width / 2, title_y - 32, "Brown Bear")

    # 6x5 grid matching the Matching cutout layout
    box_size = 1.28 * inch
    icon_size = box_size * 0.97
    spacing = 0.05 * inch
    border_pts = 4

    cols = 6
    rows = 5

    grid_width = cols * box_size + (cols - 1) * spacing
    grid_height = rows * box_size + (rows - 1) * spacing

    start_x = (width - grid_width) / 2
    content_top = accent_y - 0.4 * inch
    start_y = content_top - 0.3 * inch

    icon_idx = 0
    for col in range(cols):
        if icon_idx >= len(icons_on_page):
            break
        icon_dict = icons_on_page[icon_idx]

        for row in range(rows):
            box_x = start_x + col * (box_size + spacing)
            box_y = start_y - row * (box_size + spacing) - box_size

            c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
            c.setLineWidth(border_pts)
            c.roundRect(box_x, box_y, box_size, box_size, 8.64, stroke=1, fill=0)

            try:
                img = Image.open(icon_dict['path'])
                if mode == 'bw':
                    img = img.convert('L').convert('RGB')
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                buf.seek(0)
                icon_padding = (box_size - icon_size) / 2
                c.drawImage(
                    ImageReader(buf),
                    box_x + icon_padding,
                    box_y + icon_padding,
                    width=icon_size,
                    height=icon_size,
                    preserveAspectRatio=True,
                    mask='auto',
                )
            except Exception:
                pass

        icon_idx += 1

    # Footer - Gold standard (matches Bingo / apply_small_wins_frame)
    footer_y = border_margin + 0.26 * inch
    c.setFont(BODY_FONT, 9)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line2 = "Small Wins Studio | PCS symbols used with active PCS Maker Personal License. | \u00a9 2026"
    c.drawCentredString(width/2, footer_y, footer_line2)

    c.setFont(TITLE_FONT, 10)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line1 = f"Brown Bear Find & Cover | Level {level} | {pack_code} | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y + 12, footer_line1)

    c.showPage()

def generate_find_cover_page(c, target_icon, all_icons, level, page_num, total_pages, mode='color', pack_code="BB-FC"):
    """Generate a single Find & Cover page with Matching design spec."""
    
    width, height = letter
    
    # Page setup
    c.setPageSize(letter)
    
    # Background white
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Page Structure - 0.25" margin from edge (matching Matching spec)
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    # Draw rounded rectangle border (3px stroke) - LIGHT BLUE per spec
    r, g, b = hex_to_rgb(LIGHT_BLUE_BORDER)
    c.setStrokeColorRGB(r, g, b)
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent Stripe with level color and rounded corners
    accent_margin = 0.08 * inch
    accent_height = 1.0 * inch
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin
    
    # Use level-specific color for accent stripe
    level_color = _level_colour(level)
    if mode == 'bw':
        c.setFillColorRGB(0.7, 0.7, 0.7)
    else:
        r, g, b = hex_to_rgb(level_color)
        c.setFillColorRGB(r, g, b)
    
    # Draw accent stripe with rounded corners
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Title and Subtitle inside accent stripe
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))  # Navy
    c.setFont(TITLE_FONT, 36)
    title_y = accent_y + accent_height / 2 + 5
    c.drawCentredString(width / 2, title_y, "Find & Cover")
    
    # Subtitle: "Brown Bear"
    c.setFont(BODY_FONT, 28)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    subtitle_y = title_y - 30
    c.drawCentredString(width / 2, subtitle_y, "Brown Bear")
    
    # Target box - navy border with rounded corners
    target_box_y = accent_y - 150
    target_box_size = 100
    target_box_x = width/2 - target_box_size/2
    
    # Navy border for target box
    r, g, b = hex_to_rgb(NAVY_BORDER)
    c.setStrokeColorRGB(r, g, b)
    c.setLineWidth(3.5)
    c.roundRect(target_box_x, target_box_y, target_box_size, target_box_size, 8, fill=False, stroke=True)
    
    # Draw target icon
    try:
        img = Image.open(target_icon['path'])
        if mode == 'bw':
            img = img.convert('L').convert('RGB')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        c.drawImage(ImageReader(buf), target_box_x + 10, target_box_y + 10, 
                   width=target_box_size - 20, height=target_box_size - 20,
                   preserveAspectRatio=True, mask='auto')
    except Exception as e:
        # Draw placeholder text
        c.setFont(BODY_FONT, 12)
        c.drawCentredString(target_box_x + target_box_size/2, target_box_y + target_box_size/2, target_icon['name'][:10])
    
    # Label under target
    c.setFont(BODY_FONT, 12)
    c.setFillColorRGB(0, 0, 0)
    target_label = _strip_colour_prefix(target_icon['name'])
    c.drawCentredString(width/2, target_box_y - 20, f"Find the {target_label}")
    
    # Instruction
    c.setFont(TITLE_FONT, 14)
    c.drawCentredString(width/2, target_box_y - 45, "Cover all matching pictures")
    
    # Grid area
    grid_start_y = target_box_y - 80
    grid_rows = 4
    grid_cols = 4
    cell_size = 100
    grid_width = grid_cols * cell_size
    grid_height = grid_rows * cell_size
    grid_start_x = width/2 - grid_width/2
    
    # Generate grid content based on level
    total_cells = grid_rows * grid_cols
    grid_content = []
    
    if level == 1:
        # Errorless: All match target (100% success)
        grid_content = [target_icon] * total_cells
    elif level == 2:
        # Easy: 50% match, 50% distractors
        num_matches = total_cells // 2
        grid_content = [target_icon] * num_matches
        distractors = [icon for icon in all_icons if icon['name'] != target_icon['name']]
        while len(grid_content) < total_cells and distractors:
            grid_content.append(random.choice(distractors))
    elif level == 3:
        # Medium: ~30% match, ~70% distractors
        num_matches = total_cells // 3
        grid_content = [target_icon] * num_matches
        distractors = [icon for icon in all_icons if icon['name'] != target_icon['name']]
        while len(grid_content) < total_cells and distractors:
            grid_content.append(random.choice(distractors))
    elif level == 4:
        # Challenge: Only 1-2 matches among many distractors
        num_matches = max(1, total_cells // 8)  # Only 1-2 matches
        grid_content = [target_icon] * num_matches
        distractors = [icon for icon in all_icons if icon['name'] != target_icon['name']]
        while len(grid_content) < total_cells and distractors:
            grid_content.append(random.choice(distractors))
    # Level 5 uses the same icon-based logic (Extension).
    
    # Fill remaining with distractors if needed
    distractors = [icon for icon in all_icons if icon['name'] != target_icon['name']]
    while len(grid_content) < total_cells:
        if distractors:
            grid_content.append(random.choice(distractors))
        else:
            grid_content.append(target_icon)
    
    # Shuffle all levels
    random.shuffle(grid_content)
    
    # Draw grid with navy borders and rounded corners
    for row in range(grid_rows):
        for col in range(grid_cols):
            idx = row * grid_cols + col
            x = grid_start_x + col * cell_size
            y = grid_start_y - (row + 1) * cell_size
            
            # Navy border for grid cells
            r, g, b = hex_to_rgb(NAVY_BORDER)
            c.setStrokeColorRGB(r, g, b)
            c.setLineWidth(2)
            
            # Rounded rect for grid cells (all levels including Level 4)
            c.roundRect(x + 2, y + 2, cell_size - 4, cell_size - 4, 6, fill=False, stroke=True)
            
            # Draw icon
            icon = grid_content[idx]
            if icon:
                try:
                    img = Image.open(icon['path'])
                    if mode == 'bw':
                        img = img.convert('L').convert('RGB')
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    buf.seek(0)
                    c.drawImage(ImageReader(buf), x + 8, y + 8,
                               width=cell_size - 16, height=cell_size - 16,
                               preserveAspectRatio=True, mask='auto')
                except Exception as e:
                    pass
    
    # Footer - Gold standard (matches Matching cover / apply_small_wins_frame)
    footer_y = border_margin + 0.26 * inch
    
    c.setFont(BODY_FONT, 9)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line2 = "Small Wins Studio | PCS symbols used with active PCS Maker Personal License. | © 2026"
    c.drawCentredString(width/2, footer_y, footer_line2)
    
    c.setFont(TITLE_FONT, 10)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line1 = f"Brown Bear Find & Cover | Level {level} | {pack_code} | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y + 12, footer_line1)
    
    c.showPage()

def generate_find_cover_pdf(output_path, level, mode='color'):
    """Generate a Find & Cover PDF for a specific level."""
    
    icons = load_brown_bear_icons()
    if not icons:
        print(f"No icons found, cannot generate PDF")
        return None
    
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    # 12 activity pages + 2 cutout pages (matching style: 6 icons per page)
    total_pages = len(icons) + 2
    
    # Generate pages for each target
    random.seed(42)  # Reproducible randomness
    for i, target_icon in enumerate(icons):
        generate_find_cover_page(c, target_icon, icons, level, i+1, total_pages, mode)

    # Cutout page 1: first 6 icons
    generate_cutout_pieces_page(c, icons, level, len(icons) + 1, total_pages, mode,
                                page_number=1, icons_on_page=icons[:6])
    # Cutout page 2: next 6 icons
    generate_cutout_pieces_page(c, icons, level, len(icons) + 2, total_pages, mode,
                                page_number=2, icons_on_page=icons[6:12])
    
    c.save()
    print(f"OK Generated: {output_path}")
    return output_path

def generate_storage_labels_page(c, icons, level, mode='color', pack_code="BB-FC"):
    """Generate a storage labels page for Find & Cover."""
    
    width, height = letter
    c.setPageSize(letter)
    
    # Background white
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Page border
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    r, g, b = hex_to_rgb(LIGHT_BLUE_BORDER)
    c.setStrokeColorRGB(r, g, b)
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent stripe at top
    accent_margin = 0.08 * inch
    accent_height = 0.8 * inch
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin
    
    # Use level-specific color for accent stripe
    level_color = _level_colour(level)
    if mode == 'bw':
        c.setFillColorRGB(0.7, 0.7, 0.7)
    else:
        r, g, b = hex_to_rgb(level_color)
        c.setFillColorRGB(r, g, b)
    
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Page title
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))
    c.setFont(TITLE_FONT, 28)
    title_y = accent_y + accent_height / 2 + 5
    c.drawCentredString(width / 2, title_y, "Storage Labels")
    
    # Subtitle
    c.setFont(BODY_FONT, 20)
    subtitle_y = title_y - 30
    c.drawCentredString(width / 2, subtitle_y, f"Find & Cover – Level {level}: {_level_name(level)}")
    
    # Storage label boxes - 3 columns × 4 rows = 12 boxes
    cols = 3
    rows = 4
    
    box_width = 2.2 * inch
    box_height = 1.4 * inch
    h_spacing = 0.2 * inch
    v_spacing = 0.15 * inch
    
    # Calculate grid position
    grid_width = cols * box_width + (cols - 1) * h_spacing
    grid_height = rows * box_height + (rows - 1) * v_spacing
    start_x = (width - grid_width) / 2
    start_y = accent_y - 0.4 * inch - grid_height
    
    # Draw storage label boxes
    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            if idx >= len(icons):
                continue
            
            icon = icons[idx]
            
            box_x = start_x + col * (box_width + h_spacing)
            box_y = start_y + (rows - 1 - row) * (box_height + v_spacing)
            
            # Box background
            c.setFillColorRGB(0.98, 0.98, 0.98)
            c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
            c.setLineWidth(1.5)
            c.roundRect(box_x, box_y, box_width, box_height, 6, stroke=1, fill=1)
            
            # Level color strip on left
            strip_width = 0.15 * inch
            if mode == 'bw':
                c.setFillColorRGB(0.5, 0.5, 0.5)
            else:
                c.setFillColorRGB(*hex_to_rgb(level_color))
            c.roundRect(box_x, box_y, strip_width, box_height, 6, stroke=0, fill=1)
            c.rect(box_x + strip_width/2, box_y, strip_width/2, box_height, stroke=0, fill=1)
            
            # Product name
            c.setFillColorRGB(0, 0, 0)
            c.setFont(TITLE_FONT, 10)
            c.drawString(box_x + strip_width + 5, box_y + box_height - 15, "Find & Cover")
            
            # Theme and pack code
            c.setFont(BODY_FONT, 8)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(box_x + strip_width + 5, box_y + box_height - 26, f"Brown Bear | {pack_code}")
            
            # Level indicator
            c.setFont(TITLE_FONT, 8)
            c.drawString(box_x + strip_width + 5, box_y + box_height - 38, f"Level {level}: {_level_name(level)}")
            
            # Icon image
            try:
                img = Image.open(icon['path'])
                if mode == 'bw':
                    img = img.convert('L').convert('RGB')
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                buf.seek(0)
                icon_size = 0.6 * inch
                icon_x = box_x + box_width - icon_size - 10
                icon_y = box_y + box_height - icon_size - 8
                c.drawImage(ImageReader(buf), icon_x, icon_y,
                           width=icon_size, height=icon_size,
                           preserveAspectRatio=True, mask='auto')
            except:
                pass
            
            # Icon name
            c.setFillColorRGB(0, 0, 0)
            c.setFont(BODY_FONT, 9)
            c.drawCentredString(box_x + box_width/2, box_y + 8, icon['name'])
    
    # Footer - Gold standard (matches Matching cover / apply_small_wins_frame)
    footer_y = border_margin + 0.26 * inch
    c.setFont(BODY_FONT, 9)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line2 = "Small Wins Studio | PCS symbols used with active PCS Maker Personal License. | © 2026"
    c.drawCentredString(width/2, footer_y, footer_line2)
    
    c.setFont(TITLE_FONT, 10)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line1 = f"Brown Bear Find & Cover | Storage Labels | {pack_code}"
    c.drawCentredString(width/2, footer_y + 12, footer_line1)
    
    c.showPage()

def generate_storage_labels_pdf(output_path, mode='color'):
    """Generate storage labels PDF for all levels."""
    
    icons = load_brown_bear_icons()
    if not icons:
        print(f"No icons found, cannot generate PDF")
        return None
    
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    # Generate storage labels for each level (1-5)
    for level in [1, 2, 3, 4, 5]:
        generate_storage_labels_page(c, icons, level, mode)
    
    c.save()
    print(f"OK Generated: {output_path}")
    return output_path

def main():
    """Generate all Find & Cover PDFs."""
    
    # Output directories
    samples_dir = Path(__file__).parent / 'samples' / 'brown_bear' / 'find_cover'
    review_dir = Path(__file__).parent / 'review_pdfs'
    
    samples_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("GENERATING FIND & COVER LEVEL PDFs")
    print("=" * 60)
    
    # Generate Levels 1-4 in both modes
    for level in [1, 2, 3, 4]:
        for mode in ['color', 'bw']:
            filename = f"brown_bear_find_cover_level{level}_{mode}.pdf"
            
            # Generate in samples folder
            samples_path = samples_dir / filename
            generate_find_cover_pdf(samples_path, level, mode)
            
            # Copy to review folder
            review_path = review_dir / filename
            import shutil
            shutil.copy(samples_path, review_path)
            print(f"  Copied to: {review_path}")
    
    # Generate Level 5 (Extension - icons only)
    print("\n" + "-" * 40)
    print("GENERATING LEVEL 5: EXTENSION")
    print("-" * 40)
    
    for mode in ['color', 'bw']:
        filename = f"brown_bear_find_cover_level5_{mode}.pdf"
        
        # Generate in samples folder
        samples_path = samples_dir / filename
        generate_find_cover_pdf(samples_path, level=5, mode=mode)
        
        # Copy to review folder
        review_path = review_dir / filename
        import shutil
        shutil.copy(samples_path, review_path)
        print(f"  Copied to: {review_path}")
    
    # Generate storage labels
    print("\n" + "-" * 40)
    print("GENERATING STORAGE LABELS")
    print("-" * 40)
    
    for mode in ['color', 'bw']:
        filename = f"brown_bear_find_cover_storage_labels_{mode}.pdf"
        
        # Generate in samples folder
        samples_path = samples_dir / filename
        generate_storage_labels_pdf(samples_path, mode)
        
        # Copy to review folder
        review_path = review_dir / filename
        import shutil
        shutil.copy(samples_path, review_path)
        print(f"  Copied to: {review_path}")
    
    print("\n" + "=" * 60)
    print("FIND & COVER PDFs COMPLETE!")
    print("=" * 60)
    print(f"\nGenerated {5 * 2 + 2} PDF files (5 levels × 2 modes + 2 storage labels)")
    print(f"  Samples: {samples_dir}")
    print(f"  Review:  {review_dir}")

if __name__ == "__main__":
    main()
