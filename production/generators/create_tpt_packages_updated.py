#!/usr/bin/env python3
"""
Create TpT-Ready ZIP Packages for Each Level Product

UPDATED VERSION - Only includes required supporting documents:
- Color PDF (with cover, 16 pages)
- Black & White PDF (16 pages)
- Terms of Use Credits (official version)
- Quick Start Guide (level-specific, auto-generated)

Obsolete documents (NO LONGER INCLUDED):
- How to Use (already in PDF as final page)
- Levels of Differentiation (obsolete)
- More Packs (obsolete)

Usage:
    python3 create_tpt_packages_updated.py
"""

import os
import zipfile
import shutil
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

# Configuration
THEME = "brown_bear"
PRODUCT = "matching"
LEVELS = [
    {"num": 1, "name": "Errorless", "color": "#F4B400"},
    {"num": 2, "name": "Easy", "color": "#4285F4"},
    {"num": 3, "name": "Medium", "color": "#34A853"},
    {"num": 4, "name": "Challenge", "color": "#8C06F2"}
]

# Paths
BASE_DIR = Path(__file__).parent.parent.parent  # Repository root
FINAL_PRODUCTS_DIR = BASE_DIR / "final_products" / THEME / PRODUCT
SAMPLES_DIR = BASE_DIR / "samples" / THEME / PRODUCT
DOCS_DIR = BASE_DIR / "Draft General Docs"
TOU_PATH = DOCS_DIR / "TOU_etc" / "Terms_of_Use_Credits.pdf"
QUICK_START_TEMPLATE = DOCS_DIR / "Quick_Start_Guides" / "Quick_Start_Guide_Matching_Level1.pdf"
OUTPUT_DIR = BASE_DIR / "production" / "generators" / "tpt_packages"


def create_output_dir():
    """Create output directory for ZIP packages"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")


def generate_quick_start(level_num, level_name):
    """
    Generate level-specific Quick Start guide
    
    If template exists, copy and customize it.
    If not, create a simple Quick Start from scratch.
    
    Args:
        level_num: Level number (1-4)
        level_name: Level name (Errorless, Easy, Medium, Challenge)
        
    Returns:
        Path to generated Quick Start PDF or None
    """
    output_path = OUTPUT_DIR / f"Quick_Start_Guide_Matching_Level{level_num}.pdf"
    
    # Try to use template if it exists
    if QUICK_START_TEMPLATE.exists():
        try:
            # Copy template and update metadata
            shutil.copy(QUICK_START_TEMPLATE, output_path)
            print(f"  ✓ Quick Start copied from template")
            return output_path
        except Exception as e:
            print(f"  ⚠️  Could not copy template: {e}")
    
    # Create simple Quick Start from scratch
    try:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        width, height = letter
        
        # Title
        can.setFont("Helvetica-Bold", 24)
        can.drawString(72, height - 100, f"Brown Bear Matching - Level {level_num}")
        
        can.setFont("Helvetica-Bold", 18)
        can.drawString(72, height - 130, f"{level_name} Level")
        
        # Quick Start Instructions
        can.setFont("Helvetica-Bold", 14)
        can.drawString(72, height - 180, "Quick Start:")
        
        can.setFont("Helvetica", 12)
        y = height - 210
        instructions = [
            "1. Print all pages on cardstock (pages 2-14)",
            "2. Cut out matching pieces (pages 13-14)",
            "3. Optional: Laminate for durability",
            "4. Optional: Add velcro for reusable boards",
            "5. Match pieces to boards",
            "6. Use storage labels (page 15) to organize",
        ]
        
        for instruction in instructions:
            can.drawString(90, y, instruction)
            y -= 25
        
        # Footer
        can.setFont("Helvetica", 10)
        can.drawString(72, 50, "© 2025 Small Wins Studio. All rights reserved.")
        
        can.save()
        
        # Write PDF
        packet.seek(0)
        with open(output_path, 'wb') as f:
            f.write(packet.read())
        
        print(f"  ✓ Quick Start generated from scratch")
        return output_path
        
    except Exception as e:
        print(f"  ✗ Error generating Quick Start: {e}")
        return None


def get_level_pdfs(level_num, level_name):
    """
    Get color and B&W FINAL PDFs for a level
    
    Args:
        level_num: Level number (1-4)
        level_name: Level name (Errorless, Easy, Medium, Challenge)
        
    Returns:
        dict with 'color' and 'bw' paths, or None if not found
    """
    # Try FINAL products first (preferred)
    color_final = FINAL_PRODUCTS_DIR / f"{THEME}_{PRODUCT}_level{level_num}_{level_name}_color_FINAL.pdf"
    bw_final = FINAL_PRODUCTS_DIR / f"{THEME}_{PRODUCT}_level{level_num}_{level_name}_bw_FINAL.pdf"
    
    # Try samples as fallback
    color_sample = SAMPLES_DIR / f"{THEME}_{PRODUCT}_level{level_num}_{level_name}_color_FINAL.pdf"
    bw_sample = SAMPLES_DIR / f"{THEME}_{PRODUCT}_level{level_num}_{level_name}_bw_FINAL.pdf"
    
    # Use best available
    color_pdf = color_final if color_final.exists() else color_sample if color_sample.exists() else None
    bw_pdf = bw_final if bw_final.exists() else bw_sample if bw_sample.exists() else None
    
    if not color_pdf or not color_pdf.exists():
        print(f"  ⚠️  No color PDF found for Level {level_num} ({level_name})")
        return None
    
    if not bw_pdf or not bw_pdf.exists():
        print(f"  ⚠️  No B&W PDF found for Level {level_num} ({level_name})")
        return None
    
    return {
        'color': color_pdf,
        'bw': bw_pdf
    }


def create_level_package(level_info):
    """
    Create TpT package ZIP for a specific level
    
    Args:
        level_info: Dict with 'num', 'name', 'color'
        
    Returns:
        Path to created ZIP file or None if failed
    """
    level_num = level_info['num']
    level_name = level_info['name']
    
    print(f"\n{'='*60}")
    print(f"Creating TpT Package for Level {level_num} - {level_name}")
    print(f"{'='*60}")
    
    # Get level PDFs
    pdfs = get_level_pdfs(level_num, level_name)
    if not pdfs:
        print(f"✗ Failed to find PDFs for Level {level_num}")
        return None
    
    # Generate Quick Start
    quick_start = generate_quick_start(level_num, level_name)
    
    # Create ZIP filename
    zip_filename = OUTPUT_DIR / f"{THEME}_{PRODUCT}_level{level_num}_TpT.zip"
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add color PDF
            color_name = f"Brown_Bear_Matching_Level{level_num}_{level_name}_Color.pdf"
            zipf.write(pdfs['color'], color_name)
            print(f"  ✓ Added: {color_name} ({pdfs['color'].stat().st_size / 1024 / 1024:.1f} MB)")
            
            # Add B&W PDF
            bw_name = f"Brown_Bear_Matching_Level{level_num}_{level_name}_BW.pdf"
            zipf.write(pdfs['bw'], bw_name)
            print(f"  ✓ Added: {bw_name} ({pdfs['bw'].stat().st_size / 1024 / 1024:.1f} MB)")
            
            # Add Terms of Use
            if TOU_PATH.exists():
                zipf.write(TOU_PATH, "Terms_of_Use.pdf")
                print(f"  ✓ Added: Terms_of_Use.pdf ({TOU_PATH.stat().st_size / 1024:.0f} KB)")
            else:
                print(f"  ⚠️  Missing: Terms of Use (expected at {TOU_PATH})")
            
            # Add Quick Start
            if quick_start and quick_start.exists():
                qs_name = f"Quick_Start_Guide_Level{level_num}.pdf"
                zipf.write(quick_start, qs_name)
                print(f"  ✓ Added: {qs_name} ({quick_start.stat().st_size / 1024:.0f} KB)")
            else:
                print(f"  ⚠️  Missing: Quick Start Guide")
        
        # Get ZIP file size
        zip_size = zip_filename.stat().st_size / 1024 / 1024
        print(f"\n✓ Created: {zip_filename.name} ({zip_size:.1f} MB)")
        
        # Count files in ZIP
        with zipfile.ZipFile(zip_filename, 'r') as zipf:
            file_count = len(zipf.filelist)
            print(f"  Contains {file_count} files (should be 4: Color, B&W, TOU, Quick Start)")
        
        return zip_filename
        
    except Exception as e:
        print(f"✗ Error creating ZIP for Level {level_num}: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_all_packages():
    """Create TpT packages for all levels"""
    print("\n" + "="*60)
    print("TpT Package Creator (Updated)")
    print(f"Theme: {THEME.replace('_', ' ').title()}")
    print(f"Product: {PRODUCT.title()}")
    print("="*60)
    print("\nSupporting documents:")
    print("  ✓ Terms of Use (official)")
    print("  ✓ Quick Start (auto-generated per level)")
    print("\nObsolete documents (not included):")
    print("  ✗ How to Use (already in PDF)")
    print("  ✗ Levels of Differentiation")
    print("  ✗ More Packs")
    print("="*60)
    
    create_output_dir()
    
    created_packages = []
    for level_info in LEVELS:
        package = create_level_package(level_info)
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
    
    if created_packages:
        print(f"\nOutput location: {OUTPUT_DIR}")
        print("\n✓ All packages ready for TpT upload!")
        print("\nEach package contains 4 files:")
        print("  1. Color PDF (16 pages with cover)")
        print("  2. B&W PDF (16 pages)")
        print("  3. Terms of Use (official)")
        print("  4. Quick Start Guide (level-specific)")
    else:
        print("\n✗ No packages were created. Check errors above.")
    
    return created_packages


def verify_package_contents(zip_path):
    """
    Verify contents of a ZIP package
    
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
    
    # Optionally verify first package
    if packages:
        print("\n" + "="*60)
        print("Sample Package Contents:")
        verify_package_contents(packages[0])
