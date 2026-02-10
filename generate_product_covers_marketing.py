#!/usr/bin/env python3
"""
Product Cover Generator - Marketing Focus
Creates professional product covers with marketing benefits and product preview.

Features:
- Product title in accent strip (not level number)
- Product benefits highlighted (page count, bundle info, bonus labels)
- Product preview image
- Footer matching product specification
- Level indicator as subtitle
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


def create_marketing_cover(level, theme_name, product_type, level_pdf_path, output_path, pack_code="SWS-MTCH-BB"):
    """
    Create a professional marketing-focused cover page.
    
    Features:
    - Product title in teal accent strip (e.g., "Brown Bear Matching")
    - Level indicator as subtitle
    - Product benefits (page count, bundle info, storage labels)
    - Product preview image
    - Footer matching product specification
    
    Args:
        level: Level number (1-4)
        theme_name: Theme name (e.g., "Brown Bear")
        product_type: Product type (e.g., "Matching")
        level_pdf_path: Path to the level PDF to extract preview from
        output_path: Path to save the cover PDF
        pack_code: Product pack code (e.g., "SWS-MTCH-BB")
        
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
    
    # Get total page count for footer
    try:
        reader = PdfReader(level_pdf_path)
        total_pages = len(reader.pages) + 1  # +1 for the cover page itself
    except:
        total_pages = 16  # Default assumption
    
    # Draw main border (rounded rectangle, 0.12" radius per Design Constitution)
    c.setStrokeColor(NAVY)
    c.setLineWidth(3)
    c.roundRect(margin, margin, content_width, content_height, 0.12 * inch, stroke=True, fill=False)
    
    # === ACCENT STRIP WITH PRODUCT TITLE ===
    # Teal accent strip with product name (not level)
    accent_height = 1.0 * inch
    accent_y = height - margin - accent_height - 10
    
    c.setFillColor(TEAL)
    c.roundRect(margin + 15, accent_y, content_width - 30, accent_height, 
                0.12 * inch, fill=True, stroke=False)
    
    # Product Title (e.g., "Brown Bear Matching")
    c.setFillColor(WHITE)
    c.setFont(bold_font, 32)
    title_text = f"{theme_name} {product_type}"
    c.drawCentredString(width/2, accent_y + 50, title_text)
    
    # Level indicator as subtitle
    level_color = LEVEL_COLORS.get(level, TEAL)
    c.setFont(regular_font, 16)
    c.drawCentredString(width/2, accent_y + 20, f"Level {level} • {LEVEL_NAMES.get(level, '')}")
    
    # === PRODUCT PREVIEW IMAGE ===
    preview_y = accent_y - 30
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
    
    # Draw border around preview area with level-specific color
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
                           f"Page 1 of {total_pages-1} activity pages")
    
    # === PRODUCT BENEFITS SECTION ===
    benefits_y = preview_y_bottom - 40
    
    # Title for benefits
    c.setFillColor(NAVY)
    c.setFont(bold_font, 14)
    c.drawCentredString(width/2, benefits_y, "✨ Product Benefits ✨")
    
    benefits_y -= 25
    c.setFont(regular_font, 11)
    
    # Benefit 1: Page count
    c.drawCentredString(width/2, benefits_y, f"• {total_pages-1} Differentiated Activity Pages")
    
    # Benefit 2: Contents
    benefits_y -= 18
    c.drawCentredString(width/2, benefits_y, f"• {LEVEL_NAMES.get(level, '')} Level for Special Education")
    
    # Benefit 3: Bundle info
    benefits_y -= 18
    c.setFillColor(level_color)
    c.setFont(bold_font, 11)
    c.drawCentredString(width/2, benefits_y, "• Part of Discounted Bundle (Save 25%!)")
    
    # Benefit 4: Bonus storage labels
    benefits_y -= 18
    c.setFillColor(NAVY)
    c.setFont(regular_font, 11)
    c.drawCentredString(width/2, benefits_y, "• Bonus: Storage Labels Included")
    
    # Benefit 5: Cutout pages
    benefits_y -= 18
    c.drawCentredString(width/2, benefits_y, "• Print-Ready Cutout Pages")
    
    # === FOOTER SECTION (Matching Product Specification Format) ===
    # Two-line footer format per matching.md specification
    footer_y_line1 = margin + 30
    footer_y_line2 = margin + 18
    
    # Line 1: "Matching – Level X | {PACK_CODE}"
    c.setFillColor(NAVY)
    c.setFont(regular_font, 9)
    footer_line1 = f"{product_type} – Level {level} | {pack_code}{level}"
    c.drawCentredString(width/2, footer_y_line1, footer_line1)
    
    # Line 2: Copyright and PCS license
    c.setFillColor(LIGHT_GRAY)
    c.setFont(regular_font, 9)
    footer_line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    c.drawCentredString(width/2, footer_y_line2, footer_line2)
    
    c.save()
    print(f"  ✓ Generated marketing cover for {theme_name} {product_type} Level {level}")
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
        # Read the cover and original PDFs
        cover_reader = PdfReader(cover_pdf_path)
        original_reader = PdfReader(original_pdf_path)
        
        # Create a PDF writer
        writer = PdfWriter()
        
        # Add cover page first
        writer.add_page(cover_reader.pages[0])
        
        # Add all pages from original PDF
        for page in original_reader.pages:
            writer.add_page(page)
        
        # Write the merged PDF
        with open(output_pdf_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"  ✓ Merged cover into PDF: {output_pdf_path}")
        return output_pdf_path
        
    except Exception as e:
        print(f"  ✗ Error merging cover: {e}")
        return None


def process_all_levels(theme_name="Brown Bear", product_type="Matching", pack_code_base="SWS-MTCH-BB"):
    """
    Generate marketing covers for all 4 levels and merge them into the PDFs.
    
    Args:
        theme_name: Name of the theme
        product_type: Type of product
        pack_code_base: Base pack code (level number will be appended)
    """
    
    base_path = f"samples/{theme_name.lower().replace(' ', '_')}/matching"
    
    print(f"\n🎨 Generating Marketing Covers for {theme_name} {product_type}")
    print("=" * 60)
    
    for level in range(1, 5):
        print(f"\n📄 Processing Level {level}...")
        
        # Paths
        level_pdf_name = f"{theme_name.lower().replace(' ', '_')}_matching_level{level}_color.pdf"
        level_pdf_path = os.path.join(base_path, level_pdf_name)
        
        cover_pdf_name = f"cover_level{level}_marketing.pdf"
        cover_pdf_path = os.path.join(base_path, cover_pdf_name)
        
        merged_pdf_name = f"{theme_name.lower().replace(' ', '_')}_matching_level{level}_color_with_cover.pdf"
        merged_pdf_path = os.path.join(base_path, merged_pdf_name)
        
        # Check if level PDF exists
        if not os.path.exists(level_pdf_path):
            print(f"  ⚠ Warning: Level PDF not found: {level_pdf_path}")
            continue
        
        # Generate cover
        create_marketing_cover(
            level=level,
            theme_name=theme_name,
            product_type=product_type,
            level_pdf_path=level_pdf_path,
            output_path=cover_pdf_path,
            pack_code=pack_code_base
        )
        
        # Merge cover into PDF
        merge_cover_into_pdf(cover_pdf_path, level_pdf_path, merged_pdf_path)
    
    print("\n" + "=" * 60)
    print("✅ All marketing covers generated and merged!")
    print(f"📁 Location: {base_path}/")
    print("\nGenerated files:")
    print("  - cover_level{1-4}_marketing.pdf (individual covers)")
    print("  - *_level{1-4}_color_with_cover.pdf (merged products)")


if __name__ == "__main__":
    # Generate covers for Brown Bear Matching
    process_all_levels(
        theme_name="Brown Bear",
        product_type="Matching",
        pack_code_base="SWS-MTCH-BB"
    )
