"""
Sequencing Strips Generator - Task-Box Sizing Standard

Generates sequencing cards following the task-box sizing standard for 
classroom organization. Each sequence step is a separate task-box card
(4 cards per page in 2×2 grid with shared borders).

Features:
- Task-box compatible sizing (5.25" × 4" per card)  
- 4 cards per page (2×2 grid) with shared borders for guillotine cutting
- 3-step and 4-step sequences with step indicators
- Errorless version (correct order) and Mixed version (scrambled order)
- Real image version support
- Theme-aware design with high-contrast SPED-friendly layout
- Storage label generation
- Copyright compliance and page numbering

Requirements from specification:
- TASK BOX SIZING STANDARD: 4 cards per page (2×2 grid), shared borders
- Each step is a separate task-box card with "Step X of Y" indicator
- 3-step and 4-step sequences
- Errorless version (all steps identical - implemented as correct order)
- Real image version (if available)
- Theme awareness (fonts, colors, icons from JSON)
- Page elements (footer + page numbering)

Usage:
    from generators import generate_sequencing_strips_set
    
    items = [
        {'image': 'step1.png', 'label': 'First Step'},
        {'image': 'step2.png', 'label': 'Second Step'},
        {'image': 'step3.png', 'label': 'Third Step'},
    ]
    
    output = generate_sequencing_strips_set(
        items=items,
        theme_name='MyTheme',
        num_steps=3,
        include_errorless=True,
        include_mixed=True,
        include_real_images=False,
        output_dir='output',
        include_storage_label=True
    )
"""

import os
from PIL import Image, ImageDraw, ImageFont
from utils.config import DPI, PAGE_WIDTH, PAGE_HEIGHT, COLORS, FONT_SIZES
from utils.image_loader import get_image_loader
from utils.pdf_export import save_images_as_pdf
from utils.draw_helpers import (
    scale_image_to_fit,
    draw_page_number,
    draw_copyright_footer,
    draw_text_centered_in_rect,
    create_placeholder_image
)
from utils.fonts import get_font_manager
from utils.storage_label_helper import create_companion_label
import random

# Task box card sizing standard (4 cards per page, 2×2 grid)
# 5.25" × 4" at 300 DPI = 1575px × 1200px
TASK_BOX_CARD_WIDTH = int(5.25 * DPI)  # 1575px
TASK_BOX_CARD_HEIGHT = int(4 * DPI)  # 1200px


def generate_sequence_card(draw, card_rect, step_item, step_number, total_steps, 
                           folder_type='images', with_labels=True, theme_fonts=None):
    """
    Generate a single sequencing card within the given rectangle.
    
    Args:
        draw: PIL ImageDraw object
        card_rect: Tuple (x1, y1, x2, y2) defining card boundaries
        step_item: Dict with 'image' and 'label' keys
        step_number: Current step number (1-based)
        total_steps: Total number of steps in sequence
        folder_type: Image folder type ('images', 'real_images', etc.)
        with_labels: Include text label below icon
        theme_fonts: Optional dict of theme fonts
    """
    x1, y1, x2, y2 = card_rect
    card_width = x2 - x1
    card_height = y2 - y1
    
    # Draw card border (shared borders for guillotine cutting)
    draw.rectangle([x1, y1, x2, y2], outline=COLORS['black'], width=3)
    
    # Layout areas
    step_indicator_height = 60  # "Step 1 of 3" indicator
    icon_area_height = int(card_height * 0.65) - step_indicator_height  # 65% for icon
    label_area_height = int(card_height * 0.35)  # 35% for label
    
    # 1. Step indicator at top
    step_text = f"Step {step_number} of {total_steps}"
    
    # Draw step indicator background
    step_bg_rect = (x1 + 10, y1 + 10, x2 - 10, y1 + step_indicator_height)
    draw.rectangle(step_bg_rect, fill=COLORS['light_gray'], outline=COLORS['dark_gray'], width=2)
    
    # Center step text (font_size parameter, not font object)
    draw_text_centered_in_rect(draw, step_text, step_bg_rect, font_size=28, color=COLORS['black'])
    
    # 2. Icon area
    icon_rect = (
        x1 + 40,
        y1 + step_indicator_height + 20,
        x2 - 40,
        y1 + step_indicator_height + icon_area_height
    )
    
    # Load image
    image_loader = get_image_loader()
    try:
        img = image_loader.load_image(step_item['image'], folder_type)
        if img:
            scaled_img, (img_x, img_y) = scale_image_to_fit(img, icon_rect, padding=10)
            
            # Paste image
            if scaled_img.mode == 'RGBA':
                draw._image.paste(scaled_img, (img_x, img_y), scaled_img)
            else:
                draw._image.paste(scaled_img, (img_x, img_y))
    except:
        # Use placeholder
        placeholder_width = icon_rect[2] - icon_rect[0]
        placeholder_height = icon_rect[3] - icon_rect[1]
        placeholder = create_placeholder_image(placeholder_width, placeholder_height, 
                                              step_item.get('label', 'Image'))
        draw._image.paste(placeholder, (icon_rect[0], icon_rect[1]))
    
    # 3. Label area (if enabled)
    if with_labels and 'label' in step_item:
        label_y_start = y1 + step_indicator_height + icon_area_height + 10
        label_rect = (
            x1 + 20,
            label_y_start,
            x2 - 20,
            y2 - 20
        )
        
        # Use font_size parameter
        draw_text_centered_in_rect(draw, step_item['label'], label_rect, font_size=36, color=COLORS['black'])


def generate_sequencing_cards_page(sequence_steps, page_number, total_pages, 
                                   folder_type='images', with_labels=True, theme_fonts=None):
    """
    Generate a page with 4 sequencing cards in 2×2 grid (task-box sizing standard).
    
    Args:
        sequence_steps: List of up to 4 step items (dict with 'image', 'label', 'step_num', 'total_steps')
        page_number: Current page number
        total_pages: Total number of pages
        folder_type: Image folder type
        with_labels: Include text labels
        theme_fonts: Optional theme fonts dict
        
    Returns:
        PIL.Image: Generated page with 4 cards
    """
    # Create page
    page = Image.new('RGB', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), COLORS['white'])
    draw = ImageDraw.Draw(page)
    
    # Calculate card positions (2×2 grid, shared borders)
    # Cards share borders for guillotine cutting
    col1_x = 0
    col2_x = TASK_BOX_CARD_WIDTH
    row1_y = 0
    row2_y = TASK_BOX_CARD_HEIGHT
    
    # Define all 4 card positions
    card_positions = [
        (col1_x, row1_y, col1_x + TASK_BOX_CARD_WIDTH, row1_y + TASK_BOX_CARD_HEIGHT),  # Top-left
        (col2_x, row1_y, col2_x + TASK_BOX_CARD_WIDTH, row2_y + TASK_BOX_CARD_HEIGHT),  # Top-right
        (col1_x, row2_y, col1_x + TASK_BOX_CARD_WIDTH, row2_y + TASK_BOX_CARD_HEIGHT),  # Bottom-left
        (col2_x, row2_y, col2_x + TASK_BOX_CARD_WIDTH, row2_y + TASK_BOX_CARD_HEIGHT),  # Bottom-right
    ]
    
    # Draw each card
    for idx, step in enumerate(sequence_steps[:4]):  # Max 4 cards per page
        if idx < len(card_positions):
            card_rect = card_positions[idx]
            generate_sequence_card(
                draw, 
                card_rect, 
                step, 
                step.get('step_num', idx + 1),
                step.get('total_steps', len(sequence_steps)),
                folder_type=folder_type,
                with_labels=with_labels,
                theme_fonts=theme_fonts
            )
    
    # Add copyright footer
    draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
    
    # Add page number
    draw_page_number(draw, page_number, total_pages, PAGE_WIDTH, PAGE_HEIGHT)
    
    return page


def generate_sequencing_strips_set(items, theme_name='Theme', num_steps=3,
                                   include_errorless=True, include_mixed=True,
                                   include_real_images=False, real_image_items=None,
                                   output_dir='output', include_storage_label=False,
                                   theme_fonts=None):
    """
    Generate complete sequencing strips set with task-box sizing standard.
    
    Args:
        items: List of dict with 'image' and 'label' keys
        theme_name: Theme name for file naming
        num_steps: Number of steps per sequence (3 or 4)
        include_errorless: Generate errorless version (all steps identical)
        include_mixed: Generate mixed/scrambled version
        include_real_images: Generate real image version
        real_image_items: Optional list of real image items
        output_dir: Output directory
        include_storage_label: Generate storage labels
        theme_fonts: Optional theme fonts dict
        
    Returns:
        dict: Paths to generated files
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    output_files = {}
    
    # Prepare sequence steps
    if len(items) < num_steps:
        print(f"Warning: Need at least {num_steps} items for {num_steps}-step sequences. Using available items.")
        sequence_items = items
        num_steps = len(items)
    else:
        sequence_items = items[:num_steps]
    
    # Add step numbers to items
    for idx, item in enumerate(sequence_items):
        item['step_num'] = idx + 1
        item['total_steps'] = num_steps
    
    # 1. Generate standard (errorless) version - correct order
    if include_errorless:
        pages = []
        cards_per_page = 4
        
        # Create pages with 4 cards each
        for i in range(0, num_steps, cards_per_page):
            page_steps = sequence_items[i:i + cards_per_page]
            page = generate_sequencing_cards_page(
                page_steps,
                page_number=i // cards_per_page + 1,
                total_pages=(num_steps + cards_per_page - 1) // cards_per_page,
                folder_type='images',
                with_labels=True,
                theme_fonts=theme_fonts
            )
            pages.append(page)
        
        # Save errorless version
        filename = f'{theme_name}_Sequencing_{num_steps}Step_Errorless.pdf'
        filepath = os.path.join(output_dir, filename)
        save_images_as_pdf(pages, filepath)
        print(f"✓ Generated {num_steps}-step errorless sequencing: {filepath}")
        output_files['errorless'] = filepath
        
        # Generate storage label
        if include_storage_label:
            label_path = create_companion_label(
                main_pdf_path=filepath,
                theme_name=theme_name,
                activity_name=f'Sequencing {num_steps}-Step Errorless',
                level=None,
                icon_path=None
            )
            if label_path:
                print(f"✓ Generated storage label: {label_path}")
                output_files['errorless_label'] = label_path
    
    # 2. Generate mixed/scrambled version
    if include_mixed:
        # Scramble the order
        mixed_items = sequence_items.copy()
        random.shuffle(mixed_items)
        
        # Update step numbers to reflect scrambled order
        for idx, item in enumerate(mixed_items):
            item['step_num'] = idx + 1
        
        pages = []
        cards_per_page = 4
        
        for i in range(0, num_steps, cards_per_page):
            page_steps = mixed_items[i:i + cards_per_page]
            page = generate_sequencing_cards_page(
                page_steps,
                page_number=i // cards_per_page + 1,
                total_pages=(num_steps + cards_per_page - 1) // cards_per_page,
                folder_type='images',
                with_labels=True,
                theme_fonts=theme_fonts
            )
            pages.append(page)
        
        # Save mixed version
        filename = f'{theme_name}_Sequencing_{num_steps}Step_Mixed.pdf'
        filepath = os.path.join(output_dir, filename)
        save_images_as_pdf(pages, filepath)
        print(f"✓ Generated {num_steps}-step mixed sequencing: {filepath}")
        output_files['mixed'] = filepath
        
        # Generate storage label
        if include_storage_label:
            label_path = create_companion_label(
                main_pdf_path=filepath,
                theme_name=theme_name,
                activity_name=f'Sequencing {num_steps}-Step Mixed',
                level=None,
                icon_path=None
            )
            if label_path:
                print(f"✓ Generated storage label: {label_path}")
                output_files['mixed_label'] = label_path
    
    # 3. Generate real image version
    if include_real_images and real_image_items:
        real_items = real_image_items[:num_steps] if len(real_image_items) >= num_steps else real_image_items
        
        # Add step numbers
        for idx, item in enumerate(real_items):
            item['step_num'] = idx + 1
            item['total_steps'] = len(real_items)
        
        pages = []
        cards_per_page = 4
        actual_steps = len(real_items)
        
        for i in range(0, actual_steps, cards_per_page):
            page_steps = real_items[i:i + cards_per_page]
            page = generate_sequencing_cards_page(
                page_steps,
                page_number=i // cards_per_page + 1,
                total_pages=(actual_steps + cards_per_page - 1) // cards_per_page,
                folder_type='real_images',
                with_labels=True,
                theme_fonts=theme_fonts
            )
            pages.append(page)
        
        # Save real images version
        filename = f'{theme_name}_Sequencing_{actual_steps}Step_RealImages.pdf'
        filepath = os.path.join(output_dir, filename)
        save_images_as_pdf(pages, filepath)
        print(f"✓ Generated {actual_steps}-step real images sequencing: {filepath}")
        output_files['real_images'] = filepath
        
        # Generate storage label
        if include_storage_label:
            label_path = create_companion_label(
                main_pdf_path=filepath,
                theme_name=theme_name,
                activity_name=f'Sequencing {actual_steps}-Step Real Images',
                level=None,
                icon_path=None
            )
            if label_path:
                print(f"✓ Generated storage label: {label_path}")
                output_files['real_images_label'] = label_path
    
    return output_files


# Example usage
if __name__ == '__main__':
    # Example sequence items
    items = [
        {'image': 'bear.png', 'label': 'Brown Bear'},
        {'image': 'duck.png', 'label': 'Yellow Duck'},
        {'image': 'frog.png', 'label': 'Green Frog'},
        {'image': 'cat.png', 'label': 'Purple Cat'},
    ]
    
    # Generate 3-step sequences
    output = generate_sequencing_strips_set(
        items=items,
        theme_name='Brown_Bear',
        num_steps=3,
        include_errorless=True,
        include_mixed=True,
        include_real_images=False,
        output_dir='output',
        include_storage_label=True
    )
    
    print("\nGenerated files:")
    for key, path in output.items():
        print(f"  {key}: {path}")
