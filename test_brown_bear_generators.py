#!/usr/bin/env python3
"""
Brown Bear Theme Generator Test Script

This script runs all 29 SPED generators with the Brown Bear theme
and saves sample outputs to /samples/brown_bear/ for review.
"""

import os
import sys
from pathlib import Path

# Add the repository root to the path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

def create_output_dirs():
    """Create output directory structure"""
    base_dir = repo_root / "samples" / "brown_bear"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def test_story_sequencing(output_dir):
    """Test Story Sequencing generator"""
    print("\n1. Testing Story Sequencing...")
    try:
        from generators.story_sequencing import generate_story_sequencing_dual_mode
        paths = generate_story_sequencing_dual_mode(
            theme_name='brown_bear',
            output_dir=str(output_dir),
            differentiation_level=1
        )
        print(f"   ✓ Generated: {paths}")
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def test_vocab_cards(output_dir):
    """Test Vocabulary Cards generator"""
    print("\n2. Testing Vocabulary Cards...")
    try:
        from generators.vocab_cards import generate_vocab_cards_dual_mode
        paths = generate_vocab_cards_dual_mode(
            theme_name='brown_bear',
            output_dir=str(output_dir),
            card_type='standard'
        )
        print(f"   ✓ Generated: {paths}")
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def test_matching_cards(output_dir):
    """Test Matching Cards generator"""
    print("\n3. Testing Matching Cards...")
    try:
        from generators.matching_cards import generate_matching_cards_dual_mode
        paths = generate_matching_cards_dual_mode(
            theme_name='brown_bear',
            output_dir=str(output_dir),
            differentiation_level=1
        )
        print(f"   ✓ Generated: {paths}")
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def test_bingo_game(output_dir):
    """Test Bingo Game generator"""
    print("\n4. Testing Bingo Game...")
    try:
        from generators.bingo_game import generate_bingo_dual_mode
        paths = generate_bingo_dual_mode(
            theme_name='brown_bear',
            output_dir=str(output_dir),
            grid_size=3,
            num_cards=4
        )
        print(f"   ✓ Generated: {paths}")
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def test_word_search(output_dir):
    """Test Word Search generator"""
    print("\n5. Testing Word Search...")
    try:
        from generators.word_search import generate_word_search_dual_mode
        paths = generate_word_search_dual_mode(
            theme_name='brown_bear',
            output_dir=str(output_dir),
            grid_size=10
        )
        print(f"   ✓ Generated: {paths}")
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def test_coloring_sheets(output_dir):
    """Test Coloring Sheets generator"""
    print("\n6. Testing Coloring Sheets...")
    try:
        from generators.coloring_sheets import generate_coloring_sheets_dual_mode
        paths = generate_coloring_sheets_dual_mode(
            theme_name='brown_bear',
            output_dir=str(output_dir),
            include_title=True
        )
        print(f"   ✓ Generated: {paths}")
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def run_all_tests():
    """Run all generator tests"""
    print("=" * 70)
    print("BROWN BEAR THEME - GENERATOR TEST SUITE")
    print("=" * 70)
    
    output_dir = create_output_dirs()
    print(f"\nOutput directory: {output_dir}")
    
    results = []
    
    # Run each generator test
    results.append(("Story Sequencing", test_story_sequencing(output_dir)))
    results.append(("Vocabulary Cards", test_vocab_cards(output_dir)))
    results.append(("Matching Cards", test_matching_cards(output_dir)))
    results.append(("Bingo Game", test_bingo_game(output_dir)))
    results.append(("Word Search", test_word_search(output_dir)))
    results.append(("Coloring Sheets", test_coloring_sheets(output_dir)))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")
    
    print(f"\nResults: {passed}/{total} generators successful")
    print(f"\nSample outputs saved to: {output_dir}")
    print("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
