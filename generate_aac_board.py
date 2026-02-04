#!/usr/bin/env python3
"""
Generate Brown Bear AAC Board Product
Creates branded pages with AAC boards embedded

Three versions in one product:
- BB01: White background with boxes and text
- BB02: Blue background - no text
- BB05: Blue background with text
"""

import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from PyPDF2 import PdfWriter, PdfReader
from PIL import Image
import io

# Small Wins Studio Brand Colors
TURQUOISE = HexColor('#5DBECD')
CREAM = HexColor('#FFF8E1')
NAVY = HexColor('#1F4E78')
BORDER_GRAY = HexColor('#CCCCCC')

# Directories
ASSETS_DIR = "assets/themes/brown_bear/brown_bear_aac_chat.pdf"
OUTPUT_DIR = "samples/brown_bear/aac_board"
COVERS_DIR = "Covers"

# AAC Board versions
AAC_BOARDS = [
    {"file": "BB01.png", "name": "Version 1: White Background with Text"},
    {"file": "BB02.png", "name": "Version 2: Blue Background (No Text)"},
    {"file": "BB05.png", "name": "Version 3: Blue Background with Text"}
]

def create_output_dirs():
    """Create output directories if they don't exist"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(COVERS_DIR, exist_ok=True)
    print(f"✓ Output directories ready")

def create_branded_page_with_board(c, board_path, page_width, page_height, grayscale=False):
    """
    Create a branded page with AAC board embedded
    Uses landscape orientation with minimal padding
    """
    # Set page to landscape
    c.setPageSize(landscape(letter))
    width, height = landscape(letter)
    
    # Draw border (outer rectangle with small margin)
    margin = 0.25 * inch
    c.setStrokeColor(BORDER_GRAY)
    c.setLineWidth(3)
    c.roundRect(margin, margin, width - 2*margin, height - 2*margin, 10)
    
    # Draw turquoise accent stripe at top
    stripe_height = 0.35 * inch
    c.setFillColor(TURQUOISE)
    c.rect(margin, height - margin - stripe_height, width - 2*margin, stripe_height, fill=True, stroke=False)
    
    # Add title on stripe
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFont('Helvetica-Bold', 20)
    c.drawString(margin + 0.5*inch, height - margin - stripe_height + 0.1*inch, "Brown Bear AAC Board")
    
    # Calculate AAC board area (maximize size with minimal padding)
    board_padding = 0.4 * inch  # Minimal padding from border
    board_x = margin + board_padding
    board_y = margin + board_padding
    board_width = width - 2*margin - 2*board_padding
    board_height = height - 2*margin - stripe_height - 2*board_padding
    
    # Load and place AAC board image
    try:
        img = Image.open(board_path)
        
        # Convert to grayscale if needed
        if grayscale:
            img = img.convert('L')
        
        # Calculate scaling to fit board area while maintaining aspect ratio
        img_width, img_height = img.size
        scale_x = board_width / img_width
        scale_y = board_height / img_height
        scale = min(scale_x, scale_y)  # Use smaller scale to fit
        
        # Calculate final dimensions
        final_width = img_width * scale
        final_height = img_height * scale
        
        # Center the board in available space
        x_offset = board_x + (board_width - final_width) / 2
        y_offset = board_y + (board_height - final_height) / 2
        
        # Save image to temporary buffer
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Draw image
        c.drawImage(board_path, x_offset, y_offset, final_width, final_height, mask='auto')
        
        print(f"  ✓ AAC board embedded: {os.path.basename(board_path)}")
        
    except Exception as e:
        print(f"  ✗ Error loading board: {e}")
        # Draw placeholder
        c.setFillColor(HexColor('#EEEEEE'))
        c.rect(board_x, board_y, board_width, board_height, fill=True)
        c.setFillColor(NAVY)
        c.setFont('Helvetica', 16)
        c.drawCentredString(width/2, height/2, "AAC Board")

def create_aac_board_product(grayscale=False):
    """
    Create the complete AAC board product with 3 versions
    """
    version_name = "bw" if grayscale else "color"
    output_file = os.path.join(OUTPUT_DIR, f"brown_bear_aac_board_{version_name}.pdf")
    
    print(f"\nCreating {'Black & White' if grayscale else 'Color'} version...")
    
    # Create PDF
    c = canvas.Canvas(output_file, pagesize=landscape(letter))
    
    # Add each AAC board version as a page
    for board_info in AAC_BOARDS:
        board_path = os.path.join(ASSETS_DIR, board_info["file"])
        
        if not os.path.exists(board_path):
            print(f"  ✗ Board not found: {board_path}")
            continue
        
        print(f"  Creating page for {board_info['name']}...")
        create_branded_page_with_board(c, board_path, *landscape(letter), grayscale)
        c.showPage()
    
    # Save PDF
    c.save()
    
    file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
    print(f"✓ Created: {output_file} ({file_size:.2f} MB)")
    
    return output_file

def create_aac_board_cover():
    """
    Create professional cover for AAC Board product
    """
    cover_file = os.path.join(COVERS_DIR, "brown_bear_aac_board_cover.pdf")
    
    print(f"\nCreating cover...")
    
    c = canvas.Canvas(cover_file, pagesize=letter)
    width, height = letter
    
    # Background
    c.setFillColor(CREAM)
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Header stripe
    c.setFillColor(TURQUOISE)
    c.rect(0, height - 2*inch, width, 2*inch, fill=True, stroke=False)
    
    # Title
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFont('Helvetica-Bold', 36)
    c.drawCentredString(width/2, height - 1*inch, "Small Wins Studio")
    
    # Product title
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 42)
    c.drawCentredString(width/2, height - 3*inch, "BROWN BEAR")
    c.setFont('Helvetica-Bold', 36)
    c.drawCentredString(width/2, height - 3.6*inch, "AAC Board")
    
    # Subtitle
    c.setFont('Helvetica', 20)
    c.drawCentredString(width/2, height - 4.2*inch, "Communication Board Pack")
    
    # Feature highlights
    c.setFont('Helvetica', 16)
    features_y = height - 5.5*inch
    line_height = 0.35*inch
    
    features = [
        "✓ 3 AAC Board Versions",
        "✓ White & Blue Background Options",
        "✓ With and Without Text",
        "✓ Landscape Format for Easy Use",
        "✓ Color and Black & White Versions",
        "✓ Perfect for AAC Users"
    ]
    
    for feature in features:
        c.drawString(1.5*inch, features_y, feature)
        features_y -= line_height
    
    # Footer
    c.setFont('Helvetica', 14)
    c.setFillColor(HexColor('#FFB84D'))  # Gold
    c.drawCentredString(width/2, 1.5*inch, "Perfect for Special Education & Speech Therapy!")
    
    c.setFillColor(NAVY)
    c.setFont('Helvetica', 10)
    c.drawCentredString(width/2, 0.75*inch, "© 2025 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License")
    
    c.save()
    
    file_size = os.path.getsize(cover_file) / 1024  # KB
    print(f"✓ Created cover: {cover_file} ({file_size:.1f} KB)")
    
    return cover_file

def merge_cover_with_product(cover_file, product_file):
    """
    Merge cover as first page of product PDF
    """
    print(f"\nMerging cover into {os.path.basename(product_file)}...")
    
    # Create a new PDF with cover + product pages
    output = PdfWriter()
    
    # Add cover
    with open(cover_file, 'rb') as f:
        cover_pdf = PdfReader(f)
        output.add_page(cover_pdf.pages[0])
    
    # Add product pages
    with open(product_file, 'rb') as f:
        product_pdf = PdfReader(f)
        for page in product_pdf.pages:
            output.add_page(page)
    
    # Save merged PDF
    with open(product_file, 'wb') as f:
        output.write(f)
    
    total_pages = len(output.pages)
    print(f"✓ Merged cover into product ({total_pages} pages total)")

def main():
    """
    Main function to generate complete AAC Board product
    """
    print("=" * 60)
    print("BROWN BEAR AAC BOARD GENERATOR")
    print("Small Wins Studio")
    print("=" * 60)
    
    # Create directories
    create_output_dirs()
    
    # Create cover
    cover_file = create_aac_board_cover()
    
    # Create color version
    color_file = create_aac_board_product(grayscale=False)
    merge_cover_with_product(cover_file, color_file)
    
    # Create black & white version
    bw_file = create_aac_board_product(grayscale=True)
    merge_cover_with_product(cover_file, bw_file)
    
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print(f"\n✓ Color version: {color_file}")
    print(f"✓ B&W version: {bw_file}")
    print(f"✓ Cover: {cover_file}")
    print(f"\nProduct ready for TPT packaging!")

if __name__ == "__main__":
    main()
