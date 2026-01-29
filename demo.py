#!/usr/bin/env python3
"""
Example script demonstrating the SPED TpT activity generators.

This script shows how to use each generator to create various
educational materials for special education.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.generators import (
    generate_counting_mat_set,
    generate_bingo_board,
    generate_matching_activity,
    generate_sequencing_activity,
    generate_coloring_page,
    generate_aac_board,
    generate_label_sheet,
)


def main():
    """Run example generations for each activity type."""
    
    print("=" * 60)
    print("SPED TpT Activity Generator - Examples")
    print("=" * 60)
    print()
    
    # Ensure output directory exists
    output_dir = Path(__file__).parent / 'outputs'
    output_dir.mkdir(exist_ok=True)
    
    # 1. Generate Counting Mats
    print("1. Generating counting mats (1-5)...")
    try:
        files = generate_counting_mat_set(
            start=1,
            end=5,
            output_dir='outputs'
        )
        print(f"   ✓ Generated {len(files)} counting mats")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    print()
    
    # 2. Generate Bingo Board
    print("2. Generating bingo board...")
    try:
        sample_items = [
            "apple", "banana", "cat", "dog", "elephant",
            "fish", "grape", "hat", "ice cream", "juice",
            "kite", "lion", "moon", "nest", "orange",
            "pig", "queen", "rabbit", "sun", "tree",
            "umbrella", "violin", "water", "xylophone", "zebra"
        ]
        
        bingo_path = output_dir / 'bingo_sample.png'
        generate_bingo_board(
            sample_items,
            use_images=False,  # Use text since we don't have images
            output_path=str(bingo_path)
        )
        print(f"   ✓ Generated bingo board")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    print()
    
    # 3. Generate Matching Activity
    print("3. Generating matching activity...")
    try:
        sample_pairs = [
            ("Red", "Apple"),
            ("Yellow", "Banana"),
            ("Blue", "Sky"),
            ("Green", "Grass"),
            ("Orange", "Carrot"),
        ]
        
        matching_path = output_dir / 'matching_sample.png'
        generate_matching_activity(
            sample_pairs,
            use_images=False,  # Use text
            output_path=str(matching_path)
        )
        print(f"   ✓ Generated matching activity")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    print()
    
    # 4. Generate Sequencing Activity
    print("4. Generating sequencing activity...")
    try:
        sample_steps = [
            "Wake up",
            "Brush teeth",
            "Eat breakfast",
            "Go to school",
        ]
        
        sequencing_path = output_dir / 'sequencing_sample.png'
        generate_sequencing_activity(
            sample_steps,
            use_images=False,  # Use text
            output_path=str(sequencing_path)
        )
        print(f"   ✓ Generated sequencing activity")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    print()
    
    # 5. Generate AAC Board
    print("5. Generating AAC communication board...")
    try:
        sample_aac_items = [
            ("aac1.png", "YES"),
            ("aac2.png", "NO"),
            ("aac3.png", "HELP"),
            ("aac4.png", "MORE"),
            ("aac5.png", "DONE"),
            ("aac6.png", "PLEASE"),
            ("aac7.png", "THANK YOU"),
            ("aac8.png", "BATHROOM"),
            ("aac9.png", "DRINK"),
            ("aac10.png", "EAT"),
            ("aac11.png", "PLAY"),
            ("aac12.png", "STOP"),
        ]
        
        aac_path = output_dir / 'aac_board_sample.png'
        generate_aac_board(
            sample_aac_items,
            output_path=str(aac_path)
        )
        print(f"   ✓ Generated AAC board")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    print()
    
    # 6. Generate Labels
    print("6. Generating label sheet...")
    try:
        sample_labels = [
            "Pencils",
            "Crayons",
            "Scissors",
            "Glue",
            "Paper",
            "Books",
        ]
        
        labels_path = output_dir / 'labels_sample.png'
        generate_label_sheet(
            sample_labels,
            labels_per_page=6,
            output_path=str(labels_path)
        )
        print(f"   ✓ Generated label sheet")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    print()
    
    # 7. Note about coloring pages
    print("7. Coloring pages...")
    print("   ℹ Coloring pages require source images to convert.")
    print("   ℹ Place images in the 'images' folder and use:")
    print("   ℹ generate_coloring_page('your_image.png')")
    print()
    
    print("=" * 60)
    print("✓ Example generation complete!")
    print(f"✓ Check the '{output_dir}' folder for generated files")
    print("=" * 60)


if __name__ == '__main__':
    main()
