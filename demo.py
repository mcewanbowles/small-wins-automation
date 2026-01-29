"""
Simple demo script that creates a word search (no images needed).
This demonstrates the system works without requiring image files.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators import generate_word_search
from utils.pdf_export import create_output_directory


def create_demo_word_search():
    """Create a demo word search to verify the system works."""
    print("=" * 60)
    print("SPED Resource Automation System - Demo")
    print("=" * 60)
    print()
    print("Creating a sample word search puzzle...")
    print()
    
    # Create output directory
    output_dir = create_output_directory('output')
    
    # Create word search
    words = ['APPLE', 'BANANA', 'ORANGE', 'GRAPE', 'PEAR']
    page = generate_word_search(
        words=words,
        theme_name='Fruits',
        grid_size=10,
        show_answers=False
    )
    
    # Save as PDF
    from utils.pdf_export import save_image_as_pdf
    output_path = os.path.join(output_dir, 'Demo_Word_Search.pdf')
    save_image_as_pdf(page, output_path, title='Demo Word Search')
    
    print(f"✓ Word search created successfully!")
    print(f"  Output: {output_path}")
    print(f"  Size: {page.size[0]}x{page.size[1]} pixels")
    print(f"  Words: {', '.join(words)}")
    print()
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Add image files to images/, Colour_images/, and aac_images/ folders")
    print("2. Check examples/usage_examples.py for code samples")
    print("3. Run generators to create your SPED resources!")
    print()


if __name__ == "__main__":
    create_demo_word_search()
