#!/usr/bin/env python3
"""
Generate Final Amended Products
- Single cover page with small brown bear image
- Product pages (15 pages)
- How to Use guide (2 pages)
Total: 18 pages (single cover, NOT duplicate)
"""

import os
from PyPDF2 import PdfMerger, PdfReader

# Configuration
THEME = "brown_bear"
PRODUCT = "matching"

# Paths
SAMPLES_DIR = f"samples/{THEME}/{PRODUCT}"
COVERS_DIR = f"final_products/{THEME}/{PRODUCT}"
DOCS_DIR = "Draft General Docs/TOU_etc"
OUTPUT_DIR = f"final_products/{THEME}/{PRODUCT}"

# Level definitions
LEVELS = {
    1: {"name": "Errorless", "color": "#F4B400"},
    2: {"name": "Easy", "color": "#4285F4"},
    3: {"name": "Medium", "color": "#34A853"},
    4: {"name": "Challenge", "color": "#8C06F2"}
}

def create_complete_product(level):
    """
    Create complete product PDF with amended cover.
    Structure:
    - Page 1: Amended cover (single page)
    - Pages 2-16: Product activity pages (15 pages)
    - Pages 17-18: How to Use guide (2 pages)
    """
    level_info = LEVELS[level]
    level_name = level_info["name"]
    
    print(f"\nProcessing Level {level} - {level_name}...")
    
    # For both color and B&W versions
    for version in ["color", "bw"]:
        version_label = "Color" if version == "color" else "BW"
        
        # Input files
        cover_file = f"{COVERS_DIR}/cover_level{level}_amended.pdf"
        
        # Find product PDF (original, without cover)
        # Look for the base level PDF without "_complete" or "_with_cover" suffix
        product_file = f"{SAMPLES_DIR}/brown_bear_matching_level{level}_{version}.pdf"
        
        # Check if file exists, if not try alternative names
        if not os.path.exists(product_file):
            # Try with level name
            product_file = f"{SAMPLES_DIR}/brown_bear_matching_level{level}_{level_name}_{version}.pdf"
        
        if not os.path.exists(product_file):
            print(f"  ⚠ Product file not found: {product_file}")
            print(f"    Skipping {version_label} version")
            continue
        
        how_to_use_file = f"{DOCS_DIR}/How_to_Use.pdf"
        
        # Output file
        output_file = f"{OUTPUT_DIR}/brown_bear_matching_level{level}_{level_name}_{version}_AMENDED.pdf"
        
        # Check if all input files exist
        if not os.path.exists(cover_file):
            print(f"  ✗ Cover not found: {cover_file}")
            continue
        
        if not os.path.exists(how_to_use_file):
            print(f"  ✗ How to Use not found: {how_to_use_file}")
            continue
        
        # Create merger
        merger = PdfMerger()
        
        try:
            # Add SINGLE cover page (amended)
            with open(cover_file, 'rb') as f:
                reader = PdfReader(f)
                print(f"  + Cover: 1 page")
                merger.append(f)
            
            # Add product pages (15 pages typically)
            with open(product_file, 'rb') as f:
                reader = PdfReader(f)
                page_count = len(reader.pages)
                print(f"  + Product pages: {page_count} pages")
                merger.append(f)
            
            # Add How to Use guide
            with open(how_to_use_file, 'rb') as f:
                reader = PdfReader(f)
                guide_pages = len(reader.pages)
                print(f"  + How to Use: {guide_pages} pages")
                merger.append(f)
            
            # Write output
            with open(output_file, 'wb') as output:
                merger.write(output)
            
            # Verify output
            with open(output_file, 'rb') as f:
                final_reader = PdfReader(f)
                total_pages = len(final_reader.pages)
            
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # Convert to MB
            
            print(f"  ✓ Created: {os.path.basename(output_file)}")
            print(f"    Total pages: {total_pages}, Size: {file_size:.1f} MB")
            
        except Exception as e:
            print(f"  ✗ Error creating {version_label} version: {e}")
        
        finally:
            merger.close()

def generate_all_amended_products():
    """Generate amended products for all 4 levels"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=" * 70)
    print("AMENDED PRODUCT GENERATOR")
    print("Creating complete PDFs with SINGLE amended cover page")
    print("=" * 70)
    
    for level in [1, 2, 3, 4]:
        create_complete_product(level)
    
    print()
    print("=" * 70)
    print("✓ All amended products generated!")
    print(f"Location: {OUTPUT_DIR}/")
    print()
    print("Each PDF contains:")
    print("  • Single amended cover page (with small brown bear image)")
    print("  • Product activity pages (15 pages)")
    print("  • How to Use guide (2 pages)")
    print("=" * 70)

if __name__ == "__main__":
    generate_all_amended_products()
