#!/usr/bin/env python3
"""
Merge Covers into Product PDFs
Adds cover as the first page of each product PDF
"""

import os
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter

def merge_cover_to_product(cover_path, product_path, output_path):
    """
    Merge cover PDF as first page of product PDF
    
    Args:
        cover_path: Path to cover PDF
        product_path: Path to product PDF
        output_path: Path to save merged PDF
    """
    writer = PdfWriter()
    
    # Add cover as first page
    cover_reader = PdfReader(cover_path)
    writer.add_page(cover_reader.pages[0])
    
    # Add all product pages
    product_reader = PdfReader(product_path)
    for page in product_reader.pages:
        writer.add_page(page)
    
    # Write merged PDF
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    
    return len(product_reader.pages) + 1  # Total pages including cover

def main():
    """Main execution"""
    print("=" * 60)
    print("MERGE COVERS INTO PRODUCT PDFs")
    print("Small Wins Studio")
    print("=" * 60)
    print()
    
    # Paths
    base_dir = Path(__file__).parent
    covers_dir = base_dir / "Covers"
    matching_dir = base_dir / "samples" / "brown_bear" / "matching"
    find_cover_dir = base_dir / "samples" / "brown_bear" / "find_cover"
    
    merged_count = 0
    
    # Process Matching products
    print("Processing Matching products...")
    for level in [1, 2, 3, 4]:
        for version in ['color', 'bw']:
            product_name = f"brown_bear_matching_level{level}_{version}"
            cover_path = covers_dir / f"brown_bear_matching_level{level}_cover.pdf"
            product_path = matching_dir / f"{product_name}.pdf"
            
            if cover_path.exists() and product_path.exists():
                total_pages = merge_cover_to_product(
                    str(cover_path),
                    str(product_path),
                    str(product_path)  # Overwrite original
                )
                print(f"  ✓ Merged: {product_name}.pdf ({total_pages} pages)")
                merged_count += 1
            else:
                print(f"  ✗ Missing files for: {product_name}")
    
    print()
    
    # Process Find & Cover products
    print("Processing Find & Cover products...")
    for level in [1, 2, 3]:
        for version in ['color', 'bw']:
            product_name = f"brown_bear_find_cover_level{level}_{version}"
            cover_path = covers_dir / f"brown_bear_find_cover_level{level}_cover.pdf"
            product_path = find_cover_dir / f"{product_name}.pdf"
            
            if cover_path.exists() and product_path.exists():
                total_pages = merge_cover_to_product(
                    str(cover_path),
                    str(product_path),
                    str(product_path)  # Overwrite original
                )
                print(f"  ✓ Merged: {product_name}.pdf ({total_pages} pages)")
                merged_count += 1
            else:
                print(f"  ✗ Missing files for: {product_name}")
    
    print()
    print("=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print()
    print(f"✓ Successfully merged {merged_count} products")
    print("✓ All covers now included as page 1")
    print("✓ Ready for Teachers Pay Teachers!")
    print()

if __name__ == "__main__":
    main()
