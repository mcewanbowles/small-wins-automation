#!/usr/bin/env python3
"""
Amended Cover Generator
Creates single cover page with:
- Small brown bear image in bordered box
- Level-colored border
- Well-balanced, spaced features
- NO "differentiated" language
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from PIL import Image
import io

# Configuration
THEME = "brown_bear"
PRODUCT = "matching"
PACK_CODE_BASE = "SWS-MTCH-BB"

# Level definitions with LEVEL-SPECIFIC COLORS
LEVELS = {
    1: {
        "name": "Errorless",
        "color": "#F4B400",  # Orange
        "description": "Level 1"
    },
    2: {
        "name": "Easy",
        "color": "#4285F4",  # Blue
        "description": "Level 2"
    },
    3: {
        "name": "Medium",
        "color": "#34A853",  # Green
        "description": "Level 3"
    },
    4: {
        "name": "Challenge",
        "color": "#8C06F2",  # Purple
        "description": "Level 4"
    }
}

# Paths
ICON_PATH = f"assets/themes/{THEME}/icons/Brown bear.png"
OUTPUT_DIR = f"final_products/{THEME}/{PRODUCT}"

# Design constants
NAVY = "#1E3A5F"
FONT_PRIMARY = "Helvetica-Bold"  # Using Helvetica as Comic Sans may not be available
FONT_REGULAR = "Helvetica"

def create_cover_page(level, output_path):
    """
    Create amended cover page with:
    - Small brown bear image (2.5" x 2.5")
    - Level-colored accent strip
    - Well-balanced features
    - No "differentiated" language
    """
    # Setup
    level_info = LEVELS[level]
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
    c.setLineWidth(3)
    c.roundRect(border_x, border_y, border_width, border_height, 0.12 * inch)
    
    # Draw level-colored accent strip at top (with padding from border)
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
            # Draw image directly from file
            c.drawImage(ICON_PATH, image_x, image_y, 
                       width=image_size, height=image_size, 
                       preserveAspectRatio=True, anchor='c')
        except Exception as e:
            print(f"Warning: Could not load image: {e}")
            # Draw placeholder if image fails
            c.setFillColor(navy_color)
            c.setFont(FONT_REGULAR, 12)
            c.drawCentredString(image_x + image_size/2, image_y + image_size/2, 
                              "[Brown Bear]")
    
    # Well-balanced features section below image
    features_y = image_y - 0.5 * inch
    features_x = width / 2
    line_height = 0.35 * inch
    
    c.setFillColor(navy_color)
    c.setFont(FONT_PRIMARY, 14)
    c.drawCentredString(features_x, features_y, "✨ Product Features ✨")
    
    features_y -= line_height * 1.2
    
    # Features list (NO "differentiated" language)
    features = [
        "• 15 Activity Pages",  # REMOVED "Differentiated"
        f"• {level_info['name']} Level for Special Education",
        "• Part of Discounted Bundle (Save 25%!)",
        "• Bonus: Storage Labels Included",
        "• Print-Ready Cutout Pages"
    ]
    
    c.setFont(FONT_REGULAR, 12)
    for i, feature in enumerate(features):
        y_pos = features_y - (i * line_height)
        
        # Highlight bundle in level color
        if "Bundle" in feature:
            c.setFillColor(level_color)
            c.drawCentredString(features_x, y_pos, feature)
            c.setFillColor(navy_color)
        else:
            c.drawCentredString(features_x, y_pos, feature)
    
    # Footer with two-line format (inside border)
    footer_y = border_y + 0.5 * inch
    
    c.setFont(FONT_REGULAR, 9)
    # Line 1: Pack code and level info
    footer_line1 = f"Matching – Level {level} | {pack_code}"
    c.drawCentredString(width / 2, footer_y + 0.25 * inch, footer_line1)
    
    # Line 2: Copyright and license (lighter color)
    c.setFillColorRGB(0.6, 0.6, 0.6)  # Light gray
    footer_line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    c.drawCentredString(width / 2, footer_y, footer_line2)
    
    # Save PDF
    c.save()
    print(f"✓ Created amended cover: {output_path}")

def generate_all_covers():
    """Generate amended covers for all 4 levels"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=" * 60)
    print("AMENDED COVER GENERATOR")
    print("Single cover page with small brown bear image")
    print("=" * 60)
    print()
    
    for level in [1, 2, 3, 4]:
        output_file = f"{OUTPUT_DIR}/cover_level{level}_amended.pdf"
        create_cover_page(level, output_file)
    
    print()
    print("=" * 60)
    print("✓ All amended covers generated!")
    print(f"Location: {OUTPUT_DIR}/")
    print("=" * 60)

if __name__ == "__main__":
    generate_all_covers()
