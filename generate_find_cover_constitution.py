"""
Find and Cover Generator - Constitution Design System
Small Wins Studio

Generates Find and Cover activity sheets using the design system from the Matching product.
Uses Brown Bear theme icons with level-based color coding and professional design standards.

OUTPUT STRUCTURE (15 pages per PDF):
- Pages 1-4: Level 1 (Target + 1 distractor) - Easiest
- Pages 5-8: Level 2 (Target + 2 distractors) - Intermediate  
- Pages 9-12: Level 3 (Target + 3 distractors) - Advanced
- Pages 13-15: Storage Labels (one per level)

Features:
- 3 difficulty levels with color-coded accent stripes
- 4×4 grid (16 cells) with varying target/distractor ratios
- Professional folder-style storage labels
- Both COLOR and BW versions
- Comic Sans MS fonts
- Light blue page borders
- Rounded corners throughout
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import os
import hashlib
import time

# Try to register Comic Sans MS font, fallback to Helvetica
try:
    pdfmetrics.registerFont(TTFont('ComicSans', 'Comic Sans MS'))
    pdfmetrics.registerFont(TTFont('ComicSans-Bold', 'Comic Sans MS Bold'))
    FONT_TITLE = 'ComicSans-Bold'
    FONT_SUBTITLE = 'ComicSans'
    FONT_BODY = 'ComicSans'
except:
    FONT_TITLE = 'Helvetica-Bold'
    FONT_SUBTITLE = 'Helvetica'
    FONT_BODY = 'Helvetica'

# Page dimensions
PAGE_WIDTH = 8.5 * inch
PAGE_HEIGHT = 11 * inch

# Colors
COLOR_PAGE_BORDER = HexColor('#A0C4E8')  # Light blue
COLOR_NAVY = HexColor('#1E3A5F')  # Navy for boxes

# Level-based accent colors (3 levels for Find and Cover)
LEVEL_COLORS = {
    1: HexColor('#F4A259'),  # Orange - Beginner
    2: HexColor('#4A90E2'),  # Blue - Intermediate
    3: HexColor('#7BC47F')   # Green - Advanced
}

# Grayscale values for BW mode
LEVEL_GRAYS = {
    1: 0.6,  # Light gray
    2: 0.5,  # Medium-light gray
    3: 0.4   # Medium gray
}

def get_level_color(level, mode='color'):
    """Get the accent stripe color for a given level."""
    if mode == 'bw':
        gray_value = LEVEL_GRAYS.get(level, 0.5)
        return HexColor(f'#{int(gray_value*255):02x}{int(gray_value*255):02x}{int(gray_value*255):02x}')
    return LEVEL_COLORS.get(level, HexColor('#F4A259'))

def hex_to_grayscale(hex_color):
    """Convert hex color to grayscale."""
    if isinstance(hex_color, str):
        hex_color = HexColor(hex_color)
    # Use luminosity method
    r, g, b = hex_color.red, hex_color.green, hex_color.blue
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    return HexColor(f'#{int(gray*255):02x}{int(gray*255):02x}{int(gray*255):02x}')

def enhance_for_printing(img, mode='color'):
    """Enhance image for printing (add slight contrast boost)."""
    if mode == 'bw':
        # Convert to grayscale
        if img.mode != 'L':
            img = img.convert('L')
    return img

def get_temp_filename(img, prefix, mode, suffix=""):
    """Generate unique temp filename based on image hash."""
    img_hash = hashlib.md5(img.tobytes()).hexdigest()[:12]
    return f"/tmp/{prefix}_{img_hash}_{mode}_{suffix}.png"

def draw_page_border(c, mode='color'):
    """Draw light blue page border."""
    border_color = COLOR_PAGE_BORDER if mode == 'color' else hex_to_grayscale(COLOR_PAGE_BORDER)
    c.setStrokeColor(border_color)
    c.setLineWidth(3)
    c.roundRect(0.25*inch, 0.25*inch, PAGE_WIDTH - 0.5*inch, PAGE_HEIGHT - 0.5*inch, 0.1*inch)

def draw_accent_stripe(c, level, mode='color'):
    """Draw accent stripe at top of page."""
    stripe_height = 1.0 * inch
    stripe_y = PAGE_HEIGHT - 0.35*inch - stripe_height
    
    accent_color = get_level_color(level, mode)
    
    c.setFillColor(accent_color)
    c.setStrokeColor(accent_color)
    c.roundRect(0.4*inch, stripe_y, PAGE_WIDTH - 0.8*inch, stripe_height, 0.1*inch, fill=1, stroke=0)

def draw_title_subtitle(c, level, mode='color'):
    """Draw title and subtitle centered in accent stripe."""
    stripe_height = 1.0 * inch
    stripe_y = PAGE_HEIGHT - 0.35*inch - stripe_height
    accent_y = stripe_y
    accent_height = stripe_height
    
    # Title
    c.setFont(FONT_TITLE, 36)
    c.setFillColor(HexColor('#FFFFFF'))
    title_text = "Find and Cover"
    title_width = c.stringWidth(title_text, FONT_TITLE, 36)
    title_x = (PAGE_WIDTH - title_width) / 2
    title_y = accent_y + accent_height / 2 + 5
    c.drawString(title_x, title_y, title_text)
    
    # Subtitle
    c.setFont(FONT_SUBTITLE, 28)
    subtitle_text = "Brown Bear"
    subtitle_width = c.stringWidth(subtitle_text, FONT_SUBTITLE, 28)
    subtitle_x = (PAGE_WIDTH - subtitle_width) / 2
    subtitle_y = title_y - 30
    c.drawString(subtitle_x, subtitle_y, subtitle_text)

def draw_footer(c, level, page_num, mode='color'):
    """Draw 2-line footer."""
    footer_y = 0.4 * inch
    
    # Line 1
    c.setFont(FONT_BODY, 9)
    c.setFillColor(HexColor('#000000'))
    line1 = f"Find and Cover – Level {level} | BB03 | Page {page_num}"
    line1_width = c.stringWidth(line1, FONT_BODY, 9)
    c.drawString((PAGE_WIDTH - line1_width) / 2, footer_y + 10, line1)
    
    # Line 2
    c.setFillColor(HexColor('#999999'))
    line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    line2_width = c.stringWidth(line2, FONT_BODY, 9)
    c.drawString((PAGE_WIDTH - line2_width) / 2, footer_y, line2)

def load_brown_bear_icons():
    """Load all 12 Brown Bear theme icons."""
    icons_dir = "/home/runner/work/small-wins-automation/small-wins-automation/assets/themes/brown_bear/icons"
    
    icon_files = {
        "Black Sheep": "black_sheep.png",
        "Blue Horse": "blue_horse.png",
        "Brown Bear": "brown_bear.png",
        "Green Frog": "green_frog.png",
        "Purple Cat": "purple_cat.png",
        "Red Bird": "red_bird.png",
        "White Dog": "white_dog.png",
        "Yellow Duck": "yellow_duck.png",
        "Children": "children.png",
        "Goldfish": "goldfish.png",
        "Eyes": "see.png",  # Renamed from "See"
        "Teacher": "teacher.png"
    }
    
    icons = []
    for name, filename in icon_files.items():
        filepath = os.path.join(icons_dir, filename)
        if os.path.exists(filepath):
            try:
                img = Image.open(filepath)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                icons.append((name, img, filepath))
            except Exception as e:
                print(f"Warning: Could not load {filename}: {e}")
    
    return icons

def generate_find_cover_page(c, target_icon, all_icons, level, page_num, mode='color'):
    """Generate a single Find and Cover activity page with 4×4 grid."""
    target_name, target_img, _ = target_icon
    
    # Draw page elements
    draw_page_border(c, mode)
    draw_accent_stripe(c, level, mode)
    draw_title_subtitle(c, level, mode)
    
    # Instruction line
    instruction_y = PAGE_HEIGHT - 1.52*inch
    c.setFont(FONT_BODY, 14)
    c.setFillColor(HexColor('#000000'))
    instruction_text = f"Find the {target_name}"
    instruction_width = c.stringWidth(instruction_text, FONT_BODY, 14)
    c.drawString((PAGE_WIDTH - instruction_width) / 2, instruction_y, instruction_text)
    
    # Target box
    target_size = 0.9 * inch
    target_x = (PAGE_WIDTH - target_size) / 2
    target_y = PAGE_HEIGHT - 2.57*inch
    
    # Draw target box with navy border
    c.setStrokeColor(COLOR_NAVY if mode == 'color' else hex_to_grayscale(COLOR_NAVY))
    c.setLineWidth(4)
    c.setFillColor(HexColor('#FFFFFF'))
    c.roundRect(target_x, target_y, target_size, target_size, 0.12*inch, fill=1, stroke=1)
    
    # Place target icon
    display_img = target_img.copy()
    display_img = enhance_for_printing(display_img, mode)
    temp_target = get_temp_filename(display_img, "target", mode, target_name)
    display_img.save(temp_target, 'PNG')
    
    img_size = target_size * 0.92
    img_x = target_x + (target_size - img_size) / 2
    img_y = target_y + (target_size - img_size) / 2
    c.drawImage(temp_target, img_x, img_y, img_size, img_size, mask='auto')
    
    # 4×4 Grid
    grid_size = 4
    total_cells = 16
    
    # Get distractors (other icons)
    distractors = [icon for icon in all_icons if icon[0] != target_name]
    
    # Create cell assignments based on level
    import random
    cell_icons = []
    
    if level == 1:
        # Level 1: Target 10x, 1 distractor 6x
        cell_icons = [target_icon] * 10
        if distractors:
            cell_icons.extend([distractors[0]] * 6)
    elif level == 2:
        # Level 2: Target 8x, 2 distractors 4x each
        cell_icons = [target_icon] * 8
        if len(distractors) >= 2:
            cell_icons.extend([distractors[0]] * 4)
            cell_icons.extend([distractors[1]] * 4)
    elif level == 3:
        # Level 3: Target 6x, 3 distractors share remaining 10
        cell_icons = [target_icon] * 6
        if len(distractors) >= 3:
            for _ in range(10):
                cell_icons.append(random.choice(distractors[:3]))
    
    # Shuffle
    random.shuffle(cell_icons)
    
    # Calculate grid layout
    grid_start_y = PAGE_HEIGHT - 5.1*inch
    available_width = PAGE_WIDTH * 0.85
    cell_size = available_width / grid_size
    grid_width = cell_size * grid_size
    grid_start_x = (PAGE_WIDTH - grid_width) / 2
    
    # Draw grid cells
    steel_blue = HexColor('#5B7AA0') if mode == 'color' else HexColor('#999999')
    
    for row in range(grid_size):
        for col in range(grid_size):
            idx = row * grid_size + col
            if idx >= len(cell_icons):
                break
            
            cell_icon = cell_icons[idx]
            icon_name, icon_img, _ = cell_icon
            
            x = grid_start_x + (col * cell_size)
            y = grid_start_y - (row * cell_size)
            
            # Draw cell
            c.setStrokeColor(steel_blue)
            c.setLineWidth(2)
            c.setFillColor(HexColor('#FFFFFF'))
            c.rect(x, y, cell_size, cell_size, fill=1, stroke=1)
            
            # Place icon
            display_cell = icon_img.copy()
            display_cell = enhance_for_printing(display_cell, mode)
            temp_cell = get_temp_filename(display_cell, f"cell{idx}", mode, icon_name)
            display_cell.save(temp_cell, 'PNG')
            
            padding = cell_size * 0.08
            icon_size = cell_size - (2 * padding)
            icon_x = x + padding
            icon_y = y + padding
            c.drawImage(temp_cell, icon_x, icon_y, icon_size, icon_size, mask='auto')
    
    # Draw navy border around entire grid
    c.setStrokeColor(COLOR_NAVY if mode == 'color' else hex_to_grayscale(COLOR_NAVY))
    c.setLineWidth(4)
    c.rect(grid_start_x, grid_start_y - (grid_size * cell_size), grid_width, grid_size * cell_size, fill=0, stroke=1)
    
    draw_footer(c, level, page_num, mode)

def generate_storage_labels(c, icons, level, page_num, mode='color'):
    """Generate professional folder-style storage labels page."""
    draw_page_border(c, mode)
    draw_accent_stripe(c, level, mode)
    
    # Title
    c.setFont(FONT_TITLE, 36)
    c.setFillColor(HexColor('#FFFFFF'))
    stripe_y = PAGE_HEIGHT - 0.08*inch - 1.0*inch
    
    level_names = {1: "Level 1", 2: "Level 2", 3: "Level 3"}
    level_skills = {
        1: "2-Choice Visual Scanning (1 vs 1)",
        2: "3-Choice Visual Scanning (1 vs 2)",
        3: "4-Choice Visual Scanning (1 vs 3)"
    }
    
    title_text = f"Storage Labels - {level_names[level]}"
    title_width = c.stringWidth(title_text, FONT_TITLE, 36)
    c.drawString((PAGE_WIDTH - title_width) / 2, stripe_y + 0.5*inch, title_text)
    
    # Skill description
    c.setFont(FONT_BODY, 12)
    skill_text = level_skills[level]
    skill_width = c.stringWidth(skill_text, FONT_BODY, 12)
    c.drawString((PAGE_WIDTH - skill_width) / 2, stripe_y + 0.2*inch, skill_text)
    
    # 2×2 grid of folder labels (4 icons)
    label_width = 2.6 * inch
    label_height = 1.9 * inch
    spacing_x = 0.3 * inch
    spacing_y = 0.25 * inch
    
    total_width = (label_width * 2) + spacing_x
    start_x = (PAGE_WIDTH - total_width) / 2
    start_y = PAGE_HEIGHT - 3.0*inch
    
    pale_blue = HexColor('#E3F2FD') if mode == 'color' else HexColor('#F0F0F0')
    med_blue = HexColor('#90CAF9') if mode == 'color' else HexColor('#CCCCCC')
    dark_blue = HexColor('#1976D2') if mode == 'color' else HexColor('#000000')
    
    # Use first 4 icons
    for idx, (name, img, _) in enumerate(icons[:4]):
        row = idx // 2
        col = idx % 2
        
        label_x = start_x + col * (label_width + spacing_x)
        label_y = start_y - row * (label_height + spacing_y)
        
        # Draw label box
        c.setFillColor(pale_blue)
        c.setStrokeColor(med_blue)
        c.setLineWidth(2)
        c.roundRect(label_x, label_y, label_width, label_height, 0.1*inch, fill=1, stroke=1)
        
        # Icon name
        c.setFont(FONT_TITLE, 14)
        c.setFillColor(dark_blue)
        name_width = c.stringWidth(name, FONT_TITLE, 14)
        c.drawString(label_x + (label_width - name_width) / 2, label_y + label_height - 0.3*inch, name)
        
        # Pack code
        c.setFont(FONT_BODY, 9)
        pack_text = f"Find & Cover {level_names[level]} - BB03"
        pack_width = c.stringWidth(pack_text, FONT_BODY, 9)
        c.drawString(label_x + (label_width - pack_width) / 2, label_y + label_height - 0.5*inch, pack_text)
        
        # Icon image
        display_img = img.copy()
        display_img = enhance_for_printing(display_img, mode)
        temp_label = get_temp_filename(display_img, f"label{idx}", mode, name)
        display_img.save(temp_label, 'PNG')
        
        icon_size = 0.8 * inch
        icon_x = label_x + (label_width - icon_size) / 2
        icon_y = label_y + 0.5*inch
        c.drawImage(temp_label, icon_x, icon_y, icon_size, icon_size, mask='auto')
        
        # Icon name at bottom
        c.setFont(FONT_BODY, 10)
        c.setFillColor(HexColor('#000000'))
        bottom_name_width = c.stringWidth(name, FONT_BODY, 10)
        c.drawString(label_x + (label_width - bottom_name_width) / 2, label_y + 0.2*inch, name)
    
    # Instructions
    c.setFont(FONT_BODY, 11)
    c.setFillColor(HexColor('#666666'))
    instr_y = start_y - 2 * (label_height + spacing_y) - 0.4*inch
    instr_text = "Cut out labels and attach to folders. Teacher provides chips/counters for covering."
    instr_width = c.stringWidth(instr_text, FONT_BODY, 11)
    c.drawString((PAGE_WIDTH - instr_width) / 2, instr_y, instr_text)
    
    draw_footer(c, level, page_num, mode)

def generate_find_cover_pdf(output_dir="/home/runner/work/small-wins-automation/small-wins-automation/samples/brown_bear/find_cover", mode='color'):
    """Generate complete Find and Cover PDF for all 3 levels (15 pages total)."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Load icons
    icons = load_brown_bear_icons()
    print(f"Loaded {len(icons)} Brown Bear icons")
    
    # Use first 4 icons for the activities
    activity_icons = icons[:4]
    print(f"Using 4 icons for activities: {', '.join([name for name, _, _ in activity_icons])}")
    
    # Create PDF
    filename = f"brown_bear_find_cover_{mode}.pdf"
    output_path = os.path.join(output_dir, filename)
    c = canvas.Canvas(output_path, pagesize=letter)
    
    page_num = 0
    
    # Generate pages organized by level (3 levels)
    for level in [1, 2, 3]:
        level_names = {1: "Level 1 (1 vs 1)", 2: "Level 2 (1 vs 2)", 3: "Level 3 (1 vs 3)"}
        print(f"\nGenerating {level_names[level]}...")
        
        # Generate activity pages for all 4 icons (4 pages per level)
        for target_icon in activity_icons:
            page_num += 1
            target_name = target_icon[0]
            print(f"  Page {page_num}: Find the {target_name}")
            generate_find_cover_page(c, target_icon, icons, level, page_num, mode)
            c.showPage()
    
    # Generate storage labels for all 3 levels (3 pages)
    for level in [1, 2, 3]:
        page_num += 1
        print(f"  Page {page_num}: Storage labels - Level {level}")
        generate_storage_labels(c, activity_icons, level, page_num, mode)
        c.showPage()
    
    c.save()
    print(f"\n✓ Generated {mode.upper()} PDF: {output_path}")
    print(f"  Total pages: {page_num}")
    
    return output_path

if __name__ == "__main__":
    print("=" * 60)
    print("Find and Cover Generator - Constitution Design System")
    print("Small Wins Studio")
    print("=" * 60)
    print("\nGenerating Find and Cover activity sheets...")
    print("Theme: Brown Bear (4 icons for activities)")
    print("Levels: 1-3 (color-coded)")
    print("Output: COLOR and BW versions")
    print()
    
    # Generate both COLOR and BW versions
    color_path = generate_find_cover_pdf(mode='color')
    bw_path = generate_find_cover_pdf(mode='bw')
    
    print("\n" + "=" * 60)
    print("✓ GENERATION COMPLETE!")
    print("=" * 60)
    print(f"\nFiles created:")
    print(f"  1. {color_path}")
    print(f"  2. {bw_path}")
    print("\nEach PDF contains 15 pages:")
    print("  Level 1 (1 vs 1): Pages 1-4 (Target 10x, 1 distractor 6x)")
    print("  Level 2 (1 vs 2): Pages 5-8 (Target 8x, 2 distractors 4x each)")
    print("  Level 3 (1 vs 3): Pages 9-12 (Target 6x, 3 distractors share remaining)")
    print("  Storage Labels: Pages 13-15 (one per level)")
    print("\nSkills Practiced:")
    print("  • Visual scanning & discrimination")
    print("  • Attention to detail")
    print("  • Focus & concentration")
    print("  • Counting")
    print("\nReady for classroom use!")
    print("Teacher provides chips/counters for covering matching icons.")
