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
"""

import os
from PIL import Image, ImageDraw, ImageFont
from utils.config import DPI, PAGE_WIDTH, PAGE_HEIGHT, MARGINS, COLORS, FONT_SIZES, FOOTER_TEXT
from utils.image_loader import load_image
from utils.pdf_export import save_images_as_pdf
from utils.draw_helpers import (
    scale_image_to_fit,
    draw_page_number,
    draw_copyright_footer,
    create_placeholder_image
)
from utils.storage_label_helper import create_companion_label

# Task box card sizing standard (4 cards per page, 2×2 grid)
# 5.25" × 4" at 300 DPI = 1575px × 1200px
TASK_BOX_CARD_WIDTH = int(5.25 * DPI)  # 1575px
TASK_BOX_CARD_HEIGHT = int(4 * DPI)  # 1200px


def generate_yes_no_card(draw, card_rect, item, card_type='standard', folder_type='images'):
    """
    Generate a single Yes/No card within the given rectangle.
    
    Args:
        draw: PIL ImageDraw object
        card_rect: Tuple (x1, y1, x2, y2) defining card boundaries
        item: Dict with 'image' and 'label' keys
        card_type: 'standard', 'errorless_yes', 'errorless_no', or 'cut_paste'
        folder_type: Image folder type ('images', 'real_images', etc.)
    """
    x1, y1, x2, y2 = card_rect
    card_width = x2 - x1
    card_height = y2 - y1
    
    # Draw card border
    draw.rectangle([x1, y1, x2, y2], outline=COLORS['black'], width=3)
    
    # Layout areas
    icon_area_height = int(card_height * 0.45)  # 45% for icon
    question_area_height = int(card_height * 0.25)  # 25% for question
    response_area_height = int(card_height * 0.30)  # 30% for YES/NO
    
    # 1. Icon area (top 45%)
    icon_rect = (
        x1 + 20,
        y1 + 20,
        x2 - 20,
        y1 + icon_area_height - 10
    )
    
    try:
        img = load_image(item['image'], folder_type=folder_type)
        if img:
            scaled_coords = scale_image_to_fit(img, icon_rect, padding=10)
            if scaled_coords:
                paste_x, paste_y, paste_width, paste_height = scaled_coords
                resized_img = img.resize((paste_width, paste_height), Image.Resampling.LANCZOS)
                # Convert RGBA to RGB if needed
                if resized_img.mode == 'RGBA':
                    bg = Image.new('RGB', resized_img.size, COLORS['white'])
                    bg.paste(resized_img, mask=resized_img.split()[3])
                    resized_img = bg
                # Paste onto the page
                temp_page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
                temp_page.paste(resized_img, (paste_x, paste_y))
                # Copy the pasted area to actual draw context
                draw._image.paste(temp_page.crop((paste_x, paste_y, paste_x + paste_width, paste_y + paste_height)), (paste_x, paste_y))
    except:
        # Use placeholder
        placeholder = create_placeholder_image(icon_rect[2] - icon_rect[0], icon_rect[3] - icon_rect[1], "No Image")
        draw._image.paste(placeholder, (icon_rect[0], icon_rect[1]))
    
    # 2. Question area (middle 25%)
    question_y_start = y1 + icon_area_height
    question_text = f"Is this a {item['label']}?"
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except:
        font = ImageFont.load_default()
    
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
        # Draw two empty boxes for gluing YES/NO
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
        # Draw YES and NO circles/buttons
        circle_radius = int(response_area_height * 0.35)
        circle_y = response_y_start + response_area_height // 2
        
        # YES circle (left)
        yes_circle_x = x1 + int(card_width * 0.25)
        yes_fill = COLORS['light_gray'] if card_type == 'errorless_yes' else COLORS['white']
        no_fill = COLORS['light_gray'] if card_type == 'errorless_no' else COLORS['white']
        
        # YES
        draw.ellipse([yes_circle_x - circle_radius, circle_y - circle_radius,
                     yes_circle_x + circle_radius, circle_y + circle_radius],
                    fill=yes_fill, outline=COLORS['black'], width=3)
        
        try:
            btn_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except:
            btn_font = ImageFont.load_default()
        
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
                                page_num=1, total_pages=1):
    """
    Generate a page with 4 Yes/No cards in 2×2 grid.
    
    Args:
        items: List of item dicts
        start_idx: Starting index in items list
        card_type: Type of cards to generate
        folder_type: Image folder type
        page_num: Current page number
        total_pages: Total number of pages
    
    Returns:
        PIL Image object
    """
    # Create page
    page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
    draw = ImageDraw.Draw(page)
    
    # Calculate card positions for 2×2 grid
    # Cards share borders (guillotine cutting)
    margin = MARGINS['page']
    available_width = PAGE_WIDTH - 2 * margin
    available_height = PAGE_HEIGHT - 2 * margin - MARGINS['page']  # Extra space for footer
    
    # Two cards horizontally, two vertically
    card_width = available_width // 2
    card_height = available_height // 2
    
    # Generate 4 cards
    for row in range(2):
        for col in range(2):
            idx = start_idx + row * 2 + col
            if idx >= len(items):
                break
            
            x1 = margin + col * card_width
            y1 = margin + row * card_height
            x2 = x1 + card_width
            y2 = y1 + card_height
            
            card_rect = (x1, y1, x2, y2)
            generate_yes_no_card(draw, card_rect, items[idx], card_type, folder_type)
    
    # Add footer and page number
    draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
    draw_page_number(draw, page_num, total_pages, PAGE_WIDTH, PAGE_HEIGHT)
    
    return page


def generate_cutout_yes_no_icons(output_dir, theme_name):
    """
    Generate a page of YES and NO icons for cut-and-paste activities.
    
    Returns:
        Path to generated PDF
    """
    page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
    draw = ImageDraw.Draw(page)
    
    # Create multiple YES and NO icons (6 of each)
    icon_size = 400  # Reasonable size for cutting
    spacing = 40
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    # Calculate grid
    icons_per_row = 3
    total_icons = 12  # 6 YES + 6 NO
    
    start_x = (PAGE_WIDTH - (icons_per_row * icon_size + (icons_per_row - 1) * spacing)) // 2
    start_y = 150
    
    for i in range(total_icons):
        row = i // icons_per_row
        col = i % icons_per_row
        
        x = start_x + col * (icon_size + spacing)
        y = start_y + row * (icon_size + spacing)
        
        # Determine YES or NO
        text = "YES" if i < 6 else "NO"
        
        # Draw circle with text
        center_x = x + icon_size // 2
        center_y = y + icon_size // 2
        radius = icon_size // 2 - 10
        
        draw.ellipse([center_x - radius, center_y - radius,
                     center_x + radius, center_y + radius],
                    fill=COLORS['white'], outline=COLORS['black'], width=4)
        
        # Draw text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((center_x - text_w // 2, center_y - text_h // 2),
                 text, fill=COLORS['black'], font=font)
        
        # Draw cut lines
        draw.rectangle([x, y, x + icon_size, y + icon_size],
                      outline=COLORS['dark_gray'], width=1)
    
    # Add footer and page number
    draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
    draw_page_number(draw, 1, 1, PAGE_WIDTH, PAGE_HEIGHT)
    
    # Save
    output_path = os.path.join(output_dir, f"{theme_name}_Yes_No_Cutouts.pdf")
    save_images_as_pdf([page], output_path)
    
    return output_path


def generate_yes_no_cards_set(items, theme_name, output_dir='output',
                               include_standard=True, include_real_images=False,
                               include_errorless=True, include_cut_paste=True,
                               include_storage_label=True, folder_type='images'):
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
                                             page_num + 1, num_pages)
            pages.append(page)
        
        output_path = os.path.join(output_dir, f"{theme_name}_Yes_No_Cards.pdf")
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
                                             page_num + 1, num_pages)
            pages.append(page)
        
        output_path = os.path.join(output_dir, f"{theme_name}_Yes_No_Cards_Real_Images.pdf")
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
                                             page_num + 1, num_pages)
            pages.append(page)
        
        output_path = os.path.join(output_dir, f"{theme_name}_Yes_No_Cards_Errorless_Yes.pdf")
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
                                             page_num + 1, num_pages)
            pages.append(page)
        
        output_path = os.path.join(output_dir, f"{theme_name}_Yes_No_Cards_Errorless_No.pdf")
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
                                             page_num + 1, num_pages)
            pages.append(page)
        
        output_path = os.path.join(output_dir, f"{theme_name}_Yes_No_Cards_Cut_Paste.pdf")
        save_images_as_pdf(pages, output_path)
        output_files['cut_paste'] = output_path
        
        if include_storage_label:
            label_path = create_companion_label(output_path, theme_name, "Yes/No Cards (Cut & Paste)")
            output_files['cut_paste_label'] = label_path
        
        # Generate YES/NO cutouts
        cutouts_path = generate_cutout_yes_no_icons(output_dir, theme_name)
        output_files['cutouts'] = cutouts_path
        
        if include_storage_label:
            label_path = create_companion_label(cutouts_path, theme_name, "Yes/No Cutouts")
            output_files['cutouts_label'] = label_path
    
    return output_files
