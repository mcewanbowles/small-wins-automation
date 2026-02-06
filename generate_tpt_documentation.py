#!/usr/bin/env python3
"""
Generate TPT Documentation Pages for Small Wins Studio.
Creates professional 2-page Terms of Use, Credits, Tips, and Upselling document.
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

# Page settings
PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.25 * inch

# Brand Colors (from Design Constitution)
TEAL = '#008B8B'  # Primary brand accent
NAVY = '#1E3A5F'  # Secondary accent
LIGHT_GREY = '#999999'  # Footer text
WHITE = '#FFFFFF'
BLACK = '#000000'
LIGHT_BLUE_BORDER = '#A0C4E8'

# Level Colors
LEVEL_COLORS = {
    1: '#F4B400',  # Orange
    2: '#4285F4',  # Blue
    3: '#34A853',  # Green
    4: '#8C06F2',  # Purple
}

# Configuration - can be customized per theme
BOOK_TITLE = "Brown Bear, Brown Bear, What Do You See?"
BOOK_AUTHOR = "Bill Martin Jr. and Eric Carle"
YEAR = "2025"
TPT_STORE_URL = "www.teacherspayteachers.com/Store/Small-Wins-Studio"

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def draw_page_border(c, color=LIGHT_BLUE_BORDER):
    """Draw a rounded rectangle border around the page."""
    r, g, b = hex_to_rgb(color)
    c.setStrokeColorRGB(r, g, b)
    c.setLineWidth(2)
    radius = 8
    c.roundRect(MARGIN, MARGIN, 
                PAGE_WIDTH - 2*MARGIN, 
                PAGE_HEIGHT - 2*MARGIN, 
                radius)

def draw_accent_stripe(c, y, height, color=TEAL, text="", font_size=18):
    """Draw a colored accent stripe with optional text."""
    r, g, b = hex_to_rgb(color)
    c.setFillColorRGB(r, g, b)
    
    stripe_x = MARGIN + 10
    stripe_width = PAGE_WIDTH - 2*MARGIN - 20
    
    # Draw rounded rectangle
    c.roundRect(stripe_x, y, stripe_width, height, 6, fill=1, stroke=0)
    
    if text:
        c.setFillColorRGB(1, 1, 1)  # White text
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(stripe_x + 15, y + height/2 - font_size/3, text)

def draw_footer(c, page_num, total_pages):
    """Draw footer with copyright and page info."""
    # Line 1: Page info in Navy
    r, g, b = hex_to_rgb(NAVY)
    c.setFillColorRGB(r, g, b)
    c.setFont("Helvetica", 8)
    
    footer_y = MARGIN + 25
    c.drawCentredString(PAGE_WIDTH/2, footer_y, 
                        f"Small Wins Studio | TPT Documentation | Page {page_num}/{total_pages}")
    
    # Line 2: Copyright in light grey
    r, g, b = hex_to_rgb(LIGHT_GREY)
    c.setFillColorRGB(r, g, b)
    c.setFont("Helvetica", 7)
    c.drawCentredString(PAGE_WIDTH/2, footer_y - 12, 
                        f"© {YEAR} Small Wins Studio. All rights reserved.")

def draw_section_header(c, y, title, color=NAVY):
    """Draw a section header."""
    r, g, b = hex_to_rgb(color)
    c.setFillColorRGB(r, g, b)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(MARGIN + 20, y, title)
    
    # Underline
    c.setLineWidth(1)
    c.setStrokeColorRGB(r, g, b)
    c.line(MARGIN + 20, y - 3, PAGE_WIDTH - MARGIN - 20, y - 3)
    
    return y - 20

def draw_bullet_point(c, x, y, text, indent=0):
    """Draw a bullet point."""
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 9)
    bullet_x = x + indent
    c.drawString(bullet_x, y, "•")
    c.drawString(bullet_x + 12, y, text)
    return y - 14

def create_page_1(c):
    """Create Page 1: Terms of Use & Credits."""
    draw_page_border(c)
    
    # Header accent stripe
    draw_accent_stripe(c, PAGE_HEIGHT - MARGIN - 55, 45, TEAL, 
                       "Small Wins Studio - Terms of Use & Credits", 16)
    
    y = PAGE_HEIGHT - MARGIN - 80
    
    # Terms of Use Section
    y = draw_section_header(c, y, "📋 Terms of Use - Single-User License")
    
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0, 0, 0)
    
    # YOU MAY section
    c.setFont("Helvetica-Bold", 10)
    r, g, b = hex_to_rgb('#34A853')  # Green
    c.setFillColorRGB(r, g, b)
    c.drawString(MARGIN + 25, y, "✓ YOU MAY:")
    y -= 15
    
    c.setFillColorRGB(0, 0, 0)
    items = [
        "Use this resource for your own students in your classroom",
        "Print copies for your classroom use",
        "Share with your own substitute teachers when you are absent",
        "Adapt and modify materials for your students' needs"
    ]
    for item in items:
        y = draw_bullet_point(c, MARGIN + 35, y, item)
    
    y -= 10
    
    # YOU MAY NOT section
    c.setFont("Helvetica-Bold", 10)
    r, g, b = hex_to_rgb('#EA4335')  # Red
    c.setFillColorRGB(r, g, b)
    c.drawString(MARGIN + 25, y, "✗ YOU MAY NOT:")
    y -= 15
    
    c.setFillColorRGB(0, 0, 0)
    items = [
        "Share digital files with other teachers (please direct them to my TPT store)",
        "Upload this resource to school servers for multiple teachers",
        "Resell or redistribute this resource in any form",
        "Claim this work as your own"
    ]
    for item in items:
        y = draw_bullet_point(c, MARGIN + 35, y, item)
    
    y -= 20
    
    # Book Disclaimer Section
    y = draw_section_header(c, y, "📚 Important Book Disclaimer")
    
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0, 0, 0)
    
    disclaimer_text = [
        f"This resource is designed to complement \"{BOOK_TITLE}\" by {BOOK_AUTHOR}.",
        "",
        "This product is NOT affiliated with, endorsed by, or sponsored by the book's publisher or",
        "authors. You will need to purchase the book separately to use this resource effectively.",
        "",
        "All book-related content (characters, themes, vocabulary) is used under fair use for",
        "educational purposes. BoardMaker symbols are used under PCS Maker Personal License."
    ]
    
    for line in disclaimer_text:
        c.drawString(MARGIN + 25, y, line)
        y -= 12
    
    y -= 15
    
    # Credits Section
    y = draw_section_header(c, y, "🎨 Credits & Acknowledgments")
    
    credits = [
        ("Symbols:", "PCS® symbols © Tobii Dynavox. Used with active PCS Maker Personal License."),
        ("Design:", "Small Wins Studio original design following accessibility best practices."),
        ("Fonts:", "Standard accessibility-compliant fonts for easy reading."),
        ("Icons:", "Specially designed for AAC learners and early childhood education.")
    ]
    
    for label, text in credits:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN + 25, y, label)
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN + 80, y, text)
        y -= 14
    
    y -= 20
    
    # Contact Section
    y = draw_section_header(c, y, "📧 Contact & Support")
    
    c.setFont("Helvetica", 9)
    contact_info = [
        "Questions or issues? Please reach out through TPT messaging or leave a question on the product page.",
        "I aim to respond within 24-48 hours on school days.",
        "",
        "For additional licenses (teams, schools, districts), please contact me for discounted pricing."
    ]
    
    for line in contact_info:
        c.drawString(MARGIN + 25, y, line)
        y -= 12
    
    draw_footer(c, 1, 2)
    c.showPage()

def create_page_2(c):
    """Create Page 2: Tips, Levels, and Upselling."""
    draw_page_border(c)
    
    # Header accent stripe
    draw_accent_stripe(c, PAGE_HEIGHT - MARGIN - 55, 45, TEAL,
                       "Getting the Most from This Resource", 16)
    
    y = PAGE_HEIGHT - MARGIN - 80
    
    # Top Tips Section
    y = draw_section_header(c, y, "💡 Top Tips for Teachers")
    
    tips = [
        "Laminate activity pages for durability and repeated use with dry-erase markers or velcro",
        "Start with Level 1 (Errorless) to build confidence before increasing difficulty",
        "Use consistent praise phrases: \"Great matching!\" \"You found the [animal]!\"",
        "Pair with the actual book for maximum engagement and vocabulary building",
        "Store pieces in labeled bags or containers for easy classroom management",
        "Consider creating a dedicated \"Work Task\" box or folder for independent practice"
    ]
    
    for tip in tips:
        y = draw_bullet_point(c, MARGIN + 20, y, tip)
    
    y -= 15
    
    # Level Differentiation Section
    y = draw_section_header(c, y, "📊 Understanding the 4 Levels")
    
    # Draw level table
    table_x = MARGIN + 25
    table_width = PAGE_WIDTH - 2*MARGIN - 50
    col_widths = [table_width * 0.15, table_width * 0.25, table_width * 0.60]
    
    # Table header
    c.setFillColorRGB(*hex_to_rgb(NAVY))
    c.setFont("Helvetica-Bold", 9)
    headers = ["Level", "Name", "Description"]
    x = table_x
    for i, header in enumerate(headers):
        c.drawString(x + 5, y, header)
        x += col_widths[i]
    y -= 12
    
    # Draw header line
    c.setLineWidth(1)
    c.line(table_x, y + 3, table_x + table_width, y + 3)
    y -= 5
    
    # Level rows
    levels = [
        (1, "Errorless", "All options match—builds confidence and teaches the task"),
        (2, "Easy", "Some distractors introduced—develops discrimination skills"),
        (3, "Medium", "More distractors—strengthens visual scanning and attention"),
        (4, "Challenge", "Maximum difficulty—prepares for real-world generalization")
    ]
    
    for level_num, name, desc in levels:
        # Level color dot
        r, g, b = hex_to_rgb(LEVEL_COLORS[level_num])
        c.setFillColorRGB(r, g, b)
        c.circle(table_x + 15, y + 3, 5, fill=1, stroke=0)
        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(table_x + 25, y, f"L{level_num}")
        
        c.setFont("Helvetica", 9)
        c.drawString(table_x + col_widths[0] + 5, y, name)
        c.drawString(table_x + col_widths[0] + col_widths[1] + 5, y, desc)
        y -= 16
    
    y -= 15
    
    # Storage Tips Section
    y = draw_section_header(c, y, "📦 Storage & Organization")
    
    storage_tips = [
        "Print storage labels (included) and attach to containers or bags",
        "Color-code by level for quick identification during busy classroom moments",
        "Create a \"Work Tasks\" station with activities at multiple levels"
    ]
    
    for tip in storage_tips:
        y = draw_bullet_point(c, MARGIN + 20, y, tip)
    
    y -= 15
    
    # Bundle Upselling Section
    y = draw_section_header(c, y, "⭐ Save with Bundles!")
    
    c.setFont("Helvetica", 9)
    bundle_text = [
        "Love this resource? Check out my complete themed bundles for even more savings!",
        "",
        "Each bundle includes: Matching activities, Find & Cover pages, Storage labels,",
        "Quick Start guides, and more—all at a discounted bundle price.",
        "",
        f"Visit my store: {TPT_STORE_URL}"
    ]
    
    for line in bundle_text:
        c.drawString(MARGIN + 25, y, line)
        y -= 12
    
    y -= 15
    
    # Review Request Section
    y = draw_section_header(c, y, "🌟 Your Feedback Matters!")
    
    c.setFont("Helvetica", 9)
    review_text = [
        "As a new TPT seller, your reviews and feedback mean everything to me!",
        "",
        "If you found this resource helpful, please consider leaving a rating or review.",
        "Your feedback helps other teachers discover these materials and helps me improve.",
        "",
        "Have suggestions or found an issue? Please message me—I'm always looking to make",
        "my resources better for you and your students. Thank you for your support!"
    ]
    
    for line in review_text:
        c.drawString(MARGIN + 25, y, line)
        y -= 12
    
    draw_footer(c, 2, 2)
    c.showPage()

def generate_tpt_documentation():
    """Generate the complete TPT documentation PDF."""
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
        
        # Create pages
        create_page_1(c)
        create_page_2(c)
        
        c.save()
        print(f"Generated: {pdf_path}")
    
    print("\n✅ TPT Documentation generated successfully!")
    print(f"   - 2 pages: Terms of Use & Tips")
    print(f"   - Design: Small Wins Studio branding")
    print(f"   - Theme: {BOOK_TITLE}")

if __name__ == '__main__':
    generate_tpt_documentation()
