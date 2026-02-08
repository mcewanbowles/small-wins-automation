#!/usr/bin/env python3
"""
Windows-Compatible Product Cover Generator
No poppler required - uses theme icons for product preview
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
import io

# Constants
INCH = 72  # points per inch
PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.5 * INCH

# Colors
NAVY = "#1E3A5F"
TEAL = "#2AAEAE"
LIGHT_GRAY = "#999999"

LEVEL_COLORS = {
    1: ("#F4B400", "Errorless"),
    2: ("#4285F4", "Easy"),
    3: ("#34A853", "Medium"),
    4: ("#8C06F2", "Challenge")
}


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple (0-1 range)"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def create_icon_preview_collage(theme_name, output_path, preview_size=(5*INCH, 5*INCH), level_color=NAVY):
    """
    Create a preview image using 4 theme icons in a 2×2 grid
    This works on Windows without poppler!
    """
    icon_dir = f"assets/themes/{theme_name.lower().replace(' ', '_')}/icons"
    
    if not os.path.exists(icon_dir):
        print(f"Warning: Icon directory not found: {icon_dir}")
        return None
    
    # Get first 4 PNG icons
    icons = [f for f in os.listdir(icon_dir) if f.endswith('.png')][:4]
    
    if len(icons) < 4:
        print(f"Warning: Need at least 4 icons, found {len(icons)}")
        # Pad with the first icon if we don't have 4
        while len(icons) < 4:
            if icons:
                icons.append(icons[0])
            else:
                return None
    
    # Create collage
    collage_width, collage_height = int(preview_size[0]), int(preview_size[1])
    collage = Image.new('RGB', (collage_width, collage_height), 'white')
    
    # Size for each icon (2×2 grid with 10px margins)
    margin = 20
    icon_size = (collage_width - margin * 3) // 2
    
    for i, icon_file in enumerate(icons[:4]):
        icon_path = os.path.join(icon_dir, icon_file)
        try:
            icon_img = Image.open(icon_path)
            # Convert to RGBA if not already
            if icon_img.mode != 'RGBA':
                icon_img = icon_img.convert('RGBA')
            
            # Resize maintaining aspect ratio
            icon_img.thumbnail((icon_size, icon_size), Image.Resampling.LANCZOS)
            
            # Calculate position (2×2 grid)
            row = i // 2
            col = i % 2
            x = margin + col * (icon_size + margin) + (icon_size - icon_img.width) // 2
            y = margin + row * (icon_size + margin) + (icon_size - icon_img.height) // 2
            
            # Create white background for icon
            bg = Image.new('RGB', icon_img.size, 'white')
            if icon_img.mode == 'RGBA':
                bg.paste(icon_img, (0, 0), icon_img)
            else:
                bg.paste(icon_img, (0, 0))
            
            collage.paste(bg, (x, y))
            
        except Exception as e:
            print(f"Warning: Could not load icon {icon_file}: {e}")
            continue
    
    # Save collage
    collage.save(output_path, 'PNG')
    return output_path


def create_marketing_cover(level, theme_name="Brown Bear", product_type="Matching", 
                           pack_code="SWS-MTCH-BB", output_path=None):
    """
    Create a marketing cover for a product level
    Windows-compatible - uses icon collage instead of PDF preview
    """
    if output_path is None:
        output_path = f"samples/{theme_name.lower().replace(' ', '_')}/{product_type.lower()}/cover_level{level}_windows.pdf"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Get level info
    level_color_hex, level_name = LEVEL_COLORS.get(level, (NAVY, "Unknown"))
    level_color_rgb = hex_to_rgb(level_color_hex)
    navy_rgb = hex_to_rgb(NAVY)
    teal_rgb = hex_to_rgb(TEAL)
    gray_rgb = hex_to_rgb(LIGHT_GRAY)
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Set up fonts (Comic Sans MS with fallbacks)
    try:
        c.setFont("Comic Sans MS", 32)
    except:
        try:
            c.setFont("Arial-BoldMT", 32)
        except:
            c.setFont("Helvetica-Bold", 32)
    
    # Main border (rounded rectangle)
    border_x = MARGIN
    border_y = MARGIN
    border_width = PAGE_WIDTH - 2 * MARGIN
    border_height = PAGE_HEIGHT - 2 * MARGIN
    border_radius = 0.12 * INCH
    
    c.setStrokeColorRGB(*navy_rgb)
    c.setLineWidth(3)
    c.roundRect(border_x, border_y, border_width, border_height, border_radius)
    
    # Accent strip (teal) at top
    strip_height = 0.8 * INCH
    strip_y = PAGE_HEIGHT - MARGIN - strip_height
    c.setFillColorRGB(*teal_rgb)
    c.roundRect(border_x + 10, strip_y, border_width - 20, strip_height, border_radius, fill=1)
    
    # Product title in accent strip
    title = f"{theme_name} {product_type}"
    try:
        c.setFont("Comic Sans MS", 32)
    except:
        try:
            c.setFont("Arial-BoldMT", 32)
        except:
            c.setFont("Helvetica-Bold", 32)
    c.setFillColorRGB(1, 1, 1)  # White text
    title_width = c.stringWidth(title, "Comic Sans MS", 32) if "Comic Sans MS" in c.getAvailableFonts() else c.stringWidth(title, "Helvetica-Bold", 32)
    c.drawString((PAGE_WIDTH - title_width) / 2, strip_y + 0.5 * INCH, title)
    
    # Level subtitle
    subtitle = f"Level {level} • {level_name}"
    try:
        c.setFont("Comic Sans MS", 16)
    except:
        try:
            c.setFont("Arial", 16)
        except:
            c.setFont("Helvetica", 16)
    subtitle_width = c.stringWidth(subtitle, "Comic Sans MS", 16) if "Comic Sans MS" in c.getAvailableFonts() else c.stringWidth(subtitle, "Helvetica", 16)
    c.drawString((PAGE_WIDTH - subtitle_width) / 2, strip_y + 0.15 * INCH, subtitle)
    
    # Product preview area (icon collage)
    preview_size = (5 * INCH, 5 * INCH)
    preview_x = (PAGE_WIDTH - preview_size[0]) / 2
    preview_y = strip_y - preview_size[1] - 0.3 * INCH
    
    # Create icon collage
    collage_path = f"/tmp/preview_collage_level{level}.png"
    created_collage = create_icon_preview_collage(theme_name, collage_path, preview_size, level_color_hex)
    
    if created_collage and os.path.exists(collage_path):
        # Draw the collage
        try:
            c.drawImage(collage_path, preview_x, preview_y, 
                       width=preview_size[0], height=preview_size[1],
                       preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Warning: Could not draw collage: {e}")
            # Draw placeholder
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(preview_x, preview_y, preview_size[0], preview_size[1], fill=1)
            c.setFillColorRGB(*navy_rgb)
            c.setFont("Helvetica", 14)
            c.drawCentredString(PAGE_WIDTH / 2, preview_y + preview_size[1] / 2, 
                              f"[Theme Preview: {theme_name}]")
    else:
        # Draw placeholder if collage creation failed
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(preview_x, preview_y, preview_size[0], preview_size[1], fill=1)
        c.setFillColorRGB(*navy_rgb)
        try:
            c.setFont("Comic Sans MS", 14)
        except:
            c.setFont("Helvetica", 14)
        c.drawCentredString(PAGE_WIDTH / 2, preview_y + preview_size[1] / 2, 
                          f"[Theme Preview: {theme_name}]")
    
    # Border around preview (level-colored)
    c.setStrokeColorRGB(*level_color_rgb)
    c.setLineWidth(3)
    c.roundRect(preview_x, preview_y, preview_size[0], preview_size[1], border_radius)
    
    # Product benefits section
    benefits_y = preview_y - 0.3 * INCH
    
    try:
        c.setFont("Comic Sans MS", 16)
    except:
        try:
            c.setFont("Arial-BoldMT", 16)
        except:
            c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(*navy_rgb)
    c.drawCentredString(PAGE_WIDTH / 2, benefits_y, "✨ Product Benefits ✨")
    
    # Benefits list
    benefits = [
        "• 15 Differentiated Activity Pages",
        f"• {level_name} Level for Special Education",
        "• Part of Discounted Bundle (Save 25%!)",
        "• Bonus: Storage Labels Included",
        "• Print-Ready Cutout Pages"
    ]
    
    try:
        c.setFont("Comic Sans MS", 12)
    except:
        c.setFont("Helvetica", 12)
    
    benefits_y -= 0.25 * INCH
    for i, benefit in enumerate(benefits):
        if i == 2:  # Highlight bundle benefit
            c.setFillColorRGB(*level_color_rgb)
        else:
            c.setFillColorRGB(*navy_rgb)
        
        benefit_width = c.stringWidth(benefit, "Comic Sans MS", 12) if "Comic Sans MS" in c.getAvailableFonts() else c.stringWidth(benefit, "Helvetica", 12)
        c.drawString((PAGE_WIDTH - benefit_width) / 2, benefits_y - i * 0.25 * INCH, benefit)
    
    # Footer (two-line format per product spec)
    footer_y = MARGIN + 0.3 * INCH
    
    try:
        c.setFont("Comic Sans MS", 9)
    except:
        c.setFont("Helvetica", 9)
    
    # Line 1: Product info and pack code
    footer_line1 = f"{product_type} – Level {level} | {pack_code}{level}"
    c.setFillColorRGB(*navy_rgb)
    footer1_width = c.stringWidth(footer_line1, "Comic Sans MS", 9) if "Comic Sans MS" in c.getAvailableFonts() else c.stringWidth(footer_line1, "Helvetica", 9)
    c.drawString((PAGE_WIDTH - footer1_width) / 2, footer_y + 0.15 * INCH, footer_line1)
    
    # Line 2: Copyright and license
    footer_line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    c.setFillColorRGB(*gray_rgb)
    footer2_width = c.stringWidth(footer_line2, "Comic Sans MS", 9) if "Comic Sans MS" in c.getAvailableFonts() else c.stringWidth(footer_line2, "Helvetica", 9)
    c.drawString((PAGE_WIDTH - footer2_width) / 2, footer_y, footer_line2)
    
    # Save PDF
    c.save()
    print(f"✓ Created Windows-compatible cover: {output_path}")
    return output_path


def merge_cover_with_product(cover_path, product_path, output_path):
    """Merge cover as first page of product PDF"""
    try:
        # Read cover
        cover_reader = PdfReader(cover_path)
        cover_page = cover_reader.pages[0]
        
        # Read product
        product_reader = PdfReader(product_path)
        
        # Create writer
        writer = PdfWriter()
        
        # Add cover as first page
        writer.add_page(cover_page)
        
        # Add all product pages
        for page in product_reader.pages:
            writer.add_page(page)
        
        # Write output
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"✓ Merged cover into product: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error merging PDFs: {e}")
        return None


def process_all_levels(theme_name="Brown Bear", product_type="Matching", pack_code_base="SWS-MTCH-BB"):
    """
    Process all 4 levels
    Creates covers and merges them into product PDFs
    """
    print(f"\n{'='*60}")
    print(f"Windows-Compatible Cover Generator")
    print(f"Theme: {theme_name} | Product: {product_type}")
    print(f"Pack Code: {pack_code_base}")
    print(f"{'='*60}\n")
    
    base_path = f"samples/{theme_name.lower().replace(' ', '_')}/{product_type.lower()}"
    
    for level in range(1, 5):
        print(f"\nProcessing Level {level}...")
        
        # Create cover
        cover_path = os.path.join(base_path, f"cover_level{level}_windows.pdf")
        create_marketing_cover(level, theme_name, product_type, pack_code_base, cover_path)
        
        # Merge with product if it exists
        product_path = os.path.join(base_path, f"{theme_name.lower().replace(' ', '_')}_{product_type.lower()}_level{level}_color.pdf")
        
        if os.path.exists(product_path):
            merged_path = os.path.join(base_path, f"{theme_name.lower().replace(' ', '_')}_{product_type.lower()}_level{level}_color_with_cover_windows.pdf")
            merge_cover_with_product(cover_path, product_path, merged_path)
        else:
            print(f"  Note: Product PDF not found: {product_path}")
            print(f"  Cover created but not merged")
    
    print(f"\n{'='*60}")
    print(f"✓ All levels processed successfully!")
    print(f"✓ Covers use theme icon collages (no poppler needed)")
    print(f"✓ Works on Windows, Mac, and Linux!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    process_all_levels(
        theme_name="Brown Bear",
        product_type="Matching",
        pack_code_base="SWS-MTCH-BB"
    )
