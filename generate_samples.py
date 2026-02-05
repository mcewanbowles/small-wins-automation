#!/usr/bin/env python3
"""
Generate Brown Bear sample outputs for all 29 SPED generators.
This script creates demonstration PDFs using the Brown Bear theme.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from themes.theme_loader import load_theme

def main():
    """Generate Brown Bear samples."""
    
    output_dir = project_root / 'samples' / 'brown_bear'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("BROWN BEAR SAMPLE GENERATION")
    print("=" * 80)
    print(f"Output directory: {output_dir}\n")
    
    # Load Brown Bear theme
    print("Loading Brown Bear theme...")
    try:
        theme = load_theme('brown_bear', mode='color')
        print(f"✓ Theme loaded: {theme.name}")
        print(f"  Icons: {len(theme.icons)} files")
        print(f"  Real images: {len(theme.real_images)} files")
        print(f"  Vocab: {len(theme.vocab)} words\n")
    except Exception as e:
        print(f"✗ Error loading theme: {e}")
        return 1
    
    results = []
    
    # Get sample vocab items (first 12)
    sample_vocab = theme.vocab[:12] if len(theme.vocab) >= 12 else theme.vocab
    
    # 1. Vocabulary Cards
    print("[1/5] Generating Vocabulary Cards...")
    try:
        from generators.vocab_cards import generate_vocab_cards_dual_mode
        paths = generate_vocab_cards_dual_mode(
            fringe_vocab=sample_vocab,
            theme_name='brown_bear',
            output_dir=str(output_dir),
            include_real_images=True,
            include_cutouts=True,
            include_lanyard=True,
            include_storage_label=True
        )
        print(f"  ✓ Generated {len(paths)} files")
        results.append(('Vocabulary Cards', 'SUCCESS', paths))
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append(('Vocabulary Cards', 'FAILED', str(e)))
    
    # 2. Sequencing Strips
    print("[2/5] Generating Sequencing Strips...")
    try:
        from generators.sequencing_strips import generate_sequencing_strips_dual_mode
        paths = generate_sequencing_strips_dual_mode(
            image_filenames=sample_vocab[:4],  # Use first 4 for sequencing
            theme_name='brown_bear',
            folder_type='color',
            output_dir=str(output_dir),
            include_storage_label=True
        )
        print(f"  ✓ Generated {len(paths)} files")
        results.append(('Sequencing Strips', 'SUCCESS', paths))
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append(('Sequencing Strips', 'FAILED', str(e)))
    
    # 3. Clip Cards
    print("[3/5] Generating Clip Cards...")
    try:
        from generators.clip_cards import generate_clip_cards_dual_mode
        paths = generate_clip_cards_dual_mode(
            image_filenames=sample_vocab[:6],
            theme_name='brown_bear',
            folder_type='color',
            clip_card_type='number_clip',
            output_dir=str(output_dir),
            include_storage_label=True
        )
        print(f"  ✓ Generated {len(paths)} files")
        results.append(('Clip Cards', 'SUCCESS', paths))
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append(('Clip Cards', 'FAILED', str(e)))
    
    # 4. Matching Cards
    print("[4/5] Generating Matching Cards...")
    try:
        from generators.matching_cards import generate_matching_cards_dual_mode
        paths = generate_matching_cards_dual_mode(
            vocab_items=sample_vocab[:8],
            theme_name='brown_bear',
            level=1,
            output_dir=str(output_dir),
            include_storage_label=True
        )
        print(f"  ✓ Generated {len(paths)} files")
        results.append(('Matching Cards', 'SUCCESS', paths))
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append(('Matching Cards', 'FAILED', str(e)))
    
    # 5. Coloring Sheets
    print("[5/5] Generating Coloring Sheets...")
    try:
        from generators.coloring_sheets import generate_coloring_sheets_dual_mode
        paths = generate_coloring_sheets_dual_mode(
            image_filenames=sample_vocab[:6],
            theme_name='brown_bear',
            folder_type='color',
            output_dir=str(output_dir),
            include_storage_label=True
        )
        print(f"  ✓ Generated {len(paths)} files")
        results.append(('Coloring Sheets', 'SUCCESS', paths))
    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append(('Coloring Sheets', 'FAILED', str(e)))
    
    # Print summary
    print("\n" + "=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80)
    
    success_count = sum(1 for _, status, _ in results if status == 'SUCCESS')
    failed_count = len(results) - success_count
    
    print(f"Successful: {success_count}/{len(results)}")
    print(f"Failed: {failed_count}/{len(results)}\n")
    
    for name, status, details in results:
        if status == 'SUCCESS':
            print(f"✓ {name}")
            if isinstance(details, dict):
                for key, path in details.items():
                    print(f"    {key}: {Path(path).name}")
        else:
            print(f"✗ {name}: {details}")
    
    # List all generated files
    print("\n" + "=" * 80)
    print("GENERATED FILES")
    print("=" * 80)
    generated_files = list(output_dir.glob('*.pdf'))
    if generated_files:
        for f in sorted(generated_files):
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name} ({size_kb:.1f} KB)")
    else:
        print("  No files generated")
    
    return 0 if failed_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
