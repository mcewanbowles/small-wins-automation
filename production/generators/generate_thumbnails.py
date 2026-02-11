#!/usr/bin/env python3
"""
Thumbnail Generator
Creates 280×280 and 500×500 PNG thumbnails from PDF first page.
Uses PDF to image conversion for TpT product listings.
"""

import os
from pathlib import Path

# Try to import pdf2image
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("⚠️ pdf2image not available. Install with: pip install pdf2image")

# Try to import PIL
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL not available. Install with: pip install Pillow")

# Constants
BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "production" / "marketing"


def create_thumbnail_from_pdf(pdf_path: Path, output_dir: Path, sizes: list = None) -> list:
    """
    Create thumbnails from first page of PDF.
    
    Args:
        pdf_path: Path to source PDF
        output_dir: Directory to save thumbnails
        sizes: List of (width, height) tuples. Default: [(280, 280), (500, 500)]
    
    Returns:
        List of created thumbnail paths
    """
    if not PDF2IMAGE_AVAILABLE or not PIL_AVAILABLE:
        print("❌ Required libraries not available")
        return []
    
    if sizes is None:
        sizes = [(280, 280), (500, 500)]
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get base name for thumbnails
    base_name = pdf_path.stem
    
    created_files = []
    
    try:
        # Convert first page of PDF to image
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300)
        
        if not images:
            print(f"❌ No pages found in: {pdf_path}")
            return []
        
        original_image = images[0]
        
        for width, height in sizes:
            # Calculate crop to make square (centered)
            img_width, img_height = original_image.size
            
            # Create a square crop from center
            if img_width > img_height:
                # Landscape - crop sides
                left = (img_width - img_height) // 2
                crop_box = (left, 0, left + img_height, img_height)
            else:
                # Portrait - crop top/bottom
                top = (img_height - img_width) // 2
                crop_box = (0, top, img_width, top + img_width)
            
            # Crop to square
            cropped = original_image.crop(crop_box)
            
            # Resize to target size
            thumbnail = cropped.resize((width, height), Image.LANCZOS)
            
            # Save thumbnail
            filename = f"{base_name}_thumbnail_{width}x{height}.png"
            output_path = output_dir / filename
            thumbnail.save(output_path, "PNG")
            
            created_files.append(output_path)
            print(f"✅ Created: {output_path}")
    
    except Exception as e:
        print(f"❌ Error creating thumbnail: {e}")
    
    return created_files


def create_thumbnail_from_image(image_path: Path, output_dir: Path, sizes: list = None) -> list:
    """
    Create thumbnails from an existing image file.
    
    Args:
        image_path: Path to source image (PNG, JPG, etc.)
        output_dir: Directory to save thumbnails
        sizes: List of (width, height) tuples. Default: [(280, 280), (500, 500)]
    
    Returns:
        List of created thumbnail paths
    """
    if not PIL_AVAILABLE:
        print("❌ PIL not available")
        return []
    
    if sizes is None:
        sizes = [(280, 280), (500, 500)]
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get base name for thumbnails
    base_name = image_path.stem
    
    created_files = []
    
    try:
        original_image = Image.open(image_path)
        
        for width, height in sizes:
            # Calculate crop to make square (centered)
            img_width, img_height = original_image.size
            
            # Create a square crop from center
            if img_width > img_height:
                left = (img_width - img_height) // 2
                crop_box = (left, 0, left + img_height, img_height)
            else:
                top = (img_height - img_width) // 2
                crop_box = (0, top, img_width, top + img_width)
            
            cropped = original_image.crop(crop_box)
            thumbnail = cropped.resize((width, height), Image.LANCZOS)
            
            filename = f"{base_name}_thumbnail_{width}x{height}.png"
            output_path = output_dir / filename
            thumbnail.save(output_path, "PNG")
            
            created_files.append(output_path)
            print(f"✅ Created: {output_path}")
    
    except Exception as e:
        print(f"❌ Error creating thumbnail: {e}")
    
    return created_files


def generate_all_thumbnails(theme_id: str, product_type: str = "matching") -> None:
    """Generate thumbnails for all product PDFs."""
    
    # Try multiple possible locations for PDFs
    possible_dirs = [
        BASE_DIR / "production" / "final_products" / theme_id / product_type,
        BASE_DIR / "review_pdfs",
        BASE_DIR / "samples" / theme_id / product_type,
    ]
    
    products_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists():
            products_dir = dir_path
            break
    
    if not products_dir:
        print(f"❌ No products directory found")
        return
    
    # Output directory
    output_dir = OUTPUT_DIR / theme_id / product_type / "thumbnails"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find PDFs - look for level PDFs
    pdfs = list(products_dir.glob(f"*{theme_id}*{product_type}*level*_color.pdf"))
    
    if not pdfs:
        pdfs = list(products_dir.glob(f"*{theme_id}*level*.pdf"))
    
    if not pdfs:
        pdfs = list(products_dir.glob("*level*.pdf"))
    
    if not pdfs:
        print("❌ No PDFs found for thumbnail generation")
        return
    
    print(f"📂 Found {len(pdfs)} PDFs")
    
    for pdf_path in pdfs:
        print(f"\n📄 Processing: {pdf_path.name}")
        create_thumbnail_from_pdf(pdf_path, output_dir)
    
    print(f"\n📁 All thumbnails saved to: {output_dir}")


if __name__ == "__main__":
    print("=" * 60)
    print("Thumbnail Generator")
    print("=" * 60)
    
    # Check dependencies
    if not PDF2IMAGE_AVAILABLE:
        print("Installing pdf2image...")
        os.system("pip install pdf2image")
    
    if not PIL_AVAILABLE:
        print("Installing Pillow...")
        os.system("pip install Pillow")
    
    # Generate thumbnails for Brown Bear Matching
    generate_all_thumbnails("brown_bear", "matching")
    
    print("\n✅ Thumbnail generation complete!")
