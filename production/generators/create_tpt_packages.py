#!/usr/bin/env python3
"""
Create TpT ZIP packages for Brown Bear Matching.
Each ZIP contains: Color PDF, B&W PDF, Terms of Use, Quick Start Guide
"""

import zipfile
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PRODUCTS_DIR = BASE_DIR / "production" / "final_products" / "brown_bear" / "matching"
SUPPORT_DOCS_DIR = BASE_DIR / "production" / "support_docs"
OUTPUT_DIR = BASE_DIR / "production" / "final_products" / "brown_bear" / "matching" / "tpt_zips"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def create_tpt_package(level: int):
    """Create a TpT ZIP package for a specific level."""
    
    # File paths
    color_pdf = PRODUCTS_DIR / f"brown_bear_matching_level{level}_color.pdf"
    bw_pdf = PRODUCTS_DIR / f"brown_bear_matching_level{level}_bw.pdf"
    tou_pdf = SUPPORT_DOCS_DIR / "Terms_of_Use_Credits.pdf"
    quick_start = SUPPORT_DOCS_DIR / "Quick_Start_Guide_Matching_Level1.pdf"
    
    # Output ZIP
    zip_name = f"Brown_Bear_Matching_Level_{level}_TpT.zip"
    zip_path = OUTPUT_DIR / zip_name
    
    # Check required files exist
    files_to_include = []
    
    if color_pdf.exists():
        files_to_include.append((color_pdf, f"Brown_Bear_Matching_Level_{level}_COLOR.pdf"))
        print(f"  ✓ Color PDF: {color_pdf.name}")
    else:
        print(f"  ✗ Missing: {color_pdf.name}")
        
    if bw_pdf.exists():
        files_to_include.append((bw_pdf, f"Brown_Bear_Matching_Level_{level}_BW.pdf"))
        print(f"  ✓ B&W PDF: {bw_pdf.name}")
    else:
        print(f"  ✗ Missing: {bw_pdf.name}")
        
    if tou_pdf.exists():
        files_to_include.append((tou_pdf, "Terms_of_Use.pdf"))
        print(f"  ✓ Terms of Use: {tou_pdf.name}")
    else:
        print(f"  ✗ Missing: Terms of Use")
        
    if quick_start.exists():
        files_to_include.append((quick_start, f"Quick_Start_Guide_Level_{level}.pdf"))
        print(f"  ✓ Quick Start: {quick_start.name}")
    else:
        print(f"  ✗ Missing: Quick Start Guide")
    
    # Create ZIP if we have files
    if files_to_include:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for src_path, arc_name in files_to_include:
                zf.write(src_path, arc_name)
        
        zip_size = zip_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ Created: {zip_name} ({zip_size:.1f} MB)")
        return True
    else:
        print(f"  ⚠️ Skipped Level {level} - missing required files")
        return False

def main():
    print("=" * 60)
    print("🎯 Creating TpT ZIP Packages for Brown Bear Matching")
    print("=" * 60)
    
    # Check for support docs
    print("\n📋 Checking support documents...")
    tou_path = SUPPORT_DOCS_DIR / "Terms_of_Use_Credits.pdf"
    qs_path = SUPPORT_DOCS_DIR / "Quick_Start_Guide_Matching_Level1.pdf"
    
    if not tou_path.exists():
        print(f"❌ Terms of Use not found at: {tou_path}")
    if not qs_path.exists():
        print(f"❌ Quick Start not found at: {qs_path}")
    
    # Create packages for each level
    created = 0
    for level in range(1, 5):
        print(f"\n📦 Level {level}:")
        if create_tpt_package(level):
            created += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Created {created} TpT packages in:")
    print(f"   {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
