#!/usr/bin/env python3
"""
Complete Product Generator with Amendments
Generates final PDFs with:
- Level-colored accent strips (not teal)
- Product preview images
- Proper title padding
- How to Use merged into each level PDF
"""

import os
from PyPDF2 import PdfMerger, PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from PIL import Image
import io

# Configuration
THEME = "brown_bear"
PRODUCT = "matching"
PACK_CODE_BASE = "SWS-MTCH-BB"

# Level definitions with LEVEL-SPECIFIC COLORS (not teal!)
LEVELS = {
    1: {
        "name": "Errorless",
        "color": "#F4B400",  # Orange - MATCHES level pages
        "description": "Errorless Level for Special Education"
    },
    2: {
        "name": "Easy",
        "color": "#4285F4",  # Blue - MATCHES level pages
        "description": "Easy Level for Special Education"
    },
    3: {
        "name": "Medium",
        "color": "#34A853",  # Green - MATCHES level pages
        "description": "Medium Level for Special Education"
    },
    4: {
        "name": "Challenge",
        "color": "#8C06F2",  # Purple - MATCHES level pages
        "description": "Challenge Level for Special Education"
    }
}

# Paths
SAMPLES_DIR = f"samples/{THEME}/{PRODUCT}"
DOCS_DIR = "Draft General Docs/TOU_etc"
OUTPUT_DIR = f"final_products/{THEME}/{PRODUCT}"
ICONS_DIR = f"assets/themes/{THEME}/icons"

# Navy and other colors
NAVY = "#1E3A5F"
WHITE = "#FFFFFF"

def create_cover_with_level_color(level, theme_name, product_type, pack_code):
    """
    Create cover with LEVEL-SPECIFIC accent strip color and proper padding
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import inch
    from PIL import Image
    import glob
    
    width, height = letter
    level_info = LEVELS[level]
    level_color = level_info["color"]  # Use LEVEL color, NOT teal!
    level_name = level_info["name"]
    
    # Create PDF
    output_path = f"{OUTPUT_DIR}/cover_level{level}_final.pdf"
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Fonts (Comic Sans MS with fallbacks)
    try:
        c.setFont("Comic-Sans-MS-Bold", 32)
    except:
        try:
            c.setFont("Arial-Rounded-MT-Bold", 32)
        except:
            c.setFont("Helvetica-Bold", 32)
    
    # Page setup
    margin = 0.5 * inch
    border_radius = 0.12 * inch
    
    # Main border (navy)
    c.setStrokeColor(HexColor(NAVY))
    c.setLineWidth(3)
    c.roundRect(margin, margin, width - 2*margin, height - 2*margin, border_radius)
    
    # Accent strip with LEVEL COLOR (not teal!)
    # AMENDMENT: Proper padding from border (0.4" instead of 0.1")
    strip_top = height - margin - 0.4*inch  # More padding from top border
    strip_height = 1.2 * inch
    strip_left = margin + 0.2*inch
    strip_right = width - margin - 0.2*inch
    
    c.setFillColor(HexColor(level_color))  # USE LEVEL COLOR!
    c.roundRect(strip_left, strip_top - strip_height, 
                strip_right - strip_left, strip_height, 
                border_radius, fill=1, stroke=0)
    
    # Title in accent strip with PROPER PADDING
    c.setFillColor(HexColor(WHITE))
    
    # Product title (larger, white) with padding from top
    try:
        c.setFont("Comic-Sans-MS-Bold", 32)
    except:
        try:
            c.setFont("Arial-Rounded-MT-Bold", 32)
        except:
            c.setFont("Helvetica-Bold", 32)
    
    title = f"{theme_name.title()} {product_type.title()}"
    title_y = strip_top - 0.5*inch  # Padding from top of strip
    c.drawCentredString(width/2, title_y, title)
    
    # Level subtitle (smaller)
    try:
        c.setFont("Comic-Sans-MS", 18)
    except:
        try:
            c.setFont("Arial-Rounded-MT-Bold", 18)
        except:
            c.setFont("Helvetica", 18)
    
    subtitle = f"Level {level} • {level_name}"
    subtitle_y = strip_top - strip_height + 0.4*inch
    c.drawCentredString(width/2, subtitle_y, subtitle)
    
    # Product preview with icon collage (Windows-compatible)
    preview_size = 5 * inch
    preview_x = (width - preview_size) / 2
    preview_y = strip_top - strip_height - preview_size - 0.5*inch
    
    # Border around preview with LEVEL COLOR
    c.setStrokeColor(HexColor(level_color))
    c.setLineWidth(3)
    c.roundRect(preview_x, preview_y, preview_size, preview_size, border_radius)
    
    # Create icon collage
    try:
        icon_files = glob.glob(f"{ICONS_DIR}/*.png")[:4]
        if icon_files:
            # Create 2x2 icon collage
            collage_size = int(preview_size * 72)  # Convert to pixels
            collage = Image.new('RGB', (collage_size, collage_size), 'white')
            
            icon_size = collage_size // 2
            positions = [(0, 0), (icon_size, 0), (0, icon_size), (icon_size, icon_size)]
            
            for idx, (icon_path, pos) in enumerate(zip(icon_files, positions)):
                try:
                    icon = Image.open(icon_path)
                    icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
                    if icon.mode == 'RGBA':
                        # Paste with transparency
                        collage.paste(icon, pos, icon)
                    else:
                        collage.paste(icon, pos)
                except Exception as e:
                    print(f"  Warning: Could not load icon {icon_path}: {e}")
            
            # Save and insert collage
            img_buffer = io.BytesIO()
            collage.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            c.drawImage(Image.open(img_buffer), 
                       preview_x + 0.1*inch, preview_y + 0.1*inch,
                       preview_size - 0.2*inch, preview_size - 0.2*inch,
                       preserveAspectRatio=True)
    except Exception as e:
        print(f"  Warning: Could not create icon collage: {e}")
        # Fallback: show text
        c.setFillColor(HexColor(NAVY))
        try:
            c.setFont("Comic-Sans-MS", 14)
        except:
            c.setFont("Helvetica", 14)
        c.drawCentredString(width/2, preview_y + preview_size/2, 
                           f"[Product Preview - Level {level}]")
        c.drawCentredString(width/2, preview_y + preview_size/2 - 20,
                           "Icon Collage")
    
    # Benefits section
    benefits_y = preview_y - 0.4*inch
    c.setFillColor(HexColor(NAVY))
    
    try:
        c.setFont("Comic-Sans-MS-Bold", 16)
    except:
        c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, benefits_y, "✨ Product Benefits ✨")
    
    # Benefits list
    try:
        c.setFont("Comic-Sans-MS", 12)
    except:
        c.setFont("Helvetica", 12)
    
    benefits = [
        "• 15 Differentiated Activity Pages",
        f"• {level_info['description']}",
        "• Part of Discounted Bundle (Save 25%!)",
        "• Bonus: Storage Labels Included",
        "• Print-Ready Cutout Pages"
    ]
    
    benefit_y = benefits_y - 0.3*inch
    for i, benefit in enumerate(benefits):
        if i == 2:  # Highlight bundle savings in level color
            c.setFillColor(HexColor(level_color))
            c.drawCentredString(width/2, benefit_y, benefit)
            c.setFillColor(HexColor(NAVY))
        else:
            c.drawCentredString(width/2, benefit_y, benefit)
        benefit_y -= 0.25*inch
    
    # Footer (two-line format per product spec)
    footer_y = margin + 0.5*inch
    
    try:
        c.setFont("Comic-Sans-MS", 9)
    except:
        c.setFont("Helvetica", 9)
    
    # Line 1: Pack code and level
    c.setFillColor(HexColor(NAVY))
    footer_line1 = f"{product_type.title()} – Level {level} | {pack_code}{level}"
    c.drawCentredString(width/2, footer_y + 0.15*inch, footer_line1)
    
    # Line 2: Copyright and license (light gray)
    c.setFillColor(HexColor("#999999"))
    footer_line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    c.drawCentredString(width/2, footer_y, footer_line2)
    
    c.save()
    print(f"  ✓ Created cover with {level_name} color ({level_color})")
    return output_path


def merge_complete_product(level, theme_name, product_type):
    """
    Merge complete product: Cover + Product Pages + How to Use
    """
    merger = PdfMerger()
    
    # Find product PDFs
    color_pdf = None
    bw_pdf = None
    
    # Try to find PDFs with cover
    for filename in os.listdir(SAMPLES_DIR):
        if f"level{level}_color_with_cover" in filename and filename.endswith('.pdf'):
            color_pdf = os.path.join(SAMPLES_DIR, filename)
        elif f"level{level}_bw" in filename and filename.endswith('.pdf'):
            bw_pdf = os.path.join(SAMPLES_DIR, filename)
    
    # Fallback to regular PDFs
    if not color_pdf:
        for filename in os.listdir(SAMPLES_DIR):
            if f"level{level}_color.pdf" in filename:
                color_pdf = os.path.join(SAMPLES_DIR, filename)
    
    if not color_pdf:
        print(f"  ✗ Could not find color PDF for level {level}")
        return None, None
    
    # Create cover
    cover_pdf = create_cover_with_level_color(level, theme_name, product_type, PACK_CODE_BASE)
    
    # Merge for COLOR version: Cover + Product + How to Use
    print(f"  Creating COLOR version with How to Use...")
    merger_color = PdfMerger()
    merger_color.append(cover_pdf)
    merger_color.append(color_pdf)
    
    # Add How to Use
    how_to_use_pdf = os.path.join(DOCS_DIR, "How_to_Use.pdf")
    if os.path.exists(how_to_use_pdf):
        merger_color.append(how_to_use_pdf)
        print(f"  ✓ Added How to Use")
    else:
        print(f"  ✗ How to Use not found")
    
    # Save color version
    level_name = LEVELS[level]["name"]
    color_output = f"{OUTPUT_DIR}/{theme_name}_{product_type}_level{level}_{level_name}_color_complete.pdf"
    merger_color.write(color_output)
    merger_color.close()
    print(f"  ✓ Created: {os.path.basename(color_output)}")
    
    # Merge for B&W version if exists
    bw_output = None
    if bw_pdf and os.path.exists(bw_pdf):
        print(f"  Creating B&W version with How to Use...")
        merger_bw = PdfMerger()
        merger_bw.append(cover_pdf)  # Cover is color (marketing)
        merger_bw.append(bw_pdf)
        
        # Add How to Use
        if os.path.exists(how_to_use_pdf):
            merger_bw.append(how_to_use_pdf)
        
        bw_output = f"{OUTPUT_DIR}/{theme_name}_{product_type}_level{level}_{level_name}_bw_complete.pdf"
        merger_bw.write(bw_output)
        merger_bw.close()
        print(f"  ✓ Created: {os.path.basename(bw_output)}")
    
    return color_output, bw_output


def main():
    """Generate complete products for all levels"""
    print("=" * 70)
    print("COMPLETE PRODUCT GENERATOR WITH AMENDMENTS")
    print("=" * 70)
    print()
    print("AMENDMENTS:")
    print("✓ Accent strip uses LEVEL color (not teal)")
    print("✓ Title has proper padding (not touching border)")
    print("✓ How to Use merged into each level PDF")
    print("✓ Product preview with icon collage")
    print()
    print(f"Theme: {THEME.title()}")
    print(f"Product: {PRODUCT.title()}")
    print(f"Levels: {len(LEVELS)}")
    print("=" * 70)
    print()
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Process each level
    for level in sorted(LEVELS.keys()):
        print(f"Processing Level {level} - {LEVELS[level]['name']}...")
        print(f"  Accent color: {LEVELS[level]['color']}")
        
        color_pdf, bw_pdf = merge_complete_product(level, THEME, PRODUCT)
        
        if color_pdf:
            file_size = os.path.getsize(color_pdf) / (1024 * 1024)
            reader = PdfReader(color_pdf)
            pages = len(reader.pages)
            print(f"  ✓ Color PDF: {file_size:.1f} MB, {pages} pages")
        
        if bw_pdf:
            file_size = os.path.getsize(bw_pdf) / (1024 * 1024)
            reader = PdfReader(bw_pdf)
            pages = len(reader.pages)
            print(f"  ✓ B&W PDF: {file_size:.1f} MB, {pages} pages")
        
        print()
    
    print("=" * 70)
    print("✓ All levels processed!")
    print(f"✓ Output directory: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
