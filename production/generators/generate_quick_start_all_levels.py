#!/usr/bin/env python3
"""
Quick Start Guide Generator - Creates level-specific Quick Start PDFs
Fills in the template with level-specific content for L1-L5

Output: production/support_docs/Quick_Start_Guide_Matching_Level{N}.pdf
"""

import os
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Try to register fonts
try:
    pdfmetrics.registerFont(TTFont('ComicSans', '/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf'))
    pdfmetrics.registerFont(TTFont('ComicSans-Bold', '/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS_Bold.ttf'))
    TITLE_FONT = 'ComicSans-Bold'
    BODY_FONT = 'ComicSans'
except:
    TITLE_FONT = 'Helvetica-Bold'
    BODY_FONT = 'Helvetica'

# Colors
TEAL = HexColor('#008B8B')
TEXT_COLOR = HexColor('#2C3E50')
WHITE = white
LEVEL_COLORS = {
    1: HexColor('#FF8C42'),  # Orange - Errorless
    2: HexColor('#4A90E2'),  # Blue - Distractors
    3: HexColor('#7CB342'),  # Green - Picture+Text
    4: HexColor('#9C27B0'),  # Purple - Generalisation
    5: HexColor('#E91E63'),  # Pink - Advanced
}

# Level-specific content for Matching
LEVEL_CONTENT = {
    1: {
        "name": "Level 1 - Errorless",
        "short": "L1",
        "full": "Errorless Learning",
        "num_boards": "6 matching boards",
        "description": "Perfect for beginners! All images are identical Boardmaker symbols. Students learn the matching routine with 100% success rate - there are no wrong answers.",
        "student_routine": [
            "1. Look at target image at top",
            "2. Find matching image below",
            "3. Place on velcro strip",
            "4. Repeat for all targets",
        ],
        "troubleshooting": [
            "If struggling: Point to target, then matching piece",
            "If distracted: Use visual timer",
            "If incorrect: Gently guide to correct piece",
        ],
        "next_steps": "When student achieves 80%+ accuracy, progress to Level 2 (Distractors)",
        "quick_games": ["Speed Match", "Count the Matches", "Say the Name"],
    },
    2: {
        "name": "Level 2 - Distractors",
        "short": "L2",
        "full": "With Distractors",
        "num_boards": "6 matching boards with distractors",
        "description": "Introduces visual discrimination! Same Boardmaker images plus distractor pieces. Students must identify correct matches among similar options.",
        "student_routine": [
            "1. Look at target image at top",
            "2. Scan all pieces (ignore distractors)",
            "3. Select the MATCHING piece only",
            "4. Place on velcro strip",
        ],
        "troubleshooting": [
            "If confused: Cover distractors initially",
            "If grabbing wrong: Slow down, point to target first",
            "If frustrated: Return to Level 1 briefly",
        ],
        "next_steps": "When student achieves 80%+ accuracy, progress to Level 3 (Picture+Text)",
        "quick_games": ["Find the Match", "Odd One Out", "Partner Check"],
    },
    3: {
        "name": "Level 3 - Picture + Text",
        "short": "L3",
        "full": "Picture and Text",
        "num_boards": "6 matching boards with labels",
        "description": "Adds literacy! Boardmaker images now include text labels. Students match while seeing written words - great for early readers.",
        "student_routine": [
            "1. Look at target image AND word",
            "2. Say/sign the word (if able)",
            "3. Find matching image+word piece",
            "4. Place on velcro strip",
        ],
        "troubleshooting": [
            "If ignoring text: Point to word, model reading",
            "If reading struggle: Focus on image, expose to text",
            "If success: Encourage reading aloud",
        ],
        "next_steps": "When student achieves 80%+ accuracy, progress to Level 4 (Generalisation)",
        "quick_games": ["Read and Match", "Word Hunt", "Label Check"],
    },
    4: {
        "name": "Level 4 - Generalisation",
        "short": "L4",
        "full": "Icon to Photo",
        "num_boards": "6 matching boards (icon↔photo)",
        "description": "Builds real-world connection! Match Boardmaker icons to real photographs. Students learn that symbols represent actual objects.",
        "student_routine": [
            "1. Look at target (icon OR photo)",
            "2. Understand what it represents",
            "3. Find the matching (photo OR icon)",
            "4. Place on velcro strip",
        ],
        "troubleshooting": [
            "If confused: Show real object if possible",
            "If wrong match: Compare icon and photo together",
            "If success: Discuss 'same but different look'",
        ],
        "next_steps": "When student achieves 80%+ accuracy, progress to Level 5 (Advanced)",
        "quick_games": ["Real vs Symbol", "Photo Hunt", "Match Pairs"],
    },
    5: {
        "name": "Level 5 - Advanced",
        "short": "L5",
        "full": "B&W to Colour",
        "num_boards": "6 matching boards (B&W↔colour)",
        "description": "Abstract thinking! Match black & white images to full colour versions. Develops ability to recognize objects regardless of visual presentation.",
        "student_routine": [
            "1. Look at target (B&W OR colour)",
            "2. Identify the subject",
            "3. Find matching (colour OR B&W)",
            "4. Place on velcro strip",
        ],
        "troubleshooting": [
            "If confused: Compare shapes, not colours",
            "If wrong match: Outline the shape together",
            "If success: Great generalization skills!",
        ],
        "next_steps": "Mastery! Try new themes or move to Find & Cover activities",
        "quick_games": ["Colour Detective", "Shape Match", "Speed Round"],
    },
}


def generate_quick_start(level, output_path, theme="Brown Bear"):
    """Generate a level-specific Quick Start Guide PDF."""
    content = LEVEL_CONTENT[level]
    color = LEVEL_COLORS[level]
    
    width, height = letter
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    # Page border
    c.setStrokeColor(TEAL)
    c.setLineWidth(2)
    c.roundRect(0.4*inch, 0.4*inch, width - 0.8*inch, height - 0.8*inch, 10, stroke=1, fill=0)
    
    # Header
    header_y = height - 0.4*inch - 0.7*inch
    c.setFillColor(TEAL)
    c.roundRect(0.5*inch, header_y, width - 1*inch, 0.7*inch, 8, stroke=0, fill=1)
    
    c.setFillColor(WHITE)
    c.setFont(BODY_FONT, 14)
    c.drawCentredString(width/2, header_y + 0.45*inch, "QUICK START GUIDE")
    c.setFont(TITLE_FONT, 16)
    c.drawCentredString(width/2, header_y + 0.15*inch, f"{theme} Matching - {content['name']}")
    
    # Level badge
    badge_x = width - 1.2*inch
    c.setFillColor(color)
    c.circle(badge_x, header_y + 0.35*inch, 0.3*inch, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(TITLE_FONT, 12)
    c.drawCentredString(badge_x, header_y + 0.3*inch, content['short'])
    
    y = header_y - 0.3*inch
    
    # What This Resource Is
    c.setFillColor(TEXT_COLOR)
    c.setFont(TITLE_FONT, 12)
    c.drawString(0.6*inch, y, "📚 What This Resource Is")
    y -= 0.2*inch
    c.setFont(BODY_FONT, 10)
    
    # Word wrap description
    desc_words = content['description'].split()
    line = ""
    for word in desc_words:
        test_line = line + " " + word if line else word
        if c.stringWidth(test_line, BODY_FONT, 10) < width - 1.2*inch:
            line = test_line
        else:
            c.drawString(0.7*inch, y, line)
            y -= 0.15*inch
            line = word
    if line:
        c.drawString(0.7*inch, y, line)
    y -= 0.3*inch
    
    # Student Routine
    c.setFont(TITLE_FONT, 12)
    c.drawString(0.6*inch, y, "📋 Student Routine")
    y -= 0.2*inch
    c.setFont(BODY_FONT, 10)
    for step in content['student_routine']:
        c.drawString(0.7*inch, y, step)
        y -= 0.15*inch
    y -= 0.15*inch
    
    # Troubleshooting
    c.setFont(TITLE_FONT, 12)
    c.drawString(0.6*inch, y, "⚠️ Troubleshooting")
    y -= 0.2*inch
    c.setFont(BODY_FONT, 10)
    for tip in content['troubleshooting']:
        c.drawString(0.7*inch, y, tip)
        y -= 0.15*inch
    y -= 0.15*inch
    
    # Next Steps
    c.setFillColor(color)
    c.roundRect(0.6*inch, y - 0.4*inch, width - 1.2*inch, 0.5*inch, 5, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(TITLE_FONT, 11)
    c.drawCentredString(width/2, y - 0.2*inch, f"➡️ Next Steps: {content['next_steps']}")
    y -= 0.7*inch
    
    # Quick Games
    c.setFillColor(TEXT_COLOR)
    c.setFont(TITLE_FONT, 12)
    c.drawString(0.6*inch, y, "🎮 Quick Games")
    y -= 0.2*inch
    c.setFont(BODY_FONT, 10)
    games_text = " • ".join(content['quick_games'])
    c.drawString(0.7*inch, y, games_text)
    y -= 0.3*inch
    
    # Setup Tips Box
    c.setFillColor(HexColor('#F5F5F5'))
    c.roundRect(0.6*inch, y - 1.3*inch, width - 1.2*inch, 1.4*inch, 5, stroke=0, fill=1)
    c.setFillColor(TEXT_COLOR)
    c.setFont(TITLE_FONT, 11)
    c.drawString(0.7*inch, y - 0.2*inch, "🔧 Setup Tips")
    c.setFont(BODY_FONT, 9)
    tips = [
        "• Print on cardstock for durability",
        "• Laminate boards and pieces for longevity",
        "• Cut out pieces carefully",
        "• Add velcro dots to boards and pieces",
        "• Store in labeled folders by level",
    ]
    tip_y = y - 0.4*inch
    for tip in tips:
        c.drawString(0.8*inch, tip_y, tip)
        tip_y -= 0.15*inch
    y -= 1.5*inch
    
    # AAC Support Box
    c.setFillColor(HexColor('#E8F5E9'))
    c.roundRect(0.6*inch, y - 0.9*inch, width - 1.2*inch, 1.0*inch, 5, stroke=0, fill=1)
    c.setFillColor(TEXT_COLOR)
    c.setFont(TITLE_FONT, 11)
    c.drawString(0.7*inch, y - 0.2*inch, "💬 AAC & Communication Support")
    c.setFont(BODY_FONT, 9)
    c.drawString(0.8*inch, y - 0.4*inch, "Core Words: same, match, find, look, put, yes, no, more, done")
    c.drawString(0.8*inch, y - 0.55*inch, "Model on device before expecting use • Wait 10+ seconds for response")
    c.drawString(0.8*inch, y - 0.7*inch, "Accept ALL communication (pointing, signing, device, vocalizations)")
    
    # Footer
    c.setFillColor(TEAL)
    c.setFont(BODY_FONT, 8)
    c.drawCentredString(width/2, 0.55*inch, f"Small Wins Studio • {theme} Matching {content['short']} • www.smallwinsstudio.com")
    
    c.save()
    print(f"✓ Generated: {output_path}")


def main():
    """Generate Quick Start Guides for all levels."""
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "support_docs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("GENERATING LEVEL-SPECIFIC QUICK START GUIDES")
    print("=" * 60)
    
    for level in range(1, 6):
        output_path = output_dir / f"Quick_Start_Guide_Matching_Level{level}.pdf"
        generate_quick_start(level, output_path)
    
    print("\n" + "=" * 60)
    print(f"✅ Generated 5 Quick Start Guides in {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
