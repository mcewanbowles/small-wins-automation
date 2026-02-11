#!/usr/bin/env python3
"""
Test script for TpT Automation System

Validates that:
1. Configs can be loaded
2. Images can be found
3. PDFs can be generated
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    load_theme_config,
    load_global_config,
    get_level_color,
    find_theme_image,
    load_theme_image,
    PDFBuilder,
    hex_to_rgb,
    inches_to_points
)


def test_configs():
    """Test configuration loading."""
    print("=" * 60)
    print("Testing Configuration Loading")
    print("=" * 60)
    
    # Load global config
    global_config = load_global_config()
    print("✓ Global config loaded")
    
    # Check level colors
    print("\nLevel Colors:")
    for level in range(1, 5):
        color = get_level_color(level, global_config)
        print(f"  Level {level}: {color}")
    
    # Load theme config
    theme_config = load_theme_config("brown_bear")
    print(f"\n✓ Brown Bear theme loaded")
    
    # Show theme info
    if "colors" in theme_config:
        print(f"  Primary color: {theme_config['colors'].get('primary', 'N/A')}")
    
    return global_config, theme_config


def test_images(theme_name="brown_bear"):
    """Test image loading."""
    print("\n" + "=" * 60)
    print("Testing Image Loading")
    print("=" * 60)
    
    # Check for brown bear icon folder
    from utils.config import get_project_root
    root = get_project_root()
    
    icon_path = root / "assets" / "themes" / theme_name / "icons"
    if icon_path.exists():
        print(f"✓ Icon folder found: {icon_path}")
        
        # List available icons
        icons = list(icon_path.glob("*.png"))[:5]  # First 5
        print(f"  Found {len(list(icon_path.glob('*.png')))} PNG icons")
        if icons:
            print("  Sample icons:")
            for icon in icons:
                print(f"    - {icon.name}")
    else:
        print(f"⚠ Icon folder not found: {icon_path}")
    
    # Try to load a test image
    test_img = load_theme_image(theme_name, "bear", "icons")
    if test_img:
        print(f"✓ Test image loaded: bear icon ({test_img.size[0]}×{test_img.size[1]})")
    else:
        print("⚠ Could not load test image 'bear'")


def test_pdf_generation():
    """Test PDF generation."""
    print("\n" + "=" * 60)
    print("Testing PDF Generation")
    print("=" * 60)
    
    # Create a simple test PDF
    output_path = Path("test_output.pdf")
    
    try:
        pdf = PDFBuilder(output_path, title="Test PDF")
        pdf.add_page()
        
        # Draw test elements
        c = pdf.get_canvas()
        
        # Title
        pdf.draw_text("TpT Automation System Test", 
                     inches_to_points(1), 
                     inches_to_points(10),
                     font_size=24,
                     color=(0, 0, 0))
        
        # Draw a border (navy blue, rounded)
        navy_rgb = hex_to_rgb("#1E3A5F")
        pdf.draw_border(
            inches_to_points(1),
            inches_to_points(8),
            inches_to_points(6.5),
            inches_to_points(1.5),
            color=navy_rgb,
            thickness=2,
            rounded=True,
            corner_radius=inches_to_points(0.12)
        )
        
        # Add text inside border
        pdf.draw_text("Rounded Border Test (0.12\" radius)", 
                     inches_to_points(4.25), 
                     inches_to_points(8.75),
                     align="center",
                     color=navy_rgb)
        
        # Draw level color samples
        y = 7
        for level in range(1, 5):
            color_hex = get_level_color(level)
            color_rgb = hex_to_rgb(color_hex)
            
            # Draw colored box
            c.setFillColorRGB(*color_rgb)
            c.rect(inches_to_points(1), inches_to_points(y), 
                  inches_to_points(0.5), inches_to_points(0.5), 
                  fill=1, stroke=0)
            
            # Draw label
            pdf.draw_text(f"Level {level}: {color_hex}", 
                         inches_to_points(1.75), 
                         inches_to_points(y + 0.15),
                         color=(0, 0, 0))
            
            y -= 0.75
        
        pdf.save()
        print(f"✓ Test PDF created: {output_path}")
        
        # Check file size
        if output_path.exists():
            size_kb = output_path.stat().st_size / 1024
            print(f"  File size: {size_kb:.1f} KB")
        
    except Exception as e:
        print(f"✗ Error creating PDF: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("TpT Automation System - Component Tests")
    print("=" * 60 + "\n")
    
    try:
        # Test configs
        global_config, theme_config = test_configs()
        
        # Test images
        test_images("brown_bear")
        
        # Test PDF
        test_pdf_generation()
        
        print("\n" + "=" * 60)
        print("✓ All Tests Complete")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
