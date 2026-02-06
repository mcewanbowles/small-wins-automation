"""
BROWN BEAR SEQUENCING - Interactive Velcro Activity
Complete redesign for proper velcro sequencing with TPT brand colors

DESIGN:
- Title with story setup (Brown Bear + Eyes images, story text)
- 11 empty boxes in 2 rows (6 top, 5 bottom) for velcro pieces
- Separate cutout sheet with all 11 pieces
- Boxes same size as cutouts for velcro matching

LEVELS:
- Level 1: Watermark images as hints (easiest) - Orange #F4B400
- Level 2: Numbers only (medium) - Blue #4285F4
- Level 3: Text labels (hardest) - Green #34A853

OUTPUT: 4 pages (3 levels + 1 cutout sheet)
"""

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io

PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

# TPT Brand Colors - Updated to match Small Wins Studio branding
BRAND_NAVY = "#1E3A5F"  # Border and text
BRAND_TEAL = "#2AAEAE"  # Small Wins brand color
BRAND_GOLD = "#E8C547"  # Small Wins brand color

# Level Colors - Universal across all products
LEVEL_1_ORANGE = "#F4B400"  # Errorless
LEVEL_2_BLUE = "#4285F4"    # Distractors  
LEVEL_3_GREEN = "#34A853"   # Picture + Text
LEVEL_4_PURPLE = "#8C06F2"  # Generalisation (not used in sequencing)

# Supporting colors
LIGHT_BLUE = "#EEF4FB"
STEEL_BLUE = "#5B7AA0"
FOOTER_GREY = "#999999"

# Story sequence (11 characters in order)
STORY_SEQUENCE = [
    "brown_bear",    # 1
    "red_bird",      # 2
    "yellow_duck",   # 3
    "blue_horse",    # 4
    "green_frog",    # 5
    "purple_cat",    # 6
    "white_dog",     # 7
    "black_sheep",   # 8
    "goldfish",      # 9
    "teacher",       # 10
    "children"       # 11
]

DISPLAY_NAMES = {
    "brown_bear": "Brown Bear",
    "red_bird": "Red Bird",
    "yellow_duck": "Yellow Duck",
    "blue_horse": "Blue Horse",
    "green_frog": "Green Frog",
    "purple_cat": "Purple Cat",
    "white_dog": "White Dog",
    "black_sheep": "Black Sheep",
    "goldfish": "Goldfish",
    "teacher": "Teacher",
    "children": "Children"
}

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def load_fonts():
    """Load fonts with fallback for different operating systems"""
    scale = DPI / 72
    fonts = {}
    try:
        # Windows fonts
        fonts['title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(28 * scale))
        fonts['subtitle'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(18 * scale))
        fonts['prompt'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(16 * scale))
        fonts['number'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(24 * scale))
        fonts['label'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(11 * scale))
        fonts['footer'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(9 * scale))
        fonts['cutout_label'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(12 * scale))
    except (OSError, IOError):
        # Linux fonts (fallback)
        fonts['title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(28 * scale))
        fonts['subtitle'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(18 * scale))
        fonts['prompt'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(16 * scale))
        fonts['number'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(24 * scale))
        fonts['label'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(11 * scale))
        fonts['footer'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(9 * scale))
        fonts['cutout_label'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(12 * scale))
    return fonts


def make_transparent(image, opacity=0.15):
    """Make an image very transparent for watermark hints"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    alpha = image.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    image.putalpha(alpha)
    return image


def get_level_color(level):
    """Get the brand color for a specific level"""
    level_colors = {
        1: LEVEL_1_ORANGE,
        2: LEVEL_2_BLUE,
        3: LEVEL_3_GREEN
    }
    return level_colors.get(level, BRAND_NAVY)


def create_sequencing_page(loaded_images, level, pack_code, theme_name, page_num, total_pages=4):
    """Create sequencing activity page with empty boxes"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    # Border - using brand navy
    border_margin = int(15 * scale)
    border_radius = int(20 * scale)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, img_height - border_margin],
        radius=border_radius,
        outline=hex_to_rgb(BRAND_NAVY),
        width=int(3 * scale)
    )
    
    # Top accent stripe - using level color
    level_color = get_level_color(level)
    accent_height = int(8 * scale)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, border_margin + accent_height],
        radius=border_radius,
        fill=hex_to_rgb(level_color),
        outline=None
    )
    
    # Title
    title_text = f"{theme_name} - Sequencing"
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['title'])
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, int(30 * scale)), title_text,
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['title'])
    
    # Story setup section
    setup_y = int(75 * scale)
    
    # Brown Bear image (left)
    bb_img = loaded_images[0].copy()  # brown_bear
    bb_img.thumbnail((int(70 * scale), int(70 * scale)), Image.Resampling.LANCZOS)
    bb_x = int(50 * scale)
    page.paste(bb_img, (bb_x, setup_y), bb_img if bb_img.mode == 'RGBA' else None)
    
    # Eyes image (right of Brown Bear) - load from aac_images folder
    try:
        look_path = Path("aac_images") / "look.png"
        if look_path.exists():
            eyes_img = Image.open(look_path).convert('RGBA')
        else:
            # Fallback to see_look.png if look.png doesn't exist
            see_look_path = Path("aac_images") / "see_look.png"
            if see_look_path.exists():
                eyes_img = Image.open(see_look_path).convert('RGBA')
            else:
                eyes_img = loaded_images[0].copy()  # Last resort fallback
    except (FileNotFoundError, IOError):
        eyes_img = loaded_images[0].copy()  # Fallback
        
    eyes_img.thumbnail((int(70 * scale), int(70 * scale)), Image.Resampling.LANCZOS)
    eyes_x = bb_x + int(80 * scale)
    page.paste(eyes_img, (eyes_x, setup_y), eyes_img if eyes_img.mode == 'RGBA' else None)
    
    # Story text (right of images)
    text_x = eyes_x + int(90 * scale)
    text1 = "Brown Bear, Brown Bear, what do you see?"
    text1_bbox = draw.textbbox((0, 0), text1, font=fonts['prompt'])
    draw.text((text_x, setup_y + int(10 * scale)), text1,
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['prompt'])
    
    text2 = "I see..."
    draw.text((text_x, setup_y + int(45 * scale)), text2,
              fill=hex_to_rgb(BRAND_TEAL), font=fonts['subtitle'])
    
    # Level indicator
    level_names = {1: "Level 1 - Image Hints", 2: "Level 2 - Numbers Only", 3: "Level 3 - Text Only"}
    level_stars = {1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐"}
    level_text = f"{level_stars[level]} {level_names[level]}"
    level_bbox = draw.textbbox((0, 0), level_text, font=fonts['subtitle'])
    level_w = level_bbox[2] - level_bbox[0]
    draw.text(((img_width - level_w) // 2, int(165 * scale)), level_text,
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['subtitle'])
    
    # Sequencing boxes - 2 rows (6 + 5 = 11 boxes)
    box_width = int(95 * scale)
    box_height = int(120 * scale)
    box_spacing = int(10 * scale)
    
    # Row 1: 6 boxes
    row1_y = int(200 * scale)
    row1_count = 6
    row1_total_width = row1_count * box_width + (row1_count - 1) * box_spacing
    row1_start_x = (img_width - row1_total_width) // 2
    
    for i in range(row1_count):
        box_x = row1_start_x + i * (box_width + box_spacing)
        
        # Box with light blue fill
        draw.rounded_rectangle(
            [box_x, row1_y, box_x + box_width, row1_y + box_height],
            radius=int(8 * scale),
            fill=hex_to_rgb(LIGHT_BLUE),
            outline=hex_to_rgb(BRAND_NAVY),
            width=int(2 * scale)
        )
        
        # Number circle at top
        circle_size = int(30 * scale)
        circle_x = box_x + (box_width - circle_size) // 2
        circle_y = row1_y - int(15 * scale)
        draw.ellipse(
            [circle_x, circle_y, circle_x + circle_size, circle_y + circle_size],
            fill=hex_to_rgb(BRAND_NAVY)
        )
        
        num_text = str(i + 1)
        num_bbox = draw.textbbox((0, 0), num_text, font=fonts['number'])
        num_w = num_bbox[2] - num_bbox[0]
        num_h = num_bbox[3] - num_bbox[1]
        draw.text((circle_x + (circle_size - num_w) // 2, circle_y + (circle_size - num_h) // 2),
                 num_text, fill='white', font=fonts['number'])
        
        # Content based on level
        if level == 1:
            # Level 1: Watermark image hint
            hint_img = loaded_images[i].copy()
            hint_img = make_transparent(hint_img, opacity=0.15)
            hint_img.thumbnail((int(70 * scale), int(70 * scale)), Image.Resampling.LANCZOS)
            hint_x = box_x + (box_width - hint_img.width) // 2
            hint_y = row1_y + (box_height - hint_img.height) // 2
            page.paste(hint_img, (hint_x, hint_y), hint_img)
            
        elif level == 2:
            # Level 2: Just number (no hints)
            pass
            
        elif level == 3:
            # Level 3: Text label
            label_text = DISPLAY_NAMES[STORY_SEQUENCE[i]]
            label_bbox = draw.textbbox((0, 0), label_text, font=fonts['label'])
            label_w = label_bbox[2] - label_bbox[0]
            draw.text((box_x + (box_width - label_w) // 2, row1_y + box_height - int(30 * scale)),
                     label_text, fill=hex_to_rgb(BRAND_NAVY), font=fonts['label'])
    
    # Row 2: 5 boxes
    row2_y = row1_y + box_height + int(40 * scale)
    row2_count = 5
    row2_total_width = row2_count * box_width + (row2_count - 1) * box_spacing
    row2_start_x = (img_width - row2_total_width) // 2
    
    for i in range(row2_count):
        idx = row1_count + i  # Indexes 6-10
        box_x = row2_start_x + i * (box_width + box_spacing)
        
        # Box with light blue fill
        draw.rounded_rectangle(
            [box_x, row2_y, box_x + box_width, row2_y + box_height],
            radius=int(8 * scale),
            fill=hex_to_rgb(LIGHT_BLUE),
            outline=hex_to_rgb(BRAND_NAVY),
            width=int(2 * scale)
        )
        
        # Number circle at top
        circle_size = int(30 * scale)
        circle_x = box_x + (box_width - circle_size) // 2
        circle_y = row2_y - int(15 * scale)
        draw.ellipse(
            [circle_x, circle_y, circle_x + circle_size, circle_y + circle_size],
            fill=hex_to_rgb(BRAND_NAVY)
        )
        
        num_text = str(idx + 1)
        num_bbox = draw.textbbox((0, 0), num_text, font=fonts['number'])
        num_w = num_bbox[2] - num_bbox[0]
        num_h = num_bbox[3] - num_bbox[1]
        draw.text((circle_x + (circle_size - num_w) // 2, circle_y + (circle_size - num_h) // 2),
                 num_text, fill='white', font=fonts['number'])
        
        # Content based on level
        if level == 1:
            # Level 1: Watermark image hint
            hint_img = loaded_images[idx].copy()
            hint_img = make_transparent(hint_img, opacity=0.15)
            hint_img.thumbnail((int(70 * scale), int(70 * scale)), Image.Resampling.LANCZOS)
            hint_x = box_x + (box_width - hint_img.width) // 2
            hint_y = row2_y + (box_height - hint_img.height) // 2
            page.paste(hint_img, (hint_x, hint_y), hint_img)
            
        elif level == 2:
            # Level 2: Just number (no hints)
            pass
            
        elif level == 3:
            # Level 3: Text label
            label_text = DISPLAY_NAMES[STORY_SEQUENCE[idx]]
            label_bbox = draw.textbbox((0, 0), label_text, font=fonts['label'])
            label_w = label_bbox[2] - label_bbox[0]
            draw.text((box_x + (box_width - label_w) // 2, row2_y + box_height - int(30 * scale)),
                     label_text, fill=hex_to_rgb(BRAND_NAVY), font=fonts['label'])
    
    # Footer
    footer_y = img_height - int(60 * scale)
    footer_text = f"{theme_name} - {pack_code} | Sequencing (Set 1) | Page {page_num}/{total_pages}"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=fonts['footer'])
    footer_w = footer_bbox[2] - footer_bbox[0]
    draw.text(((img_width - footer_w) // 2, footer_y), footer_text,
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['footer'])
    
    # Copyright - Updated to Small Wins Studio branding
    copyright_y = img_height - int(35 * scale)
    copyright_text = "© 2025 Small Wins Studio. All rights reserved. • PCS® symbols used with active PCS Maker Personal License."
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_w = copyright_bbox[2] - copyright_bbox[0]
    draw.text(((img_width - copyright_w) // 2, copyright_y), copyright_text,
              fill=FOOTER_GREY, font=fonts['copyright'])
    
    return page


def create_cutout_page(loaded_images, pack_code, theme_name, page_num, total_pages=4):
    """Create cutout pieces page - 11 pieces same size as boxes"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    # Border - using brand navy
    border_margin = int(15 * scale)
    border_radius = int(20 * scale)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, img_height - border_margin],
        radius=border_radius,
        outline=hex_to_rgb(BRAND_NAVY),
        width=int(3 * scale)
    )
    
    # Top accent stripe - using brand teal for cutouts
    accent_height = int(8 * scale)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, border_margin + accent_height],
        radius=border_radius,
        fill=hex_to_rgb(BRAND_TEAL),
        outline=None
    )
    
    # Title
    title_text = f"{theme_name} - Sequencing Cutouts"
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['title'])
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, int(30 * scale)), title_text,
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['title'])
    
    # Instruction
    instr_text = "✂ Cut out these pieces. Use velcro to attach them to the sequencing boxes in story order."
    instr_bbox = draw.textbbox((0, 0), instr_text, font=fonts['label'])
    instr_w = instr_bbox[2] - instr_bbox[0]
    draw.text(((img_width - instr_w) // 2, int(75 * scale)), instr_text,
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['label'])
    
    # Cutout pieces - same size as boxes
    box_width = int(95 * scale)
    box_height = int(120 * scale)
    box_spacing = int(15 * scale)
    
    # Layout: 6 + 5 pieces
    # Row 1: 6 pieces
    row1_y = int(120 * scale)
    row1_count = 6
    row1_total_width = row1_count * box_width + (row1_count - 1) * box_spacing
    row1_start_x = (img_width - row1_total_width) // 2
    
    for i in range(row1_count):
        box_x = row1_start_x + i * (box_width + box_spacing)
        
        # Box with dashed border (for cutting) - using brand teal
        draw.rounded_rectangle(
            [box_x, row1_y, box_x + box_width, row1_y + box_height],
            radius=int(8 * scale),
            fill='white',
            outline=hex_to_rgb(BRAND_TEAL),
            width=int(2 * scale)
        )
        
        # Image
        char_img = loaded_images[i].copy()
        char_img.thumbnail((int(65 * scale), int(65 * scale)), Image.Resampling.LANCZOS)
        char_x = box_x + (box_width - char_img.width) // 2
        char_y = row1_y + int(15 * scale)
        page.paste(char_img, (char_x, char_y), char_img if char_img.mode == 'RGBA' else None)
        
        # Label
        label_text = DISPLAY_NAMES[STORY_SEQUENCE[i]]
        label_bbox = draw.textbbox((0, 0), label_text, font=fonts['cutout_label'])
        label_w = label_bbox[2] - label_bbox[0]
        draw.text((box_x + (box_width - label_w) // 2, row1_y + box_height - int(35 * scale)),
                 label_text, fill=hex_to_rgb(BRAND_NAVY), font=fonts['cutout_label'])
        
        # Number
        num_text = str(i + 1)
        num_bbox = draw.textbbox((0, 0), num_text, font=fonts['label'])
        num_w = num_bbox[2] - num_bbox[0]
        draw.text((box_x + (box_width - num_w) // 2, row1_y + box_height - int(20 * scale)),
                 num_text, fill='#666666', font=fonts['label'])
    
    # Row 2: 5 pieces
    row2_y = row1_y + box_height + int(25 * scale)
    row2_count = 5
    row2_total_width = row2_count * box_width + (row2_count - 1) * box_spacing
    row2_start_x = (img_width - row2_total_width) // 2
    
    for i in range(row2_count):
        idx = row1_count + i
        box_x = row2_start_x + i * (box_width + box_spacing)
        
        # Box with dashed border - using brand teal
        draw.rounded_rectangle(
            [box_x, row2_y, box_x + box_width, row2_y + box_height],
            radius=int(8 * scale),
            fill='white',
            outline=hex_to_rgb(BRAND_TEAL),
            width=int(2 * scale)
        )
        
        # Image
        char_img = loaded_images[idx].copy()
        char_img.thumbnail((int(65 * scale), int(65 * scale)), Image.Resampling.LANCZOS)
        char_x = box_x + (box_width - char_img.width) // 2
        char_y = row2_y + int(15 * scale)
        page.paste(char_img, (char_x, char_y), char_img if char_img.mode == 'RGBA' else None)
        
        # Label
        label_text = DISPLAY_NAMES[STORY_SEQUENCE[idx]]
        label_bbox = draw.textbbox((0, 0), label_text, font=fonts['cutout_label'])
        label_w = label_bbox[2] - label_bbox[0]
        draw.text((box_x + (box_width - label_w) // 2, row2_y + box_height - int(35 * scale)),
                 label_text, fill=hex_to_rgb(BRAND_NAVY), font=fonts['cutout_label'])
        
        # Number
        num_text = str(idx + 1)
        num_bbox = draw.textbbox((0, 0), num_text, font=fonts['label'])
        num_w = num_bbox[2] - num_bbox[0]
        draw.text((box_x + (box_width - num_w) // 2, row2_y + box_height - int(20 * scale)),
                 num_text, fill='#666666', font=fonts['label'])
    
    # Footer
    footer_y = img_height - int(60 * scale)
    footer_text = f"{theme_name} - {pack_code} | Sequencing (Set 1) | Page {page_num}/{total_pages}"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=fonts['footer'])
    footer_w = footer_bbox[2] - footer_bbox[0]
    draw.text(((img_width - footer_w) // 2, footer_y), footer_text,
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['footer'])
    
    # Copyright - Updated to Small Wins Studio branding
    copyright_y = img_height - int(35 * scale)
    copyright_text = "© 2025 Small Wins Studio. All rights reserved. • PCS® symbols used with active PCS Maker Personal License."
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_w = copyright_bbox[2] - copyright_bbox[0]
    draw.text(((img_width - copyright_w) // 2, copyright_y), copyright_text,
              fill=FOOTER_GREY, font=fonts['copyright'])
    
    return page


def add_storage_labels_sequencing(c, page_width, page_height):
    """Add storage labels page at end"""
    inch = 72  # points
    
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(page_width/2, page_height - 1*inch, "Storage Labels - Sequencing")
    
    # Updated to use TPT brand level colors
    labels_data = [
        ("Sequencing - Level 1", "Image Hints (Easiest)", LEVEL_1_ORANGE),
        ("Sequencing - Level 2", "Numbers Only (Medium)", LEVEL_2_BLUE),
        ("Sequencing - Level 3", "Text Only (Hardest)", LEVEL_3_GREEN)
    ]
    
    label_width = 5 * inch
    label_height = 3 * inch
    y_start = page_height - 2.5*inch
    
    for i, (title, description, color_hex) in enumerate(labels_data):
        y_pos = y_start - (i * (label_height + 0.75*inch))
        x_pos = (page_width - label_width) / 2
        
        # Background
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.roundRect(x_pos, y_pos, label_width, label_height, 10, fill=1, stroke=1)
        
        # Color header - using TPT brand level colors
        hex_color = color_hex.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
        c.setFillColorRGB(*rgb)
        c.roundRect(x_pos, y_pos + label_height - 0.9*inch, 
                   label_width, 0.9*inch, 10, fill=1, stroke=0)
        
        # Title
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(page_width/2, y_pos + label_height - 0.5*inch, title)
        
        # Description
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.setFont("Helvetica", 20)
        c.drawCentredString(page_width/2, y_pos + 0.5*inch, description)


def generate_sequencing_pack(images_folder, pack_code="BB0ALL", theme_name="Brown Bear"):
    """Generate complete sequencing pack - 3 levels + cutouts"""
    
    print(f"\n{'='*70}")
    print(f"  📊 GENERATING SEQUENCING (3 LEVELS + CUTOUTS): {pack_code}")
    print(f"  Theme: {theme_name}")
    print(f"  Updated with TPT Brand Colors - Small Wins Studio")
    print(f"{'='*70}\n")
    
    images_path = Path(images_folder)
    if not images_path.exists():
        print(f"❌ Error: Folder '{images_folder}' not found!")
        return False
    
    # Load images in story order
    loaded_images = []
    missing_images = []
    
    for char in STORY_SEQUENCE:
        img_file = images_path / f"{char}.png"
        
        if not img_file.exists():
            missing_images.append(char)
            continue
        
        img = Image.open(img_file)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        loaded_images.append(img)
    
    if missing_images:
        print(f"❌ Missing images: {', '.join(missing_images)}")
        return False
    
    if len(loaded_images) != 11:
        print(f"❌ Need exactly 11 images, found {len(loaded_images)}")
        return False
    
    output_folder = Path("OUTPUT")
    output_folder.mkdir(exist_ok=True)
    
    print(f"📝 Pack Details:")
    print(f"   Code: {pack_code}")
    print(f"   Theme: {theme_name}")
    print(f"   Story Characters: {', '.join(DISPLAY_NAMES[c] for c in STORY_SEQUENCE)}\n")
    
    print(f"📄 Creating pages...\n")
    
    saved_pages = []
    total_pages = 4
    
    # Level 1: Image hints (Orange)
    print(f"   Level 1: Image Hints (easiest) - {LEVEL_1_ORANGE}...")
    page1 = create_sequencing_page(loaded_images, 1, pack_code, theme_name, 1, total_pages)
    saved_pages.append(page1)
    
    # Level 2: Numbers only (Blue)
    print(f"   Level 2: Numbers Only (medium) - {LEVEL_2_BLUE}...")
    page2 = create_sequencing_page(loaded_images, 2, pack_code, theme_name, 2, total_pages)
    saved_pages.append(page2)
    
    # Level 3: Text labels (Green)
    print(f"   Level 3: Text Only (hardest) - {LEVEL_3_GREEN}...")
    page3 = create_sequencing_page(loaded_images, 3, pack_code, theme_name, 3, total_pages)
    saved_pages.append(page3)
    
    # Cutout pieces (Teal)
    print(f"   Cutout Pieces - {BRAND_TEAL}...")
    page4 = create_cutout_page(loaded_images, pack_code, theme_name, 4, total_pages)
    saved_pages.append(page4)
    
    print(f"\n   ✅ 4 pages generated\n")
    
    # Create PDF
    print(f"📄 Creating PDF...")
    pdf_path = f"OUTPUT/{pack_code}_Sequencing_4Pages.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    for page in saved_pages:
        img_buffer = io.BytesIO()
        page.save(img_buffer, format='PNG', dpi=(DPI, DPI))
        img_buffer.seek(0)
        c.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    
    # Add storage labels page
    add_storage_labels_sequencing(c, PAGE_WIDTH, PAGE_HEIGHT)
    c.showPage()
    
    c.save()
    print(f"   ✅ {pdf_path}\n")
    
    print(f"{'='*70}")
    print(f"  ✨ SUCCESS! Sequencing pack generated with TPT brand colors")
    print(f"  © 2025 Small Wins Studio")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python SEQUENCING.py <images_folder> [pack_code] [theme_name]")
        print("\nExample:")
        print("  python SEQUENCING.py brown_bear_images BB0ALL 'Brown Bear'")
        sys.exit(1)
    
    images_folder = sys.argv[1]
    pack_code = sys.argv[2] if len(sys.argv) > 2 else "BB0ALL"
    theme_name = sys.argv[3] if len(sys.argv) > 3 else "Brown Bear"
    
    success = generate_sequencing_pack(images_folder, pack_code, theme_name)
    sys.exit(0 if success else 1)
