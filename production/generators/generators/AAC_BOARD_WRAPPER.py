"""
AAC BOARD WRAPPER - Add Small Wins Branding to Boardmaker PDFs
Takes existing Boardmaker AAC boards and adds professional branding

FEATURES:
- Adds Small Wins Studio professional border
- Adds title at top
- Adds copyright notice at bottom
- Creates both "with text" and "without text" versions
- Landscape orientation
- Professional appearance

INPUT: Brown_Bear.pdf from aac_board folder
OUTPUT: Branded AAC boards ready for TPT
"""

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
import io
from pypdf import PdfReader

PAGE_WIDTH, PAGE_HEIGHT = landscape(letter)
DPI = 300

# Professional color palette
TITLE_BLUE = "#2B4C7E"
NAVY_BLUE = "#1E3A5F"
STEEL_BLUE = "#5B7AA0"
PURPLE = "#6B5BE2"
LIGHT_BLUE = "#EEF4FB"

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def load_fonts():
    scale = DPI / 72
    fonts = {}
    try:
        fonts['title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(32 * scale))
        fonts['subtitle'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(18 * scale))
        fonts['instruction'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(16 * scale))
        fonts['footer'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(9 * scale))
    except:
        fonts['title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(32 * scale))
        fonts['subtitle'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(18 * scale))
        fonts['instruction'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(16 * scale))
        fonts['footer'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(9 * scale))
    return fonts


def draw_professional_border(draw, img_width, img_height, scale):
    """Draw Small Wins professional border"""
    border_margin = int(15 * scale)
    border_radius = int(20 * scale)
    
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, img_height - border_margin],
        radius=border_radius,
        outline=hex_to_rgb(NAVY_BLUE),
        width=int(3 * scale)
    )
    
    # Top accent stripe
    accent_height = int(10 * scale)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, border_margin + accent_height],
        radius=border_radius,
        fill=hex_to_rgb(TITLE_BLUE),
        outline=None
    )
    
    # Bottom corner accents
    corner_size = int(30 * scale)
    corner_offset = border_margin + int(5 * scale)
    
    draw.arc(
        [corner_offset, img_height - corner_offset - corner_size, 
         corner_offset + corner_size, img_height - corner_offset],
        start=90, end=180,
        fill=hex_to_rgb(PURPLE),
        width=int(4 * scale)
    )
    
    draw.arc(
        [img_width - corner_offset - corner_size, img_height - corner_offset - corner_size,
         img_width - corner_offset, img_height - corner_offset],
        start=0, end=90,
        fill=hex_to_rgb(PURPLE),
        width=int(4 * scale)
    )


def create_branded_aac_board(boardmaker_image, title, subtitle, page_num, total_pages, pack_code, theme_name):
    """Create branded AAC board page with Boardmaker content centered"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    # Draw professional border
    draw_professional_border(draw, img_width, img_height, scale)
    
    # Title area - simple and centered
    title_y = int(30 * scale)
    
    # Format: "Brown Bear - AAC Board - [Version]"
    simple_title = f"Brown Bear - AAC Board - {title}"
    
    title_bbox = draw.textbbox((0, 0), simple_title, font=fonts['title'])
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, title_y), simple_title,
              fill=hex_to_rgb(TITLE_BLUE), font=fonts['title'])
    
    # Subtitle/instruction - simple description
    subtitle_y = int(70 * scale)
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=fonts['instruction'])
    subtitle_w = subtitle_bbox[2] - subtitle_bbox[0]
    draw.text(((img_width - subtitle_w) // 2, subtitle_y), subtitle,
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['instruction'])
    
    # Place Boardmaker AAC board image - MUCH LARGER, nearly touching borders
    board_y = int(105 * scale)
    board_max_width = img_width - int(40 * scale)  # Only 20pt margin each side
    board_max_height = img_height - board_y - int(80 * scale)  # Only 80pt for footer
    
    # Resize Boardmaker image to fit - use maximum space
    bm_img = boardmaker_image.copy()
    bm_img.thumbnail((board_max_width, board_max_height), Image.Resampling.LANCZOS)
    
    # Center the board
    board_x = (img_width - bm_img.width) // 2
    board_y_positioned = board_y
    
    page.paste(bm_img, (board_x, board_y_positioned), bm_img if bm_img.mode == 'RGBA' else None)
    
    # Footer
    footer_y = img_height - int(60 * scale)
    footer_text = f"{theme_name} - {pack_code} | AAC Core Words Board | Page {page_num}/{total_pages}"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=fonts['footer'])
    footer_w = footer_bbox[2] - footer_bbox[0]
    draw.text(((img_width - footer_w) // 2, footer_y), footer_text,
              fill=hex_to_rgb(NAVY_BLUE), font=fonts['footer'])
    
    # Copyright (within border)
    copyright_y = img_height - int(35 * scale)
    copyright_text = "© 2026 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License"
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_w = copyright_bbox[2] - copyright_bbox[0]
    draw.text(((img_width - copyright_w) // 2, copyright_y), copyright_text,
              fill='#999999', font=fonts['copyright'])
    
    return page


def generate_branded_aac_boards(boardmaker_pdf_path, pack_code="BB0ALL", theme_name="Brown Bear"):
    """Generate branded AAC boards from Boardmaker PDF"""
    
    print(f"\n{'='*70}")
    print(f"  🎯 GENERATING BRANDED AAC BOARDS: {pack_code}")
    print(f"  Theme: {theme_name}")
    print(f"{'='*70}\n")
    
    pdf_path = Path(boardmaker_pdf_path)
    if not pdf_path.exists():
        print(f"❌ Error: PDF '{boardmaker_pdf_path}' not found!")
        return False
    
    # Read Boardmaker PDF
    print("📦 Loading Boardmaker PDF...")
    reader = PdfReader(pdf_path)
    
    Path("OUTPUT").mkdir(exist_ok=True)
    
    # Pages structure from the PDF:
    # Page 0: With text (white background)
    # Page 1: Without text (white background)
    # Pages 2-5: High contrast versions
    
    saved_pages = []
    
    print(f"\n🎨 Creating branded AAC boards...")
    
    # Version 1: WITH TEXT (Page 0 of Boardmaker PDF)
    print(f"   Processing: With Text Labels...")
    page = reader.pages[0]
    
    # Convert PDF page to image
    # Note: This is a simplified approach. In production, you might need PyMuPDF (fitz)
    # For now, we'll use a placeholder approach
    
    # Since we can't easily convert PDF to image in this environment,
    # let's create a note about the approach
    
    print("\n⚠️  NOTE: This generator requires the Boardmaker PDF pages as PNG images.")
    print("    Please save each page of Brown_Bear.pdf as PNG images in aac_board folder:")
    print("    - BB01.png (with text)")
    print("    - BB02.png (without text)")
    print("    - BB03.png (high contrast with text) [optional]")
    print("    - BB04.png (high contrast without text) [optional]")
    
    # For now, let's look for pre-converted images
    aac_folder = Path("aac_board")
    
    if not aac_folder.exists():
        print(f"\n❌ Folder 'aac_board' not found!")
        print(f"   Please create this folder and add the AAC board PNG images (BB01.png, BB02.png, etc.).")
        return False
    
    # Look for BB01-BB04 PNG images from Boardmaker export
    # Typical Boardmaker export order:
    # BB01.png = With text labels
    # BB02.png = Without text labels  
    # BB03.png = High contrast with text
    # BB04.png = High contrast without text
    
    bb01_img = aac_folder / "BB01.png"
    bb02_img = aac_folder / "BB02.png"
    bb03_img = aac_folder / "BB03.png"
    bb04_img = aac_folder / "BB04.png"
    
    images_to_process = [
        (bb01_img, "With Text Labels", 
         "Point, touch, or look at the symbols to communicate.", "WithText"),
        (bb02_img, "Symbols Only", 
         "Visual communication symbols without text labels.", "SymbolsOnly"),
        (bb03_img, "High Contrast - With Text", 
         "High contrast symbols with text labels.", "HighContrast_WithText"),
        (bb04_img, "High Contrast - Symbols Only", 
         "High contrast symbols without text labels.", "HighContrast_SymbolsOnly"),
    ]
    
    total_pages = len([img for img, _, _, _ in images_to_process if img.exists()])
    page_num = 1
    
    for img_path, title, subtitle, suffix in images_to_process:
        if not img_path.exists():
            print(f"   ⚠️  Skipping: {img_path.name} (not found)")
            continue
        
        print(f"   Page {page_num}: {title}")
        
        # Load Boardmaker image
        bm_img = Image.open(img_path)
        if bm_img.mode != 'RGBA':
            bm_img = bm_img.convert('RGBA')
        
        # Create branded page
        branded_page = create_branded_aac_board(
            bm_img, title, subtitle, page_num, total_pages, pack_code, theme_name
        )
        saved_pages.append((branded_page, suffix))
        page_num += 1
    
    if not saved_pages:
        print("\n❌ No images found to process!")
        return False
    
    print(f"\n   ✅ {len(saved_pages)} pages generated\n")
    
    # Create PDFs
    print(f"📄 Creating PDFs...")
    
    # Combined PDF with all versions
    combined_pdf_path = f"OUTPUT/{pack_code}_AAC_Boards_ALL.pdf"
    c = canvas.Canvas(combined_pdf_path, pagesize=landscape(letter))
    
    for page, suffix in saved_pages:
        img_buffer = io.BytesIO()
        page.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_reader = ImageReader(img_buffer)
        c.drawImage(img_reader, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    
    c.save()
    print(f"   ✅ {combined_pdf_path}")
    
    # Individual PDFs
    for page, suffix in saved_pages:
        pdf_path = f"OUTPUT/{pack_code}_AAC_Board_{suffix}.pdf"
        c = canvas.Canvas(pdf_path, pagesize=landscape(letter))
        
        img_buffer = io.BytesIO()
        page.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_reader = ImageReader(img_buffer)
        c.drawImage(img_reader, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
        c.save()
        print(f"   ✅ {pdf_path}")
    
    print(f"\n{'='*70}")
    print(f"  ✨ AAC BOARDS COMPLETE!")
    print(f"  📦 {len(saved_pages)} branded versions created")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\nUsage: python AAC_BOARD_WRAPPER.py <pack_code> [theme_name]")
        print("Example: python AAC_BOARD_WRAPPER.py BB0ALL 'Brown Bear'")
        print("\nNOTE: Requires images in 'aac_board' folder:")
        print("  - aac_board_with_text.png")
        print("  - aac_board_no_text.png")
        print("  - aac_board_with_text_highcontrast.png (optional)")
        print("  - aac_board_no_text_highcontrast.png (optional)")
        sys.exit(1)
    
    pack_code = sys.argv[1]
    theme_name = sys.argv[2] if len(sys.argv) > 2 else "Brown Bear"
    
    # Try multiple possible PDF locations
    pdf_paths = [
        "aac_board/Brown_Bear.pdf",
        "Brown_Bear.pdf",
        "../aac_board/Brown_Bear.pdf"
    ]
    
    pdf_path = None
    for path in pdf_paths:
        if Path(path).exists():
            pdf_path = path
            break
    
    if not pdf_path:
        print("\n❌ ERROR: Brown_Bear.pdf not found!")
        print("\nTried these locations:")
        for path in pdf_paths:
            print(f"  - {path}")
        print("\nPlease place Brown_Bear.pdf in one of these locations.")
        sys.exit(1)
    
    success = generate_branded_aac_boards(pdf_path, pack_code, theme_name)
    
    if not success:
        sys.exit(1)
