#!/usr/bin/env python3
"""
Comprehensive Matching Cards Generator for Brown Bear Theme

Generates complete matching activity product with:
- All 4 difficulty levels for every icon in the theme
- Target-and-distractor format (not matching pairs)
- Cutout pages
- Storage label pages
- Modern brand styling
- Dual-mode output (color + BW)

Rules:
- Level 1: 5 targets, 0 distractors (errorless)
- Level 2: 4 targets, 1 distractor
- Level 3: 3 targets, 2 distractors
- Level 4: 1 target, 4 distractors
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.units import inch
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from themes.theme_loader import load_theme
from utils.color_helpers import image_to_grayscale


# Modern brand colors
BRAND_COLORS = {
    'primary': '#4A90E2',      # Modern blue
    'secondary': '#F5A623',     # Warm orange
    'accent': '#7ED321',        # Fresh green
    'text': '#4A4A4A',          # Charcoal
    'border': '#E0E0E0',        # Light grey
    'background': '#FFFFFF',     # White
}

# Updated spacing and layout
SPACING = {
    'page_margin': 0.5 * inch,
    'card_spacing': 0.2 * inch,
    'icon_padding': 0.15 * inch,
    'footer_height': 0.4 * inch,
}

# Icon sizing
ICON_SIZE = (1.2 * inch, 1.2 * inch)  # Updated icon size
CARD_SIZE = (1.5 * inch, 1.5 * inch)  # Updated card size


def clean_icon_name(filename):
    """Extract clean name from icon filename."""
    name = filename.replace('.png', '').replace('.jpg', '')
    # Remove color prefixes
    for prefix in ['Brown ', 'Blue ', 'Green ', 'Yellow ', 'Red ', 'Purple ', 'White ', 'Black ']:
        name = name.replace(prefix, '')
    return name.strip().lower()


def load_all_icons(theme, mode='color'):
    """Load all icons from the Brown Bear theme folder."""
    icons_dir = '/home/runner/work/small-wins-automation/small-wins-automation/assets/themes/brown_bear/icons'
    
    loaded_images = []
    image_names = []
    
    # Get all PNG files
    for filename in sorted(os.listdir(icons_dir)):
        if filename.endswith('.png') and filename != '.gitkeep':
            filepath = os.path.join(icons_dir, filename)
            try:
                img = Image.open(filepath).convert('RGB')  # Convert to RGB first
                
                # Convert to grayscale for BW mode
                if mode == 'bw':
                    img = img.convert('L').convert('RGB')  # Simple grayscale conversion
                
                loaded_images.append(img)
                image_names.append(clean_icon_name(filename))
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    return loaded_images, image_names


def select_distractors(all_indices, target_index, num_distractors):
    """Select random distractors excluding the target."""
    available = [i for i in all_indices if i != target_index]
    if len(available) < num_distractors:
        # Not enough distractors, duplicate some
        distractors = random.sample(available, min(len(available), num_distractors))
        while len(distractors) < num_distractors:
            distractors.append(random.choice(available))
    else:
        distractors = random.sample(available, num_distractors)
    return distractors


def create_matching_page(loaded_images, image_names, target_index, level, pack_code, theme_name, page_num, total_pages, mode='color'):
    """
    Create a single matching activity page.
    
    Args:
        loaded_images: List of all loaded PIL images
        image_names: List of cleaned names for each image
        target_index: Index of the target image
        level: Difficulty level (1-4)
        pack_code: Product code (e.g., "BB03")
        theme_name: Theme name for footer
        page_num: Current page number
        total_pages: Total number of pages
        mode: 'color' or 'bw'
    
    Returns:
        PIL.Image: Rendered page
    """
    # Page size
    page_width, page_height = int(8.5 * inch), int(11 * inch)
    
    # Create page
    if mode == 'color':
        page = Image.new('RGB', (page_width, page_height), BRAND_COLORS['background'])
    else:
        page = Image.new('RGB', (page_width, page_height), '#FFFFFF')
    
    draw = ImageDraw.Draw(page)
    
    # Determine number of targets and distractors based on level
    if level == 1:
        num_targets = 5
        num_distractors = 0
    elif level == 2:
        num_targets = 4
        num_distractors = 1
    elif level == 3:
        num_targets = 3
        num_distractors = 2
    elif level == 4:
        num_targets = 1
        num_distractors = 4
    else:
        raise ValueError(f"Invalid level: {level}")
    
    # Select distractors
    all_indices = list(range(len(loaded_images)))
    distractor_indices = select_distractors(all_indices, target_index, num_distractors)
    
    # Create list of all cards to place (targets + distractors)
    card_indices = [target_index] * num_targets + distractor_indices
    random.shuffle(card_indices)
    
    # Layout: place target image at top, then grid of options below
    margin = SPACING['page_margin']
    
    # Draw target area at top
    target_y = margin
    target_box_height = 2.5 * inch
    target_box_rect = (margin, target_y, page_width - margin, target_y + target_box_height)
    
    # Draw target box background
    if mode == 'color':
        draw.rectangle(target_box_rect, outline=BRAND_COLORS['primary'], width=3)
    else:
        draw.rectangle(target_box_rect, outline='#000000', width=3)
    
    # Draw target image
    target_img = loaded_images[target_index]
    target_img_resized = target_img.copy()
    target_img_resized.thumbnail((int(2 * inch), int(2 * inch)), Image.Resampling.LANCZOS)
    
    # Center target image
    target_x = int((page_width - target_img_resized.width) / 2)
    target_img_y = int(target_y + (target_box_height - target_img_resized.height) / 2)
    
    if target_img_resized.mode == 'RGBA':
        page.paste(target_img_resized, (target_x, target_img_y), target_img_resized)
    else:
        page.paste(target_img_resized, (target_x, target_img_y))
    
    # Draw grid of options below
    options_start_y = target_y + target_box_height + 0.5 * inch
    
    # Calculate grid
    total_cards = len(card_indices)
    if total_cards <= 3:
        grid_cols = total_cards
        grid_rows = 1
    else:
        grid_cols = 3
        grid_rows = (total_cards + grid_cols - 1) // grid_cols
    
    card_width, card_height = CARD_SIZE
    spacing = SPACING['card_spacing']
    
    # Calculate grid positioning
    grid_width = grid_cols * card_width + (grid_cols - 1) * spacing
    grid_start_x = (page_width - grid_width) / 2
    
    # Draw cards
    for idx, card_index in enumerate(card_indices):
        row = idx // grid_cols
        col = idx % grid_cols
        
        x = int(grid_start_x + col * (card_width + spacing))
        y = int(options_start_y + row * (card_height + spacing))
        
        # Draw card background
        card_rect = (x, y, x + card_width, y + card_height)
        
        if mode == 'color':
            draw.rectangle(card_rect, fill=BRAND_COLORS['background'], outline=BRAND_COLORS['border'], width=2)
        else:
            draw.rectangle(card_rect, fill='#FFFFFF', outline='#000000', width=2)
        
        # Draw icon inside card
        icon = loaded_images[card_index]
        icon_resized = icon.copy()
        icon_resized.thumbnail(ICON_SIZE, Image.Resampling.LANCZOS)
        
        # Center icon in card
        icon_x = int(x + (card_width - icon_resized.width) / 2)
        icon_y = int(y + (card_height - icon_resized.height) / 2)
        
        if icon_resized.mode == 'RGBA':
            page.paste(icon_resized, (icon_x, icon_y), icon_resized)
        else:
            page.paste(icon_resized, (icon_x, icon_y))
    
    # Draw footer
    footer_y = page_height - SPACING['footer_height']
    footer_text = f"{pack_code} | {theme_name} | Level {level} | Page {page_num}/{total_pages}"
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Get text bbox
    bbox = draw.textbbox((0, 0), footer_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (page_width - text_width) / 2
    
    if mode == 'color':
        draw.text((text_x, footer_y), footer_text, fill=BRAND_COLORS['text'], font=font)
    else:
        draw.text((text_x, footer_y), footer_text, fill='#000000', font=font)
    
    return page


def create_cutout_page(loaded_images, image_names, start_idx, pack_code, theme_name, page_num, total_pages, mode='color'):
    """Create a page with 6 cutout icons."""
    page_width, page_height = int(8.5 * inch), int(11 * inch)
    
    if mode == 'color':
        page = Image.new('RGB', (page_width, page_height), BRAND_COLORS['background'])
    else:
        page = Image.new('RGB', (page_width, page_height), '#FFFFFF')
    
    draw = ImageDraw.Draw(page)
    
    # 2x3 grid for cutouts
    grid_cols, grid_rows = 3, 2
    margin = SPACING['page_margin']
    card_width, card_height = CARD_SIZE
    spacing = SPACING['card_spacing']
    
    grid_width = grid_cols * card_width + (grid_cols - 1) * spacing
    grid_height = grid_rows * card_height + (grid_rows - 1) * spacing
    
    grid_start_x = (page_width - grid_width) / 2
    grid_start_y = margin + inch
    
    for i in range(6):
        if start_idx + i >= len(loaded_images):
            break
        
        row = i // grid_cols
        col = i % grid_cols
        
        x = int(grid_start_x + col * (card_width + spacing))
        y = int(grid_start_y + row * (card_height + spacing))
        
        # Draw dashed cut line
        card_rect = (x, y, x + card_width, y + card_height)
        if mode == 'color':
            draw.rectangle(card_rect, outline=BRAND_COLORS['border'], width=1)
        else:
            draw.rectangle(card_rect, outline='#CCCCCC', width=1)
        
        # Draw icon
        icon = loaded_images[start_idx + i]
        icon_resized = icon.copy()
        icon_resized.thumbnail(ICON_SIZE, Image.Resampling.LANCZOS)
        
        icon_x = int(x + (card_width - icon_resized.width) / 2)
        icon_y = int(y + (card_height - icon_resized.height) / 2)
        
        if icon_resized.mode == 'RGBA':
            page.paste(icon_resized, (icon_x, icon_y), icon_resized)
        else:
            page.paste(icon_resized, (icon_x, icon_y))
    
    # Footer
    footer_y = page_height - SPACING['footer_height']
    footer_text = f"{pack_code} | {theme_name} | Cutouts | Page {page_num}/{total_pages}"
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), footer_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (page_width - text_width) / 2
    
    if mode == 'color':
        draw.text((text_x, footer_y), footer_text, fill=BRAND_COLORS['text'], font=font)
    else:
        draw.text((text_x, footer_y), footer_text, fill='#000000', font=font)
    
    return page


def create_storage_label_page(image_names, pack_code, theme_name, mode='color'):
    """Create storage label page."""
    page_width, page_height = int(8.5 * inch), int(11 * inch)
    
    if mode == 'color':
        page = Image.new('RGB', (page_width, page_height), BRAND_COLORS['background'])
    else:
        page = Image.new('RGB', (page_width, page_height), '#FFFFFF')
    
    draw = ImageDraw.Draw(page)
    
    # Title
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except:
        title_font = label_font = ImageFont.load_default()
    
    title_text = f"{theme_name} Matching Cards"
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_x = (page_width - title_width) / 2
    
    if mode == 'color':
        draw.text((title_x, inch), title_text, fill=BRAND_COLORS['primary'], font=title_font)
    else:
        draw.text((title_x, inch), title_text, fill='#000000', font=title_font)
    
    # List items
    y_pos = 2 * inch
    for name in sorted(set(image_names)):
        display_name = name.title()
        if mode == 'color':
            draw.text((inch, y_pos), f"• {display_name}", fill=BRAND_COLORS['text'], font=label_font)
        else:
            draw.text((inch, y_pos), f"• {display_name}", fill='#000000', font=label_font)
        y_pos += 0.5 * inch
    
    # Footer
    footer_y = page_height - SPACING['footer_height']
    footer_text = f"{pack_code} | {theme_name} | Storage Label"
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), footer_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (page_width - text_width) / 2
    
    if mode == 'color':
        draw.text((text_x, footer_y), footer_text, fill=BRAND_COLORS['text'], font=font)
    else:
        draw.text((text_x, footer_y), footer_text, fill='#000000', font=font)
    
    return page


def generate_full_matching_product(output_dir, mode='color'):
    """
    Generate complete matching product for Brown Bear theme.
    
    Creates:
    - All 4 levels × all icons matching pages
    - Cutout pages
    - Storage label page
    """
    # Load theme
    theme = load_theme('brown_bear', mode=mode)
    
    # Load all icons
    loaded_images, image_names = load_all_icons(theme, mode=mode)
    
    print(f"Loaded {len(loaded_images)} icons: {image_names}")
    
    # Product settings
    pack_code = "BB03"
    theme_name = "Brown Bear"
    
    # Calculate total pages
    num_icons = len(loaded_images)
    matching_pages = num_icons * 4  # 4 levels per icon
    cutout_pages = (num_icons + 5) // 6  # 6 icons per cutout page
    storage_label_pages = 1
    total_pages = matching_pages + cutout_pages + storage_label_pages
    
    print(f"Generating {total_pages} pages total:")
    print(f"  - {matching_pages} matching pages (4 levels × {num_icons} icons)")
    print(f"  - {cutout_pages} cutout pages")
    print(f"  - {storage_label_pages} storage label page")
    
    all_pages = []
    page_num = 1
    
    # Generate matching pages for each icon at each level
    for icon_idx in range(num_icons):
        for level in [1, 2, 3, 4]:
            print(f"Generating page {page_num}/{total_pages}: {image_names[icon_idx]} - Level {level}")
            page = create_matching_page(
                loaded_images, image_names, icon_idx, level,
                pack_code, theme_name, page_num, total_pages, mode
            )
            all_pages.append(page)
            page_num += 1
    
    # Generate cutout pages
    for cutout_page_idx in range(cutout_pages):
        start_idx = cutout_page_idx * 6
        print(f"Generating cutout page {page_num}/{total_pages}")
        page = create_cutout_page(
            loaded_images, image_names, start_idx,
            pack_code, theme_name, page_num, total_pages, mode
        )
        all_pages.append(page)
        page_num += 1
    
    # Generate storage label page
    print(f"Generating storage label page {page_num}/{total_pages}")
    page = create_storage_label_page(image_names, pack_code, theme_name, mode)
    all_pages.append(page)
    
    # Save as PDF
    mode_suffix = '_bw' if mode == 'bw' else '_color'
    output_file = os.path.join(output_dir, f'brown_bear_matching_full{mode_suffix}.pdf')
    
    print(f"Saving {len(all_pages)} pages to {output_file}")
    
    # Convert to RGB if needed
    rgb_pages = []
    for page in all_pages:
        if page.mode != 'RGB':
            rgb_pages.append(page.convert('RGB'))
        else:
            rgb_pages.append(page)
    
    # Save PDF
    if rgb_pages:
        rgb_pages[0].save(
            output_file,
            save_all=True,
            append_images=rgb_pages[1:] if len(rgb_pages) > 1 else [],
            resolution=300.0
        )
    
    print(f"✅ Generated {output_file}")
    print(f"   Total pages: {len(all_pages)}")
    print(f"   File size: {os.path.getsize(output_file) / 1024:.1f} KB")
    
    return output_file


def main():
    """Generate both color and BW versions of the full matching product."""
    output_dir = '/home/runner/work/small-wins-automation/small-wins-automation/samples/brown_bear/matching'
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("BROWN BEAR MATCHING CARDS - FULL PRODUCT GENERATION")
    print("=" * 60)
    print()
    
    # Generate color version
    print("\n📘 GENERATING COLOR VERSION...")
    print("-" * 60)
    color_pdf = generate_full_matching_product(output_dir, mode='color')
    
    # Generate BW version
    print("\n📝 GENERATING BLACK & WHITE VERSION...")
    print("-" * 60)
    bw_pdf = generate_full_matching_product(output_dir, mode='bw')
    
    print("\n" + "=" * 60)
    print("✅ GENERATION COMPLETE!")
    print("=" * 60)
    print(f"\nColor PDF: {color_pdf}")
    print(f"BW PDF: {bw_pdf}")
    print()


if __name__ == '__main__':
    main()
