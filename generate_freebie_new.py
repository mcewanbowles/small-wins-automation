#!/usr/bin/env python3
"""
Freebie Generator for Small Wins Studio TPT Products
Generates a freebie PDF by merging:
- Cover page
- Page 1 from each level (levels 1-4)
- All cutout pages from all levels

This is a "taster" product to attract customers.
"""

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import os
import tempfile

# Level colors
LEVEL_COLORS = {
    1: HexColor('#90EE90'),  # Light Green - Errorless
    2: HexColor('#ADD8E6'),  # Light Blue - Easy
    3: HexColor('#FFD580'),  # Light Orange - Medium
    4: HexColor('#FFB6C1'),  # Light Pink - Challenge
    5: HexColor('#DDA0DD'),  # Light Purple - Real Photos
}

LEVEL_NAMES = {
    1: 'Errorless',
    2: 'Easy',
    3: 'Medium',
    4: 'Challenge',
    5: 'Real Photos',
}

TEAL = HexColor('#008B8B')
NAVY = HexColor('#1E3A5F')
WHITE = HexColor('#FFFFFF')
LIGHT_GRAY = HexColor('#999999')


def generate_freebie_cover(output_path, product_title):
    """Generate the freebie cover page."""
    
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Teal header
    c.setFillColor(TEAL)
    c.rect(0, height - 100, width, 100, fill=True, stroke=False)
    
    # FREEBIE badge
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 36)
    c.drawCentredString(width/2, height - 60, "FREE SAMPLER")
    
    c.setFont('Helvetica', 18)
    c.drawCentredString(width/2, height - 85, "Try Before You Buy!")
    
    # Title
    y = height - 150
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(width/2, y, product_title)
    
    # Subtitle
    y -= 30
    c.setFont('Helvetica', 16)
    c.drawCentredString(width/2, y, "1 Sample Activity from Each Level")
    
    # What's included box
    y -= 60
    box_height = 200
    c.setFillColor(HexColor('#F0F8FF'))
    c.setStrokeColor(TEAL)
    c.setLineWidth(2)
    c.roundRect(50, y - box_height, width - 100, box_height, 10, fill=True, stroke=True)
    
    # What's included title
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(width/2, y - 25, "What's Included:")
    
    # List items
    items = [
        "✓ 1 sample activity page from EACH level (4 levels)",
        "✓ ALL matching cutouts from all levels",
        "✓ Complete preview of differentiation levels",
        "✓ Ready to print and use immediately",
        "✓ Perfect introduction to the full product"
    ]
    
    c.setFont('Helvetica', 12)
    item_y = y - 55
    for item in items:
        c.drawCentredString(width/2, item_y, item)
        item_y -= 22
    
    # Levels preview
    y = y - box_height - 40
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(width/2, y, "Preview All 4 Levels:")
    
    # Level color boxes (only 1-4)
    y -= 30
    box_width = 100
    box_height = 60
    start_x = (width - (box_width * 4 + 30)) / 2
    
    for level in range(1, 5):
        x = start_x + (level - 1) * (box_width + 10)
        color = LEVEL_COLORS[level]
        
        c.setFillColor(color)
        c.setStrokeColor(NAVY)
        c.setLineWidth(1)
        c.roundRect(x, y - box_height, box_width, box_height, 5, fill=True, stroke=True)
        
        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 11)
        c.drawCentredString(x + box_width/2, y - 25, f"Level {level}")
        c.setFont('Helvetica', 9)
        c.drawCentredString(x + box_width/2, y - 40, LEVEL_NAMES[level])
    
    # CTA section
    y = y - box_height - 50
    c.setFillColor(TEAL)
    c.roundRect(width/2 - 150, y - 10, 300, 35, 8, fill=True, stroke=False)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(width/2, y + 3, "Love it? Get the Full Bundle!")
    
    # Footer
    footer_y = 50
    c.setFillColor(LIGHT_GRAY)
    c.setFont('Helvetica', 10)
    c.drawCentredString(width/2, footer_y + 15, "Visit: teacherspayteachers.com/Store/Small-Wins-Studio")
    c.setFont('Helvetica', 9)
    c.drawCentredString(width/2, footer_y, "⭐ Small Wins Studio  © 2025 All rights reserved.")
    
    c.save()
    return output_path


def extract_page_from_pdf(source_pdf, page_number):
    """
    Extract a specific page from a PDF.
    
    Args:
        source_pdf: Path to source PDF
        page_number: Page number to extract (1-indexed)
    
    Returns:
        PyPDF2 page object or None
    """
    try:
        reader = PdfReader(source_pdf)
        if page_number <= len(reader.pages):
            return reader.pages[page_number - 1]  # Convert to 0-indexed
        else:
            print(f"  ⚠ Warning: Page {page_number} not found in {os.path.basename(source_pdf)}")
            return None
    except Exception as e:
        print(f"  ⚠ Warning: Could not read {os.path.basename(source_pdf)}: {e}")
        return None


def find_cutout_pages(pdf_path):
    """
    Find cutout pages in a PDF by looking for pages that likely contain cutouts.
    In matching PDFs, cutout pages typically come after the activity pages.
    
    For now, we'll extract the last 2 pages which are typically cutouts and storage labels.
    
    Args:
        pdf_path: Path to the PDF
    
    Returns:
        List of page objects
    """
    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        
        # Assuming cutout pages are typically the last 2-3 pages
        # We'll take last 2 pages (cutouts page and possibly storage labels)
        cutout_pages = []
        
        if total_pages >= 2:
            # Get last 2 pages (cutouts and storage labels)
            cutout_pages.append(reader.pages[-2])  # Second to last
            cutout_pages.append(reader.pages[-1])  # Last page
        
        return cutout_pages
        
    except Exception as e:
        print(f"  ⚠ Warning: Could not extract cutout pages from {os.path.basename(pdf_path)}: {e}")
        return []


def generate_freebie(output_path, product_title, product_type='Matching',
                    product_pdf_dir=None, product_pdf_pattern=None):
    """
    Generate a freebie PDF by merging:
    - Cover page
    - Page 1 from Level 1
    - Page 1 from Level 2
    - Page 1 from Level 3
    - Page 1 from Level 4
    - All cutout pages from all levels
    
    Args:
        output_path: Path to save the freebie PDF
        product_title: Title of the product
        product_type: Type of product (e.g., 'Matching')
        product_pdf_dir: Directory containing the product PDFs
        product_pdf_pattern: Pattern for product PDF filenames
    """
    
    print(f"\nGenerating freebie for {product_title}...")
    
    # Create PDF writer
    writer = PdfWriter()
    
    # If no PDF directory provided, try to find it
    if product_pdf_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        book_title = product_title.replace(f" {product_type}", "")
        product_pdf_dir = os.path.join(base_dir, 'samples', 
                                      book_title.lower().replace(' ', '_'),
                                      product_type.lower())
    
    # If no pattern provided, use default
    if product_pdf_pattern is None:
        book_title = product_title.replace(f" {product_type}", "")
        product_pdf_pattern = "{book_title}_{product_type}_level{level}_color.pdf"
    
    print(f"Looking for product PDFs in: {product_pdf_dir}")
    
    # Step 1: Generate and add cover page
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_cover:
        cover_path = temp_cover.name
    
    generate_freebie_cover(cover_path, product_title)
    cover_reader = PdfReader(cover_path)
    writer.add_page(cover_reader.pages[0])
    print("  ✓ Added freebie cover page")
    
    # Step 2: Add page 1 from each level (levels 1-4)
    for level in range(1, 5):
        book_title = product_title.replace(f" {product_type}", "")
        pdf_filename = product_pdf_pattern.format(
            book_title=book_title.lower().replace(' ', '_'),
            product_type=product_type.lower(),
            level=level
        )
        pdf_path = os.path.join(product_pdf_dir, pdf_filename)
        
        print(f"\nLevel {level}: {LEVEL_NAMES[level]}")
        print(f"  Looking for: {pdf_filename}")
        
        if os.path.exists(pdf_path):
            # Extract page 1
            page = extract_page_from_pdf(pdf_path, 1)
            if page:
                writer.add_page(page)
                print(f"  ✓ Added page 1 from Level {level}")
        else:
            print(f"  ⚠ PDF not found: {pdf_filename}")
    
    # Step 3: Add all cutout pages from all levels
    print("\nAdding cutout pages from all levels:")
    
    for level in range(1, 5):
        book_title = product_title.replace(f" {product_type}", "")
        pdf_filename = product_pdf_pattern.format(
            book_title=book_title.lower().replace(' ', '_'),
            product_type=product_type.lower(),
            level=level
        )
        pdf_path = os.path.join(product_pdf_dir, pdf_filename)
        
        if os.path.exists(pdf_path):
            cutout_pages = find_cutout_pages(pdf_path)
            for page in cutout_pages:
                writer.add_page(page)
            if cutout_pages:
                print(f"  ✓ Added {len(cutout_pages)} cutout page(s) from Level {level}")
    
    # Write the final PDF
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    
    # Clean up temp cover
    try:
        os.remove(cover_path)
    except:
        pass
    
    print(f"\n✅ Generated freebie: {output_path}")
    print(f"   Total pages: {len(writer.pages)}")
    
    return output_path


if __name__ == '__main__':
    output_dir = 'review_pdfs'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate Brown Bear Matching Freebie
    output_path = os.path.join(output_dir, 'brown_bear_matching_freebie.pdf')
    generate_freebie(output_path, 'Brown Bear Matching', 'Matching')
    
    print("\nFreebie now includes actual pages from the product!")
    print("Structure: Cover + Page 1 from each level + All cutouts")
