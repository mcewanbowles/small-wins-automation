#!/usr/bin/env python3
"""
Product Cover Generator for Small Wins Studio
Automatically creates beautiful professional covers for all products.
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from PIL import Image
import fitz  # PyMuPDF

# Color scheme
COLORS = {
    'turquoise': HexColor('#5DBECD'),
    'cream': HexColor('#FFF8E1'),
    'navy': HexColor('#1F4E78'),
    'gold': HexColor('#FFB84D'),
    'orange': HexColor('#F4A259'),
    'blue': HexColor('#4A90E2'),
    'green': HexColor('#7BC47F'),
    'purple': HexColor('#B88DD9'),
}

# Level colors
LEVEL_COLORS = {
    1: COLORS['orange'],
    2: COLORS['blue'],
    3: COLORS['green'],
    4: COLORS['purple'],
}

def extract_pdf_page_as_image(pdf_path, page_num=0, output_path=None, dpi=150):
    """Extract a page from PDF as an image."""
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        
        # Render page to pixmap
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        if output_path:
            img.save(output_path)
        
        doc.close()
        return img
    except Exception as e:
        print(f"  ⚠ Warning: Could not extract page from {pdf_path}: {e}")
        return None

def create_product_cover(product_name, level, pdf_path, output_path):
    """Create a beautiful product cover."""
    
    # Extract product type
    if 'matching' in product_name.lower():
        product_type = 'Matching'
    elif 'find' in product_name.lower() and 'cover' in product_name.lower():
        product_type = 'Find and Cover'
    else:
        product_type = product_name.replace('_', ' ').title()
    
    # Simple level naming - just "Level X" without descriptions
    level_name = f'Level {level}'
    level_color = LEVEL_COLORS.get(level, COLORS['turquoise'])
    
    # Create canvas
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    
    # Background - cream
    c.setFillColor(COLORS['cream'])
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # Top header - turquoise
    header_height = 1.5*inch
    c.setFillColor(COLORS['turquoise'])
    c.rect(0, height - header_height, width, header_height, fill=1, stroke=0)
    
    # Studio name in header
    c.setFillColor(COLORS['cream'])
    c.setFont('Helvetica-Bold', 24)
    c.drawCentredString(width/2, height - 0.75*inch, '🌟 SMALL WINS STUDIO 🌟')
    
    # Product title
    c.setFillColor(COLORS['navy'])
    c.setFont('Helvetica-Bold', 36)
    title_y = height - header_height - 0.7*inch
    c.drawCentredString(width/2, title_y, f'Brown Bear {product_type}')
    
    # Level badge - colored by level
    badge_y = title_y - 0.6*inch
    badge_width = 3*inch
    badge_height = 0.5*inch
    badge_x = (width - badge_width) / 2
    
    c.setFillColor(level_color)
    c.roundRect(badge_x, badge_y, badge_width, badge_height, 0.1*inch, fill=1, stroke=0)
    
    c.setFillColor(COLORS['cream'])
    c.setFont('Helvetica-Bold', 24)
    c.drawCentredString(width/2, badge_y + 0.15*inch, level_name.upper())
    
    # Extract and place preview image from PDF
    preview_y = badge_y - 0.5*inch
    preview_width = 4*inch
    preview_height = 5*inch
    preview_x = (width - preview_width) / 2
    
    # Try to extract page from PDF
    temp_img_path = Path(output_path).parent / f'temp_preview_{level}.png'
    img = extract_pdf_page_as_image(pdf_path, 0, str(temp_img_path))
    
    if img and temp_img_path.exists():
        # Draw preview image
        c.drawImage(str(temp_img_path), preview_x, preview_y - preview_height, 
                   preview_width, preview_height, preserveAspectRatio=True)
        
        # Border around preview
        c.setStrokeColor(level_color)
        c.setLineWidth(3)
        c.rect(preview_x - 5, preview_y - preview_height - 5, 
              preview_width + 10, preview_height + 10, fill=0, stroke=1)
        
        # Clean up temp file
        try:
            temp_img_path.unlink()
        except:
            pass
    else:
        # Placeholder if no preview
        c.setFillColor(level_color)
        c.rect(preview_x, preview_y - preview_height, preview_width, preview_height, fill=1, stroke=0)
        c.setFillColor(COLORS['cream'])
        c.setFont('Helvetica', 14)
        c.drawCentredString(width/2, preview_y - preview_height/2, 'Preview Image')
    
    # Feature bullets
    features_y = preview_y - preview_height - 0.6*inch
    c.setFillColor(COLORS['navy'])
    c.setFont('Helvetica', 14)
    
    # Determine if this is Level 1 Matching for errorless mention
    is_level1_matching = (level == 1 and 'matching' in product_name.lower())
    
    if is_level1_matching:
        features = [
            '✓ Errorless Learning Format',
            '✓ File Folder Activities',
            '✓ Complete with Storage Labels',
            '✓ Research-Based Visual Discrimination'
        ]
    else:
        features = [
            '✓ Research-Based Visual Discrimination',
            '✓ File Folder Activities',
            '✓ Complete with Storage Labels',
            '✓ Level-Appropriate Difficulty'
        ]
    
    for i, feature in enumerate(features):
        c.drawCentredString(width/2, features_y - (i * 0.3*inch), feature)
    
    # Bottom tagline
    c.setFillColor(COLORS['gold'])
    c.setFont('Helvetica-Bold', 18)
    c.drawCentredString(width/2, 0.7*inch, 'Perfect for Special Education!')
    
    # Small footer
    c.setFillColor(COLORS['navy'])
    c.setFont('Helvetica', 10)
    c.drawCentredString(width/2, 0.3*inch, '© 2025 Small Wins Studio')
    
    c.save()
    print(f"  ✓ Created: {output_path.name}")

def main():
    """Generate covers for all products."""
    
    print("=" * 60)
    print("PRODUCT COVER GENERATOR")
    print("Small Wins Studio")
    print("=" * 60)
    print()
    
    # Create output directory
    covers_dir = Path('Covers')
    covers_dir.mkdir(exist_ok=True)
    print(f"✓ Output directory: {covers_dir}")
    print()
    
    # Find all level PDFs
    samples_dir = Path('samples/brown_bear')
    
    products = []
    
    # Matching products
    matching_dir = samples_dir / 'matching'
    if matching_dir.exists():
        for level in range(1, 5):
            pdf_path = matching_dir / f'brown_bear_matching_level{level}_color.pdf'
            if pdf_path.exists():
                products.append({
                    'name': 'matching',
                    'level': level,
                    'pdf_path': pdf_path,
                    'output': covers_dir / f'brown_bear_matching_level{level}_cover.pdf'
                })
    
    # Find & Cover products
    find_cover_dir = samples_dir / 'find_cover'
    if find_cover_dir.exists():
        for level in range(1, 4):
            pdf_path = find_cover_dir / f'brown_bear_find_cover_level{level}_color.pdf'
            if pdf_path.exists():
                products.append({
                    'name': 'find_cover',
                    'level': level,
                    'pdf_path': pdf_path,
                    'output': covers_dir / f'brown_bear_find_cover_level{level}_cover.pdf'
                })
    
    if not products:
        print("⚠ No products found to create covers for!")
        print("  Make sure product PDFs exist in samples/brown_bear/")
        return
    
    print(f"Found {len(products)} product(s) to create covers for")
    print()
    
    # Generate covers
    print("Creating covers...")
    for product in products:
        create_product_cover(
            product['name'],
            product['level'],
            product['pdf_path'],
            product['output']
        )
    
    print()
    print("=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print()
    print(f"✓ Created {len(products)} product covers")
    print(f"✓ All covers saved to: {covers_dir}")
    print()
    print("🎉 Ready for Teachers Pay Teachers!")

if __name__ == '__main__':
    main()
