#!/usr/bin/env python3
"""
Quick Start Instructions Generator for Matching Activity
Creates a professional 2-page PDF with instructions for all levels.
Uses Comic Sans MS throughout - Title 28pt, Subtitle 16pt, Body 11pt
Matches the branding of the Matching Product exactly.
"""

import os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Try to register Comic Sans - fall back to Helvetica if not available
try:
    pdfmetrics.registerFont(TTFont('ComicSans', '/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf'))
    pdfmetrics.registerFont(TTFont('ComicSans-Bold', '/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS_Bold.ttf'))
    TITLE_FONT = 'ComicSans-Bold'
    BODY_FONT = 'ComicSans'
except:
    TITLE_FONT = 'Helvetica-Bold'
    BODY_FONT = 'Helvetica'

# FONT RULES - Only 3 sizes throughout
TITLE_SIZE = 28      # Main title
SUBTITLE_SIZE = 16   # Subtitle
BODY_SIZE = 11       # All body text

# Level colors - EXACT match to Design Constitution
LEVEL_COLORS = {
    1: HexColor('#F4B400'),  # Orange - Errorless
    2: HexColor('#4285F4'),  # Blue - Distractors
    3: HexColor('#34A853'),  # Green - Moderate
    4: HexColor('#8C06F2'),  # Purple - Challenge
}

# Brand colors
LIGHT_BLUE_BORDER = HexColor('#A0C4E8')
WARM_ORANGE = HexColor('#F5A623')
LIGHT_GREY = HexColor('#F0F0F0')
DARK_GREY = HexColor('#333333')

# Fixed page structure
BORDER_MARGIN = 0.5 * inch
ACCENT_HEIGHT = 0.85 * inch
FOOTER_HEIGHT = 0.5 * inch


def draw_page_border(c, width, height):
    """Draw rounded rectangle border with accent stripe."""
    content_width = width - 2 * BORDER_MARGIN
    content_height = height - 2 * BORDER_MARGIN
    
    # Light blue border - rounded corners, 3px stroke
    c.setStrokeColor(LIGHT_BLUE_BORDER)
    c.setLineWidth(3)
    c.roundRect(BORDER_MARGIN, BORDER_MARGIN, content_width, content_height, 12, stroke=1, fill=0)
    
    # Accent stripe - WARM ORANGE, rounded corners, inside border
    accent_margin = 0.1 * inch
    accent_x = BORDER_MARGIN + accent_margin
    accent_y = height - BORDER_MARGIN - ACCENT_HEIGHT - accent_margin
    accent_width = content_width - 2 * accent_margin
    
    c.setFillColor(WARM_ORANGE)
    c.roundRect(accent_x, accent_y, accent_width, ACCENT_HEIGHT, 8, stroke=0, fill=1)
    
    return accent_y, accent_width


def draw_title_in_stripe(c, width, accent_y, accent_width, title, subtitle):
    """Draw title and subtitle CENTERED in accent stripe - WHITE text."""
    accent_x = BORDER_MARGIN + 0.1 * inch
    
    # Title - WHITE, CENTERED vertically and horizontally
    c.setFillColor(white)
    c.setFont(TITLE_FONT, TITLE_SIZE)
    title_y = accent_y + ACCENT_HEIGHT/2 + 5
    c.drawCentredString(width/2, title_y, title)
    
    # Subtitle - WHITE, CENTERED below title
    c.setFont(BODY_FONT, SUBTITLE_SIZE)
    subtitle_y = title_y - 25
    c.drawCentredString(width/2, subtitle_y, subtitle)


def draw_footer(c, width, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear"):
    """Draw 2-line footer INSIDE the border."""
    footer_y1 = BORDER_MARGIN + 0.35 * inch
    footer_y2 = BORDER_MARGIN + 0.18 * inch
    
    c.setFillColor(black)
    c.setFont(TITLE_FONT, 9)
    line1 = f"{pack_code} | {theme_name} | Quick Start | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y1, line1)
    
    c.setFont(BODY_FONT, 8)
    line2 = "© 2025 Small Wins Studio • For personal and classroom use only"
    c.drawCentredString(width/2, footer_y2, line2)


def draw_level_box(c, x, y, box_width, box_height, level, title, instructions):
    """Draw a level instruction box with color-coded header - fills the box."""
    color = LEVEL_COLORS[level]
    
    # Background box - light grey
    c.setFillColor(LIGHT_GREY)
    c.roundRect(x, y - box_height, box_width, box_height, 8, stroke=0, fill=1)
    
    # Header bar with level color
    header_height = 0.35 * inch
    c.setFillColor(color)
    c.roundRect(x, y - header_height, box_width, header_height, 8, stroke=0, fill=1)
    
    # Cover the bottom corners of the header to make it flat at the bottom
    c.rect(x, y - header_height, box_width, 10, stroke=0, fill=1)
    
    # Level title - WHITE, CENTERED in header
    c.setFillColor(white)
    c.setFont(TITLE_FONT, BODY_SIZE)
    c.drawCentredString(x + box_width/2, y - header_height + 0.1*inch, title)
    
    # Instructions - BODY_SIZE, properly spaced to fill box
    c.setFillColor(DARK_GREY)
    c.setFont(BODY_FONT, BODY_SIZE - 1)
    
    text_y = y - header_height - 0.25*inch
    line_spacing = 0.18 * inch
    for line in instructions:
        c.drawCentredString(x + box_width/2, text_y, line)
        text_y -= line_spacing


def create_page1_how_to_play(c, width, height):
    """Create page 1: How to Play with 2x2 grid of levels + tips."""
    accent_y, accent_width = draw_page_border(c, width, height)
    draw_title_in_stripe(c, width, accent_y, accent_width, "QUICK START", "Brown Bear Matching")
    
    # 2x2 grid for levels - balanced and centered
    box_width = 3.5 * inch
    box_height = 1.6 * inch
    h_gap = 0.25 * inch
    v_gap = 0.15 * inch
    
    total_width = box_width * 2 + h_gap
    left_x = (width - total_width) / 2
    right_x = left_x + box_width + h_gap
    
    top_y = accent_y - 0.15 * inch
    
    # Level 1 - Top Left (Orange)
    l1_instructions = [
        "5 matching pictures, 0 distractors",
        "Errorless - all answers correct!",
        "Builds confidence. Use watermarks.",
    ]
    draw_level_box(c, left_x, top_y, box_width, box_height, 1, 
                   "Level 1: Errorless (Orange)", l1_instructions)
    
    # Level 2 - Top Right (Blue)
    l2_instructions = [
        "4 matching pictures, 1 distractor",
        "Student finds the one that matches",
        "Low frustration discrimination",
    ]
    draw_level_box(c, right_x, top_y, box_width, box_height, 2,
                   "Level 2: Easy (Blue)", l2_instructions)
    
    # Level 3 - Bottom Left (Green)
    bottom_y = top_y - box_height - v_gap
    l3_instructions = [
        "3 matching pictures, 2 distractors",
        "Moderate challenge, more choices",
        "Encourage verbalization",
    ]
    draw_level_box(c, left_x, bottom_y, box_width, box_height, 3,
                   "Level 3: Medium (Green)", l3_instructions)
    
    # Level 4 - Bottom Right (Purple)
    l4_instructions = [
        "1 matching picture, 4 distractors",
        "True discrimination - find the ONE",
        "Assessment ready. Celebrate!",
    ]
    draw_level_box(c, right_x, bottom_y, box_width, box_height, 4,
                   "Level 4: Challenge (Purple)", l4_instructions)
    
    # General Tips box - full width, fills remaining space
    tips_y = bottom_y - box_height - 0.15*inch
    tips_height = tips_y - BORDER_MARGIN - FOOTER_HEIGHT - 0.15*inch
    tips_box_y = BORDER_MARGIN + FOOTER_HEIGHT + 0.1*inch
    tips_height = tips_y - tips_box_y
    
    c.setFillColor(LIGHT_GREY)
    c.roundRect(left_x, tips_box_y, total_width, tips_height, 8, stroke=0, fill=1)
    
    # Tips header
    c.setFillColor(DARK_GREY)
    c.setFont(TITLE_FONT, BODY_SIZE + 2)
    c.drawCentredString(width/2, tips_box_y + tips_height - 0.25*inch, "General Tips for Success")
    
    # Tips content - CENTERED, evenly spaced
    c.setFont(BODY_FONT, BODY_SIZE)
    tips = [
        "• Start at Level 1 until 80% accuracy, then progress",
        "• Use AAC symbols: match, same, find, look",
        "• Allow response time - count to 10 silently",
        "• Praise effort AND accuracy: 'Great matching!'",
    ]
    tips_text_y = tips_box_y + tips_height - 0.5*inch
    for tip in tips:
        c.drawCentredString(width/2, tips_text_y, tip)
        tips_text_y -= 0.2*inch
    
    draw_footer(c, width, 1, 2)
    c.showPage()


def create_page2_variations_and_prep(c, width, height):
    """Create page 2: 2x2 grid with Games, AAC, Prep, Storage."""
    accent_y, accent_width = draw_page_border(c, width, height)
    draw_title_in_stripe(c, width, accent_y, accent_width, "QUICK START", "Brown Bear Matching")
    
    # 2x2 grid for content sections
    box_width = 3.5 * inch
    box_height = 2.8 * inch
    h_gap = 0.25 * inch
    v_gap = 0.15 * inch
    
    total_width = box_width * 2 + h_gap
    left_x = (width - total_width) / 2
    right_x = left_x + box_width + h_gap
    
    top_y = accent_y - 0.15 * inch
    bottom_y = top_y - box_height - v_gap
    
    # Top Left: Game Variations
    draw_section_box(c, left_x, top_y, box_width, box_height,
                     "Game Variations", LEVEL_COLORS[2], [
        "Memory Match: Use extra target",
        "card. Turn cutouts face-down.",
        "Student turns over to find match.",
        "",
        "Sort & Match: Lay multiple",
        "targets. Sort all cutouts.",
        "",
        "Speed Match: Time it! Track",
        "progress and celebrate wins.",
    ])
    
    # Top Right: AAC & Praise
    draw_section_box(c, right_x, top_y, box_width, box_height,
                     "AAC & Praise", LEVEL_COLORS[1], [
        "Model AAC symbol use",
        "Core words: match, same, find",
        "",
        "Praise phrases:",
        "• 'Great matching!'",
        "• 'You found it!'",
        "• 'Keep looking carefully!'",
        "",
        "Allow response time (10 sec)",
    ])
    
    # Bottom Left: Preparation
    draw_section_box(c, left_x, bottom_y, box_width, box_height,
                     "Preparation", LEVEL_COLORS[3], [
        "Print: Cardstock (110lb+)",
        "Laminate: 3-5 mil pouches",
        "",
        "Velcro:",
        "• HOOK (rough) → activity boxes",
        "• LOOP (soft) → cutout backs",
        "",
        "Cut: Guillotine strips first,",
        "then individual icons",
    ])
    
    # Bottom Right: Storage
    draw_section_box(c, right_x, bottom_y, box_width, box_height,
                     "Storage", LEVEL_COLORS[4], [
        "Use manila file folders",
        "One folder per level",
        "",
        "Color-code folders:",
        "L1=Orange, L2=Blue",
        "L3=Green, L4=Purple",
        "",
        "Store cutouts in ziplock",
        "Keep flat, attach label",
    ])
    
    draw_footer(c, width, 2, 2)
    c.showPage()


def draw_section_box(c, x, y, box_width, box_height, title, color, lines):
    """Draw a section box with colored header and content that fills the space."""
    # Background box
    c.setFillColor(LIGHT_GREY)
    c.roundRect(x, y - box_height, box_width, box_height, 8, stroke=0, fill=1)
    
    # Colored header bar
    header_height = 0.35 * inch
    c.setFillColor(color)
    c.roundRect(x, y - header_height, box_width, header_height, 8, stroke=0, fill=1)
    c.rect(x, y - header_height, box_width, 10, stroke=0, fill=1)  # Square bottom edge
    
    # Title - WHITE, CENTERED
    c.setFillColor(white)
    c.setFont(TITLE_FONT, BODY_SIZE + 1)
    c.drawCentredString(x + box_width/2, y - header_height + 0.1*inch, title)
    
    # Content lines - CENTERED, evenly spaced to fill box
    c.setFillColor(DARK_GREY)
    c.setFont(BODY_FONT, BODY_SIZE)
    
    text_y = y - header_height - 0.25*inch
    line_spacing = 0.2 * inch
    for line in lines:
        c.drawCentredString(x + box_width/2, text_y, line)
        text_y -= line_spacing


def generate_quick_start_pdf(output_path, pack_code="BB03", theme_name="Brown Bear"):
    """Generate the complete Quick Start Instructions PDF."""
    width, height = letter
    
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Page 1: How to Play
    create_page1_how_to_play(c, width, height)
    
    # Page 2: Variations & Preparation
    create_page2_variations_and_prep(c, width, height)
    
    c.save()
    print(f"✓ Generated: {output_path}")
    return output_path


if __name__ == "__main__":
    # Generate to review_pdfs and samples folders
    os.makedirs("review_pdfs", exist_ok=True)
    os.makedirs("samples/brown_bear/matching", exist_ok=True)
    
    generate_quick_start_pdf("review_pdfs/brown_bear_matching_quick_start.pdf")
    generate_quick_start_pdf("samples/brown_bear/matching/brown_bear_matching_quick_start.pdf")
    
    print("\n✓ Quick Start Instructions generated!")
    print("  - review_pdfs/brown_bear_matching_quick_start.pdf")
    print("  - samples/brown_bear/matching/brown_bear_matching_quick_start.pdf")
