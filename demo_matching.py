"""
Demo script for the Matching Cards Generator with 4 differentiation levels.

This demonstrates the SPED-friendly matching card system that supports:
- Level 1: Identical errorless matching
- Level 2: Outline-to-color matching
- Level 3: AAC symbol to real image matching
- Level 4: AAC symbol to text matching
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.matching_cards import generate_matching_cards_set
from utils.pdf_export import create_output_directory


def demo_matching_generator():
    """Demonstrate the 4-level matching card generator."""
    print("=" * 70)
    print("MATCHING CARDS GENERATOR - 4 Differentiation Levels Demo")
    print("=" * 70)
    print()
    
    # Create output directory
    output_dir = create_output_directory('output')
    
    # Example items (Brown Bear theme)
    # Note: This demo will work even if images are missing (placeholder cards will be created)
    items = [
        {'image': 'bear', 'label': 'Brown Bear'},
        {'image': 'duck', 'label': 'Yellow Duck'},
        {'image': 'frog', 'label': 'Green Frog'},
        {'image': 'cat', 'label': 'Purple Cat'},
        {'image': 'dog', 'label': 'Blue Dog'},
    ]
    
    print("Theme: Brown Bear")
    print(f"Items: {len(items)} animals")
    print()
    
    # Generate all 4 levels
    for level in range(1, 5):
        level_names = {
            1: "Identical Errorless Matching",
            2: "Outline-to-Color Matching",
            3: "AAC Symbol to Real Image Matching",
            4: "AAC Symbol to Text Matching"
        }
        
        print(f"Generating Level {level}: {level_names[level]}...")
        
        try:
            pages = generate_matching_cards_set(
                items=items,
                level=level,
                card_size='large',
                cards_per_page=6,
                output_dir=output_dir,
                theme_name='Brown_Bear'
            )
            print(f"  ✓ Success - {len(pages)} pages generated")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print()
    
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Generated PDFs:")
    print(f"  - {output_dir}/Brown_Bear_Matching_Level1_Identical_Errorless.pdf")
    print(f"  - {output_dir}/Brown_Bear_Matching_Level2_Outline_to_Color.pdf")
    print(f"  - {output_dir}/Brown_Bear_Matching_Level3_AAC_to_Real_Image.pdf")
    print(f"  - {output_dir}/Brown_Bear_Matching_Level4_AAC_to_Text.pdf")
    print()
    print("Note: If images are missing from the image folders, placeholder cards")
    print("      are generated to demonstrate the structure and layout.")
    print()
    print("To use actual images:")
    print("  1. Place color images in: images/bear.png, images/duck.png, etc.")
    print("  2. Place outline images in: Colour_images/bear.png, etc.")
    print("  3. Place AAC symbols in: aac_images/bear.png, etc.")
    print("  4. Run this demo again to see the real images!")
    print()


if __name__ == "__main__":
    demo_matching_generator()
