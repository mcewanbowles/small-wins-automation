#!/usr/bin/env python3
"""
Quick Start Example for Small Wins Studio Generators

This script demonstrates how to use the matching generator
to create TpT resources.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from generators.matching import MatchingGenerator


def main():
    """Generate a quick example using the Brown Bear theme"""
    print("=" * 60)
    print("Small Wins Studio Generator - Quick Start Example")
    print("=" * 60)
    print()
    
    # Configure
    theme = "brown_bear"
    output_dir = "exports"
    
    print(f"Theme: {theme}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Create generator
    try:
        generator = MatchingGenerator(theme, output_dir)
        
        # Generate Level 1 only for quick demo
        print("Generating Level 1 (Errorless) matching activity...")
        output_path = generator.ensure_output_dir('matching')
        generator.generate_level(1, output_path)
        
        # Generate supporting materials
        print("Generating cutouts...")
        generator.generate_cutouts(output_path)
        
        print("Generating storage labels...")
        generator.generate_storage_labels(output_path)
        
        print()
        print("✓ Generation complete!")
        print()
        print(f"Generated files in: {output_path}/")
        print("  - brown_bear_matching_level1_color.pdf")
        print("  - brown_bear_matching_level1_bw.pdf")
        print("  - brown_bear_matching_cutouts.pdf")
        print("  - brown_bear_matching_storage_labels.pdf")
        print()
        print("Next steps:")
        print("  1. Review the generated PDFs")
        print("  2. Generate all levels: python -m generators.matching --theme brown_bear --output exports/")
        print("  3. See GENERATOR_README.md for full documentation")
        print()
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print()
        print("Make sure:")
        print("  1. You're running this from the repository root")
        print("  2. The theme configuration exists in themes/brown_bear.json")
        print("  3. Icon files exist in assets/themes/brown_bear/icons/")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
