#!/usr/bin/env python3
"""
PDF Page Thumbnail Generator
=============================

Generates PNG thumbnails for each page of product PDFs.
Organizes thumbnails in separate folders by product and level.

Usage:
    python3 generate_page_thumbnails.py

Output:
    Thumbnails/
    ├── brown_bear_matching_level1/
    │   ├── page_01.png
    │   ├── page_02.png
    │   └── ...
    ├── brown_bear_find_cover_level1/
    │   └── ...
    └── ...

Author: Small Wins Studio
Date: 2026-02-03
"""

import os
import sys
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF

# ============================================================================
# CONFIGURATION
# ============================================================================

# Output directory for thumbnails
THUMBNAILS_BASE_DIR = Path("Thumbnails")

# Thumbnail settings
THUMBNAIL_DPI = 150  # DPI for thumbnail quality (150 is good for web/preview)
THUMBNAIL_WIDTH = 800  # Max width in pixels (maintains aspect ratio)

# Products to scan
SAMPLES_DIR = Path("samples/brown_bear")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def ensure_directory(path):
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_product_pdfs():
    """
    Find all product level PDFs.
    
    Returns:
        list: List of tuples (pdf_path, product_name)
    """
    pdfs = []
    
    # Find & Cover PDFs
    find_cover_dir = SAMPLES_DIR / "find_cover"
    if find_cover_dir.exists():
        for level in range(1, 4):  # Levels 1-3
            for mode in ['color', 'bw']:
                pdf_path = find_cover_dir / f"brown_bear_find_cover_level{level}_{mode}.pdf"
                if pdf_path.exists():
                    product_name = f"brown_bear_find_cover_level{level}_{mode}"
                    pdfs.append((pdf_path, product_name))
    
    # Matching PDFs
    matching_dir = SAMPLES_DIR / "matching"
    if matching_dir.exists():
        for level in range(1, 5):  # Levels 1-4
            for mode in ['color', 'bw']:
                pdf_path = matching_dir / f"brown_bear_matching_level{level}_{mode}.pdf"
                if pdf_path.exists():
                    product_name = f"brown_bear_matching_level{level}_{mode}"
                    pdfs.append((pdf_path, product_name))
    
    return pdfs


def convert_pdf_to_thumbnails(pdf_path, product_name, output_dir, dpi=150, max_width=800):
    """
    Convert each page of a PDF to PNG thumbnails.
    
    Args:
        pdf_path: Path to PDF file
        product_name: Name for the product (used for folder)
        output_dir: Base output directory
        dpi: DPI for rendering (default 150)
        max_width: Maximum width for thumbnails (default 800px)
    
    Returns:
        tuple: (success_count, total_pages)
    """
    try:
        # Open PDF
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Create product-specific folder
        product_folder = output_dir / product_name
        ensure_directory(product_folder)
        
        success_count = 0
        
        print(f"\n  Processing: {product_name}")
        print(f"  Pages: {total_pages}")
        
        # Convert each page
        for page_num in range(total_pages):
            try:
                # Get page
                page = doc[page_num]
                
                # Render at specified DPI
                zoom = dpi / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Resize to max width if needed (maintain aspect ratio)
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Save as PNG
                output_path = product_folder / f"page_{page_num+1:02d}.png"
                img.save(output_path, "PNG", optimize=True)
                
                success_count += 1
                
                # Progress indicator
                if (page_num + 1) % 5 == 0 or (page_num + 1) == total_pages:
                    print(f"    ✓ {page_num + 1}/{total_pages} pages converted")
                    
            except Exception as e:
                print(f"    ✗ Error on page {page_num + 1}: {e}")
        
        doc.close()
        
        print(f"  ✓ Completed: {success_count}/{total_pages} pages")
        
        return success_count, total_pages
        
    except Exception as e:
        print(f"  ✗ Error processing {pdf_path}: {e}")
        return 0, 0


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main function to generate all thumbnails."""
    
    print("=" * 70)
    print("PDF PAGE THUMBNAIL GENERATOR")
    print("Small Wins Studio")
    print("=" * 70)
    print()
    
    # Create base output directory
    ensure_directory(THUMBNAILS_BASE_DIR)
    print(f"✓ Output directory: {THUMBNAILS_BASE_DIR}")
    print()
    
    # Find all product PDFs
    print("Scanning for product PDFs...")
    pdfs = get_product_pdfs()
    
    if not pdfs:
        print("✗ No product PDFs found!")
        print(f"  Make sure PDFs exist in {SAMPLES_DIR}")
        return
    
    print(f"✓ Found {len(pdfs)} product PDF(s)")
    print()
    
    # Process each PDF
    print("=" * 70)
    print("GENERATING THUMBNAILS")
    print("=" * 70)
    
    total_success = 0
    total_pages = 0
    processed_products = []
    
    for pdf_path, product_name in pdfs:
        success, pages = convert_pdf_to_thumbnails(
            pdf_path, 
            product_name, 
            THUMBNAILS_BASE_DIR,
            dpi=THUMBNAIL_DPI,
            max_width=THUMBNAIL_WIDTH
        )
        
        total_success += success
        total_pages += pages
        
        if success > 0:
            processed_products.append(product_name)
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    
    print(f"📊 Statistics:")
    print(f"  • Products processed: {len(processed_products)}")
    print(f"  • Total pages: {total_pages}")
    print(f"  • Thumbnails created: {total_success}")
    print(f"  • Success rate: {(total_success/total_pages*100):.1f}%" if total_pages > 0 else "  • Success rate: 0%")
    print()
    
    print(f"📁 Products:")
    for product in processed_products:
        product_folder = THUMBNAILS_BASE_DIR / product
        png_count = len(list(product_folder.glob("*.png")))
        print(f"  ✓ {product} ({png_count} thumbnails)")
    print()
    
    print(f"📂 All thumbnails saved to: {THUMBNAILS_BASE_DIR}/")
    print()
    print("✅ Thumbnail generation complete!")
    print()


if __name__ == "__main__":
    main()
