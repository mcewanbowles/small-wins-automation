"""
BEGINNING-MIDDLE-END STORY MAPS GENERATOR - BROWN BEAR
Creates narrative structure visual organizers

PRODUCT STRUCTURE:
- Story map worksheets (3 difficulty levels)
- Sequencing strips with transition words
- Retelling prompt cards
- Visual scaffolding for narrative comprehension

EDUCATIONAL PURPOSE:
Builds narrative comprehension, story structure understanding, and retelling skills
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
PURPLE = "#6B5BE2"
LIGHT_BLUE = "#EEF4FB"
LIGHT_GREEN = "#E8F5E9"
LIGHT_YELLOW = "#FFF9E6"

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def load_fonts():
    scale = DPI / 72
    fonts = {}
    try:
        fonts['title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(32 * scale))
        fonts['section'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(24 * scale))
        fonts['label'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(16 * scale))
        fonts['text'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(14 * scale))
        fonts['footer'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(7 * scale))
    except:
        fonts['title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(32 * scale))
        fonts['section'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(24 * scale))
        fonts['label'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(16 * scale))
        fonts['text'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(14 * scale))
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


def create_full_story_timeline(images, image_names, page_num, total_pages, pack_code, theme_name):
    """Create a full story timeline with ALL animals in sequence"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'black')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    draw_professional_border(draw, img_width, img_height, scale)
    
    # Title
    title_text = f"{theme_name} - Complete Story Sequence"
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['title'])
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, int(35 * scale)), title_text,
              fill=hex_to_rgb(TITLE_BLUE), font=fonts['title'])
    
    # Instruction
    instr_text = "The Brown Bear story in order:"
    instr_bbox = draw.textbbox((0, 0), instr_text, font=fonts['label'])
    instr_w = instr_bbox[2] - instr_bbox[0]
    draw.text(((img_width - instr_w) // 2, int(75 * scale)), instr_text,
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['label'])
    
    # Layout: 4 columns × 3 rows = 12 animals
    cols = 4
    rows = (len(images) + cols - 1) // cols
    
    box_width = int(130 * scale)
    box_height = int(150 * scale)
    h_spacing = int(15 * scale)
    v_spacing = int(15 * scale)
    
    grid_width = cols * box_width + (cols - 1) * h_spacing
    grid_height = rows * box_height + (rows - 1) * v_spacing
    
    start_x = (img_width - grid_width) // 2
    start_y = int(120 * scale)
    
    # Draw each animal in sequence
    for idx, (img, name) in enumerate(zip(images, image_names)):
        col = idx % cols
        row = idx // cols
        
        box_x = start_x + col * (box_width + h_spacing)
        box_y = start_y + row * (box_height + v_spacing)
        
        # Sequence number circle
        num_radius = int(18 * scale)
        num_x = box_x + num_radius + int(10 * scale)
        num_y = box_y + num_radius + int(5 * scale)
        
        draw.ellipse(
            [num_x - num_radius, num_y - num_radius,
             num_x + num_radius, num_y + num_radius],
            fill=hex_to_rgb(TITLE_BLUE),
            outline=hex_to_rgb(NAVY_BLUE),
            width=2
        )
        
        num_text = str(idx + 1)
        num_bbox = draw.textbbox((0, 0), num_text, font=fonts['label'])
        num_w = num_bbox[2] - num_bbox[0]
        num_h = num_bbox[3] - num_bbox[1]
        draw.text((num_x - num_w // 2, num_y - num_h // 2 - int(2 * scale)),
                 num_text, fill='white', font=fonts['label'])
        
        # Image box
        img_box_size = int(100 * scale)
        img_box_x = box_x + (box_width - img_box_size) // 2
        img_box_y = box_y + int(35 * scale)
        
        draw.rounded_rectangle(
            [img_box_x, img_box_y, img_box_x + img_box_size, img_box_y + img_box_size],
            radius=int(8 * scale),
            fill=hex_to_rgb(LIGHT_BLUE),
            outline=hex_to_rgb(NAVY_BLUE),
            width=int(2 * scale)
        )
        
        # Paste image at MAXIMUM size within box
        img_copy = img.copy()
        max_img_size = int(90 * scale)  # MAXIMUM size
        img_copy.thumbnail((max_img_size, max_img_size), Image.Resampling.LANCZOS)
        paste_x = img_box_x + (img_box_size - img_copy.width) // 2
        paste_y = img_box_y + (img_box_size - img_copy.height) // 2
        page.paste(img_copy, (paste_x, paste_y), img_copy if img_copy.mode == 'RGBA' else None)
        
        # Name label
        label_y = img_box_y + img_box_size + int(5 * scale)
        label_bbox = draw.textbbox((0, 0), name, font=fonts['text'])
        label_w = label_bbox[2] - label_bbox[0]
        draw.text((box_x + (box_width - label_w) // 2, label_y),
                 name, fill=hex_to_rgb(NAVY_BLUE), font=fonts['text'])
        
        # Arrow to next (if not last in row)
        if col < cols - 1 and idx < len(images) - 1:
            arrow_x = box_x + box_width + int(3 * scale)
            arrow_y = img_box_y + img_box_size // 2
            arrow_end_x = arrow_x + h_spacing - int(6 * scale)
            
            draw.line([arrow_x, arrow_y, arrow_end_x, arrow_y],
                     fill=hex_to_rgb(PURPLE), width=int(3 * scale))
            # Arrowhead
            draw.polygon([
                (arrow_end_x, arrow_y),
                (arrow_end_x - int(8 * scale), arrow_y - int(6 * scale)),
                (arrow_end_x - int(8 * scale), arrow_y + int(6 * scale))
            ], fill=hex_to_rgb(PURPLE))
    
    # Footer
    footer_y = img_height - int(70 * scale)
    footer_text = f"{theme_name} - {pack_code} | Story Timeline | Page {page_num}/{total_pages}"
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


def create_story_map_page(level, images, page_num, total_pages, pack_code, theme_name):
    """Create a beginning-middle-end story map"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'black')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    draw_professional_border(draw, img_width, img_height, scale)
    
    # Title
    title_text = f"{theme_name} - Story Map"
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['title'])
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, int(35 * scale)), title_text,
              fill=hex_to_rgb(TITLE_BLUE), font=fonts['title'])
    
    # Level indicator
    level_text = f"Level {level}"
    level_bbox = draw.textbbox((0, 0), level_text, font=fonts['label'])
    level_w = level_bbox[2] - level_bbox[0]
    draw.text(((img_width - level_w) // 2, int(75 * scale)), level_text,
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['label'])
    
    # Three sections: Beginning, Middle, End
    section_width = int(480 * scale)
    section_height = int(160 * scale)
    section_x = (img_width - section_width) // 2
    
    sections = [
        {'name': 'BEGINNING', 'y': int(120 * scale), 'color': LIGHT_GREEN, 'prompt': 'First, I see:'},
        {'name': 'MIDDLE', 'y': int(310 * scale), 'color': LIGHT_YELLOW, 'prompt': 'Then, I see:'},
        {'name': 'END', 'y': int(500 * scale), 'color': LIGHT_BLUE, 'prompt': 'Last, I see:'}
    ]
    
    for idx, section in enumerate(sections):
        section_y = section['y']
        
        # Section box
        draw.rounded_rectangle(
            [section_x, section_y, section_x + section_width, section_y + section_height],
            radius=int(10 * scale),
            fill=hex_to_rgb(section['color']),
            outline=hex_to_rgb(NAVY_BLUE),
            width=int(3 * scale)
        )
        
        # Section header
        header_height = int(40 * scale)
        draw.rounded_rectangle(
            [section_x, section_y, section_x + section_width, section_y + header_height],
            radius=int(10 * scale),
            fill=hex_to_rgb(TITLE_BLUE),
            outline=None
        )
        
        # Section name
        name_bbox = draw.textbbox((0, 0), section['name'], font=fonts['section'])
        name_w = name_bbox[2] - name_bbox[0]
        name_h = name_bbox[3] - name_bbox[1]
        draw.text((section_x + (section_width - name_w) // 2,
                  section_y + (header_height - name_h) // 2),
                 section['name'], fill='white', font=fonts['section'])
        
        if level == 1:
            # Level 1: Image velcro area only
            img_area_size = int(100 * scale)
            img_x = section_x + (section_width - img_area_size) // 2
            img_y = section_y + header_height + int(15 * scale)
            
            draw.rectangle(
                [img_x, img_y, img_x + img_area_size, img_y + img_area_size],
                outline=hex_to_rgb(PURPLE),
                width=int(3 * scale)
            )
            
            # Paste sample image at MAXIMUM size
            if idx < len(images):
                img = images[idx].copy()
                img.thumbnail((int(95 * scale), int(95 * scale)), Image.Resampling.LANCZOS)  # MAXIMUM (was 80)
                paste_x = img_x + (img_area_size - img.width) // 2
                paste_y = img_y + (img_area_size - img.height) // 2
                page.paste(img, (paste_x, paste_y), img if img.mode == 'RGBA' else None)
        
        elif level == 2:
            # Level 2: Image + sentence frame
            # Prompt text
            prompt_y = section_y + header_height + int(12 * scale)
            draw.text((section_x + int(20 * scale), prompt_y), section['prompt'],
                     fill=hex_to_rgb(NAVY_BLUE), font=fonts['label'])
            
            # Writing lines
            line_y = prompt_y + int(30 * scale)
            line_spacing = int(25 * scale)
            for i in range(2):
                y = line_y + i * line_spacing
                draw.line([section_x + int(20 * scale), y,
                          section_x + section_width - int(20 * scale), y],
                         fill=hex_to_rgb(STEEL_BLUE), width=2)
        
        else:  # Level 3
            # Level 3: Full writing space
            prompt_y = section_y + header_height + int(12 * scale)
            draw.text((section_x + int(20 * scale), prompt_y), "I can write:",
                     fill=hex_to_rgb(NAVY_BLUE), font=fonts['label'])
            
            # Writing lines
            line_y = prompt_y + int(30 * scale)
            line_spacing = int(22 * scale)
            for i in range(3):
                y = line_y + i * line_spacing
                draw.line([section_x + int(20 * scale), y,
                          section_x + section_width - int(20 * scale), y],
                         fill=hex_to_rgb(STEEL_BLUE), width=2)
        
        # Arrow to next section (except for last)
        if idx < 2:
            arrow_x = img_width // 2
            arrow_y = section_y + section_height + int(12 * scale)
            arrow_size = int(20 * scale)
            
            # Draw arrow pointing down
            arrow_points = [
                (arrow_x, arrow_y + arrow_size),
                (arrow_x - arrow_size // 2, arrow_y),
                (arrow_x + arrow_size // 2, arrow_y)
            ]
            draw.polygon(arrow_points, fill=hex_to_rgb(PURPLE))
    
    # Footer
    footer_y = img_height - int(70 * scale)
    footer_text = f"{theme_name} - {pack_code} | Story Map Level {level} | Page {page_num}/{total_pages}"
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


def generate_story_maps_pack(images_folder, pack_code="BB01", theme_name="Brown Bear"):
    """Generate beginning-middle-end story maps pack"""
    
    print(f"\n{'='*70}")
    print(f"  🎯 GENERATING STORY MAPS PACK: {pack_code}")
    print(f"  Theme: {theme_name}")
    print(f"{'='*70}\n")
    
    images_path = Path(images_folder)
    if not images_path.exists():
        print(f"❌ Error: Folder '{images_folder}' not found!")
        return False
    
    image_files = sorted(images_path.glob("*.png"))
    if len(image_files) < 3:
        print(f"❌ Error: Need at least 3 images. Found {len(image_files)}")
        return False
    
    # Load ALL images for complete story sequence
    print("📦 Loading images...")
    loaded_images = []
    image_names = []
    
    for img_path in image_files:
        # Skip see.png if it exists
        if 'see.png' in str(img_path).lower() and 'sheep' not in str(img_path).lower():
            img = Image.open(img_path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            loaded_images.append(img)
            image_names.append("Eyes")
            print(f"   ✅ {img_path.name} → Eyes")
            continue
            
        img = Image.open(img_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        loaded_images.append(img)
        name = img_path.stem.replace('_', ' ').replace('-', ' ').title()
        image_names.append(name)
        print(f"   ✅ {img_path.name} → {name}")
    
    print(f"\n📚 Complete story: {len(loaded_images)} characters loaded")
    
    Path("OUTPUT").mkdir(exist_ok=True)
    
    saved_pages = []
    page_num = 1
    total_pages = 4  # Timeline + 3 levels of story maps
    
    print(f"\n🎨 Generating story maps...")
    
    # Page 1: Full story timeline with ALL animals
    print(f"   Creating complete story timeline...")
    timeline_page = create_full_story_timeline(loaded_images, image_names, page_num, total_pages, pack_code, theme_name)
    saved_pages.append(timeline_page)
    page_num += 1
    
    # Pages 2-4: Three levels of story maps (Beginning/Middle/End)
    for level in [1, 2, 3]:
        print(f"   Level {level} story map...")
        page = create_story_map_page(level, loaded_images[:3], page_num, total_pages, pack_code, theme_name)
        saved_pages.append(page)
        page_num += 1
    
    print(f"\n   ✅ {len(saved_pages)} pages generated\n")
    
    # Create PDF
    print(f"📄 Creating PDF...")
    pdf_path = f"OUTPUT/{pack_code}_StoryMaps_{len(saved_pages)}Pages.pdf"
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
    print(f"  ✨ STORY MAPS PACK COMPLETE!")
    print(f"  📦 {len(saved_pages)} pages")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python STORY_MAPS.py <pack_code> [theme_name]")
        print("Example: python STORY_MAPS.py BB01 'Brown Bear'")
        sys.exit(1)
    
    pack_code = sys.argv[1]
    theme_name = sys.argv[2] if len(sys.argv) > 2 else "Brown Bear"
    
    success = generate_story_maps_pack("images", pack_code, theme_name)
    
    if not success:
        sys.exit(1)
