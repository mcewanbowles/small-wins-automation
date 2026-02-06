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
}

LEVEL_NAMES = {
    1: 'Errorless',
    2: 'Mixed',
    3: 'Challenging',
    4: 'Cut & Paste'
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

def generate_find_cover_page(c, target_icon, all_icons, level, page_num, mode='color'):
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
        # Errorless: All match target
        grid_content = [target_icon] * total_cells
    elif level == 2:
        # Mixed: 50% match
        num_matches = total_cells // 2
        grid_content = [target_icon] * num_matches
        distractors = [icon for icon in all_icons if icon['name'] != target_icon['name']]
        while len(grid_content) < total_cells and distractors:
            grid_content.append(random.choice(distractors))
    elif level == 3:
        # Challenging: Fewer matches
        num_matches = total_cells // 3
        grid_content = [target_icon] * num_matches
        distractors = [icon for icon in all_icons if icon['name'] != target_icon['name']]
        while len(grid_content) < total_cells and distractors:
            grid_content.append(random.choice(distractors))
    elif level == 4:
        # Cut & Paste: Empty circles
        grid_content = [None] * total_cells
    
    # Fill remaining with distractors if needed
    distractors = [icon for icon in all_icons if icon['name'] != target_icon['name']]
    while len(grid_content) < total_cells:
        if distractors:
            grid_content.append(random.choice(distractors))
        else:
            grid_content.append(target_icon)
    
    # Shuffle (except level 4)
    if level != 4:
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
            
            if level == 4:
                # Draw circle for cut & paste
                center_x = x + cell_size/2
                center_y = y + cell_size/2
                c.circle(center_x, center_y, cell_size/2 - 5, fill=False, stroke=True)
            else:
                # Rounded rect for grid cells
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
    
    # Footer with proper styling
    border_margin = 0.25 * inch
    c.setFont('Helvetica', 10)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawCentredString(width/2, border_margin + 5, "© 2025 Small Wins Studio")
    c.drawRightString(width - border_margin - 10, border_margin + 5, f"BB-FC Level {level}")
    
    c.showPage()

def generate_find_cover_pdf(output_path, level, mode='color'):
    """Generate a Find & Cover PDF for a specific level."""
    
    icons = load_brown_bear_icons()
    if not icons:
        print(f"No icons found, cannot generate PDF")
        return None
    
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    # Generate pages for each target
    random.seed(42)  # Reproducible randomness
    for i, target_icon in enumerate(icons):
        generate_find_cover_page(c, target_icon, icons, level, i+1, mode)
    
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
    
    # Generate all levels in both modes
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
    
    print("\n" + "=" * 60)
    print("FIND & COVER PDFs COMPLETE!")
    print("=" * 60)
    print(f"\nGenerated {4 * 2} PDF files (4 levels × 2 modes)")
    print(f"  Samples: {samples_dir}")
    print(f"  Review:  {review_dir}")

if __name__ == "__main__":
    main()
