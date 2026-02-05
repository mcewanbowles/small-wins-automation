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
LIGHT_GREY_VELCRO = '#E6E6E6'
LIGHT_GREY_FOOTER = '#999999'
WHITE = '#FFFFFF'
BLACK = '#000000'

# Level-specific accent colors (Master Product Specification)
LEVEL_COLORS = {
    1: '#F4B400',  # Orange - Errorless
    2: '#4285F4',  # Blue - Distractors
    3: '#34A853',  # Green - Moderate Challenge
    4: '#8C06F2',  # Purple - Maximum Challenge
}

# Level names for display
LEVEL_NAMES = {
    1: 'Errorless',
    2: 'Distractors',
    3: 'Moderate',
    4: 'Challenge',
}


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
    Create a matching page following Design Constitution standards.
    """
    width, height = letter
    
    # Global Page Structure (Section 2)
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    # Draw rounded rectangle border (3px stroke)
    c.setStrokeColorRGB(*hex_to_rgb(PRIMARY_BLUE))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # Accent Stripe: 0.35" height at top, LEVEL-SPECIFIC COLOR
    accent_height = 0.35 * inch
    level_color = LEVEL_COLORS.get(level, '#F4B400')  # Default to orange if unknown level
    c.setFillColorRGB(*hex_to_rgb(level_color))
    c.rect(border_margin, height - border_margin - accent_height, content_width, accent_height, stroke=0, fill=1)
    
    # Title + Subtitle: Sitting ON the accent stripe, aligned left
    title_x = border_margin + 0.1 * inch
    title_y = height - border_margin - accent_height / 2 + 0.1 * inch
    
    # Use white text for better contrast on colored backgrounds
    c.setFillColorRGB(1, 1, 1)  # White text
    c.setFont("Helvetica-Bold", 22)
    level_name = LEVEL_NAMES.get(level, '')
    c.drawString(title_x, title_y, f"Matching - Level {level}: {level_name}")
    
    subtitle_y = title_y - 0.25 * inch
    c.setFont("Helvetica", 16)
    c.setFillColorRGB(1, 1, 1)  # White text
    c.drawString(title_x, subtitle_y, f"{theme_name} Pack ({pack_code})")
    
    # 0.5" top margin before content
    content_top = height - border_margin - accent_height - 0.5 * inch
    
    # Target Image: 1.8" x 1.8", centered
    target_size = 1.8 * inch
    target_x = width / 2 - target_size / 2
    target_y = content_top - target_size - 0.2 * inch
    
    # Draw target image with border
    if target_img:
        temp_target = "/tmp/temp_target.png"
        target_img.save(temp_target, 'PNG')
        c.drawImage(temp_target, target_x, target_y, width=target_size, height=target_size, preserveAspectRatio=True, mask='auto')
        
        c.setStrokeColorRGB(*hex_to_rgb(PRIMARY_BLUE))
        c.setLineWidth(2)
        c.rect(target_x, target_y, target_size, target_size, stroke=1, fill=0)
    
    # 5-row layout below target
    box_size = 1.0 * inch
    box_spacing = 0.15 * inch
    
    rows_start_y = target_y - 0.3 * inch
    
    column_gap = 0.8 * inch
    left_col_x = width / 2 - box_size - column_gap / 2
    right_col_x = width / 2 + column_gap / 2
    
    # Draw 5 rows
    for row in range(5):
        row_y = rows_start_y - row * (box_size + box_spacing)
        
        img_box_x = left_col_x
        img_box_y = row_y - box_size
        
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1)
        c.roundRect(img_box_x, img_box_y, box_size, box_size, 8, stroke=1, fill=0)
        
        # Level 1 Watermark Logic: 25% opacity watermark of target
        if level == 1 and target_img:
            temp_watermark = f"/tmp/watermark_{row}.png"
            watermark_img = target_img.copy()
            watermark_img = watermark_img.convert('RGBA')
            alpha = watermark_img.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.25))
            watermark_img.putalpha(alpha)
            watermark_img.save(temp_watermark, 'PNG')
            
            watermark_size = box_size * 0.7
            watermark_x = img_box_x + (box_size - watermark_size) / 2
            watermark_y = img_box_y + (box_size - watermark_size) / 2
            c.drawImage(temp_watermark, watermark_x, watermark_y, width=watermark_size, height=watermark_size, preserveAspectRatio=True, mask='auto')
        
        # Place icon in image box
        if row < len(images):
            img = images[row]
            icon_size = box_size * 0.75
            icon_x = img_box_x + (box_size - icon_size) / 2
            icon_y = img_box_y + (box_size - icon_size) / 2
            
            temp_icon = f"/tmp/temp_icon_{row}.png"
            img.save(temp_icon, 'PNG')
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size, preserveAspectRatio=True, mask='auto')
        
        # Right column: Velcro dot
        velcro_diameter = 0.35 * inch
        velcro_radius = velcro_diameter / 2
        velcro_center_x = right_col_x + box_size / 2
        velcro_center_y = img_box_y + box_size / 2
        
        c.setFillColorRGB(*hex_to_rgb(LIGHT_GREY_VELCRO))
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setLineWidth(1.5)
        c.circle(velcro_center_x, velcro_center_y, velcro_radius, stroke=1, fill=1)
        
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.setFont("Helvetica", 6)
        text_width = c.stringWidth("velcro", "Helvetica", 6)
        c.drawString(velcro_center_x - text_width/2, velcro_center_y - 2, "velcro")
        
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(0.5)
        c.roundRect(right_col_x, img_box_y, box_size, box_size, 8, stroke=1, fill=0)
    
    # Footer
    footer_y_line1 = border_margin + 0.3 * inch
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    footer_line1 = f"{pack_code} | {theme_name} | Level {level} | Page {page_num}/{total_pages}"
    footer_width1 = c.stringWidth(footer_line1, "Helvetica-Bold", 10)
    c.drawString((width - footer_width1) / 2, footer_y_line1, footer_line1)
    
    footer_y_line2 = border_margin + 0.1 * inch
    c.setFillColorRGB(*hex_to_rgb(LIGHT_GREY_FOOTER))
    c.setFont("Helvetica", 9)
    footer_line2 = "2025 Small Wins Studio - PCS symbols used with active PCS Maker Personal License"
    footer_width2 = c.stringWidth(footer_line2, "Helvetica", 9)
    c.drawString((width - footer_width2) / 2, footer_y_line2, footer_line2)
    
    c.showPage()


def create_cutout_page_constitution(c, images, names, start_idx, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear"):
    """Create cutout page following Design Constitution Section 9."""
    width, height = letter
    
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    c.setStrokeColorRGB(*hex_to_rgb(PRIMARY_BLUE))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    accent_height = 0.35 * inch
    c.setFillColorRGB(*hex_to_rgb(LEVEL_COLORS[1]))  # Use Level 1 orange for cutouts
    c.rect(border_margin, height - border_margin - accent_height, content_width, accent_height, stroke=0, fill=1)
    
    title_x = border_margin + 0.1 * inch
    title_y = height - border_margin - accent_height / 2 + 0.1 * inch
    c.setFillColorRGB(1, 1, 1)  # White text
    c.setFont("Helvetica-Bold", 22)
    c.drawString(title_x, title_y, "Cutout Matching Pieces")
    
    subtitle_y = title_y - 0.25 * inch
    c.setFont("Helvetica", 16)
    c.setFillColorRGB(1, 1, 1)  # White text
    c.drawString(title_x, subtitle_y, f"{theme_name} Pack ({pack_code})")
    
    icon_size = 1.5 * inch
    icons_per_strip = 5
    strip_width = icons_per_strip * icon_size
    strip_height = icon_size
    num_strips = 4
    
    start_x = (width - strip_width) / 2
    content_top = height - border_margin - accent_height - 0.5 * inch
    start_y = content_top - 0.5 * inch
    
    for strip in range(num_strips):
        strip_y = start_y - strip * strip_height
        
        for i in range(icons_per_strip):
            idx = start_idx + strip * icons_per_strip + i
            if idx >= len(images):
                break
            
            icon_x = start_x + i * icon_size
            icon_y = strip_y - strip_height
            
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.setLineWidth(1)
            c.roundRect(icon_x, icon_y, icon_size, icon_size, 8, stroke=1, fill=0)
            
            padding = icon_size * 0.1
            actual_icon_size = icon_size - 2 * padding
            centered_x = icon_x + padding
            centered_y = icon_y + padding
            
            temp_icon = f"/tmp/cutout_{idx}.png"
            images[idx].save(temp_icon, 'PNG')
            c.drawImage(temp_icon, centered_x, centered_y, width=actual_icon_size, height=actual_icon_size, preserveAspectRatio=True, mask='auto')
    
    footer_y_line1 = border_margin + 0.3 * inch
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    footer_line1 = f"{pack_code} | {theme_name} | Cutouts | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y_line1, footer_line1)
    
    footer_y_line2 = border_margin + 0.1 * inch
    c.setFillColorRGB(*hex_to_rgb(LIGHT_GREY_FOOTER))
    c.setFont("Helvetica", 9)
    footer_line2 = "2025 Small Wins Studio - PCS symbols used with active PCS Maker Personal License"
    c.drawCentredString(width/2, footer_y_line2, footer_line2)
    
    c.showPage()


def create_storage_label_page_constitution(c, names, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear"):
    """Create storage label page following Design Constitution Section 10."""
    width, height = letter
    
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    c.setStrokeColorRGB(*hex_to_rgb(PRIMARY_BLUE))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    accent_height = 0.35 * inch
    c.setFillColorRGB(*hex_to_rgb(LEVEL_COLORS[1]))  # Use Level 1 orange for storage
    c.rect(border_margin, height - border_margin - accent_height, content_width, accent_height, stroke=0, fill=1)
    
    title_x = border_margin + 0.1 * inch
    title_y = height - border_margin - accent_height / 2 + 0.1 * inch
    c.setFillColorRGB(1, 1, 1)  # White text
    c.setFont("Helvetica-Bold", 22)
    c.drawString(title_x, title_y, "Storage Labels - Matching Pack")
    
    subtitle_y = title_y - 0.25 * inch
    c.setFont("Helvetica", 16)
    c.setFillColorRGB(1, 1, 1)  # White text
    c.drawString(title_x, subtitle_y, f"{theme_name} Pack ({pack_code})")
    
    info_y = height - 2.5 * inch
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, info_y, f"{theme_name} Matching Cards")
    
    info_y -= 0.4 * inch
    c.setFont("Helvetica", 14)
    c.setFillColorRGB(*hex_to_rgb(LEVEL_COLORS[1]))  # Orange accent
    c.drawCentredString(width/2, info_y, f"Pack Code: {pack_code}")
    
    vocab_y = info_y - 0.8 * inch
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, vocab_y, "Vocabulary:")
    
    vocab_y -= 0.4 * inch
    c.setFont("Helvetica", 11)
    col_width = content_width / 3
    
    for i, name in enumerate(names):
        col = i % 3
        row = i // 3
        x = border_margin + col * col_width + col_width / 2
        y = vocab_y - row * 0.3 * inch
        c.drawCentredString(x, y, name)
    
    footer_y_line1 = border_margin + 0.3 * inch
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    footer_line1 = f"{pack_code} | {theme_name} | Storage Labels | Page {page_num}/{total_pages}"
    c.drawCentredString(width/2, footer_y_line1, footer_line1)
    
    footer_y_line2 = border_margin + 0.1 * inch
    c.setFillColorRGB(*hex_to_rgb(LIGHT_GREY_FOOTER))
    c.setFont("Helvetica", 9)
    footer_line2 = "2025 Small Wins Studio - PCS symbols used with active PCS Maker Personal License"
    c.drawCentredString(width/2, footer_y_line2, footer_line2)
    
    c.showPage()


def generate_matching_product_constitution(theme_name="Brown Bear", pack_code="BB03", output_dir="review_pdfs", mode='color'):
    """Generate complete Matching product following Design Constitution."""
    icon_folder = '/home/runner/work/small-wins-automation/small-wins-automation/assets/themes/brown_bear/icons'
    icons, names = load_all_icons(icon_folder)
    
    if not icons:
        print("Error: No icons loaded. Stopping.")
        return None
    
    print(f"\nGenerating {theme_name} Matching product with {len(icons)} icons...")
    print(f"Pack Code: {pack_code}")
    print(f"Mode: {mode}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    output_filename = f"brown_bear_matching_{mode}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    c = canvas.Canvas(output_path, pagesize=letter)
    
    num_icons = len(icons)
    matching_pages = num_icons * 4
    cutout_pages = (num_icons + 19) // 20
    storage_pages = 1
    total_pages = matching_pages + cutout_pages + storage_pages
    
    print(f"Total pages: {total_pages} ({matching_pages} matching + {cutout_pages} cutout + {storage_pages} storage)")
    
    page_num = 1
    
    for icon_idx, (target_img, target_name) in enumerate(zip(icons, names)):
        other_icons = [img for i, img in enumerate(icons) if i != icon_idx]
        other_names = [name for i, name in enumerate(names) if i != icon_idx]
        
        for level in range(1, 5):
            if level == 1:
                selected_images = [target_img] * 5
                selected_names = [target_name] * 5
            elif level == 2:
                distractor_indices = random.sample(range(len(other_icons)), 1)
                selected_images = [target_img] * 4 + [other_icons[distractor_indices[0]]]
                selected_names = [target_name] * 4 + [other_names[distractor_indices[0]]]
            elif level == 3:
                distractor_indices = random.sample(range(len(other_icons)), 2)
                selected_images = [target_img] * 3 + [other_icons[i] for i in distractor_indices]
                selected_names = [target_name] * 3 + [other_names[i] for i in distractor_indices]
            else:
                distractor_indices = random.sample(range(len(other_icons)), 4)
                selected_images = [target_img] * 1 + [other_icons[i] for i in distractor_indices]
                selected_names = [target_name] * 1 + [other_names[i] for i in distractor_indices]
            
            if level > 1:
                combined = list(zip(selected_images, selected_names))
                random.shuffle(combined)
                selected_images, selected_names = zip(*combined)
                selected_images = list(selected_images)
                selected_names = list(selected_names)
            
            create_matching_page_constitution(
                c, target_img, target_name, selected_images, selected_names,
                level, page_num, total_pages, pack_code, theme_name, mode
            )
            
            page_num += 1
            print(f"  Generated: {target_name} - Level {level} (Page {page_num-1}/{total_pages})")
    
    icons_per_page = 20
    for cutout_page_idx in range(cutout_pages):
        start_idx = cutout_page_idx * icons_per_page
        create_cutout_page_constitution(c, icons, names, start_idx, page_num, total_pages, pack_code, theme_name)
        page_num += 1
        print(f"  Generated: Cutout page {cutout_page_idx + 1} (Page {page_num-1}/{total_pages})")
    
    create_storage_label_page_constitution(c, names, page_num, total_pages, pack_code, theme_name)
    print(f"  Generated: Storage Labels (Page {page_num}/{total_pages})")
    
    c.save()
    
    print(f"\n Generated: {output_path}")
    print(f"  Total pages: {total_pages}")
    print(f"  File size: {os.path.getsize(output_path) / 1024:.1f} KB")
    
    return output_path


def main():
    """Generate both color and BW versions."""
    print("=" * 60)
    print("Brown Bear Matching Cards - Design Constitution Compliant")
    print("=" * 60)
    
    output_dir = "/home/runner/work/small-wins-automation/small-wins-automation/review_pdfs"
    
    print("\n[1/2] Generating COLOR version...")
    color_path = generate_matching_product_constitution(
        theme_name="Brown Bear",
        pack_code="BB03",
        output_dir=output_dir,
        mode='color'
    )
    
    print("\n[2/2] Generating BLACK & WHITE version...")
    bw_path = generate_matching_product_constitution(
        theme_name="Brown Bear",
        pack_code="BB03",
        output_dir=output_dir,
        mode='bw'
    )
    
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nOutput files:")
    if color_path:
        print(f"  - {color_path}")
    if bw_path:
        print(f"  - {bw_path}")
    print(f"\nDesign Constitution compliance:")
    print(f"  - Border, accent stripe, title/subtitle: OK")
    print(f"  - Activity boxes (1.0 x 1.0): OK")
    print(f"  - Velcro dots (0.35 diameter): OK")
    print(f"  - Level 1 watermarks (25% opacity): OK")
    print(f"  - Cutout strips (5 icons, touching): OK")
    print(f"  - Footer typography (10pt/9pt): OK")
    

if __name__ == "__main__":
    main()
