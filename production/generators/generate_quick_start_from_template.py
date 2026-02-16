#!/usr/bin/env python3
"""
Quick Start Guide Generator - Using HTML Template
Generates 5 level-specific Quick Start PDFs from the HTML template with placeholders
Output: production/support_docs/Quick_Start_Guide_Matching_Level{N}.pdf
"""

import os
import sys
from pathlib import Path
from weasyprint import HTML

# Level-specific content for Matching - Brown Bear theme
LEVEL_CONTENT = {
    1: {
        "level": "1",
        "level_full": "Level 1 (Errorless)",
        "num_boards": "6 matching boards",
        "num_levels": "5",
        "description_full": """Perfect for beginners! All images are identical Boardmaker symbols. 
        Students learn the matching routine with 100% success rate - there are no wrong answers. 
        This builds confidence and teaches the matching task itself before adding complexity.""",
        "student_routine": """
                <ol class="steps">
                    <li>Look at the target image at the top of the board</li>
                    <li>Find the matching piece from your pile</li>
                    <li>Place it on the velcro strip below the target</li>
                    <li>Repeat for all target images on the board</li>
                    <li>When finished, place board in "done" area</li>
                </ol>
        """,
        "troubleshooting": """
                <ul>
                    <li><strong>If struggling:</strong> Point to target, then point to the matching piece</li>
                    <li><strong>If distracted:</strong> Use a visual timer or break into smaller sessions</li>
                    <li><strong>If placing incorrectly:</strong> Gently guide hand to correct spot</li>
                    <li><strong>If refusing task:</strong> Try different theme or reduce number of pieces</li>
                </ul>
        """,
        "next_steps": """
                <div class="content-box">
                    <p><strong>When student achieves 80%+ independent accuracy:</strong> Progress to <strong>Level 2 (Distractors)</strong> to introduce visual discrimination.</p>
                </div>
        """,
        "quick_games": """
                <ul>
                    <li><strong>Speed Match:</strong> Use timer to encourage faster matching (celebrate all attempts!)</li>
                    <li><strong>Count the Matches:</strong> Count pieces together as they place them</li>
                    <li><strong>Say the Name:</strong> Label each image as student matches (AAC modeling!)</li>
                    <li><strong>Partner Check:</strong> Student matches, peer/teacher gives thumbs up</li>
                </ul>
        """
    },
    2: {
        "level": "2",
        "level_full": "Level 2 (Distractors)",
        "num_boards": "6 matching boards",
        "num_levels": "5",
        "description_full": """Introduces visual discrimination! Same Boardmaker images PLUS distractor pieces. 
        Students must identify the correct matches among similar options. This builds scanning and 
        discrimination skills essential for academic tasks.""",
        "student_routine": """
                <ol class="steps">
                    <li>Look at the target image at the top</li>
                    <li>Scan through ALL the pieces (including distractors)</li>
                    <li>Select ONLY the piece that matches the target</li>
                    <li>Place it on the velcro strip</li>
                    <li>Ignore the distractor pieces - leave them aside</li>
                </ol>
        """,
        "troubleshooting": """
                <ul>
                    <li><strong>If confused by distractors:</strong> Cover distractors initially, gradually reveal them</li>
                    <li><strong>If grabbing wrong pieces:</strong> Slow down, point to target first before searching</li>
                    <li><strong>If frustrated:</strong> Return to Level 1 briefly to rebuild confidence</li>
                    <li><strong>If too easy:</strong> Ready for Level 3!</li>
                </ul>
        """,
        "next_steps": """
                <div class="content-box">
                    <p><strong>When student achieves 80%+ independent accuracy:</strong> Progress to <strong>Level 3 (Picture + Text)</strong> to introduce literacy connections.</p>
                </div>
        """,
        "quick_games": """
                <ul>
                    <li><strong>Find the Match First:</strong> Race (gently!) to find correct piece</li>
                    <li><strong>Odd One Out:</strong> Identify which pieces are distractors before matching</li>
                    <li><strong>Partner Check:</strong> Peer verification - "Is this right?"</li>
                    <li><strong>Distractor Sort:</strong> After matching, sort distractors vs. matches</li>
                </ul>
        """
    },
    3: {
        "level": "3",
        "level_full": "Level 3 (Picture + Text)",
        "num_boards": "6 matching boards",
        "num_levels": "5",
        "description_full": """Adds literacy! Boardmaker images now include text labels underneath. 
        Students match while seeing written words - great for early readers and pre-readers learning 
        sight words. Supports literacy development in a low-pressure format.""",
        "student_routine": """
                <ol class="steps">
                    <li>Look at the target image AND the word label</li>
                    <li>Say or sign the word (if able) - model on AAC device</li>
                    <li>Find the matching image+word piece</li>
                    <li>Place it on the velcro strip</li>
                    <li>Repeat, encouraging word exposure each time</li>
                </ol>
        """,
        "troubleshooting": """
                <ul>
                    <li><strong>If ignoring text:</strong> Point to word, model reading it aloud</li>
                    <li><strong>If reading struggle:</strong> Focus on image match, let them see text passively</li>
                    <li><strong>If showing success:</strong> Encourage reading words aloud during matching</li>
                    <li><strong>If mastering:</strong> Try covering images, match by text only!</li>
                </ul>
        """,
        "next_steps": """
                <div class="content-box">
                    <p><strong>When student achieves 80%+ independent accuracy:</strong> Progress to <strong>Level 4 (Generalisation)</strong> to connect symbols to real photos.</p>
                </div>
        """,
        "quick_games": """
                <ul>
                    <li><strong>Read and Match:</strong> Student reads word before finding piece</li>
                    <li><strong>Word Hunt:</strong> Find a specific word among the pieces</li>
                    <li><strong>Label Check:</strong> Cover images, match by words only</li>
                    <li><strong>Spell It:</strong> Use letter tiles to spell the words after matching</li>
                </ul>
        """
    },
    4: {
        "level": "4",
        "level_full": "Level 4 (Generalisation)",
        "num_boards": "6 matching boards",
        "num_levels": "5",
        "description_full": """Builds real-world connection! Match Boardmaker icons to real photographs. 
        Students learn that symbols represent actual objects - critical for AAC users and supports 
        generalisation of concepts beyond symbolic representations.""",
        "student_routine": """
                <ol class="steps">
                    <li>Look at the target (either icon OR photo)</li>
                    <li>Think about what it represents (the actual object/animal/person)</li>
                    <li>Find the matching piece in the other format (photo OR icon)</li>
                    <li>Place it on the velcro strip</li>
                    <li>Both icon and photo represent the SAME thing!</li>
                </ol>
        """,
        "troubleshooting": """
                <ul>
                    <li><strong>If confused:</strong> Show the real object if possible, or additional photos</li>
                    <li><strong>If wrong matches:</strong> Compare icon and photo side-by-side, discuss similarities</li>
                    <li><strong>If showing success:</strong> Discuss "same but looks different" concept</li>
                    <li><strong>If mastering:</strong> Great! This is advanced generalization skill</li>
                </ul>
        """,
        "next_steps": """
                <div class="content-box">
                    <p><strong>When student achieves 80%+ independent accuracy:</strong> Progress to <strong>Level 5 (Advanced)</strong> for the ultimate challenge!</p>
                </div>
        """,
        "quick_games": """
                <ul>
                    <li><strong>Real vs Symbol:</strong> Sort pieces into "real photo" and "icon" piles first</li>
                    <li><strong>Photo Hunt:</strong> Find the real photo that matches an icon</li>
                    <li><strong>Match Pairs:</strong> Lay all pieces out, find icon-photo pairs</li>
                    <li><strong>Which is Which:</strong> Name the object, student finds both versions</li>
                </ul>
        """
    },
    5: {
        "level": "5",
        "level_full": "Level 5 (Advanced)",
        "num_boards": "6 matching boards",
        "num_levels": "5",
        "description_full": """Abstract thinking! Match black & white images to full colour versions. 
        Develops ability to recognize objects regardless of visual presentation - highest level of 
        visual discrimination and cognitive flexibility.""",
        "student_routine": """
                <ol class="steps">
                    <li>Look at the target (either B&W OR colour)</li>
                    <li>Identify what the subject/object is</li>
                    <li>Find the matching piece in the other format (colour OR B&W)</li>
                    <li>Place it on the velcro strip</li>
                    <li>Recognize: same shape, different appearance!</li>
                </ol>
        """,
        "troubleshooting": """
                <ul>
                    <li><strong>If confused:</strong> Compare shapes and outlines, not colors</li>
                    <li><strong>If wrong matches:</strong> Trace or outline the shape together to show similarity</li>
                    <li><strong>If showing success:</strong> Excellent generalization skills!</li>
                    <li><strong>If mastering:</strong> Student has completed all 5 levels - celebrate!</li>
                </ul>
        """,
        "next_steps": """
                <div class="content-box">
                    <p><strong>Mastery Achieved!</strong> Try new themes (other book characters) or move to <strong>Find & Cover activities</strong> for a new challenge.</p>
                </div>
        """,
        "quick_games": """
                <ul>
                    <li><strong>Colour Detective:</strong> Student predicts what color the B&W image should be</li>
                    <li><strong>Shape Match:</strong> Focus on outlines/shapes instead of colors</li>
                    <li><strong>Speed Round:</strong> Timed matching with celebration for all attempts</li>
                    <li><strong>Memory Match:</strong> Flip pieces face-down, match from memory</li>
                </ul>
        """
    }
}


def generate_quick_start_pdf(level, output_dir, template_path):
    """Generate a level-specific Quick Start PDF from HTML template."""
    
    # Get level content
    content = LEVEL_CONTENT[level]
    
    # Read HTML template
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Replace all placeholders in one pass
    replacements = {
        '{{LEVEL}}': content['level'],
        '{{LEVEL_FULL}}': content['level_full'],
        '{{NUM_BOARDS}}': content['num_boards'],
        '{{NUM_LEVELS}}': content['num_levels'],
        '{{DESCRIPTION_FULL}}': content['description_full'],
        '{{STUDENT_ROUTINE}}': content['student_routine'],
        '{{TROUBLESHOOTING}}': content['troubleshooting'],
        '{{NEXT_STEPS}}': content['next_steps'],
        '{{QUICK_GAMES}}': content['quick_games'],
    }
    
    for placeholder, value in replacements.items():
        html_content = html_content.replace(placeholder, value)
    
    # Generate PDF from HTML
    output_path = output_dir / f"Quick_Start_Guide_Matching_Level{level}.pdf"
    
    # Convert HTML to PDF using WeasyPrint
    HTML(string=html_content, base_url=str(template_path.parent)).write_pdf(str(output_path))
    
    # Get file size
    file_size = output_path.stat().st_size
    print(f"OK Level {level}: {output_path.name} ({file_size / 1024:.1f} KB)")
    
    return output_path


def main():
    """Generate all 5 Quick Start Guides from the HTML template."""
    
    # Paths
    base_dir = Path(__file__).parent.parent.parent
    template_path = base_dir / "Draft General Docs" / "Quick_Start_Guides" / "Quick_Start_Guide_Matching_Level1.html"
    output_dir = base_dir / "production" / "support_docs"
    
    # Verify template exists
    if not template_path.exists():
        print(f"ERROR Template not found: {template_path}")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("GENERATING QUICK START GUIDES FROM HTML TEMPLATE")
    print("=" * 70)
    print(f"Template: {template_path.name}")
    print(f"Output:   {output_dir}")
    print()
    
    # Generate all 5 levels
    generated_files = []
    for level in range(1, 6):
        try:
            output_path = generate_quick_start_pdf(level, output_dir, template_path)
            generated_files.append(output_path)
        except Exception as e:
            print(f"ERROR generating Level {level}: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 70)
    print(f"OK Successfully generated {len(generated_files)}/5 Quick Start Guides")
    print("=" * 70)
    print()
    print("Files created:")
    for path in generated_files:
        print(f"  - {path.relative_to(base_dir)}")
    print()
    print("OK All Quick Start Guides use the same beautiful design!")
    print("OK Each guide has level-specific content for Matching activities")


if __name__ == "__main__":
    main()
