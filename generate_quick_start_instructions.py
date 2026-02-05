#!/usr/bin/env python3
"""
Quick Start Instructions Generator for Matching Activity
Creates a professional 2-page PDF with instructions for all levels.
"""

import os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black

# Level colors
LEVEL_COLORS = {
    1: HexColor('#F4A259'),  # Orange - Errorless
    2: HexColor('#4A90E2'),  # Blue - Easy
    3: HexColor('#7BC47F'),  # Green - Medium
    4: HexColor('#9B59B6'),  # Purple - Hard
}

# Brand colors
WARM_ORANGE = HexColor('#F5A623')
PRIMARY_BLUE = HexColor('#4A90E2')
LIGHT_GREY = HexColor('#F5F5F5')
DARK_GREY = HexColor('#333333')


def draw_page_border(c, width, height):
    """Draw rounded rectangle border with accent stripe."""
    margin = 0.5 * inch
    
    # Border
    c.setStrokeColor(PRIMARY_BLUE)
    c.setLineWidth(3)
    c.roundRect(margin, margin, width - 2*margin, height - 2*margin, 10, stroke=1, fill=0)
    
    # Accent stripe
    c.setFillColor(WARM_ORANGE)
    stripe_height = 0.4 * inch
    c.rect(margin, height - margin - stripe_height, width - 2*margin, stripe_height, stroke=0, fill=1)


def draw_footer(c, width, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear"):
    """Draw 2-line footer."""
    footer_y1 = 0.5 * inch + 0.15 * inch
    footer_y2 = 0.5 * inch - 0.05 * inch
    
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    line1 = f"{pack_code} | {theme_name} | Quick Start Instructions | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y1, line1)
    
    c.setFont("Helvetica", 8)
    line2 = "© 2025 Small Wins Studio • For personal and classroom use only"
    c.drawCentredString(width/2, footer_y2, line2)


def draw_level_box(c, x, y, width, height, level, title, instructions):
    """Draw a color-coded level instruction box."""
    color = LEVEL_COLORS[level]
    
    # Header box with level color
    header_height = 0.35 * inch
    c.setFillColor(color)
    c.roundRect(x, y - header_height, width, header_height, 5, stroke=0, fill=1)
    
    # Level title in white
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 0.15*inch, y - header_height + 0.1*inch, title)
    
    # Instructions below
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica", 9)
    
    text_y = y - header_height - 0.2*inch
    for line in instructions:
        c.drawString(x + 0.1*inch, text_y, line)
        text_y -= 0.18*inch
    
    return text_y


def create_page1_how_to_play(c, width, height):
    """Create page 1 with How to Play instructions for each level."""
    draw_page_border(c, width, height)
    
    # Title in accent stripe
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - 0.5*inch - 0.25*inch, "Quick Start Instructions")
    
    # Subtitle
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 1.1*inch, "How to Play - Matching Activity")
    
    # Introduction
    c.setFont("Helvetica", 10)
    intro_y = height - 1.5*inch
    intro_text = [
        "This matching activity helps students develop visual discrimination, attention,",
        "and matching skills. Each level increases in difficulty with more distractors.",
        "Start with Level 1 and progress as the student demonstrates mastery."
    ]
    for line in intro_text:
        c.drawCentredString(width/2, intro_y, line)
        intro_y -= 0.18*inch
    
    # Level boxes
    box_width = 3.5 * inch
    box_height = 1.8 * inch
    left_x = 0.6 * inch
    right_x = 4.3 * inch
    
    # Level 1 - Top Left
    level1_y = height - 2.3*inch
    level1_instructions = [
        "• 5 matching pictures, 0 distractors",
        "• Errorless learning - all answers are correct!",
        "• Place target card at top of activity page",
        "• Student matches all 5 cutout icons to boxes",
        "• Great for introduction and building confidence",
        "Tip: Use Level 1 watermarks as visual guides"
    ]
    draw_level_box(c, left_x, level1_y, box_width, box_height, 1, 
                   "Level 1 - Errorless Learning", level1_instructions)
    
    # Level 2 - Top Right
    level2_y = height - 2.3*inch
    level2_instructions = [
        "• 4 matching pictures, 1 distractor",
        "• Student must identify which 4 match",
        "• Place the distractor aside when found",
        "• Builds discrimination with low frustration",
        "• Continue praising correct matches",
        "Tip: Say \"Find the [target]\" to prompt"
    ]
    draw_level_box(c, right_x, level2_y, box_width, box_height, 2,
                   "Level 2 - Easy", level2_instructions)
    
    # Level 3 - Bottom Left
    level3_y = height - 4.5*inch
    level3_instructions = [
        "• 3 matching pictures, 2 distractors",
        "• Moderate challenge for developing skills",
        "• Student identifies 3 correct matches",
        "• Two icons don't belong - set aside",
        "• Encourage verbalization of choices",
        "Tip: Ask \"Does this match?\" for each"
    ]
    draw_level_box(c, left_x, level3_y, box_width, box_height, 3,
                   "Level 3 - Medium", level3_instructions)
    
    # Level 4 - Bottom Right
    level4_y = height - 4.5*inch
    level4_instructions = [
        "• 1 matching picture, 4 distractors",
        "• Most challenging - true discrimination",
        "• Student finds the ONE correct match",
        "• Four icons are distractors",
        "• Great for assessment and mastery",
        "Tip: Celebrate success enthusiastically!"
    ]
    draw_level_box(c, right_x, level4_y, box_width, box_height, 4,
                   "Level 4 - Challenge", level4_instructions)
    
    # General tips section
    tips_y = height - 6.8*inch
    c.setFillColor(LIGHT_GREY)
    c.roundRect(left_x, tips_y - 1.6*inch, width - 1.2*inch, 1.6*inch, 8, stroke=0, fill=1)
    
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_x + 0.15*inch, tips_y - 0.25*inch, "💡 General Tips for Success")
    
    c.setFont("Helvetica", 9)
    tips = [
        "• Start with Level 1 until student shows 80% accuracy, then progress to next level",
        "• Use AAC symbols and core vocabulary: \"match\", \"same\", \"different\", \"find\", \"look\"",
        "• Model the activity first before asking student to complete independently",
        "• Allow adequate response time - some students need extra processing time",
        "• Praise effort as well as accuracy: \"Great trying!\", \"You're looking carefully!\"",
        "• For students with motor challenges, accept pointing or eye gaze as responses",
        "• Keep sessions short (5-10 minutes) to maintain engagement and attention"
    ]
    tips_text_y = tips_y - 0.5*inch
    for tip in tips:
        c.drawString(left_x + 0.15*inch, tips_text_y, tip)
        tips_text_y -= 0.15*inch
    
    draw_footer(c, width, 1, 2)
    c.showPage()


def create_page2_variations_and_prep(c, width, height):
    """Create page 2 with game variations, AAC tips, and preparation instructions."""
    draw_page_border(c, width, height)
    
    # Title in accent stripe
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - 0.5*inch - 0.25*inch, "Quick Start Instructions")
    
    # Left column - Game Variations
    left_x = 0.6 * inch
    col_width = 3.5 * inch
    
    c.setFillColor(PRIMARY_BLUE)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_x, height - 1.15*inch, "🎮 Game Variations")
    
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica-Bold", 10)
    variations_y = height - 1.45*inch
    
    variations = [
        ("Memory Match", [
            "Use the extra target card! Turn cutouts",
            "face-down. Student turns over cards to",
            "find matches. Great for memory skills."
        ]),
        ("Sort & Match", [
            "Lay multiple target cards on the table.",
            "Student sorts all cutouts to the correct",
            "target. Works well for group activities."
        ]),
        ("Find the Match", [
            "Spread 5 cutouts face-up. Show target",
            "card and ask \"Which one matches?\"",
            "Good for quick discrimination practice."
        ]),
        ("Speed Match", [
            "Time how quickly student can match all",
            "5 icons correctly. Track progress over",
            "time. Builds fluency and confidence."
        ]),
        ("Partner Play", [
            "Two students take turns matching.",
            "One holds the target, other finds match.",
            "Encourages social interaction and turn-taking."
        ])
    ]
    
    for title, desc in variations:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(DARK_GREY)
        c.drawString(left_x, variations_y, f"• {title}")
        c.setFont("Helvetica", 8)
        variations_y -= 0.15*inch
        for line in desc:
            c.drawString(left_x + 0.15*inch, variations_y, line)
            variations_y -= 0.12*inch
        variations_y -= 0.08*inch
    
    # AAC & Praise section
    aac_y = variations_y - 0.15*inch
    c.setFillColor(PRIMARY_BLUE)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_x, aac_y, "✨ Using AAC & Praise")
    
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica", 9)
    aac_tips = [
        "• Model AAC symbol use during the activity",
        "• Use core words: \"match\", \"same\", \"look\", \"find\"",
        "• Praise phrases: \"Great matching!\", \"You found it!\",",
        "  \"That's the same!\", \"Excellent looking!\"",
        "• Allow response time (count to 10 silently)",
        "• Accept all communication forms",
        "• Celebrate small wins with enthusiasm!"
    ]
    aac_y -= 0.25*inch
    for tip in aac_tips:
        c.drawString(left_x, aac_y, tip)
        aac_y -= 0.15*inch
    
    # Right column - Preparation & Storage
    right_x = 4.3 * inch
    
    c.setFillColor(PRIMARY_BLUE)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(right_x, height - 1.15*inch, "🔧 Preparation")
    
    c.setFillColor(DARK_GREY)
    prep_y = height - 1.45*inch
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(right_x, prep_y, "Printing:")
    c.setFont("Helvetica", 9)
    prep_y -= 0.18*inch
    printing = [
        "• Print on cardstock (110lb or heavier)",
        "• Use color version for best results",
        "• BW version works for budget printing"
    ]
    for line in printing:
        c.drawString(right_x, prep_y, line)
        prep_y -= 0.15*inch
    
    prep_y -= 0.1*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(right_x, prep_y, "Laminating:")
    c.setFont("Helvetica", 9)
    prep_y -= 0.18*inch
    laminating = [
        "• Laminate all pages for durability",
        "• Use 3-5 mil laminating pouches",
        "• Round corners for safety (optional)"
    ]
    for line in laminating:
        c.drawString(right_x, prep_y, line)
        prep_y -= 0.15*inch
    
    prep_y -= 0.1*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(right_x, prep_y, "Velcro Application:")
    c.setFont("Helvetica", 9)
    prep_y -= 0.18*inch
    velcro = [
        "• HOOK side (rough): activity page boxes",
        "• LOOP side (soft): back of cutout icons",
        "• Use 3/4\" velcro dots or strips",
        "• Press firmly and let adhesive cure 24hrs"
    ]
    for line in velcro:
        c.drawString(right_x, prep_y, line)
        prep_y -= 0.15*inch
    
    prep_y -= 0.1*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(right_x, prep_y, "Cutting Cutouts:")
    c.setFont("Helvetica", 9)
    prep_y -= 0.18*inch
    cutting = [
        "• Cut strips on guillotine paper cutter",
        "• Then cut individual icons from strips",
        "• Icons are sized for easy handling"
    ]
    for line in cutting:
        c.drawString(right_x, prep_y, line)
        prep_y -= 0.15*inch
    
    # Storage section
    storage_y = prep_y - 0.25*inch
    c.setFillColor(PRIMARY_BLUE)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(right_x, storage_y, "📁 Storage Tips")
    
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica", 9)
    storage_y -= 0.25*inch
    storage = [
        "• Use manila file folders for each level",
        "• Attach storage label to folder front",
        "• Color-code folders to match levels:",
        "   L1=Orange, L2=Blue, L3=Green, L4=Purple",
        "• Store cutouts in small ziplock bags",
        "• Keep quick start sheet in front",
        "• Store flat to prevent warping"
    ]
    for line in storage:
        c.drawString(right_x, storage_y, line)
        storage_y -= 0.15*inch
    
    # Bottom tip box
    tip_y = 1.3 * inch
    c.setFillColor(LEVEL_COLORS[1])  # Orange
    c.roundRect(0.6*inch, tip_y - 0.6*inch, width - 1.2*inch, 0.6*inch, 8, stroke=0, fill=1)
    
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width/2, tip_y - 0.25*inch, 
                        "💡 Pro Tip: Create a complete set for each student or classroom station!")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, tip_y - 0.45*inch,
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
