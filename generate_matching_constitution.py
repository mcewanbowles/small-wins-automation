#!/usr/bin/env python3
"""
Small Wins Studio - Matching Activity Generator
Following EXACT specs from:
- design/product_specs/matching.md
- design/Design-Constitution.md
- generators/matching/README.md

Output: Separate PDF per level, each containing:
- 12 activity pages (one per icon)
- Cutout page
- Storage labels page
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import random

# =============================================================================
# COLOR CONFIGURATION
# =============================================================================
NAVY_BORDER = '#1E3A5F'           # Target box and matching box borders
PURPLE_BORDER = '#6B5BE2'         # Velcro box border
VELCRO_FILL = '#E8E8E8'           # Light grey velcro box fill
VELCRO_DOT_FILL = '#CCCCCC'       # Velcro dot fill
VELCRO_DOT_OUTLINE = '#999999'    # Velcro dot outline
FOOTER_GREY = '#999999'           # Footer line 2

# LEVEL-SPECIFIC ACCENT COLORS
LEVEL_COLORS = {
    1: '#F5A623',   # Orange - Errorless
    2: '#4285F4',   # Blue - Easy
    3: '#34A853',   # Green - Medium
    4: '#8C06F2',   # Purple - Hard
}

LEVEL_NAMES = {
    1: 'Errorless',
    2: 'Easy',
    3: 'Medium',
    4: 'Hard'
}

# LEVEL LOGIC: (targets, distractors)
LEVEL_LOGIC = {
    1: (5, 0),  # 5 targets, 0 distractors
    2: (4, 1),  # 4 targets, 1 distractor
    3: (3, 2),  # 3 targets, 2 distractors
    4: (1, 4),  # 1 target, 4 distractors
}


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple (0-1 range for reportlab)."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (r/255, g/255, b/255)


def load_all_icons(icon_folder):
    """Load all PNG icons from the specified folder."""
    icons = []
    names = []
    
    if not os.path.exists(icon_folder):
        print(f"Error: Icon folder not found: {icon_folder}")
        return icons, names
    
    png_files = sorted([f for f in os.listdir(icon_folder) 
                       if f.lower().endswith('.png') and not f.startswith('.')])
    
    print(f"Found {len(png_files)} icon files in {icon_folder}")
    
    for filename in png_files:
        filepath = os.path.join(icon_folder, filename)
        try:
            img = Image.open(filepath)
            if img.mode == 'RGBA':
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            icons.append(img)
            # "See" must be renamed to "Eyes" per spec section 6
            name = os.path.splitext(filename)[0].replace('_', ' ').title()
            if name.lower() == 'see':
                name = 'Eyes'
            names.append(name)
            print(f"  Loaded: {filename} -> {name}")
        except Exception as e:
            print(f"  Error loading {filename}: {e}")
    
    return icons, names


def create_matching_page(c, target_img, target_name, row_images, level, 
                         page_num, total_pages, pack_code, theme_name, mode='color'):
    """
    Create a single matching activity page.
    
    Args:
        c: ReportLab canvas
        target_img: PIL Image of the target icon
        target_name: Name of the target icon
        row_images: List of 5 PIL Images for the matching boxes
        level: 1-4
        page_num: Current page number
        total_pages: Total pages in this PDF
        pack_code: e.g., "BB03"
        theme_name: e.g., "Brown Bear"
        mode: 'color' or 'bw'
    """
    width, height = letter  # 8.5" x 11"
    
    # Get level-specific color
    accent_color = LEVEL_COLORS.get(level, LEVEL_COLORS[1])
    
    # ===== PAGE BORDER =====
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
    c.setLineWidth(2)
    c.roundRect(border_margin, border_margin, content_width, content_height, 8, stroke=1, fill=0)
    
    # ===== ACCENT STRIPE (DEEPER per user request) =====
    stripe_margin = 0.1 * inch
    stripe_height = 0.85 * inch  # Deeper stripe
    stripe_x = border_margin + stripe_margin
    stripe_y = height - border_margin - stripe_margin - stripe_height
    stripe_width = content_width - 2 * stripe_margin
    
    if mode == 'color':
        c.setFillColorRGB(*hex_to_rgb(accent_color))
    else:
        c.setFillColorRGB(0.7, 0.7, 0.7)
    c.roundRect(stripe_x, stripe_y, stripe_width, stripe_height, 6, stroke=0, fill=1)
    
    # ===== TITLE + SUBTITLE (Centered in accent stripe) =====
    c.setFillColorRGB(1, 1, 1)  # White text
    stripe_center_y = stripe_y + stripe_height / 2
    
    # Title: "MATCHING"
    c.setFont("Helvetica-Bold", 26)
    title_text = "MATCHING"
    title_width = c.stringWidth(title_text, "Helvetica-Bold", 26)
    c.drawString((width - title_width) / 2, stripe_center_y + 0.12 * inch, title_text)
    
    # Subtitle: Theme name
    c.setFont("Helvetica", 16)
    subtitle_width = c.stringWidth(theme_name, "Helvetica", 16)
    c.drawString((width - subtitle_width) / 2, stripe_center_y - 0.18 * inch, theme_name)
    
    # ===== INSTRUCTION LINE =====
    instruction_y = stripe_y - 0.25 * inch
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    instruction_text = f"Match the {target_name}"
    instruction_width = c.stringWidth(instruction_text, "Helvetica-Bold", 12)
    c.drawString((width - instruction_width) / 2, instruction_y, instruction_text)
    
    # ===== TARGET BOX (Smaller per user request) =====
    target_box_size = 0.75 * inch
    target_box_x = (width - target_box_size) / 2
    target_box_y = instruction_y - target_box_size - 0.1 * inch
    
    # Soft shadow
    c.setFillColorRGB(0, 0, 0)
    c.setFillAlpha(0.07)
    c.roundRect(target_box_x + 2, target_box_y - 2, target_box_size, target_box_size, 6, stroke=0, fill=1)
    c.setFillAlpha(1.0)
    
    # Target box
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
    c.setLineWidth(2.5)
    c.roundRect(target_box_x, target_box_y, target_box_size, target_box_size, 6, stroke=1, fill=1)
    
    # Target image (max size, no padding)
    if target_img:
        temp_target = "/tmp/temp_target.png"
        target_img.save(temp_target, 'PNG')
        icon_size = target_box_size * 0.95
        icon_x = target_box_x + (target_box_size - icon_size) / 2
        icon_y = target_box_y + (target_box_size - icon_size) / 2
        c.drawImage(temp_target, icon_x, icon_y, width=icon_size, height=icon_size, 
                   preserveAspectRatio=True, mask='auto')
    
    # ===== MATCHING GRID (5 rows x 2 columns) =====
    box_size = 1.35 * inch
    column_gap = 1.8 * inch
    row_spacing = 0.06 * inch
    
    # Calculate grid dimensions
    total_grid_height = 5 * box_size + 4 * row_spacing
    footer_height = 0.45 * inch
    grid_bottom = border_margin + footer_height
    grid_top = target_box_y - 0.1 * inch
    
    available_height = grid_top - grid_bottom
    if total_grid_height > available_height:
        box_size = (available_height - 4 * row_spacing) / 5
    
    grid_start_y = grid_bottom + (available_height - total_grid_height) / 2 + total_grid_height
    
    # Center columns
    total_width = 2 * box_size + column_gap
    left_col_x = (width - total_width) / 2
    right_col_x = left_col_x + box_size + column_gap
    
    for row in range(5):
        row_y = grid_start_y - row * (box_size + row_spacing) - box_size
        
        # LEFT COLUMN: Matching box
        c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
        c.setLineWidth(2.5)
        c.setFillColorRGB(1, 1, 1)
        c.roundRect(left_col_x, row_y, box_size, box_size, 6, stroke=1, fill=1)
        
        # Draw icon (max size, no padding)
        if row < len(row_images) and row_images[row]:
            img = row_images[row]
            temp_icon = f"/tmp/temp_icon_{row}.png"
            img.save(temp_icon, 'PNG')
            icon_size = box_size * 0.98
            icon_x = left_col_x + (box_size - icon_size) / 2
            icon_y = row_y + (box_size - icon_size) / 2
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size,
                       preserveAspectRatio=True, mask='auto')
        
        # RIGHT COLUMN: Velcro box
        c.setFillColorRGB(*hex_to_rgb(VELCRO_FILL))
        c.setStrokeColorRGB(*hex_to_rgb(PURPLE_BORDER))
        c.setLineWidth(2.5)
        c.roundRect(right_col_x, row_y, box_size, box_size, 6, stroke=1, fill=1)
        
        # Level 1 watermark
        if level == 1 and target_img:
            temp_wm = f"/tmp/watermark_{row}.png"
            wm_img = target_img.copy().convert('RGBA')
            alpha = wm_img.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.25))
            wm_img.putalpha(alpha)
            wm_img.save(temp_wm, 'PNG')
            wm_size = box_size * 0.70
            wm_x = right_col_x + (box_size - wm_size) / 2
            wm_y = row_y + (box_size - wm_size) / 2
            c.drawImage(temp_wm, wm_x, wm_y, width=wm_size, height=wm_size,
                       preserveAspectRatio=True, mask='auto')
        
        # Velcro dot (smaller)
        velcro_diameter = 0.18 * inch
        c.setFillColorRGB(*hex_to_rgb(VELCRO_DOT_FILL))
        c.setStrokeColorRGB(*hex_to_rgb(VELCRO_DOT_OUTLINE))
        c.setLineWidth(1)
        c.circle(right_col_x + box_size/2, row_y + box_size/2, velcro_diameter/2, stroke=1, fill=1)
    
    # ===== FOOTER =====
    footer_line1_y = border_margin + 0.22 * inch
    footer_line2_y = border_margin + 0.08 * inch
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 9)
    footer_line1 = f"Matching - Level {level} | {pack_code} | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_line1_y, footer_line1)
    
    c.setFillColorRGB(*hex_to_rgb(FOOTER_GREY))
    c.setFont("Helvetica", 8)
    footer_line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    c.drawCentredString(width/2, footer_line2_y, footer_line2)
    
    c.showPage()


def create_cutout_page(c, icons, names, level, pack_code, theme_name, mode='color'):
    """Create a cutout page with 4x5 grid of icons."""
    width, height = letter
    accent_color = LEVEL_COLORS.get(level, LEVEL_COLORS[1])
    
    # Page border
    border_margin = 0.25 * inch
    c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
    c.setLineWidth(2)
    c.roundRect(border_margin, border_margin, 
                width - 2*border_margin, height - 2*border_margin, 8, stroke=1, fill=0)
    
    # Accent stripe
    stripe_margin = 0.1 * inch
    stripe_height = 0.6 * inch
    stripe_x = border_margin + stripe_margin
    stripe_y = height - border_margin - stripe_margin - stripe_height
    stripe_width = width - 2*border_margin - 2*stripe_margin
    
    if mode == 'color':
        c.setFillColorRGB(*hex_to_rgb(accent_color))
    else:
        c.setFillColorRGB(0.7, 0.7, 0.7)
    c.roundRect(stripe_x, stripe_y, stripe_width, stripe_height, 6, stroke=0, fill=1)
    
    # Title
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 20)
    title = f"Cutout Matching Pieces - {theme_name}"
    title_width = c.stringWidth(title, "Helvetica-Bold", 20)
    c.drawString((width - title_width)/2, stripe_y + stripe_height/2 - 0.05*inch, title)
    
    # Grid: 4 columns x 5 rows
    grid_top = stripe_y - 0.3 * inch
    grid_bottom = border_margin + 0.4 * inch
    grid_left = border_margin + 0.3 * inch
    grid_right = width - border_margin - 0.3 * inch
    
    cols = 4
    rows = 5
    box_width = (grid_right - grid_left) / cols
    box_height = (grid_top - grid_bottom) / rows
    box_size = min(box_width, box_height) - 0.05 * inch
    
    # Center the grid
    total_grid_width = cols * box_size
    total_grid_height = rows * box_size
    start_x = (width - total_grid_width) / 2
    start_y = grid_top
    
    icon_idx = 0
    for row in range(rows):
        for col in range(cols):
            if icon_idx >= len(icons):
                icon_idx = 0  # Wrap around
            
            box_x = start_x + col * box_size
            box_y = start_y - (row + 1) * box_size
            
            # Box border
            c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
            c.setLineWidth(2)
            c.setFillColorRGB(1, 1, 1)
            c.roundRect(box_x, box_y, box_size, box_size, 4, stroke=1, fill=1)
            
            # Icon
            if icons[icon_idx]:
                temp_icon = f"/tmp/cutout_icon_{icon_idx}.png"
                icons[icon_idx].save(temp_icon, 'PNG')
                icon_size = box_size * 0.90
                c.drawImage(temp_icon, 
                           box_x + (box_size - icon_size)/2,
                           box_y + (box_size - icon_size)/2,
                           width=icon_size, height=icon_size,
                           preserveAspectRatio=True, mask='auto')
            
            icon_idx += 1
    
    # Footer
    c.setFillColorRGB(*hex_to_rgb(FOOTER_GREY))
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, border_margin + 0.15*inch, 
                       f"Cutouts - Level {level} | {pack_code}")
    
    c.showPage()


def create_storage_label_page(c, icons, names, level, pack_code, theme_name, mode='color'):
    """Create a storage label page."""
    width, height = letter
    accent_color = LEVEL_COLORS.get(level, LEVEL_COLORS[1])
    
    # Page border
    border_margin = 0.25 * inch
    c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
    c.setLineWidth(2)
    c.roundRect(border_margin, border_margin,
                width - 2*border_margin, height - 2*border_margin, 8, stroke=1, fill=0)
    
    # Accent stripe
    stripe_margin = 0.1 * inch
    stripe_height = 0.7 * inch
    stripe_x = border_margin + stripe_margin
    stripe_y = height - border_margin - stripe_margin - stripe_height
    stripe_width = width - 2*border_margin - 2*stripe_margin
    
    if mode == 'color':
        c.setFillColorRGB(*hex_to_rgb(accent_color))
    else:
        c.setFillColorRGB(0.7, 0.7, 0.7)
    c.roundRect(stripe_x, stripe_y, stripe_width, stripe_height, 6, stroke=0, fill=1)
    
    # Title
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 22)
    title = f"{theme_name} Matching Cards"
    title_width = c.stringWidth(title, "Helvetica-Bold", 22)
    c.drawString((width - title_width)/2, stripe_y + stripe_height/2 + 0.08*inch, title)
    
    c.setFont("Helvetica", 14)
    subtitle = f"Level {level}: {LEVEL_NAMES[level]} | {pack_code}"
    subtitle_width = c.stringWidth(subtitle, "Helvetica", 14)
    c.drawString((width - subtitle_width)/2, stripe_y + stripe_height/2 - 0.18*inch, subtitle)
    
    # Vocabulary list (3 columns)
    list_top = stripe_y - 0.5 * inch
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, list_top, "Vocabulary")
    
    cols = 3
    col_width = (width - 2*border_margin - 1*inch) / cols
    start_x = border_margin + 0.5*inch
    
    c.setFont("Helvetica", 11)
    for i, name in enumerate(names):
        col = i % cols
        row = i // cols
        x = start_x + col * col_width
        y = list_top - 0.4*inch - row * 0.25*inch
        c.drawString(x, y, f"• {name}")
    
    # Footer
    c.setFillColorRGB(*hex_to_rgb(FOOTER_GREY))
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, border_margin + 0.15*inch,
                       "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License.")
    
    c.showPage()


def generate_level_pdf(icons, names, level, pack_code, theme_name, output_path, mode='color'):
    """
    Generate a complete PDF for one level.
    Contains: 12 activity pages (one per icon) + cutout page + storage label page
    """
    print(f"\n  Generating Level {level} ({LEVEL_NAMES[level]}) - {mode}...")
    
    c = canvas.Canvas(output_path, pagesize=letter)
    
    num_targets, num_distractors = LEVEL_LOGIC[level]
    total_pages = len(icons) + 2  # activity pages + cutout + storage
    
    # Generate one activity page per icon
    for page_idx, (target_img, target_name) in enumerate(zip(icons, names)):
        # Build row images based on level logic
        row_images = []
        
        # Add target images
        for _ in range(num_targets):
            row_images.append(target_img)
        
        # Add distractor images (random, but not the target)
        other_icons = [(img, name) for img, name in zip(icons, names) if name != target_name]
        distractors = random.sample(other_icons, min(num_distractors, len(other_icons)))
        for dist_img, _ in distractors:
            row_images.append(dist_img)
        
        # Shuffle the row images
        random.shuffle(row_images)
        
        create_matching_page(c, target_img, target_name, row_images, level,
                            page_idx + 1, total_pages, pack_code, theme_name, mode)
    
    # Cutout page
    create_cutout_page(c, icons, names, level, pack_code, theme_name, mode)
    
    # Storage label page
    create_storage_label_page(c, icons, names, level, pack_code, theme_name, mode)
    
    c.save()
    print(f"    Saved: {output_path}")


def generate_matching_pack(theme_path, theme_name, pack_code, output_dir):
    """
    Generate complete matching pack for a theme.
    Output: 8 PDFs (4 levels x 2 modes) + shared cutouts + storage labels
    """
    print(f"\n{'='*60}")
    print(f"Generating Matching Pack: {theme_name} ({pack_code})")
    print(f"{'='*60}")
    
    # Load icons
    icon_folder = os.path.join(theme_path, 'icons')
    icons, names = load_all_icons(icon_folder)
    
    if len(icons) < 5:
        print(f"Error: Need at least 5 icons, found {len(icons)}")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate PDFs for each level
    for level in [1, 2, 3, 4]:
        for mode in ['color', 'bw']:
            filename = f"{theme_name.lower().replace(' ', '_')}_matching_level{level}_{mode}.pdf"
            output_path = os.path.join(output_dir, filename)
            generate_level_pdf(icons, names, level, pack_code, theme_name, output_path, mode)
    
    print(f"\n{'='*60}")
    print(f"Complete! Generated 8 PDFs in {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    # Default paths
    BASE_DIR = Path(__file__).parent
    THEME_PATH = BASE_DIR / "assets" / "themes" / "brown_bear"
    OUTPUT_DIR = BASE_DIR / "review_pdfs"
    
    generate_matching_pack(
        theme_path=str(THEME_PATH),
        theme_name="Brown Bear",
        pack_code="BB03",
        output_dir=str(OUTPUT_DIR)
    )
