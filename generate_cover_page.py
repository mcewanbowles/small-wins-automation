#!/usr/bin/env python3
"""
Cover Page Generator for Small Wins Studio TPT Products
Generates color-coded cover pages for each level with product images,
selling points, and professional branding.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import os

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


def generate_cover_page(output_path, product_title, product_subtitle, level, 
                        activity_pages=7, cutout_pages=2, 
                        selling_points=None, product_type='Matching'):
    """Generate a cover page for a TPT product level."""
    
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
    
    # Product image placeholder
    y -= 40
    img_width = 400
    img_height = 280
    img_x = (width - img_width) / 2
    img_y = y - img_height
    
    # Draw placeholder box with light background
    c.setFillColor(HexColor('#F5F5F5'))
    c.setStrokeColor(level_color)
    c.setLineWidth(3)
    c.rect(img_x, img_y, img_width, img_height, fill=True, stroke=True)
    
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


def generate_all_covers(output_dir, book_title, product_type='Matching'):
    """Generate cover pages for all 5 levels."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    generated = []
    
    for level in range(1, 6):
        level_name = LEVEL_NAMES[level]
        output_path = os.path.join(output_dir, f"{book_title.lower().replace(' ', '_')}_{product_type.lower()}_level{level}_cover.pdf")
        
        generate_cover_page(
            output_path=output_path,
            product_title=f"{book_title} {product_type}",
            product_subtitle=f"Level {level}: {level_name}",
            level=level,
            product_type=product_type
        )
        
        generated.append(output_path)
        print(f"Generated: {output_path}")
    
    return generated


if __name__ == '__main__':
    # Generate cover pages for Brown Bear Matching
    output_dir = 'review_pdfs'
    generated = generate_all_covers(output_dir, 'Brown Bear', 'Matching')
    
    print(f"\n✅ Generated {len(generated)} cover pages in {output_dir}/")
