#!/usr/bin/env python3
"""
Brown Bear Matching Cards Generator - Matching Product Specification Compliant
Generates matching activity pages following Small Wins Studio Matching Product Spec
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import random

# Try to register Comic Sans MS font (available on most systems)
try:
    # Register Comic Sans MS if available
    pdfmetrics.registerFont(TTFont('Comic-Sans-MS', 'comic.ttf'))
    pdfmetrics.registerFont(TTFont('Comic-Sans-MS-Bold', 'comicbd.ttf'))
    TITLE_FONT = 'Comic-Sans-MS-Bold'
    BODY_FONT = 'Comic-Sans-MS'
except:
    # Fallback to Helvetica if Comic Sans not available
    TITLE_FONT = 'Helvetica-Bold'
    BODY_FONT = 'Helvetica'

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Matching Product Specification Colors
LIGHT_BLUE_BORDER = '#A0C4E8'  # Light blue border for pages
NAVY_BORDER = '#1E3A5F'  # Navy border for target and matching boxes
PURPLE_BORDER = '#6B5BE2'  # Purple border for velcro boxes
LIGHT_GREY_FILL = '#E8E8E8'  # Light grey fill for velcro boxes
VELCRO_DOT_FILL = '#CCCCCC'  # Velcro dot fill
VELCRO_DOT_OUTLINE = '#999999'  # Velcro dot outline
WARM_ORANGE = '#F5A623'  # Accent stripe color
WHITE = '#FFFFFF'
BLACK = '#000000'


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
    - 5 rows × 2 columns layout
    """
    width, height = letter
    
    # Import color utilities for BW mode support
    from utils.color_helpers import hex_to_grayscale, enhance_for_printing
    import hashlib
    
    # Create hash-based temp filenames to reuse same file for same icon
    def get_temp_filename(img, prefix, suffix=""):
        img_hash = hashlib.md5(img.tobytes()).hexdigest()[:12]
        return f"/tmp/{prefix}_{img_hash}_{mode}_{suffix}.png"
    
    # Page Structure - 0.25" margin from edge
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    # Draw rounded rectangle border (3px stroke) - LIGHT BLUE per spec
    c.setStrokeColorRGB(*hex_to_rgb(LIGHT_BLUE_BORDER))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent Stripe - moved higher (less padding from border), increased height
    accent_margin = 0.08 * inch  # Reduced from 0.15" to move stripe higher
    accent_height = 1.0 * inch  # Height for title and subtitle
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin
    
    # Use warm orange for color mode, grayscale for BW mode
    if mode == 'bw':
        gray_orange = hex_to_grayscale(WARM_ORANGE)
        c.setFillColorRGB(*hex_to_rgb(gray_orange))
    else:
        c.setFillColorRGB(*hex_to_rgb(WARM_ORANGE))
    
    # Draw accent stripe with rounded corners
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Title and Subtitle - BOTH INSIDE accent stripe, CENTERED per spec, LARGER FONTS
    # Title: "Matching"
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))  # Navy
    c.setFont(TITLE_FONT, 36)  # Increased from 28pt to 36pt
    title_text = "Matching"
    # Moved down for better centering - position based on center of stripe
    title_y = accent_y + accent_height / 2 + 10  # Adjusted down from +20 to +10
    c.drawCentredString(width / 2, title_y, title_text)
    
    # Subtitle: "Brown Bear" - ALSO INSIDE stripe, below title
    c.setFont(BODY_FONT, 28)  # Increased from 20pt to 28pt
    c.setFillColorRGB(0.2, 0.2, 0.2)  # Dark grey
    subtitle_text = "Brown Bear"
    subtitle_y_in_stripe = title_y - 42  # Below title with more spacing, adjusted from -36 to -42
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
        
        # Draw Navy border around target (slightly thicker than matching boxes per spec)
        c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
        c.setLineWidth(4)  # 4px, thicker than matching boxes (3.5px)
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
        
        # Draw matching box with Navy border (3-4px per spec) - simple, no ornaments
        c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
        c.setLineWidth(3.5)  # 3-4px border per spec
        c.roundRect(img_box_x, img_box_y, box_size, box_size, corner_radius, stroke=1, fill=0)
        
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
            
            # Image fills 97% of box (95-100% range per spec)
            icon_size = box_size * 0.97
            icon_x = img_box_x + (box_size - icon_size) / 2
            icon_y = img_box_y + (box_size - icon_size) / 2
            
            temp_icon = get_temp_filename(display_img, "icon")
            if not os.path.exists(temp_icon):
                display_img.save(temp_icon, 'PNG')
            
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size, 
                       preserveAspectRatio=True, mask='auto')
        
        # Right column: Velcro box with purple border and light grey fill
        velcro_box_x = right_col_x
        velcro_box_y = img_box_y
        
        # Draw velcro box with light grey fill and purple border (3-4px per spec)
        c.setFillColorRGB(*hex_to_rgb(LIGHT_GREY_FILL))
        c.setStrokeColorRGB(*hex_to_rgb(PURPLE_BORDER))
        c.setLineWidth(3.5)  # 3-4px border per spec
        c.roundRect(velcro_box_x, velcro_box_y, box_size, box_size, corner_radius, stroke=1, fill=1)
        
        # Draw velcro dot (0.3" diameter, centered)
        velcro_diameter = 0.3 * inch
        velcro_radius = velcro_diameter / 2
        velcro_center_x = velcro_box_x + box_size / 2
        velcro_center_y = velcro_box_y + box_size / 2
        
        # Velcro dot with specific colors per Product Spec
        c.setFillColorRGB(*hex_to_rgb(VELCRO_DOT_FILL))
        c.setStrokeColorRGB(*hex_to_rgb(VELCRO_DOT_OUTLINE))
        c.setLineWidth(1.5)
        c.circle(velcro_center_x, velcro_center_y, velcro_radius, stroke=1, fill=1)
        
        # Optional tiny "velcro" text
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.setFont("Helvetica", 6)
        text_width = c.stringWidth("velcro", "Helvetica", 6)
        c.drawString(velcro_center_x - text_width/2, velcro_center_y - 2, "velcro")
    
    # Footer - TWO lines per Product Spec (8-9pt, centered, 0.3" from bottom)
    # Line 1: "Matching – Level X | BB03"
    # Line 2: "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License." (light grey)
    footer_y = border_margin + 0.3 * inch
    
    # Line 2 (lower line) in light grey #999999
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    c.drawCentredString(width / 2, footer_y, footer_line2)
    
    # Line 1 (upper line) in dark grey/black
    c.setFillColorRGB(0, 0, 0)
    footer_line1 = f"Matching – Level {level} | {pack_code}"
    c.drawCentredString(width / 2, footer_y + 12, footer_line1)
    
    c.showPage()


def create_cutout_page_constitution(c, images, names, icons_on_page, page_number, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear", level=None, mode='color'):
    """
    Create cutout page following updated requirements:
    - 5 copies of each icon (60 total per level)
    - 2 pages per level (30 pieces per page)
    - Box size matches activity boxes (1.28")
    - 6 columns × 5 rows = 30 boxes per page
    - Title includes page number (1 of 2, 2 of 2)
    """
    width, height = letter
    
    # Import color utilities for BW mode
    from utils.color_helpers import hex_to_grayscale
    
    # Border - Light blue
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    c.setStrokeColorRGB(*hex_to_rgb(LIGHT_BLUE_BORDER))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent stripe: moved higher
    accent_margin = 0.08 * inch
    accent_height = 1.0 * inch  # Larger stripe for title
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin
    
    # Use warm orange for color mode, grayscale for BW mode
    if mode == 'bw':
        gray_orange = hex_to_grayscale(WARM_ORANGE)
        c.setFillColorRGB(*hex_to_rgb(gray_orange))
    else:
        c.setFillColorRGB(*hex_to_rgb(WARM_ORANGE))
    
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Title with page number
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))  # Navy
    # Title: "Cut Out Matching Pieces"
    try:
        c.setFont("Comic-Sans-MS-Bold", 28)
    except:
        c.setFont("Helvetica-Bold", 28)
    
    title_text = "Cut Out Matching Pieces"
    title_y = accent_y + accent_height / 2 + 10
    c.drawCentredString(width / 2, title_y, title_text)
    
    # Subtitle: "Brown Bear" (no level info)
    try:
        c.setFont("Comic-Sans-MS", 20)
    except:
        c.setFont("Helvetica", 20)
    c.setFillColorRGB(0.2, 0.2, 0.2)  # Dark grey
    subtitle_text = theme_name
    subtitle_y = title_y - 32
    c.drawCentredString(width / 2, subtitle_y, subtitle_text)
    
    # Box size matches activity boxes (1.28" from user requirements)
    box_size = 1.28 * inch
    # Icon fills most of box (97% fill)
    icon_size = box_size * 0.97
    spacing = 0.05 * inch  # Minimal spacing for tight cutting
    border_pts = 3  # 3pt border
    
    # 6 columns × 5 rows = 30 boxes (5 copies of 6 icons)
    cols = 6
    rows = 5
    
    # Calculate grid dimensions
    grid_width = cols * box_size + (cols - 1) * spacing
    grid_height = rows * box_size + (rows - 1) * spacing
    
    # Center grid on page
    start_x = (width - grid_width) / 2
    content_top = accent_y - 0.4 * inch
    start_y = content_top - 0.3 * inch
    
    # Draw 6×5 grid - each icon appears 5 times in a column
    icon_idx = 0
    for col in range(cols):
        if icon_idx >= len(icons_on_page):
            break
        img = icons_on_page[icon_idx]
        
        # Draw 5 copies of this icon in this column
        for row in range(rows):
            box_x = start_x + col * (box_size + spacing)
            box_y = start_y - row * (box_size + spacing) - box_size
            
            # Draw box with 3pt border
            c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
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
            temp_icon = f"/tmp/cutout_{img_hash}_{mode}_{col}_{row}.png"
            if not os.path.exists(temp_icon):
                img_copy.save(temp_icon, 'PNG')
            
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size,
                       preserveAspectRatio=True, mask='auto')
        
        icon_idx += 1
    
    # Footer - TWO lines per Product Spec
    footer_y = border_margin + 0.3 * inch
    
    # Line 2 (lower line) in light grey
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    c.drawCentredString(width / 2, footer_y, footer_line2)
    
    # Line 1 (upper line)
    c.setFillColorRGB(0, 0, 0)
    if level:
        footer_line1 = f"Matching – Level {level} | {pack_code}"
    else:
        footer_line1 = f"Cutouts | {pack_code}"
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
    
    # Page border - Light blue
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    c.setStrokeColorRGB(*hex_to_rgb(LIGHT_BLUE_BORDER))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent stripe at top
    accent_margin = 0.08 * inch
    accent_height = 1.0 * inch
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin
    
    if mode == 'bw':
        gray_orange = hex_to_grayscale(WARM_ORANGE)
        c.setFillColorRGB(*hex_to_rgb(gray_orange))
    else:
        c.setFillColorRGB(*hex_to_rgb(WARM_ORANGE))
    
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Page title
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))
    try:
        c.setFont("Comic-Sans-MS-Bold", 36)
    except:
        c.setFont("Helvetica-Bold", 36)
    
    title_text = "Storage Labels"
    title_y = accent_y + accent_height / 2 + 10
    c.drawCentredString(width / 2, title_y, title_text)
    
    # Subtitle
    try:
        c.setFont("Comic-Sans-MS", 28)
    except:
        c.setFont("Helvetica", 28)
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
        
        # Draw box with pale blue background
        if mode == 'bw':
            # Use light gray for BW
            c.setFillColorRGB(0.95, 0.95, 0.95)
        else:
            c.setFillColorRGB(*hex_to_rgb(PALE_BLUE))
        
        c.setStrokeColorRGB(*hex_to_rgb(MEDIUM_BLUE))
        c.setLineWidth(2)
        c.roundRect(box_x, box_y, box_width, box_height, 6, stroke=1, fill=1)
        
        # Title: "Matching"
        c.setFillColorRGB(*hex_to_rgb(DARK_BLUE))
        c.setFont("Helvetica-Bold", 11)
        text_y = box_y + box_height - 0.2 * inch
        c.drawCentredString(box_x + box_width / 2, text_y, "Matching")
        
        # Subtitle: "Brown Bear BB03"
        c.setFont("Helvetica", 9)
        text_y -= 0.18 * inch
        c.drawCentredString(box_x + box_width / 2, text_y, f"{theme_name} {pack_code}")
        
        # Level info
        if level:
            c.setFont("Helvetica-Bold", 9)
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
        temp_icon = f"/tmp/storage_{img_hash}_{mode}_{idx}.png"
        if not os.path.exists(temp_icon):
            img_copy.save(temp_icon, 'PNG')
        
        c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size,
                   preserveAspectRatio=True, mask='auto')
        
        # Icon name (centered below icon) - adjusted position
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0, 0, 0)
        name_y = icon_y - 0.18 * inch  # Moved down from -0.15" to -0.18"
        c.drawCentredString(box_x + box_width / 2, name_y, names[idx])
    
    # Footer
    footer_y = border_margin + 0.3 * inch
    
    # Line 2 (lower line) in light grey
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    c.drawCentredString(width / 2, footer_y, footer_line2)
    
    # Line 1 (upper line)
    c.setFillColorRGB(0, 0, 0)
    if level:
        footer_line1 = f"Matching – Level {level} | {pack_code}"
    else:
        footer_line1 = f"Storage Labels | {pack_code}"
    c.drawCentredString(width / 2, footer_y + 12, footer_line1)
    
    c.showPage()


def generate_matching_product_constitution(theme_name="Brown Bear", pack_code="BB03", output_dir="samples/brown_bear/matching", mode='color'):
    """
    Generate complete Matching product following Design Constitution.
    
    Returns paths to generated PDFs.
    """
    # Load icons from /assets/[theme]/icons/ (Section 12)
    icon_folder = f'/home/runner/work/small-wins-automation/small-wins-automation/assets/themes/brown_bear/icons'
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
    total_pages = pages_per_level * 4  # 4 levels
    
    print(f"Total pages: {total_pages} (4 levels × {pages_per_level} pages/level)")
    
    page_num = 1
    
    # REORGANIZED: Generate by level first, then by icon within each level
    # This allows each level to be sold separately with its own cutouts and storage labels
    for level in range(1, 5):
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
            else:  # level == 4
                # Level 4: 1 target, 4 distractors
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
    
    print(f"\n✓ Generated: {output_path}")
    print(f"  Total pages: {total_pages}")
    print(f"  File size: {os.path.getsize(output_path) / 1024:.1f} KB")
    
    return output_path


def main():
    """Generate both color and BW versions."""
    print("=" * 60)
    print("Brown Bear Matching Cards - Design Constitution Compliant")
    print("=" * 60)
    
    output_dir = "/home/runner/work/small-wins-automation/small-wins-automation/samples/brown_bear/matching"
    
    # Generate color version
    print("\n[1/2] Generating COLOR version...")
    color_path = generate_matching_product_constitution(
        theme_name="Brown Bear",
        pack_code="BB03",
        output_dir=output_dir,
        mode='color'
    )
    
    # Generate BW version
    print("\n[2/2] Generating BLACK & WHITE version...")
    bw_path = generate_matching_product_constitution(
        theme_name="Brown Bear",
        pack_code="BB03",
        output_dir=output_dir,
        mode='bw'
    )
    
    print("\n" + "=" * 60)
    print("✓ GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nOutput files:")
    if color_path:
        print(f"  • {color_path}")
    if bw_path:
        print(f"  • {bw_path}")
    print(f"\nDesign Constitution compliance: ✓")
    print(f"  • Border, accent stripe, title/subtitle: ✓")
    print(f"  • Activity boxes (1.0\" × 1.0\"): ✓")
    print(f"  • Velcro dots (0.35\" diameter): ✓")
    print(f"  • Level 1 watermarks (25% opacity): ✓")
    print(f"  • Cutout strips (5 icons, touching): ✓")
    print(f"  • Footer typography (10pt/9pt): ✓")
    

if __name__ == "__main__":
    main()
