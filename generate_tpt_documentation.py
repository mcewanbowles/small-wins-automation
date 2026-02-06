#!/usr/bin/env python3
"""
Generate TPT Documentation Pages for Small Wins Studio.
Creates professional 1-page Terms of Use & Credits document.
Follows Small Wins Studio Design Constitution.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

# Page settings
PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.5 * inch  # Match page margins throughout
INNER_MARGIN = MARGIN + 15  # Content margin

# Brand Colors (from Design Constitution)
TEAL = '#008B8B'  # Primary brand accent
NAVY = '#1E3A5F'  # Secondary accent
LIGHT_GREY = '#999999'  # Footer text
WHITE = '#FFFFFF'
BLACK = '#000000'
LIGHT_BLUE_BORDER = '#A0C4E8'

# Configuration - can be customized per theme
BOOK_TITLE = "Brown Bear, Brown Bear, What Do You See?"
BOOK_AUTHOR = "Bill Martin Jr. and Eric Carle"
YEAR = "2025"
TPT_STORE_URL = "www.teacherspayteachers.com/Store/Small-Wins-Studio"

# Logo path
LOGO_PATH = Path(__file__).parent / 'assets' / 'branding' / 'small_wins_logo.png' / 'star.png'

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def draw_page_border(c, color=TEAL):
    """Draw a rounded rectangle border around the page in TEAL."""
    r, g, b = hex_to_rgb(color)
    c.setStrokeColorRGB(r, g, b)
    c.setLineWidth(2)
    radius = 8
    c.roundRect(MARGIN - 10, MARGIN - 10, 
                PAGE_WIDTH - 2*MARGIN + 20, 
                PAGE_HEIGHT - 2*MARGIN + 20, 
                radius)

def draw_header_with_logo(c, y):
    """Draw centered header with logo next to Small Wins Studio."""
    # Draw logo if exists
    logo_width = 30
    logo_height = 30
    title_text = "Small Wins Studio"
    
    c.setFont("Helvetica-Bold", 20)
    title_width = c.stringWidth(title_text, "Helvetica-Bold", 20)
    
    # Calculate total width (logo + spacing + title)
    total_width = logo_width + 10 + title_width
    start_x = (PAGE_WIDTH - total_width) / 2
    
    # Draw logo
    if LOGO_PATH.exists():
        c.drawImage(str(LOGO_PATH), start_x, y - 5, width=logo_width, height=logo_height,
                   preserveAspectRatio=True, mask='auto')
    
    # Draw title centered after logo
    r, g, b = hex_to_rgb(TEAL)
    c.setFillColorRGB(r, g, b)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(start_x + logo_width + 10, y, title_text)
    
    # Subtitle centered
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 11)
    c.drawCentredString(PAGE_WIDTH/2, y - 25, "Terms of Use & Credits")
    
    return y - 50

def draw_accent_stripe(c, y, height, color=TEAL, text="", font_size=14):
    """Draw a colored accent stripe with centered text."""
    r, g, b = hex_to_rgb(color)
    c.setFillColorRGB(r, g, b)
    
    stripe_x = MARGIN - 5
    stripe_width = PAGE_WIDTH - 2*MARGIN + 10
    
    # Draw rounded rectangle
    c.roundRect(stripe_x, y, stripe_width, height, 6, fill=1, stroke=0)
    
    if text:
        c.setFillColorRGB(1, 1, 1)  # White text
        c.setFont("Helvetica-Bold", font_size)
        # Center the text
        c.drawCentredString(PAGE_WIDTH/2, y + height/2 - font_size/3, text)

def draw_footer(c, product_name="Brown Bear Matching", product_code="BB-MATCH", page_num=1):
    """Draw standard footer with product info, star logo, Small Wins, copyright in light grey."""
    footer_y = MARGIN + 8
    
    # Product name and page number ABOVE the footer line
    r, g, b = hex_to_rgb(LIGHT_GREY)
    c.setFillColorRGB(r, g, b)
    c.setFont("Helvetica", 8)
    product_line = f"{product_name} | {product_code} | Page {page_num}"
    c.drawCentredString(PAGE_WIDTH / 2, footer_y + 15, product_line)
    
    # Star logo - slightly larger so it rises above the S of "Small Wins"
    logo_size = 16  # Larger than text height so star rises above
    footer_text = "Small Wins Studio"
    c.setFont("Helvetica", 8)
    text_width = c.stringWidth(footer_text, "Helvetica", 8)
    
    # Star positioned close to "S" as though part of the word
    logo_gap = 1  # Very close to text (almost touching)
    copyright_text = f"© {YEAR} All rights reserved."
    total_width = logo_size + logo_gap + text_width + 15 + c.stringWidth(copyright_text, "Helvetica", 7)
    start_x = (PAGE_WIDTH - total_width) / 2
    
    # Draw star logo - transparent background, rising above S
    if LOGO_PATH.exists():
        # Position star so it rises above the "S" - base at footer level, top above text
        c.drawImage(str(LOGO_PATH), start_x, footer_y - 2, width=logo_size, height=logo_size,
                   preserveAspectRatio=True, mask='auto')
    
    # Small Wins Studio text - in light grey, positioned very close to star
    r, g, b = hex_to_rgb(LIGHT_GREY)
    c.setFillColorRGB(r, g, b)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(start_x + logo_size + logo_gap, footer_y, footer_text)
    
    # Copyright - in light grey
    c.setFont("Helvetica", 7)
    c.drawString(start_x + logo_size + logo_gap + text_width + 15, footer_y, copyright_text)

def draw_section_header(c, y, title, color=NAVY, centered=True):
    """Draw a section header - centered, larger font."""
    r, g, b = hex_to_rgb(color)
    c.setFillColorRGB(r, g, b)
    c.setFont("Helvetica-Bold", 13)  # Larger font
    
    if centered:
        c.drawCentredString(PAGE_WIDTH/2, y, title)
    else:
        c.drawString(INNER_MARGIN, y, title)
    
    # Underline
    c.setLineWidth(1)
    c.setStrokeColorRGB(r, g, b)
    c.line(INNER_MARGIN, y - 3, PAGE_WIDTH - INNER_MARGIN, y - 3)
    
    return y - 20

def draw_bullet_point(c, x, y, text, indent=0, max_width=None):
    """Draw a bullet point with proper wrapping - larger font."""
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 11)  # Larger font
    bullet_x = x + indent
    c.drawString(bullet_x, y, "•")
    c.drawString(bullet_x + 12, y, text)
    return y - 15  # More spacing

def create_single_page(c):
    """Create single-page Terms of Use & Credits document with larger fonts."""
    draw_page_border(c)  # Now uses teal
    
    y = PAGE_HEIGHT - MARGIN - 10
    
    # Header with logo and centered title
    y = draw_header_with_logo(c, y)
    
    y -= 15
    
    # Terms of Use Section
    y = draw_section_header(c, y, "📋 Terms of Use - Single-User License")
    
    c.setFont("Helvetica", 11)  # Larger font
    c.setFillColorRGB(0, 0, 0)
    
    # YOU MAY section
    c.setFont("Helvetica-Bold", 11)
    r, g, b = hex_to_rgb('#34A853')  # Green
    c.setFillColorRGB(r, g, b)
    c.drawString(INNER_MARGIN, y, "✓ YOU MAY:")
    y -= 16
    
    c.setFillColorRGB(0, 0, 0)
    items = [
        "Use this resource for your own students • Print copies for classroom use",
        "Share with substitute teachers • Adapt materials for your students' needs"
    ]
    for item in items:
        y = draw_bullet_point(c, INNER_MARGIN + 10, y, item)
    
    y -= 12
    
    # YOU MAY NOT section
    c.setFont("Helvetica-Bold", 11)
    r, g, b = hex_to_rgb('#EA4335')  # Red
    c.setFillColorRGB(r, g, b)
    c.drawString(INNER_MARGIN, y, "✗ YOU MAY NOT:")
    y -= 16
    
    c.setFillColorRGB(0, 0, 0)
    items = [
        "Share digital files with other teachers • Upload to school servers",
        "Resell or redistribute this resource • Claim this work as your own"
    ]
    for item in items:
        y = draw_bullet_point(c, INNER_MARGIN + 10, y, item)
    
    y -= 20
    
    # Book Disclaimer Section - with proper margins
    y = draw_section_header(c, y, "📚 Important Book Disclaimer")
    
    c.setFont("Helvetica", 11)  # Larger font
    c.setFillColorRGB(0, 0, 0)
    
    # Calculate text width to use full margin
    text_width = PAGE_WIDTH - 2*INNER_MARGIN
    
    disclaimer_lines = [
        f"This product is designed to complement \"{BOOK_TITLE}\" by {BOOK_AUTHOR}. This product is NOT affiliated with, endorsed by, or sponsored by the book's publisher or authors. You will need to purchase the book separately.",
        "",
        "All book-related content is used under fair use for educational purposes. BoardMaker symbols are used under PCS Maker Personal License."
    ]
    
    for line in disclaimer_lines:
        if line:
            # Word wrap to fit margins
            words = line.split()
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if c.stringWidth(test_line, "Helvetica", 11) < text_width:
                    current_line = test_line
                else:
                    c.drawString(INNER_MARGIN, y, current_line)
                    y -= 14
                    current_line = word
            if current_line:
                c.drawString(INNER_MARGIN, y, current_line)
                y -= 14
        else:
            y -= 8
    
    y -= 15
    
    # Credits Section (simplified - no Fonts & Icons)
    y = draw_section_header(c, y, "🎨 Credits & Acknowledgments")
    
    credits = [
        ("Symbols:", "PCS® symbols © Tobii Dynavox. Used with active PCS Maker Personal License."),
        ("Design:", "Small Wins Studio original design following accessibility best practices.")
    ]
    
    for label, text in credits:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(INNER_MARGIN, y, label)
        c.setFont("Helvetica", 11)
        c.drawString(INNER_MARGIN + 60, y, text)
        y -= 16
    
    y -= 20
    
    # Combined Bundles & Feedback Section - REMOVED "each bundle includes..."
    y = draw_section_header(c, y, "⭐ Save with Bundles & Your Feedback Matters!")
    
    c.setFont("Helvetica", 11)  # Larger font
    c.setFillColorRGB(0, 0, 0)
    
    combined_text = [
        "Love this resource? Check out my complete themed bundles for savings!",
        "",
        "As a new TPT seller, your reviews and feedback mean everything! If you found",
        f"this resource helpful, please consider leaving a rating.",
        "",
        f"Visit: {TPT_STORE_URL}"
    ]
    
    for line in combined_text:
        c.drawString(INNER_MARGIN, y, line)
        y -= 14
    
    draw_footer(c)
    c.showPage()

def generate_tpt_documentation():
    """Generate the complete TPT documentation PDF (1 page)."""
    # Create output directories
    output_dirs = [
        Path(__file__).parent / 'review_pdfs',
        Path(__file__).parent / 'samples' / 'brown_bear' / 'matching'
    ]
    
    for output_dir in output_dirs:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate PDF
    pdf_filename = 'small_wins_tpt_documentation.pdf'
    
    for output_dir in output_dirs:
        pdf_path = output_dir / pdf_filename
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        
        # Create single page
        create_single_page(c)
        
        c.save()
        print(f"Generated: {pdf_path}")
    
    print("\n✅ TPT Documentation generated successfully!")
    print(f"   - 1 page: Terms of Use & Credits")
    print(f"   - Design: Small Wins Studio branding with logo")
    print(f"   - Theme: {BOOK_TITLE}")

if __name__ == '__main__':
    generate_tpt_documentation()
