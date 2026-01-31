"""
Yes/No Cards Generator for SPED Resources

Generates Yes/No question cards for receptive language and categorization tasks.
Cards are task-box friendly with 4 cards per page in a 2×2 grid with shared borders
for easy guillotine cutting.

Features:
- Task-box compatible sizing (5.25" × 4" per card)
- 4 cards per page (2×2 grid)
- Shared borders for guillotine cutting
- Standard, Real Image, Errorless, and Cut-and-Paste versions
- Large icons and clear YES/NO response areas
- SPED-compliant high contrast design
- Dual-mode output (color + black-and-white)
"""

import os
from PIL import Image, ImageDraw, ImageFont
from utils.config import DPI, PAGE_WIDTH, PAGE_HEIGHT, MARGINS, COLORS, FONT_SIZES, FOOTER_TEXT
from utils.image_loader import load_image
from utils.pdf_export import save_images_as_pdf
from utils.layout import create_page_canvas, add_footer
from utils.grid_layout import create_grid_positions
from utils.image_utils import scale_image_proportional, center_image_in_box
from utils.color_helpers import hex_to_grayscale, image_to_grayscale
from utils.fonts import get_font_manager
from utils.storage_label_helper import create_companion_label

# Task box card sizing standard (4 cards per page, 2×2 grid)
# 5.25" × 4" at 300 DPI = 1575px × 1200px
TASK_BOX_CARD_WIDTH = int(5.25 * DPI)  # 1575px
TASK_BOX_CARD_HEIGHT = int(4 * DPI)  # 1200px


def generate_yes_no_card(page, card_rect, item, card_type='standard', folder_type='images', mode='color'):
    """
    Generate a single Yes/No card within the given rectangle using modern utilities.
    
    Args:
        page: PIL Image object (page canvas)
        card_rect: Tuple (x1, y1, x2, y2) defining card boundaries
        item: Dict with 'image' and 'label' keys
        card_type: 'standard', 'errorless_yes', 'errorless_no', or 'cut_paste'
        folder_type: Image folder type ('images', 'real_images', etc.)
        mode: 'color' or 'bw' for dual-mode output
    """
    draw = ImageDraw.Draw(page)
    x1, y1, x2, y2 = card_rect
    card_width = x2 - x1
    card_height = y2 - y1
    
    # Draw card border - high contrast SPED standard
    border_color = COLORS['black']
    draw.rectangle([x1, y1, x2, y2], outline=border_color, width=3)
    
    # Layout areas - SPED-optimized proportions
    icon_area_height = int(card_height * 0.45)  # 45% for icon
    question_area_height = int(card_height * 0.25)  # 25% for question
    response_area_height = int(card_height * 0.30)  # 30% for YES/NO
    
    padding = 20
    
    # 1. Icon area (top 45%) - using modern image utilities
    icon_box_width = card_width - (padding * 2)
    icon_box_height = icon_area_height - (padding * 2)
    
    try:
        img = load_image(item['image'], folder_type=folder_type)
        if img:
            # Convert to grayscale if BW mode using color_helpers
            if mode == 'bw':
                img = image_to_grayscale(img)
            
            # Scale proportionally using image_utils
            scaled_img = scale_image_proportional(img, max_width=icon_box_width, max_height=icon_box_height)
            
            # Center in box
            centered_img = center_image_in_box(scaled_img, icon_box_width, icon_box_height, COLORS['white'] + (255,))
            
            # Convert RGBA to RGB for pasting
            if centered_img.mode == 'RGBA':
                bg = Image.new('RGB', centered_img.size, COLORS['white'])
                bg.paste(centered_img, mask=centered_img.split()[3] if len(centered_img.split()) == 4 else None)
                centered_img = bg
            
            # Paste onto page
            page.paste(centered_img, (x1 + padding, y1 + padding))
    except Exception as e:
        # Fallback: draw placeholder text
        draw.text((x1 + card_width // 2, y1 + icon_area_height // 2), 
                 "No Image", fill=COLORS['black'], anchor="mm")
    
    # 2. Question area (middle 25%) - using font manager
    question_y_start = y1 + icon_area_height
    question_text = f"Is this a {item['label']}?"
    
    font_mgr = get_font_manager()
    try:
        font = font_mgr.get_font('body', 32, bold=True)
    except:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    
    # Center question text
    bbox = draw.textbbox((0, 0), question_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = x1 + (card_width - text_width) // 2
    text_y = question_y_start + (question_area_height - text_height) // 2
    draw.text((text_x, text_y), question_text, fill=COLORS['black'], font=font)
    
    # 3. Response area (bottom 30%)
    response_y_start = y1 + icon_area_height + question_area_height
    
    if card_type == 'cut_paste':
        # Draw two empty boxes for gluing YES/NO - SPED standard dashed boxes
        box_width = int(card_width * 0.35)
        box_height = int(response_area_height * 0.7)
        box_y = response_y_start + (response_area_height - box_height) // 2
        
        # YES box (left)
        yes_box_x = x1 + int(card_width * 0.15)
        draw.rectangle([yes_box_x, box_y, yes_box_x + box_width, box_y + box_height],
                      outline=COLORS['black'], width=2)
        
        # NO box (right)
        no_box_x = x2 - int(card_width * 0.15) - box_width
        draw.rectangle([no_box_x, box_y, no_box_x + box_width, box_y + box_height],
                      outline=COLORS['black'], width=2)
    else:
        # Draw YES and NO circles/buttons with SPED-compliant spacing
        circle_radius = int(response_area_height * 0.35)
        circle_y = response_y_start + response_area_height // 2
        
        # Errorless highlighting - use light gray fills in both modes
        yes_fill = COLORS['light_gray'] if card_type == 'errorless_yes' else COLORS['white']
        no_fill = COLORS['light_gray'] if card_type == 'errorless_no' else COLORS['white']
        
        # YES circle (left)
        yes_circle_x = x1 + int(card_width * 0.25)
        draw.ellipse([yes_circle_x - circle_radius, circle_y - circle_radius,
                     yes_circle_x + circle_radius, circle_y + circle_radius],
                    fill=yes_fill, outline=COLORS['black'], width=3)
        
        try:
            btn_font = font_mgr.get_font('body', 36, bold=True)
        except:
            btn_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        
        yes_bbox = draw.textbbox((0, 0), "YES", font=btn_font)
        yes_text_w = yes_bbox[2] - yes_bbox[0]
        yes_text_h = yes_bbox[3] - yes_bbox[1]
        draw.text((yes_circle_x - yes_text_w // 2, circle_y - yes_text_h // 2), 
                 "YES", fill=COLORS['black'], font=btn_font)
        
        # NO circle (right)
        no_circle_x = x2 - int(card_width * 0.25)
        draw.ellipse([no_circle_x - circle_radius, circle_y - circle_radius,
                     no_circle_x + circle_radius, circle_y + circle_radius],
                    fill=no_fill, outline=COLORS['black'], width=3)
        
        no_bbox = draw.textbbox((0, 0), "NO", font=btn_font)
        no_text_w = no_bbox[2] - no_bbox[0]
        no_text_h = no_bbox[3] - no_bbox[1]
        draw.text((no_circle_x - no_text_w // 2, circle_y - no_text_h // 2), 
                 "NO", fill=COLORS['black'], font=btn_font)


def generate_yes_no_cards_page(items, start_idx, card_type='standard', folder_type='images',
                                page_num=1, total_pages=1, mode='color'):
    """
    Generate a page with 4 Yes/No cards in 2×2 grid using modern layout utilities.
    
    Args:
        items: List of item dicts
        start_idx: Starting index in items list
        card_type: Type of cards to generate
        folder_type: Image folder type
        page_num: Current page number
        total_pages: Total number of pages
        mode: 'color' or 'bw' for dual-mode output
    
    Returns:
        PIL Image object
    """
    # Create page using layout utilities
    page = create_page_canvas(PAGE_WIDTH, PAGE_HEIGHT, COLORS['background'])
    
    # Convert RGBA to RGB for PDF compatibility
    if page.mode == 'RGBA':
        rgb_page = Image.new('RGB', page.size, COLORS['white'])
        rgb_page.paste(page, mask=page.split()[3] if len(page.split()) == 4 else None)
        page = rgb_page
    
    # Calculate card positions for 2×2 grid using grid_layout utilities
    margin = MARGINS['page']
    available_width = PAGE_WIDTH - 2 * margin
    available_height = PAGE_HEIGHT - 2 * margin - 100  # Space for footer
    
    # Two cards horizontally, two vertically (shared borders for guillotine cutting)
    card_width = available_width // 2
    card_height = available_height // 2
    
    # Calculate grid positions
    positions = create_grid_positions(
        cols=2, 
        rows=2, 
        cell_width=card_width, 
        cell_height=card_height, 
        spacing=0,  # Shared borders - no spacing
        container_width=PAGE_WIDTH, 
        container_height=PAGE_HEIGHT - 100  # Leave room for footer
    )
    
    # Generate 4 cards at calculated positions
    for idx, (x, y) in enumerate(positions[:4]):  # Max 4 cards per page
        item_idx = start_idx + idx
        if item_idx >= len(items):
            break
        
        card_rect = (x, y, x + card_width, y + card_height)
        generate_yes_no_card(page, card_rect, items[item_idx], card_type, folder_type, mode)
    
    # Add footer using layout utilities
    page = add_footer(page, FOOTER_TEXT)
    
    # Add page number if multiple pages
    if total_pages > 1:
        draw = ImageDraw.Draw(page)
        font_mgr = get_font_manager()
        try:
            page_font = font_mgr.get_font('body', 14)
        except:
            page_font = ImageFont.load_default()
        
        page_text = f"Page {page_num} of {total_pages}"
        bbox = draw.textbbox((0, 0), page_text, font=page_font)
        text_width = bbox[2] - bbox[0]
        draw.text((PAGE_WIDTH - text_width - 50, PAGE_HEIGHT - 50), 
                 page_text, fill=COLORS['black'], font=page_font)
    
    return page


def generate_cutout_yes_no_icons(output_dir, theme_name, mode='color'):
    """
    Generate a page of YES and NO icons for cut-and-paste activities using modern utilities.
    
    Args:
        output_dir: Output directory path
        theme_name: Theme name for file naming
        mode: 'color' or 'bw' for dual-mode output
    
    Returns:
        Path to generated PDF
    """
    # Create page using layout utilities
    page = create_page_canvas(PAGE_WIDTH, PAGE_HEIGHT, COLORS['background'])
    
    # Convert to RGB
    if page.mode == 'RGBA':
        rgb_page = Image.new('RGB', page.size, COLORS['white'])
        rgb_page.paste(page, mask=page.split()[3] if len(page.split()) == 4 else None)
        page = rgb_page
    
    draw = ImageDraw.Draw(page)
    
    # Create multiple YES and NO icons (6 of each) using grid layout
    icon_size = 400  # SPED-compliant size for cutting
    
    # Use grid_layout to position icons
    positions = create_grid_positions(
        cols=3,
        rows=4,
        cell_width=icon_size,
        cell_height=icon_size,
        spacing=40,
        container_width=PAGE_WIDTH,
        container_height=PAGE_HEIGHT - 150  # Leave room for footer
    )
    
    font_mgr = get_font_manager()
    try:
        font = font_mgr.get_font('body', 48, bold=True)
    except:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    
    # Draw 12 icons (6 YES, 6 NO)
    for i in range(12):
        if i >= len(positions):
            break
            
        x, y = positions[i]
        
        # Determine YES or NO
        text = "YES" if i < 6 else "NO"
        
        # Draw circle with text - SPED standard high contrast
        center_x = x + icon_size // 2
        center_y = y + icon_size // 2
        radius = icon_size // 2 - 10
        
        draw.ellipse([center_x - radius, center_y - radius,
                     center_x + radius, center_y + radius],
                    fill=COLORS['white'], outline=COLORS['black'], width=4)
        
        # Draw text centered
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((center_x - text_w // 2, center_y - text_h // 2),
                 text, fill=COLORS['black'], font=font)
        
        # Draw dashed cut lines for guillotine cutting
        line_color = COLORS['dark_gray']
        draw.rectangle([x, y, x + icon_size, y + icon_size],
                      outline=line_color, width=1)
    
    # Add footer using layout utilities
    page = add_footer(page, FOOTER_TEXT)
    
    # Save with mode suffix
    mode_suffix = f"_{mode}"
    output_path = os.path.join(output_dir, f"{theme_name}_Yes_No_Cutouts{mode_suffix}.pdf")
    save_images_as_pdf([page], output_path)
    
    return output_path


def generate_yes_no_cards_set(items, theme_name, output_dir='output',
                               include_standard=True, include_real_images=False,
                               include_errorless=True, include_cut_paste=True,
                               include_storage_label=True, folder_type='images', mode='color'):
    """
    Generate complete set of Yes/No cards.
    
    Args:
        items: List of dicts with 'image' and 'label' keys
        theme_name: Name of theme for file naming
        output_dir: Output directory path
        include_standard: Generate standard Yes/No cards
        include_real_images: Generate real image version
        include_errorless: Generate errorless versions
        include_cut_paste: Generate cut-and-paste version
        include_storage_label: Generate storage labels
        folder_type: Default folder type for images
        mode: 'color' or 'bw' for dual-mode output
    
    Returns:
        Dict with paths to generated files
    """
    os.makedirs(output_dir, exist_ok=True)
    output_files = {}
    
    # Calculate pages needed (4 cards per page)
    cards_per_page = 4
    num_pages = (len(items) + cards_per_page - 1) // cards_per_page
    
    # Standard Yes/No cards
    if include_standard:
        pages = []
        for page_num in range(num_pages):
            start_idx = page_num * cards_per_page
            page = generate_yes_no_cards_page(items, start_idx, 'standard', folder_type,
                                             page_num + 1, num_pages, mode)
            pages.append(page)
        
        mode_suffix = f"_{mode}" if mode else ""
        output_path = os.path.join(output_dir, f"{theme_name}_Yes_No_Cards{mode_suffix}.pdf")
        save_images_as_pdf(pages, output_path)
        output_files['standard'] = output_path
        
        if include_storage_label:
            label_path = create_companion_label(output_path, theme_name, "Yes/No Cards")
            output_files['standard_label'] = label_path
    
    # Real Image version
    if include_real_images:
        pages = []
        for page_num in range(num_pages):
            start_idx = page_num * cards_per_page
            page = generate_yes_no_cards_page(items, start_idx, 'standard', 'real_images',
                                             page_num + 1, num_pages, mode)
            pages.append(page)
        
        mode_suffix = f"_{mode}" if mode else ""
        output_path = os.path.join(output_dir, f"{theme_name}_Yes_No_Cards_Real_Images{mode_suffix}.pdf")
        save_images_as_pdf(pages, output_path)
        output_files['real_images'] = output_path
        
        if include_storage_label:
            label_path = create_companion_label(output_path, theme_name, "Yes/No Cards (Real Images)")
            output_files['real_images_label'] = label_path
    
    # Errorless versions
    if include_errorless:
        # Errorless YES version
        pages = []
        for page_num in range(num_pages):
            start_idx = page_num * cards_per_page
            page = generate_yes_no_cards_page(items, start_idx, 'errorless_yes', folder_type,
                                             page_num + 1, num_pages, mode)
            pages.append(page)
        
        mode_suffix = f"_{mode}" if mode else ""
        output_path = os.path.join(output_dir, f"{theme_name}_Yes_No_Cards_Errorless_Yes{mode_suffix}.pdf")
        save_images_as_pdf(pages, output_path)
        output_files['errorless_yes'] = output_path
        
        if include_storage_label:
            label_path = create_companion_label(output_path, theme_name, "Yes/No Cards (Errorless YES)")
            output_files['errorless_yes_label'] = label_path
        
        # Errorless NO version
        pages = []
        for page_num in range(num_pages):
            start_idx = page_num * cards_per_page
            page = generate_yes_no_cards_page(items, start_idx, 'errorless_no', folder_type,
                                             page_num + 1, num_pages, mode)
            pages.append(page)
        
        mode_suffix = f"_{mode}" if mode else ""
        output_path = os.path.join(output_dir, f"{theme_name}_Yes_No_Cards_Errorless_No{mode_suffix}.pdf")
        save_images_as_pdf(pages, output_path)
        output_files['errorless_no'] = output_path
        
        if include_storage_label:
            label_path = create_companion_label(output_path, theme_name, "Yes/No Cards (Errorless NO)")
            output_files['errorless_no_label'] = label_path
    
    # Cut-and-paste version
    if include_cut_paste:
        pages = []
        for page_num in range(num_pages):
            start_idx = page_num * cards_per_page
            page = generate_yes_no_cards_page(items, start_idx, 'cut_paste', folder_type,
                                             page_num + 1, num_pages, mode)
            pages.append(page)
        
        mode_suffix = f"_{mode}" if mode else ""
        output_path = os.path.join(output_dir, f"{theme_name}_Yes_No_Cards_Cut_Paste{mode_suffix}.pdf")
        save_images_as_pdf(pages, output_path)
        output_files['cut_paste'] = output_path
        
        if include_storage_label:
            label_path = create_companion_label(output_path, theme_name, "Yes/No Cards (Cut & Paste)")
            output_files['cut_paste_label'] = label_path
        
        # Generate YES/NO cutouts with mode parameter
        cutouts_path = generate_cutout_yes_no_icons(output_dir, theme_name, mode)
        output_files['cutouts'] = cutouts_path
        
        if include_storage_label:
            label_path = create_companion_label(cutouts_path, theme_name, "Yes/No Cutouts")
            output_files['cutouts_label'] = label_path
    
    return output_files


def generate_yes_no_cards_dual_mode(items, theme_name, output_dir='output',
                                     include_standard=True, include_real_images=False,
                                     include_errorless=True, include_cut_paste=True,
                                     include_storage_label=True, folder_type='images'):
    """
    Generate complete set of Yes/No cards in BOTH color and black-and-white modes.
    
    This is a convenience wrapper that calls generate_yes_no_cards_set() twice:
    once for color mode and once for BW mode.
    
    Args:
        items: List of dicts with 'image' and 'label' keys
        theme_name: Name of theme for file naming
        output_dir: Output directory path
        include_standard: Generate standard Yes/No cards
        include_real_images: Generate real image version
        include_errorless: Generate errorless versions
        include_cut_paste: Generate cut-and-paste version
        include_storage_label: Generate storage labels
        folder_type: Default folder type for images
    
    Returns:
        Dict with 'color' and 'bw' keys, each containing paths to generated files
    """
    results = {}
    
    # Generate color version
    results['color'] = generate_yes_no_cards_set(
        items, theme_name, output_dir,
        include_standard, include_real_images,
        include_errorless, include_cut_paste,
        include_storage_label, folder_type, mode='color'
    )
    
    # Generate black-and-white version
    results['bw'] = generate_yes_no_cards_set(
        items, theme_name, output_dir,
        include_standard, include_real_images,
        include_errorless, include_cut_paste,
        include_storage_label, folder_type, mode='bw'
    )
    
    return results
