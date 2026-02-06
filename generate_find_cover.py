#!/usr/bin/env python3
"""
Generate Find & Cover Level PDFs for Brown Bear theme.
Produces all 4 levels in both color and BW versions.
Uses Matching Product Spec design elements.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from PIL import Image
import random

# Page settings
PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.5 * inch

# Matching Product Spec Colors
LIGHT_BLUE_BORDER = '#A0C4E8'  # Light blue border for pages
NAVY_BORDER = '#1E3A5F'  # Navy border for target and boxes
WHITE = '#FFFFFF'
BLACK = '#000000'

# Level colors for accent strips (matching Matching product)
LEVEL_COLORS = {
    1: '#F4A259',  # Orange - Level 1 (beginner)
    2: '#4A90E2',  # Blue - Level 2 (easy)
    3: '#7BC47F',  # Green - Level 3 (medium)
    4: '#9B59B6',  # Purple - Level 4 (hard)
    5: '#008B8B',  # Teal - Level 5 (real photos)
}

LEVEL_NAMES = {
    1: 'Errorless',
    2: 'Easy',
    3: 'Medium',
    4: 'Challenge',
    5: 'Real Photos'
}

# Mapping from BoardMaker icons to real photos
REAL_IMAGE_MAPPING = {
    'Brown bear.png': 'bear.png',
    'Red bird.png': 'bird.png',
    'Purple cat.png': 'cat.png',
    'White dog.png': 'dog.png',
    'Yellow duck.png': 'duck.png',
    'Green frog.png': 'frog.png',
    'goldfish.png': 'goldfish.png',
    'Blue horse.png': 'horse.png',
    'Black sheep.png': 'sheep1.png',
    'teacher.png': 'teacher.png',
}

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def load_brown_bear_icons():
    """Load all Brown Bear icons."""
    icon_folder = Path(__file__).parent / 'assets' / 'themes' / 'brown_bear' / 'icons'
    icons = []
    
    if not icon_folder.exists():
        print(f"Warning: Icon folder not found: {icon_folder}")
        return icons
    
    for png_file in sorted(icon_folder.glob('*.png')):
        if png_file.name.startswith('.'):
            continue
        name = png_file.stem.replace('_', ' ').title()
        icons.append({
            'path': str(png_file),
            'name': name
        })
    
    return icons

def load_real_images():
    """Load all real images for Level 5."""
    real_folder = Path(__file__).parent / 'assets' / 'themes' / 'brown_bear' / 'real_images'
    real_images = []
    
    if not real_folder.exists():
        print(f"Warning: Real images folder not found: {real_folder}")
        return real_images
    
    for png_file in sorted(real_folder.glob('*.png')):
        if png_file.name.startswith('.'):
            continue
        name = png_file.stem.replace('_', ' ').title()
        real_images.append({
            'path': str(png_file),
            'name': name,
            'filename': png_file.name
        })
    
    return real_images

def get_matching_real_image(boardmaker_icon_filename, real_images):
    """Get the real image that matches a BoardMaker icon."""
    real_filename = REAL_IMAGE_MAPPING.get(boardmaker_icon_filename)
    if real_filename:
        for img in real_images:
            if img['filename'] == real_filename:
                return img
    return None

def generate_find_cover_page(c, target_icon, all_icons, level, page_num, total_pages, mode='color', pack_code="BB-FC"):
    """Generate a single Find & Cover page with Matching design spec."""
    
    width, height = letter
    
    # Page setup
    c.setPageSize(letter)
    
    # Background white
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Page Structure - 0.25" margin from edge (matching Matching spec)
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    # Draw rounded rectangle border (3px stroke) - LIGHT BLUE per spec
    r, g, b = hex_to_rgb(LIGHT_BLUE_BORDER)
    c.setStrokeColorRGB(r, g, b)
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent Stripe with level color and rounded corners
    accent_margin = 0.08 * inch
    accent_height = 1.0 * inch
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin
    
    # Use level-specific color for accent stripe
    level_color = LEVEL_COLORS.get(level, '#F4A259')
    if mode == 'bw':
        c.setFillColorRGB(0.7, 0.7, 0.7)
    else:
        r, g, b = hex_to_rgb(level_color)
        c.setFillColorRGB(r, g, b)
    
    # Draw accent stripe with rounded corners
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Title and Subtitle inside accent stripe
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))  # Navy
    c.setFont('Helvetica-Bold', 36)
    title_y = accent_y + accent_height / 2 + 5
    c.drawCentredString(width / 2, title_y, "Find & Cover")
    
    # Subtitle: "Brown Bear"
    c.setFont('Helvetica', 28)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    subtitle_y = title_y - 30
    c.drawCentredString(width / 2, subtitle_y, "Brown Bear")
    
    # Level indicator below stripe
    c.setFont('Helvetica-Bold', 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, accent_y - 20, f"Level {level}: {LEVEL_NAMES[level]}")
    
    # Target box - navy border with rounded corners
    target_box_y = accent_y - 150
    target_box_size = 100
    target_box_x = width/2 - target_box_size/2
    
    # Navy border for target box
    r, g, b = hex_to_rgb(NAVY_BORDER)
    c.setStrokeColorRGB(r, g, b)
    c.setLineWidth(3.5)
    c.roundRect(target_box_x, target_box_y, target_box_size, target_box_size, 8, fill=False, stroke=True)
    
    # Draw target icon
    try:
        img = Image.open(target_icon['path'])
        if mode == 'bw':
            img = img.convert('L').convert('RGB')
        # Save temp image
        temp_path = f'/tmp/target_{page_num}.png'
        img.save(temp_path)
        c.drawImage(temp_path, target_box_x + 10, target_box_y + 10, 
                   width=target_box_size - 20, height=target_box_size - 20,
                   preserveAspectRatio=True, mask='auto')
    except Exception as e:
        # Draw placeholder text
        c.setFont('Helvetica', 12)
        c.drawCentredString(target_box_x + target_box_size/2, target_box_y + target_box_size/2, target_icon['name'][:10])
    
    # Label under target
    c.setFont('Helvetica', 12)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, target_box_y - 20, f"Find: {target_icon['name']}")
    
    # Instruction
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(width/2, target_box_y - 45, "Cover all matching pictures")
    
    # Grid area
    grid_start_y = target_box_y - 80
    grid_rows = 4
    grid_cols = 4
    cell_size = 100
    grid_width = grid_cols * cell_size
    grid_height = grid_rows * cell_size
    grid_start_x = width/2 - grid_width/2
    
    # Generate grid content based on level
    total_cells = grid_rows * grid_cols
    grid_content = []
    
    if level == 1:
        # Errorless: All match target (100% success)
        grid_content = [target_icon] * total_cells
    elif level == 2:
        # Easy: 50% match, 50% distractors
        num_matches = total_cells // 2
        grid_content = [target_icon] * num_matches
        distractors = [icon for icon in all_icons if icon['name'] != target_icon['name']]
        while len(grid_content) < total_cells and distractors:
            grid_content.append(random.choice(distractors))
    elif level == 3:
        # Medium: ~30% match, ~70% distractors
        num_matches = total_cells // 3
        grid_content = [target_icon] * num_matches
        distractors = [icon for icon in all_icons if icon['name'] != target_icon['name']]
        while len(grid_content) < total_cells and distractors:
            grid_content.append(random.choice(distractors))
    elif level == 4:
        # Challenge: Only 1-2 matches among many distractors
        num_matches = max(1, total_cells // 8)  # Only 1-2 matches
        grid_content = [target_icon] * num_matches
        distractors = [icon for icon in all_icons if icon['name'] != target_icon['name']]
        while len(grid_content) < total_cells and distractors:
            grid_content.append(random.choice(distractors))
    # Level 5 handled separately in generate_find_cover_level5_page
    
    # Fill remaining with distractors if needed
    distractors = [icon for icon in all_icons if icon['name'] != target_icon['name']]
    while len(grid_content) < total_cells:
        if distractors:
            grid_content.append(random.choice(distractors))
        else:
            grid_content.append(target_icon)
    
    # Shuffle all levels
    random.shuffle(grid_content)
    
    # Draw grid with navy borders and rounded corners
    for row in range(grid_rows):
        for col in range(grid_cols):
            idx = row * grid_cols + col
            x = grid_start_x + col * cell_size
            y = grid_start_y - (row + 1) * cell_size
            
            # Navy border for grid cells
            r, g, b = hex_to_rgb(NAVY_BORDER)
            c.setStrokeColorRGB(r, g, b)
            c.setLineWidth(2)
            
            # Rounded rect for grid cells (all levels including Level 4)
            c.roundRect(x + 2, y + 2, cell_size - 4, cell_size - 4, 6, fill=False, stroke=True)
            
            # Draw icon
            icon = grid_content[idx]
            if icon:
                try:
                    img = Image.open(icon['path'])
                    if mode == 'bw':
                        img = img.convert('L').convert('RGB')
                    temp_path = f'/tmp/grid_{page_num}_{idx}.png'
                    img.save(temp_path)
                    c.drawImage(temp_path, x + 8, y + 8,
                               width=cell_size - 16, height=cell_size - 16,
                               preserveAspectRatio=True, mask='auto')
                except Exception as e:
                    pass
    
    # Footer - TWO lines per Product Spec (both in light grey #999999)
    # Line 1 (upper): "Find & Cover – Level X | BB-FC | Page Y/Total"
    # Line 2 (lower): "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    footer_y = border_margin + 0.3 * inch
    
    # Line 2 (lower line) - Copyright in light grey #999999
    c.setFont('Helvetica', 9)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    c.drawCentredString(width/2, footer_y, footer_line2)
    
    # Line 1 (upper line) - Product/Level/Page info in light grey #999999
    c.setFont('Helvetica', 10)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line1 = f"Find & Cover – Level {level} | {pack_code} | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y + 12, footer_line1)
    
    c.showPage()

def generate_find_cover_pdf(output_path, level, mode='color'):
    """Generate a Find & Cover PDF for a specific level."""
    
    icons = load_brown_bear_icons()
    if not icons:
        print(f"No icons found, cannot generate PDF")
        return None
    
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    # Calculate total pages
    total_pages = len(icons)
    
    # Generate pages for each target
    random.seed(42)  # Reproducible randomness
    for i, target_icon in enumerate(icons):
        generate_find_cover_page(c, target_icon, icons, level, i+1, total_pages, mode)
    
    c.save()
    print(f"✓ Generated: {output_path}")
    return output_path

def generate_storage_labels_page(c, icons, level, mode='color', pack_code="BB-FC"):
    """Generate a storage labels page for Find & Cover."""
    
    width, height = letter
    c.setPageSize(letter)
    
    # Background white
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Page border
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    r, g, b = hex_to_rgb(LIGHT_BLUE_BORDER)
    c.setStrokeColorRGB(r, g, b)
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent stripe at top
    accent_margin = 0.08 * inch
    accent_height = 0.8 * inch
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin
    
    # Use level-specific color for accent stripe
    level_color = LEVEL_COLORS.get(level, '#F4A259')
    if mode == 'bw':
        c.setFillColorRGB(0.7, 0.7, 0.7)
    else:
        r, g, b = hex_to_rgb(level_color)
        c.setFillColorRGB(r, g, b)
    
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Page title
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))
    c.setFont("Helvetica-Bold", 28)
    title_y = accent_y + accent_height / 2 + 5
    c.drawCentredString(width / 2, title_y, "Storage Labels")
    
    # Subtitle
    c.setFont("Helvetica", 20)
    subtitle_y = title_y - 30
    c.drawCentredString(width / 2, subtitle_y, f"Find & Cover – Level {level}: {LEVEL_NAMES[level]}")
    
    # Storage label boxes - 3 columns × 4 rows = 12 boxes
    cols = 3
    rows = 4
    
    box_width = 2.2 * inch
    box_height = 1.4 * inch
    h_spacing = 0.2 * inch
    v_spacing = 0.15 * inch
    
    # Calculate grid position
    grid_width = cols * box_width + (cols - 1) * h_spacing
    grid_height = rows * box_height + (rows - 1) * v_spacing
    start_x = (width - grid_width) / 2
    start_y = accent_y - 0.4 * inch - grid_height
    
    # Draw storage label boxes
    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            if idx >= len(icons):
                continue
            
            icon = icons[idx]
            
            box_x = start_x + col * (box_width + h_spacing)
            box_y = start_y + (rows - 1 - row) * (box_height + v_spacing)
            
            # Box background
            c.setFillColorRGB(0.98, 0.98, 0.98)
            c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
            c.setLineWidth(1.5)
            c.roundRect(box_x, box_y, box_width, box_height, 6, stroke=1, fill=1)
            
            # Level color strip on left
            strip_width = 0.15 * inch
            if mode == 'bw':
                c.setFillColorRGB(0.5, 0.5, 0.5)
            else:
                c.setFillColorRGB(*hex_to_rgb(level_color))
            c.roundRect(box_x, box_y, strip_width, box_height, 6, stroke=0, fill=1)
            c.rect(box_x + strip_width/2, box_y, strip_width/2, box_height, stroke=0, fill=1)
            
            # Product name
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(box_x + strip_width + 5, box_y + box_height - 15, "Find & Cover")
            
            # Theme and pack code
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(box_x + strip_width + 5, box_y + box_height - 26, f"Brown Bear | {pack_code}")
            
            # Level indicator
            c.setFont("Helvetica-Bold", 8)
            c.drawString(box_x + strip_width + 5, box_y + box_height - 38, f"Level {level}: {LEVEL_NAMES[level]}")
            
            # Icon image
            try:
                img = Image.open(icon['path'])
                if mode == 'bw':
                    img = img.convert('L').convert('RGB')
                temp_path = f'/tmp/label_icon_{idx}.png'
                img.save(temp_path)
                icon_size = 0.6 * inch
                icon_x = box_x + box_width - icon_size - 10
                icon_y = box_y + box_height - icon_size - 8
                c.drawImage(temp_path, icon_x, icon_y, 
                           width=icon_size, height=icon_size,
                           preserveAspectRatio=True, mask='auto')
            except:
                pass
            
            # Icon name
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 9)
            c.drawCentredString(box_x + box_width/2, box_y + 8, icon['name'])
    
    # Footer
    footer_y = border_margin + 0.3 * inch
    c.setFont('Helvetica', 9)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    c.drawCentredString(width/2, footer_y, footer_line2)
    
    c.setFont('Helvetica', 10)
    footer_line1 = f"Find & Cover – Storage Labels | {pack_code}"
    c.drawCentredString(width/2, footer_y + 12, footer_line1)
    
    c.showPage()

def generate_storage_labels_pdf(output_path, mode='color'):
    """Generate storage labels PDF for all levels."""
    
    icons = load_brown_bear_icons()
    if not icons:
        print(f"No icons found, cannot generate PDF")
        return None
    
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    # Generate storage labels for each level (1-5)
    for level in [1, 2, 3, 4, 5]:
        generate_storage_labels_page(c, icons, level, mode)
    
    c.save()
    print(f"✓ Generated: {output_path}")
    return output_path

def generate_level5_page(c, target_icon, all_icons, real_images, page_num, total_pages, mode='color', pack_code="BB-FC"):
    """Generate a Level 5 Find & Cover page with real photos in grid."""
    
    width, height = letter
    level = 5
    
    # Page setup
    c.setPageSize(letter)
    
    # Background white
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Page Structure - 0.25" margin from edge
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    # Draw rounded rectangle border - LIGHT BLUE
    r, g, b = hex_to_rgb(LIGHT_BLUE_BORDER)
    c.setStrokeColorRGB(r, g, b)
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent Stripe with Teal color for Level 5
    accent_margin = 0.08 * inch
    accent_height = 1.0 * inch
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin
    
    # Teal color for Level 5
    level_color = LEVEL_COLORS.get(5, '#008B8B')
    if mode == 'bw':
        c.setFillColorRGB(0.7, 0.7, 0.7)
    else:
        r, g, b = hex_to_rgb(level_color)
        c.setFillColorRGB(r, g, b)
    
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Title inside accent stripe
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))
    c.setFont('Helvetica-Bold', 36)
    title_y = accent_y + accent_height / 2 + 5
    c.drawCentredString(width / 2, title_y, "Find & Cover")
    
    # Subtitle
    c.setFont('Helvetica', 28)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    subtitle_y = title_y - 30
    c.drawCentredString(width / 2, subtitle_y, "Brown Bear - Real Photos")
    
    # Level indicator
    c.setFont('Helvetica-Bold', 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, accent_y - 20, f"Level 5: {LEVEL_NAMES[5]}")
    
    # Target box - BoardMaker icon as target
    target_box_y = accent_y - 150
    target_box_size = 100
    target_box_x = width/2 - target_box_size/2
    
    # Navy border for target box
    r, g, b = hex_to_rgb(NAVY_BORDER)
    c.setStrokeColorRGB(r, g, b)
    c.setLineWidth(3.5)
    c.roundRect(target_box_x, target_box_y, target_box_size, target_box_size, 8, fill=False, stroke=True)
    
    # Draw BoardMaker icon as target
    try:
        img = Image.open(target_icon['path'])
        if mode == 'bw':
            img = img.convert('L').convert('RGB')
        temp_path = f'/tmp/target_l5_{page_num}.png'
        img.save(temp_path)
        c.drawImage(temp_path, target_box_x + 10, target_box_y + 10, 
                   width=target_box_size - 20, height=target_box_size - 20,
                   preserveAspectRatio=True, mask='auto')
    except Exception as e:
        c.setFont('Helvetica', 12)
        c.drawCentredString(target_box_x + target_box_size/2, target_box_y + target_box_size/2, target_icon['name'][:10])
    
    # Label under target
    c.setFont('Helvetica', 12)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, target_box_y - 20, f"Find: {target_icon['name']}")
    
    # Instruction
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(width/2, target_box_y - 45, "Cover matching REAL photos")
    
    # Grid area with REAL IMAGES
    grid_start_y = target_box_y - 80
    grid_rows = 4
    grid_cols = 4
    cell_size = 100
    grid_width = grid_cols * cell_size
    grid_height = grid_rows * cell_size
    grid_start_x = width/2 - grid_width/2
    
    # Get available real images (only those that exist)
    available_real_images = [img for img in real_images if Path(img['path']).exists()]
    
    if not available_real_images:
        # No real images available - draw placeholder text
        c.setFont('Helvetica', 16)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(width/2, grid_start_y - grid_height/2, "Real images not yet available")
        c.drawCentredString(width/2, grid_start_y - grid_height/2 - 20, "Add images to assets/themes/brown_bear/real_images/")
    else:
        # Generate grid content with real images
        total_cells = grid_rows * grid_cols
        grid_content = []
        
        # Get the real image that matches the target BoardMaker icon
        target_filename = Path(target_icon['path']).name
        matching_real = get_matching_real_image(target_filename, real_images)
        
        if matching_real and Path(matching_real['path']).exists():
            # 50% of cells will be matches
            num_matches = total_cells // 2
            grid_content = [matching_real] * num_matches
            
            # Fill rest with other real images (distractors)
            other_real = [img for img in available_real_images if img['filename'] != matching_real['filename']]
            while len(grid_content) < total_cells:
                if other_real:
                    grid_content.append(random.choice(other_real))
                else:
                    grid_content.append(matching_real)
        else:
            # No matching real image - use random real images
            while len(grid_content) < total_cells:
                grid_content.append(random.choice(available_real_images))
        
        # Shuffle
        random.shuffle(grid_content)
        
        # Draw grid with real images
        for row in range(grid_rows):
            for col in range(grid_cols):
                idx = row * grid_cols + col
                x = grid_start_x + col * cell_size
                y = grid_start_y - (row + 1) * cell_size
                
                # Navy border for grid cells
                r, g, b = hex_to_rgb(NAVY_BORDER)
                c.setStrokeColorRGB(r, g, b)
                c.setLineWidth(2)
                c.roundRect(x + 2, y + 2, cell_size - 4, cell_size - 4, 6, fill=False, stroke=True)
                
                # Draw real image
                real_img = grid_content[idx]
                if real_img and Path(real_img['path']).exists():
                    try:
                        img = Image.open(real_img['path'])
                        if mode == 'bw':
                            img = img.convert('L').convert('RGB')
                        temp_path = f'/tmp/grid_l5_{page_num}_{idx}.png'
                        img.save(temp_path)
                        c.drawImage(temp_path, x + 8, y + 8,
                                   width=cell_size - 16, height=cell_size - 16,
                                   preserveAspectRatio=True, mask='auto')
                    except Exception as e:
                        pass
    
    # Footer
    footer_y = border_margin + 0.3 * inch
    c.setFont('Helvetica', 9)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line2 = "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
    c.drawCentredString(width/2, footer_y, footer_line2)
    
    c.setFont('Helvetica', 10)
    c.setFillColorRGB(*hex_to_rgb('#999999'))
    footer_line1 = f"Find & Cover – Level 5 | {pack_code} | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y + 12, footer_line1)
    
    c.showPage()

def generate_level5_pdf(output_path, mode='color'):
    """Generate Level 5 Real Photos PDF."""
    
    icons = load_brown_bear_icons()
    real_images = load_real_images()
    
    if not icons:
        print(f"No BoardMaker icons found, cannot generate PDF")
        return None
    
    if not real_images:
        print(f"Warning: No real images found, generating with placeholders")
    
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    # Only generate pages for icons that have matching real images
    icons_with_real = []
    for icon in icons:
        icon_filename = Path(icon['path']).name
        matching_real = get_matching_real_image(icon_filename, real_images)
        if matching_real and Path(matching_real['path']).exists():
            icons_with_real.append(icon)
    
    # If no matching real images, use all icons with placeholder message
    if not icons_with_real:
        icons_with_real = icons[:6]  # Just use first 6 icons as placeholders
    
    total_pages = len(icons_with_real)
    
    random.seed(42)
    for i, target_icon in enumerate(icons_with_real):
        generate_level5_page(c, target_icon, icons, real_images, i+1, total_pages, mode)
    
    c.save()
    print(f"✓ Generated: {output_path}")
    return output_path

def main():
    """Generate all Find & Cover PDFs."""
    
    # Output directories
    samples_dir = Path(__file__).parent / 'samples' / 'brown_bear' / 'find_cover'
    review_dir = Path(__file__).parent / 'review_pdfs'
    
    samples_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("GENERATING FIND & COVER LEVEL PDFs")
    print("=" * 60)
    
    # Generate Levels 1-4 in both modes
    for level in [1, 2, 3, 4]:
        for mode in ['color', 'bw']:
            filename = f"brown_bear_find_cover_level{level}_{mode}.pdf"
            
            # Generate in samples folder
            samples_path = samples_dir / filename
            generate_find_cover_pdf(samples_path, level, mode)
            
            # Copy to review folder
            review_path = review_dir / filename
            import shutil
            shutil.copy(samples_path, review_path)
            print(f"  Copied to: {review_path}")
    
    # Generate Level 5 (Real Photos)
    print("\n" + "-" * 40)
    print("GENERATING LEVEL 5: REAL PHOTOS")
    print("-" * 40)
    
    for mode in ['color', 'bw']:
        filename = f"brown_bear_find_cover_level5_{mode}.pdf"
        
        # Generate in samples folder
        samples_path = samples_dir / filename
        generate_level5_pdf(samples_path, mode)
        
        # Copy to review folder
        review_path = review_dir / filename
        import shutil
        shutil.copy(samples_path, review_path)
        print(f"  Copied to: {review_path}")
    
    # Generate storage labels
    print("\n" + "-" * 40)
    print("GENERATING STORAGE LABELS")
    print("-" * 40)
    
    for mode in ['color', 'bw']:
        filename = f"brown_bear_find_cover_storage_labels_{mode}.pdf"
        
        # Generate in samples folder
        samples_path = samples_dir / filename
        generate_storage_labels_pdf(samples_path, mode)
        
        # Copy to review folder
        review_path = review_dir / filename
        import shutil
        shutil.copy(samples_path, review_path)
        print(f"  Copied to: {review_path}")
    
    print("\n" + "=" * 60)
    print("FIND & COVER PDFs COMPLETE!")
    print("=" * 60)
    print(f"\nGenerated {5 * 2 + 2} PDF files (5 levels × 2 modes + 2 storage labels)")
    print(f"  Samples: {samples_dir}")
    print(f"  Review:  {review_dir}")

if __name__ == "__main__":
    main()
