#!/usr/bin/env python3
"""
Level Cover Generator with Product Preview
Creates cover pages for each level with a preview image of the first page,
then merges the cover into the level PDF.

Requirements:
- Extract page 1 from each level PDF as PNG
- Insert PNG preview into cover's product image area
- Merge cover as first page of level PDF
"""

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pdf2image import convert_from_path
from PIL import Image
import os
import tempfile

# Brand colors from Design Constitution
TEAL = HexColor('#2AAEAE')
NAVY = HexColor('#1E3A5F')
WHITE = HexColor('#FFFFFF')
LIGHT_GRAY = HexColor('#999999')

# Level colors
LEVEL_COLORS = {
    1: HexColor('#F4B400'),  # Orange - Errorless
    2: HexColor('#4285F4'),  # Blue - Easy
    3: HexColor('#34A853'),  # Green - Medium
    4: HexColor('#8C06F2'),  # Purple - Challenge
}

LEVEL_NAMES = {
    1: 'Errorless',
    2: 'Easy',
    3: 'Medium',
    4: 'Challenge',
}


def setup_fonts():
    """Setup Comic Sans MS with fallbacks."""
    try:
        pdfmetrics.registerFont(TTFont('ComicSans', 'comic.ttf'))
        pdfmetrics.registerFont(TTFont('ComicSansBold', 'comicbd.ttf'))
        return 'ComicSans', 'ComicSansBold'
    except:
        pass
    
    try:
        pdfmetrics.registerFont(TTFont('ArialRounded', 'ARLRDBD.TTF'))
        return 'ArialRounded', 'ArialRounded'
    except:
        pass
    
    return 'Helvetica', 'Helvetica-Bold'


def extract_first_page_as_image(pdf_path, output_image_path=None):
    """
    Extract the first page of a PDF as a PNG image.
    
    Args:
        pdf_path: Path to the PDF file
        output_image_path: Optional path to save the image
        
    Returns:
        PIL Image object or path to saved image
    """
    try:
        # Convert first page to image at 300 DPI
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300)
        
        if images:
            img = images[0]
            
            if output_image_path:
                img.save(output_image_path, 'PNG')
                return output_image_path
            else:
                return img
        else:
            print(f"  ⚠ Warning: No images extracted from {pdf_path}")
            return None
            
    except Exception as e:
        print(f"  ⚠ Warning: Could not extract image from {pdf_path}: {e}")
        print(f"     (Poppler may not be installed)")
        return None


def create_level_cover_with_preview(level, theme_name, product_type, level_pdf_path, output_path):
    """
    Create a cover page for a specific level with a preview of the first page.
    
    Args:
        level: Level number (1-4)
        theme_name: Theme name (e.g., "Brown Bear")
        product_type: Product type (e.g., "Matching")
        level_pdf_path: Path to the level PDF to extract preview from
        output_path: Path to save the cover PDF
        
    Returns:
        Path to generated cover PDF or None
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
    # Level-specific color header
    level_color = LEVEL_COLORS.get(level, TEAL)
    header_height = 0.8 * inch
    header_y = height - margin - header_height - 10
    
    c.setFillColor(level_color)
    c.roundRect(margin + 10, header_y, content_width - 20, header_height, 
                0.12 * inch, fill=True, stroke=False)
    
    # Level text
    c.setFillColor(WHITE)
    c.setFont(bold_font, 36)
    c.drawCentredString(width/2, header_y + 40, f"Level {level}")
    
    c.setFont(regular_font, 18)
    c.drawCentredString(width/2, header_y + 15, LEVEL_NAMES.get(level, ''))
    
    # === TITLE SECTION ===
    y = header_y - 40
    c.setFillColor(NAVY)
    c.setFont(bold_font, 24)
    c.drawCentredString(width/2, y, f"{theme_name} {product_type}")
    
    # === PRODUCT PREVIEW IMAGE ===
    preview_y = y - 50
    preview_width = 5.0 * inch
    preview_height = 5.0 * inch
    preview_x = (width - preview_width) / 2
    preview_y_bottom = preview_y - preview_height
    
    # Try to extract and insert the product preview image
    preview_inserted = False
    try:
        # Extract first page as image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_img:
            preview_img_path = tmp_img.name
        
        if extract_first_page_as_image(level_pdf_path, preview_img_path):
            # Insert the preview image
            c.drawImage(preview_img_path, preview_x, preview_y_bottom, 
                       width=preview_width, height=preview_height, 
                       preserveAspectRatio=True, mask='auto')
            preview_inserted = True
            
            # Clean up temp file
            try:
                os.unlink(preview_img_path)
            except:
                pass
    except Exception as e:
        print(f"  ⚠ Could not insert preview image: {e}")
    
    # Draw border around preview area
    c.setStrokeColor(level_color)
    c.setLineWidth(3)
    c.roundRect(preview_x, preview_y_bottom, preview_width, preview_height, 
                0.12 * inch, stroke=True, fill=False)
    
    # If preview wasn't inserted, add placeholder text
    if not preview_inserted:
        c.setFillColor(LIGHT_GRAY)
        c.setFont(regular_font, 14)
        c.drawCentredString(width/2, preview_y_bottom + preview_height/2, 
                           "[Product Preview]")
        c.drawCentredString(width/2, preview_y_bottom + preview_height/2 - 20,
                           f"Page 1 of Level {level}")
    
    # === DESCRIPTION ===
    desc_y = preview_y_bottom - 30
    c.setFillColor(NAVY)
    c.setFont(regular_font, 12)
    c.drawCentredString(width/2, desc_y, 
                       f"This level provides {LEVEL_NAMES.get(level, '').lower()} practice")
    
    # === FOOTER SECTION ===
    footer_y = margin + 40
    
    # Small Wins Studio branding
    c.setFillColor(NAVY)
    c.setFont(bold_font, 11)
    c.drawCentredString(width/2, footer_y + 20, "⭐ Small Wins Studio ⭐")
    
    # Copyright and PCS® license
    c.setFillColor(LIGHT_GRAY)
    c.setFont(regular_font, 9)
    c.drawCentredString(width/2, footer_y + 5, 
                       "© 2025 Small Wins Studio. All rights reserved.")
    c.drawCentredString(width/2, footer_y - 7,
                       "PCS® symbols used with active PCS Maker Personal License.")
    
    c.save()
    print(f"  ✓ Generated cover for Level {level}")
    return output_path


def merge_cover_into_pdf(cover_pdf_path, original_pdf_path, output_pdf_path):
    """
    Merge cover page as the first page of a PDF.
    
    Args:
        cover_pdf_path: Path to the cover PDF
        original_pdf_path: Path to the original product PDF
        output_pdf_path: Path to save the merged PDF
        
    Returns:
        Path to merged PDF or None
    """
    try:
        # Read PDFs
        cover_reader = PdfReader(cover_pdf_path)
        original_reader = PdfReader(original_pdf_path)
        
        # Create writer
        writer = PdfWriter()
        
        # Add cover as first page
        writer.add_page(cover_reader.pages[0])
        
        # Add all original pages
        for page in original_reader.pages:
            writer.add_page(page)
        
        # Write merged PDF
        with open(output_pdf_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"  ✓ Merged cover into PDF: {os.path.basename(output_pdf_path)}")
        return output_pdf_path
        
    except Exception as e:
        print(f"  ✗ Error merging cover: {e}")
        return None


def process_all_levels(theme_name="Brown Bear", product_type="Matching"):
    """
    Process all levels: create covers with previews and merge into PDFs.
    
    Args:
        theme_name: Theme name
        product_type: Product type
    """
    
    theme_slug = theme_name.lower().replace(' ', '_')
    product_slug = product_type.lower()
    
    base_dir = f"samples/{theme_slug}/{product_slug}"
    
    print(f"\n{'='*60}")
    print(f"Generating Level Covers with Product Previews")
    print(f"Theme: {theme_name}")
    print(f"Product: {product_type}")
    print(f"{'='*60}\n")
    
    for level in range(1, 5):
        print(f"\nProcessing Level {level}...")
        
        # Paths
        level_pdf = f"{base_dir}/{theme_slug}_{product_slug}_level{level}_color.pdf"
        cover_pdf = f"{base_dir}/{theme_slug}_{product_slug}_level{level}_cover_temp.pdf"
        output_pdf = f"{base_dir}/{theme_slug}_{product_slug}_level{level}_color_with_cover.pdf"
        
        # Check if level PDF exists
        if not os.path.exists(level_pdf):
            print(f"  ⚠ Level {level} PDF not found: {level_pdf}")
            continue
        
        # Generate cover with preview
        cover_path = create_level_cover_with_preview(
            level=level,
            theme_name=theme_name,
            product_type=product_type,
            level_pdf_path=level_pdf,
            output_path=cover_pdf
        )
        
        if cover_path:
            # Merge cover into PDF
            merged_path = merge_cover_into_pdf(
                cover_pdf_path=cover_path,
                original_pdf_path=level_pdf,
                output_pdf_path=output_pdf
            )
            
            if merged_path:
                # Clean up temp cover
                try:
                    os.unlink(cover_pdf)
                except:
                    pass
                
                # Optionally replace original with merged version
                # os.replace(output_pdf, level_pdf)
    
    print(f"\n{'='*60}")
    print("Level cover generation complete!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    # Process Brown Bear Matching levels
    process_all_levels(theme_name="Brown Bear", product_type="Matching")
