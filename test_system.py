#!/usr/bin/env python3
"""
Test script to verify the generator system is working correctly.

This script runs basic tests to ensure:
1. Dependencies are installed
2. Theme configuration is valid
3. Icons are accessible
4. PDF generation works
"""

import sys
from pathlib import Path
import traceback


def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        import reportlab
        print("  ✓ reportlab imported")
    except ImportError:
        print("  ✗ reportlab not found - run: pip install -r requirements.txt")
        return False
    
    try:
        from PIL import Image
        print("  ✓ Pillow (PIL) imported")
    except ImportError:
        print("  ✗ Pillow not found - run: pip install -r requirements.txt")
        return False
    
    try:
        from generators.base import BaseGenerator
        from generators.pdf_utils import PageLayout
        from generators.matching import MatchingGenerator
        print("  ✓ Generator modules imported")
    except ImportError as e:
        print(f"  ✗ Generator import failed: {e}")
        return False
    
    return True


def test_theme_config():
    """Test that theme configuration can be loaded"""
    print("\nTesting theme configuration...")
    try:
        from generators.base import BaseGenerator
        
        # Try to load Brown Bear theme
        gen = BaseGenerator('brown_bear', '/tmp/test')
        print(f"  ✓ Theme config loaded: {gen.theme_config.get('theme_name', 'Unknown')}")
        
        # Check for required keys
        if 'fringe_icons' in gen.theme_config or 'real_image_icons' in gen.theme_config:
            print("  ✓ Icon configuration found")
        else:
            print("  ⚠ Warning: No icon configuration found in theme")
        
        return True
    except FileNotFoundError as e:
        print(f"  ✗ Theme config not found: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Theme config error: {e}")
        traceback.print_exc()
        return False


def test_icon_access():
    """Test that icons can be accessed"""
    print("\nTesting icon access...")
    try:
        from generators.base import BaseGenerator
        
        gen = BaseGenerator('brown_bear', '/tmp/test')
        icons = gen.theme_config.get('fringe_icons', {})
        
        if not icons:
            print("  ⚠ Warning: No icons defined in theme")
            return True
        
        # Try to access first icon
        first_icon_name, first_icon_file = list(icons.items())[0]
        try:
            icon_path = gen.get_icon_path(first_icon_file)
            print(f"  ✓ Icon accessible: {first_icon_name} ({first_icon_file})")
            print(f"    Path: {icon_path}")
            return True
        except FileNotFoundError:
            print(f"  ✗ Icon file not found: {first_icon_file}")
            print(f"    Expected at: assets/themes/brown_bear/icons/{first_icon_file}")
            return False
        
    except Exception as e:
        print(f"  ✗ Icon access error: {e}")
        traceback.print_exc()
        return False


def test_pdf_generation():
    """Test that PDF generation works"""
    print("\nTesting PDF generation...")
    try:
        from generators.matching import MatchingGenerator
        import tempfile
        import os
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = MatchingGenerator('brown_bear', tmpdir)
            output_path = gen.ensure_output_dir('matching')
            
            # Generate Level 1 only
            gen.generate_level(1, output_path)
            
            # Check that files were created
            color_pdf = output_path / 'brown_bear_matching_level1_color.pdf'
            bw_pdf = output_path / 'brown_bear_matching_level1_bw.pdf'
            
            if color_pdf.exists() and bw_pdf.exists():
                print(f"  ✓ PDFs generated successfully")
                print(f"    Color: {color_pdf.stat().st_size} bytes")
                print(f"    B&W: {bw_pdf.stat().st_size} bytes")
                return True
            else:
                print(f"  ✗ PDFs not created")
                return False
        
    except Exception as e:
        print(f"  ✗ PDF generation error: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Small Wins Studio Generator - System Test")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Theme Config Test", test_theme_config),
        ("Icon Access Test", test_icon_access),
        ("PDF Generation Test", test_pdf_generation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! The generator system is ready to use.")
        print("\nTry running:")
        print("  python quick_start.py")
        print("  python -m generators.matching --theme brown_bear --output exports/")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
