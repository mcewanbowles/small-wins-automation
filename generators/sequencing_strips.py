"""
Sequencing Strips Generator - File Folder Activity Sizing

Generates full-width sequencing strips for US file folder activities.
Each sequence is displayed horizontally as a full-width strip with
all steps shown in order from left to right.

Features:
- Full-width US Letter sizing (11" × 2.5-3" per strip)
- 2-3 strips per page depending on height
- 3-step and 4-step sequences displayed horizontally
- Errorless version (correct order) and Mixed version (scrambled order)
- Real image version support
- Theme-aware design with high-contrast SPED-friendly layout
- Storage label generation
- Copyright compliance and page numbering

Requirements from specification:
- FILE FOLDER SIZING: Full-width strips (11" wide × 2.5-3" high)
- 2-3 strips per page
- Each strip shows complete sequence horizontally
- Step indicators for each step box
- 3-step and 4-step sequences
- Errorless version (correct order)
- Mixed version (scrambled order)
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
from utils.color_helpers import hex_to_grayscale, image_to_grayscale
import random

# File folder strip sizing (full-width US Letter strips)
# 11" wide × 2.75" high at 300 DPI
STRIP_WIDTH = int(11 * DPI)  # 3300px (full US Letter width)
STRIP_HEIGHT = int(2.75 * DPI)  # 825px (2.75 inches high)
MARGIN_TOP = int(0.5 * DPI)  # 150px top margin
MARGIN_BOTTOM = int(0.75 * DPI)  # 225px bottom margin for footer


def generate_sequence_strip(sequence_items, strip_y_position, folder_type='images', 
                           with_labels=True, theme_fonts=None, mode='color'):
    """
    Generate a single horizontal sequencing strip showing all steps.
    
    Args:
        sequence_items: List of step items (dict with 'image', 'label', 'step_num', 'total_steps')
        strip_y_position: Y position where strip should be drawn
        folder_type: Image folder type ('images', 'real_images', etc.')
        with_labels: Include text label below icon
        theme_fonts: Optional dict of theme fonts
        mode: Output mode - 'color' or 'bw' (black-and-white)
        
    Returns:
        PIL.Image: Strip image
    """
    # Determine colors based on mode
    bg_color = COLORS['white'] if mode == 'color' else '#FFFFFF'
    border_color = COLORS['black'] if mode == 'color' else '#000000'
    text_color = COLORS['black'] if mode == 'color' else '#000000'
    
    # Create strip image
    strip = Image.new('RGB', (STRIP_WIDTH, STRIP_HEIGHT), bg_color)
    draw = ImageDraw.Draw(strip)
    
    # Draw outer border
    draw.rectangle([0, 0, STRIP_WIDTH - 1, STRIP_HEIGHT - 1], 
                  outline=border_color, width=4)
    
    num_steps = len(sequence_items)
    
    # Calculate step box dimensions
    # Divide strip width equally among steps
    step_box_width = STRIP_WIDTH // num_steps
    
    # Draw each step box
    for idx, step_item in enumerate(sequence_items):
        x_start = idx * step_box_width
        x_end = x_start + step_box_width
        
        # Draw vertical divider between steps (except after last step)
        if idx < num_steps - 1:
            draw.line([(x_end, 0), (x_end, STRIP_HEIGHT)], 
                     fill=COLORS['black'], width=3)
        
        # Layout within each step box
        step_indicator_height = 50  # "Step 1" indicator
        icon_area_height = int(STRIP_HEIGHT * 0.60) - step_indicator_height
        label_area_height = int(STRIP_HEIGHT * 0.40)
        
        # 1. Step indicator at top
        step_num = step_item.get('step_num', idx + 1)
        total_steps = step_item.get('total_steps', num_steps)
        step_text = f"Step {step_num}"
        
        # Mode-aware colors for step indicator
        step_bg_color = COLORS['light_gray'] if mode == 'color' else '#F0F0F0'
        step_border_color = COLORS['dark_gray'] if mode == 'color' else '#808080'
        
        step_bg_rect = (x_start + 10, 10, x_end - 10, step_indicator_height)
        draw.rectangle(step_bg_rect, fill=step_bg_color, 
                      outline=step_border_color, width=2)
        draw_text_centered_in_rect(draw, step_text, step_bg_rect, 
                                   font_size=24, color=text_color)
        
        # 2. Icon area
        icon_padding = 20
        icon_rect = (
            x_start + icon_padding,
            step_indicator_height + 15,
            x_end - icon_padding,
            step_indicator_height + icon_area_height
        )
        
        # Load and draw image
        image_loader = get_image_loader()
        try:
            img = image_loader.load_image(step_item['image'], folder_type)
            if img:
                # Convert to grayscale if in BW mode
                if mode == 'bw':
                    img = image_to_grayscale(img)
                
                scaled_img, (img_x, img_y) = scale_image_to_fit(img, icon_rect, padding=5)
                
                if scaled_img.mode == 'RGBA':
                    strip.paste(scaled_img, (img_x, img_y), scaled_img)
                else:
                    strip.paste(scaled_img, (img_x, img_y))
        except:
            # Use placeholder
            placeholder_width = icon_rect[2] - icon_rect[0]
            placeholder_height = icon_rect[3] - icon_rect[1]
            placeholder = create_placeholder_image(placeholder_width, placeholder_height,
                                                  step_item.get('label', 'Image'))
            strip.paste(placeholder, (icon_rect[0], icon_rect[1]))
        
        # 3. Label area (if enabled)
        if with_labels and 'label' in step_item:
            label_y_start = step_indicator_height + icon_area_height + 5
            label_rect = (
                x_start + 10,
                label_y_start,
                x_end - 10,
                STRIP_HEIGHT - 10
            )
            draw_text_centered_in_rect(draw, step_item['label'], label_rect,
                                       font_size=28, color=text_color)
    
    return strip


def generate_sequencing_strips_page(sequences, page_number, total_pages,
                                   folder_type='images', with_labels=True, theme_fonts=None, mode='color'):
    """
    Generate a page with 2-3 sequencing strips (file folder sizing).
    
    Args:
        sequences: List of sequences, each sequence is a list of step items
        page_number: Current page number
        total_pages: Total number of pages
        folder_type: Image folder type
        with_labels: Include text labels
        theme_fonts: Optional theme fonts dict
        mode: Output mode - 'color' or 'bw'
        
    Returns:
        PIL.Image: Generated page with strips
    """
    # Mode-aware background color
    bg_color = COLORS['white'] if mode == 'color' else '#FFFFFF'
    
    # Create page
    page = Image.new('RGB', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), bg_color)
    
    # Calculate positions for strips
    # Available height = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    available_height = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    num_strips = len(sequences)
    
    # Calculate spacing
    if num_strips == 1:
        strip_spacing = 0
        y_positions = [MARGIN_TOP]
    elif num_strips == 2:
        strip_spacing = (available_height - 2 * STRIP_HEIGHT) // 3
        y_positions = [
            MARGIN_TOP + strip_spacing,
            MARGIN_TOP + strip_spacing + STRIP_HEIGHT + strip_spacing
        ]
    else:  # 3 strips
        strip_spacing = (available_height - 3 * STRIP_HEIGHT) // 4
        y_positions = [
            MARGIN_TOP + strip_spacing,
            MARGIN_TOP + strip_spacing + STRIP_HEIGHT + strip_spacing,
            MARGIN_TOP + 2 * strip_spacing + 2 * STRIP_HEIGHT + strip_spacing
        ]
    
    # Generate and paste each strip
    for idx, sequence_items in enumerate(sequences[:3]):  # Max 3 strips per page
        if idx < len(y_positions):
            strip = generate_sequence_strip(
                sequence_items,
                y_positions[idx],
                folder_type=folder_type,
                with_labels=with_labels,
                theme_fonts=theme_fonts,
                mode=mode
            )
            # Paste strip onto page
            # Center horizontally
            x_position = (int(PAGE_WIDTH) - STRIP_WIDTH) // 2
            page.paste(strip, (x_position, int(y_positions[idx])))
    
    # Add copyright footer and page number
    draw = ImageDraw.Draw(page)
    draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
    draw_page_number(draw, page_number, total_pages, PAGE_WIDTH, PAGE_HEIGHT)
    
    return page


def generate_sequencing_strips_set(items, theme_name='Theme', num_steps=3,
                                   include_errorless=True, include_mixed=True,
                                   include_real_images=False, real_image_items=None,
                                   output_dir='output', include_storage_label=False,
                                   theme_fonts=None, mode='color'):
    """
    Generate complete sequencing strips set with file folder sizing.
    
    Args:
        items: List of dict with 'image' and 'label' keys
        theme_name: Theme name for file naming
        num_steps: Number of steps per sequence (3 or 4)
        include_errorless: Generate errorless version (correct order)
        include_mixed: Generate mixed/scrambled version
        include_real_images: Generate real image version
        real_image_items: Optional list of real image items
        output_dir: Output directory
        include_storage_label: Generate storage labels
        theme_fonts: Optional theme fonts dict
        mode: Output mode - 'color' or 'bw' (default: 'color')
        
    Returns:
        dict: Paths to generated files (includes both color and bw files if mode used for dual generation)
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
        # Create single strip showing sequence
        # Each page can have multiple copies of the same sequence for cutting
        # Let's put 3 identical strips per page
        sequences_per_page = 3
        pages = []
        
        # Generate 1 page with 3 identical strips
        page_sequences = [sequence_items.copy() for _ in range(sequences_per_page)]
        page = generate_sequencing_strips_page(
            page_sequences,
            page_number=1,
            total_pages=1,
            folder_type='images',
            with_labels=True,
            theme_fonts=theme_fonts,
            mode=mode
        )
        pages.append(page)
        
        # Save errorless version with mode suffix
        mode_suffix = '_color' if mode == 'color' else '_bw'
        filename = f'{theme_name}_Sequencing_{num_steps}Step_Errorless{mode_suffix}.pdf'
        filepath = os.path.join(output_dir, filename)
        save_images_as_pdf(pages, filepath)
        print(f"✓ Generated {num_steps}-step errorless sequencing ({mode}): {filepath}")
        output_files[f'errorless_{mode}'] = filepath
        
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
            item['step_num'] = item.get('original_step_num', idx + 1)
        
        # Generate 3 identical strips per page
        sequences_per_page = 3
        pages = []
        
        page_sequences = [mixed_items.copy() for _ in range(sequences_per_page)]
        page = generate_sequencing_strips_page(
            page_sequences,
            page_number=1,
            total_pages=1,
            folder_type='images',
            with_labels=True,
            theme_fonts=theme_fonts,
            mode=mode
        )
        pages.append(page)
        
        # Save mixed version with mode suffix
        mode_suffix = '_color' if mode == 'color' else '_bw'
        filename = f'{theme_name}_Sequencing_{num_steps}Step_Mixed{mode_suffix}.pdf'
        filepath = os.path.join(output_dir, filename)
        save_images_as_pdf(pages, filepath)
        print(f"✓ Generated {num_steps}-step mixed sequencing ({mode}): {filepath}")
        output_files[f'mixed_{mode}'] = filepath
        
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
        
        actual_steps = len(real_items)
        sequences_per_page = 3
        pages = []
        
        page_sequences = [real_items.copy() for _ in range(sequences_per_page)]
        page = generate_sequencing_strips_page(
            page_sequences,
            page_number=1,
            total_pages=1,
            folder_type='real_images',
            with_labels=True,
            theme_fonts=theme_fonts,
            mode=mode
        )
        pages.append(page)
        
        # Save real images version with mode suffix
        mode_suffix = '_color' if mode == 'color' else '_bw'
        filename = f'{theme_name}_Sequencing_{actual_steps}Step_RealImages{mode_suffix}.pdf'
        filepath = os.path.join(output_dir, filename)
        save_images_as_pdf(pages, filepath)
        print(f"✓ Generated {actual_steps}-step real images sequencing ({mode}): {filepath}")
        output_files[f'real_images_{mode}'] = filepath
        
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


def generate_sequencing_strips_dual_mode(items, theme_name='Theme', num_steps=3,
                                         include_errorless=True, include_mixed=True,
                                         include_real_images=False, real_image_items=None,
                                         output_dir='output', include_storage_label=False,
                                         theme_fonts=None):
    """
    Generate sequencing strips in both color and black-and-white modes.
    
    This is a convenience wrapper that calls generate_sequencing_strips_set twice
    to automatically produce both color and BW versions.
    
    Args:
        items: List of dict with 'image' and 'label' keys
        theme_name: Theme name for file naming
        num_steps: Number of steps per sequence (3 or 4)
        include_errorless: Generate errorless version (correct order)
        include_mixed: Generate mixed/scrambled version
        include_real_images: Generate real image version
        real_image_items: Optional list of real image items
        output_dir: Output directory
        include_storage_label: Generate storage labels
        theme_fonts: Optional theme fonts dict
        
    Returns:
        dict: Combined paths to all generated files (color and BW)
    """
    output_files = {}
    
    # Generate color version
    print("\n=== Generating COLOR version ===")
    color_files = generate_sequencing_strips_set(
        items=items,
        theme_name=theme_name,
        num_steps=num_steps,
        include_errorless=include_errorless,
        include_mixed=include_mixed,
        include_real_images=include_real_images,
        real_image_items=real_image_items,
        output_dir=output_dir,
        include_storage_label=include_storage_label,
        theme_fonts=theme_fonts,
        mode='color'
    )
    output_files.update(color_files)
    
    # Generate black-and-white version
    print("\n=== Generating BLACK-AND-WHITE version ===")
    bw_files = generate_sequencing_strips_set(
        items=items,
        theme_name=theme_name,
        num_steps=num_steps,
        include_errorless=include_errorless,
        include_mixed=include_mixed,
        include_real_images=include_real_images,
        real_image_items=real_image_items,
        output_dir=output_dir,
        include_storage_label=include_storage_label,
        theme_fonts=theme_fonts,
        mode='bw'
    )
    output_files.update(bw_files)
    
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
    
    # Generate 3-step sequences in both color and BW modes
    output = generate_sequencing_strips_dual_mode(
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
