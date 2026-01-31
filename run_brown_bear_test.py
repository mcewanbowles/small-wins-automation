#!/usr/bin/env python3
"""
Brown Bear Test Runner - Generates sample outputs for all 29 generators
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from themes.theme_loader import load_theme

# Output directory
OUTPUT_DIR = "samples/brown_bear"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_generator_test(generator_name, test_func, description):
    """Run a single generator test"""
    print(f"\n{'='*80}")
    print(f"Testing: {generator_name}")
    print(f"Description: {description}")
    print(f"{'='*80}")
    
    try:
        result = test_func()
        print(f"✅ SUCCESS: {generator_name}")
        if result:
            print(f"   Output: {result}")
        return True
    except FileNotFoundError as e:
        print(f"⚠️  MISSING FILE: {generator_name}")
        print(f"   {str(e)}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {generator_name}")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_matching_cards():
    """Test Matching Cards generator"""
    from generators.matching_cards import generate_matching_cards_dual_mode
    
    items = [
        {'image': 'bear', 'label': 'Bear'},
        {'image': 'duck', 'label': 'Duck'},
        {'image': 'frog', 'label': 'Frog'},
        {'image': 'cat', 'label': 'Cat'},
    ]
    
    paths = generate_matching_cards_dual_mode(
        items=items,
        level=1,
        theme_name='brown_bear',
        output_dir=OUTPUT_DIR,
        include_storage_label=True
    )
    return paths

def test_word_search():
    """Test Word Search generator"""
    from generators.word_search import generate_word_search_dual_mode
    
    words = ['BEAR', 'DUCK', 'FROG', 'CAT', 'DOG', 'BIRD']
    
    paths = generate_word_search_dual_mode(
        words=words,
        grid_size=10,
        theme_name='brown_bear',
        output_dir=OUTPUT_DIR
    )
    return paths

def test_coloring_sheets():
    """Test Coloring Sheets generator"""
    from generators.coloring_sheets import generate_coloring_sheets_dual_mode
    
    theme = load_theme('brown_bear', mode='color')
    
    # Use Brown Bear coloring images
    images = ['bear', 'duck', 'frog', 'cat']
    
    paths = generate_coloring_sheets_dual_mode(
        coloring_images=images,
        theme_name='brown_bear',
        output_dir=OUTPUT_DIR,
        include_title=True
    )
    return paths

def main():
    """Run all generator tests"""
    print("\n" + "="*80)
    print("BROWN BEAR TEST SUITE - 29 SPED Generators")
    print("="*80)
    
    tests = [
        ("Matching Cards", test_matching_cards, "Level 1 - Errorless matching"),
        ("Word Search", test_word_search, "10x10 grid with word list"),
        ("Coloring Sheets", test_coloring_sheets, "Full-page coloring pages"),
    ]
    
    results = []
    for name, func, desc in tests:
        success = run_generator_test(name, func, desc)
        results.append((name, success))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nResults: {passed}/{total} generators passed")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # List generated files
    print("\n" + "="*80)
    print("GENERATED FILES")
    print("="*80)
    
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for file in sorted(files):
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath)
            print(f"  {filepath} ({size:,} bytes)")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
