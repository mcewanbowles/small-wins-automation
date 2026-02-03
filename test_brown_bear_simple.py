#!/usr/bin/env python3
"""
Simplified Brown Bear Test - Direct imports to avoid circular dependencies
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

OUTPUT_DIR = "samples/brown_bear"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("\n" + "="*80)
print("SIMPLIFIED BROWN BEAR TEST")
print("="*80)

# Test 1: Theme Loader
print("\n[1] Testing Theme Loader with new /assets/ structure...")
try:
    from themes.theme_loader import load_theme
    
    theme = load_theme('brown_bear', mode='color')
    print(f"✅ Theme loaded successfully: {theme.name}")
    print(f"   Icons found: {len(theme.icons)}")
    print(f"   Real images found: {len(theme.real_images)}")
    print(f"   Colors: {len(theme.colours)}")
    
    # Test image path resolution
    bear_icon = theme.get_icon_path('bear.png')
    if bear_icon and os.path.exists(bear_icon):
        print(f"✅ Icon path resolution works: {bear_icon}")
    else:
        print(f"⚠️  Icon path not found, trying alternatives...")
        # Try with spaces
        bear_icon = theme.get_icon_path('Brown bear.png')
        if bear_icon and os.path.exists(bear_icon):
            print(f"✅ Found with alternative name: {bear_icon}")
        
except Exception as e:
    print(f"❌ Theme loader failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Color Helpers
print("\n[2] Testing Color Helpers for grayscale conversion...")
try:
    from utils.color_helpers import hex_to_grayscale, image_to_grayscale
    from PIL import Image
    
    # Test hex conversion
    gray = hex_to_grayscale('#FF5733')
    print(f"✅ Hex to grayscale works: #FF5733 → {gray}")
    
    # Test image conversion if we have an image
    test_img_path = "assets/themes/brown_bear/icons/Brown bear.png"
    if os.path.exists(test_img_path):
        img = Image.open(test_img_path)
        gray_img = image_to_grayscale(img)
        print(f"✅ Image to grayscale works: {img.mode} → {gray_img.mode}")
    
except Exception as e:
    print(f"❌ Color helpers failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Layout Utilities
print("\n[3] Testing Modern Layout Utilities...")
try:
    from utils.layout import create_page_canvas, add_footer
    
    canvas = create_page_canvas(mode='color')
    print(f"✅ Page canvas created: {canvas.size}, {canvas.mode}")
    
    add_footer(canvas, "Test Activity", page_num=1, mode='color')
    print(f"✅ Footer added successfully")
    
    # Save test output
    test_pdf_path = os.path.join(OUTPUT_DIR, "test_layout.png")
    canvas.save(test_pdf_path)
    print(f"✅ Test image saved: {test_pdf_path}")
    
except Exception as e:
    print(f"❌ Layout utilities failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Simple Word Search (no complex dependencies)
print("\n[4] Testing Word Search Generator (simplest generator)...")
try:
    # Import directly to avoid __init__.py issues
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "word_search",
        "generators/word_search.py"
    )
    word_search_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(word_search_module)
    
    # Check the actual function signature
    print(f"   Available functions: {[x for x in dir(word_search_module) if 'generate' in x.lower()]}")
    
except Exception as e:
    print(f"⚠️  Word Search test skipped: {e}")

# Test 5: List all available assets
print("\n[5] Asset Inventory:")
print("-" * 80)

asset_dirs = [
    "assets/global/aac_core",
    "assets/global/colours",
    "assets/themes/brown_bear/icons",
    "assets/themes/brown_bear/real_images",
    "assets/themes/brown_bear/colouring",
]

for asset_dir in asset_dirs:
    if os.path.exists(asset_dir):
        files = [f for f in os.listdir(asset_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        print(f"\n{asset_dir}:")
        print(f"  {len(files)} files found")
        if files:
            print(f"  Sample: {files[:3]}")
    else:
        print(f"\n{asset_dir}: NOT FOUND")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
print(f"\nOutput directory: {OUTPUT_DIR}")
print(f"Files created: {len([f for f in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, f))])}")
