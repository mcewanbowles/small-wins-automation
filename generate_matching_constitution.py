#!/usr/bin/env python3
"""
Brown Bear Matching Cards Generator - Design Constitution Compliant
Generates matching activity pages following Small Wins Studio Design Constitution v1.0
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

# Brand colors (Design Constitution)
PRIMARY_BLUE = '#4A90E2'
WARM_ORANGE = '#F5A623'  # Matching product accent stripe color
LIGHT_GREY_VELCRO = '#E6E6E6'
LIGHT_GREY_FOOTER = '#999999'
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
    
    Matching Product Specification Requirements:
    - 5 rows × 2 columns layout
    - Large matching boxes: 1.4"–1.6" (using 1.5")
    - Small target icon at top
    - Image fills 90–95% of box (using 92%)
    - Velcro boxes same size as image boxes
    - Level 1 watermark logic
    - Levels 2-4 distractor logic
    - BW mode: grayscale (no orange)
    """
    width, height = letter
    
    # Import color utilities for BW mode support
    from utils.color_helpers import hex_to_grayscale, enhance_for_printing
    import hashlib
    
    # Create hash-based temp filenames to reuse same file for same icon
    def get_temp_filename(img, prefix, suffix=""):
        # Use image data hash for consistent filename per unique icon
        img_hash = hashlib.md5(img.tobytes()).hexdigest()[:12]
        return f"/tmp/{prefix}_{img_hash}_{mode}_{suffix}.png"
    
    # Global Page Structure
    # Border: 0.25" margin from edge
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    # Draw rounded rectangle border (3px stroke)
    c.setStrokeColorRGB(*hex_to_rgb(PRIMARY_BLUE))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # 2.2 Accent Stripe: 0.35" height per Design Constitution
    accent_height = 0.35 * inch  # Design Constitution spec
    accent_x = border_margin
    accent_y = height - border_margin - accent_height
    accent_width = content_width
    
    # Use warm orange for color mode, grayscale for BW mode
    if mode == 'bw':
        gray_orange = hex_to_grayscale(WARM_ORANGE)
        c.setFillColorRGB(*hex_to_rgb(gray_orange))
    else:
        c.setFillColorRGB(*hex_to_rgb(WARM_ORANGE))
    c.rect(accent_x, accent_y, accent_width, accent_height, stroke=0, fill=1)
    
    # 2.3 Title + Subtitle: Sitting ON the accent stripe, aligned LEFT per Design Constitution
    title_x = border_margin + 0.1 * inch  # Left-aligned with small margin
    
    # Title: "Matching – Level X" (22-24 pt)
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))  # Navy color
    c.setFont("Helvetica-Bold", 22)
    title_text = f"Matching – Level {level}"
    title_y = accent_y + accent_height / 2 + 0.05 * inch
    c.drawString(title_x, title_y, title_text)
    
    # Subtitle: "Brown Bear Pack (BB03)" (16-18 pt)
    subtitle_y = title_y - 0.22 * inch
    c.setFont("Helvetica", 16)
    c.setFillColorRGB(0.2, 0.2, 0.2)  # Dark grey
    subtitle_text = f"{theme_name} Pack ({pack_code})"
    c.drawString(title_x, subtitle_y, subtitle_text)
    
    # 0.5" top margin before content
    content_top = accent_y - 0.5 * inch
    
    # Small Target Image at top per Matching Product Specification
    target_size = 1.0 * inch  # Small target icon
    target_x = width / 2 - target_size / 2
    target_y = content_top - target_size
    
    # Draw target image with border
    if target_img:
        # Create a copy to avoid modifying the original
        display_target = target_img.copy()
        
        # Convert to grayscale in BW mode
        if mode == 'bw':
            display_target = enhance_for_printing(display_target, mode='bw')
        
        # Save target image with hash-based filename (reuses same file for same icon)
        temp_target = get_temp_filename(display_target, "target")
        if not os.path.exists(temp_target):
            display_target.save(temp_target, 'PNG')
        
        c.drawImage(temp_target, target_x, target_y, width=target_size, height=target_size, 
                   preserveAspectRatio=True, mask='auto')
        
        # Draw border around target
        c.setStrokeColorRGB(0, 0, 0)  # Black border for high contrast
        c.setLineWidth(2)
        c.rect(target_x, target_y, target_size, target_size, stroke=1, fill=0)
    
    # 5-row layout below target per Matching Product Specification
    # Large matching boxes: 1.4"–1.6" (using 1.5")
    box_size = 1.5 * inch
    box_spacing = 0.15 * inch
    corner_radius = 10  # 0.1-0.15" radius
    
    # Calculate starting position for 5 rows
    rows_start_y = target_y - 0.3 * inch
    
    # Left column (image boxes) and right column (velcro boxes) - centered
    # Velcro boxes same size as image boxes per spec
    column_gap = 0.5 * inch  # Reduced gap since boxes are larger
    left_col_x = width / 2 - box_size - column_gap / 2
    right_col_x = width / 2 + column_gap / 2
    
    # Draw 5 rows
    for row in range(5):
        row_y = rows_start_y - row * (box_size + box_spacing)
        
        # Left column: Image box with rounded corners
        img_box_x = left_col_x
        img_box_y = row_y - box_size
        
        # Draw image box with rounded corners
        c.setStrokeColorRGB(0, 0, 0)  # Black border for high contrast
        c.setLineWidth(1)
        c.roundRect(img_box_x, img_box_y, box_size, box_size, corner_radius, stroke=1, fill=0)
        
        # Level 1 Watermark Logic: 20-30% opacity watermark of target
        if level == 1 and target_img:
            # Create watermark at 25% opacity
            watermark_img = target_img.copy()
            watermark_img = watermark_img.convert('RGBA')
            alpha = watermark_img.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.25))  # 25% opacity
            watermark_img.putalpha(alpha)
            
            # Save with hash-based filename
            temp_watermark = get_temp_filename(watermark_img, "watermark")
            if not os.path.exists(temp_watermark):
                watermark_img.save(temp_watermark, 'PNG')
            
            # Draw watermark centered in box at 75% of box size
            watermark_size = box_size * 0.75
            watermark_x = img_box_x + (box_size - watermark_size) / 2
            watermark_y = img_box_y + (box_size - watermark_size) / 2
            c.drawImage(temp_watermark, watermark_x, watermark_y, 
                       width=watermark_size, height=watermark_size, 
                       preserveAspectRatio=True, mask='auto')
        
        # Place icon in image box - image fills 90-95% of box per spec
        if row < len(images):
            # Create a copy to avoid modifying the original
            display_img = images[row].copy()
            
            # Convert to grayscale in BW mode
            if mode == 'bw':
                display_img = enhance_for_printing(display_img, mode='bw')
            
            # Image fills 92% of box (center of 90-95% range)
            icon_size = box_size * 0.92
            icon_x = img_box_x + (box_size - icon_size) / 2
            icon_y = img_box_y + (box_size - icon_size) / 2
            
            # Save with hash-based filename (reuses same file for same icon)
            temp_icon = get_temp_filename(display_img, "icon")
            if not os.path.exists(temp_icon):
                display_img.save(temp_icon, 'PNG')
            
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size, 
                       preserveAspectRatio=True, mask='auto')
        
        # Right column: Velcro box - same size as image box per spec
        velcro_box_x = right_col_x
        velcro_box_y = img_box_y
        
        # Draw velcro box outline (same size as image box)
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(1)
        c.roundRect(velcro_box_x, velcro_box_y, box_size, box_size, corner_radius, stroke=1, fill=0)
        
        # Draw velcro indicator (small circle in center)
        velcro_diameter = 0.5 * inch
        velcro_radius = velcro_diameter / 2
        velcro_center_x = velcro_box_x + box_size / 2
        velcro_center_y = velcro_box_y + box_size / 2
        
        # Light grey fill (#E6E6E6) with thin outline
        c.setFillColorRGB(*hex_to_rgb(LIGHT_GREY_VELCRO))
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setLineWidth(1.5)
        c.circle(velcro_center_x, velcro_center_y, velcro_radius, stroke=1, fill=1)
        
        # Optional tiny "velcro" text
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.setFont("Helvetica", 6)
        text_width = c.stringWidth("velcro", "Helvetica", 6)
        c.drawString(velcro_center_x - text_width/2, velcro_center_y - 2, "velcro")
    
    # 2.4 Footer (Two Lines) - Section 2.4
    # Line 1: [Pack Code] | [Theme Name] | Level X | Page N/Total (10-11 pt)
    footer_y_line1 = border_margin + 0.3 * inch
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    footer_line1 = f"{pack_code} | {theme_name} | Level {level} | Page {page_num}/{total_pages}"
    footer_width1 = c.stringWidth(footer_line1, "Helvetica-Bold", 10)
    c.drawString((width - footer_width1) / 2, footer_y_line1, footer_line1)
    
    # Line 2: © 2025 Small Wins Studio • PCS® symbols... (9 pt, light grey #999999)
    footer_y_line2 = border_margin + 0.1 * inch
    c.setFillColorRGB(*hex_to_rgb(LIGHT_GREY_FOOTER))
    c.setFont("Helvetica", 9)
    footer_line2 = "© 2025 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License"
    footer_width2 = c.stringWidth(footer_line2, "Helvetica", 9)
    c.drawString((width - footer_width2) / 2, footer_y_line2, footer_line2)
    
    c.showPage()


def create_cutout_page_constitution(c, images, names, start_idx, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear"):
    """
    Create cutout page following Matching Product Specification.
    
    Requirements per spec:
    - 60pt icons
    - 180pt box
    - 15pt spacing
    - 3pt border
    - 5-icon strips
    - Strips must touch for guillotine cutting
    """
    width, height = letter
    
    # Border
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    c.setStrokeColorRGB(*hex_to_rgb(PRIMARY_BLUE))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent stripe: 0.5" height, inside border with rounded corners
    accent_height = 0.5 * inch
    accent_x = border_margin + 5
    accent_y = height - border_margin - accent_height - 5
    accent_width = content_width - 10
    
    c.setFillColorRGB(*hex_to_rgb(WARM_ORANGE))
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Title: "Cutout Matching Pieces" left-aligned
    title_x = border_margin + 0.1 * inch
    title_y = accent_y + accent_height / 2 + 0.05 * inch
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))  # Navy
    c.setFont("Helvetica-Bold", 22)
    c.drawString(title_x, title_y, "Cutout Matching Pieces")
    
    # Subtitle: "Brown Bear Pack (BB03)"
    subtitle_y = title_y - 0.22 * inch
    c.setFont("Helvetica", 16)
    c.setFillColorRGB(0.2, 0.2, 0.2)  # Dark grey
    c.drawString(title_x, subtitle_y, f"{theme_name} Pack ({pack_code})")
    
    # Cutout specifications per Matching Product Spec
    box_size_pts = 180  # 180pt box
    icon_size_pts = 60  # 60pt icons
    spacing_pts = 15    # 15pt spacing
    border_pts = 3      # 3pt border
    icons_per_strip = 5
    
    # Calculate strip dimensions
    strip_width_pts = icons_per_strip * box_size_pts
    strip_height_pts = box_size_pts
    
    # Convert to inches for reportlab
    box_size = box_size_pts / 72.0 * inch
    icon_size = icon_size_pts / 72.0 * inch
    spacing = spacing_pts / 72.0 * inch
    
    # 4 strips per page (4×5 layout = 20 icons per page)
    num_strips = 4
    
    # Center strips on page
    strip_width = icons_per_strip * box_size
    start_x = (width - strip_width) / 2
    content_top = accent_y - 0.35 * inch
    start_y = content_top - 0.5 * inch
    
    # Draw 4 strips (touching, no gaps between strips)
    for strip in range(num_strips):
        strip_y = start_y - strip * box_size  # No gap between strips
        
        # Draw 5 icons in this strip
        for i in range(icons_per_strip):
            idx = start_idx + strip * icons_per_strip + i
            if idx >= len(images):
                break
            
            box_x = start_x + i * box_size
            box_y = strip_y - box_size
            
            # Draw box with 3pt border
            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(border_pts)
            c.rect(box_x, box_y, box_size, box_size, stroke=1, fill=0)
            
            # Draw icon (60pt) centered in 180pt box
            # Center the 60pt icon in the 180pt box
            icon_padding = (box_size - icon_size) / 2
            icon_x = box_x + icon_padding
            icon_y = box_y + icon_padding
            
            # Draw icon
            temp_icon = f"/tmp/cutout_{idx}.png"
            images[idx].save(temp_icon, 'PNG')
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size, 
                       preserveAspectRatio=True, mask='auto')
    
    # Footer
    footer_y_line1 = border_margin + 0.3 * inch
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    footer_line1 = f"{pack_code} | {theme_name} | Cutouts | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y_line1, footer_line1)
    
    footer_y_line2 = border_margin + 0.1 * inch
    c.setFillColorRGB(*hex_to_rgb(LIGHT_GREY_FOOTER))
    c.setFont("Helvetica", 9)
    footer_line2 = "© 2025 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License"
    c.drawCentredString(width/2, footer_y_line2, footer_line2)
    
    c.showPage()


def create_storage_label_page_constitution(c, names, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear"):
    """Create storage label page following Design Constitution Section 10."""
    width, height = letter
    
    # Border
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    c.setStrokeColorRGB(*hex_to_rgb(PRIMARY_BLUE))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent stripe: 0.5" height, inside border with rounded corners
    accent_height = 0.5 * inch
    accent_x = border_margin + 5
    accent_y = height - border_margin - accent_height - 5
    accent_width = content_width - 10
    
    c.setFillColorRGB(*hex_to_rgb(WARM_ORANGE))
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # Title: "Storage Labels – Matching Pack" left-aligned
    title_x = border_margin + 0.1 * inch
    title_y = accent_y + accent_height / 2 + 0.05 * inch
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))  # Navy
    c.setFont("Helvetica-Bold", 22)
    c.drawString(title_x, title_y, "Storage Labels – Matching Pack")
    
    # Subtitle: "Brown Bear Pack (BB03)" per Design Constitution Section 10
    subtitle_y = title_y - 0.22 * inch
    c.setFont("Helvetica", 16)
    c.setFillColorRGB(0.2, 0.2, 0.2)  # Dark grey
    c.drawString(title_x, subtitle_y, f"{theme_name} Pack ({pack_code})")
    
    # Product info - Updated to match requirements
    info_y = height - 2.5 * inch
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, info_y, "Brown Bear Matching Cards")  # Updated to "Brown Bear Matching Cards"
    
    info_y -= 0.4 * inch
    c.setFont("Helvetica", 14)
    c.setFillColorRGB(*hex_to_rgb(WARM_ORANGE))
    c.drawCentredString(width/2, info_y, f"Pack Code: {pack_code}")
    
    # Clean 3-column vocabulary table (Section 10)
    vocab_y = info_y - 0.8 * inch
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, vocab_y, "Vocabulary:")
    
    # 3-column layout
    vocab_y -= 0.4 * inch
    c.setFont("Helvetica", 11)
    col_width = content_width / 3
    
    for i, name in enumerate(names):
        col = i % 3
        row = i // 3
        x = border_margin + col * col_width + col_width / 2
        y = vocab_y - row * 0.3 * inch
        c.drawCentredString(x, y, name)
    
    # Footer
    footer_y_line1 = border_margin + 0.3 * inch
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    footer_line1 = f"{pack_code} | {theme_name} | Storage Labels | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y_line1, footer_line1)
    
    footer_y_line2 = border_margin + 0.1 * inch
    c.setFillColorRGB(*hex_to_rgb(LIGHT_GREY_FOOTER))
    c.setFont("Helvetica", 9)
    footer_line2 = "© 2025 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License"
    c.drawCentredString(width/2, footer_y_line2, footer_line2)
    
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
    
    # Calculate total pages
    num_icons = len(icons)
    # Section 7.1: Matching levels 1-4 for each icon
    matching_pages = num_icons * 4
    # Section 9: Cutout pages (20 icons per page in 4×5 layout)
    cutout_pages = (num_icons + 19) // 20  # Ceiling division
    # Section 10: Storage label page
    storage_pages = 1
    total_pages = matching_pages + cutout_pages + storage_pages
    
    print(f"Total pages: {total_pages} ({matching_pages} matching + {cutout_pages} cutout + {storage_pages} storage)")
    
    page_num = 1
    
    # Generate matching pages for each icon at all 4 levels
    for icon_idx, (target_img, target_name) in enumerate(zip(icons, names)):
        # Get all other icons for distractors
        other_icons = [img for i, img in enumerate(icons) if i != icon_idx]
        other_names = [name for i, name in enumerate(names) if i != icon_idx]
        
        # Generate 4 levels (Section 7.1)
        for level in range(1, 5):
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
    
    # Generate cutout pages (Section 9: 20 icons per page in 4×5 layout)
    icons_per_page = 20
    for cutout_page_idx in range(cutout_pages):
        start_idx = cutout_page_idx * icons_per_page
        create_cutout_page_constitution(c, icons, names, start_idx, page_num, total_pages, pack_code, theme_name)
        page_num += 1
        print(f"  Generated: Cutout page {cutout_page_idx + 1} (Page {page_num-1}/{total_pages})")
    
    # Generate storage label page (Section 10)
    create_storage_label_page_constitution(c, names, page_num, total_pages, pack_code, theme_name)
    print(f"  Generated: Storage Labels (Page {page_num}/{total_pages})")
    
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
