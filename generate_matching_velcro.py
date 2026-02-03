#!/usr/bin/env python3
"""
Brown Bear Matching Cards Generator - 5×2 Velcro Box Layout
Generates matching activity pages with target image at top and 5-row velcro box layout below.
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import random

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Modern brand colors
PRIMARY_BLUE = '#4A90E2'
WARM_ORANGE = '#F5A623'
FRESH_GREEN = '#7ED321'
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
    - Top accent stripe
    - 2-line footer with pack code, theme name, level, page number and copyright
    """
    width, height = letter
    
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
    
    # Draw rounded rectangle border (3px primary blue)
    c.setStrokeColorRGB(*[x/255 for x in hex_to_rgb(PRIMARY_BLUE)])
    c.setLineWidth(3)
    c.roundRect(margin, margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Draw top accent stripe (warm orange)
    c.setFillColorRGB(*[x/255 for x in hex_to_rgb(WARM_ORANGE)])
    c.rect(margin, height - margin - 0.3*inch, content_width, 0.3*inch, stroke=0, fill=1)
    
    # Target image area (centered at top)
    target_area_top = height - margin - 0.5*inch
    target_area_height = 2 * inch
    target_img_size = 1.8 * inch
    target_x = width / 2 - target_img_size / 2
    target_y = target_area_top - target_img_size
    
    # Draw target image with border
    if target_img:
        # Save target image temporarily
        temp_target = "/tmp/temp_target.png"
        target_img.save(temp_target, 'PNG')
        c.drawImage(temp_target, target_x, target_y, width=target_img_size, height=target_img_size, preserveAspectRatio=True, mask='auto')
        
        # Draw border around target
        c.setStrokeColorRGB(*[x/255 for x in hex_to_rgb(PRIMARY_BLUE)])
        c.setLineWidth(2)
        c.rect(target_x, target_y, target_img_size, target_img_size, stroke=1, fill=0)
    
    # 5-row layout below target
    row_start_y = target_y - 0.5*inch
    row_height = 1.3 * inch
    row_spacing = 0.1 * inch
    
    image_box_width = 1.2 * inch
    image_box_height = 1.2 * inch
    velcro_box_width = 1.2 * inch
    velcro_box_height = 1.2 * inch
    
    column_gap = 0.5 * inch
    left_column_x = margin + 1.5 * inch
    right_column_x = left_column_x + image_box_width + column_gap
    
    # Draw 5 rows
    for row in range(5):
        row_y = row_start_y - row * (row_height + row_spacing)
        
        # Left column: Image box
        img_box_x = left_column_x
        img_box_y = row_y - image_box_height
        
        # Draw image box border
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1)
        c.rect(img_box_x, img_box_y, image_box_width, image_box_height, stroke=1, fill=0)
        
        # Place icon in image box
        if row < len(images):
            img = images[row]
            # Center icon in box with padding
            icon_size = image_box_width * 0.8
            icon_x = img_box_x + (image_box_width - icon_size) / 2
            icon_y = img_box_y + (image_box_height - icon_size) / 2
            
            # Save icon temporarily
            temp_icon = f"/tmp/temp_icon_{row}.png"
            img.save(temp_icon, 'PNG')
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size, preserveAspectRatio=True, mask='auto')
        
        # Right column: Velcro box (small circle centered in box)
        velcro_box_x = right_column_x
        velcro_box_y = row_y - velcro_box_height
        
        # Draw velcro circle (small, 25-30% of box width, centered)
        # Using 27% for optimal visibility
        circle_diameter = velcro_box_width * 0.27
        circle_radius = circle_diameter / 2
        circle_x = velcro_box_x + velcro_box_width / 2
        circle_y = velcro_box_y + velcro_box_height / 2
        
        # Light grey fill (#E6E6E6) with thin medium grey outline
        c.setFillColorRGB(*[x/255 for x in hex_to_rgb('#E6E6E6')])
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setLineWidth(1.5)
        c.circle(circle_x, circle_y, circle_radius, stroke=1, fill=1)
        
        # Optional tiny "velcro" text in circle (6-7pt)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.setFont("Helvetica", 6)
        text_width = c.stringWidth("velcro", "Helvetica", 6)
        c.drawString(circle_x - text_width/2, circle_y - 2, "velcro")
    
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


def create_cutout_page(c, images, names, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear"):
    """Create a cutout page with 6 icons in 3×2 grid."""
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(*[x/255 for x in hex_to_rgb(PRIMARY_BLUE)])
    c.drawCentredString(width/2, height - 0.75*inch, "Cutout Icons")
    
    # 3×2 grid
    cols = 3
    rows = 2
    card_width = 2 * inch
    card_height = 2 * inch
    h_spacing = 0.5 * inch
    v_spacing = 0.5 * inch
    
    grid_width = cols * card_width + (cols - 1) * h_spacing
    grid_height = rows * card_height + (rows - 1) * v_spacing
    
    start_x = (width - grid_width) / 2
    start_y = height - 1.5*inch - grid_height
    
    idx = 0
    for row in range(rows):
        for col in range(cols):
            if idx >= len(images):
                break
            
            x = start_x + col * (card_width + h_spacing)
            y = start_y + (rows - 1 - row) * (card_height + v_spacing)
            
            # Dashed border for cutting
            c.setDash(3, 3)
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.setLineWidth(1)
            c.rect(x, y, card_width, card_height, stroke=1, fill=0)
            c.setDash()  # Reset to solid
            
            # Center icon
            icon_size = card_width * 0.7
            icon_x = x + (card_width - icon_size) / 2
            icon_y = y + (card_height - icon_size) / 2
            
            # Save and draw icon
            temp_icon = f"/tmp/cutout_icon_{idx}.png"
            images[idx].save(temp_icon, 'PNG')
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size, preserveAspectRatio=True, mask='auto')
            
            idx += 1
    
    # 2-line footer with copyright
    footer_y_line1 = 0.5 * inch + 0.2 * inch
    footer_y_line2 = 0.5 * inch
    
    # Line 1: Pack code, theme, cutouts, page number
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 9)
    footer_line1 = f"{pack_code} | {theme_name} | Cutouts | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y_line1, footer_line1)
    
    # Line 2: Copyright and license
    c.setFont("Helvetica", 8)
    footer_line2 = "© 2025 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License"
    c.drawCentredString(width/2, footer_y_line2, footer_line2)
    
    c.showPage()


def create_storage_label_page(c, names, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear"):
    """Create storage label page."""
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.setFillColorRGB(*[x/255 for x in hex_to_rgb(PRIMARY_BLUE)])
    c.drawCentredString(width/2, height - 1*inch, f"{theme_name} Matching Cards")
    
    # Pack code
    c.setFont("Helvetica-Bold", 18)
    c.setFillColorRGB(*[x/255 for x in hex_to_rgb(WARM_ORANGE)])
    c.drawCentredString(width/2, height - 1.5*inch, f"Pack Code: {pack_code}")
    
    # Vocabulary list
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, height - 2.25*inch, "Vocabulary:")
    
    # List items in columns
    y_start = height - 2.75*inch
    col_width = width / 3
    items_per_col = (len(names) + 2) // 3
    
    for idx, name in enumerate(names):
        col = idx // items_per_col
        row = idx % items_per_col
        x = col * col_width + col_width / 2
        y = y_start - row * 0.3*inch
        c.drawCentredString(x, y, f"• {name}")
    
    # 2-line footer with copyright
    footer_y_line1 = 0.5 * inch + 0.2 * inch
    footer_y_line2 = 0.5 * inch
    
    # Line 1: Pack code, theme, storage label, page number
    c.setFont("Helvetica-Bold", 9)
    footer_line1 = f"{pack_code} | {theme_name} | Storage Label | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y_line1, footer_line1)
    
    # Line 2: Copyright and license
    c.setFont("Helvetica", 8)
    footer_line2 = "© 2025 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License"
    c.drawCentredString(width/2, footer_y_line2, footer_line2)
    
    c.showPage()


def generate_matching_product_velcro(icon_folder, output_dir, pack_code="BB03", theme_name="Brown Bear"):
    """
    Generate complete matching product with 5×2 velcro box layout.
    
    Returns:
        tuple: (color_pdf_path, bw_pdf_path)
    """
    # Load all icons
    icons, names = load_all_icons(icon_folder)
    
    if not icons:
        print("No icons found. Cannot generate matching product.")
        return None, None
    
    print(f"\nGenerating matching product for {len(icons)} icons...")
    print(f"Icons: {', '.join(names)}")
    
    # Calculate total pages
    matching_pages = len(icons) * 4  # 4 levels per icon
    cutout_pages = (len(icons) + 5) // 6  # 6 icons per cutout page
    storage_pages = 1
    total_pages = matching_pages + cutout_pages + storage_pages
    
    print(f"\nTotal pages: {total_pages}")
    print(f"  - Matching pages: {matching_pages} (12 icons × 4 levels)")
    print(f"  - Cutout pages: {cutout_pages}")
    print(f"  - Storage label pages: {storage_pages}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate COLOR version
    color_pdf = os.path.join(output_dir, f"{theme_name.lower().replace(' ', '_')}_matching_velcro_color.pdf")
    print(f"\nGenerating color PDF: {color_pdf}")
    
    c = canvas.Canvas(color_pdf, pagesize=letter)
    page_num = 1
    
    # Generate matching pages for each icon (4 levels each)
    for target_idx, (target_img, target_name) in enumerate(zip(icons, names)):
        print(f"\nGenerating pages for target: {target_name} ({target_idx + 1}/{len(icons)})")
        
        # Get list of distractor indices (all icons except current target)
        distractor_indices = [i for i in range(len(icons)) if i != target_idx]
        
        for level in range(1, 5):
            print(f"  Level {level}...", end=" ")
            
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
                pack_code, theme_name, mode='color'
            )
            page_num += 1
            print("Done")
    
    # Generate cutout pages
    print(f"\nGenerating {cutout_pages} cutout page(s)...")
    for cutout_page_idx in range(cutout_pages):
        start_idx = cutout_page_idx * 6
        end_idx = min(start_idx + 6, len(icons))
        cutout_icons = icons[start_idx:end_idx]
        cutout_names = names[start_idx:end_idx]
        
        create_cutout_page(c, cutout_icons, cutout_names, page_num, total_pages, pack_code, theme_name)
        page_num += 1
        print(f"  Cutout page {cutout_page_idx + 1}/{cutout_pages} done")
    
    # Generate storage label page
    print("\nGenerating storage label page...")
    create_storage_label_page(c, names, page_num, total_pages, pack_code, theme_name)
    
    c.save()
    print(f"\n✓ Color PDF saved: {color_pdf}")
    
    # Generate BW version (same structure, just note it's BW in filename)
    bw_pdf = os.path.join(output_dir, f"{theme_name.lower().replace(' ', '_')}_matching_velcro_bw.pdf")
    print(f"\nGenerating BW PDF: {bw_pdf}")
    
    # For BW, we would convert images to grayscale, but for now just create same structure
    # (In production, you'd convert all images to grayscale first)
    c_bw = canvas.Canvas(bw_pdf, pagesize=letter)
    page_num = 1
    
    # Generate matching pages for each icon (4 levels each)
    for target_idx, (target_img, target_name) in enumerate(zip(icons, names)):
        distractor_indices = [i for i in range(len(icons)) if i != target_idx]
        
        for level in range(1, 5):
            if level == 1:
                num_targets = 5
                num_distractors = 0
            elif level == 2:
                num_targets = 4
                num_distractors = 1
            elif level == 3:
                num_targets = 3
                num_distractors = 2
            else:
                num_targets = 1
                num_distractors = 4
            
            row_images = []
            row_names = []
            
            for _ in range(num_targets):
                row_images.append(target_img)
                row_names.append(target_name)
            
            if num_distractors > 0 and distractor_indices:
                selected_distractors = random.sample(distractor_indices, min(num_distractors, len(distractor_indices)))
                for dist_idx in selected_distractors:
                    row_images.append(icons[dist_idx])
                    row_names.append(names[dist_idx])
            
            combined = list(zip(row_images, row_names))
            random.shuffle(combined)
            row_images, row_names = zip(*combined) if combined else ([], [])
            
            create_matching_page_velcro(
                c_bw, target_img, target_name,
                list(row_images), list(row_names),
                level, page_num, total_pages,
                pack_code, theme_name, mode='bw'
            )
            page_num += 1
    
    for cutout_page_idx in range(cutout_pages):
        start_idx = cutout_page_idx * 6
        end_idx = min(start_idx + 6, len(icons))
        cutout_icons = icons[start_idx:end_idx]
        cutout_names = names[start_idx:end_idx]
        
        create_cutout_page(c_bw, cutout_icons, cutout_names, page_num, total_pages, pack_code, theme_name)
        page_num += 1
    
    create_storage_label_page(c_bw, names, page_num, total_pages, pack_code, theme_name)
    
    c_bw.save()
    print(f"✓ BW PDF saved: {bw_pdf}")
    
    return color_pdf, bw_pdf


if __name__ == "__main__":
    # Configuration
    ICON_FOLDER = "/home/runner/work/small-wins-automation/small-wins-automation/assets/themes/brown_bear/icons"
    OUTPUT_DIR = "/home/runner/work/small-wins-automation/small-wins-automation/samples/brown_bear/matching"
    PACK_CODE = "BB03"
    THEME_NAME = "Brown Bear"
    
    print("=" * 60)
    print("Brown Bear Matching Cards Generator")
    print("5×2 Velcro Box Layout")
    print("=" * 60)
    
    # Generate matching product
    color_pdf, bw_pdf = generate_matching_product_velcro(
        ICON_FOLDER,
        OUTPUT_DIR,
        PACK_CODE,
        THEME_NAME
    )
    
    if color_pdf and bw_pdf:
        print("\n" + "=" * 60)
        print("✓ MATCHING PRODUCT GENERATION COMPLETE")
        print("=" * 60)
        print(f"\nColor PDF: {color_pdf}")
        print(f"BW PDF: {bw_pdf}")
        print("\nBoth PDFs include:")
        print("  - Matching pages (4 levels per icon)")
        print("  - Cutout pages (6 icons per page)")
        print("  - Storage label page")
        print("\nLayout features:")
        print("  - Target image centered at top")
        print("  - 5 rows with image boxes (left) and velcro boxes (right)")
        print("  - Rounded rectangle border with accent stripe")
        print("  - Footer with pack code, theme, level, page numbers")
    else:
        print("\n✗ Generation failed - check error messages above")
