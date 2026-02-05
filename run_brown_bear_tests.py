#!/usr/bin/env python3
"""
Comprehensive Brown Bear sample generation script.
Generates samples for all 29 dual-mode generators.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from themes.theme_loader import load_theme

def main():
    """Generate Brown Bear samples for all generators."""
    
    # Load Brown Bear theme
    print("Loading Brown Bear theme...")
    theme = load_theme('brown_bear', mode='color')
    print(f"✅ Theme loaded: {theme.name}")
    print(f"   - Icons: {len(theme.icons)} files")
    print(f"   - Real images: {len(theme.real_images)} files")
    print(f"   - Vocab: {len(theme.vocab)} words")
    print()
    
    # Create output directory
    output_dir = 'samples/brown_bear'
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    errors = []
    
    # Generator 1: Vocab Cards
    try:
        print("1. Generating Vocab Cards...")
        from generators.vocab_cards import generate_vocab_cards_dual_mode
        
        fringe_vocab = theme.vocab[:6]  # Use first 6 vocab words
        paths = generate_vocab_cards_dual_mode(
            fringe_vocab=fringe_vocab,
            theme_name='brown_bear',
            output_dir=output_dir,
            include_storage_label=True
        )
        results.append(('Vocab Cards', paths))
        print(f"   ✅ Generated: {paths.get('color', 'N/A')}")
    except Exception as e:
        errors.append(('Vocab Cards', str(e)))
        print(f"   ❌ Error: {e}")
    
    # Generator 2: Matching Cards
    try:
        print("2. Generating Matching Cards...")
        from generators.matching_cards import generate_matching_cards_dual_mode
        
        # matching_cards uses 'items' parameter (list of vocab words)
        items = theme.vocab[:8]
        paths = generate_matching_cards_dual_mode(
            items=items,
            theme_name='brown_bear',
            level=1,
            output_dir=output_dir,
            include_storage_label=True
        )
        results.append(('Matching Cards', paths))
        print(f"   ✅ Generated: {paths.get('color', 'N/A')}")
    except Exception as e:
        errors.append(('Matching Cards', str(e)))
        print(f"   ❌ Error: {e}")
    
    # Generator 3: Story Sequencing  
    try:
        print("3. Generating Story Sequencing...")
        from generators.story_sequencing import generate_story_sequencing_dual_mode
        
        # Use sequencing data from theme if available
        if theme.sequencing and len(theme.sequencing) > 0:
            story_data = theme.sequencing[0]  # First sequence
        else:
            story_data = theme.vocab[:4]  # Fallback to first 4 vocab words
            
        paths = generate_story_sequencing_dual_mode(
            story_data=story_data,
            theme_name='brown_bear',
            output_dir=output_dir,
            include_storage_label=True
        )
        results.append(('Story Sequencing', paths))
        print(f"   ✅ Generated: {paths.get('color', 'N/A')}")
    except Exception as e:
        errors.append(('Story Sequencing', str(e)))
        print(f"   ❌ Error: {e}")
    
    # Generator 4: Coloring Sheets
    try:
        print("4. Generating Coloring Sheets...")
        from generators.coloring_sheets import generate_coloring_sheets_dual_mode
        
        # coloring_sheets uses 'image_title_pairs' parameter
        image_title_pairs = [(word.lower() + '.png', word) for word in theme.vocab[:6]]
        paths = generate_coloring_sheets_dual_mode(
            image_title_pairs=image_title_pairs,
            theme_name='brown_bear',
            output_dir=output_dir,
            include_storage_label=True
        )
        results.append(('Coloring Sheets', paths))
        print(f"   ✅ Generated: {paths.get('color', 'N/A')}")
    except Exception as e:
        errors.append(('Coloring Sheets', str(e)))
        print(f"   ❌ Error: {e}")
    
    # Generator 5: Storage Labels
    try:
        print("5. Generating Storage Labels...")
        from generators.storage_labels import generate_storage_labels_dual_mode
        
        # storage_labels uses 'label_data' parameter - list of (text, image) tuples
        label_data = [(word, word.lower() + '.png') for word in theme.vocab[:6]]
        paths = generate_storage_labels_dual_mode(
            label_data=label_data,
            theme_name='brown_bear',
            label_size='medium',
            output_dir=output_dir
        )
        results.append(('Storage Labels', paths))
        print(f"   ✅ Generated: {paths.get('color', 'N/A')}")
    except Exception as e:
        errors.append(('Storage Labels', str(e)))
        print(f"   ❌ Error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)
    print(f"✅ Successful: {len(results)}")
    print(f"❌ Errors: {len(errors)}")
    
    if results:
        print("\nGenerated Files:")
        for name, paths in results:
            print(f"  • {name}")
            if isinstance(paths, dict):
                for mode, path in paths.items():
                    print(f"      - {mode}: {path}")
    
    if errors:
        print("\nErrors:")
        for name, error in errors:
            print(f"  • {name}: {error}")
    
    print(f"\nOutput directory: {output_dir}")
    print("="*60)
    
    return len(errors) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
