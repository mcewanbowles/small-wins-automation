#!/usr/bin/env python3
"""
Complete Product Generator - FINAL VERSION
Merges:
1. New cover with updated text
2. Product pages with page numbers
3. How to Use guide

Per user requirements:
- Cover color matches activity pages
- Updated cover text
- Page numbers on all pages (X/Y format)
"""

import os
import sys
import io
import tempfile
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Configuration
THEME = "brown_bear"
PRODUCT = "matching"

# Paths
COVER_DIR = f"final_products/{THEME}/{PRODUCT}"
PRODUCT_DIR = f"samples/{THEME}/{PRODUCT}"
DOCS_DIR = "Draft General Docs/TOU_etc"
OUTPUT_DIR = f"final_products/{THEME}/{PRODUCT}"

# Level definitions
LEVELS = {
    1: {"name": "Errorless", "file_suffix": "level1"},
    2: {"name": "Easy", "file_suffix": "level2"},
    3: {"name": "Medium", "file_suffix": "level3"},
    4: {"name": "Challenge", "file_suffix": "level4"}
}

def add_page_numbers_to_pdf(input_pdf_path, output_pdf_path, start_page=1):
    """
    Add small page numbers to PDF in format: Page X/Y
    Adds to bottom right corner in small text
    """
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    total_pages = len(reader.pages)
    
    for page_num, page in enumerate(reader.pages):
        # Create overlay with page number
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        width, height = letter
        
        # Add small page number in bottom right (inside margin)
        can.setFont("Helvetica", 8)
        can.setFillColorRGB(0.4, 0.4, 0.4)  # Gray text
        
        # Calculate actual page number (start_page accounts for cover)
        actual_page = start_page + page_num
        page_text = f"Page {actual_page}/{total_pages + start_page - 1}"
        
        # Position in bottom right corner (0.6" from edge)
        x_pos = width - (1.0 * inch)
        y_pos = 0.4 * inch
        
        can.drawString(x_pos, y_pos, page_text)
        can.save()
        
        # Merge page number overlay onto original page
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        page.merge_page(overlay_pdf.pages[0])
        
        writer.add_page(page)
    
    # Write output
    with open(output_pdf_path, 'wb') as output_file:
        writer.write(output_file)
    
    print(f"  ✓ Added page numbers: {os.path.basename(output_pdf_path)}")
    return total_pages

def merge_complete_product(level, mode='color'):
    """
    Merge complete product:
    1. Cover (with updated text)
    2. Product pages (with page numbers)
    3. How to Use guide
    """
    level_info = LEVELS[level]
    level_suffix = level_info["file_suffix"]
    level_name = level_info["name"]
    
    # File paths
    cover_pdf = f"{COVER_DIR}/cover_{level_suffix}_FINAL.pdf"
    
    # Find the product PDF (color or bw)
    if mode == 'color':
        product_pdf = f"{PRODUCT_DIR}/brown_bear_matching_{level_suffix}_color.pdf"
    else:
        product_pdf = f"{PRODUCT_DIR}/brown_bear_matching_{level_suffix}_bw.pdf"
    
    how_to_use_pdf = f"{DOCS_DIR}/How_to_Use.pdf"
    
    # Output file
    output_filename = f"brown_bear_matching_level{level}_{level_name}_{mode}_FINAL.pdf"
    output_path = f"{OUTPUT_DIR}/{output_filename}"
    
    # Check if files exist
    if not os.path.exists(cover_pdf):
        print(f"  ⚠ Cover not found: {cover_pdf}")
        return
    
    if not os.path.exists(product_pdf):
        print(f"  ⚠ Product not found: {product_pdf}")
        return
    
    # Create temporary file with page numbers
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_path = temp_file.name
    temp_file.close()
    
    # Add page numbers to product PDF (starting from page 2 since cover is page 1)
    product_pages = add_page_numbers_to_pdf(product_pdf, temp_path, start_page=2)
    
    # Merge all PDFs
    writer = PdfWriter()
    
    # 1. Add cover (page 1)
    cover_reader = PdfReader(cover_pdf)
    writer.add_page(cover_reader.pages[0])
    
    # 2. Add product pages with numbers (pages 2-16)
    product_reader = PdfReader(temp_path)
    for page in product_reader.pages:
        writer.add_page(page)
    
    # 3. Add How to Use guide (if exists)
    if os.path.exists(how_to_use_pdf):
        how_to_reader = PdfReader(how_to_use_pdf)
        for page in how_to_reader.pages:
            writer.add_page(page)
    
    # Write final PDF
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    
    # Clean up temp file
    os.unlink(temp_path)
    
    total_final_pages = 1 + product_pages + (len(PdfReader(how_to_use_pdf).pages) if os.path.exists(how_to_use_pdf) else 0)
    print(f"✓ Created: {output_filename} ({total_final_pages} pages)")

def generate_all_products():
    """Generate complete products for all levels"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=" * 70)
    print("COMPLETE PRODUCT GENERATOR - FINAL VERSION")
    print("With updated covers and page numbers")
    print("=" * 70)
    print()
    
    for level in [1, 2, 3, 4]:
        level_name = LEVELS[level]["name"]
        print(f"Processing Level {level} ({level_name}):")
        
        # Color version
        merge_complete_product(level, mode='color')
        
        # B&W version
        merge_complete_product(level, mode='bw')
        
        print()
    
    print("=" * 70)
    print("✓ All complete products generated successfully!")
    print("=" * 70)

if __name__ == "__main__":
    generate_all_products()
