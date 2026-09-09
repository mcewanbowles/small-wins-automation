"""
TOKEN BOARDS GENERATOR - UPDATED DESIGN
Creates token economy boards with separate cutouts

UPDATED DESIGN:
- Token board has own Small Wins border (cut separately from tokens)
- Board includes copyright branding within border
- Token cutouts on separate section
- Multiple token options (stars, thumbs, checkmarks, etc.)

EDUCATIONAL PURPOSE:
Token economy, behavior management, completion tracking
"""

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
import io
import sys
# Ensure repo root is importable so 'utils' package resolves when running nested scripts
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from utils.sws_design import generate_teacher_cover_page, apply_small_wins_frame

PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

# Professional color palette
TITLE_BLUE = "#2B4C7E"
NAVY_BLUE = "#1E3A5F"
STEEL_BLUE = "#5B7AA0"
PURPLE = "#6B5BE2"
LIGHT_BLUE = "#EEF4FB"
GREEN = "#4CAF50"
GOLD = "#FFD700"

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def load_fonts():
    scale = DPI / 72
    fonts = {}
    try:
        fonts['title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(24 * scale))
        fonts['instruction'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(18 * scale))
        fonts['label'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(13 * scale))
        fonts['footer'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(7 * scale))
    except:
        fonts['title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(24 * scale))
        fonts['instruction'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(18 * scale))
        fonts['label'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(13 * scale))
        fonts['footer'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(7 * scale))
    return fonts


def _resolve_theme_assets(theme_slug: str | None):
    try:
        repo_root = Path(__file__).resolve().parents[3]
        slug_dir = (repo_root / 'assets' / 'themes' / theme_slug) if (isinstance(theme_slug, str) and theme_slug) else None
        header_icon_img = None
        hero_path_str = None
        book_cover_path_str = None
        if slug_dir and slug_dir.exists():
            for cand in [slug_dir / 'hero_header.png', slug_dir / 'heroes' / 'hero_header.png', slug_dir / 'characters' / 'hero_header.png', slug_dir / 'header_icon.png', slug_dir / 'hero.png']:
                if cand.exists():
                    hero_path_str = str(cand)
                    try:
                        imh = Image.open(str(cand))
                        header_icon_img = imh.convert('RGBA') if imh.mode != 'RGBA' else imh
                    except Exception:
                        header_icon_img = None
                    break
            search_dirs = [slug_dir, slug_dir / 'covers', slug_dir / 'book']
            names = ['book_cover', 'cover', 'book']
            exts = ['png', 'jpg', 'jpeg', 'webp']
            for sd in search_dirs:
                for nm in names:
                    for ex in exts:
                        fp = sd / f"{nm}.{ex}"
                        if fp.exists():
                            book_cover_path_str = str(fp)
                            break
                    if book_cover_path_str:
                        break
                if book_cover_path_str:
                    break
        return header_icon_img, hero_path_str, book_cover_path_str
    except Exception:
        return None, None, None


def draw_professional_border(draw, x, y, width, height, scale):
    """Draw Small Wins professional border"""
    border_radius = int(15 * scale)
    
    draw.rounded_rectangle(
        [x, y, x + width, y + height],
        radius=border_radius,
        outline=hex_to_rgb(GREEN),
        width=int(3 * scale)
    )
    
    # Top accent stripe
    accent_height = int(8 * scale)
    draw.rounded_rectangle(
        [x, y, x + width, y + accent_height],
        radius=border_radius,
        fill=hex_to_rgb(GREEN),
        outline=None
    )
    
    # Bottom corner accents
    corner_size = int(25 * scale)
    corner_offset = int(5 * scale)
    
    draw.arc(
        [x + corner_offset, y + height - corner_offset - corner_size, 
         x + corner_offset + corner_size, y + height - corner_offset],
        start=90, end=180,
        fill=hex_to_rgb(PURPLE),
        width=int(3 * scale)
    )
    
    draw.arc(
        [x + width - corner_offset - corner_size, y + height - corner_offset - corner_size,
         x + width - corner_offset, y + height - corner_offset],
        start=0, end=90,
        fill=hex_to_rgb(PURPLE),
        width=int(3 * scale)
    )


def draw_star(draw, center_x, center_y, size, fill_color):
    """Draw a 5-pointed star"""
    import math
    points = []
    for i in range(10):
        angle = math.pi / 2 + (2 * math.pi * i / 10)
        radius = size if i % 2 == 0 else size * 0.4
        x = center_x + radius * math.cos(angle)
        y = center_y - radius * math.sin(angle)
        points.append((x, y))
    
    draw.polygon(points, fill=fill_color, outline=hex_to_rgb(NAVY_BLUE), width=2)


def draw_thumbs_up(draw, center_x, center_y, size, fill_color):
    """Draw a simplified thumbs up"""
    # This is simplified - in production you'd use an actual icon image
    # Draw as a rounded rectangle for thumb + circle for finger
    thumb_width = int(size * 0.4)
    thumb_height = int(size * 0.7)
    
    # Thumb body
    draw.rounded_rectangle(
        [center_x - thumb_width//2, center_y - thumb_height//2,
         center_x + thumb_width//2, center_y + thumb_height//2],
        radius=int(size * 0.15),
        fill=fill_color,
        outline=hex_to_rgb(NAVY_BLUE),
        width=2
    )
    
    # Thumb tip (circle)
    tip_size = int(size * 0.3)
    draw.ellipse(
        [center_x - tip_size//2, center_y - thumb_height//2 - tip_size//2,
         center_x + tip_size//2, center_y - thumb_height//2 + tip_size//2],
        fill=fill_color,
        outline=hex_to_rgb(NAVY_BLUE),
        width=2
    )


def create_token_board_page(num_tokens, page_num, total_pages, pack_code, theme_name, header_left_icon=None):
    """Create token board page with board and cutouts"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    # SECTION 1: Token Board (will be cut out separately)
    board_margin = int(30 * scale)
    board_width = img_width - 2 * board_margin
    board_height = int(300 * scale)
    board_y = int(40 * scale)
    
    # Draw board border
    draw_professional_border(draw, board_margin, board_y, board_width, board_height, scale)
    
    # Board title
    title_y = board_y + int(25 * scale)
    title_text = f"I am all done when I have {num_tokens} tokens."
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['instruction'])
    title_w = title_bbox[2] - title_bbox[0]
    draw.text((board_margin + (board_width - title_w) // 2, title_y), title_text,
              fill=hex_to_rgb(NAVY_BLUE), font=fonts['instruction'])
    
    # Token boxes
    boxes_y = title_y + int(60 * scale)
    box_size = int(80 * scale)
    box_spacing = int(15 * scale)
    
    total_boxes_width = num_tokens * box_size + (num_tokens - 1) * box_spacing
    boxes_start_x = board_margin + (board_width - total_boxes_width) // 2
    
    for i in range(num_tokens):
        box_x = boxes_start_x + i * (box_size + box_spacing)
        
        draw.rounded_rectangle(
            [box_x, boxes_y, box_x + box_size, boxes_y + box_size],
            radius=int(8 * scale),
            fill='white',
            outline=hex_to_rgb(NAVY_BLUE),
            width=int(3 * scale)
        )
        
        # Velcro circle indicator
        circle_size = int(50 * scale)
        circle_x = box_x + (box_size - circle_size) // 2
        circle_y = boxes_y + (box_size - circle_size) // 2
        
        draw.ellipse(
            [circle_x, circle_y, circle_x + circle_size, circle_y + circle_size],
            outline=hex_to_rgb(STEEL_BLUE),
            width=int(2 * scale)
        )
    
    # Copyright on board (since it's cut separately)
    copyright_y = board_y + board_height - int(25 * scale)
    copyright_text = "© 2026 Small Wins Studio"
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_w = copyright_bbox[2] - copyright_bbox[0]
    draw.text((board_margin + (board_width - copyright_w) // 2, copyright_y), copyright_text,
              fill='#999999', font=fonts['copyright'])
    
    # CUT LINE between board and tokens
    cut_line_y = board_y + board_height + int(25 * scale)
    draw.text((board_margin, cut_line_y - int(15 * scale)), "✂️ Cut along line",
             fill=hex_to_rgb(STEEL_BLUE), font=fonts['label'])
    
    # Dashed cut line
    dash_length = int(15 * scale)
    dash_gap = int(10 * scale)
    x = board_margin
    while x < img_width - board_margin:
        draw.line([x, cut_line_y, min(x + dash_length, img_width - board_margin), cut_line_y],
                 fill='#CCCCCC', width=int(2 * scale))
        x += dash_length + dash_gap
    
    # SECTION 2: Token Cutouts
    cutouts_y = cut_line_y + int(30 * scale)
    cutouts_title_text = "Cut out tokens below. Attach hook-and-loop dots to back."
    cutouts_bbox = draw.textbbox((0, 0), cutouts_title_text, font=fonts['label'])
    cutouts_w = cutouts_bbox[2] - cutouts_bbox[0]
    draw.text(((img_width - cutouts_w) // 2, cutouts_y), cutouts_title_text,
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['label'])
    
    # Create token cutouts - stars and thumbs up
    tokens_start_y = cutouts_y + int(35 * scale)
    token_size = int(70 * scale)
    token_spacing = int(20 * scale)
    
    # Calculate grid
    tokens_per_row = num_tokens
    total_tokens_width = tokens_per_row * token_size + (tokens_per_row - 1) * token_spacing
    tokens_start_x = (img_width - total_tokens_width) // 2
    
    # Row 1: Gold stars
    for i in range(num_tokens):
        token_x = tokens_start_x + i * (token_size + token_spacing)
        
        # Token border
        draw.rounded_rectangle(
            [token_x, tokens_start_y, token_x + token_size, tokens_start_y + token_size],
            radius=int(8 * scale),
            fill='white',
            outline=hex_to_rgb(NAVY_BLUE),
            width=int(2 * scale)
        )
        
        # Star
        star_size = int(token_size * 0.35)
        draw_star(draw, token_x + token_size // 2, tokens_start_y + token_size // 2, 
                 star_size, hex_to_rgb(GOLD))
    
    # Row 2: Thumbs up
    thumbs_y = tokens_start_y + token_size + token_spacing
    for i in range(num_tokens):
        token_x = tokens_start_x + i * (token_size + token_spacing)
        
        # Token border
        draw.rounded_rectangle(
            [token_x, thumbs_y, token_x + token_size, thumbs_y + token_size],
            radius=int(8 * scale),
            fill='white',
            outline=hex_to_rgb(NAVY_BLUE),
            width=int(2 * scale)
        )
        
        # Thumbs up
        thumb_size = int(token_size * 0.4)
        draw_thumbs_up(draw, token_x + token_size // 2, thumbs_y + token_size // 2,
                      thumb_size, hex_to_rgb("#F4A460"))  # Sandy brown for skin tone
    
    # Footer and header via universal frame
    apply_small_wins_frame(
        page,
        product_title="Token Boards",
        subtitle=theme_name,
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        header_left_icon=header_left_icon,
        draw_accent_strip=True,
        draw_header=True,
        draw_subtitle=True,
        draw_footer=True,
        footer_title=f"{theme_name} | Token Boards",
    )
    
    return page


def generate_token_boards_pack(pack_code="BB0ALL", theme_name="Brown Bear"):
    """Generate token boards pack"""
    
    print(f"\n{'='*70}")
    print(f"  🎯 GENERATING TOKEN BOARDS: {pack_code}")
    print(f"  Theme: {theme_name}")
    print(f"{'='*70}\n")
    
    repo_root = Path(__file__).resolve().parents[3]
    out_dir = repo_root / "Studioforge" / "OUTPUT" / pack_code
    out_dir.mkdir(parents=True, exist_ok=True)
    
    saved_pages = []
    
    # Generate boards for different token counts
    token_counts = [3, 5, 7, 10]
    total_pages = len(token_counts) + 1
    
    # Cover page with teacher branding
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in theme_name).strip("_")
    header_icon_img, hero_path_str, book_cover_path_str = _resolve_theme_assets(slug)
    cover_page = generate_teacher_cover_page(
        theme_name=theme_name,
        pack_code=pack_code,
        product_name="Token Boards",
        page_count=len(token_counts),
        level_count=None,
        hero_image=header_icon_img,
        hero_image_path=hero_path_str,
        book_cover_path=book_cover_path_str,
        draw_footer=True,
    )
    saved_pages.append(cover_page)
    
    print(f"🎨 Generating {len(token_counts)} token boards...")
    
    for idx, num_tokens in enumerate(token_counts, 1):
        print(f"   Board {idx}: {num_tokens} tokens")
        page = create_token_board_page(num_tokens, idx + 1, total_pages, pack_code, theme_name, header_left_icon=header_icon_img)
        saved_pages.append(page)
    
    print(f"\n   ✅ {len(saved_pages)} pages generated\n")
    
    # Create PDF
    print(f"📄 Creating PDF...")
    pdf_path = str(out_dir / f"{pack_code}_TokenBoards_{len(saved_pages)}Pages.pdf")
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
    print(f"  ✨ TOKEN BOARDS COMPLETE!")
    print(f"  📦 {len(saved_pages)} pages")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python TOKEN_BOARDS.py <pack_code> [theme_name]")
        print("Example: python TOKEN_BOARDS.py BB0ALL 'Brown Bear'")
        sys.exit(1)
    
    pack_code = sys.argv[1]
    theme_name = sys.argv[2] if len(sys.argv) > 2 else "Brown Bear"
    
    success = generate_token_boards_pack(pack_code, theme_name)
    
    if not success:
        sys.exit(1)
