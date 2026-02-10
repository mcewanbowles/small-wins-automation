#!/usr/bin/env python3
"""
Cover Page Generator for Small Wins Studio TPT Products
Generates color-coded cover pages for each level with product images,
selling points, and professional branding.

Updated to include actual product preview images from first page of PDFs.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from pdf2image import convert_from_path
from PIL import Image
import os
import tempfile

# Level colors
LEVEL_COLORS = {
    1: HexColor('#90EE90'),  # Light Green - Errorless
    2: HexColor('#ADD8E6'),  # Light Blue - Easy
    3: HexColor('#FFD580'),  # Light Orange - Medium
    4: HexColor('#FFB6C1'),  # Light Pink - Challenge
    5: HexColor('#DDA0DD'),  # Light Purple - Real Photos
    0: HexColor('#008B8B'),  # Teal - Unleveled/Bundle
}

LEVEL_NAMES = {
    1: 'Errorless',
    2: 'Easy',
    3: 'Medium',
    4: 'Challenge',
    5: 'Real Photos',
    0: 'Complete Bundle',
}

TEAL = HexColor('#008B8B')
NAVY = HexColor('#1E3A5F')
WHITE = HexColor('#FFFFFF')
LIGHT_GRAY = HexColor('#999999')


def extract_first_page_as_image(pdf_path, output_image_path=None, dpi=150):
    """
    Extract the first page of a PDF as a PNG image.
    
    Args:
        pdf_path: Path to the source PDF
        output_image_path: Path to save the image (optional)
        dpi: DPI for the conversion (default 150 for good quality/size balance)
    
    Returns:
        Path to the generated image
    """
    if not os.path.exists(pdf_path):
        print(f"Warning: PDF not found: {pdf_path}")
        return None
    
    try:
        # Convert first page only
        images = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=1)
        
        if not images:
            print(f"Warning: Could not convert PDF: {pdf_path}")
            return None
        
        # Get the first (and only) image
        image = images[0]
        
        # If no output path specified, create a temp file
        if output_image_path is None:
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            output_image_path = temp_file.name
            temp_file.close()
        
        # Save the image
        image.save(output_image_path, 'PNG')
        print(f"  ✓ Extracted first page from {os.path.basename(pdf_path)}")
        
        return output_image_path
        
    except Exception as e:
        print(f"Warning: Error extracting image from PDF: {e}")
        return None


def generate_cover_page(output_path, product_title, product_subtitle, level, 
                        activity_pages=7, cutout_pages=2, 
                        selling_points=None, product_type='Matching',
                        product_image_path=None):
    """
    Generate a cover page for a TPT product level.
    
    Args:
        output_path: Path to save the cover PDF
        product_title: Title of the product
        product_subtitle: Subtitle (usually level info)
        level: Level number (1-5)
        activity_pages: Number of activity pages
        cutout_pages: Number of cutout pages
        selling_points: List of selling points (optional)
        product_type: Type of product (e.g., 'Matching')
        product_image_path: Path to product preview image (optional)
    """
    
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Get level color
    level_color = LEVEL_COLORS.get(level, LEVEL_COLORS[0])
    level_name = LEVEL_NAMES.get(level, 'Bundle')
    
    # Draw colored border
    border_width = 15
    c.setStrokeColor(level_color)
    c.setLineWidth(border_width)
    c.rect(border_width/2, border_width/2, 
           width - border_width, height - border_width)
    
    # Draw accent stripe at top
    c.setFillColor(level_color)
    c.rect(0, height - 80, width, 80, fill=True, stroke=False)
    
    # Level badge
    if level > 0:
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 24)
        level_text = f"Level {level}: {level_name}"
        c.drawCentredString(width/2, height - 55, level_text)
    else:
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 24)
        c.drawCentredString(width/2, height - 55, "Complete Bundle")
    
    # Title section
    y = height - 130
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 32)
    c.drawCentredString(width/2, y, product_title)
    
    # Subtitle
    y -= 35
    c.setFont('Helvetica', 20)
    c.drawCentredString(width/2, y, product_subtitle)
    
    # Product image area
    y -= 40
    img_width = 400
    img_height = 280
    img_x = (width - img_width) / 2
    img_y = y - img_height
    
    # Draw border around product image area
    c.setStrokeColor(level_color)
    c.setLineWidth(3)
    c.rect(img_x, img_y, img_width, img_height, fill=False, stroke=True)
    
    # Insert product image if available
    if product_image_path and os.path.exists(product_image_path):
        try:
            # Open the image to get dimensions
            img = Image.open(product_image_path)
            orig_width, orig_height = img.size
            
            # Calculate scaling to fit within the box while maintaining aspect ratio
            scale_x = img_width / orig_width
            scale_y = img_height / orig_height
            scale = min(scale_x, scale_y) * 0.95  # 95% to add small padding
            
            # Calculate new dimensions
            new_width = orig_width * scale
            new_height = orig_height * scale
            
            # Center the image in the box
            x_offset = img_x + (img_width - new_width) / 2
            y_offset = img_y + (img_height - new_height) / 2
            
            # Draw the image
            c.drawImage(product_image_path, x_offset, y_offset, 
                       width=new_width, height=new_height, 
                       preserveAspectRatio=True, mask='auto')
            
            print(f"  ✓ Added product image to cover")
            
        except Exception as e:
            print(f"  ⚠ Warning: Could not add product image: {e}")
            # Draw placeholder if image fails
            c.setFillColor(HexColor('#F5F5F5'))
            c.rect(img_x + 2, img_y + 2, img_width - 4, img_height - 4, fill=True, stroke=False)
            c.setFillColor(LIGHT_GRAY)
            c.setFont('Helvetica', 16)
            c.drawCentredString(width/2, img_y + img_height/2, "[Product Image]")
    else:
        # Draw placeholder box with light background
        c.setFillColor(HexColor('#F5F5F5'))
        c.rect(img_x + 2, img_y + 2, img_width - 4, img_height - 4, fill=True, stroke=False)
        
        # Placeholder text
        c.setFillColor(LIGHT_GRAY)
        c.setFont('Helvetica', 16)
        c.drawCentredString(width/2, img_y + img_height/2, "[Product Image]")
    
    # Page counts section
    y = img_y - 30
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 14)
    
    page_info = f"{activity_pages} pages of {product_type.lower()} activities"
    c.drawCentredString(width/2, y, page_info)
    
    y -= 20
    c.setFont('Helvetica', 12)
    c.drawCentredString(width/2, y, f"{cutout_pages} pages of cutouts + bonus storage labels")
    
    # Part of Bundle badge
    y -= 25
    c.setFillColor(level_color)
    c.roundRect(width/2 - 80, y - 10, 160, 25, 5, fill=True, stroke=False)
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(width/2, y - 2, "Part of a Bundle!")
    
    # Selling points section
    y -= 50
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(width/2, y, "What's Inside:")
    
    if selling_points is None:
        selling_points = [
            "Differentiated activities for diverse learners",
            "Print-ready pages with consistent formatting",
            "Color-coded organization system included"
        ]
    
    y -= 25
    c.setFont('Helvetica', 12)
    for point in selling_points[:3]:
        c.drawCentredString(width/2, y, f"✓ {point}")
        y -= 20
    
    # Footer section
    footer_y = 50
    
    # Product info line
    c.setFillColor(LIGHT_GRAY)
    c.setFont('Helvetica', 10)
    product_code = f"BB-{product_type.upper()[:5]}-L{level}" if level > 0 else f"BB-{product_type.upper()[:5]}-BUNDLE"
    c.drawCentredString(width/2, footer_y + 15, f"{product_title} | {product_code}")
    
    # Copyright line
    c.setFont('Helvetica', 9)
    c.drawCentredString(width/2, footer_y, "⭐ Small Wins Studio  © 2025 All rights reserved.")
    
    c.save()
    return output_path


def generate_all_covers(output_dir, book_title, product_type='Matching', 
                       product_pdf_dir=None, product_pdf_pattern=None):
    """
    Generate cover pages for all 5 levels with product images.
    
    Args:
        output_dir: Directory to save cover PDFs
        book_title: Title of the book/theme (e.g., 'Brown Bear')
        product_type: Type of product (e.g., 'Matching')
        product_pdf_dir: Directory containing the product PDFs (optional)
        product_pdf_pattern: Pattern for product PDF filenames (optional)
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    generated = []
    temp_images = []  # Track temp files for cleanup
    
    # If no pattern provided, use default
    if product_pdf_pattern is None:
        product_pdf_pattern = "{book_title}_{product_type}_level{level}_color.pdf"
    
    # If no PDF directory provided, try to find it
    if product_pdf_dir is None:
        # Try samples directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        product_pdf_dir = os.path.join(base_dir, 'samples', 
                                      book_title.lower().replace(' ', '_'),
                                      product_type.lower())
    
    print(f"\nGenerating covers for {book_title} {product_type}...")
    print(f"Looking for product PDFs in: {product_pdf_dir}")
    
    for level in range(1, 6):
        level_name = LEVEL_NAMES[level]
        output_path = os.path.join(output_dir, 
                                   f"{book_title.lower().replace(' ', '_')}_{product_type.lower()}_level{level}_cover.pdf")
        
        # Try to find the product PDF for this level
        product_image_path = None
        if product_pdf_dir and os.path.exists(product_pdf_dir):
            # Build the PDF filename
            pdf_filename = product_pdf_pattern.format(
                book_title=book_title.lower().replace(' ', '_'),
                product_type=product_type.lower(),
                level=level
            )
            product_pdf_path = os.path.join(product_pdf_dir, pdf_filename)
            
            print(f"\nLevel {level}: {level_name}")
            print(f"  Looking for: {pdf_filename}")
            
            if os.path.exists(product_pdf_path):
                # Extract first page as image
                product_image_path = extract_first_page_as_image(product_pdf_path)
                if product_image_path:
                    temp_images.append(product_image_path)
            else:
                print(f"  ⚠ Product PDF not found, using placeholder")
        
        # Generate the cover
        generate_cover_page(
            output_path=output_path,
            product_title=f"{book_title} {product_type}",
            product_subtitle=f"Level {level}: {level_name}",
            level=level,
            product_type=product_type,
            product_image_path=product_image_path
        )
        
        generated.append(output_path)
        print(f"  ✓ Generated: {os.path.basename(output_path)}")
    
    # Clean up temporary image files
    for temp_img in temp_images:
        try:
            if os.path.exists(temp_img):
                os.remove(temp_img)
        except Exception as e:
            print(f"Warning: Could not delete temp file {temp_img}: {e}")
    
    return generated


if __name__ == '__main__':
    # Generate cover pages for Brown Bear Matching with product images
    output_dir = 'review_pdfs'
    generated = generate_all_covers(output_dir, 'Brown Bear', 'Matching')
    
    print(f"\n✅ Generated {len(generated)} cover pages in {output_dir}/")
    print("\nCovers now include product preview images from first page of each level!")
