#!/usr/bin/env python3
"""
Build Pipeline - Theme Pack Generator

This script generates a complete theme pack with ALL enabled generators and storage labels
from a single theme JSON file.

Usage:
    python build_theme_pack.py brown_bear
    python build_theme_pack.py brown_bear --no-labels
    python build_theme_pack.py brown_bear --generators matching,counting,bingo
"""

import os
import sys
import argparse
from pathlib import Path

# Import utilities
from utils import get_theme_loader
from utils.config import DPI, CARD_SIZES

# Import all generators
from generators import (
    generate_matching_cards_set,
    generate_counting_mats_set,
    generate_bingo_set,
    generate_sequencing_set,
    generate_find_cover_set,
    generate_sorting_cards_set,
    generate_sentence_strips_set,
    generate_yes_no_questions_set,
    generate_wh_questions_set,
    generate_story_maps_set,
    generate_color_questions_set,
    generate_coloring_sheets_set,
    generate_coloring_strips_page,
    generate_word_search_set,
)


def build_matching_cards(theme_name, items, output_dir, include_labels):
    """Generate matching cards for all 4 levels."""
    print("\n📋 Generating Matching Cards (4 levels)...")
    
    matching_items = [{'image': item['image'], 'label': item['label']} for item in items]
    
    for level in range(1, 5):
        try:
            generate_matching_cards_set(
                items=matching_items,
                level=level,
                card_size='large',
                cards_per_page=6,
                output_dir=output_dir,
                theme_name=theme_name,
                include_storage_label=include_labels
            )
            print(f"  ✓ Level {level} complete")
        except Exception as e:
            print(f"  ✗ Level {level} failed: {e}")


def build_counting_mats(theme_name, items, output_dir, include_labels):
    """Generate counting mats for levels 1-3."""
    print("\n🔢 Generating Counting Mats (3 levels)...")
    
    image_filenames = [f"{item['image']}.png" for item in items[:5]]
    
    for level in range(1, 4):
        try:
            generate_counting_mats_set(
                image_filenames=image_filenames,
                theme_name=theme_name,
                number_range=(1, 10),
                level=level,
                output_dir=output_dir,
                include_storage_label=include_labels
            )
            print(f"  ✓ Level {level} complete")
        except Exception as e:
            print(f"  ✗ Level {level} failed: {e}")


def build_bingo(theme_name, items, output_dir, include_labels):
    """Generate bingo cards."""
    print("\n🎯 Generating Bingo Cards...")
    
    image_filenames = [f"{item['image']}.png" for item in items[:9]]
    
    try:
        generate_bingo_set(
            image_filenames=image_filenames,
            num_cards=6,
            grid_size=3,
            output_dir=output_dir,
            theme_name=theme_name,
            include_storage_label=include_labels
        )
        print("  ✓ Bingo complete")
    except Exception as e:
        print(f"  ✗ Bingo failed: {e}")


def build_sequencing(theme_name, items, output_dir, include_labels):
    """Generate sequencing cards for levels 1-3."""
    print("\n📊 Generating Sequencing Cards (3 levels)...")
    
    # Create a sequence from the first 3-4 items
    image_sequence = [f"{item['image']}.png" for item in items[:4]]
    
    for level in range(1, 4):
        try:
            generate_sequencing_set(
                image_sequence=image_sequence,
                theme_name=theme_name,
                level=level,
                output_dir=output_dir,
                include_storage_label=include_labels
            )
            print(f"  ✓ Level {level} complete")
        except Exception as e:
            print(f"  ✗ Level {level} failed: {e}")


def build_find_cover(theme_name, items, output_dir, include_labels):
    """Generate find & cover activities."""
    print("\n🔍 Generating Find & Cover...")
    
    all_images = [f"{item['image']}.png" for item in items]
    target_images = all_images[:6]  # First 6 as targets
    
    try:
        generate_find_cover_set(
            target_images=target_images,
            all_images=all_images,
            theme_name=theme_name,
            num_sheets=3,
            grid_size=4,
            output_dir=output_dir,
            include_storage_label=include_labels
        )
        print("  ✓ Find & Cover complete")
    except Exception as e:
        print(f"  ✗ Find & Cover failed: {e}")


def build_sorting_cards(theme_name, items, output_dir, include_labels):
    """Generate sorting cards for levels 1-3."""
    print("\n🗂️ Generating Sorting Cards (3 levels)...")
    
    # Categorize by color - create dict with color as key, list of image filenames as value
    categories_dict = {}
    for item in items:
        color = item.get('color', 'other')
        if color not in categories_dict:
            categories_dict[color] = []
        categories_dict[color].append(f"{item['image']}.png")
    
    for level in range(1, 4):
        try:
            generate_sorting_cards_set(
                categories_dict=categories_dict,
                level=level,
                theme_name=theme_name,
                output_dir=output_dir,
                include_storage_label=include_labels
            )
            print(f"  ✓ Level {level} complete")
        except Exception as e:
            print(f"  ✗ Level {level} failed: {e}")


def build_sentence_strips(theme_name, items, output_dir, include_labels):
    """Generate AAC sentence strips."""
    print("\n💬 Generating Sentence Strips (AAC)...")
    
    # Create sentence templates: "I see [animal]"
    sentence_templates = [
        f"I see {item['label'].lower()}"
        for item in items[:5]
    ]
    
    try:
        generate_sentence_strips_set(
            sentence_templates=sentence_templates,
            theme_name=theme_name,
            output_dir=output_dir,
            include_storage_label=include_labels
        )
        print("  ✓ Sentence Strips complete")
    except Exception as e:
        print(f"  ✗ Sentence Strips failed: {e}")


def build_yes_no_questions(theme_name, items, output_dir, include_labels):
    """Generate yes/no questions for levels 1-3."""
    print("\n✅ Generating Yes/No Questions (3 levels)...")
    
    # Create question data: list of dicts with image, question, and answer
    question_data = [
        {
            'image': f"{item['image']}.png",
            'question': f"Is this a {item['label'].lower()}?",
            'answer': True
        }
        for item in items[:5]
    ]
    
    for level in range(1, 4):
        try:
            generate_yes_no_questions_set(
                question_data=question_data,
                level=level,
                theme_name=theme_name,
                output_dir=output_dir,
                include_storage_label=include_labels
            )
            print(f"  ✓ Level {level} complete")
        except Exception as e:
            print(f"  ✗ Level {level} failed: {e}")


def build_wh_questions(theme_name, items, output_dir, include_labels):
    """Generate WH questions for levels 1-3."""
    print("\n❓ Generating WH Questions (3 levels)...")
    
    # Create question data: list of dicts with image, question, choices, and answer
    question_data = [
        {
            'image': f"{item['image']}.png",
            'question': f"What color is the {item['label'].split()[-1].lower()}?",
            'choices': [item.get('color', 'brown').title(), 'Red', 'Blue', 'Green'],
            'answer': item.get('color', 'brown').title()
        }
        for item in items[:5]
    ]
    
    for level in range(1, 4):
        try:
            generate_wh_questions_set(
                question_data=question_data,
                level=level,
                theme_name=theme_name,
                output_dir=output_dir,
                include_storage_label=include_labels
            )
            print(f"  ✓ Level {level} complete")
        except Exception as e:
            print(f"  ✗ Level {level} failed: {e}")


def build_story_maps(theme_name, items, output_dir, include_labels):
    """Generate story maps for levels 1-3."""
    print("\n📖 Generating Story Maps (3 levels)...")
    
    # Create story data
    stories_data = [
        {
            'title': f"The {theme_name.replace('_', ' ').title()} Story",
            'characters': [item['label'] for item in items[:3]],
            'setting': 'In the animal kingdom',
            'problem': 'The animals need to find their colors',
            'solution': 'They work together'
        }
    ]
    
    for level in range(1, 4):
        try:
            generate_story_maps_set(
                stories_data=stories_data,
                level=level,
                theme_name=theme_name,
                output_dir=output_dir,
                include_storage_label=include_labels
            )
            print(f"  ✓ Level {level} complete")
        except Exception as e:
            print(f"  ✗ Level {level} failed: {e}")


def build_color_questions(theme_name, items, output_dir, include_labels):
    """Generate color questions for levels 1-3."""
    print("\n🎨 Generating Color Questions (3 levels)...")
    
    # Create question data
    question_data = [
        {
            'image': f"{item['image']}.png",
            'color': item.get('color', 'brown'),
            'label': item['label']
        }
        for item in items[:5]
    ]
    
    for level in range(1, 4):
        try:
            generate_color_questions_set(
                question_data=question_data,
                level=level,
                theme_name=theme_name,
                output_dir=output_dir,
                include_storage_label=include_labels
            )
            print(f"  ✓ Level {level} complete")
        except Exception as e:
            print(f"  ✗ Level {level} failed: {e}")


def build_coloring_sheets(theme_name, items, output_dir, include_labels):
    """Generate coloring sheets."""
    print("\n🖍️ Generating Coloring Sheets...")
    
    # Create image-title pairs
    image_title_pairs = [(f"{item['image']}.png", item['label']) for item in items[:8]]
    
    try:
        generate_coloring_sheets_set(
            image_title_pairs=image_title_pairs,
            theme_name=theme_name,
            output_dir=output_dir,
            include_storage_label=include_labels
        )
        print("  ✓ Coloring Sheets complete")
    except Exception as e:
        print(f"  ✗ Coloring Sheets failed: {e}")


def build_coloring_strips(theme_name, items, output_dir, include_labels):
    """Generate coloring strips."""
    print("\n✏️ Generating Coloring Strips...")
    
    # Create image-label pairs
    image_label_pairs = [(f"{item['image']}.png", item['label']) for item in items[:6]]
    
    try:
        generate_coloring_strips_page(
            image_label_pairs=image_label_pairs,
            theme_name=theme_name,
            output_dir=output_dir,
            include_storage_label=include_labels
        )
        print("  ✓ Coloring Strips complete")
    except Exception as e:
        print(f"  ✗ Coloring Strips failed: {e}")


def build_word_search(theme_name, items, output_dir, include_labels):
    """Generate word search."""
    print("\n🔤 Generating Word Search...")
    
    # Create word lists - just one list with all the labels
    word_lists = [[item['label'] for item in items[:8]]]
    
    try:
        generate_word_search_set(
            word_lists=word_lists,
            theme_name=theme_name,
            grid_size=15,
            output_dir=output_dir,
            include_storage_label=include_labels
        )
        print("  ✓ Word Search complete")
    except Exception as e:
        print(f"  ✗ Word Search failed: {e}")


# Generator registry - maps generator names to build functions
GENERATOR_REGISTRY = {
    'matching': build_matching_cards,
    'counting': build_counting_mats,
    'bingo': build_bingo,
    'sequencing': build_sequencing,
    'find_cover': build_find_cover,
    'sorting': build_sorting_cards,
    'sentence_strips': build_sentence_strips,
    'yes_no': build_yes_no_questions,
    'wh_questions': build_wh_questions,
    'story_maps': build_story_maps,
    'color_questions': build_color_questions,
    'coloring_sheets': build_coloring_sheets,
    'coloring_strips': build_coloring_strips,
    'word_search': build_word_search,
}


def build_theme_pack(theme_name, generators=None, include_labels=True, output_base='output'):
    """
    Build a complete theme pack with all enabled generators.
    
    Args:
        theme_name (str): Name of theme file (without .json extension)
        generators (list): List of specific generators to run, or None for all
        include_labels (bool): Whether to generate storage labels
        output_base (str): Base output directory
    """
    print("=" * 70)
    print(f"🎨 BUILDING THEME PACK: {theme_name}")
    print("=" * 70)
    
    # Load theme
    print(f"\n📂 Loading theme '{theme_name}.json'...")
    loader = get_theme_loader()
    
    try:
        theme_data = loader.load_theme(theme_name)
        items = loader.get_theme_items(theme_name)
        
        theme_title = theme_data.get('name', theme_name)
        print(f"  ✓ Theme loaded: {theme_title}")
        print(f"  ✓ {len(items)} items found")
        
    except FileNotFoundError:
        print(f"  ✗ Error: Theme file 'themes/{theme_name}.json' not found")
        return False
    except Exception as e:
        print(f"  ✗ Error loading theme: {e}")
        return False
    
    # Create output directory
    output_dir = os.path.join(output_base, theme_name)
    os.makedirs(output_dir, exist_ok=True)
    print(f"  ✓ Output directory: {output_dir}")
    
    # Determine which generators to run
    if generators:
        generators_to_run = {g: GENERATOR_REGISTRY[g] for g in generators if g in GENERATOR_REGISTRY}
        print(f"\n🔧 Running {len(generators_to_run)} selected generators...")
    else:
        generators_to_run = GENERATOR_REGISTRY
        print(f"\n🔧 Running all {len(generators_to_run)} generators...")
    
    if include_labels:
        print("  ✓ Storage labels enabled")
    else:
        print("  ⚠ Storage labels disabled")
    
    # Run each generator
    success_count = 0
    fail_count = 0
    
    for gen_name, gen_func in generators_to_run.items():
        try:
            gen_func(theme_name, items, output_dir, include_labels)
            success_count += 1
        except Exception as e:
            print(f"\n  ✗ {gen_name} failed with error: {e}")
            fail_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 BUILD SUMMARY")
    print("=" * 70)
    print(f"  ✓ Successful: {success_count}/{len(generators_to_run)}")
    if fail_count > 0:
        print(f"  ✗ Failed: {fail_count}/{len(generators_to_run)}")
    print(f"  📁 Output: {output_dir}")
    print("=" * 70)
    
    return fail_count == 0


def main():
    """Main entry point for build pipeline."""
    parser = argparse.ArgumentParser(
        description='Build a complete SPED resource theme pack',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build everything for brown_bear theme
  python build_theme_pack.py brown_bear
  
  # Build without storage labels
  python build_theme_pack.py brown_bear --no-labels
  
  # Build only specific generators
  python build_theme_pack.py brown_bear --generators matching,counting,bingo
  
  # Custom output directory
  python build_theme_pack.py brown_bear --output my_output
  
Available generators:
  matching, counting, bingo, sequencing, find_cover, sorting,
  sentence_strips, yes_no, wh_questions, story_maps, color_questions,
  coloring_sheets, coloring_strips, word_search
        """
    )
    
    parser.add_argument(
        'theme',
        nargs='?',
        help='Theme name (from themes/ directory, without .json extension)'
    )
    
    parser.add_argument(
        '--generators', '-g',
        help='Comma-separated list of generators to run (default: all)',
        default=None
    )
    
    parser.add_argument(
        '--no-labels',
        action='store_true',
        help='Disable storage label generation'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Base output directory (default: output)'
    )
    
    parser.add_argument(
        '--list-generators',
        action='store_true',
        help='List all available generators and exit'
    )
    
    args = parser.parse_args()
    
    # List generators if requested
    if args.list_generators:
        print("Available generators:")
        for gen_name in sorted(GENERATOR_REGISTRY.keys()):
            print(f"  - {gen_name}")
        return 0
    
    # Parse generator list
    generator_list = None
    if args.generators:
        generator_list = [g.strip() for g in args.generators.split(',')]
        # Validate generator names
        invalid = [g for g in generator_list if g not in GENERATOR_REGISTRY]
        if invalid:
            print(f"Error: Unknown generator(s): {', '.join(invalid)}")
            print(f"Use --list-generators to see available generators")
            return 1
    
    # Build theme pack
    success = build_theme_pack(
        theme_name=args.theme,
        generators=generator_list,
        include_labels=not args.no_labels,
        output_base=args.output
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
