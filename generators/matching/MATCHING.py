"""
BROWN BEAR MATCHING - Interactive Velcro Activity
Complete implementation with TPT brand colors and Small Wins Studio branding

DESIGN:
- 5 rows × 2 columns layout (matching boxes + velcro boxes)
- Target box at top showing reference image
- Matching boxes (left) and velcro boxes (right)
- Professional branding aligned with Design Constitution

LEVELS:
- Level 1 (Orange #F4B400): Errorless - 5 targets, 0 distractors, watermark hints
- Level 2 (Blue #4285F4): Easy - 4 targets, 1 distractor
- Level 3 (Green #34A853): Medium - 3 targets, 2 distractors  
- Level 4 (Purple #8C06F2): Hard - 1 target, 4 distractors

OUTPUT: 4 levels (color + BW) + cutout page + storage labels
"""

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
import random

PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

# TPT Brand Colors - Small Wins Studio branding
BRAND_NAVY = "#1E3A5F"  # Border and text
BRAND_TEAL = "#2AAEAE"  # Small Wins brand color
BRAND_GOLD = "#E8C547"  # Small Wins brand color

# Level Colors - Universal across all products
LEVEL_1_ORANGE = "#F4B400"  # Errorless
LEVEL_2_BLUE = "#4285F4"    # Distractors  
LEVEL_3_GREEN = "#34A853"   # Picture + Text
LEVEL_4_PURPLE = "#8C06F2"  # Generalisation

# Supporting colors
LIGHT_GREY = "#E8E8E8"      # Velcro box fill
VELCRO_FILL = "#CCCCCC"     # Velcro dot fill
VELCRO_OUTLINE = "#999999"  # Velcro dot outline
PURPLE_BORDER = "#6B5BE2"   # Velcro box border
FOOTER_GREY = "#999999"

# Brown Bear theme icons (12 core icons)
BROWN_BEAR_ICONS = [
    "brown_bear", "red_bird", "yellow_duck", "blue_horse",
    "green_frog", "purple_cat", "white_dog", "black_sheep",
    "goldfish", "teacher", "children", "eyes"  # "see" renamed to "eyes"
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
    "children": "Children",
    "eyes": "Eyes"
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
        fonts['title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(24 * scale))
        fonts['subtitle'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(16 * scale))
        fonts['instruction'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(14 * scale))
        fonts['footer'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(10 * scale))
        fonts['copyright'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(8 * scale))
        fonts['label'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(11 * scale))
    except (OSError, IOError):
        # Linux fonts (fallback)
        fonts['title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(24 * scale))
        fonts['subtitle'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(16 * scale))
        fonts['instruction'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(14 * scale))
        fonts['footer'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(10 * scale))
        fonts['copyright'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(8 * scale))
        fonts['label'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(11 * scale))
    return fonts


def make_transparent(image, opacity=0.25):
    """Make an image transparent for watermark hints"""
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
        3: LEVEL_3_GREEN,
        4: LEVEL_4_PURPLE
    }
    return level_colors.get(level, BRAND_NAVY)


def get_level_config(level):
    """Get the configuration for each level"""
    configs = {
        1: {"targets": 5, "distractors": 0, "watermark": True, "name": "Errorless"},
        2: {"targets": 4, "distractors": 1, "watermark": False, "name": "Easy"},
        3: {"targets": 3, "distractors": 2, "watermark": False, "name": "Medium"},
        4: {"targets": 1, "distractors": 4, "watermark": False, "name": "Hard"}
    }
    return configs.get(level, configs[1])


def select_icons_for_level(loaded_images, icon_names, level, target_icon):
    """
    Select icons for a level based on targets/distractors configuration
    Returns list of (image, is_target) tuples
    """
    config = get_level_config(level)
    targets_count = config["targets"]
    distractors_count = config["distractors"]
    
    # Get target image
    target_idx = icon_names.index(target_icon)
    target_img = loaded_images[target_idx]
    
    # Create target entries
    result = [(target_img, True) for _ in range(targets_count)]
    
    # Select distractors (different from target)
    if distractors_count > 0:
        distractor_names = [name for name in icon_names if name != target_icon]
        selected_distractors = random.sample(distractor_names, min(distractors_count, len(distractor_names)))
        
        for dist_name in selected_distractors:
            dist_idx = icon_names.index(dist_name)
            result.append((loaded_images[dist_idx], False))
    
    # Shuffle the order
    random.shuffle(result)
    
    return result


def create_matching_page(loaded_images, icon_names, target_icon, level, pack_code, theme_name, is_bw=False):
    """Create a matching activity page"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    config = get_level_config(level)
    
    # Border - using brand navy
    border_margin = int(15 * scale)
    border_radius = int(20 * scale)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, img_height - border_margin],
        radius=border_radius,
        outline=hex_to_rgb(BRAND_NAVY),
        width=int(3 * scale)
    )
    
    # Top accent stripe - using level color (or grayscale for BW)
    level_color = get_level_color(level)
    if is_bw:
        # Convert to grayscale
        rgb = hex_to_rgb(level_color)
        gray_value = int(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
        accent_color = (gray_value, gray_value, gray_value)
    else:
        accent_color = hex_to_rgb(level_color)
    
    # Taller accent stripe for title + subtitle
    accent_height = int(60 * scale)
    draw.rounded_rectangle(
        [border_margin + int(10 * scale), border_margin + int(10 * scale), 
         img_width - border_margin - int(10 * scale), border_margin + int(10 * scale) + accent_height],
        radius=int(12 * scale),
        fill=accent_color,
        outline=None
    )
    
    # Title
    title_text = "Match the Pictures"
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['title'])
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, border_margin + int(20 * scale)), title_text,
              fill='white', font=fonts['title'])
    
    # Subtitle
    subtitle_text = theme_name
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=fonts['subtitle'])
    subtitle_w = subtitle_bbox[2] - subtitle_bbox[0]
    draw.text(((img_width - subtitle_w) // 2, border_margin + int(48 * scale)), subtitle_text,
              fill='white', font=fonts['subtitle'])
    
    # Instruction line below accent stripe
    instr_y = border_margin + int(85 * scale)
    target_name = DISPLAY_NAMES.get(target_icon, target_icon.replace('_', ' ').title())
    instr_text = f"Match the {target_name}"
    instr_bbox = draw.textbbox((0, 0), instr_text, font=fonts['instruction'])
    instr_w = instr_bbox[2] - instr_bbox[0]
    draw.text(((img_width - instr_w) // 2, instr_y), instr_text,
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['instruction'])
    
    # Target box (reference image)
    target_y = instr_y + int(35 * scale)
    target_box_size = int(110 * scale)
    target_box_x = (img_width - target_box_size) // 2
    
    # Draw target box with shadow
    shadow_offset = int(3 * scale)
    draw.rounded_rectangle(
        [target_box_x + shadow_offset, target_y + shadow_offset, 
         target_box_x + target_box_size + shadow_offset, target_y + target_box_size + shadow_offset],
        radius=int(12 * scale),
        fill=(220, 220, 220, 20),
        outline=None
    )
    
    draw.rounded_rectangle(
        [target_box_x, target_y, target_box_x + target_box_size, target_y + target_box_size],
        radius=int(12 * scale),
        fill='white',
        outline=hex_to_rgb(BRAND_NAVY),
        width=int(4 * scale)
    )
    
    # Target image
    target_idx = icon_names.index(target_icon)
    target_img = loaded_images[target_idx].copy()
    target_img.thumbnail((int(85 * scale), int(85 * scale)), Image.Resampling.LANCZOS)
    target_img_x = target_box_x + (target_box_size - target_img.width) // 2
    target_img_y = target_y + (target_box_size - target_img.height) // 2
    
    if is_bw and target_img.mode == 'RGBA':
        # Convert to grayscale
        target_img = target_img.convert('L').convert('RGBA')
    
    page.paste(target_img, (target_img_x, target_img_y), target_img if target_img.mode == 'RGBA' else None)
    
    # Matching grid - 5 rows × 2 columns
    grid_start_y = target_y + target_box_size + int(30 * scale)
    box_size = int(135 * scale)  # Slightly smaller to fit 5 rows
    row_spacing = int(15 * scale)
    col_spacing = int(130 * scale)  # Space between columns
    
    # Center the two columns
    total_width = 2 * box_size + col_spacing
    grid_start_x = (img_width - total_width) // 2
    
    # Select icons for this level
    selected_icons = select_icons_for_level(loaded_images, icon_names, level, target_icon)
    
    for row in range(5):
        row_y = grid_start_y + row * (box_size + row_spacing)
        
        # Left column - Matching box
        left_x = grid_start_x
        
        if row < len(selected_icons):
            icon_img, is_target = selected_icons[row]
            
            # Matching box
            border_color = hex_to_rgb(BRAND_NAVY) if not is_bw else (60, 60, 60)
            draw.rounded_rectangle(
                [left_x, row_y, left_x + box_size, row_y + box_size],
                radius=int(12 * scale),
                fill='white',
                outline=border_color,
                width=int(3 * scale)
            )
            
            # Icon image
            icon_copy = icon_img.copy()
            if is_bw and icon_copy.mode == 'RGBA':
                icon_copy = icon_copy.convert('L').convert('RGBA')
            
            icon_copy.thumbnail((int(115 * scale), int(115 * scale)), Image.Resampling.LANCZOS)
            icon_x = left_x + (box_size - icon_copy.width) // 2
            icon_y = row_y + (box_size - icon_copy.height) // 2
            page.paste(icon_copy, (icon_x, icon_y), icon_copy if icon_copy.mode == 'RGBA' else None)
        
        # Right column - Velcro box
        right_x = grid_start_x + box_size + col_spacing
        
        # Velcro box background
        velcro_fill = (232, 232, 232) if not is_bw else (240, 240, 240)
        velcro_border = hex_to_rgb(PURPLE_BORDER) if not is_bw else (100, 100, 100)
        
        draw.rounded_rectangle(
            [right_x, row_y, right_x + box_size, row_y + box_size],
            radius=int(12 * scale),
            fill=velcro_fill,
            outline=velcro_border,
            width=int(3 * scale)
        )
        
        # Velcro dot (centered)
        if config["watermark"] and row < len(selected_icons):
            # Level 1: Add watermark hint
            _, is_target = selected_icons[row]
            if is_target:
                hint_img = loaded_images[target_idx].copy()
                hint_img = make_transparent(hint_img, opacity=0.25)
                if is_bw and hint_img.mode == 'RGBA':
                    hint_img = hint_img.convert('L').convert('RGBA')
                hint_img.thumbnail((int(90 * scale), int(90 * scale)), Image.Resampling.LANCZOS)
                hint_x = right_x + (box_size - hint_img.width) // 2
                hint_y = row_y + (box_size - hint_img.height) // 2
                page.paste(hint_img, (hint_x, hint_y), hint_img)
        
        # Velcro dot
        dot_size = int(30 * scale)
        dot_x = right_x + (box_size - dot_size) // 2
        dot_y = row_y + (box_size - dot_size) // 2
        
        dot_fill = hex_to_rgb(VELCRO_FILL) if not is_bw else (200, 200, 200)
        dot_outline = hex_to_rgb(VELCRO_OUTLINE) if not is_bw else (150, 150, 150)
        
        draw.ellipse(
            [dot_x, dot_y, dot_x + dot_size, dot_y + dot_size],
            fill=dot_fill,
            outline=dot_outline,
            width=int(2 * scale)
        )
    
    # Footer - Two lines
    footer_y = img_height - int(55 * scale)
    
    # Line 1: Activity info
    level_name = config["name"]
    footer_line1 = f"Matching – Level {level} ({level_name}) | {pack_code}"
    footer1_bbox = draw.textbbox((0, 0), footer_line1, font=fonts['footer'])
    footer1_w = footer1_bbox[2] - footer1_bbox[0]
    draw.text(((img_width - footer1_w) // 2, footer_y), footer_line1,
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['footer'])
    
    # Line 2: Copyright
    copyright_y = img_height - int(35 * scale)
    copyright_text = "© 2025 Small Wins Studio. All rights reserved. • PCS® symbols used with active PCS Maker Personal License."
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_w = copyright_bbox[2] - copyright_bbox[0]
    draw.text(((img_width - copyright_w) // 2, copyright_y), copyright_text,
              fill=FOOTER_GREY, font=fonts['copyright'])
    
    return page


def create_cutout_page(loaded_images, icon_names, pack_code, theme_name, is_bw=False):
    """Create cutout pieces page - 4 columns × 5 rows"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    # Border
    border_margin = int(15 * scale)
    border_radius = int(20 * scale)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, img_height - border_margin],
        radius=border_radius,
        outline=hex_to_rgb(BRAND_NAVY),
        width=int(3 * scale)
    )
    
    # Top accent stripe
    accent_color = hex_to_rgb(BRAND_TEAL) if not is_bw else (100, 100, 100)
    accent_height = int(50 * scale)
    draw.rounded_rectangle(
        [border_margin + int(10 * scale), border_margin + int(10 * scale), 
         img_width - border_margin - int(10 * scale), border_margin + int(10 * scale) + accent_height],
        radius=int(12 * scale),
        fill=accent_color,
        outline=None
    )
    
    # Title
    title_text = f"Cutout Matching Pieces – {theme_name}"
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['title'])
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, border_margin + int(25 * scale)), title_text,
              fill='white', font=fonts['title'])
    
    # Cutout grid - 4 columns × 5 rows = 20 boxes
    grid_start_y = border_margin + int(90 * scale)
    box_size = int(135 * scale)
    spacing = int(15 * scale)
    
    cols = 4
    rows = 5
    
    # Center the grid
    total_width = cols * box_size + (cols - 1) * spacing
    grid_start_x = (img_width - total_width) // 2
    
    icon_idx = 0
    for row in range(rows):
        for col in range(cols):
            if icon_idx >= len(loaded_images):
                break
            
            box_x = grid_start_x + col * (box_size + spacing)
            box_y = grid_start_y + row * (box_size + spacing)
            
            # Cutout box border
            border_color = hex_to_rgb(BRAND_TEAL) if not is_bw else (100, 100, 100)
            draw.rounded_rectangle(
                [box_x, box_y, box_x + box_size, box_y + box_size],
                radius=int(12 * scale),
                fill='white',
                outline=border_color,
                width=int(3 * scale)
            )
            
            # Icon
            icon_img = loaded_images[icon_idx].copy()
            if is_bw and icon_img.mode == 'RGBA':
                icon_img = icon_img.convert('L').convert('RGBA')
            
            icon_img.thumbnail((int(90 * scale), int(90 * scale)), Image.Resampling.LANCZOS)
            icon_x = box_x + (box_size - icon_img.width) // 2
            icon_y = box_y + int(15 * scale)
            page.paste(icon_img, (icon_x, icon_y), icon_img if icon_img.mode == 'RGBA' else None)
            
            # Label
            icon_name = icon_names[icon_idx]
            label_text = DISPLAY_NAMES.get(icon_name, icon_name.replace('_', ' ').title())
            label_bbox = draw.textbbox((0, 0), label_text, font=fonts['label'])
            label_w = label_bbox[2] - label_bbox[0]
            draw.text((box_x + (box_size - label_w) // 2, box_y + box_size - int(30 * scale)),
                     label_text, fill=hex_to_rgb(BRAND_NAVY), font=fonts['label'])
            
            icon_idx += 1
    
    # Footer
    footer_y = img_height - int(55 * scale)
    footer_line1 = f"Cutout Matching Pieces | {pack_code}"
    footer1_bbox = draw.textbbox((0, 0), footer_line1, font=fonts['footer'])
    footer1_w = footer1_bbox[2] - footer1_bbox[0]
    draw.text(((img_width - footer1_w) // 2, footer_y), footer_line1,
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['footer'])
    
    copyright_y = img_height - int(35 * scale)
    copyright_text = "© 2025 Small Wins Studio. All rights reserved. • PCS® symbols used with active PCS Maker Personal License."
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_w = copyright_bbox[2] - copyright_bbox[0]
    draw.text(((img_width - copyright_w) // 2, copyright_y), copyright_text,
              fill=FOOTER_GREY, font=fonts['copyright'])
    
    return page


def add_storage_labels(c, page_width, page_height):
    """Add storage labels page"""
    inch = 72
    
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(page_width/2, page_height - 1*inch, "Storage Labels - Matching")
    
    # Level-coded storage labels
    labels_data = [
        ("Matching - Level 1", "Errorless (5 targets, watermarks)", LEVEL_1_ORANGE),
        ("Matching - Level 2", "Easy (4 targets, 1 distractor)", LEVEL_2_BLUE),
        ("Matching - Level 3", "Medium (3 targets, 2 distractors)", LEVEL_3_GREEN),
        ("Matching - Level 4", "Hard (1 target, 4 distractors)", LEVEL_4_PURPLE)
    ]
    
    label_width = 5 * inch
    label_height = 2.5 * inch
    y_start = page_height - 2*inch
    
    for i, (title, description, color_hex) in enumerate(labels_data):
        y_pos = y_start - (i * (label_height + 0.5*inch))
        x_pos = (page_width - label_width) / 2
        
        # Background
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.roundRect(x_pos, y_pos, label_width, label_height, 10, fill=1, stroke=1)
        
        # Color header
        hex_color = color_hex.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
        c.setFillColorRGB(*rgb)
        c.roundRect(x_pos, y_pos + label_height - 0.8*inch, 
                   label_width, 0.8*inch, 10, fill=1, stroke=0)
        
        # Title
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 32)
        c.drawCentredString(page_width/2, y_pos + label_height - 0.45*inch, title)
        
        # Description
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.setFont("Helvetica", 18)
        c.drawCentredString(page_width/2, y_pos + 0.4*inch, description)


def generate_matching_pack(images_folder, pack_code="BB03", theme_name="Brown Bear"):
    """Generate complete matching pack - 4 levels (color + BW) + cutouts + labels"""
    
    print(f"\n{'='*70}")
    print(f"  🎯 GENERATING MATCHING ACTIVITY: {pack_code}")
    print(f"  Theme: {theme_name}")
    print(f"  Updated with TPT Brand Colors - Small Wins Studio")
    print(f"{'='*70}\n")
    
    images_path = Path(images_folder)
    if not images_path.exists():
        print(f"❌ Error: Folder '{images_folder}' not found!")
        return False
    
    # Load all icons
    loaded_images = []
    icon_names = []
    missing_images = []
    
    for icon_name in BROWN_BEAR_ICONS:
        # Handle "eyes" as alternative name for "see"
        img_file = images_path / f"{icon_name}.png"
        if not img_file.exists() and icon_name == "eyes":
            img_file = images_path / "see.png"
        
        if not img_file.exists():
            missing_images.append(icon_name)
            continue
        
        img = Image.open(img_file)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        loaded_images.append(img)
        icon_names.append(icon_name)
    
    if missing_images:
        print(f"❌ Missing images: {', '.join(missing_images)}")
        print(f"   Found {len(loaded_images)} of {len(BROWN_BEAR_ICONS)} icons")
    
    if len(loaded_images) < 5:
        print(f"❌ Need at least 5 images, found {len(loaded_images)}")
        return False
    
    output_folder = Path("OUTPUT")
    output_folder.mkdir(exist_ok=True)
    
    print(f"📝 Pack Details:")
    print(f"   Code: {pack_code}")
    print(f"   Theme: {theme_name}")
    print(f"   Icons: {len(loaded_images)} loaded\n")
    
    # Select a target icon (use first available)
    target_icon = icon_names[0]
    
    print(f"📄 Creating matching pages...\n")
    
    saved_pages_color = []
    saved_pages_bw = []
    
    # Generate all 4 levels
    for level in range(1, 5):
        config = get_level_config(level)
        level_color = get_level_color(level)
        
        print(f"   Level {level}: {config['name']} - {level_color}...")
        
        # Color version
        page_color = create_matching_page(loaded_images, icon_names, target_icon, level, 
                                         pack_code, theme_name, is_bw=False)
        saved_pages_color.append((level, page_color))
        
        # BW version
        page_bw = create_matching_page(loaded_images, icon_names, target_icon, level, 
                                       pack_code, theme_name, is_bw=True)
        saved_pages_bw.append((level, page_bw))
    
    # Cutout pages
    print(f"   Cutout Pages (Color & BW)...")
    cutout_color = create_cutout_page(loaded_images, icon_names, pack_code, theme_name, is_bw=False)
    cutout_bw = create_cutout_page(loaded_images, icon_names, pack_code, theme_name, is_bw=True)
    
    print(f"\n   ✅ {len(saved_pages_color)} levels × 2 versions + cutouts generated\n")
    
    # Create PDFs
    print(f"📄 Creating PDFs...")
    
    # Color PDF
    pdf_path_color = f"OUTPUT/{pack_code}_Matching_Color.pdf"
    c = canvas.Canvas(pdf_path_color, pagesize=letter)
    
    for level, page in saved_pages_color:
        img_buffer = io.BytesIO()
        page.save(img_buffer, format='PNG', dpi=(DPI, DPI))
        img_buffer.seek(0)
        c.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    
    # Add cutout page
    img_buffer = io.BytesIO()
    cutout_color.save(img_buffer, format='PNG', dpi=(DPI, DPI))
    img_buffer.seek(0)
    c.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
    c.showPage()
    
    # Add storage labels
    add_storage_labels(c, PAGE_WIDTH, PAGE_HEIGHT)
    c.showPage()
    
    c.save()
    print(f"   ✅ {pdf_path_color}")
    
    # BW PDF
    pdf_path_bw = f"OUTPUT/{pack_code}_Matching_BW.pdf"
    c = canvas.Canvas(pdf_path_bw, pagesize=letter)
    
    for level, page in saved_pages_bw:
        img_buffer = io.BytesIO()
        page.save(img_buffer, format='PNG', dpi=(DPI, DPI))
        img_buffer.seek(0)
        c.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    
    # Add cutout page
    img_buffer = io.BytesIO()
    cutout_bw.save(img_buffer, format='PNG', dpi=(DPI, DPI))
    img_buffer.seek(0)
    c.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
    c.showPage()
    
    # Add storage labels (same as color)
    add_storage_labels(c, PAGE_WIDTH, PAGE_HEIGHT)
    c.showPage()
    
    c.save()
    print(f"   ✅ {pdf_path_bw}\n")
    
    print(f"{'='*70}")
    print(f"  ✨ SUCCESS! Matching pack generated with TPT brand colors")
    print(f"  © 2025 Small Wins Studio")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python MATCHING.py <images_folder> [pack_code] [theme_name]")
        print("\nExample:")
        print("  python MATCHING.py brown_bear_images BB03 'Brown Bear'")
        sys.exit(1)
    
    images_folder = sys.argv[1]
    pack_code = sys.argv[2] if len(sys.argv) > 2 else "BB03"
    theme_name = sys.argv[3] if len(sys.argv) > 3 else "Brown Bear"
    
    success = generate_matching_pack(images_folder, pack_code, theme_name)
    sys.exit(0 if success else 1)
