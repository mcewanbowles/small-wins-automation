"""
BROWN BEAR SEQUENCING - Interactive Velcro Activity
Evidence-based 5-level progression for special education students

DESIGN:
- PORTRAIT orientation (8.5" × 11") per user request
- Title centered in colored accent stripe with padding
- 11 empty boxes in creative SNAKE PATHWAY layout (not grid)
- S-curve wiggly path showing sequence journey down the page
- More engaging visual for SPED students
- Separate cutout sheet with all 11 pieces (matching snake layout)
- Boxes same size as cutouts for velcro matching (85×105 points)
- Design Constitution compliant: proper margins, footer within border, and branding

EVIDENCE-BASED 5-LEVEL PROGRESSION (Concrete to Abstract, Maximum Support to Independence):
- Level 1: Color PCS symbol watermarks (errorless learning) - Orange #F4B400
- Level 2: Real photo watermarks (generalization to authentic images) - Blue #4285F4
- Level 3: B&W PCS symbols (removes color & realism cues) - Green #34A853
- Level 4: Text labels only (literacy-based) - Purple #8C06F2
- Level 5: No help - blank boxes (complete independence/assessment) - Red #EA4335

PEDAGOGICAL RATIONALE:
- Level 1: Maximum visual scaffolding with familiar symbols
- Level 2: Bridges symbols to real-world photographs for generalization
- Level 3: Removes color and realism, focuses on shape discrimination
- Level 4: Minimal support, promotes literacy skills
- Level 5: Full independence, student must recall sequence from memory

OUTPUT: 11 pages (5 activity levels + 5 level-specific cutout pages + 1 storage labels)

CUTOUT PAGES (one for each level):
- Level 1 cutouts: Color PCS symbols
- Level 2 cutouts: Real photographs
- Level 3 cutouts: Black & white symbols (for coloring)
- Level 4 cutouts: Text labels only
- Level 5 cutouts: Blank boxes
- Layout: 4-4-3 rows to optimize space in portrait orientation
"""

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io

# PORTRAIT orientation per user request (8.5" × 11")
PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

# TPT Brand Colors - Updated to match Small Wins Studio branding
BRAND_NAVY = "#1E3A5F"  # Border and text
BRAND_TEAL = "#2AAEAE"  # Small Wins brand color
BRAND_GOLD = "#E8C547"  # Small Wins brand color

# Level Colors - Universal across all products (per Master Product Specification)
LEVEL_1_ORANGE = "#F4B400"  # Errorless - Color symbol watermarks
LEVEL_2_BLUE = "#4285F4"    # Distractors - Real photo watermarks
LEVEL_3_GREEN = "#34A853"   # Picture + Text - B&W symbols
LEVEL_4_PURPLE = "#8C06F2"  # Generalisation - Text labels only
LEVEL_5_RED = "#EA4335"     # Independence - No help (blank boxes)

# Supporting colors
LIGHT_BLUE = "#EEF4FB"
STEEL_BLUE = "#5B7AA0"
FOOTER_GREY = "#999999"

# Story sequence (11 characters in order)
# NOTE: Starting with Red Bird per user request - Brown Bear is not in the sequence boxes
STORY_SEQUENCE = [
    "red_bird",      # 1 - Story starts here: "Red Bird, what do you see?"
    "yellow_duck",   # 2
    "blue_horse",    # 3
    "green_frog",    # 4
    "purple_cat",    # 5
    "white_dog",     # 6
    "black_sheep",   # 7
    "goldfish",      # 8
    "teacher",       # 9
    "children",      # 10
    "brown_bear"     # 11 - Brown Bear comes last
]

# Real image filename mapping (for Level 2)
REAL_IMAGE_MAPPING = {
    "brown_bear": "bear.png",
    "red_bird": "bird.png",
    "yellow_duck": "duck.png",
    "blue_horse": "horse.png",
    "green_frog": "frog.png",
    "purple_cat": "cat.png",
    "white_dog": "dog.png",
    "black_sheep": "sheep.png",
    "goldfish": "goldfish.png",
    "teacher": "teacher.png",
    "children": "teacher.png"  # Use teacher image for children if no children.png exists
}

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
        fonts['number_small'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(20 * scale))  # Smaller for better fit
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
        fonts['number_small'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(20 * scale))  # Smaller for better fit
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


def convert_to_bw(image):
    """Convert image to black and white line art style for Level 3"""
    # Convert to grayscale first
    if image.mode == 'RGBA':
        # Create a white background
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    
    grayscale = image.convert('L')
    
    # Enhance contrast for line-art effect
    enhancer = ImageEnhance.Contrast(grayscale)
    high_contrast = enhancer.enhance(2.0)
    
    # Convert back to RGBA
    bw_image = high_contrast.convert('RGBA')
    return bw_image


def get_level_color(level):
    """Get the brand color for a specific level"""
    level_colors = {
        1: LEVEL_1_ORANGE,
        2: LEVEL_2_BLUE,
        3: LEVEL_3_GREEN,
        4: LEVEL_4_PURPLE,
        5: LEVEL_5_RED
    }
    return level_colors.get(level, BRAND_NAVY)


def create_sequencing_page(loaded_images, real_images, level, pack_code, theme_name, page_num, total_pages=7):
    """Create sequencing activity page with empty boxes - PORTRAIT LAYOUT (per Design Constitution)
    
    Args:
        loaded_images: List of PCS symbol images
        real_images: List of real photograph images (for Level 2)
        level: 1-5 difficulty level
        pack_code: Product code
        theme_name: Theme name (e.g., "Brown Bear")
        page_num: Current page number
        total_pages: Total pages in PDF
    """
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    # Margins: 0.5" per Design Constitution
    margin = int(0.5 * 72 * scale)  # 0.5 inch = 36 points at 72 DPI
    
    # Border: 2-3px rounded rectangle, 0.12" corner radius
    border_radius = int(0.12 * 72 * scale)  # 0.12 inch
    draw.rounded_rectangle(
        [margin, margin, img_width - margin, img_height - margin],
        radius=border_radius,
        outline=hex_to_rgb(BRAND_NAVY),
        width=int(3 * scale)
    )
    
    # Accent stripe: increased height for better padding around title
    level_color = get_level_color(level)
    accent_height = int(0.65 * 72 * scale)  # 0.65 inch (increased from 0.55)
    accent_padding = int(0.12 * 72 * scale)  # 0.12 inch padding from border
    draw.rounded_rectangle(
        [margin + accent_padding, margin + accent_padding, 
         img_width - margin - accent_padding, margin + accent_padding + accent_height],
        radius=int(0.12 * 72 * scale),
        fill=hex_to_rgb(level_color),
        outline=None
    )
    
    # Title - centered in accent stripe with proper vertical padding (15px top, 12px bottom)
    title_text = f"{theme_name} - Sequencing"
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['title'])
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    # Center vertically in accent stripe
    title_y = margin + accent_padding + (accent_height - title_h) // 2
    draw.text(((img_width - title_w) // 2, title_y), title_text,
              fill='white', font=fonts['title'])
    
    # Compact story setup section
    setup_y = margin + accent_padding + accent_height + int(12 * scale)
    
    # Red Bird image (sequence now starts with Red Bird per user request)
    rb_img = loaded_images[0].copy()  # red_bird is now first in STORY_SEQUENCE
    rb_img.thumbnail((int(45 * scale), int(45 * scale)), Image.Resampling.LANCZOS)
    rb_x = int(40 * scale)
    page.paste(rb_img, (rb_x, setup_y), rb_img if rb_img.mode == 'RGBA' else None)
    
    # Smaller Eyes image
    try:
        look_path = Path("aac_images") / "look.png"
        if look_path.exists():
            eyes_img = Image.open(look_path).convert('RGBA')
        else:
            see_look_path = Path("aac_images") / "see_look.png"
            if see_look_path.exists():
                eyes_img = Image.open(see_look_path).convert('RGBA')
            else:
                eyes_img = loaded_images[0].copy()
    except (FileNotFoundError, IOError):
        eyes_img = loaded_images[0].copy()
        
    eyes_img.thumbnail((int(45 * scale), int(45 * scale)), Image.Resampling.LANCZOS)
    eyes_x = rb_x + int(55 * scale)
    page.paste(eyes_img, (eyes_x, setup_y), eyes_img if eyes_img.mode == 'RGBA' else None)
    
    # Compact story text (updated to Red Bird)
    text_x = eyes_x + int(65 * scale)
    draw.text((text_x, setup_y + int(5 * scale)), "Red Bird, what do you see? I see...",
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['prompt'])
    
    # NOTE: Level subtitle removed per user request - level indicated by color only
    
    # SNAKE PATHWAY LAYOUT: Creative wiggly path showing sequence journey
    # Boxes wind down the page in an S-curve pattern - more engaging for SPED students
    box_width = int(85 * scale)
    box_height = int(105 * scale)
    
    # Starting Y position
    first_box_y = setup_y + int(60 * scale)
    
    # Snake pathway positions - manually positioned for creative S-curve
    # Format: (x_offset_from_left_margin, y_offset_from_first_box)
    # Creates a flowing snake pattern down the page
    snake_positions = [
        # Top row: 4 boxes going right (boxes 1-4)
        (100, 0),      # Box 1
        (225, 0),      # Box 2
        (350, 0),      # Box 3
        (475, 0),      # Box 4
        
        # Curve down and left (boxes 5-8)
        (450, 145),    # Box 5 (start curving back)
        (350, 175),    # Box 6 (diagonal down-left)
        (250, 205),    # Box 7 (continuing down-left)
        (150, 235),    # Box 8 (continuing down-left)
        
        # Bottom row: 3 boxes going right (boxes 9-11)
        (175, 380),    # Box 9
        (300, 380),    # Box 10
        (425, 380),    # Box 11
    ]
    
    # Draw each box at its snake pathway position
    for i, (x_offset, y_offset) in enumerate(snake_positions):
        box_x = int(x_offset * scale)
        box_y = first_box_y + int(y_offset * scale)
            
        # Box with light blue fill
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_width, box_y + box_height],
            radius=int(8 * scale),
            fill=hex_to_rgb(LIGHT_BLUE),
            outline=hex_to_rgb(BRAND_NAVY),
            width=int(2 * scale)
        )
        
        # Number circle at top - smaller numbers, better centered
        circle_size = int(28 * scale)
        circle_x = box_x + (box_width - circle_size) // 2
        circle_y = box_y - int(14 * scale)
        draw.ellipse(
            [circle_x, circle_y, circle_x + circle_size, circle_y + circle_size],
            fill=hex_to_rgb(BRAND_NAVY)
        )
        
        # Smaller number font for better fit
        num_text = str(i + 1)
        num_bbox = draw.textbbox((0, 0), num_text, font=fonts['number_small'])
        num_w = num_bbox[2] - num_bbox[0]
        num_h = num_bbox[3] - num_bbox[1]
        # Better centering - adjust for font baseline
        draw.text((circle_x + (circle_size - num_w) // 2, 
                  circle_y + (circle_size - num_h) // 2 - int(2 * scale)),
                 num_text, fill='white', font=fonts['number_small'])
        
        # Content based on level
        if level == 1:
            # Level 1: Color PCS symbol watermark hints (errorless learning)
            hint_img = loaded_images[i].copy()
            hint_img = make_transparent(hint_img, opacity=0.15)
            hint_img.thumbnail((int(65 * scale), int(65 * scale)), Image.Resampling.LANCZOS)
            hint_x = box_x + (box_width - hint_img.width) // 2
            hint_y = box_y + (box_height - hint_img.height) // 2
            page.paste(hint_img, (hint_x, hint_y), hint_img)
            
        elif level == 2:
            # Level 2: Real photo watermark hints (generalization to authentic images)
            if real_images and i < len(real_images):
                hint_img = real_images[i].copy()
                hint_img = make_transparent(hint_img, opacity=0.15)
                hint_img.thumbnail((int(65 * scale), int(65 * scale)), Image.Resampling.LANCZOS)
                hint_x = box_x + (box_width - hint_img.width) // 2
                hint_y = box_y + (box_height - hint_img.height) // 2
                page.paste(hint_img, (hint_x, hint_y), hint_img)
            
        elif level == 3:
            # Level 3: Black & white PCS symbols (remove color and realism cues)
            bw_img = loaded_images[i].copy()
            bw_img = convert_to_bw(bw_img)
            bw_img.thumbnail((int(65 * scale), int(65 * scale)), Image.Resampling.LANCZOS)
            bw_x = box_x + (box_width - bw_img.width) // 2
            bw_y = box_y + (box_height - bw_img.height) // 2
            page.paste(bw_img, (bw_x, bw_y), bw_img if bw_img.mode == 'RGBA' else None)
            
        elif level == 4:
            # Level 4: Text labels only (literacy-based, minimal support)
            label_text = DISPLAY_NAMES[STORY_SEQUENCE[i]]
            label_bbox = draw.textbbox((0, 0), label_text, font=fonts['label'])
            label_w = label_bbox[2] - label_bbox[0]
            draw.text((box_x + (box_width - label_w) // 2, box_y + box_height - int(25 * scale)),
                     label_text, fill=hex_to_rgb(BRAND_NAVY), font=fonts['label'])
        
        elif level == 5:
            # Level 5: No help - blank boxes (complete independence/assessment)
            pass  # Intentionally blank - student works from memory
    
    # NOTE: Arrows removed per user request - snake pathway shows flow naturally
    
    # Footer - Two lines inside border
    # Line 1: Product name
    footer_y = img_height - margin - int(45 * scale)  # Inside border
    footer_line1 = f"{theme_name} Sequencing – {pack_code}"
    footer1_bbox = draw.textbbox((0, 0), footer_line1, font=fonts['footer'])
    footer1_w = footer1_bbox[2] - footer1_bbox[0]
    draw.text(((img_width - footer1_w) // 2, footer_y), footer_line1,
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['footer'])
    
    # Line 2: Small Wins and copyright - inside border
    copyright_y = img_height - margin - int(25 * scale)  # Inside border
    copyright_text = "© 2025 Small Wins Studio. All rights reserved. • PCS® symbols used with active PCS Maker Personal License."
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_w = copyright_bbox[2] - copyright_bbox[0]
    draw.text(((img_width - copyright_w) // 2, copyright_y), copyright_text,
              fill=FOOTER_GREY, font=fonts['copyright'])


    
    return page


def create_cutout_page(loaded_images, real_images, pack_code, theme_name, level, page_num, total_pages=11):
    """Create level-specific cutout pieces page - LANDSCAPE with 3-per-row layout (4 rows: 3-3-3-2)
    
    Level-specific cutouts:
    - Level 1: Color PCS symbols (current icons)
    - Level 2: Real photographs
    - Level 3: Black & white symbols (for coloring)
    - Level 4: Text labels only
    - Level 5: Blank boxes (for complete independence)
    """
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    # Margins: 0.5" per Design Constitution (same as activity pages)
    margin = int(0.5 * 72 * scale)
    border_radius = int(0.12 * 72 * scale)
    draw.rounded_rectangle(
        [margin, margin, img_width - margin, img_height - margin],
        radius=border_radius,
        outline=hex_to_rgb(BRAND_NAVY),
        width=int(3 * scale)
    )
    
    # Accent stripe - using level color for cutouts
    level_color = get_level_color(level)
    accent_height = int(0.55 * 72 * scale)  # 0.55 inch
    accent_padding = int(0.12 * 72 * scale)  # 0.12 inch padding from border
    draw.rounded_rectangle(
        [margin + accent_padding, margin + accent_padding, 
         img_width - margin - accent_padding, margin + accent_padding + accent_height],
        radius=int(0.12 * 72 * scale),
        fill=hex_to_rgb(level_color),
        outline=None
    )
    
    # Title - level-specific
    level_names = {
        1: "Level 1 - Color Symbol Cutouts",
        2: "Level 2 - Real Photo Cutouts",
        3: "Level 3 - B&W Symbol Cutouts (for Coloring)",
        4: "Level 4 - Text Label Cutouts",
        5: "Level 5 - Blank Cutouts"
    }
    title_text = f"{theme_name} - {level_names[level]}"
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['title'])
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, margin + accent_padding + int(10 * scale)), title_text,
              fill='white', font=fonts['title'])
    
    # Instruction
    instr_y = margin + accent_padding + accent_height + int(12 * scale)
    instr_text = "✂ Cut out these pieces. Use velcro to attach them to the sequencing boxes in story order."
    instr_bbox = draw.textbbox((0, 0), instr_text, font=fonts['label'])
    instr_w = instr_bbox[2] - instr_bbox[0]
    draw.text(((img_width - instr_w) // 2, instr_y), instr_text,
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['label'])
    
    # Cutout pieces - SAME SIZE AS ACTIVITY PAGE BOXES (85x105)
    # Use same 3-row layout (4-4-3) to match activity pages
    box_width = int(85 * scale)
    box_height = int(105 * scale)
    box_spacing = int(10 * scale)
    row_spacing = int(20 * scale)  # Tighter spacing for cutout page
    
    # Starting Y position for first row
    first_row_y = instr_y + int(35 * scale)
    
    # Define rows: [count, starting_index] - same as activity pages
    rows = [
        (4, 0),   # Row 1: pieces 1-4
        (4, 4),   # Row 2: pieces 5-8
        (3, 8)    # Row 3: pieces 9-11
    ]
    
    for row_num, (count, start_idx) in enumerate(rows):
        # Calculate row Y position
        row_y = first_row_y + row_num * (box_height + row_spacing)
        
        # Calculate centered X position for this row
        row_width = count * box_width + (count - 1) * box_spacing
        row_start_x = (img_width - row_width) // 2
        
        # Draw cutout pieces in this row
        for col in range(count):
            i = start_idx + col
            box_x = row_start_x + col * (box_width + box_spacing)
            
            # Box with cutting border - using level color
            draw.rounded_rectangle(
                [box_x, row_y, box_x + box_width, row_y + box_height],
                radius=int(8 * scale),
                fill='white',
                outline=hex_to_rgb(level_color),
                width=int(2 * scale)
            )
            
            # Level-specific content
            if level == 1:
                # Level 1: Color PCS symbols
                char_img = loaded_images[i].copy()
                char_img.thumbnail((int(60 * scale), int(60 * scale)), Image.Resampling.LANCZOS)
                char_x = box_x + (box_width - char_img.width) // 2
                char_y = row_y + int(12 * scale)
                page.paste(char_img, (char_x, char_y), char_img if char_img.mode == 'RGBA' else None)
                
                # Label and number
                label_text = DISPLAY_NAMES[STORY_SEQUENCE[i]]
                label_bbox = draw.textbbox((0, 0), label_text, font=fonts['cutout_label'])
                label_w = label_bbox[2] - label_bbox[0]
                draw.text((box_x + (box_width - label_w) // 2, row_y + box_height - int(30 * scale)),
                         label_text, fill=hex_to_rgb(BRAND_NAVY), font=fonts['cutout_label'])
                
                num_text = str(i + 1)
                num_bbox = draw.textbbox((0, 0), num_text, font=fonts['label'])
                num_w = num_bbox[2] - num_bbox[0]
                draw.text((box_x + (box_width - num_w) // 2, row_y + box_height - int(15 * scale)),
                         num_text, fill='#666666', font=fonts['label'])
                         
            elif level == 2:
                # Level 2: Real photographs
                if real_images and i < len(real_images):
                    char_img = real_images[i].copy()
                    char_img.thumbnail((int(60 * scale), int(60 * scale)), Image.Resampling.LANCZOS)
                    char_x = box_x + (box_width - char_img.width) // 2
                    char_y = row_y + int(12 * scale)
                    page.paste(char_img, (char_x, char_y), char_img if char_img.mode == 'RGBA' else None)
                else:
                    # Fallback to PCS symbols if real images not available
                    char_img = loaded_images[i].copy()
                    char_img.thumbnail((int(60 * scale), int(60 * scale)), Image.Resampling.LANCZOS)
                    char_x = box_x + (box_width - char_img.width) // 2
                    char_y = row_y + int(12 * scale)
                    page.paste(char_img, (char_x, char_y), char_img if char_img.mode == 'RGBA' else None)
                
                # Label and number
                label_text = DISPLAY_NAMES[STORY_SEQUENCE[i]]
                label_bbox = draw.textbbox((0, 0), label_text, font=fonts['cutout_label'])
                label_w = label_bbox[2] - label_bbox[0]
                draw.text((box_x + (box_width - label_w) // 2, row_y + box_height - int(30 * scale)),
                         label_text, fill=hex_to_rgb(BRAND_NAVY), font=fonts['cutout_label'])
                
                num_text = str(i + 1)
                num_bbox = draw.textbbox((0, 0), num_text, font=fonts['label'])
                num_w = num_bbox[2] - num_bbox[0]
                draw.text((box_x + (box_width - num_w) // 2, row_y + box_height - int(15 * scale)),
                         num_text, fill='#666666', font=fonts['label'])
                         
            elif level == 3:
                # Level 3: Black & white symbols (for coloring)
                bw_img = loaded_images[i].copy()
                bw_img = convert_to_bw(bw_img)
                bw_img.thumbnail((int(60 * scale), int(60 * scale)), Image.Resampling.LANCZOS)
                bw_x = box_x + (box_width - bw_img.width) // 2
                bw_y = row_y + int(12 * scale)
                page.paste(bw_img, (bw_x, bw_y), bw_img if bw_img.mode == 'RGBA' else None)
                
                # Label and number
                label_text = DISPLAY_NAMES[STORY_SEQUENCE[i]]
                label_bbox = draw.textbbox((0, 0), label_text, font=fonts['cutout_label'])
                label_w = label_bbox[2] - label_bbox[0]
                draw.text((box_x + (box_width - label_w) // 2, row_y + box_height - int(30 * scale)),
                         label_text, fill=hex_to_rgb(BRAND_NAVY), font=fonts['cutout_label'])
                
                num_text = str(i + 1)
                num_bbox = draw.textbbox((0, 0), num_text, font=fonts['label'])
                num_w = num_bbox[2] - num_bbox[0]
                draw.text((box_x + (box_width - num_w) // 2, row_y + box_height - int(15 * scale)),
                         num_text, fill='#666666', font=fonts['label'])
                         
            elif level == 4:
                # Level 4: Text labels only (large and clear)
                label_text = DISPLAY_NAMES[STORY_SEQUENCE[i]]
                label_bbox = draw.textbbox((0, 0), label_text, font=fonts['cutout_label'])
                label_w = label_bbox[2] - label_bbox[0]
                label_h = label_bbox[3] - label_bbox[1]
                # Center text vertically and horizontally
                draw.text((box_x + (box_width - label_w) // 2, row_y + (box_height - label_h) // 2),
                         label_text, fill=hex_to_rgb(BRAND_NAVY), font=fonts['cutout_label'])
                
                # Number at bottom
                num_text = str(i + 1)
                num_bbox = draw.textbbox((0, 0), num_text, font=fonts['label'])
                num_w = num_bbox[2] - num_bbox[0]
                draw.text((box_x + (box_width - num_w) // 2, row_y + box_height - int(15 * scale)),
                         num_text, fill='#666666', font=fonts['label'])
                         
            elif level == 5:
                # Level 5: Blank boxes (number only for identification)
                num_text = str(i + 1)
                num_bbox = draw.textbbox((0, 0), num_text, font=fonts['number'])
                num_w = num_bbox[2] - num_bbox[0]
                num_h = num_bbox[3] - num_bbox[1]
                # Center number in box
                draw.text((box_x + (box_width - num_w) // 2, row_y + (box_height - num_h) // 2),
                         num_text, fill='#CCCCCC', font=fonts['number'])
    
    # Footer - Two lines matching Design Constitution style
    footer_y = img_height - int(55 * scale)
    
    # Line 1: Activity info
    footer_line1 = f"Sequencing Cutouts – Level {level} | {pack_code}"
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


def add_storage_labels_sequencing(c, page_width, page_height):
    """Add storage labels page at end - LANDSCAPE orientation"""
    inch = 72  # points
    
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(page_width/2, page_height - 1*inch, "Storage Labels - Sequencing")
    
    # Updated to reflect 5-level evidence-based progression
    labels_data = [
        ("Level 1", "Color Symbol Hints", LEVEL_1_ORANGE),
        ("Level 2", "Real Photo Hints", LEVEL_2_BLUE),
        ("Level 3", "B&W Symbols", LEVEL_3_GREEN),
        ("Level 4", "Text Labels", LEVEL_4_PURPLE),
        ("Level 5", "No Help", LEVEL_5_RED)
    ]
    
    # Smaller labels to fit 5 in landscape
    label_width = 4 * inch
    label_height = 2.2 * inch
    y_start = page_height - 2*inch
    
    for i, (title, description, color_hex) in enumerate(labels_data):
        y_pos = y_start - (i * (label_height + 0.4*inch))
        x_pos = (page_width - label_width) / 2
        
        # Background
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.roundRect(x_pos, y_pos, label_width, label_height, 10, fill=1, stroke=1)
        
        # Color header - using TPT brand level colors
        hex_color = color_hex.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
        c.setFillColorRGB(*rgb)
        c.roundRect(x_pos, y_pos + label_height - 0.7*inch, 
                   label_width, 0.7*inch, 10, fill=1, stroke=0)
        
        # Title
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(page_width/2, y_pos + label_height - 0.4*inch, title)
        
        # Description
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.setFont("Helvetica", 18)
        c.drawCentredString(page_width/2, y_pos + 0.3*inch, description)


def generate_sequencing_pack(images_folder, pack_code="BB0ALL", theme_name="Brown Bear"):
    """Generate complete sequencing pack - 5 levels + cutouts"""
    
    print(f"\n{'='*70}")
    print(f"  📊 GENERATING SEQUENCING (5 LEVELS + CUTOUTS): {pack_code}")
    print(f"  Theme: {theme_name}")
    print(f"  Evidence-Based Progression - Small Wins Studio")
    print(f"{'='*70}\n")
    
    images_path = Path(images_folder)
    if not images_path.exists():
        print(f"❌ Error: Folder '{images_folder}' not found!")
        return False
    
    # Load PCS symbol images in story order
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
        print(f"❌ Missing PCS symbol images: {', '.join(missing_images)}")
        return False
    
    if len(loaded_images) != 11:
        print(f"❌ Need exactly 11 PCS images, found {len(loaded_images)}")
        return False
    
    # Load real photograph images for Level 2
    real_images = []
    real_images_path = Path("assets/themes/brown_bear/real_images")
    
    if real_images_path.exists():
        print(f"📷 Loading real photographs from {real_images_path}...")
        real_missing = []
        
        for char in STORY_SEQUENCE:
            real_filename = REAL_IMAGE_MAPPING.get(char)
            if real_filename:
                real_file = real_images_path / real_filename
                if real_file.exists():
                    img = Image.open(real_file)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    real_images.append(img)
                else:
                    real_missing.append(f"{char} -> {real_filename}")
                    # Fallback to PCS symbol if real image missing
                    real_images.append(loaded_images[len(real_images)])
        
        if real_missing:
            print(f"⚠️  Some real images not found (using PCS fallback): {', '.join(real_missing)}")
        else:
            print(f"   ✅ All 11 real photographs loaded successfully\n")
    else:
        print(f"⚠️  Real images folder not found: {real_images_path}")
        print(f"   Using PCS symbols for Level 2 as fallback\n")
        real_images = loaded_images.copy()
    
    output_folder = Path("OUTPUT")
    output_folder.mkdir(exist_ok=True)
    
    print(f"📝 Pack Details:")
    print(f"   Code: {pack_code}")
    print(f"   Theme: {theme_name}")
    print(f"   Story Characters: {', '.join(DISPLAY_NAMES[c] for c in STORY_SEQUENCE)}\n")
    
    print(f"📄 Creating pages...\n")
    
    saved_pages = []
    total_pages = 11  # 5 levels + 5 cutout pages + storage labels
    
    # Level 1: Color PCS symbol watermarks (Orange)
    print(f"   Level 1: Color Symbol Hints - {LEVEL_1_ORANGE}...")
    page1 = create_sequencing_page(loaded_images, real_images, 1, pack_code, theme_name, 1, total_pages)
    saved_pages.append(page1)
    
    # Level 2: Real photo watermarks (Blue)
    print(f"   Level 2: Real Photo Hints - {LEVEL_2_BLUE}...")
    page2 = create_sequencing_page(loaded_images, real_images, 2, pack_code, theme_name, 2, total_pages)
    saved_pages.append(page2)
    
    # Level 3: B&W PCS symbols (Green)
    print(f"   Level 3: B&W Symbols - {LEVEL_3_GREEN}...")
    page3 = create_sequencing_page(loaded_images, real_images, 3, pack_code, theme_name, 3, total_pages)
    saved_pages.append(page3)
    
    # Level 4: Text labels only (Purple)
    print(f"   Level 4: Text Labels Only - {LEVEL_4_PURPLE}...")
    page4 = create_sequencing_page(loaded_images, real_images, 4, pack_code, theme_name, 4, total_pages)
    saved_pages.append(page4)
    
    # Level 5: No help - blank boxes (Red)
    print(f"   Level 5: No Help (Independence) - {LEVEL_5_RED}...")
    page5 = create_sequencing_page(loaded_images, real_images, 5, pack_code, theme_name, 5, total_pages)
    saved_pages.append(page5)
    
    # Cutout pieces - one page for each level (5 pages total)
    print(f"   Level 1 Cutouts (Color Symbols) - {LEVEL_1_ORANGE}...")
    cutout1 = create_cutout_page(loaded_images, real_images, pack_code, theme_name, 1, 6, 11)
    saved_pages.append(cutout1)
    
    print(f"   Level 2 Cutouts (Real Photos) - {LEVEL_2_BLUE}...")
    cutout2 = create_cutout_page(loaded_images, real_images, pack_code, theme_name, 2, 7, 11)
    saved_pages.append(cutout2)
    
    print(f"   Level 3 Cutouts (B&W for Coloring) - {LEVEL_3_GREEN}...")
    cutout3 = create_cutout_page(loaded_images, real_images, pack_code, theme_name, 3, 8, 11)
    saved_pages.append(cutout3)
    
    print(f"   Level 4 Cutouts (Text Only) - {LEVEL_4_PURPLE}...")
    cutout4 = create_cutout_page(loaded_images, real_images, pack_code, theme_name, 4, 9, 11)
    saved_pages.append(cutout4)
    
    print(f"   Level 5 Cutouts (Blank) - {LEVEL_5_RED}...")
    cutout5 = create_cutout_page(loaded_images, real_images, pack_code, theme_name, 5, 10, 11)
    saved_pages.append(cutout5)
    
    print(f"\n   ✅ 10 pages generated (5 levels + 5 cutout pages)\n")
    
    # Create PDF
    print(f"📄 Creating PDF...")
    pdf_path = f"OUTPUT/{pack_code}_Sequencing_5Levels.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)  # Portrait orientation (8.5" × 11")
    
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
    print(f"  ✨ SUCCESS! 5-Level Sequencing pack generated")
    print(f"  © 2025 Small Wins Studio")
    print(f"  📄 Total pages: 11 (5 activity levels + 5 cutout pages + storage labels)")
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
