#!/usr/bin/env python3
"""
Freebie Generator for Small Wins Studio TPT Products
Generates a freebie PDF by merging:
- Cover page (with full branding and copyright)
- Page 1 from each level (levels 1-4)
- All cutout pages from all levels

This is a "taster" product to attract customers and funnel them to the full product.

Design Specification: /design/product_specs/freebie.md
"""

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import tempfile

# Standard level colors from Design Constitution
LEVEL_COLORS = {
    1: HexColor('#F4B400'),  # Orange - Errorless
    2: HexColor('#4285F4'),  # Blue - Easy
    3: HexColor('#34A853'),  # Green - Medium
    4: HexColor('#8C06F2'),  # Purple - Challenge
    5: HexColor('#DDA0DD'),  # Light Purple - Real Photos (optional)
}

LEVEL_NAMES = {
    1: 'Errorless',
    2: 'Easy',
    3: 'Medium',
    4: 'Challenge',
    5: 'Real Photos',
}

# Brand colors from Design Constitution
TEAL = HexColor('#2AAEAE')  # Updated to match Design Constitution
NAVY = HexColor('#1E3A5F')
WHITE = HexColor('#FFFFFF')
LIGHT_GRAY = HexColor('#999999')
LIGHT_BLUE_BG = HexColor('#F0F8FF')


def setup_fonts():
    """Setup Comic Sans MS with fallbacks."""
    fonts_tried = []
    
    # Try to register Comic Sans MS
    try:
        pdfmetrics.registerFont(TTFont('ComicSans', 'comic.ttf'))
        pdfmetrics.registerFont(TTFont('ComicSansBold', 'comicbd.ttf'))
        return 'ComicSans', 'ComicSansBold'
    except:
        fonts_tried.append('Comic Sans MS (comic.ttf)')
    
    # Fallback to Arial Rounded MT Bold
    try:
        pdfmetrics.registerFont(TTFont('ArialRounded', 'ARLRDBD.TTF'))
        return 'ArialRounded', 'ArialRounded'
    except:
        fonts_tried.append('Arial Rounded MT Bold')
    
    # Ultimate fallback to Helvetica
    return 'Helvetica', 'Helvetica-Bold'


def generate_freebie_cover(output_path, product_title):
    """
    Generate the freebie cover page with full branding and copyright.
    Follows Design Constitution and freebie.md specifications.
    """
    
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Setup fonts
    regular_font, bold_font = setup_fonts()
    
    # Margins per Design Constitution: 0.5" all sides
    margin = 0.5 * inch
    content_width = width - (2 * margin)
    content_height = height - (2 * margin)
    
    # Draw main border (rounded rectangle, 0.12" radius per Design Constitution)
    c.setStrokeColor(NAVY)
    c.setLineWidth(3)
    c.roundRect(margin, margin, content_width, content_height, 0.12 * inch, stroke=True, fill=False)
    
    # === HEADER SECTION ===
    # Teal header banner
    header_height = 1.0 * inch
    header_y = height - margin - header_height
    c.setFillColor(TEAL)
    c.roundRect(margin + 10, header_y, content_width - 20, header_height, 
                0.12 * inch, fill=True, stroke=False)
    
    # "FREE SAMPLER" text
    c.setFillColor(WHITE)
    c.setFont(bold_font, 42)
    c.drawCentredString(width/2, header_y + 50, "FREE SAMPLER")
    
    c.setFont(regular_font, 20)
    c.drawCentredString(width/2, header_y + 20, "Try Before You Buy!")
    
    # === TITLE SECTION ===
    y = header_y - 50
    c.setFillColor(NAVY)
    c.setFont(bold_font, 28)
    c.drawCentredString(width/2, y, product_title)
    
    # Subtitle
    y -= 35
    c.setFont(regular_font, 16)
    c.drawCentredString(width/2, y, "Sample Activities from All 4 Differentiation Levels")
    
    # === "WHAT'S INCLUDED" BOX ===
    y -= 60
    box_height = 200
    box_y = y - box_height
    
    # Box with rounded corners
    c.setFillColor(LIGHT_BLUE_BG)
    c.setStrokeColor(TEAL)
    c.setLineWidth(2)
    c.roundRect(margin + 30, box_y, content_width - 60, box_height, 
                0.12 * inch, fill=True, stroke=True)
    
    # Box title
    c.setFillColor(NAVY)
    c.setFont(bold_font, 18)
    c.drawCentredString(width/2, y - 30, "What's Included in This FREE Sample:")
    
    # List items with checkmarks
    items = [
        "✓  1 Sample Activity Page from EACH Level (4 levels total)",
        "✓  ALL Matching Cutouts from All Levels",
        "✓  Complete Preview of Differentiation Options",
        "✓  Ready to Print and Use Immediately",
        "✓  Perfect Introduction to the Full Product Bundle"
    ]
    
    c.setFont(regular_font, 13)
    c.setFillColor(NAVY)
    item_y = y - 65
    for item in items:
        c.drawCentredString(width/2, item_y, item)
        item_y -= 25
    
    # === LEVELS PREVIEW SECTION ===
    y = box_y - 50
    c.setFillColor(NAVY)
    c.setFont(bold_font, 16)
    c.drawCentredString(width/2, y, "Preview All 4 Differentiation Levels:")
    
    # Level color boxes (1-4 only)
    y -= 35
    box_width = 110
    box_height = 70
    start_x = (width - (box_width * 4 + 30)) / 2
    
    for level in range(1, 5):
        x = start_x + (level - 1) * (box_width + 10)
        color = LEVEL_COLORS[level]
        
        # Box with level color and rounded corners
        c.setFillColor(color)
        c.setStrokeColor(NAVY)
        c.setLineWidth(2)
        c.roundRect(x, y - box_height, box_width, box_height, 
                    0.12 * inch, fill=True, stroke=True)
        
        # Level number and name
        c.setFillColor(NAVY)
        c.setFont(bold_font, 14)
        c.drawCentredString(x + box_width/2, y - 25, f"Level {level}")
        c.setFont(regular_font, 11)
        c.drawCentredString(x + box_width/2, y - 45, LEVEL_NAMES[level])
    
    # === CALL-TO-ACTION ===
    y = y - box_height - 60
    c.setFillColor(TEAL)
    c.roundRect(width/2 - 180, y - 15, 360, 45, 
                0.12 * inch, fill=True, stroke=False)
    c.setFillColor(WHITE)
    c.setFont(bold_font, 18)
    c.drawCentredString(width/2, y + 5, "Love It? Get the Full Product Bundle!")
    
    # === FOOTER SECTION ===
    footer_y = margin + 60
    
    # Small Wins Studio branding
    c.setFillColor(NAVY)
    c.setFont(bold_font, 12)
    c.drawCentredString(width/2, footer_y + 30, "⭐ Small Wins Studio ⭐")
    
    # TpT Store link
    c.setFillColor(LIGHT_GRAY)
    c.setFont(regular_font, 11)
    c.drawCentredString(width/2, footer_y + 15, 
                       "teacherspayteachers.com/Store/Small-Wins-Studio")
    
    # Copyright and PCS® license (per Design Constitution)
    c.setFont(regular_font, 9)
    c.drawCentredString(width/2, footer_y, 
                       "© 2025 Small Wins Studio. All rights reserved.")
    c.drawCentredString(width/2, footer_y - 12,
                       "PCS® symbols used with active PCS Maker Personal License.")
    
    c.save()
    return output_path
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
