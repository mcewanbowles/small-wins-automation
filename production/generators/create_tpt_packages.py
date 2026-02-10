#!/usr/bin/env python3
"""
Create TpT-Ready ZIP Packages for Each Level Product

This script packages level products with all required supporting documents:
- Color PDF (with cover if available)
- Black & White PDF
- Terms of Use
- How to Use
- Levels of Differentiation
- More Packs (promotional)

Usage:
    python3 create_tpt_packages.py
"""

import os
import zipfile
import shutil
from pathlib import Path

# Configuration
THEME = "brown_bear"
PRODUCT = "matching"
LEVELS = [1, 2, 3, 4]

# Paths
BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / "samples" / THEME / PRODUCT
DOCS_DIR = BASE_DIR / "Draft General Docs" / "TOU_etc"
OUTPUT_DIR = BASE_DIR / "tpt_packages"

# Required documents
REQUIRED_DOCS = {
    "Terms_of_Use.pdf": "Terms of Use.pdf",
    "How_to_Use.pdf": "How to Use.pdf",
    "Levels_Differentiation.pdf": "Levels of Differentiation.pdf",
    "More Packs.pdf": "More Packs.pdf"
}


def create_output_dir():
    """Create output directory for ZIP packages"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")


def get_level_pdfs(level):
    """Get color and B&W PDFs for a level
    
    Args:
        level: Level number (1-4)
        
    Returns:
        dict with 'color' and 'bw' paths, or None if not found
    """
    # Try with cover first
    color_with_cover = SAMPLES_DIR / f"{THEME}_{PRODUCT}_level{level}_color_with_cover.pdf"
    color_windows = SAMPLES_DIR / f"{THEME}_{PRODUCT}_level{level}_color_with_cover_windows.pdf"
    color_basic = SAMPLES_DIR / f"{THEME}_{PRODUCT}_level{level}_color.pdf"
    
    # Use best available color PDF
    if color_with_cover.exists():
        color_pdf = color_with_cover
    elif color_windows.exists():
        color_pdf = color_windows
    elif color_basic.exists():
        color_pdf = color_basic
    else:
        print(f"  ⚠️  No color PDF found for Level {level}")
        return None
    
    # Get B&W PDF
    bw_pdf = SAMPLES_DIR / f"{THEME}_{PRODUCT}_level{level}_bw.pdf"
    if not bw_pdf.exists():
        print(f"  ⚠️  No B&W PDF found for Level {level}")
        return None
    
    return {
        'color': color_pdf,
        'bw': bw_pdf
    }


def create_level_package(level):
    """Create TpT package ZIP for a specific level
    
    Args:
        level: Level number (1-4)
        
    Returns:
        Path to created ZIP file or None if failed
    """
    print(f"\n{'='*60}")
    print(f"Creating TpT Package for Level {level}")
    print(f"{'='*60}")
    
    # Get level PDFs
    pdfs = get_level_pdfs(level)
    if not pdfs:
        print(f"✗ Failed to find PDFs for Level {level}")
        return None
    
    # Create ZIP filename
    zip_filename = OUTPUT_DIR / f"{THEME}_{PRODUCT}_level{level}_TpT.zip"
    
    # Determine level name
    level_names = {
        1: "Errorless",
        2: "Easy",
        3: "Medium",
        4: "Challenge"
    }
    level_name = level_names.get(level, f"Level{level}")
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add color PDF
            color_name = f"Brown_Bear_Matching_Level{level}_{level_name}_Color.pdf"
            zipf.write(pdfs['color'], color_name)
            print(f"  ✓ Added: {color_name} ({pdfs['color'].stat().st_size / 1024 / 1024:.1f} MB)")
            
            # Add B&W PDF
            bw_name = f"Brown_Bear_Matching_Level{level}_{level_name}_BW.pdf"
            zipf.write(pdfs['bw'], bw_name)
            print(f"  ✓ Added: {bw_name} ({pdfs['bw'].stat().st_size / 1024 / 1024:.1f} MB)")
            
            # Add required documents
            for source_name, archive_name in REQUIRED_DOCS.items():
                doc_path = DOCS_DIR / source_name
                if doc_path.exists():
                    zipf.write(doc_path, archive_name)
                    print(f"  ✓ Added: {archive_name} ({doc_path.stat().st_size / 1024:.0f} KB)")
                else:
                    print(f"  ⚠️  Missing: {archive_name}")
        
        # Get ZIP file size
        zip_size = zip_filename.stat().st_size / 1024 / 1024
        print(f"\n✓ Created: {zip_filename.name} ({zip_size:.1f} MB)")
        return zip_filename
        
    except Exception as e:
        print(f"✗ Error creating ZIP for Level {level}: {e}")
        return None


def create_all_packages():
    """Create TpT packages for all levels"""
    print("\n" + "="*60)
    print("TpT Package Creator")
    print(f"Theme: {THEME.replace('_', ' ').title()}")
    print(f"Product: {PRODUCT.title()}")
    print("="*60)
    
    create_output_dir()
    
    created_packages = []
    for level in LEVELS:
        package = create_level_package(level)
        if package:
            created_packages.append(package)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\nCreated {len(created_packages)} TpT packages:")
    for package in created_packages:
        size = package.stat().st_size / 1024 / 1024
        print(f"  ✓ {package.name} ({size:.1f} MB)")
    
    print(f"\nOutput location: {OUTPUT_DIR}")
    print("\n✓ All packages ready for TpT upload!")
    
    return created_packages


def verify_package_contents(zip_path):
    """Verify contents of a ZIP package
    
    Args:
        zip_path: Path to ZIP file
    """
    print(f"\nVerifying: {zip_path.name}")
    print("-" * 40)
    
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        for info in zipf.filelist:
            size_mb = info.file_size / 1024 / 1024
            print(f"  {info.filename} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    packages = create_all_packages()
    
    # Verify first package as sample
    if packages:
        print("\n" + "="*60)
        print("SAMPLE PACKAGE CONTENTS (Level 1)")
        print("="*60)
        verify_package_contents(packages[0])
