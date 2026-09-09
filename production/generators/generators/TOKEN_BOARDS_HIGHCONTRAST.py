"""
TOKEN BOARDS & VISUAL SCHEDULES GENERATOR - BROWN BEAR
Creates behavior support materials with story character themes

PRODUCT STRUCTURE:
- 3, 5, 8, and 10-token boards
- First/Then boards
- Working For displays
- Multiple sizes (full page, half page, portable)

EDUCATIONAL PURPOSE:
Supports positive behavior, visual schedules, and reinforcement systems
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
TITLE_BLUE = "#FFFFFF"
NAVY_BLUE = "#FFFFFF"
STEEL_BLUE = "#FFFFFF"
PURPLE = "#FF6BE2"
LIGHT_BLUE = "#EEF4FB"
LIGHT_GREEN = "#E8F5E9"

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def load_fonts():
    scale = DPI / 72
    fonts = {}
    try:
        fonts['title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(36 * scale))
        fonts['large'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(28 * scale))
        fonts['medium'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(20 * scale))
        fonts['instruction'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(14 * scale))
        fonts['footer'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(7 * scale))
    except:
        fonts['title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(36 * scale))
        fonts['large'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(28 * scale))
        fonts['medium'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(20 * scale))
        fonts['instruction'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(14 * scale))
        fonts['footer'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(7 * scale))
    return fonts


def draw_professional_border(draw, img_width, img_height, scale):
    """Draw Small Wins professional border"""
    border_margin = int(15 * scale)
    border_radius = int(20 * scale)
    
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, img_height - border_margin],
        radius=border_radius,
        outline='#FFFFFF',
        width=int(2 * scale)
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


def create_token_board(num_tokens, character_images, page_num, total_pages, pack_code, theme_name):
    """Create a token board page"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'black')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    draw_professional_border(draw, img_width, img_height, scale)
    
    # Title
    title_text = f"{theme_name} - {num_tokens} Token Board"
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['title'])
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, int(40 * scale)), title_text,
              fill=hex_to_rgb(TITLE_BLUE), font=fonts['title'])
    
    # "I can do it!" motivational text
    motivation_text = "I can do it!"
    motivation_bbox = draw.textbbox((0, 0), motivation_text, font=fonts['large'])
    motivation_w = motivation_bbox[2] - motivation_bbox[0]
    draw.text(((img_width - motivation_w) // 2, int(95 * scale)), motivation_text,
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['large'])
    
    # Token circles
    tokens_start_y = int(160 * scale)
    token_size = int(110 * scale)
    token_spacing = int(25 * scale)
    
    # Calculate layout
    if num_tokens <= 5:
        cols = num_tokens
        rows = 1
    elif num_tokens <= 8:
        cols = 4
        rows = 2
    else:  # 10 tokens
        cols = 5
        rows = 2
    
    total_width = cols * token_size + (cols - 1) * token_spacing
    start_x = (img_width - total_width) // 2
    
    token_idx = 0
    for row in range(rows):
        for col in range(cols):
            if token_idx >= num_tokens:
                break
            
            token_x = start_x + col * (token_size + token_spacing)
            token_y = tokens_start_y + row * (token_size + token_spacing + int(20 * scale))
            
            # Token circle with velcro indicator
            draw.ellipse(
                [token_x, token_y, token_x + token_size, token_y + token_size],
                fill=hex_to_rgb(LIGHT_GREEN),
                outline=hex_to_rgb(PURPLE),
                width=int(4 * scale)
            )
            
            # Inner circle for velcro placement
            inner_margin = int(8 * scale)
            draw.ellipse(
                [token_x + inner_margin, token_y + inner_margin,
                 token_x + token_size - inner_margin, token_y + token_size - inner_margin],
                outline=hex_to_rgb(PURPLE),
                width=int(2 * scale)
            )
            
            # Token number
            token_num = str(token_idx + 1)
            num_bbox = draw.textbbox((0, 0), token_num, font=fonts['medium'])
            num_w = num_bbox[2] - num_bbox[0]
            num_h = num_bbox[3] - num_bbox[1]
            draw.text((token_x + (token_size - num_w) // 2,
                      token_y + (token_size - num_h) // 2),
                     token_num, fill=hex_to_rgb(NAVY_BLUE), font=fonts['medium'])
            
            # Paste character image if available
            if token_idx < len(character_images):
                img = character_images[token_idx % len(character_images)].copy()
                img_size = int(60 * scale)
                img.thumbnail((img_size, img_size), Image.Resampling.LANCZOS)
                img_x = token_x + (token_size - img.width) // 2
                img_y = token_y + (token_size - img.height) // 2 + int(20 * scale)
                page.paste(img, (img_x, img_y), img if img.mode == 'RGBA' else None)
            
            token_idx += 1
    
    # "Working For" section at bottom
    working_for_y = img_height - int(250 * scale)
    
    # Working For box
    box_width = int(400 * scale)
    box_height = int(140 * scale)
    box_x = (img_width - box_width) // 2
    
    draw.rounded_rectangle(
        [box_x, working_for_y, box_x + box_width, working_for_y + box_height],
        radius=int(10 * scale),
        fill=hex_to_rgb(LIGHT_BLUE),
        outline=hex_to_rgb(NAVY_BLUE),
        width=int(3 * scale)
    )
    
    # "Working For:" label
    label_text = "Working For:"
    label_bbox = draw.textbbox((0, 0), label_text, font=fonts['medium'])
    label_w = label_bbox[2] - label_bbox[0]
    draw.text((box_x + (box_width - label_w) // 2, working_for_y + int(15 * scale)),
              label_text, fill=hex_to_rgb(NAVY_BLUE), font=fonts['medium'])
    
    # Velcro placement area
    velcro_size = int(90 * scale)
    velcro_x = box_x + (box_width - velcro_size) // 2
    velcro_y = working_for_y + int(60 * scale)
    
    draw.rectangle(
        [velcro_x, velcro_y, velcro_x + velcro_size, velcro_y + velcro_size],
        outline=hex_to_rgb(PURPLE),
        width=int(3 * scale)
    )
    
    # Footer
    footer_y = img_height - int(70 * scale)
    footer_text = f"{theme_name} - {pack_code} | Token Board ({num_tokens} tokens) | Page {page_num}/{total_pages}"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=fonts['footer'])
    footer_w = footer_bbox[2] - footer_bbox[0]
    draw.text(((img_width - footer_w) // 2, footer_y), footer_text,
              fill=hex_to_rgb(NAVY_BLUE), font=fonts['footer'])
    
    # Copyright
    copyright_y = img_height - int(40 * scale)
    copyright_text = "© 2026 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License"
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_w = copyright_bbox[2] - copyright_bbox[0]
    draw.text(((img_width - copyright_w) // 2, copyright_y), copyright_text,
              fill='#999999', font=fonts['copyright'])
    
    return page


def create_first_then_board(page_num, total_pages, pack_code, theme_name):
    """Create First/Then visual schedule board"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'black')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    draw_professional_border(draw, img_width, img_height, scale)
    
    # Title
    title_text = f"{theme_name} - First/Then Board"
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['title'])
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, int(40 * scale)), title_text,
              fill=hex_to_rgb(TITLE_BLUE), font=fonts['title'])
    
    # Two columns: FIRST and THEN
    board_y = int(120 * scale)
    column_width = int(280 * scale)
    column_height = int(420 * scale)
    column_spacing = int(60 * scale)
    
    total_width = 2 * column_width + column_spacing
    start_x = (img_width - total_width) // 2
    
    # FIRST column (left)
    first_x = start_x
    
    draw.rounded_rectangle(
        [first_x, board_y, first_x + column_width, board_y + column_height],
        radius=int(15 * scale),
        fill='white',
        outline=hex_to_rgb(NAVY_BLUE),
        width=int(4 * scale)
    )
    
    # FIRST header
    first_header_height = int(60 * scale)
    draw.rounded_rectangle(
        [first_x, board_y, first_x + column_width, board_y + first_header_height],
        radius=int(15 * scale),
        fill=hex_to_rgb(TITLE_BLUE),
        outline=None
    )
    
    first_text = "FIRST"
    first_bbox = draw.textbbox((0, 0), first_text, font=fonts['large'])
    first_w = first_bbox[2] - first_bbox[0]
    first_h = first_bbox[3] - first_bbox[1]
    draw.text((first_x + (column_width - first_w) // 2,
              board_y + (first_header_height - first_h) // 2),
             first_text, fill='white', font=fonts['large'])
    
    # FIRST velcro area
    velcro_margin = int(30 * scale)
    velcro_y = board_y + first_header_height + velcro_margin
    velcro_height = column_height - first_header_height - 2 * velcro_margin
    
    draw.rectangle(
        [first_x + velcro_margin, velcro_y,
         first_x + column_width - velcro_margin, velcro_y + velcro_height],
        outline=hex_to_rgb(PURPLE),
        width=int(3 * scale)
    )
    
    # THEN column (right)
    then_x = start_x + column_width + column_spacing
    
    draw.rounded_rectangle(
        [then_x, board_y, then_x + column_width, board_y + column_height],
        radius=int(15 * scale),
        fill='white',
        outline=hex_to_rgb(NAVY_BLUE),
        width=int(4 * scale)
    )
    
    # THEN header
    draw.rounded_rectangle(
        [then_x, board_y, then_x + column_width, board_y + first_header_height],
        radius=int(15 * scale),
        fill=hex_to_rgb(PURPLE),
        outline=None
    )
    
    then_text = "THEN"
    then_bbox = draw.textbbox((0, 0), then_text, font=fonts['large'])
    then_w = then_bbox[2] - then_bbox[0]
    draw.text((then_x + (column_width - then_w) // 2,
              board_y + (first_header_height - first_h) // 2),
             then_text, fill='white', font=fonts['large'])
    
    # THEN velcro area
    draw.rectangle(
        [then_x + velcro_margin, velcro_y,
         then_x + column_width - velcro_margin, velcro_y + velcro_height],
        outline=hex_to_rgb(PURPLE),
        width=int(3 * scale)
    )
    
    # Footer
    footer_y = img_height - int(70 * scale)
    footer_text = f"{theme_name} - {pack_code} | First/Then Board | Page {page_num}/{total_pages}"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=fonts['footer'])
    footer_w = footer_bbox[2] - footer_bbox[0]
    draw.text(((img_width - footer_w) // 2, footer_y), footer_text,
              fill=hex_to_rgb(NAVY_BLUE), font=fonts['footer'])
    
    # Copyright
    copyright_y = img_height - int(40 * scale)
    copyright_text = "© 2026 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License"
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_w = copyright_bbox[2] - copyright_bbox[0]
    draw.text(((img_width - copyright_w) // 2, copyright_y), copyright_text,
              fill='#999999', font=fonts['copyright'])
    
    return page


def generate_token_boards_pack(images_folder, pack_code="BB01", theme_name="Brown Bear"):
    """Generate token boards and visual schedules pack"""
    
    print(f"\n{'='*70}")
    print(f"  🎯 GENERATING TOKEN BOARDS PACK: {pack_code}")
    print(f"  Theme: {theme_name}")
    print(f"{'='*70}\n")
    
    images_path = Path(images_folder)
    if not images_path.exists():
        print(f"❌ Error: Folder '{images_folder}' not found!")
        return False
    
    image_files = sorted(images_path.glob("*.png"))
    if len(image_files) < 4:
        print(f"❌ Error: Need at least 4 images. Found {len(image_files)}")
        return False
    
    # Load images
    print("📦 Loading images...")
    loaded_images = []
    
    for img_path in image_files[:4]:
        img = Image.open(img_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        loaded_images.append(img)
        print(f"   ✅ {img_path.name}")
    
    Path("OUTPUT").mkdir(exist_ok=True)
    
    saved_pages = []
    page_num = 1
    
    print(f"\n🎨 Generating token boards...")
    
    # Generate token boards
    for num_tokens in [3, 5, 8, 10]:
        print(f"   {num_tokens}-token board...")
        page = create_token_board(num_tokens, loaded_images, page_num, 6, pack_code, theme_name)
        saved_pages.append(page)
        page_num += 1
    
    # Generate First/Then boards
    print(f"   First/Then board...")
    page = create_first_then_board(page_num, 6, pack_code, theme_name)
    saved_pages.append(page)
    page_num += 1
    
    # Generate another First/Then variant
    print(f"   First/Then board (variant)...")
    page = create_first_then_board(page_num, 6, pack_code, theme_name)
    saved_pages.append(page)
    
    print(f"\n   ✅ {len(saved_pages)} pages generated\n")
    
    # Create PDF
    print(f"📄 Creating PDF...")
    pdf_path = f"OUTPUT/{pack_code}_TokenBoards_{len(saved_pages)}Pages.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    for page in saved_pages:
        img_buffer = io.BytesIO()
        page.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_reader = ImageReader(img_buffer)
        c.drawImage(img_reader, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    
    c.save()
    
    print(f"✅ PDF created: {pdf_path}")
    print(f"\n{'='*70}")
    print(f"  ✨ TOKEN BOARDS PACK COMPLETE!")
    print(f"  📦 {len(saved_pages)} pages")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python TOKEN_BOARDS.py <pack_code> [theme_name]")
        print("Example: python TOKEN_BOARDS.py BB01 'Brown Bear'")
        sys.exit(1)
    
    pack_code = sys.argv[1]
    theme_name = sys.argv[2] if len(sys.argv) > 2 else "Brown Bear"
    
    success = generate_token_boards_pack("images", pack_code, theme_name)
    
    if not success:
        sys.exit(1)
