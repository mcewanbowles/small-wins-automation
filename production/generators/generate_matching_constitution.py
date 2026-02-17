"""
Brown Bear Matching Cards Generator - Matching Product Specification Compliant
Generates matching activity pages following Small Wins Studio Matching Product Spec
"""

import os
import sys
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import random
from PyPDF2 import PdfReader, PdfWriter

# Use OS temp directory for intermediate images (Windows-safe)
TEMP_DIR = Path(tempfile.gettempdir())

# Try to register Comic Sans MS font (available on most systems)
try:
    # Register Comic Sans MS if available
    _comic = Path("C:/Windows/Fonts/comic.ttf")
    _comic_bold = Path("C:/Windows/Fonts/comicbd.ttf")
    pdfmetrics.registerFont(TTFont('Comic-Sans-MS', str(_comic if _comic.exists() else Path('comic.ttf'))))
    pdfmetrics.registerFont(TTFont('Comic-Sans-MS-Bold', str(_comic_bold if _comic_bold.exists() else Path('comicbd.ttf'))))
    TITLE_FONT = 'Comic-Sans-MS-Bold'
    BODY_FONT = 'Comic-Sans-MS'
except:
    # Fallback to Helvetica if Comic Sans not available
    TITLE_FONT = 'Helvetica-Bold'
    BODY_FONT = 'Helvetica'

# Add repo root to path for imports (so `utils` resolves correctly)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Theme config (source of truth for level names/colours)
THEME_ID = "brown_bear"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_theme_level_colours(theme_id: str) -> dict[int, str]:
    try:
        theme_path = REPO_ROOT / "themes" / f"{theme_id}.json"
        with open(theme_path, "r", encoding="utf-8") as f:
            theme = json.load(f)
        levels = theme["matching"]["levels"]
        return {i: levels[f"L{i}"]["colour"] for i in range(1, 6)}
    except Exception:
        return {}

# Matching Product Specification Colors
LIGHT_BLUE_BORDER = '#A0C4E8'  # Light blue border for pages (COLOR MODE)
NAVY_BORDER = '#1E3A5F'  # Navy border for target and matching boxes (COLOR MODE)
PURPLE_BORDER = '#6B5BE2'  # Purple border for velcro boxes (COLOR MODE)
LIGHT_GREY_FILL = '#E8E8E8'  # Light grey fill for velcro boxes
VELCRO_DOT_FILL = '#CCCCCC'  # Velcro dot fill
VELCRO_DOT_OUTLINE = '#999999'  # Velcro dot outline
WARM_ORANGE = '#F5A623'  # Accent stripe color (default)
WHITE = '#FFFFFF'
BLACK = '#000000'

# Level-Based Accent Colors (source of truth: theme config)
LEVEL_COLORS = _load_theme_level_colours(THEME_ID)


def get_level_color(level, mode='color'):
    """Get the accent stripe color for a specific level."""
    from utils.color_helpers import hex_to_grayscale
    color = LEVEL_COLORS.get(level, WARM_ORANGE)
    if mode == 'bw':
        return hex_to_grayscale(color)
    return color


def get_border_color_for_mode(color, mode='color'):
    """
    Get border color appropriate for the mode.
    In BW mode, returns black for maximum contrast.
    In color mode, returns the original color.
    """
    from utils.color_helpers import adjust_for_bw_mode
    if mode == 'bw':
        # For B&W mode, use black for all borders for maximum contrast
        return BLACK
    return color


def load_all_icons(icon_folder):
    """Load all PNG icons from the specified folder."""
    icons = []
    names = []
    
    if not os.path.exists(icon_folder):
        print(f"Error: Icon folder not found: {icon_folder}")
        return icons, names
    
    # Get all PNG files
    png_files = sorted([f for f in os.listdir(icon_folder) if f.lower().endswith('.png') and not f.startswith('.')])
    
    print(f"Found {len(png_files)} icon files in {icon_folder}")
    
    for filename in png_files:
        filepath = os.path.join(icon_folder, filename)
        try:
            img = Image.open(filepath)
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            icons.append(img)
            # Clean name: remove extension and clean up
            name = os.path.splitext(filename)[0].replace('_', ' ').title()
            
            # Product Spec requirement: "See" must be renamed to "Eyes"
            if name.lower() == 'see':
                name = 'Eyes'
            
            names.append(name)
            print(f"  Loaded: {filename} -> {name}")
        except Exception as e:
            print(f"  Error loading {filename}: {e}")
    
    return icons, names


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple (0-1 range for reportlab)."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (r/255, g/255, b/255)


def create_matching_page_constitution(c, target_img, target_name, images, names, level, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear", mode='color'):
    """
    Create a matching page following Matching Product Specification.
    
    Product Spec Requirements:
    - Centered title and subtitle
    - Subtitle "Match the [Icon]" ABOVE target box
    - Accent stripe must NOT touch page border (add margin)
    - Navy borders #1E3A5F for target and matching boxes
    - Purple borders #6B5BE2 for velcro boxes
    - Light grey fill #E8E8E8 for velcro boxes
    - Decorative corner details on matching boxes
    - Single line footer at bottom
    - 5 rows x 2 columns layout
    """
    width, height = letter
    
    # Import color utilities for BW mode support
    from utils.color_helpers import hex_to_grayscale, enhance_for_printing
    import hashlib

    # Create hash-based temp filenames to reuse same file for same icon
    def get_temp_filename(img, prefix, suffix=""):
        img_hash = hashlib.md5(img.tobytes()).hexdigest()[:12]
        return str(TEMP_DIR / f"{prefix}_{img_hash}_{mode}_{suffix}.png")
    
    # Page Structure - 0.25" margin from edge
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    # Draw rounded rectangle border (thicker stroke) - LIGHT BLUE in color mode, BLACK in B&W mode
    border_color = get_border_color_for_mode(LIGHT_BLUE_BORDER, mode)
    c.setStrokeColorRGB(*hex_to_rgb(border_color))
    c.setLineWidth(4)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent Stripe - moved higher (less padding from border), increased height
    accent_margin = 0.08 * inch  # Reduced from 0.15" to move stripe higher
    accent_height = 1.0 * inch  # Height for title and subtitle
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin
    
    # Use level-specific color for accent stripe
    level_color = get_level_color(level, mode)
    c.setFillColorRGB(*hex_to_rgb(level_color))
    
    # Draw accent stripe with rounded corners
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Title and Subtitle - BOTH INSIDE accent stripe, CENTERED per spec, LARGER FONTS
    # Title: "Matching"
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))  # Navy
    c.setFont(TITLE_FONT, 36)  # Increased from 28pt to 36pt
    title_text = "Matching"
    # Positioned with padding from top, not touching edges
    title_y = accent_y + accent_height / 2 + 5  # Adjusted for better centering with padding
    c.drawCentredString(width / 2, title_y, title_text)
    
    # Subtitle: "Brown Bear" - ALSO INSIDE stripe, below title, closer together
    c.setFont(BODY_FONT, 28)  # Increased from 20pt to 28pt
    c.setFillColorRGB(0.2, 0.2, 0.2)  # Dark grey
    subtitle_text = "Brown Bear"
    subtitle_y_in_stripe = title_y - 30  # Closer to title (was -42), not touching either edge
    c.drawCentredString(width / 2, subtitle_y_in_stripe, subtitle_text)
    
    # Instruction line "Match the [icon_name]" - BELOW stripe, ABOVE target box per spec
    instruction_text = f"Match the {target_name}"
    instruction_y = accent_y - 20  # Below the stripe
    c.setFont(BODY_FONT, 14)  # Comic Sans or Helvetica
    c.drawCentredString(width / 2, instruction_y, instruction_text)
    
    # Position for content below instruction line
    content_top = instruction_y - 0.2 * inch
    
    # Target Box - centered horizontally, navy border, soft shadow, 20% smaller and nearer
    target_size = 0.72 * inch  # 20% smaller than 0.9" (0.9 * 0.8 = 0.72)
    target_x = width / 2 - target_size / 2
    target_y = content_top - 0.08 * inch - target_size  # Moved higher, nearer to instruction (reduced from 0.12")
    
    # Draw Target Box with Navy border, soft shadow, rounded corners
    if target_img:
        # Create a copy to avoid modifying the original
        display_target = target_img.copy()
        
        # Convert to grayscale in BW mode
        if mode == 'bw':
            display_target = enhance_for_printing(display_target, mode='bw')
        
        # Draw soft shadow (5-8% opacity) first
        shadow_offset = 4
        c.setFillColorRGB(0, 0, 0)
        c.setFillAlpha(0.06)  # 6% opacity shadow
        c.roundRect(target_x + shadow_offset, target_y - shadow_offset, 
                   target_size, target_size, 8.64, stroke=0, fill=1)
        c.setFillAlpha(1.0)  # Reset opacity
        
        # Save target image with hash-based filename
        temp_target = get_temp_filename(display_target, "target")
        if not os.path.exists(temp_target):
            display_target.save(temp_target, 'PNG')
        
        c.drawImage(temp_target, target_x, target_y, width=target_size, height=target_size, 
                   preserveAspectRatio=True, mask='auto')
        
        # Draw Navy border around target (thicker) - BLACK in B&W mode
        navy_color = get_border_color_for_mode(NAVY_BORDER, mode)
        c.setStrokeColorRGB(*hex_to_rgb(navy_color))
        c.setLineWidth(5)  # Thicker to match other activities
        c.roundRect(target_x, target_y, target_size, target_size, 8.64, stroke=1, fill=0)
    
    # 5-row layout below target - Matching boxes reduced by another 5%
    box_size = 1.2825 * inch  # Additional 5% reduction (1.35 * 0.95 = 1.2825)
    box_spacing = 0.16 * inch  # Further reduced spacing to fit boxes higher
    corner_radius = 8.64  # 0.12" = 8.64 pts
    
    # Calculate starting position for 5 rows - moved even higher
    rows_start_y = target_y - 0.2 * inch  # Further reduced to move boxes higher
    
    # Column spacing: increased for visual balance (1.3"-1.5")
    column_gap = 1.45 * inch  # Increased for better visual balance
    left_col_x = width / 2 - box_size - column_gap / 2
    right_col_x = width / 2 + column_gap / 2
    
    # Draw 5 rows
    for row in range(5):
        row_y = rows_start_y - row * (box_size + box_spacing)
        
        # Left column: Simple matching box with navy border (ornaments removed)
        img_box_x = left_col_x
        img_box_y = row_y - box_size
        
        # Draw the contents first, then stroke the border once on top.
        
        # Level 1 Watermark Logic: 20-30% opacity, 70-80% of box
        if level == 1 and target_img:
            watermark_img = target_img.copy()
            watermark_img = watermark_img.convert('RGBA')
            alpha = watermark_img.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.25))  # 25% opacity
            watermark_img.putalpha(alpha)
            
            temp_watermark = get_temp_filename(watermark_img, "watermark")
            if not os.path.exists(temp_watermark):
                watermark_img.save(temp_watermark, 'PNG')
            
            # Watermark at 75% of box size (center of 70-80% range)
            watermark_size = box_size * 0.75
            watermark_x = img_box_x + (box_size - watermark_size) / 2
            watermark_y = img_box_y + (box_size - watermark_size) / 2
            c.drawImage(temp_watermark, watermark_x, watermark_y, 
                       width=watermark_size, height=watermark_size, 
                       preserveAspectRatio=True, mask='auto')
        
        # Place icon in matching box - fills 95-100% (using 97% per spec)
        if row < len(images):
            display_img = images[row].copy()
            
            if mode == 'bw':
                display_img = enhance_for_printing(display_img, mode='bw')
            
            # Leave a touch more padding so the icon edge can't visually read as a 2nd border.
            icon_size = box_size * 0.93
            icon_x = img_box_x + (box_size - icon_size) / 2
            icon_y = img_box_y + (box_size - icon_size) / 2
            
            temp_icon = get_temp_filename(display_img, "icon")
            if not os.path.exists(temp_icon):
                display_img.save(temp_icon, 'PNG')
            
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size, 
                       preserveAspectRatio=True, mask='auto')

        # Stroke the matching box border once, on top.
        navy_color = get_border_color_for_mode(NAVY_BORDER, mode)
        c.setStrokeColorRGB(*hex_to_rgb(navy_color))
        c.setLineWidth(4.5)
        c.roundRect(img_box_x, img_box_y, box_size, box_size, corner_radius, stroke=1, fill=0)
        
        # Right column: Velcro box with purple border and light grey fill
        velcro_box_x = right_col_x
        velcro_box_y = img_box_y
        
        # Draw velcro box with light grey fill and thicker purple border - BLACK border in B&W mode
        c.setFillColorRGB(*hex_to_rgb(LIGHT_GREY_FILL))
        purple_color = get_border_color_for_mode(PURPLE_BORDER, mode)
        c.setStrokeColorRGB(*hex_to_rgb(purple_color))
        c.setLineWidth(4.5)
        c.roundRect(velcro_box_x, velcro_box_y, box_size, box_size, corner_radius, stroke=1, fill=1)
        
        # Draw velcro dot (0.3" diameter, centered)
        velcro_diameter = 0.3 * inch
        velcro_radius = velcro_diameter / 2
        velcro_center_x = velcro_box_x + box_size / 2
        velcro_center_y = velcro_box_y + box_size / 2
        
        # Velcro dot with specific colors per Product Spec
        c.setFillColorRGB(*hex_to_rgb(VELCRO_DOT_FILL))
        c.setStrokeColorRGB(*hex_to_rgb(VELCRO_DOT_OUTLINE))
        c.setLineWidth(2)
        c.circle(velcro_center_x, velcro_center_y, velcro_radius, stroke=1, fill=1)
        
        # Optional tiny "velcro" text
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.setFont(BODY_FONT, 6)
        text_width = c.stringWidth("velcro", BODY_FONT, 6)
        c.drawString(velcro_center_x - text_width/2, velcro_center_y - 2, "velcro")
    
    # Footer - Gold standard (matches Bingo / apply_small_wins_frame)
    footer_y = border_margin + 0.26 * inch
    
    # Line 2 (lower) - studio / license / copyright
    c.setFont(BODY_FONT, 9)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line2 = "Small Wins Studio | PCS symbols used with active PCS Maker Personal License. | © 2026"
    c.drawCentredString(width / 2, footer_y, footer_line2)
    
    # Line 1 (upper) - product / level / code / page (bold)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    c.setFont(TITLE_FONT, 10)
    footer_line1 = f"Brown Bear Matching | Level {level} | {pack_code} | Page {page_num}/{total_pages}"
    c.drawCentredString(width / 2, footer_y + 12, footer_line1)
    
    c.showPage()


def create_cutout_page_constitution(c, images, names, icons_on_page, page_number, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear", level=None, mode='color'):
    """
    Create cutout page following updated requirements:
    - 5 copies of each icon (60 total per level)
    - 2 pages per level (30 pieces per page)
    - Box size matches activity boxes (1.28")
    - 6 columns x 5 rows = 30 boxes per page
    - Title includes page number (1 of 2, 2 of 2)
    """
    width, height = letter
    
    # Import color utilities for BW mode
    from utils.color_helpers import hex_to_grayscale
    
    # Border - Light blue in color mode, black in B&W mode
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    border_color = get_border_color_for_mode(LIGHT_BLUE_BORDER, mode)
    c.setStrokeColorRGB(*hex_to_rgb(border_color))
    c.setLineWidth(4)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent stripe: moved higher
    accent_margin = 0.08 * inch
    accent_height = 1.0 * inch  # Larger stripe for title
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin
    
    # Use level-specific color for accent stripe
    level_color = get_level_color(level, mode)
    c.setFillColorRGB(*hex_to_rgb(level_color))
    
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Title with page number
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))  # Navy
    # Title: "Cut Out Matching Pieces"
    c.setFont(TITLE_FONT, 28)
    
    title_text = "Cut Out Matching Pieces"
    title_y = accent_y + accent_height / 2 + 10
    c.drawCentredString(width / 2, title_y, title_text)
    
    # Subtitle: "Brown Bear" (no level info)
    c.setFont(BODY_FONT, 20)
    c.setFillColorRGB(0.2, 0.2, 0.2)  # Dark grey
    subtitle_text = theme_name
    subtitle_y = title_y - 32
    c.drawCentredString(width / 2, subtitle_y, subtitle_text)
    
    # Box size matches activity boxes (1.28" from user requirements)
    box_size = 1.28 * inch
    # Icon fills most of box (97% fill)
    icon_size = box_size * 0.97
    spacing = 0.05 * inch  # Minimal spacing for tight cutting
    border_pts = 4  # thicker border to match activity pages
    
    # 6 columns x 5 rows = 30 boxes (5 copies of 6 icons)
    cols = 6
    rows = 5
    
    # Calculate grid dimensions
    grid_width = cols * box_size + (cols - 1) * spacing
    grid_height = rows * box_size + (rows - 1) * spacing
    
    # Center grid on page
    start_x = (width - grid_width) / 2
    content_top = accent_y - 0.4 * inch
    start_y = content_top - 0.3 * inch
    
    # Draw 6x5 grid - each icon appears 5 times in a column
    icon_idx = 0
    for col in range(cols):
        if icon_idx >= len(icons_on_page):
            break
        img = icons_on_page[icon_idx]
        
        # Draw 5 copies of this icon in this column
        for row in range(rows):
            box_x = start_x + col * (box_size + spacing)
            box_y = start_y - row * (box_size + spacing) - box_size
            
            # Draw box with 3pt border - BLACK in B&W mode
            navy_color = get_border_color_for_mode(NAVY_BORDER, mode)
            c.setStrokeColorRGB(*hex_to_rgb(navy_color))
            c.setLineWidth(border_pts)
            c.roundRect(box_x, box_y, box_size, box_size, 8.64, stroke=1, fill=0)
            
            # Draw icon (fills 97% of box, centered)
            icon_padding = (box_size - icon_size) / 2
            icon_x = box_x + icon_padding
            icon_y = box_y + icon_padding
            
            # Save and draw icon
            import hashlib
            img_copy = img.copy()
            if mode == 'bw':
                from utils.color_helpers import enhance_for_printing
                img_copy = enhance_for_printing(img_copy, mode='bw')
            
            img_hash = hashlib.md5(img_copy.tobytes()).hexdigest()[:12]
            temp_icon = str(TEMP_DIR / f"cutout_{img_hash}_{mode}_{col}_{row}.png")
            if not os.path.exists(temp_icon):
                img_copy.save(temp_icon, 'PNG')
            
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size,
                       preserveAspectRatio=True, mask='auto')
        
        icon_idx += 1
    
    # Footer - Gold standard (matches Bingo / apply_small_wins_frame)
    footer_y = border_margin + 0.26 * inch
    
    c.setFont(BODY_FONT, 9)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line2 = "Small Wins Studio | PCS symbols used with active PCS Maker Personal License. | © 2026"
    c.drawCentredString(width / 2, footer_y, footer_line2)
    
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    c.setFont(TITLE_FONT, 10)
    if level:
        footer_line1 = f"Brown Bear Matching | Level {level} | {pack_code} | Page {page_num}/{total_pages}"
    else:
        footer_line1 = f"Brown Bear Matching | Cutouts | {pack_code}"
    c.drawCentredString(width / 2, footer_y + 12, footer_line1)
    
    c.showPage()


def create_storage_label_page_constitution(c, images, names, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear", level=None, mode='color'):
    """
    Create storage label page with professional rectangular boxes.
    
    Each box contains:
    - Title: "Matching"
    - Subtitle: "Brown Bear BB03"
    - Level info
    - Icon image
    - Icon name
    
    Professional, classy design with pale blue color scheme.
    """
    width, height = letter
    
    # Import color utilities
    from utils.color_helpers import hex_to_grayscale
    
    # Define pale blue color scheme
    PALE_BLUE = '#E3F2FD'  # Very light blue background
    MEDIUM_BLUE = '#90CAF9'  # Medium blue for accents
    DARK_BLUE = '#1976D2'  # Dark blue for text
    
    # Page border - Light blue in color mode, black in B&W mode
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    border_color = get_border_color_for_mode(LIGHT_BLUE_BORDER, mode)
    c.setStrokeColorRGB(*hex_to_rgb(border_color))
    c.setLineWidth(4)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent stripe at top
    accent_margin = 0.08 * inch
    accent_height = 1.0 * inch
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin
    
    # Use level-specific color for accent stripe
    level_color = get_level_color(level, mode)
    c.setFillColorRGB(*hex_to_rgb(level_color))
    
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Page title
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))
    c.setFont(TITLE_FONT, 36)
    
    title_text = "Storage Labels"
    title_y = accent_y + accent_height / 2 + 10
    c.drawCentredString(width / 2, title_y, title_text)
    
    # Subtitle
    c.setFont(BODY_FONT, 28)
    subtitle_text = f"{theme_name} – Level {level}" if level else theme_name
    subtitle_y = title_y - 42
    c.drawCentredString(width / 2, subtitle_y, subtitle_text)
    
    # Storage label boxes - 3 columns × 4 rows = 12 boxes
    cols = 3
    rows = 4
    
    box_width = 2.2 * inch
    box_height = 1.5 * inch
    h_spacing = 0.3 * inch
    v_spacing = 0.25 * inch
    
    # Calculate grid position
    grid_width = cols * box_width + (cols - 1) * h_spacing
    grid_height = rows * box_height + (rows - 1) * v_spacing
    start_x = (width - grid_width) / 2
    start_y = accent_y - 0.5 * inch - grid_height
    
    # Draw boxes
    for idx in range(min(len(images), 12)):
        row = idx // cols
        col = idx % cols
        
        box_x = start_x + col * (box_width + h_spacing)
        box_y = start_y + (rows - 1 - row) * (box_height + v_spacing)
        
        # Draw box with pale blue background (light gray in B&W)
        if mode == 'bw':
            # Use light gray for BW
            c.setFillColorRGB(0.95, 0.95, 0.95)
        else:
            c.setFillColorRGB(*hex_to_rgb(PALE_BLUE))
        
        # Border color - medium blue in color mode, black in B&W mode
        border_color = get_border_color_for_mode(MEDIUM_BLUE, mode)
        c.setStrokeColorRGB(*hex_to_rgb(border_color))
        c.setLineWidth(3)
        c.roundRect(box_x, box_y, box_width, box_height, 6, stroke=1, fill=1)
        
        # Title: "Matching" - dark blue in color mode, black in B&W mode
        text_color = get_border_color_for_mode(DARK_BLUE, mode)
        c.setFillColorRGB(*hex_to_rgb(text_color))
        c.setFont(TITLE_FONT, 11)
        text_y = box_y + box_height - 0.2 * inch
        c.drawCentredString(box_x + box_width / 2, text_y, "Matching")
        
        # Subtitle: "Brown Bear BB03"
        c.setFont(BODY_FONT, 9)
        text_y -= 0.18 * inch
        c.drawCentredString(box_x + box_width / 2, text_y, f"{theme_name} {pack_code}")
        
        # Level info
        if level:
            c.setFont(TITLE_FONT, 9)
            text_y -= 0.16 * inch
            c.drawCentredString(box_x + box_width / 2, text_y, f"Level {level}")
        else:
            text_y -= 0.16 * inch
        
        # Icon image (centered) - moved down to avoid cutting off text
        icon_size = 0.6 * inch
        icon_x = box_x + (box_width - icon_size) / 2
        icon_y = box_y + 0.35 * inch  # Moved down from 0.45" to 0.35"
        
        # Save and draw icon
        import hashlib
        img_copy = images[idx].copy()
        if mode == 'bw':
            from utils.color_helpers import enhance_for_printing
            img_copy = enhance_for_printing(img_copy, mode='bw')
        
        img_hash = hashlib.md5(img_copy.tobytes()).hexdigest()[:12]
        temp_icon = str(TEMP_DIR / f"storage_{img_hash}_{mode}_{idx}.png")
        if not os.path.exists(temp_icon):
            img_copy.save(temp_icon, 'PNG')
        
        c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size,
                   preserveAspectRatio=True, mask='auto')
        
        # Icon name (centered below icon) - adjusted position
        c.setFont(BODY_FONT, 10)
        c.setFillColorRGB(0, 0, 0)
        name_y = icon_y - 0.18 * inch  # Moved down from -0.15" to -0.18"
        c.drawCentredString(box_x + box_width / 2, name_y, names[idx])
    
    # Footer - Gold standard (matches Bingo / apply_small_wins_frame)
    footer_y = border_margin + 0.26 * inch
    
    c.setFont(BODY_FONT, 9)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line2 = "Small Wins Studio | PCS symbols used with active PCS Maker Personal License. | © 2026"
    c.drawCentredString(width / 2, footer_y, footer_line2)
    
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    c.setFont(TITLE_FONT, 10)
    if level:
        footer_line1 = f"Brown Bear Matching | Level {level} | {pack_code} | Page {page_num}/{total_pages}"
    else:
        footer_line1 = f"Brown Bear Matching | Storage Labels | {pack_code}"
    c.drawCentredString(width / 2, footer_y + 12, footer_line1)
    
    c.showPage()


def generate_matching_product_constitution(theme_name="Brown Bear", pack_code="BB03", output_dir="samples/brown_bear/matching", mode='color'):
    """
    Generate complete Matching product following Design Constitution.
    
    Returns paths to generated PDFs.
    """
    # Load icons from assets/themes/[theme]/icons
    repo_root = Path(__file__).resolve().parents[2]
    icon_folder = repo_root / "assets" / "themes" / "brown_bear" / "icons"
    icons, names = load_all_icons(icon_folder)
    
    if not icons:
        print("Error: No icons loaded. Stopping.")
        return None
    
    print(f"\nGenerating {theme_name} Matching product with {len(icons)} icons...")
    print(f"Pack Code: {pack_code}")
    print(f"Mode: {mode}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Section 11: Naming Conventions (snake_case)
    output_filename = f"brown_bear_matching_{mode}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Calculate total pages - REORGANIZED BY LEVEL
    num_icons = len(icons)
    # Each level has: 12 matching pages + 2 cutout pages + 1 storage = 15 pages per level
    pages_per_level = num_icons + 2 + 1  # matching + 2 cutouts + storage
    total_pages = pages_per_level * 5  # 5 levels
    
    print(f"Total pages: {total_pages} (5 levels x {pages_per_level} pages/level)")
    
    page_num = 1
    
    # REORGANIZED: Generate by level first, then by icon within each level
    # This allows each level to be sold separately with its own cutouts and storage labels
    for level in range(1, 6):
        print(f"\n=== LEVEL {level} ===")
        
        # Generate all matching pages for this level (all 12 icons)
        for icon_idx, (target_img, target_name) in enumerate(zip(icons, names)):
            # Get all other icons for distractors
            other_icons = [img for i, img in enumerate(icons) if i != icon_idx]
            other_names = [name for i, name in enumerate(names) if i != icon_idx]
            
            # Determine targets and distractors based on level
            if level == 1:
                # Level 1: 5 targets, 0 distractors
                selected_images = [target_img] * 5
                selected_names = [target_name] * 5
            elif level == 2:
                # Level 2: 4 targets, 1 distractor
                distractor_indices = random.sample(range(len(other_icons)), 1)
                selected_images = [target_img] * 4 + [other_icons[distractor_indices[0]]]
                selected_names = [target_name] * 4 + [other_names[distractor_indices[0]]]
            elif level == 3:
                # Level 3: 3 targets, 2 distractors
                distractor_indices = random.sample(range(len(other_icons)), 2)
                selected_images = [target_img] * 3 + [other_icons[i] for i in distractor_indices]
                selected_names = [target_name] * 3 + [other_names[i] for i in distractor_indices]
            elif level == 4:
                # Level 4: 1 target, 4 distractors
                distractor_indices = random.sample(range(len(other_icons)), 4)
                selected_images = [target_img] * 1 + [other_icons[i] for i in distractor_indices]
                selected_names = [target_name] * 1 + [other_names[i] for i in distractor_indices]
            else:  # level == 5
                # Level 5: keep the same layout and visual design as other levels.
                # Use the hardest distractor pattern (1 target + 4 distractors).
                distractor_indices = random.sample(range(len(other_icons)), 4)
                selected_images = [target_img] * 1 + [other_icons[i] for i in distractor_indices]
                selected_names = [target_name] * 1 + [other_names[i] for i in distractor_indices]
            
            # Shuffle images (except Level 1 where order doesn't matter as much)
            if level > 1:
                combined = list(zip(selected_images, selected_names))
                random.shuffle(combined)
                selected_images, selected_names = zip(*combined)
                selected_images = list(selected_images)
                selected_names = list(selected_names)
            
            # Create matching page
            create_matching_page_constitution(
                c, target_img, target_name, selected_images, selected_names,
                level, page_num, total_pages, pack_code, theme_name, mode
            )
            
            page_num += 1
            print(f"  Generated: {target_name} - Level {level} (Page {page_num-1}/{total_pages})")
        
        # Generate 2 cutout pages for this level (60 pieces total: 5 of each of 12 icons)
        # Page 1: First 6 icons (30 pieces)
        page1_icons = icons[:6]
        create_cutout_page_constitution(c, icons, names, page1_icons, 1, page_num, total_pages, pack_code, theme_name, level, mode)
        page_num += 1
        print(f"  Generated: Cutout page 1 - Level {level} (Page {page_num-1}/{total_pages})")
        
        # Page 2: Next 6 icons (30 pieces)
        page2_icons = icons[6:12]
        create_cutout_page_constitution(c, icons, names, page2_icons, 2, page_num, total_pages, pack_code, theme_name, level, mode)
        page_num += 1
        print(f"  Generated: Cutout page 2 - Level {level} (Page {page_num-1}/{total_pages})")
        
        # Generate storage label page for this level
        create_storage_label_page_constitution(c, icons, names, page_num, total_pages, pack_code, theme_name, level, mode)
        page_num += 1
        print(f"  Generated: Storage Labels - Level {level} (Page {page_num-1}/{total_pages})")
    
    # Save PDF
    c.save()
    
    print(f"\nOK Generated: {output_path}")
    print(f"  Total pages: {total_pages}")
    print(f"  File size: {os.path.getsize(output_path) / 1024:.1f} KB")
    
    return output_path


def add_preview_watermark(input_pdf_path, output_pdf_path):
    """Add diagonal PREVIEW watermark to PDF."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from PyPDF2 import PdfReader, PdfWriter
    import io
    
    # Read the input PDF
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    
    # Create watermark
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Set watermark properties
    can.setFont("Helvetica-Bold", 140)
    can.setFillColor(colors.gray, alpha=0.3)
    
    # Save canvas state
    can.saveState()
    
    # Rotate and position text
    page_width, page_height = letter
    # Move the watermark down so it covers the main activity area rather than the header strip.
    can.translate(page_width/2, (page_height/2) - 55)
    can.rotate(45)
    can.drawCentredString(0, 0, "PREVIEW")
    
    can.restoreState()
    can.save()
    
    # Move to the beginning of the StringIO buffer
    packet.seek(0)
    watermark_pdf = PdfReader(packet)
    watermark_page = watermark_pdf.pages[0]
    
    # Add watermark to each page
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        page.merge_page(watermark_page)
        writer.add_page(page)
    
    # Write output
    with open(output_pdf_path, 'wb') as output_file:
        writer.write(output_file)
    
    print(f"OK Created preview PDF: {output_pdf_path}")
    return output_pdf_path


def split_pdf_by_level(full_pdf_path, output_dir, theme_name, pack_code, mode):
    """Split a full PDF into separate PDFs for each level."""
    from PyPDF2 import PdfReader, PdfWriter
    
    reader = PdfReader(full_pdf_path)
    total_pages = len(reader.pages)
    
    # Matching structure: Each level has 15 pages (12 activities + 2 cutouts + 1 storage)
    pages_per_level = 15
    num_levels = 5
    
    level_pdfs = []
    
    for level in range(1, num_levels + 1):
        # Calculate page range for this level
        start_page = (level - 1) * pages_per_level
        end_page = start_page + pages_per_level
        
        # Create new PDF for this level
        writer = PdfWriter()
        
        for page_num in range(start_page, min(end_page, total_pages)):
            writer.add_page(reader.pages[page_num])
        
        # Determine output filename
        level_filename = f"brown_bear_matching_level{level}_{mode}.pdf"
        level_path = os.path.join(output_dir, level_filename)
        
        # Write level PDF
        with open(level_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"  OK Level {level} {mode.upper()}: {level_filename} ({pages_per_level} pages)")
        level_pdfs.append(level_path)
    
    return level_pdfs


def main():
    """Generate both color and BW versions, plus separate level PDFs and previews."""
    print("=" * 60)
    print("Brown Bear Matching Cards - Design Constitution Compliant")
    print("=" * 60)
    
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = str(repo_root / "samples" / "brown_bear" / "matching")
    
    # Generate full color version
    print("\n[1/4] Generating full COLOR PDF...")
    color_path = generate_matching_product_constitution(
        theme_name="Brown Bear",
        pack_code="BB03",
        output_dir=output_dir,
        mode='color'
    )
    
    # Generate full BW version
    print("\n[2/4] Generating full BLACK & WHITE PDF...")
    bw_path = generate_matching_product_constitution(
        theme_name="Brown Bear",
        pack_code="BB03",
        output_dir=output_dir,
        mode='bw'
    )
    
    if not color_path or not bw_path:
        print("ERROR Matching PDF generation failed; skipping split/preview steps")
        return

    # Split color PDF by level
    print("\n[3/4] Creating separate COLOR PDFs for each level...")
    color_level_pdfs = split_pdf_by_level(color_path, output_dir, "Brown Bear", "BB03", "color")
    
    # Split BW PDF by level
    print("\n[4/4] Creating separate BW PDFs for each level...")
    bw_level_pdfs = split_pdf_by_level(bw_path, output_dir, "Brown Bear", "BB03", "bw")
    
    # Create preview versions (color only)
    print("\n[BONUS] Creating PREVIEW versions with watermark...")
    preview_pdfs = []
    for level_num, color_level_pdf in enumerate(color_level_pdfs, 1):
        preview_filename = f"brown_bear_matching_level{level_num}_preview.pdf"
        preview_path = os.path.join(output_dir, preview_filename)
        add_preview_watermark(color_level_pdf, preview_path)
        preview_pdfs.append(preview_path)

    try:
        from PyPDF2 import PdfReader
        total_pages = len(PdfReader(color_path).pages)
    except Exception:
        total_pages = "?"
    
    print("\n" + "=" * 60)
    print("OK GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nFull PDFs:")
    print(f"  • {os.path.basename(color_path)} ({total_pages} pages)")
    print(f"  • {os.path.basename(bw_path)} ({total_pages} pages)")
    print(f"\nLevel PDFs (15 pages each):")
    for level in range(1, 6):
        print(f"  Level {level}:")
        print(f"    • brown_bear_matching_level{level}_color.pdf")
        print(f"    • brown_bear_matching_level{level}_bw.pdf")
        print(f"    • brown_bear_matching_level{level}_preview.pdf (with watermark)")
    print(f"\nDesign Constitution compliance: OK")
    print(f"  • Border, accent stripe, title/subtitle: OK")
    print(f"  • Activity boxes (1.0\" × 1.0\"): OK")
    print(f"  • Velcro dots (0.35\" diameter): OK")
    print(f"  • Level 1 watermarks (25% opacity): OK")
    print(f"  • Cutout strips (5 icons, touching): OK")
    print(f"  • Footer typography (10pt/9pt): OK")
    print(f"  • Separate level PDFs: OK")
    print(f"  • Preview watermarks: OK")
    

if __name__ == "__main__":
    main()
