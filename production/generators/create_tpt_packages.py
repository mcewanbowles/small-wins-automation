#!/usr/bin/env python3
"""
Create TpT-Ready ZIP Packages for Each Level Product

This script packages level products with ONLY the required supporting documents:
- Color PDF (with cover, 16 pages)
- Black & White PDF (16 pages)
- Terms of Use Credits (official version)
- Quick Start Guide (level-specific, auto-generated)

Obsolete documents (NO LONGER INCLUDED):
- How to Use (already in PDF as page 16)
- Levels of Differentiation (obsolete)
- More Packs (obsolete)

Usage:
    python3 create_tpt_packages.py
"""

import os
import zipfile
import shutil
from pathlib import Path
import json
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Configuration
THEME = "brown_bear"
PRODUCT = "matching"

# Paths
REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "samples" / THEME / PRODUCT
FINAL_DIR = REPO_ROOT / "production" / "final_products" / THEME / PRODUCT
SUPPORT_DOCS_DIR = REPO_ROOT / "production" / "support_docs"
OUTPUT_DIR = FINAL_DIR / "tpt_zips"

TOU_PDF = SUPPORT_DOCS_DIR / "Terms_of_Use_Credits.pdf"


def _load_matching_level_names(theme_id: str) -> dict[int, str]:
    theme_path = REPO_ROOT / "themes" / f"{theme_id}.json"
    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)
    levels = theme["matching"]["levels"]
    return {i: levels[f"L{i}"]["name"] for i in range(1, 6)}


_LEVEL_NAMES = _load_matching_level_names(THEME)

LEVELS = [
    {"num": i, "name": _LEVEL_NAMES[i]} for i in range(1, 6)
]


def create_output_dir():
    """Create output directory for ZIP packages"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")


def get_level_pdfs(level_num: int, level_name: str):
    """Get color and B&W PDFs for a level.
    
    Args:
        level: Level number (1-4)
        
    Returns:
        dict with 'color' and 'bw' paths, or None if not found
    """
    # Prefer FINAL merged PDFs (cover + numbered pages)
    color_pdf = FINAL_DIR / f"brown_bear_matching_level{level_num}_{level_name}_color_FINAL.pdf"
    bw_pdf = FINAL_DIR / f"brown_bear_matching_level{level_num}_{level_name}_bw_FINAL.pdf"

    if not color_pdf.exists():
        # Fallback to non-FINAL split PDFs (still usable for packaging)
        color_pdf = FINAL_DIR / f"brown_bear_matching_level{level_num}_color.pdf"
    if not bw_pdf.exists():
        bw_pdf = FINAL_DIR / f"brown_bear_matching_level{level_num}_bw.pdf"

    if not color_pdf.exists():
        print(f"  WARNING No color PDF found for Level {level_num}")
        return None
    if not bw_pdf.exists():
        print(f"  WARNING No B&W PDF found for Level {level_num}")
        return None
    
    return {
        'color': color_pdf,
        'bw': bw_pdf,
    }


def create_level_package(level):
    """Create TpT package ZIP for a specific level
    
    Args:
        level: Level number (1-4)
        
    Returns:
        Path to created ZIP file or None if failed
    """
    level_num = level["num"]
    level_name = level["name"]

    print(f"\n{'='*60}")
    print(f"Creating TpT Package for Level {level_num} ({level_name})")
    print(f"{'='*60}")
    
    # Get level PDFs
    pdfs = get_level_pdfs(level_num, level_name)
    if not pdfs:
        print(f"FAILED to find PDFs for Level {level_num}")
        return None
    
    # Create ZIP filename
    zip_filename = OUTPUT_DIR / f"{THEME}_{PRODUCT}_level{level_num}_TpT.zip"
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add color PDF
            color_name = f"Brown_Bear_Matching_Level{level_num}_{level_name}_Color.pdf"
            zipf.write(pdfs['color'], color_name)
            print(f"  OK Added: {color_name} ({pdfs['color'].stat().st_size / 1024 / 1024:.1f} MB)")
            
            # Add B&W PDF
            bw_name = f"Brown_Bear_Matching_Level{level_num}_{level_name}_BW.pdf"
            zipf.write(pdfs['bw'], bw_name)
            print(f"  OK Added: {bw_name} ({pdfs['bw'].stat().st_size / 1024 / 1024:.1f} MB)")
            
            # Add Terms of Use + Credits
            if TOU_PDF.exists():
                zipf.write(TOU_PDF, "Terms_of_Use_Credits.pdf")
                print(f"  OK Added: Terms_of_Use_Credits.pdf ({TOU_PDF.stat().st_size / 1024:.0f} KB)")
            else:
                print("  WARNING Missing: Terms_of_Use_Credits.pdf")

            # Add level-specific Quick Start Guide
            quick_start_pdf = SUPPORT_DOCS_DIR / f"Quick_Start_Guide_Matching_Level{level_num}.pdf"
            if quick_start_pdf.exists():
                zipf.write(quick_start_pdf, f"Quick_Start_Guide_Matching_Level{level_num}.pdf")
                print(f"  OK Added: Quick_Start_Guide_Matching_Level{level_num}.pdf ({quick_start_pdf.stat().st_size / 1024:.0f} KB)")
            else:
                print(f"  WARNING Missing: Quick_Start_Guide_Matching_Level{level_num}.pdf")
        
        # Get ZIP file size
        zip_size = zip_filename.stat().st_size / 1024 / 1024
        print(f"\nOK Created: {zip_filename.name} ({zip_size:.1f} MB)")
        return zip_filename
        
    except Exception as e:
        print(f"Error creating ZIP for Level {level_num}: {e}")
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
        print(f"  OK {package.name} ({size:.1f} MB)")
    
    print(f"\nOutput location: {OUTPUT_DIR}")
    print("\nAll packages ready for TpT upload!")
    
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
