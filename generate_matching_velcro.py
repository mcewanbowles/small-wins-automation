#!/usr/bin/env python3
"""
Brown Bear Matching Cards Generator - 5×2 Velcro Box Layout
Based on user's finalized code with improvements:
- Separate PDF per level (all 12 icons + cutouts + storage for each level)
- Cutouts: 4×5 grid (same size as activity boxes, guillotine-friendly)
- Level-specific colors: L1=Orange, L2=Blue, L3=Green, L4=Purple
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import random

# Level-specific colors
LEVEL_COLORS = {
    1: '#F5A623',  # Orange - Errorless
    2: '#4285F4',  # Blue - Easy
    3: '#34A853',  # Green - Medium
    4: '#8C06F2',  # Purple - Hard
}

# Other brand colors
PRIMARY_BLUE = '#4A90E2'
LIGHT_GREY = '#D3D3D3'
WHITE = '#FFFFFF'
BLACK = '#000000'


def load_all_icons(icon_folder):
    """Load all PNG icons from the specified folder."""
    icons = []
    names = []
    
    if not os.path.exists(icon_folder):
        print(f"Warning: Icon folder not found: {icon_folder}")
        return icons, names
    
    # Get all PNG files
    png_files = sorted([f for f in os.listdir(icon_folder) if f.lower().endswith('.png')])
    
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
            names.append(name)
            print(f"  Loaded: {filename} -> {name}")
        except Exception as e:
            print(f"  Error loading {filename}: {e}")
    
    return icons, names


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_matching_page_velcro(c, target_img, target_name, images, names, level, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear", mode='color'):
    """
    Create a single matching page with 5×2 velcro box layout.
    
    Layout:
    - Page title at top-left above accent stripe
    - Target image centered at top
    - 5 rows below with 2 columns each:
      - Left: Image box with icon
      - Right: Velcro box (small circle, 25-30% of box width)
    - Rounded rectangle border
    - Top accent stripe (level-specific color)
    - 2-line footer with pack code, theme name, level, page number and copyright
    """
    width, height = letter
    
    # Get level-specific color
    level_color = LEVEL_COLORS.get(level, LEVEL_COLORS[1])
    
    # Page margins and dimensions
    margin = 0.5 * inch
    content_width = width - 2 * margin
    content_height = height - 2 * margin
    
    # Page titles (above accent stripe)
    title_y = height - margin + 0.15 * inch
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(margin + 0.1*inch, title_y, f"Matching Activity – Level {level}")
    
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawString(margin + 0.1*inch, title_y - 0.2*inch, f"{theme_name} Pack ({pack_code})")
    
    # Draw rounded rectangle border (3px in level color)
    c.setStrokeColorRGB(*[x/255 for x in hex_to_rgb(level_color)])
    c.setLineWidth(3)
    c.roundRect(margin, margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Draw top accent stripe (level-specific color)
    c.setFillColorRGB(*[x/255 for x in hex_to_rgb(level_color)])
    c.rect(margin, height - margin - 0.3*inch, content_width, 0.3*inch, stroke=0, fill=1)
    
    # Target image area (centered at top)
    target_area_top = height - margin - 0.5*inch
    target_img_size = 1.8 * inch
    target_x = width / 2 - target_img_size / 2
    target_y = target_area_top - target_img_size
    
    # Draw target image with border
    if target_img:
        # Save target image temporarily
        temp_target = "/tmp/temp_target.png"
        target_img.save(temp_target, 'PNG')
        c.drawImage(temp_target, target_x, target_y, width=target_img_size, height=target_img_size, preserveAspectRatio=True, mask='auto')
        
        # Draw border around target (level color)
        c.setStrokeColorRGB(*[x/255 for x in hex_to_rgb(level_color)])
        c.setLineWidth(2)
        c.rect(target_x, target_y, target_img_size, target_img_size, stroke=1, fill=0)
    
    # 5-row layout below target
    row_start_y = target_y - 0.5*inch
    row_height = 1.2 * inch
    row_spacing = 0.1 * inch
    
    image_box_size = 1.2 * inch
    velcro_box_size = 1.2 * inch
    
    column_gap = 0.8 * inch  # Wider gap between columns
    total_row_width = image_box_size + column_gap + velcro_box_size
    left_column_x = (width - total_row_width) / 2
    right_column_x = left_column_x + image_box_size + column_gap
    
    # Draw 5 rows
    for row in range(5):
        row_y = row_start_y - row * (row_height + row_spacing)
        
        # Left column: Image box
        img_box_x = left_column_x
        img_box_y = row_y - image_box_size
        
        # Draw image box border (level color)
        c.setStrokeColorRGB(*[x/255 for x in hex_to_rgb(level_color)])
        c.setLineWidth(1.5)
        c.rect(img_box_x, img_box_y, image_box_size, image_box_size, stroke=1, fill=0)
        
        # Place icon in image box
        if row < len(images):
            img = images[row]
            # Center icon in box with minimal padding (max size)
            icon_size = image_box_size * 0.9
            icon_x = img_box_x + (image_box_size - icon_size) / 2
            icon_y = img_box_y + (image_box_size - icon_size) / 2
            
            # Save icon temporarily
            temp_icon = f"/tmp/temp_icon_{row}.png"
            img.save(temp_icon, 'PNG')
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size, preserveAspectRatio=True, mask='auto')
        
        # Right column: Velcro box (small circle centered in box)
        velcro_box_x = right_column_x
        velcro_box_y = row_y - velcro_box_size
        
        # Draw velcro circle (small, 25% of box width, centered)
        circle_diameter = velcro_box_size * 0.25
        circle_radius = circle_diameter / 2
        circle_x = velcro_box_x + velcro_box_size / 2
        circle_y = velcro_box_y + velcro_box_size / 2
        
        # Light grey fill with thin medium grey outline
        c.setFillColorRGB(*[x/255 for x in hex_to_rgb('#E6E6E6')])
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setLineWidth(1.5)
        c.circle(circle_x, circle_y, circle_radius, stroke=1, fill=1)
    
    # 2-line footer with copyright
    footer_y_line1 = margin + 0.35 * inch
    footer_y_line2 = margin + 0.15 * inch
    
    # Line 1: Pack code, theme, level, page number
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 9)
    footer_line1 = f"{pack_code} | {theme_name} | Level {level} | Page {page_num}/{total_pages}"
    footer_width1 = c.stringWidth(footer_line1, "Helvetica-Bold", 9)
    c.drawString((width - footer_width1) / 2, footer_y_line1, footer_line1)
    
    # Line 2: Copyright and license
    c.setFont("Helvetica", 8)
    footer_line2 = "© 2025 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License"
    footer_width2 = c.stringWidth(footer_line2, "Helvetica", 8)
    c.drawString((width - footer_width2) / 2, footer_y_line2, footer_line2)
    
    c.showPage()


def create_cutout_page(c, images, names, level, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear"):
    """
    Create a cutout page with 4×5 grid (4 columns, 5 rows = 20 icons max).
    Same size as activity boxes, guillotine-friendly (icons touch).
    """
    width, height = letter
    level_color = LEVEL_COLORS.get(level, LEVEL_COLORS[1])
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(*[x/255 for x in hex_to_rgb(level_color)])
    c.drawCentredString(width/2, height - 0.6*inch, f"Cutout Icons - Level {level}")
    
    # 4×5 grid (same size as activity boxes: 1.2")
    cols = 4
    rows = 5
    card_size = 1.2 * inch  # Same as activity box
    
    # No spacing between cards for guillotine cutting
    grid_width = cols * card_size
    grid_height = rows * card_size
    
    start_x = (width - grid_width) / 2
    start_y = height - 1.0*inch
    
    idx = 0
    for row in range(rows):
        for col in range(cols):
            if idx >= len(images):
                break
            
            x = start_x + col * card_size
            y = start_y - (row + 1) * card_size
            
            # Thin dashed border for cutting guide
            c.setDash(2, 2)
            c.setStrokeColorRGB(0.6, 0.6, 0.6)
            c.setLineWidth(0.5)
            c.rect(x, y, card_size, card_size, stroke=1, fill=0)
            c.setDash()  # Reset to solid
            
            # Icon fills most of the box (90%)
            icon_size = card_size * 0.9
            icon_x = x + (card_size - icon_size) / 2
            icon_y = y + (card_size - icon_size) / 2
            
            # Save and draw icon
            temp_icon = f"/tmp/cutout_icon_{idx}.png"
            images[idx].save(temp_icon, 'PNG')
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size, preserveAspectRatio=True, mask='auto')
            
            idx += 1
    
    # 2-line footer
    footer_y_line1 = 0.45 * inch
    footer_y_line2 = 0.25 * inch
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 9)
    footer_line1 = f"{pack_code} | {theme_name} | Level {level} Cutouts | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y_line1, footer_line1)
    
    c.setFont("Helvetica", 8)
    footer_line2 = "© 2025 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License"
    c.drawCentredString(width/2, footer_y_line2, footer_line2)
    
    c.showPage()


def create_storage_label_page(c, names, level, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear"):
    """Create storage label page for this level."""
    width, height = letter
    level_color = LEVEL_COLORS.get(level, LEVEL_COLORS[1])
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.setFillColorRGB(*[x/255 for x in hex_to_rgb(level_color)])
    c.drawCentredString(width/2, height - 1*inch, f"{theme_name} Matching Cards")
    
    # Level indicator
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 1.4*inch, f"Level {level}")
    
    # Pack code
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawCentredString(width/2, height - 1.9*inch, f"Pack Code: {pack_code}")
    
    # Vocabulary list
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, height - 2.5*inch, "Vocabulary:")
    
    # List items in 3 columns
    c.setFont("Helvetica", 11)
    y_start = height - 2.9*inch
    col_width = width / 3
    items_per_col = (len(names) + 2) // 3
    
    for idx, name in enumerate(names):
        col = idx // items_per_col
        row = idx % items_per_col
        x = col * col_width + col_width / 2
        y = y_start - row * 0.35*inch
        c.drawCentredString(x, y, f"• {name}")
    
    # 2-line footer
    footer_y_line1 = 0.45 * inch
    footer_y_line2 = 0.25 * inch
    
    c.setFont("Helvetica-Bold", 9)
    footer_line1 = f"{pack_code} | {theme_name} | Level {level} Storage Label | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y_line1, footer_line1)
    
    c.setFont("Helvetica", 8)
    footer_line2 = "© 2025 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License"
    c.drawCentredString(width/2, footer_y_line2, footer_line2)
    
    c.showPage()


def generate_level_pdf(icons, names, level, output_dir, pack_code, theme_name, mode='color'):
    """
    Generate a complete PDF for one level.
    Contains: All 12 activity pages + cutout page + storage label page
    """
    # Calculate total pages: 12 activity + 1 cutout + 1 storage = 14 pages
    total_pages = len(icons) + 2  # activity pages + cutout + storage
    
    # Output filename
    mode_suffix = 'color' if mode == 'color' else 'bw'
    filename = f"{theme_name.lower().replace(' ', '_')}_matching_level{level}_{mode_suffix}.pdf"
    pdf_path = os.path.join(output_dir, filename)
    
    print(f"\n  Generating Level {level} ({mode}): {filename}")
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    page_num = 1
    
    # Get distractor indices (all icons except current target)
    all_indices = list(range(len(icons)))
    
    # Determine target/distractor counts based on level
    if level == 1:
        num_targets = 5
        num_distractors = 0
    elif level == 2:
        num_targets = 4
        num_distractors = 1
    elif level == 3:
        num_targets = 3
        num_distractors = 2
    else:  # level == 4
        num_targets = 1
        num_distractors = 4
    
    # Generate activity page for each icon
    for target_idx, (target_img, target_name) in enumerate(zip(icons, names)):
        # Get distractor indices (all except current target)
        distractor_indices = [i for i in all_indices if i != target_idx]
        
        # Build list of images for the 5 rows
        row_images = []
        row_names = []
        
        # Add targets
        for _ in range(num_targets):
            row_images.append(target_img)
            row_names.append(target_name)
        
        # Add distractors (randomly selected)
        if num_distractors > 0 and distractor_indices:
            selected_distractors = random.sample(distractor_indices, min(num_distractors, len(distractor_indices)))
            for dist_idx in selected_distractors:
                row_images.append(icons[dist_idx])
                row_names.append(names[dist_idx])
        
        # Shuffle the list so targets and distractors are mixed
        combined = list(zip(row_images, row_names))
        random.shuffle(combined)
        row_images, row_names = zip(*combined) if combined else ([], [])
        
        # Create matching page
        create_matching_page_velcro(
            c, target_img, target_name,
            list(row_images), list(row_names),
            level, page_num, total_pages,
            pack_code, theme_name, mode
        )
        page_num += 1
    
    # Generate cutout page (4×5 grid)
    create_cutout_page(c, icons, names, level, page_num, total_pages, pack_code, theme_name)
    page_num += 1
    
    # Generate storage label page
    create_storage_label_page(c, names, level, page_num, total_pages, pack_code, theme_name)
    
    c.save()
    print(f"    ✓ Saved: {pdf_path} ({total_pages} pages)")
    
    return pdf_path


def generate_matching_product(icon_folder, output_dir, pack_code="BB03", theme_name="Brown Bear"):
    """
    Generate complete matching product with separate PDF per level.
    
    Output structure:
    - level1_color.pdf (12 activity + cutout + storage = 14 pages)
    - level1_bw.pdf
    - level2_color.pdf
    - level2_bw.pdf
    - level3_color.pdf
    - level3_bw.pdf
    - level4_color.pdf
    - level4_bw.pdf
    """
    # Load all icons
    icons, names = load_all_icons(icon_folder)
    
    if not icons:
        print("No icons found. Cannot generate matching product.")
        return []
    
    print(f"\nGenerating matching product for {len(icons)} icons...")
    print(f"Icons: {', '.join(names)}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    generated_pdfs = []
    
    # Generate PDF for each level (1-4)
    for level in range(1, 5):
        print(f"\n{'='*50}")
        print(f"LEVEL {level}")
        print(f"{'='*50}")
        
        # Color version
        color_pdf = generate_level_pdf(icons, names, level, output_dir, pack_code, theme_name, 'color')
        generated_pdfs.append(color_pdf)
        
        # BW version
        bw_pdf = generate_level_pdf(icons, names, level, output_dir, pack_code, theme_name, 'bw')
        generated_pdfs.append(bw_pdf)
    
    return generated_pdfs


if __name__ == "__main__":
    # Configuration
    ICON_FOLDER = "/home/runner/work/small-wins-automation/small-wins-automation/assets/themes/brown_bear/icons"
    OUTPUT_DIR = "/home/runner/work/small-wins-automation/small-wins-automation/review_pdfs"
    PACK_CODE = "BB03"
    THEME_NAME = "Brown Bear"
    
    print("=" * 60)
    print("Brown Bear Matching Cards Generator")
    print("5×2 Velcro Box Layout - Separate PDF per Level")
    print("=" * 60)
    
    # Generate matching product
    pdfs = generate_matching_product(
        ICON_FOLDER,
        OUTPUT_DIR,
        PACK_CODE,
        THEME_NAME
    )
    
    if pdfs:
        print("\n" + "=" * 60)
        print("✓ MATCHING PRODUCT GENERATION COMPLETE")
        print("=" * 60)
        print(f"\nGenerated {len(pdfs)} PDFs:")
        for pdf in pdfs:
            print(f"  • {os.path.basename(pdf)}")
        print("\nEach level PDF contains:")
        print("  - 12 activity pages (one per icon)")
        print("  - 1 cutout page (4×5 grid, guillotine-friendly)")
        print("  - 1 storage label page")
        print("\nLevel colors:")
        print("  - Level 1: 🟠 Orange (Errorless)")
        print("  - Level 2: 🔵 Blue (Easy)")
        print("  - Level 3: 🟢 Green (Medium)")
        print("  - Level 4: 🟣 Purple (Hard)")
    else:
        print("\n✗ Generation failed - check error messages above")
