#!/usr/bin/env python3
"""
Brown Bear Matching Cards Generator - EXACT SPEC from design/product_specs/matching.md
Matches the finalized product exactly - Updated with user feedback improvements.
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import Color
import random

# EXACT COLORS FROM SPEC
NAVY_BORDER = '#1E3A5F'           # Target box and matching box borders
PURPLE_BORDER = '#6B5BE2'         # Velcro box border
VELCRO_FILL = '#E8E8E8'           # Light grey velcro box fill
VELCRO_DOT_FILL = '#CCCCCC'       # Velcro dot fill
VELCRO_DOT_OUTLINE = '#999999'    # Velcro dot outline
FOOTER_GREY = '#999999'           # Footer line 2

# LEVEL-SPECIFIC ACCENT COLORS (per user request)
LEVEL_COLORS = {
    1: '#F5A623',   # Orange - Errorless
    2: '#4285F4',   # Blue - Easy
    3: '#34A853',   # Green - Medium
    4: '#8C06F2',   # Purple - Hard
}


def load_all_icons(icon_folder):
    """Load all PNG icons from the specified folder."""
    icons = []
    names = []
    
    if not os.path.exists(icon_folder):
        print(f"Error: Icon folder not found: {icon_folder}")
        return icons, names
    
    png_files = sorted([f for f in os.listdir(icon_folder) if f.lower().endswith('.png') and not f.startswith('.')])
    
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


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple (0-1 range for reportlab)."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (r/255, g/255, b/255)


def create_matching_page_spec(c, target_img, target_name, images, names, level, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear", mode='color'):
    """
    Create a matching page following EXACT SPEC from design/product_specs/matching.md
    Updated with user feedback improvements.
    """
    width, height = letter  # 8.5" x 11"
    
    # ===== PAGE BORDER =====
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    # Draw page border (navy)
    c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
    c.setLineWidth(2)
    c.roundRect(border_margin, border_margin, content_width, content_height, 8, stroke=1, fill=0)
    
    # ===== ACCENT STRIPE (Section 8) =====
    # DEEPER ACCENT STRIPE - per user request
    stripe_margin = 0.1 * inch
    stripe_height = 0.85 * inch  # DEEPER (was 0.6")
    stripe_x = border_margin + stripe_margin
    stripe_y = height - border_margin - stripe_margin - stripe_height
    stripe_width = content_width - 2 * stripe_margin
    
    # Get level-specific color - EACH LEVEL MUST USE CORRECT COLOR
    accent_color = LEVEL_COLORS.get(level, LEVEL_COLORS[1])
    
    if mode == 'color':
        c.setFillColorRGB(*hex_to_rgb(accent_color))
    else:
        c.setFillColorRGB(0.7, 0.7, 0.7)  # Grayscale for BW
    c.roundRect(stripe_x, stripe_y, stripe_width, stripe_height, 6, stroke=0, fill=1)
    
    # ===== TITLE + SUBTITLE (CENTERED VERTICALLY AND HORIZONTALLY in accent stripe) =====
    c.setFillColorRGB(1, 1, 1)  # White text on accent
    
    # Calculate vertical center of stripe for PERFECT centering
    stripe_center_y = stripe_y + stripe_height / 2
    
    # Title: "MATCHING" - centered
    c.setFont("Helvetica-Bold", 26)  # Larger for MATCHING title
    title_text = "MATCHING"
    title_width = c.stringWidth(title_text, "Helvetica-Bold", 26)
    title_x = (width - title_width) / 2
    title_y = stripe_center_y + 0.12 * inch  # Above center
    c.drawString(title_x, title_y, title_text)
    
    # Subtitle: Theme name - centered
    c.setFont("Helvetica", 16)
    subtitle_text = theme_name
    subtitle_width = c.stringWidth(subtitle_text, "Helvetica", 16)
    subtitle_x = (width - subtitle_width) / 2
    subtitle_y = stripe_center_y - 0.18 * inch  # Below center
    c.drawString(subtitle_x, subtitle_y, subtitle_text)
    
    # ===== INSTRUCTION LINE (Section 1) =====
    instruction_y = stripe_y - 0.25 * inch
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)  # Slightly smaller
    instruction_text = f"Match the {target_name}"
    instruction_width = c.stringWidth(instruction_text, "Helvetica-Bold", 12)
    c.drawString((width - instruction_width) / 2, instruction_y, instruction_text)
    
    # ===== TARGET BOX (Section 2) - SMALLER =====
    # IMPROVED: Much smaller target box
    target_box_size = 0.75 * inch  # Reduced further to 0.75"
    target_box_x = (width - target_box_size) / 2
    target_box_y = instruction_y - target_box_size - 0.1 * inch
    
    # Draw soft shadow
    c.setFillColorRGB(0, 0, 0)
    c.setFillAlpha(0.07)
    c.roundRect(target_box_x + 2, target_box_y - 2, target_box_size, target_box_size, 6, stroke=0, fill=1)
    c.setFillAlpha(1.0)
    
    # Draw target box with white fill and navy border
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
    c.setLineWidth(2.5)
    c.roundRect(target_box_x, target_box_y, target_box_size, target_box_size, 6, stroke=1, fill=1)
    
    # Draw target image - MAX SIZE NO PADDING
    if target_img:
        temp_target = "/tmp/temp_target.png"
        target_img.save(temp_target, 'PNG')
        icon_size = target_box_size * 0.95  # Max size, minimal padding
        icon_x = target_box_x + (target_box_size - icon_size) / 2
        icon_y = target_box_y + (target_box_size - icon_size) / 2
        c.drawImage(temp_target, icon_x, icon_y, width=icon_size, height=icon_size, preserveAspectRatio=True, mask='auto')
    
    # ===== MATCHING BOXES AND VELCRO BOXES (Sections 3, 4) =====
    # IMPROVED: Slightly larger boxes, wider column spacing, centered on page
    box_size = 1.35 * inch  # Increased slightly from 1.25" per user request
    column_gap = 1.8 * inch  # Good spacing between columns
    row_spacing = 0.06 * inch  # Tight spacing between rows
    
    # Calculate grid dimensions
    total_grid_height = 5 * box_size + 4 * row_spacing
    footer_height = 0.45 * inch  # Reserve space for footer
    grid_bottom = border_margin + footer_height
    grid_top = target_box_y - 0.1 * inch
    
    # Center the grid vertically in available space
    available_height = grid_top - grid_bottom
    if total_grid_height > available_height:
        # Scale down box size if needed
        box_size = (available_height - 4 * row_spacing) / 5
    
    grid_start_y = grid_bottom + (available_height - total_grid_height) / 2 + total_grid_height
    
    # Center columns horizontally - CENTERED AND ALIGNED on page
    total_width = 2 * box_size + column_gap
    left_col_x = (width - total_width) / 2
    right_col_x = left_col_x + box_size + column_gap
    
    for row in range(5):
        row_y = grid_start_y - row * (box_size + row_spacing) - box_size
        
        # ===== LEFT COLUMN: MATCHING BOX (Section 3) =====
        c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
        c.setLineWidth(2.5)
        c.setFillColorRGB(1, 1, 1)
        c.roundRect(left_col_x, row_y, box_size, box_size, 6, stroke=1, fill=1)
        
        # Draw icon - MAX SIZE NO PADDING (98% fill)
        if row < len(images):
            img = images[row]
            temp_icon = f"/tmp/temp_icon_{row}.png"
            img.save(temp_icon, 'PNG')
            icon_size = box_size * 0.98  # MAX SIZE, no padding
            icon_x = left_col_x + (box_size - icon_size) / 2
            icon_y = row_y + (box_size - icon_size) / 2
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size, preserveAspectRatio=True, mask='auto')
        
        # ===== RIGHT COLUMN: VELCRO BOX (Section 4) =====
        c.setFillColorRGB(*hex_to_rgb(VELCRO_FILL))
        c.setStrokeColorRGB(*hex_to_rgb(PURPLE_BORDER))
        c.setLineWidth(2.5)
        c.roundRect(right_col_x, row_y, box_size, box_size, 6, stroke=1, fill=1)
        
        # Level 1: Watermark in velcro box (Section 5.1)
        if level == 1 and target_img:
            temp_watermark = f"/tmp/watermark_velcro_{row}.png"
            watermark_img = target_img.copy().convert('RGBA')
            alpha = watermark_img.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.25))
            watermark_img.putalpha(alpha)
            watermark_img.save(temp_watermark, 'PNG')
            wm_size = box_size * 0.70
            wm_x = right_col_x + (box_size - wm_size) / 2
            wm_y = row_y + (box_size - wm_size) / 2
            c.drawImage(temp_watermark, wm_x, wm_y, width=wm_size, height=wm_size, preserveAspectRatio=True, mask='auto')
        
        # Velcro dot - SMALLER
        velcro_diameter = 0.18 * inch  # Reduced from 0.2"
        velcro_center_x = right_col_x + box_size / 2
        velcro_center_y = row_y + box_size / 2
        c.setFillColorRGB(*hex_to_rgb(VELCRO_DOT_FILL))
        c.setStrokeColorRGB(*hex_to_rgb(VELCRO_DOT_OUTLINE))
        c.setLineWidth(1)
        c.circle(velcro_center_x, velcro_center_y, velcro_diameter / 2, stroke=1, fill=1)
    
    # ===== FOOTER (Section 10) =====
    footer_line1_y = border_margin + 0.22 * inch
    footer_line2_y = border_margin + 0.08 * inch
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 9)
    footer_line1 = f"Matching - Level {level} | {pack_code}"
    c.drawCentredString(width / 2, footer_line1_y, footer_line1)
    
    c.setFillColorRGB(*hex_to_rgb(FOOTER_GREY))
    c.setFont("Helvetica", 8)
    footer_line2 = "2025 Small Wins Studio. PCS symbols used with active PCS Maker Personal License."
    c.drawCentredString(width / 2, footer_line2_y, footer_line2)
    
    c.showPage()


def create_cutout_page_spec(c, images, names, start_idx, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear", mode='color'):
    """Create cutout page following EXACT SPEC Section 7."""
    width, height = letter
    
    # Page border
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
    c.setLineWidth(2)
    c.roundRect(border_margin, border_margin, content_width, content_height, 8, stroke=1, fill=0)
    
    # Accent stripe - use orange for cutouts
    stripe_margin = 0.1 * inch
    stripe_height = 0.6 * inch
    stripe_x = border_margin + stripe_margin
    stripe_y = height - border_margin - stripe_margin - stripe_height
    stripe_width = content_width - 2 * stripe_margin
    
    if mode == 'color':
        c.setFillColorRGB(*hex_to_rgb(LEVEL_COLORS[1]))  # Orange
    else:
        c.setFillColorRGB(0.7, 0.7, 0.7)
    c.roundRect(stripe_x, stripe_y, stripe_width, stripe_height, 6, stroke=0, fill=1)
    
    # Title centered in stripe
    stripe_center_y = stripe_y + stripe_height / 2
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 20)
    title_text = "Cutout Matching Pieces"
    title_width = c.stringWidth(title_text, "Helvetica-Bold", 20)
    c.drawString((width - title_width) / 2, stripe_center_y + 0.08 * inch, title_text)
    
    c.setFont("Helvetica", 14)
    subtitle_text = theme_name
    subtitle_width = c.stringWidth(subtitle_text, "Helvetica", 14)
    c.drawString((width - subtitle_width) / 2, stripe_center_y - 0.18 * inch, subtitle_text)
    
    # 4 columns x 5 rows = 20 boxes (Section 7)
    box_size = 1.4 * inch
    cols = 4
    rows = 5
    
    grid_width = cols * box_size
    grid_height = rows * box_size
    grid_x = (width - grid_width) / 2
    grid_top = stripe_y - 0.3 * inch
    
    for row in range(rows):
        for col in range(cols):
            idx = start_idx + row * cols + col
            if idx >= len(images):
                break
            
            box_x = grid_x + col * box_size
            box_y = grid_top - (row + 1) * box_size
            
            c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
            c.setLineWidth(2.5)
            c.setFillColorRGB(1, 1, 1)
            c.rect(box_x, box_y, box_size, box_size, stroke=1, fill=1)
            
            temp_icon = f"/tmp/cutout_{idx}.png"
            images[idx].save(temp_icon, 'PNG')
            icon_size = box_size * 0.85
            icon_x = box_x + (box_size - icon_size) / 2
            icon_y = box_y + (box_size - icon_size) / 2
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size, preserveAspectRatio=True, mask='auto')
    
    # Footer
    footer_line1_y = border_margin + 0.22 * inch
    footer_line2_y = border_margin + 0.08 * inch
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width / 2, footer_line1_y, f"Cutouts | {pack_code}")
    
    c.setFillColorRGB(*hex_to_rgb(FOOTER_GREY))
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, footer_line2_y, "2025 Small Wins Studio. PCS symbols used with active PCS Maker Personal License.")
    
    c.showPage()


def create_storage_label_page_spec(c, icons, names, page_num, total_pages, pack_code="BB03", theme_name="Brown Bear", mode='color'):
    """Create storage label page."""
    width, height = letter
    
    # Page border
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    c.setStrokeColorRGB(*hex_to_rgb(NAVY_BORDER))
    c.setLineWidth(2)
    c.roundRect(border_margin, border_margin, content_width, content_height, 8, stroke=1, fill=0)
    
    # Accent stripe - orange
    stripe_margin = 0.1 * inch
    stripe_height = 0.6 * inch
    stripe_x = border_margin + stripe_margin
    stripe_y = height - border_margin - stripe_margin - stripe_height
    stripe_width = content_width - 2 * stripe_margin
    
    if mode == 'color':
        c.setFillColorRGB(*hex_to_rgb(LEVEL_COLORS[1]))
    else:
        c.setFillColorRGB(0.7, 0.7, 0.7)
    c.roundRect(stripe_x, stripe_y, stripe_width, stripe_height, 6, stroke=0, fill=1)
    
    # Title centered in stripe
    stripe_center_y = stripe_y + stripe_height / 2
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 20)
    title_text = "Storage Labels"
    title_width = c.stringWidth(title_text, "Helvetica-Bold", 20)
    c.drawString((width - title_width) / 2, stripe_center_y + 0.08 * inch, title_text)
    
    c.setFont("Helvetica", 14)
    subtitle_text = f"{theme_name} Matching Cards"
    subtitle_width = c.stringWidth(subtitle_text, "Helvetica", 14)
    c.drawString((width - subtitle_width) / 2, stripe_center_y - 0.18 * inch, subtitle_text)
    
    # Pack info
    info_y = stripe_y - 0.5 * inch
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, info_y, f"Pack Code: {pack_code}")
    
    # Vocabulary header
    vocab_y = info_y - 0.4 * inch
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, vocab_y, "Vocabulary:")
    
    # Display icons with labels in 3 columns
    col_width = content_width / 3
    icon_display_size = 0.55 * inch
    items_per_col = 4
    
    for i, (img, name) in enumerate(zip(icons[:12], names[:12])):
        col = i % 3
        row = i // 3
        
        x = border_margin + col * col_width + col_width / 2
        y = vocab_y - 0.4 * inch - row * (icon_display_size + 0.25 * inch)
        
        temp_icon = f"/tmp/storage_{i}.png"
        img.save(temp_icon, 'PNG')
        c.drawImage(temp_icon, x - icon_display_size/2, y - icon_display_size, 
                   width=icon_display_size, height=icon_display_size, 
                   preserveAspectRatio=True, mask='auto')
        
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0, 0, 0)
        label_width = c.stringWidth(name, "Helvetica", 9)
        c.drawString(x - label_width/2, y - icon_display_size - 0.12 * inch, name)
    
    # Footer
    footer_line1_y = border_margin + 0.22 * inch
    footer_line2_y = border_margin + 0.08 * inch
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width / 2, footer_line1_y, f"Storage Labels | {pack_code}")
    
    c.setFillColorRGB(*hex_to_rgb(FOOTER_GREY))
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, footer_line2_y, "2025 Small Wins Studio. PCS symbols used with active PCS Maker Personal License.")
    
    c.showPage()


def generate_matching_product_spec(theme_name="Brown Bear", pack_code="BB03", output_dir="review_pdfs", mode='color'):
    """Generate complete Matching product following EXACT SPEC."""
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
    cutout_pages = 1
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
                distractor_idx = random.choice(range(len(other_icons)))
                selected_images = [target_img] * 4 + [other_icons[distractor_idx]]
                selected_names = [target_name] * 4 + [other_names[distractor_idx]]
            elif level == 3:
                distractor_indices = random.sample(range(len(other_icons)), 2)
                selected_images = [target_img] * 3 + [other_icons[i] for i in distractor_indices]
                selected_names = [target_name] * 3 + [other_names[i] for i in distractor_indices]
            else:
                distractor_indices = random.sample(range(len(other_icons)), 4)
                selected_images = [target_img] + [other_icons[i] for i in distractor_indices]
                selected_names = [target_name] + [other_names[i] for i in distractor_indices]
            
            if level > 1:
                combined = list(zip(selected_images, selected_names))
                random.shuffle(combined)
                selected_images, selected_names = zip(*combined)
                selected_images = list(selected_images)
                selected_names = list(selected_names)
            
            create_matching_page_spec(
                c, target_img, target_name, selected_images, selected_names,
                level, page_num, total_pages, pack_code, theme_name, mode
            )
            
            page_num += 1
            print(f"  Generated: {target_name} - Level {level} (Page {page_num-1}/{total_pages})")
    
    create_cutout_page_spec(c, icons, names, 0, page_num, total_pages, pack_code, theme_name, mode)
    page_num += 1
    print(f"  Generated: Cutout page (Page {page_num-1}/{total_pages})")
    
    create_storage_label_page_spec(c, icons, names, page_num, total_pages, pack_code, theme_name, mode)
    print(f"  Generated: Storage Labels (Page {page_num}/{total_pages})")
    
    c.save()
    
    print(f"\n Generated: {output_path}")
    print(f"  Total pages: {total_pages}")
    print(f"  File size: {os.path.getsize(output_path) / 1024:.1f} KB")
    
    return output_path


def main():
    """Generate both color and BW versions following EXACT SPEC."""
    print("=" * 60)
    print("Brown Bear Matching Cards - IMPROVED VERSION")
    print("Following design/product_specs/matching.md + User Feedback")
    print("=" * 60)
    print("\nImprovements applied:")
    print("  - Title/Subtitle better centered in accent stripe")
    print("  - Target box smaller (0.85\" instead of 1.2\")")
    print("  - Grid boxes smaller (1.25\" instead of 1.5\")")
    print("  - Column spacing wider (2.0\" gap)")
    print("  - Velcro circle smaller (0.2\" instead of 0.3\")")
    print("  - Level-specific accent colors:")
    print("    L1=Orange, L2=Blue, L3=Green, L4=Purple")
    
    output_dir = "/home/runner/work/small-wins-automation/small-wins-automation/review_pdfs"
    
    print("\n[1/2] Generating COLOR version...")
    color_path = generate_matching_product_spec(
        theme_name="Brown Bear",
        pack_code="BB03",
        output_dir=output_dir,
        mode='color'
    )
    
    print("\n[2/2] Generating BLACK & WHITE version...")
    bw_path = generate_matching_product_spec(
        theme_name="Brown Bear",
        pack_code="BB03",
        output_dir=output_dir,
        mode='bw'
    )
    
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE - IMPROVED VERSION")
    print("=" * 60)
    print(f"\nOutput files:")
    if color_path:
        print(f"  - {color_path}")
    if bw_path:
        print(f"  - {bw_path}")


if __name__ == "__main__":
    main()
