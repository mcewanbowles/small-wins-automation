"""
AAC COMMUNICATION BOARD GENERATOR
Creates a visual board with core words + theme words for AAC users

NO PNG FILES NEEDED - All text-based with professional design
"""

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
import io

PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

# Professional color palette
TITLE_BLUE = "#2B4C7E"
NAVY_BLUE = "#1E3A5F"
STEEL_BLUE = "#5B7AA0"
PURPLE = "#6B5BE2"
LIGHT_BLUE = "#EEF4FB"
LIGHT_YELLOW = "#FFF9E6"

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def load_fonts():
    scale = DPI / 72
    fonts = {}
    try:
        fonts['title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(36 * scale))
        fonts['subtitle'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(18 * scale))
        fonts['word'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(20 * scale))
        fonts['label'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(10 * scale))
        fonts['footer'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(7 * scale))
    except:
        fonts['title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(36 * scale))
        fonts['subtitle'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(18 * scale))
        fonts['word'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(20 * scale))
        fonts['label'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(10 * scale))
        fonts['footer'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(7 * scale))
    return fonts


def create_aac_communication_board(theme_images, theme_names, pack_code, theme_name):
    """
    Create AAC Communication Board with:
    - Core words (20 words in text)
    - Theme words (4 animals with images)
    - Professional design
    """
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    scale = DPI / 72
    fonts = load_fonts()
    
    # Professional border
    border_margin = int(15 * scale)
    border_radius = int(20 * scale)
    border_color = "#D0D0D0"
    border_width = int(2 * scale)
    
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, img_height - border_margin],
        radius=border_radius,
        outline=hex_to_rgb(border_color),
        width=border_width
    )
    
    # Top accent stripe
    accent_height = int(8 * scale)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, border_margin + accent_height],
        radius=border_radius,
        fill=hex_to_rgb(TITLE_BLUE),
        outline=None
    )
    
    # Bottom corner accents
    corner_size = int(25 * scale)
    corner_offset = border_margin + int(5 * scale)
    
    draw.arc(
        [corner_offset, img_height - corner_offset - corner_size, 
         corner_offset + corner_size, img_height - corner_offset],
        start=90, end=180,
        fill=hex_to_rgb(PURPLE),
        width=int(3 * scale)
    )
    
    draw.arc(
        [img_width - corner_offset - corner_size, img_height - corner_offset - corner_size,
         img_width - corner_offset, img_height - corner_offset],
        start=0, end=90,
        fill=hex_to_rgb(PURPLE),
        width=int(3 * scale)
    )
    
    # Title
    title_text = f"{theme_name} - AAC Communication Board"
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['title'])
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (img_width - title_width) // 2
    title_y = int(40 * scale)
    draw.text((title_x, title_y), title_text, fill=hex_to_rgb(TITLE_BLUE), font=fonts['title'])
    
    # Section 1: Core Words
    section1_y = int(95 * scale)
    section1_text = "Core Words"
    sect_bbox = draw.textbbox((0, 0), section1_text, font=fonts['subtitle'])
    sect_w = sect_bbox[2] - sect_bbox[0]
    draw.text(((img_width - sect_w) // 2, section1_y), section1_text, 
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['subtitle'])
    
    # Core words grid - 5 columns x 4 rows = 20 words
    core_words = [
        "I", "see", "want", "like", "is",
        "big", "little", "more", "go", "stop",
        "help", "can", "get", "put", "on",
        "in", "good", "yes", "no", "the"
    ]
    
    grid_start_y = section1_y + int(40 * scale)
    grid_margin = int(60 * scale)
    box_size = int(90 * scale)
    box_spacing = int(15 * scale)
    
    cols = 5
    rows = 4
    
    total_grid_width = (cols * box_size) + ((cols - 1) * box_spacing)
    grid_start_x = (img_width - total_grid_width) // 2
    
    for idx, word in enumerate(core_words):
        row = idx // cols
        col = idx % cols
        
        box_x = grid_start_x + (col * (box_size + box_spacing))
        box_y = grid_start_y + (row * (box_size + box_spacing))
        
        # Draw word box
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_size, box_y + box_size],
            radius=int(8 * scale),
            fill=hex_to_rgb(LIGHT_BLUE),
            outline=hex_to_rgb(NAVY_BLUE),
            width=int(3 * scale)
        )
        
        # Draw word text centered
        word_bbox = draw.textbbox((0, 0), word, font=fonts['word'])
        word_w = word_bbox[2] - word_bbox[0]
        word_h = word_bbox[3] - word_bbox[1]
        word_x = box_x + (box_size - word_w) // 2
        word_y = box_y + (box_size - word_h) // 2
        draw.text((word_x, word_y), word, fill=hex_to_rgb(TITLE_BLUE), font=fonts['word'])
    
    # Section 2: Theme Words
    section2_y = grid_start_y + (rows * (box_size + box_spacing)) + int(30 * scale)
    section2_text = "Theme Animals"
    sect2_bbox = draw.textbbox((0, 0), section2_text, font=fonts['subtitle'])
    sect2_w = sect2_bbox[2] - sect2_bbox[0]
    draw.text(((img_width - sect2_w) // 2, section2_y), section2_text, 
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['subtitle'])
    
    # Theme animals - 4 boxes with images + names
    theme_start_y = section2_y + int(35 * scale)
    theme_box_size = int(100 * scale)
    theme_spacing = int(25 * scale)
    
    total_theme_width = (4 * theme_box_size) + (3 * theme_spacing)
    theme_start_x = (img_width - total_theme_width) // 2
    
    for idx, (img, name) in enumerate(zip(theme_images, theme_names)):
        box_x = theme_start_x + (idx * (theme_box_size + theme_spacing))
        box_y = theme_start_y
        
        # Draw box
        draw.rounded_rectangle(
            [box_x, box_y, box_x + theme_box_size, box_y + theme_box_size],
            radius=int(8 * scale),
            fill='white',
            outline=hex_to_rgb(PURPLE),
            width=int(3 * scale)
        )
        
        # Paste image
        img_size = int(70 * scale)
        img_copy = img.copy()
        img_copy.thumbnail((img_size, img_size), Image.Resampling.LANCZOS)
        
        img_x = box_x + (theme_box_size - img_copy.width) // 2
        img_y = box_y + int(15 * scale)
        page.paste(img_copy, (img_x, img_y), img_copy if img_copy.mode == 'RGBA' else None)
        
        # Name below image
        name_bbox = draw.textbbox((0, 0), name, font=fonts['word'])
        name_w = name_bbox[2] - name_bbox[0]
        name_x = box_x + (theme_box_size - name_w) // 2
        name_y = box_y + int(85 * scale)
        draw.text((name_x, name_y), name, fill=hex_to_rgb(NAVY_BLUE), font=fonts['word'])
    
    # Footer
    footer_text = f"{theme_name} - {pack_code} | AAC Communication Board | Page 1/1"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=fonts['footer'])
    footer_width = footer_bbox[2] - footer_bbox[0]
    footer_x = (img_width - footer_width) // 2
    footer_y = img_height - int(85 * scale)
    draw.text((footer_x, footer_y), footer_text, fill=hex_to_rgb(NAVY_BLUE), font=fonts['footer'])
    
    # Copyright
    copyright_text = "© 2026 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License"
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_width = copyright_bbox[2] - copyright_bbox[0]
    copyright_x = (img_width - copyright_width) // 2
    copyright_y = img_height - int(35 * scale)
    draw.text((copyright_x, copyright_y), copyright_text, fill='#999999', font=fonts['copyright'])
    
    return page


def generate_aac_board(images_folder, pack_code="BB01", theme_name="Brown Bear"):
    """Generate AAC Communication Board"""
    
    print(f"\n{'='*70}")
    print(f"  📱 GENERATING AAC COMMUNICATION BOARD: {pack_code}")
    print(f"  Theme: {theme_name}")
    print(f"{'='*70}\n")
    
    # Load theme images
    images_path = Path(images_folder)
    if not images_path.exists():
        print(f"❌ Error: Folder '{images_folder}' not found!")
        return False
    
    image_files = sorted(images_path.glob("*.png"))
    if len(image_files) < 4:
        print(f"❌ Error: Need at least 4 images! Found {len(image_files)}")
        return False
    
    print(f"   Loading {len(image_files)} theme images...")
    theme_images = []
    theme_names = []
    
    for f in image_files[:4]:
        img = Image.open(f).convert('RGBA')
        theme_images.append(img)
        name = f.stem.replace('_', ' ').replace('-', ' ').title()
        theme_names.append(name)
        print(f"   ✅ {name}")
    
    Path("OUTPUT").mkdir(exist_ok=True)
    
    print(f"   Creating AAC Communication Board...")
    page = create_aac_board(theme_images, theme_names, pack_code, theme_name)
    
    # Save PDF
    pdf_path = f"OUTPUT/{pack_code}_AAC_Board.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    buf = io.BytesIO()
    page.save(buf, format='PNG', dpi=(DPI, DPI))
    buf.seek(0)
    c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
    c.save()
    print(f"   ✅ {pdf_path}")
    
    # Thumbnail
    Path("OUTPUT/thumbnails").mkdir(exist_ok=True)
    thumb = page.copy()
    thumb.thumbnail((500, 647), Image.Resampling.LANCZOS)
    thumb_path = f"OUTPUT/thumbnails/{pack_code}_AAC_Board_thumb.png"
    thumb.save(thumb_path, "PNG")
    print(f"   ✅ Thumbnail created")
    
    print(f"\n{'='*70}")
    print(f"  ✅ AAC COMMUNICATION BOARD COMPLETE!")
    print(f"{'='*70}\n")
    return True


if __name__ == "__main__":
    import sys
    pack_code = sys.argv[1] if len(sys.argv) > 1 else "BB01"
    theme_name = sys.argv[2] if len(sys.argv) > 2 else "Brown Bear"
    generate_aac_board("images", pack_code, theme_name)
