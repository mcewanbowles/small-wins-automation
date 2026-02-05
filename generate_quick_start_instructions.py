#!/usr/bin/env python3
"""
Quick Start Instructions Generator for Matching Activity
Creates a professional 2-page PDF with instructions for all levels.
Matches the branding of the Matching Product exactly.
"""

import os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black

# Level colors - SAME as matching product
LEVEL_COLORS = {
    1: HexColor('#F4A259'),  # Orange - Errorless
    2: HexColor('#4A90E2'),  # Blue - Easy
    3: HexColor('#7BC47F'),  # Green - Medium
    4: HexColor('#9B59B6'),  # Purple - Hard
}

# Brand colors - SAME as matching product
LIGHT_BLUE_BORDER = HexColor('#A0C4E8')  # Light blue border for pages
WARM_ORANGE = HexColor('#F5A623')
PRIMARY_BLUE = HexColor('#4A90E2')
LIGHT_GREY = HexColor('#F0F0F0')
DARK_GREY = HexColor('#333333')
NAVY = HexColor('#001F3F')

# Fixed page structure - SAME as matching product
BORDER_MARGIN = 0.25 * inch
ACCENT_MARGIN = 0.08 * inch
ACCENT_HEIGHT = 1.0 * inch
FOOTER_HEIGHT = 0.55 * inch  # Space for 2-line footer within border


def draw_page_border(c, width, height):
    """Draw rounded rectangle border with accent stripe - MATCHES MATCHING PRODUCT."""
    content_width = width - 2 * BORDER_MARGIN
    content_height = height - 2 * BORDER_MARGIN
    
    # Border - Light blue, rounded corners, 3px stroke
    c.setStrokeColor(LIGHT_BLUE_BORDER)
    c.setLineWidth(3)
    c.roundRect(BORDER_MARGIN, BORDER_MARGIN, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent stripe - positioned with margin from border, rounded corners
    accent_x = BORDER_MARGIN + ACCENT_MARGIN
    accent_y = height - BORDER_MARGIN - ACCENT_HEIGHT - ACCENT_MARGIN - 0.1 * inch
    accent_width = content_width - 2 * ACCENT_MARGIN
    
    c.setFillColor(WARM_ORANGE)
    c.roundRect(accent_x, accent_y, accent_width, ACCENT_HEIGHT, 8, stroke=0, fill=1)
    
    return accent_y  # Return position for title placement


def draw_footer(c, width, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear"):
    """Draw 2-line footer INSIDE the border."""
    # Footer positioned within the border
    footer_y1 = BORDER_MARGIN + 0.35 * inch
    footer_y2 = BORDER_MARGIN + 0.15 * inch
    
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    line1 = f"{pack_code} | {theme_name} | Quick Start Instructions | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y1, line1)
    
    c.setFont("Helvetica", 8)
    line2 = "© 2025 Small Wins Studio • For personal and classroom use only"
    c.drawCentredString(width/2, footer_y2, line2)


def draw_level_box(c, x, y, box_width, box_height, level, title, instructions):
    """Draw a color-coded level instruction box with proper alignment."""
    color = LEVEL_COLORS[level]
    
    # Header box with level color - rounded corners, centered text
    header_height = 0.4 * inch
    c.setFillColor(color)
    c.roundRect(x, y - header_height, box_width, header_height, 6, stroke=0, fill=1)
    
    # Level title in white - CENTERED in header
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    title_width = c.stringWidth(title, "Helvetica-Bold", 11)
    c.drawString(x + (box_width - title_width) / 2, y - header_height + 0.12*inch, title)
    
    # Instructions below - properly spaced
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica", 9)
    
    text_y = y - header_height - 0.22*inch
    line_spacing = 0.17 * inch
    for line in instructions:
        c.drawString(x + 0.12*inch, text_y, line)
        text_y -= line_spacing
    
    return text_y


def create_page1_how_to_play(c, width, height):
    """Create page 1 with How to Play instructions for each level."""
    accent_y = draw_page_border(c, width, height)
    
    # Title in accent stripe - CENTERED both horizontally and vertically
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 32)
    title_y = accent_y + ACCENT_HEIGHT / 2 + 8
    c.drawCentredString(width/2, title_y, "Quick Start Instructions")
    
    # Subtitle below title in accent stripe
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica-Bold", 20)
    subtitle_y = title_y - 28
    c.drawCentredString(width/2, subtitle_y, "Brown Bear")
    
    # Section title - "How to Play"
    section_y = accent_y - 0.25 * inch
    c.setFillColor(PRIMARY_BLUE)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, section_y, "How to Play - Matching Activity")
    
    # Introduction - properly spaced and centered
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica", 10)
    intro_y = section_y - 0.35 * inch
    intro_text = [
        "This matching activity helps students develop visual discrimination, attention,",
        "and matching skills. Each level increases in difficulty with more distractors.",
        "Start with Level 1 and progress as the student demonstrates mastery (80%+ accuracy)."
    ]
    for line in intro_text:
        c.drawCentredString(width/2, intro_y, line)
        intro_y -= 0.18*inch
    
    # Level boxes - aligned in 2x2 grid, properly spaced
    box_width = 3.4 * inch
    box_height = 1.75 * inch
    h_gap = 0.35 * inch  # Horizontal gap between boxes
    v_gap = 0.2 * inch   # Vertical gap between rows
    
    # Calculate centered positions
    total_width = box_width * 2 + h_gap
    left_x = (width - total_width) / 2
    right_x = left_x + box_width + h_gap
    
    # Level 1 - Top Left
    level1_y = intro_y - 0.2*inch
    level1_instructions = [
        "• 5 matching pictures, 0 distractors",
        "• Errorless learning - all answers are correct!",
        "• Builds confidence and understanding",
        "• Watermarks provide visual guides",
        "Tip: Perfect for introduction activities"
    ]
    draw_level_box(c, left_x, level1_y, box_width, box_height, 1, 
                   "Level 1 - Errorless Learning", level1_instructions)
    
    # Level 2 - Top Right
    level2_instructions = [
        "• 4 matching pictures, 1 distractor",
        "• Student identifies the one that doesn't match",
        "• Low frustration discrimination practice",
        "• Praise correct matches enthusiastically",
        "Tip: Say \"Find the [target]\" to prompt"
    ]
    draw_level_box(c, right_x, level1_y, box_width, box_height, 2,
                   "Level 2 - Easy", level2_instructions)
    
    # Level 3 - Bottom Left
    level3_y = level1_y - box_height - v_gap
    level3_instructions = [
        "• 3 matching pictures, 2 distractors",
        "• Moderate challenge for developing skills",
        "• Encourage verbalization of choices",
        "• Set aside distractors when found",
        "Tip: Ask \"Does this match?\" for each"
    ]
    draw_level_box(c, left_x, level3_y, box_width, box_height, 3,
                   "Level 3 - Medium", level3_instructions)
    
    # Level 4 - Bottom Right
    level4_instructions = [
        "• 1 matching picture, 4 distractors",
        "• Most challenging - true discrimination",
        "• Student finds the ONE correct match",
        "• Great for assessment and mastery",
        "Tip: Celebrate success enthusiastically!"
    ]
    draw_level_box(c, right_x, level3_y, box_width, box_height, 4,
                   "Level 4 - Challenge", level4_instructions)
    
    # General tips section - properly spaced within border
    tips_y = level3_y - box_height - 0.15*inch
    tips_box_height = tips_y - BORDER_MARGIN - FOOTER_HEIGHT - 0.1*inch
    tips_box_y = tips_y - tips_box_height
    
    c.setFillColor(LIGHT_GREY)
    c.roundRect(left_x, tips_box_y, total_width, tips_box_height, 8, stroke=0, fill=1)
    
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width/2, tips_y - 0.22*inch, "💡 General Tips for Success")
    
    c.setFont("Helvetica", 9)
    tips = [
        "• Start with Level 1 until 80% accuracy, then progress",
        "• Use AAC symbols and core vocabulary: match, same, find, look",
        "• Model the activity first before independent practice",
        "• Allow adequate response time - count to 10 silently",
        "• Praise effort AND accuracy: \"Great trying!\", \"You're looking carefully!\""
    ]
    tips_text_y = tips_y - 0.45*inch
    line_spacing = 0.17 * inch
    for tip in tips:
        c.drawCentredString(width/2, tips_text_y, tip)
        tips_text_y -= line_spacing
    
    draw_footer(c, width, 1, 2)
    c.showPage()


def create_page2_variations_and_prep(c, width, height):
    """Create page 2 with game variations, AAC tips, and preparation instructions."""
    accent_y = draw_page_border(c, width, height)
    
    # Title in accent stripe - CENTERED both horizontally and vertically (same as page 1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 32)
    title_y = accent_y + ACCENT_HEIGHT / 2 + 8
    c.drawCentredString(width/2, title_y, "Quick Start Instructions")
    
    # Subtitle below title in accent stripe
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica-Bold", 20)
    subtitle_y = title_y - 28
    c.drawCentredString(width/2, subtitle_y, "Brown Bear")
    
    # Calculate column positions - properly centered with gap
    col_width = 3.3 * inch
    col_gap = 0.4 * inch
    total_width = col_width * 2 + col_gap
    left_x = (width - total_width) / 2
    right_x = left_x + col_width + col_gap
    
    content_start_y = accent_y - 0.2 * inch
    
    # Left column - Game Variations
    c.setFillColor(PRIMARY_BLUE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(left_x, content_start_y, "🎮 Game Variations")
    
    c.setFillColor(DARK_GREY)
    variations_y = content_start_y - 0.3*inch
    
    variations = [
        ("Memory Match", "Use the extra target card! Turn cutouts face-down.", 
         "Student turns over to find matches."),
        ("Sort & Match", "Lay multiple target cards on the table.",
         "Student sorts all cutouts to correct targets."),
        ("Find the Match", "Spread 5 cutouts face-up. Show target and",
         "ask \"Which one matches?\" Quick practice."),
        ("Speed Match", "Time how quickly student can match all 5.",
         "Track progress. Builds fluency."),
        ("Partner Play", "Two students take turns matching. One holds",
         "target, other finds match. Great for social skills.")
    ]
    
    for title, line1, line2 in variations:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left_x, variations_y, f"• {title}")
        c.setFont("Helvetica", 8)
        variations_y -= 0.14*inch
        c.drawString(left_x + 0.12*inch, variations_y, line1)
        variations_y -= 0.12*inch
        c.drawString(left_x + 0.12*inch, variations_y, line2)
        variations_y -= 0.18*inch
    
    # AAC & Praise section
    aac_y = variations_y - 0.1*inch
    c.setFillColor(PRIMARY_BLUE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(left_x, aac_y, "✨ Using AAC & Praise")
    
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica", 9)
    aac_tips = [
        "• Model AAC symbol use during the activity",
        "• Use core words: match, same, look, find",
        "• Praise: \"Great matching!\", \"You found it!\"",
        "• Allow response time (count to 10 silently)",
        "• Accept all communication forms",
        "• Celebrate small wins with enthusiasm!"
    ]
    aac_y -= 0.28*inch
    for tip in aac_tips:
        c.drawString(left_x, aac_y, tip)
        aac_y -= 0.16*inch
    
    # Right column - Preparation & Storage
    prep_y = content_start_y
    c.setFillColor(PRIMARY_BLUE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(right_x, prep_y, "🔧 Preparation")
    
    c.setFillColor(DARK_GREY)
    prep_y -= 0.3*inch
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(right_x, prep_y, "Printing:")
    c.setFont("Helvetica", 9)
    prep_y -= 0.17*inch
    printing = [
        "• Print on cardstock (110lb or heavier)",
        "• Use color version for best results",
        "• BW version works for budget printing"
    ]
    for line in printing:
        c.drawString(right_x, prep_y, line)
        prep_y -= 0.14*inch
    
    prep_y -= 0.08*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(right_x, prep_y, "Laminating:")
    c.setFont("Helvetica", 9)
    prep_y -= 0.17*inch
    laminating = [
        "• Laminate all pages for durability",
        "• Use 3-5 mil laminating pouches",
        "• Round corners for safety (optional)"
    ]
    for line in laminating:
        c.drawString(right_x, prep_y, line)
        prep_y -= 0.14*inch
    
    prep_y -= 0.08*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(right_x, prep_y, "Velcro Application:")
    c.setFont("Helvetica", 9)
    prep_y -= 0.17*inch
    velcro = [
        "• HOOK side (rough): activity page boxes",
        "• LOOP side (soft): back of cutout icons",
        "• Use 3/4\" velcro dots or strips",
        "• Press firmly, let adhesive cure 24hrs"
    ]
    for line in velcro:
        c.drawString(right_x, prep_y, line)
        prep_y -= 0.14*inch
    
    prep_y -= 0.08*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(right_x, prep_y, "Cutting Cutouts:")
    c.setFont("Helvetica", 9)
    prep_y -= 0.17*inch
    cutting = [
        "• Cut strips on guillotine paper cutter",
        "• Then cut individual icons from strips",
        "• Icons are sized for easy handling"
    ]
    for line in cutting:
        c.drawString(right_x, prep_y, line)
        prep_y -= 0.14*inch
    
    # Storage section
    storage_y = prep_y - 0.12*inch
    c.setFillColor(PRIMARY_BLUE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(right_x, storage_y, "📁 Storage Tips")
    
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica", 9)
    storage_y -= 0.28*inch
    storage = [
        "• Use manila file folders for each level",
        "• Attach storage label to folder front",
        "• Color-code folders to match levels:",
        "  L1=Orange, L2=Blue, L3=Green, L4=Purple",
        "• Store cutouts in small ziplock bags",
        "• Store flat to prevent warping"
    ]
    for line in storage:
        c.drawString(right_x, storage_y, line)
        storage_y -= 0.14*inch
    
    # Bottom tip box - aligned with footer
    tip_box_y = BORDER_MARGIN + FOOTER_HEIGHT + 0.1*inch
    tip_box_height = 0.55 * inch
    tip_box_width = total_width
    
    c.setFillColor(LEVEL_COLORS[1])  # Orange
    c.roundRect(left_x, tip_box_y, tip_box_width, tip_box_height, 8, stroke=0, fill=1)
    
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width/2, tip_box_y + tip_box_height - 0.2*inch, 
                        "💡 Pro Tip: Create a complete set for each student or classroom station!")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, tip_box_y + tip_box_height - 0.4*inch,
                        "Label everything clearly and train aides/parents on how to use each level.")
    
    draw_footer(c, width, 2, 2)
    c.showPage()


def generate_quick_start_instructions(output_path, pack_code="BB03", theme_name="Brown Bear"):
    """Generate the complete Quick Start Instructions PDF."""
    width, height = letter
    
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Page 1: How to Play
    create_page1_how_to_play(c, width, height)
    
    # Page 2: Game Variations, AAC, Preparation, Storage
    create_page2_variations_and_prep(c, width, height)
    
    c.save()
    print(f"✓ Quick Start Instructions saved: {output_path}")
    return output_path


if __name__ == "__main__":
    # Output paths
    SAMPLES_DIR = "/home/runner/work/small-wins-automation/small-wins-automation/samples/brown_bear/matching"
    REVIEW_DIR = "/home/runner/work/small-wins-automation/small-wins-automation/review_pdfs"
    
    # Ensure directories exist
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    os.makedirs(REVIEW_DIR, exist_ok=True)
    
    print("=" * 60)
    print("Quick Start Instructions Generator")
    print("=" * 60)
    
    # Generate to samples folder
    samples_path = os.path.join(SAMPLES_DIR, "brown_bear_matching_quick_start.pdf")
    generate_quick_start_instructions(samples_path)
    
    # Copy to review folder
    review_path = os.path.join(REVIEW_DIR, "brown_bear_matching_quick_start.pdf")
    generate_quick_start_instructions(review_path)
    
    print("\n" + "=" * 60)
    print("✓ QUICK START INSTRUCTIONS GENERATED")
    print("=" * 60)
    print(f"\nSamples: {samples_path}")
    print(f"Review: {review_path}")
