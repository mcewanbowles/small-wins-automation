#!/usr/bin/env python3
"""
Final Cover Generator with Updated Text
Creates single cover page with:
- Level-colored border (matching activity pages)
- Small brown bear image in bordered box
- Updated text per user requirements
- Quick Start instructions
"""

import os
import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from PIL import Image

# Configuration
THEME = "brown_bear"
PRODUCT = "matching"
PACK_CODE_BASE = "SWS-MTCH-BB"

# Repo root
REPO_ROOT = Path(__file__).resolve().parent

def _load_matching_levels():
    theme_path = REPO_ROOT / "themes" / f"{THEME}.json"
    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)
    levels = theme["matching"]["levels"]
    out = {}
    for i in range(1, 6):
        key = f"L{i}"
        out[i] = {
            "name": levels[key]["name"],
            "color": levels[key]["colour"],
            "description": f"Level {i} — {levels[key]['name']}"
        }
    return out


LEVELS = _load_matching_levels()

# Paths
ICON_PATH = f"assets/themes/{THEME}/icons/Brown bear.png"
OUTPUT_DIR = str(REPO_ROOT / "production" / "final_products" / THEME / PRODUCT)

# Design constants
NAVY = "#1E3A5F"
FONT_PRIMARY = "Helvetica-Bold"
FONT_REGULAR = "Helvetica"


def _trim_transparent_padding(img: Image.Image) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    bbox = img.getbbox()
    if not bbox:
        return img
    return img.crop(bbox)

def create_cover_page(level, output_path, grayscale=False):
    """
    Create cover page with updated text requirements:
    - 15 Activity Pages
    - Level X Matching to Boards
    - Colour + Black & White Versions Included
    - Print-Ready Cutout Pieces (optional laminate/Velcro for reuse)
    - Bonus: Storage Labels Included
    - Quick Start instructions
    
    Args:
        level: Level number (1-4)
        output_path: Path to save PDF
        grayscale: If True, creates B&W version (no color)
    """
    # Setup
    level_info = LEVELS[level]
    
    if grayscale:
        # For B&W version, use grayscale only
        level_color = HexColor("#808080")  # Medium gray instead of level color
        navy_color = HexColor("#000000")  # Black instead of navy
    else:
        level_color = HexColor(level_info["color"])
        navy_color = HexColor(NAVY)
    
    pack_code = f"{PACK_CODE_BASE}{level}"
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter  # 8.5" x 11" = 612 x 792 points
    
    # Margins
    margin = 0.5 * inch
    border_x = margin
    border_y = margin
    border_width = width - (2 * margin)
    border_height = height - (2 * margin)
    
    # Draw outer navy border with rounded corners
    c.setStrokeColor(navy_color)
    c.setLineWidth(4)
    c.roundRect(border_x, border_y, border_width, border_height, 0.12 * inch)
    
    # Draw level-colored accent strip at top (matching activity pages)
    accent_padding = 0.3 * inch
    accent_height = 1.2 * inch
    accent_y = border_y + border_height - accent_height - accent_padding
    accent_width = border_width - (2 * accent_padding)
    
    c.setFillColor(level_color)
    c.roundRect(border_x + accent_padding, accent_y, accent_width, accent_height, 
                0.12 * inch, fill=1, stroke=0)
    
    # Product title in accent strip (white text, proper padding)
    c.setFillColorRGB(1, 1, 1)  # White
    c.setFont(FONT_PRIMARY, 32)
    title_y = accent_y + accent_height * 0.6
    c.drawCentredString(width / 2, title_y, "Brown Bear Matching")
    
    # Level subtitle in accent strip
    c.setFont(FONT_REGULAR, 16)
    subtitle_y = accent_y + accent_height * 0.25
    c.drawCentredString(width / 2, subtitle_y, f"{level_info['description']}")
    
    # Small brown bear image in bordered box (2.5" x 2.5")
    image_size = 2.5 * inch
    image_x = (width - image_size) / 2
    image_y = accent_y - image_size - 0.8 * inch
    
    # Draw border around image with level color
    border_padding = 0.15 * inch
    c.setStrokeColor(level_color)
    c.setLineWidth(4)
    c.roundRect(image_x - border_padding, image_y - border_padding,
                image_size + (2 * border_padding), image_size + (2 * border_padding),
                0.12 * inch)
    
    # Add brown bear image if available
    if os.path.exists(ICON_PATH):
        try:
            if grayscale:
                # Convert image to grayscale for B&W version
                img = Image.open(ICON_PATH)
                img_gray = _trim_transparent_padding(img).convert('L')  # Convert to grayscale
                # Save to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_path = temp_file.name
                    img_gray.save(temp_path)
                c.drawImage(temp_path, image_x, image_y, 
                           width=image_size, height=image_size, 
                           preserveAspectRatio=True, anchor='c')
                os.unlink(temp_path)  # Clean up temp file
            else:
                import tempfile
                img = _trim_transparent_padding(Image.open(ICON_PATH))
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_path = temp_file.name
                    img.save(temp_path)
                c.drawImage(temp_path, image_x, image_y,
                           width=image_size, height=image_size,
                           preserveAspectRatio=True, anchor='c')
                os.unlink(temp_path)
        except Exception as e:
            print(f"Warning: Could not load image: {e}")
            c.setFillColor(navy_color)
            c.setFont(FONT_REGULAR, 12)
            c.drawCentredString(image_x + image_size/2, image_y + image_size/2, 
                              "[Brown Bear]")
    
    # Features section below image
    features_y = image_y - 0.7 * inch
    features_x = width / 2
    line_height = 0.32 * inch

    c.setFillColor(level_color)
    c.setFont(FONT_PRIMARY, 14)
    c.drawCentredString(features_x, features_y, "✨ Product Features ✨")
    
    features_y -= line_height * 1.2
    
    # Updated features list per user requirements
    features = [
        "15 Activity Pages",
        f"Level {level} Matching to Boards",
        "Colour + Black & White Versions Included",
        "Print-Ready Cutout Pieces (optional laminate/Velcro for reuse)",
        "Bonus: Storage Labels Included"
    ]
    
    c.setFillColor(navy_color)
    c.setFont(FONT_REGULAR, 11)
    for i, feature in enumerate(features):
        y_pos = features_y - (i * line_height)
        c.drawCentredString(features_x, y_pos, feature)
    
    # Quick Start Instructions section
    quick_start_y = features_y - (len(features) * line_height) - 0.6 * inch
    
    c.setFont(FONT_PRIMARY, 12)
    c.setFillColor(level_color)
    c.drawCentredString(features_x, quick_start_y, "Quick Start Instructions")
    
    quick_start_y -= line_height * 1.1
    
    # Quick start text with arrows
    c.setFont(FONT_REGULAR, 10)
    c.setFillColor(navy_color)
    quick_start_text = "Print → Cut → (optional laminate/Velcro) → Match pieces to boards → Pack away with storage labels"
    c.drawCentredString(features_x, quick_start_y, quick_start_text)
    
    # Footer with two-line format (inside border)
    footer_y = border_y + 0.32 * inch
    
    c.setFont(FONT_REGULAR, 9)
    # Line 1: Pack code and level info
    footer_line1 = f"Matching – Level {level} | {pack_code}"
    c.drawCentredString(width / 2, footer_y + 0.22 * inch, footer_line1)
    
    # Line 2: Copyright and license (lighter color)
    c.setFillColorRGB(0.6, 0.6, 0.6)  # Light gray
    footer_line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    c.drawCentredString(width / 2, footer_y, footer_line2)
    
    # Save PDF
    c.save()
    print(f"OK Created final cover: {output_path}")

def generate_all_covers():
    """Generate final covers for all 4 levels - both color and B&W versions"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=" * 60)
    print("FINAL COVER GENERATOR")
    print("Updated text per user requirements")
    print("Generating COLOR and B&W versions")
    print("=" * 60)
    print()
    
    for level in [1, 2, 3, 4, 5]:
        # Color version
        output_file_color = f"{OUTPUT_DIR}/cover_level{level}_color_FINAL.pdf"
        create_cover_page(level, output_file_color, grayscale=False)
        
        # B&W version (grayscale)
        output_file_bw = f"{OUTPUT_DIR}/cover_level{level}_bw_FINAL.pdf"
        create_cover_page(level, output_file_bw, grayscale=True)
    
    print()
    print("=" * 60)
    print("OK All covers generated successfully!")
    print("  - 4 color covers")
    print("  - 4 B&W (grayscale) covers")
    print("=" * 60)

if __name__ == "__main__":
    generate_all_covers()
