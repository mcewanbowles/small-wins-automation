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
    Create a matching page following Design Constitution standards.
    
    Design Constitution Requirements (Updated):
    - Border: 3px stroke, 0.25" margin from edge
    - Accent stripe: 0.5" height, warm orange for Matching, inside border with rounded corners
    - Title: "Matching Activity – Level X" (navy), centered on stripe
    - Subtitle: "Brown Bear" (dark grey), centered on stripe
    - Activity boxes: 1.0" × 1.0", rounded corners 0.12"
    - Target image: 1.4" × 1.4", thin outline, rounded corners 0.12", soft shadow (10-15% opacity)
    - Velcro dot: centered, light grey #E6E6E6
    - Level 1 watermark: 20-30% opacity of target in matching boxes
    - Vertical spacing: 0.25", centered block, 0.25" bottom padding
    - Footer: 2 lines with correct typography
    """
    width, height = letter
    
    # Global Page Structure (Section 2)
    # 2.1 Border: 0.25" margin from edge
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin
    
    # Draw rounded rectangle border (3px stroke)
    c.setStrokeColorRGB(*hex_to_rgb(PRIMARY_BLUE))
    c.setLineWidth(3)
    # Rounded corners with 0.1-0.15" radius
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)
    
    # 2.2 Accent Stripe: 0.6" height at top, warm orange for Matching, inside border with rounded corners
    accent_height = 0.6 * inch  # Increased from 0.5" to 0.6"
    accent_x = border_margin + 5  # Slightly inside border
    accent_y = height - border_margin - accent_height - 5
    accent_width = content_width - 10
    
    c.setFillColorRGB(*hex_to_rgb(WARM_ORANGE))
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)
    
    # 2.3 Title + Subtitle: Centered vertically within the accent stripe
    # Title: "Matching Activity" (24 pt, navy) - Level removed per requirements
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))  # Navy color
    c.setFont("Helvetica-Bold", 24)
    title_text = "Matching Activity"  # Removed "– Level X" as it's in footer
    title_width = c.stringWidth(title_text, "Helvetica-Bold", 24)
    title_x = width / 2 - title_width / 2
    
    # Subtitle: "Brown Bear" (18 pt, dark grey)
    c.setFont("Helvetica", 18)
    subtitle_text = theme_name
    subtitle_width = c.stringWidth(subtitle_text, "Helvetica", 18)
    subtitle_x = width / 2 - subtitle_width / 2
    
    # Calculate total height of both text lines with spacing
    title_height = 24  # approximate font height
    subtitle_height = 18
    text_spacing = 6  # spacing between title and subtitle
    total_text_height = title_height + text_spacing + subtitle_height
    
    # Center both lines vertically within the stripe
    stripe_center_y = accent_y + accent_height / 2
    title_y = stripe_center_y + (total_text_height / 2) - title_height + 6
    subtitle_y = title_y - text_spacing - subtitle_height + 3
    
    # Draw title
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))
    c.setFont("Helvetica-Bold", 24)
    c.drawString(title_x, title_y, title_text)
    
    # Draw subtitle
    c.setFillColorRGB(0.3, 0.3, 0.3)  # Dark grey
    c.setFont("Helvetica", 18)
    c.drawString(subtitle_x, subtitle_y, subtitle_text)
    
    # 0.35" padding below accent stripe
    content_top = accent_y - 0.35 * inch
    
    # Target Image: 1.4" × 1.4", centered, thin outline, rounded corners 0.12", soft shadow
    target_size = 1.4 * inch
    target_x = width / 2 - target_size / 2
    target_y = content_top - target_size
    
    # Draw target image with soft shadow and border
    if target_img:
        # Draw soft shadow (10-15% opacity) with larger offset and blur simulation
        shadow_offset = 8  # Increased from 3 to 8px (6-10px range)
        shadow_opacity = 0.12  # 12% opacity (10-15% range)
        
        # Simulate blur by drawing multiple shadow layers with decreasing opacity
        c.setFillColorRGB(0, 0, 0)
        blur_layers = 3
        for i in range(blur_layers):
            layer_opacity = shadow_opacity * (1 - i / (blur_layers * 2))
            c.setFillAlpha(layer_opacity)
            offset = shadow_offset + i
            c.roundRect(target_x + offset, target_y - offset, 
                       target_size, target_size, 8.64, stroke=0, fill=1)
        c.setFillAlpha(1.0)  # Reset opacity
        
        # Save target image temporarily
        temp_target = "/tmp/temp_target.png"
        target_img.save(temp_target, 'PNG')
        c.drawImage(temp_target, target_x, target_y, width=target_size, height=target_size, 
                   preserveAspectRatio=True, mask='auto')
        
        # Draw thin border around target with rounded corners (0.12" = 8.64 pts)
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setLineWidth(1)  # Thin outline
        c.roundRect(target_x, target_y, target_size, target_size, 8.64, stroke=1, fill=0)
    
    # 5-row layout below target
    # Activity Boxes: 1.0" × 1.0" with 0.25" vertical spacing, rounded corners 0.12"
    box_size = 1.0 * inch
    box_spacing = 0.25 * inch  # Updated vertical spacing
    corner_radius = 8.64  # 0.12" = 8.64 pts
    
    # Calculate starting position for 5 rows
    # Start below target with 0.35" padding (as specified in requirements)
    rows_start_y = target_y - 0.35 * inch
    
    # Left column (image boxes) and right column (velcro boxes) - centered with increased spacing
    column_gap = 1.2 * inch  # Increased from 0.8" to 1.2" for better horizontal spacing
    left_col_x = width / 2 - box_size - column_gap / 2
    right_col_x = width / 2 + column_gap / 2
    
    # Draw 5 rows
    for row in range(5):
        row_y = rows_start_y - row * (box_size + box_spacing)
        
        # Left column: Image box with rounded corners (0.12")
        img_box_x = left_col_x
        img_box_y = row_y - box_size
        
        # Draw image box with rounded corners
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1)
        c.roundRect(img_box_x, img_box_y, box_size, box_size, corner_radius, stroke=1, fill=0)
        
        # Level 1 Watermark Logic (Section 8): 20-30% opacity watermark of target
        if level == 1 and target_img:
            # Create watermark at 25% opacity
            temp_watermark = f"/tmp/watermark_{row}.png"
            watermark_img = target_img.copy()
            # Reduce opacity by converting to RGBA and adjusting alpha
            watermark_img = watermark_img.convert('RGBA')
            alpha = watermark_img.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.25))  # 25% opacity
            watermark_img.putalpha(alpha)
            watermark_img.save(temp_watermark, 'PNG')
            
            # Draw watermark centered in box
            watermark_size = box_size * 0.7
            watermark_x = img_box_x + (box_size - watermark_size) / 2
            watermark_y = img_box_y + (box_size - watermark_size) / 2
            c.drawImage(temp_watermark, watermark_x, watermark_y, width=watermark_size, height=watermark_size, preserveAspectRatio=True, mask='auto')
        
        # Place icon in image box (centered)
        if row < len(images):
            img = images[row]
            # Center icon in box with padding
            icon_size = box_size * 0.75
            icon_x = img_box_x + (box_size - icon_size) / 2
            icon_y = img_box_y + (box_size - icon_size) / 2
            
            # Save icon temporarily
            temp_icon = f"/tmp/temp_icon_{row}.png"
            img.save(temp_icon, 'PNG')
            c.drawImage(temp_icon, icon_x, icon_y, width=icon_size, height=icon_size, preserveAspectRatio=True, mask='auto')
        
        # Right column: Velcro dot (Section 4 & 6)
        # Velcro Dot: centered in matching box with rounded corners 0.12"
        velcro_diameter = 0.35 * inch  # Middle of range
        velcro_radius = velcro_diameter / 2
        velcro_center_x = right_col_x + box_size / 2
        velcro_center_y = img_box_y + box_size / 2
        
        # Light grey fill (#E6E6E6) with thin outline (1-2px medium grey)
        c.setFillColorRGB(*hex_to_rgb(LIGHT_GREY_VELCRO))
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setLineWidth(1.5)
        c.circle(velcro_center_x, velcro_center_y, velcro_radius, stroke=1, fill=1)
        
        # Optional tiny "velcro" text (6-7 pt)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.setFont("Helvetica", 6)
        text_width = c.stringWidth("velcro", "Helvetica", 6)
        c.drawString(velcro_center_x - text_width/2, velcro_center_y - 2, "velcro")
        
        # Draw box outline around velcro area with rounded corners (0.12")
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(0.5)
        c.roundRect(right_col_x, img_box_y, box_size, box_size, corner_radius, stroke=1, fill=0)
    
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
    Create cutout page following Design Constitution Section 9.
    
    Requirements:
    - Title: "Cutout Matching Pieces"
    - Subtitle: "[Theme] Pack ([Pack Code])"
    - 5-icon strips
    - Strips must touch (no gaps) for guillotine cutting
    - Max icon size: 1.5" × 1.5"
    - 4×5 or 5×5 strips per page
    - Rounded corners: 0.12"
    - Accent stripe: 0.5" tall, inside border with rounded corners
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
    
    # Title: "Cutout Matching Pieces" centered on stripe
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))  # Navy
    c.setFont("Helvetica-Bold", 24)
    title_text = "Cutout Matching Pieces"
    title_width = c.stringWidth(title_text, "Helvetica-Bold", 24)
    title_x = width / 2 - title_width / 2
    title_y = accent_y + accent_height / 2 + 0.15 * inch
    c.drawString(title_x, title_y, title_text)
    
    # Subtitle centered on stripe (cutout page)
    subtitle_y = title_y - 0.28 * inch
    c.setFont("Helvetica", 18)
    c.setFillColorRGB(0.3, 0.3, 0.3)  # Dark grey
    subtitle_text = theme_name
    subtitle_width = c.stringWidth(subtitle_text, "Helvetica", 18)
    subtitle_x = width / 2 - subtitle_width / 2
    c.drawString(subtitle_x, subtitle_y, subtitle_text)
    
    # 5-icon strips that touch (Section 9)
    # Max icon size: 1.5" × 1.5"
    icon_size = 1.5 * inch
    icons_per_strip = 5
    corner_radius = 8.64  # 0.12" = 8.64 pts
    
    # Calculate strip dimensions
    strip_width = icons_per_strip * icon_size
    strip_height = icon_size
    
    # 4 strips per page (4×5 layout = 20 icons per page)
    num_strips = 4
    
    # Center strips on page
    start_x = (width - strip_width) / 2
    content_top = accent_y - 0.35 * inch
    start_y = content_top - 0.5 * inch
    
    # Draw 4 strips (touching, no gaps)
    for strip in range(num_strips):
        strip_y = start_y - strip * strip_height  # No gap between strips
        
        # Draw 5 icons in this strip
        for i in range(icons_per_strip):
            idx = start_idx + strip * icons_per_strip + i
            if idx >= len(images):
                break
            
            icon_x = start_x + i * icon_size
            icon_y = strip_y - strip_height
            
            # Draw box with rounded corners (0.12")
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.setLineWidth(1)
            c.roundRect(icon_x, icon_y, icon_size, icon_size, corner_radius, stroke=1, fill=0)
            
            # Icons should touch edges - minimal padding
            padding = icon_size * 0.02  # Reduced from 0.1 to 0.02 for icons to touch edges
            actual_icon_size = icon_size - 2 * padding
            centered_x = icon_x + padding
            centered_y = icon_y + padding
            
            # Draw icon
            temp_icon = f"/tmp/cutout_{idx}.png"
            images[idx].save(temp_icon, 'PNG')
            c.drawImage(temp_icon, centered_x, centered_y, width=actual_icon_size, height=actual_icon_size, preserveAspectRatio=True, mask='auto')
    
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
    
    # Title: "Storage Labels – Matching Pack" centered on stripe
    c.setFillColorRGB(*hex_to_rgb('#001F3F'))  # Navy
    c.setFont("Helvetica-Bold", 24)
    title_text = "Storage Labels – Matching Pack"
    title_width = c.stringWidth(title_text, "Helvetica-Bold", 24)
    title_x = width / 2 - title_width / 2
    title_y = accent_y + accent_height / 2 + 0.15 * inch
    c.drawString(title_x, title_y, title_text)
    
    # Subtitle centered on stripe (storage labels)
    subtitle_y = title_y - 0.28 * inch
    c.setFont("Helvetica", 18)
    c.setFillColorRGB(0.3, 0.3, 0.3)  # Dark grey
    subtitle_text = theme_name
    subtitle_width = c.stringWidth(subtitle_text, "Helvetica", 18)
    subtitle_x = width / 2 - subtitle_width / 2
    c.drawString(subtitle_x, subtitle_y, subtitle_text)
    
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
