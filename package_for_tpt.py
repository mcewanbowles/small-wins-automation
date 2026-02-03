#!/usr/bin/env python3
"""
TPT Product Packaging Automation Script
========================================

Automates the complete Teachers Pay Teachers product packaging workflow:
- Preview images (JPG, 150 DPI)
- Thumbnails (PNG, 500x500px square)
- Cover PDFs (professional design)
- Folder structure organization
- ZIP file creation

Usage:
    python package_for_tpt.py

Author: Small Wins Studio
Date: 2026-02-03
"""

import os
import sys
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import zipfile
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

# Color scheme
COLORS = {
    'turquoise': (0.365, 0.745, 0.804),  # #5DBECD (header)
    'cream': (1.0, 0.973, 0.882),         # #FFF8E1 (body)
    'navy': (0.122, 0.306, 0.471),        # #1F4E78 (subtitle)
    'gold': (1.0, 0.722, 0.302),          # #FFB84D (footer)
    'white': (1.0, 1.0, 1.0)
}

# Design specifications
COVER_SPECS = {
    'header_height': 2 * inch,
    'title_fontsize': 42,
    'subtitle_fontsize': 18,
    'footer_fontsize': 14,
    'thumbnail_size': (300, 300)
}

# Output directories
OUTPUT_DIR = Path("TPT_Packages")
PREVIEWS_DIR = OUTPUT_DIR / "Previews"
THUMBNAILS_DIR = OUTPUT_DIR / "Thumbnails"
COVERS_DIR = OUTPUT_DIR / "Covers"
ZIPS_DIR = OUTPUT_DIR / "Zips"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def hex_to_rgb_tuple(hex_color):
    """Convert hex color to RGB tuple (0-1 range)."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def ensure_directories():
    """Create all necessary output directories."""
    for dir_path in [OUTPUT_DIR, PREVIEWS_DIR, THUMBNAILS_DIR, COVERS_DIR, ZIPS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created output directories in {OUTPUT_DIR}")


def find_product_pdfs():
    """Find all product PDF files."""
    # Look in samples directory
    samples_dir = Path("samples/brown_bear")
    pdfs = []
    
    # Find and Cover PDFs
    find_cover_dir = samples_dir / "find_cover"
    if find_cover_dir.exists():
        color_pdf = find_cover_dir / "brown_bear_find_cover_color.pdf"
        if color_pdf.exists():
            pdfs.append(color_pdf)
    
    # Matching PDFs
    matching_dir = samples_dir / "matching"
    if matching_dir.exists():
        color_pdf = matching_dir / "brown_bear_matching_color.pdf"
        if color_pdf.exists():
            pdfs.append(color_pdf)
    
    return pdfs


# ============================================================================
# PREVIEW IMAGES
# ============================================================================

def create_preview_images(pdf_path, product_name):
    """
    Convert first 4 pages of PDF to JPG preview images at 150 DPI.
    
    Args:
        pdf_path: Path to the PDF file
        product_name: Name of the product (for file naming)
    
    Returns:
        List of created preview image paths
    """
    previews = []
    
    try:
        doc = fitz.open(pdf_path)
        num_pages = min(4, len(doc))  # First 4 pages or less
        
        for page_num in range(num_pages):
            page = doc[page_num]
            
            # Render at 150 DPI (zoom factor = 150/72)
            zoom = 150 / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Save as JPG
            preview_path = PREVIEWS_DIR / f"{product_name}_Preview{page_num + 1}.jpg"
            pix.save(preview_path, "jpeg")
            previews.append(preview_path)
        
        doc.close()
        print(f"  ✓ Created {len(previews)} preview images")
        
    except Exception as e:
        print(f"  ✗ Error creating previews: {e}")
    
    return previews


# ============================================================================
# THUMBNAILS
# ============================================================================

def create_thumbnail(pdf_path, product_name):
    """
    Convert first page to square PNG thumbnail (500x500px).
    
    Args:
        pdf_path: Path to the PDF file
        product_name: Name of the product
    
    Returns:
        Path to created thumbnail
    """
    thumbnail_path = None
    
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        
        # Render at high quality (300 DPI)
        zoom = 300 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Crop to center square
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        
        img_square = img.crop((left, top, right, bottom))
        
        # Resize to 500x500
        img_thumbnail = img_square.resize((500, 500), Image.Resampling.LANCZOS)
        
        # Save as PNG
        thumbnail_path = THUMBNAILS_DIR / f"{product_name}_Thumbnail.png"
        img_thumbnail.save(thumbnail_path, "PNG")
        
        doc.close()
        print(f"  ✓ Created thumbnail (500x500px)")
        
    except Exception as e:
        print(f"  ✗ Error creating thumbnail: {e}")
    
    return thumbnail_path


# ============================================================================
# COVER PDF
# ============================================================================

def create_cover_pdf(product_name, thumbnail_path):
    """
    Generate professional cover PDF using ReportLab.
    
    Args:
        product_name: Name of the product
        thumbnail_path: Path to the thumbnail image
    
    Returns:
        Path to created cover PDF
    """
    cover_path = COVERS_DIR / f"{product_name}_Cover.pdf"
    
    try:
        c = canvas.Canvas(str(cover_path), pagesize=letter)
        width, height = letter
        
        # Turquoise header (2 inches tall)
        c.setFillColorRGB(*COLORS['turquoise'])
        c.rect(0, height - COVER_SPECS['header_height'], width, COVER_SPECS['header_height'], fill=1, stroke=0)
        
        # Cream body
        c.setFillColorRGB(*COLORS['cream'])
        c.rect(0, 0, width, height - COVER_SPECS['header_height'], fill=1, stroke=0)
        
        # White title on header
        c.setFillColorRGB(*COLORS['white'])
        c.setFont("Helvetica-Bold", COVER_SPECS['title_fontsize'])
        
        # Format product name for display
        display_name = product_name.replace('_', ' ').replace('brown bear ', '').title()
        title_y = height - COVER_SPECS['header_height'] / 2 + 20
        c.drawCentredString(width / 2, title_y, display_name)
        
        # Centered thumbnail (300x300px)
        if thumbnail_path and thumbnail_path.exists():
            thumb_img = Image.open(thumbnail_path)
            thumb_img = thumb_img.resize(COVER_SPECS['thumbnail_size'], Image.Resampling.LANCZOS)
            
            thumb_x = (width - COVER_SPECS['thumbnail_size'][0]) / 2
            thumb_y = height - COVER_SPECS['header_height'] - COVER_SPECS['thumbnail_size'][1] - 1.5*inch
            
            c.drawImage(ImageReader(thumb_img), thumb_x, thumb_y, 
                       width=COVER_SPECS['thumbnail_size'][0], 
                       height=COVER_SPECS['thumbnail_size'][1])
        
        # Navy subtitle
        c.setFillColorRGB(*COLORS['navy'])
        c.setFont("Helvetica", COVER_SPECS['subtitle_fontsize'])
        subtitle_y = thumb_y - 0.5*inch
        c.drawCentredString(width / 2, subtitle_y, "Engaging File Folder Activities")
        
        # Gold footer with star
        c.setFillColorRGB(*COLORS['gold'])
        c.setFont("Helvetica-Bold", COVER_SPECS['footer_fontsize'])
        footer_text = "© 2025 Small Wins Studio ⭐"
        c.drawCentredString(width / 2, 0.75*inch, footer_text)
        
        c.save()
        print(f"  ✓ Created cover PDF")
        
    except Exception as e:
        print(f"  ✗ Error creating cover: {e}")
        cover_path = None
    
    return cover_path


# ============================================================================
# FOLDER STRUCTURE & ZIP
# ============================================================================

def create_product_package(pdf_path, product_name, cover_path):
    """
    Create organized folder structure and ZIP file.
    
    Args:
        pdf_path: Path to the product PDF
        product_name: Name of the product
        cover_path: Path to the cover PDF
    
    Returns:
        Path to created ZIP file
    """
    # Create temp directory for packaging
    temp_dir = OUTPUT_DIR / "temp" / product_name
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Copy main PDF
        import shutil
        main_pdf = temp_dir / f"{product_name}.pdf"
        shutil.copy(pdf_path, main_pdf)
        
        # Copy cover PDF
        if cover_path and cover_path.exists():
            cover_dest = temp_dir / f"{product_name}_Cover.pdf"
            shutil.copy(cover_path, cover_dest)
        
        # Create Quick Start Guide (placeholder)
        quick_start = temp_dir / "Quick_Start_Guide.pdf"
        c = canvas.Canvas(str(quick_start), pagesize=letter)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, 700, "Quick Start Guide")
        c.setFont("Helvetica", 12)
        c.drawString(100, 660, f"Product: {product_name}")
        c.drawString(100, 640, "1. Print and laminate pages")
        c.drawString(100, 620, "2. Attach storage labels")
        c.drawString(100, 600, "3. Use in file folders")
        c.save()
        
        # Create Terms of Use directory
        terms_dir = temp_dir / "Terms_of_Use"
        terms_dir.mkdir(exist_ok=True)
        
        # Create Terms of Use PDF (placeholder)
        terms_pdf = terms_dir / "Terms_of_Use.pdf"
        c = canvas.Canvas(str(terms_pdf), pagesize=letter)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, 700, "Terms of Use")
        c.setFont("Helvetica", 10)
        c.drawString(100, 660, "© 2025 Small Wins Studio. All rights reserved.")
        c.drawString(100, 640, "For personal or single classroom use only.")
        c.save()
        
        # Create ZIP file
        zip_path = ZIPS_DIR / f"{product_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in temp_dir.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(temp_dir.parent)
                    zipf.write(file, arcname)
        
        # Clean up temp directory
        shutil.rmtree(temp_dir.parent)
        
        print(f"  ✓ Created ZIP package")
        return zip_path
        
    except Exception as e:
        print(f"  ✗ Error creating package: {e}")
        return None


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def process_product(pdf_path):
    """
    Complete packaging workflow for a single product.
    
    Args:
        pdf_path: Path to the product PDF
    
    Returns:
        Dictionary with all created files
    """
    product_name = pdf_path.stem
    
    print(f"\n{'='*60}")
    print(f"Processing: {product_name}")
    print(f"{'='*60}")
    
    results = {
        'product_name': product_name,
        'previews': [],
        'thumbnail': None,
        'cover': None,
        'zip': None
    }
    
    # 1. Create preview images
    print("1. Creating preview images...")
    results['previews'] = create_preview_images(pdf_path, product_name)
    
    # 2. Create thumbnail
    print("2. Creating thumbnail...")
    results['thumbnail'] = create_thumbnail(pdf_path, product_name)
    
    # 3. Create cover PDF
    print("3. Creating cover PDF...")
    results['cover'] = create_cover_pdf(product_name, results['thumbnail'])
    
    # 4. Create package and ZIP
    print("4. Creating folder structure and ZIP...")
    results['zip'] = create_product_package(pdf_path, product_name, results['cover'])
    
    print(f"\n✓ {product_name} - Ready for TPT upload!")
    
    return results


def main():
    """Main entry point for TPT packaging automation."""
    print("\n" + "="*60)
    print("TPT PRODUCT PACKAGING AUTOMATION")
    print("Small Wins Studio")
    print("="*60 + "\n")
    
    # Setup
    ensure_directories()
    
    # Find products
    print("\nScanning for products...")
    products = find_product_pdfs()
    
    if not products:
        print("✗ No product PDFs found!")
        print("  Expected PDFs in samples/brown_bear/")
        return
    
    print(f"✓ Found {len(products)} product(s)")
    
    # Process each product
    all_results = []
    for pdf_path in products:
        results = process_product(pdf_path)
        all_results.append(results)
    
    # Final summary
    print("\n" + "="*60)
    print("PACKAGING COMPLETE!")
    print("="*60)
    
    print("\n📦 ZIP FILES CREATED:")
    for result in all_results:
        if result['zip']:
            print(f"  ✓ {result['zip'].name}")
    
    print("\n🖼️  PREVIEW IMAGES CREATED:")
    for result in all_results:
        for preview in result['previews']:
            print(f"  ✓ {preview.name}")
    
    print("\n📊 SUMMARY:")
    print(f"  • {len(all_results)} products ready for TPT!")
    print(f"  • {sum(len(r['previews']) for r in all_results)} preview images")
    print(f"  • {len([r for r in all_results if r['thumbnail']])} thumbnails")
    print(f"  • {len([r for r in all_results if r['cover']])} covers")
    print(f"  • {len([r for r in all_results if r['zip']])} ZIP packages")
    
    print(f"\n✓ All files in: {OUTPUT_DIR}")
    print("\n🎉 Ready for TPT upload!\n")


if __name__ == "__main__":
    main()
