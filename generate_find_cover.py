#!/usr/bin/env python3
"""
Generate Find & Cover Level PDFs for Brown Bear theme.
Produces all 4 levels in both color and BW versions.
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

# Level colors for accent strips
LEVEL_COLORS = {
    1: '#FF8C42',  # Orange
    2: '#4A90E2',  # Blue
    3: '#7CB342',  # Green
    4: '#9C27B0',  # Purple
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
    """Generate a single Find & Cover page."""
    
    # Page setup
    c.setPageSize(letter)
    
    # Background
    if mode == 'bw':
        c.setFillColorRGB(1, 1, 1)
    else:
        c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)
    
    # Page border
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setLineWidth(2)
    c.rect(MARGIN/2, MARGIN/2, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN, fill=False, stroke=True)
    
    # Level color accent strip at top
    level_color = LEVEL_COLORS.get(level, '#FF8C42')
    if mode == 'color':
        r, g, b = hex_to_rgb(level_color)
        c.setFillColorRGB(r, g, b)
    else:
        c.setFillColorRGB(0.7, 0.7, 0.7)
    c.rect(MARGIN/2, PAGE_HEIGHT - MARGIN/2 - 30, PAGE_WIDTH - MARGIN, 30, fill=True, stroke=False)
    
    # Title
    c.setFillColorRGB(0, 0, 0)
    c.setFont('Helvetica-Bold', 24)
    title = "Find & Cover"
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - MARGIN - 50, title)
    
    # Level indicator
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - MARGIN - 70, f"Level {level}: {LEVEL_NAMES[level]}")
    
    # Target box
    target_box_y = PAGE_HEIGHT - MARGIN - 200
    target_box_size = 100
    target_box_x = PAGE_WIDTH/2 - target_box_size/2
    
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(2)
    c.rect(target_box_x, target_box_y, target_box_size, target_box_size, fill=False, stroke=True)
    
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
    c.drawCentredString(PAGE_WIDTH/2, target_box_y - 20, f"Find: {target_icon['name']}")
    
    # Instruction
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(PAGE_WIDTH/2, target_box_y - 45, "Cover all matching pictures")
    
    # Grid area
    grid_start_y = target_box_y - 80
    grid_rows = 4
    grid_cols = 4
    cell_size = 100
    grid_width = grid_cols * cell_size
    grid_height = grid_rows * cell_size
    grid_start_x = PAGE_WIDTH/2 - grid_width/2
    
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
    
    # Draw grid
    for row in range(grid_rows):
        for col in range(grid_cols):
            idx = row * grid_cols + col
            x = grid_start_x + col * cell_size
            y = grid_start_y - (row + 1) * cell_size
            
            # Cell border
            c.setStrokeColorRGB(0.3, 0.3, 0.3)
            c.setLineWidth(1)
            
            if level == 4:
                # Draw circle for cut & paste
                center_x = x + cell_size/2
                center_y = y + cell_size/2
                c.circle(center_x, center_y, cell_size/2 - 5, fill=False, stroke=True)
            else:
                c.rect(x + 2, y + 2, cell_size - 4, cell_size - 4, fill=False, stroke=True)
                
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
    
    # Footer
    c.setFont('Helvetica', 10)
    c.drawCentredString(PAGE_WIDTH/2, MARGIN, "© 2025 Small Wins Studio")
    c.drawRightString(PAGE_WIDTH - MARGIN, MARGIN, f"Brown Bear Find & Cover - Level {level}")
    
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
