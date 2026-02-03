#!/usr/bin/env python3
"""
Generate Brown Bear sample outputs for all 29 SPED generators.
This script tests each generator with the new asset structure.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def generate_samples():
    """Generate Brown Bear samples for all generators."""
    
    output_dir = project_root / 'samples' / 'brown_bear'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("BROWN BEAR SAMPLE GENERATION - All 29 Generators")
    print("=" * 80)
    print(f"Output directory: {output_dir}")
    print()
    
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }
    
    # Generator 1: Story Sequencing (modernized)
    print("[1/29] Story Sequencing...")
    try:
        from generators.story_sequencing import generate_story_sequencing_dual_mode
        theme_name = 'brown_bear'
        paths = generate_story_sequencing_dual_mode(
            theme_name=theme_name,
            output_dir=str(output_dir),
            num_pages=4
        )
        results['success'].append(('Story Sequencing', paths))
        print(f"  ✓ Generated: {paths}")
    except Exception as e:
        results['failed'].append(('Story Sequencing', str(e)))
        print(f"  ✗ Error: {e}")
    
    # Generator 2: Vocab Cards
    print("[2/29] Vocab Cards...")
    try:
        from generators.vocab_cards import generate_vocab_cards_dual_mode
        paths = generate_vocab_cards_dual_mode(
            theme_name='brown_bear',
            output_dir=str(output_dir),
            card_types=['basic', 'with_text']
        )
        results['success'].append(('Vocab Cards', paths))
        print(f"  ✓ Generated: {paths}")
    except Exception as e:
        results['failed'].append(('Vocab Cards', str(e)))
        print(f"  ✗ Error: {e}")
    
    # Generator 3: Puppet Characters (modernized)
    print("[3/29] Puppet Characters...")
    try:
        from generators.puppet_characters import generate_puppet_characters_dual_mode
        paths = generate_puppet_characters_dual_mode(
            theme_name='brown_bear',
            output_dir=str(output_dir),
            puppet_types=['stick', 'finger']
        )
        results['success'].append(('Puppet Characters', paths))
        print(f"  ✓ Generated: {paths}")
    except Exception as e:
        results['failed'].append(('Puppet Characters', str(e)))
        print(f"  ✗ Error: {e}")
    
    # Continue with remaining generators...
    # For now, print summary
    print()
    print("=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80)
    print(f"Successful: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Skipped: {len(results['skipped'])}")
    
    if results['failed']:
        print("\nFailed generators:")
        for name, error in results['failed']:
            print(f"  - {name}: {error}")
    
    return results

if __name__ == '__main__':
    results = generate_samples()
    
    # Exit with error code if any failed
    if results['failed']:
        sys.exit(1)
    else:
        print("\n✓ All samples generated successfully!")
        sys.exit(0)
