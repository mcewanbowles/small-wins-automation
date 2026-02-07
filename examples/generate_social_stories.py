#!/usr/bin/env python3
"""
Example script showing how to use the Social Stories Generator
Run from repository root: python examples/generate_social_stories.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generators.social_stories.generator import SocialStoryGenerator, generate_all_stories

def example_single_story():
    """Generate a single social story"""
    print("=" * 60)
    print("Example: Generate Single Story")
    print("=" * 60)
    
    story_path = "assets/social_stories/good_touch_bad_touch/SOCIAL_STORY_Good_Touch_Bad_Touch.txt"
    
    generator = SocialStoryGenerator(story_path)
    output_pdf = generator.generate_pdf()
    
    print(f"\n✓ Story generated: {output_pdf}")
    print(f"✓ File size: {Path(output_pdf).stat().st_size / 1024:.1f} KB")
    print()

if __name__ == "__main__":
    print("\n🎨 Social Stories Generator - Usage Example\n")
    
    example_single_story()
    
    print("=" * 60)
    print("✨ Example complete!")
    print("=" * 60)
    print("\nFor more information, see:")
    print("  - generators/social_stories/README.md")
    print("  - generators/social_stories/QUICKSTART.md")
    print("  - docs/SOCIAL_STORIES_IMPLEMENTATION.md")
    print()
