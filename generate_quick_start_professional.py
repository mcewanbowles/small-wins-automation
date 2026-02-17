#!/usr/bin/env python3
"""
Professional Quick Start Instructions Generator
Creates comprehensive Quick Start PDFs for Matching and Find & Cover
with teal branding, level colors as accents, and extensive guidance
for students with complex communication and special needs.

Design Brief (per TPT amendments):
- Primary Brand Color: Teal #008B8B
- Level Colors: Orange #FF8C42, Blue #4A90E2, Green #7CB342, Purple #9C27B0
- Font: Comic Sans MS throughout (centered titles)
- Layout: Professional, uncluttered, easy to read
- Content: Comprehensive tips for special needs, AAC support, game variations
- Consistent spacing, alignment, and branding
"""

import os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Try to register Comic Sans (Windows paths first, then Linux fallback)
try:
    pdfmetrics.registerFont(TTFont('ComicSans', 'C:/Windows/Fonts/comic.ttf'))
    pdfmetrics.registerFont(TTFont('ComicSans-Bold', 'C:/Windows/Fonts/comicbd.ttf'))
    TITLE_FONT = 'ComicSans-Bold'
    BODY_FONT = 'ComicSans'
except Exception:
    try:
        pdfmetrics.registerFont(TTFont('ComicSans', '/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf'))
        pdfmetrics.registerFont(TTFont('ComicSans-Bold', '/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS_Bold.ttf'))
        TITLE_FONT = 'ComicSans-Bold'
        BODY_FONT = 'ComicSans'
    except Exception:
        TITLE_FONT = 'Helvetica-Bold'
        BODY_FONT = 'Helvetica'

# Typography per design brief
MAIN_TITLE_SIZE = 18  # Main title
SUBTITLE_SIZE = 14    # "QUICK START"
SECTION_HEADER_SIZE = 12  # Section headings
BODY_SIZE = 10        # Body text

# Brand colors per design brief
TEAL = HexColor('#008B8B')         # Primary brand color
TEXT_COLOR = HexColor('#2C3E50')   # Dark gray for text
BACKGROUND = HexColor('#FFFFFF')   # White background
SECTION_BG = HexColor('#F5F5F5')   # Subtle gray sections
BORDER_COLOR = HexColor('#008B8B') # Teal border

# Level colors (used as accents only)
LEVEL_COLORS = {
    1: HexColor('#FF8C42'),  # Orange
    2: HexColor('#4A90E2'),  # Blue
    3: HexColor('#7CB342'),  # Green
    4: HexColor('#9C27B0'),  # Purple
    5: HexColor('#E74C3C'),  # Red
}

# Page layout
BORDER_MARGIN = 0.4 * inch
HEADER_HEIGHT = 0.7 * inch


def draw_page_border(c, width, height):
    """Draw page border in teal."""
    c.setStrokeColor(BORDER_COLOR)
    c.setLineWidth(2)
    c.roundRect(BORDER_MARGIN, BORDER_MARGIN, 
                width - 2*BORDER_MARGIN, height - 2*BORDER_MARGIN, 
                10, stroke=1, fill=0)


def draw_header(c, width, height, product_name, theme_name):
    """Draw header with teal accent and centered titles."""
    header_y = height - BORDER_MARGIN - HEADER_HEIGHT
    header_width = width - 2*BORDER_MARGIN - 0.2*inch
    
    # Teal accent bar
    c.setFillColor(TEAL)
    c.roundRect(BORDER_MARGIN + 0.1*inch, header_y, 
                header_width, HEADER_HEIGHT, 8, stroke=0, fill=1)
    
    # "QUICK START" subtitle - white, centered
    c.setFillColor(white)
    c.setFont(BODY_FONT, SUBTITLE_SIZE)
    c.drawCentredString(width/2, header_y + HEADER_HEIGHT - 0.25*inch, "QUICK START")
    
    # Main title - white, bold, centered
    c.setFont(TITLE_FONT, MAIN_TITLE_SIZE)
    title = f"{theme_name} {product_name}"
    c.drawCentredString(width/2, header_y + 0.15*inch, title)
    
    return header_y


def draw_level_card(c, x, y, card_width, card_height, level, title, bullets):
    """Draw a level card with colored left border accent (not full background)."""
    color = LEVEL_COLORS[level]
    
    # White card background with subtle gray
    c.setFillColor(white)
    c.roundRect(x, y, card_width, card_height, 6, stroke=0, fill=1)
    
    # Thin border
    c.setStrokeColor(HexColor('#DDDDDD'))
    c.setLineWidth(1)
    c.roundRect(x, y, card_width, card_height, 6, stroke=1, fill=0)
    
    # Colored left border accent (thin stripe)
    accent_width = 4
    c.setFillColor(color)
    c.rect(x, y, accent_width, card_height, stroke=0, fill=1)
    
    # Level badge - small circular badge with level number
    badge_x = x + 0.2*inch
    badge_y = y + card_height - 0.25*inch
    badge_radius = 0.12*inch
    c.setFillColor(color)
    c.circle(badge_x, badge_y, badge_radius, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont(TITLE_FONT, 8)
    c.drawCentredString(badge_x, badge_y - 3, f"L{level}")
    
    # Title - teal color
    c.setFillColor(TEAL)
    c.setFont(TITLE_FONT, SECTION_HEADER_SIZE)
    c.drawString(x + 0.4*inch, y + card_height - 0.28*inch, title)
    
    # Bullets - dark gray
    c.setFillColor(TEXT_COLOR)
    c.setFont(BODY_FONT, BODY_SIZE)
    text_y = y + card_height - 0.5*inch
    for bullet in bullets:
        c.drawString(x + 0.15*inch, text_y, f"• {bullet}")
        text_y -= 0.16*inch


def draw_section(c, x, y, section_width, section_height, title, color, lines):
    """Draw a section with teal header and content."""
    # White background
    c.setFillColor(SECTION_BG)
    c.roundRect(x, y, section_width, section_height, 6, stroke=0, fill=1)
    
    # Thin border
    c.setStrokeColor(HexColor('#DDDDDD'))
    c.setLineWidth(1)
    c.roundRect(x, y, section_width, section_height, 6, stroke=1, fill=0)
    
    # Colored top accent line
    c.setFillColor(color)
    c.rect(x, y + section_height - 3, section_width, 3, stroke=0, fill=1)
    
    # Title - teal
    c.setFillColor(TEAL)
    c.setFont(TITLE_FONT, SECTION_HEADER_SIZE - 1)
    c.drawString(x + 0.1*inch, y + section_height - 0.22*inch, title)
    
    # Content - dark gray
    c.setFillColor(TEXT_COLOR)
    c.setFont(BODY_FONT, BODY_SIZE - 1)
    text_y = y + section_height - 0.4*inch
    for line in lines:
        c.drawString(x + 0.08*inch, text_y, line)
        text_y -= 0.13*inch


def draw_footer(c, width, pack_code, theme_name, product_name):
    """Draw footer with Small Wins Studio branding and star logo."""
    footer_y = BORDER_MARGIN + 0.15*inch
    
    c.setFillColor(TEXT_COLOR)
    c.setFont(BODY_FONT, 8)
    
    # Build footer text with star logo rising above the S of Small Wins
    footer_text = f"Small Wins Studio | PCS symbols used with active PCS Maker Personal License. | © 2026"
    text_width = c.stringWidth(footer_text, BODY_FONT, 8)
    
    # Position text centered, but leave room for star before "Small"
    # Star logo goes just before "Small Wins Studio" - slightly larger, rising above S
    logo_path = Path(__file__).parent / "assets" / "branding" / "small_wins_logo.png" / "star.png"
    
    # Calculate text position (centered)
    text_x = (width - text_width) / 2
    
    if logo_path.exists():
        # Draw the star logo - slightly larger (14pt height) rising above the "S"
        logo_size = 14  # Larger than text so star rises above
        # Position star just before "Small" (after "© 2025 ")
        logo_y = footer_y - 2
        logo_x = text_x - logo_size - 2
        c.drawImage(str(logo_path), logo_x, logo_y, width=logo_size, height=logo_size, 
                   preserveAspectRatio=True, mask='auto')
        c.drawCentredString(width/2, footer_y, footer_text)
    else:
        # Fallback: no logo, just centered text
        c.drawCentredString(width/2, footer_y, footer_text)


def generate_matching_quick_start(output_path, theme_name="Brown Bear", pack_code="BB03"):
    """Generate professional Matching Quick Start (single page)."""
    width, height = letter
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Page structure
    draw_page_border(c, width, height)
    header_y = draw_header(c, width, height, "Matching", theme_name)
    
    # 5 level cards: 3 on top row, 2 on bottom row
    card_width = 2.35 * inch
    card_height = 1.20 * inch
    h_gap = 0.12 * inch
    v_gap = 0.08 * inch
    
    total_width_3 = card_width * 3 + h_gap * 2
    left_x = (width - total_width_3) / 2
    
    top_y = header_y - 0.08*inch - card_height
    bottom_y = top_y - card_height - v_gap
    
    # Row 1: Levels 1-3
    draw_level_card(c, left_x, top_y, card_width, card_height, 1,
                    "Errorless", [
                        "ALL 5 match - 0 distractors",
                        "100% success, builds confidence",
                    ])
    draw_level_card(c, left_x + card_width + h_gap, top_y, card_width, card_height, 2,
                    "Easy", [
                        "4 matching + 1 distractor",
                        "Low frustration discrimination",
                    ])
    draw_level_card(c, left_x + 2*(card_width + h_gap), top_y, card_width, card_height, 3,
                    "Medium", [
                        "3 matching + 2 distractors",
                        "Builds visual search skills",
                    ])
    
    # Row 2: Levels 4-5 (centered)
    total_width_2 = card_width * 2 + h_gap
    row2_left = (width - total_width_2) / 2
    draw_level_card(c, row2_left, bottom_y, card_width, card_height, 4,
                    "Challenge", [
                        "1-2 matches + 3-4 distractors",
                        "True discrimination task",
                    ])
    draw_level_card(c, row2_left + card_width + h_gap, bottom_y, card_width, card_height, 5,
                    "Extension", [
                        "Hardest distractor pattern",
                        "For students ready to extend",
                    ])
    
    total_width = total_width_3
    
    # Tips section - full width with more content
    tips_y = bottom_y - 0.1*inch
    tips_height = 0.9*inch
    tips_box_y = tips_y - tips_height
    
    c.setFillColor(SECTION_BG)
    c.roundRect(left_x, tips_box_y, total_width, tips_height, 6, stroke=0, fill=1)
    
    c.setFillColor(TEAL)
    c.setFont(TITLE_FONT, SECTION_HEADER_SIZE)
    c.drawCentredString(width/2, tips_box_y + tips_height - 0.18*inch, "💡 Tips for Complex Learners & Special Needs")
    
    c.setFillColor(TEXT_COLOR)
    c.setFont(BODY_FONT, BODY_SIZE - 1)
    tips = [
        "✓ Start at Level 1 until 80% accuracy achieved before moving up",
        "✓ Allow 10-15 seconds processing time before prompting",
        "✓ Use hand-over-hand guidance, then fade to pointing, then independence",
        "✓ Accept AAC responses (device, sign, pointing) - don't require verbal speech",
    ]
    tip_y = tips_box_y + tips_height - 0.38*inch
    for tip in tips:
        c.drawCentredString(width/2, tip_y, tip)
        tip_y -= 0.14*inch
    
    # 3-column bottom section with enhanced content
    section_width = (total_width - 2*h_gap) / 3
    section_height = 1.55*inch
    section_y = tips_box_y - 0.1*inch - section_height
    
    # Game Variations - More activities
    draw_section(c, left_x, section_y, section_width, section_height,
                 "🎮 Game Variations", LEVEL_COLORS[2], [
                     "Memory Match: Turn",
                     "cutouts face-down,",
                     "find matching pairs!",
                     "Speed Match: Use a",
                     "timer, track progress",
                     "Choice: \"Show me dog\"",
                 ])
    
    # AAC & Communication - Detailed prompts
    draw_section(c, left_x + section_width + h_gap, section_y, section_width, section_height,
                 "🎙️ AAC & Prompts", LEVEL_COLORS[1], [
                     "Core Words: match,",
                     "same, find, look, more",
                     "Model on device first",
                     "Praise: \"Great finding!\"",
                     "\"You matched it!\"",
                     "\"Good looking!\"",
                 ])
    
    # Preparation & Storage
    draw_section(c, left_x + 2*(section_width + h_gap), section_y, section_width, section_height,
                 "🔧 Prep & Storage", LEVEL_COLORS[3], [
                     "Print: cardstock",
                     "Laminate: 3-5 mil",
                     "Velcro: hook on box",
                     "loop on cutouts",
                     "Color-code folders",
                     "by level colors",
                 ])
    
    draw_footer(c, width, pack_code, theme_name, "Matching")
    c.save()
    print(f"OK Generated: {output_path}")


def generate_find_cover_quick_start(output_path, theme_name="Brown Bear", pack_code="BB04"):
    """Generate professional Find & Cover Quick Start (single page)."""
    width, height = letter
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Page structure
    draw_page_border(c, width, height)
    header_y = draw_header(c, width, height, "Find & Cover", theme_name)
    
    # 5 level cards: 3 on top row, 2 on bottom row
    card_width = 2.35 * inch
    card_height = 1.20 * inch
    h_gap = 0.12 * inch
    v_gap = 0.08 * inch
    
    total_width_3 = card_width * 3 + h_gap * 2
    left_x = (width - total_width_3) / 2
    
    top_y = header_y - 0.08*inch - card_height
    bottom_y = top_y - card_height - v_gap
    
    # Row 1: Levels 1-3
    draw_level_card(c, left_x, top_y, card_width, card_height, 1,
                    "Errorless", [
                        "ALL icons match - 100% success",
                        "Great for introducing activity",
                    ])
    draw_level_card(c, left_x + card_width + h_gap, top_y, card_width, card_height, 2,
                    "Supported", [
                        "Some matches + distractors",
                        "Great with prompting support",
                    ])
    draw_level_card(c, left_x + 2*(card_width + h_gap), top_y, card_width, card_height, 3,
                    "Independent", [
                        "More distractors in field",
                        "Builds scanning skills",
                    ])
    
    # Row 2: Levels 4-5 (centered)
    total_width_2 = card_width * 2 + h_gap
    row2_left = (width - total_width_2) / 2
    draw_level_card(c, row2_left, bottom_y, card_width, card_height, 4,
                    "Generalisation", [
                        "Complex fields, fewer matches",
                        "Higher-level discrimination",
                    ])
    draw_level_card(c, row2_left + card_width + h_gap, bottom_y, card_width, card_height, 5,
                    "Extension", [
                        "Hardest distractor pattern",
                        "For students ready to extend",
                    ])
    
    total_width = total_width_3
    
    # Tips section - full width with more content
    tips_y = bottom_y - 0.1*inch
    tips_height = 0.9*inch
    tips_box_y = tips_y - tips_height
    
    c.setFillColor(SECTION_BG)
    c.roundRect(left_x, tips_box_y, total_width, tips_height, 6, stroke=0, fill=1)
    
    c.setFillColor(TEAL)
    c.setFont(TITLE_FONT, SECTION_HEADER_SIZE)
    c.drawCentredString(width/2, tips_box_y + tips_height - 0.18*inch, "💡 Tips for Complex Learners & Special Needs")
    
    c.setFillColor(TEXT_COLOR)
    c.setFont(BODY_FONT, BODY_SIZE - 1)
    tips = [
        "✓ Use bingo daubers, chips, or dry-erase markers to cover targets",
        "✓ Point to each icon while searching - model the visual scanning",
        "✓ Allow 10-15 seconds processing time before prompting",
        "✓ Accept any communication method - pointing, device, sign language",
    ]
    tip_y = tips_box_y + tips_height - 0.38*inch
    for tip in tips:
        c.drawCentredString(width/2, tip_y, tip)
        tip_y -= 0.14*inch
    
    # 3-column bottom section with enhanced content
    section_width = (total_width - 2*h_gap) / 3
    section_height = 1.55*inch
    section_y = tips_box_y - 0.1*inch - section_height
    
    # Game Variations - More activities
    draw_section(c, left_x, section_y, section_width, section_height,
                 "🎮 Game Variations", LEVEL_COLORS[2], [
                     "Race: Who covers all",
                     "targets first?",
                     "Count: How many did",
                     "you find? Count aloud!",
                     "Point & Name: Say",
                     "what you found!",
                 ])
    
    # AAC & Communication - Detailed prompts
    draw_section(c, left_x + section_width + h_gap, section_y, section_width, section_height,
                 "🎙️ AAC & Prompts", LEVEL_COLORS[1], [
                     "Core Words: find,",
                     "cover, same, look, more",
                     "Model on device first",
                     "Praise: \"Great finding!\"",
                     "\"You covered it!\"",
                     "\"Good scanning!\"",
                 ])
    
    # Preparation & Storage
    draw_section(c, left_x + 2*(section_width + h_gap), section_y, section_width, section_height,
                 "🔧 Prep & Storage", LEVEL_COLORS[3], [
                     "Print: cardstock",
                     "Laminate boards",
                     "Use dry-erase for",
                     "reusable covering",
                     "Store flat in folders",
                     "Color-code by level",
                 ])
    
    draw_footer(c, width, pack_code, theme_name, "Find & Cover")
    c.save()
    print(f"OK Generated: {output_path}")


if __name__ == "__main__":
    # Create output directories
    os.makedirs("review_pdfs", exist_ok=True)
    os.makedirs("samples/brown_bear/matching", exist_ok=True)
    os.makedirs("samples/brown_bear/find_cover", exist_ok=True)
    
    # Generate Matching Quick Start
    generate_matching_quick_start("review_pdfs/brown_bear_matching_quick_start.pdf")
    generate_matching_quick_start("samples/brown_bear/matching/brown_bear_matching_quick_start.pdf")
    
    # Generate Find & Cover Quick Start
    generate_find_cover_quick_start("review_pdfs/brown_bear_find_cover_quick_start.pdf")
    generate_find_cover_quick_start("samples/brown_bear/find_cover/brown_bear_find_cover_quick_start.pdf")
    
    print("\nOK Professional Quick Start guides generated!")
    print("  Matching: review_pdfs/brown_bear_matching_quick_start.pdf")
    print("  Find & Cover: review_pdfs/brown_bear_find_cover_quick_start.pdf")
