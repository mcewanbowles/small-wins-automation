"""
Sequencing Strips Generator

Generates sequencing strips for teaching order and temporal sequences.
Includes 3-step and 4-step sequences with differentiation levels:
- Level 1: Errorless (correct order)
- Level 2: Mixed order (scrambled)
- Level 3: Cut-and-paste version
- Level 4: WH-version ("What happens next?")

Features lanyard-friendly design with hole-punch indicators and
interchangeable icons matching exact size of matching cards.
"""

import os
from PIL import Image, ImageDraw, ImageFont
from utils.config import DPI, PAGE_WIDTH, PAGE_HEIGHT, MARGINS, CARD_SIZES, FONT_SIZES, COLORS
from utils.image_loader import get_image_loader
from utils.layout import create_page_canvas, add_page_border
from utils.pdf_export import save_images_as_pdf
from utils.draw_helpers import (
    scale_image_to_fit,
    draw_card_background,
    draw_page_number,
    draw_copyright_footer,
    draw_text_centered_in_rect,
    create_placeholder_image
)
from utils.fonts import get_font_manager
from utils.storage_label_helper import create_companion_label
import random


def generate_sequencing_strip(sequence_items, strip_number=1, total_strips=1,
                              with_lanyard=True, card_style=None, with_labels=True):
    """
    Generate a single sequencing strip page with horizontal icon layout.
    
    Args:
        sequence_items: List of dict with 'image' and 'label' keys (3 or 4 items)
        strip_number: Current strip number for page numbering
        total_strips: Total number of strips for page numbering
        with_lanyard: Include lanyard strip with hole-punch indicator
        card_style: Optional dict with border_width, corner_radius, shadow
        with_labels: Include text labels under icons
        
    Returns:
        PIL.Image: Generated strip page
    """
    # Create page
    page = create_page_canvas()
    draw = ImageDraw.Draw(page)
    
    # Default card style
    if card_style is None:
        card_style = {'border_width': 2, 'corner_radius': 10, 'shadow': False}
    
    # Constants
    num_slots = len(sequence_items)
    icon_size = CARD_SIZES['standard']  # 750x750px - same as matching cards
    label_height = 60 if with_labels else 0
    
    # Lanyard strip specifications
    lanyard_width = 150 if with_lanyard else 0
    
    # Calculate strip dimensions
    strip_height = icon_size + label_height + 40  # 40px padding
    strip_width = PAGE_WIDTH - 2 * MARGINS['page']
    
    # Calculate icon area
    icon_area_width = strip_width - lanyard_width - 20  # 20px separator
    icon_spacing = 20
    total_icon_width = num_slots * icon_size + (num_slots - 1) * icon_spacing
    
    # Center the icons in available space
    start_x = MARGINS['page'] + lanyard_width + 20 + (icon_area_width - total_icon_width) // 2
    start_y = (PAGE_HEIGHT - strip_height - 200) // 2  # Leave room for footer
    
    # Draw lanyard strip if enabled
    if with_lanyard:
        lanyard_x = MARGINS['page']
        lanyard_y = start_y
        
        # Draw reinforced border
        draw.rectangle(
            [(lanyard_x, lanyard_y), (lanyard_x + lanyard_width, lanyard_y + strip_height)],
            outline=COLORS['black'],
            width=5
        )
        
        # Draw hole-punch indicator (centered)
        hole_center_x = lanyard_x + lanyard_width // 2
        hole_center_y = lanyard_y + strip_height // 2
        hole_radius = 15
        
        # Draw concentric circles for reinforcement pattern
        for r in range(hole_radius, hole_radius + 15, 3):
            draw.ellipse(
                [(hole_center_x - r, hole_center_y - r),
                 (hole_center_x + r, hole_center_y + r)],
                outline=COLORS['dark_gray'],
                width=1
            )
        
        # Draw center hole
        draw.ellipse(
            [(hole_center_x - hole_radius, hole_center_y - hole_radius),
             (hole_center_x + hole_radius, hole_center_y + hole_radius)],
            fill=COLORS['white'],
            outline=COLORS['black'],
            width=2
        )
        
        # Draw vertical separator line
        separator_x = lanyard_x + lanyard_width + 10
        draw.line(
            [(separator_x, lanyard_y), (separator_x, lanyard_y + strip_height)],
            fill=COLORS['black'],
            width=3
        )
    
    # Load image loader
    image_loader = get_image_loader()
    font_manager = get_font_manager()
    
    # Draw each icon in the sequence
    for i, item in enumerate(sequence_items):
        # Calculate position
        icon_x = start_x + i * (icon_size + icon_spacing)
        icon_y = start_y + 20
        
        # Draw card background
        cell_rect = (icon_x, icon_y, icon_x + icon_size, icon_y + icon_size)
        draw_card_background(draw, cell_rect, card_style)
        
        # Load and scale image
        try:
            folder_type = item.get('folder_type', 'images')
            theme_image = image_loader.load_image(item['image'], folder_type)
        except Exception:
            theme_image = create_placeholder_image(icon_size, icon_size, item.get('label', 'Image'))
        
        # Scale image to fit with minimal padding
        scaled_img, (img_x, img_y) = scale_image_to_fit(
            theme_image,
            cell_rect,
            padding=5
        )
        
        # Paste image
        if scaled_img.mode == 'RGBA':
            page.paste(scaled_img, (img_x, img_y), scaled_img)
        else:
            page.paste(scaled_img, (img_x, img_y))
        
        # Draw label if enabled
        if with_labels and 'label' in item:
            label_y = icon_y + icon_size + 5
            label_rect = (icon_x, label_y, icon_x + icon_size, label_y + label_height - 5)
            
            try:
                font = font_manager.get_font('body', FONT_SIZES['body'])
            except:
                font = None
            
            draw_text_centered_in_rect(draw, item['label'], label_rect, font, COLORS['black'])
    
    # Add page border
    add_page_border(page)
    
    # Add copyright footer
    draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
    
    # Add page number
    draw_page_number(draw, strip_number, total_strips, PAGE_WIDTH, PAGE_HEIGHT)
    
    return page


def generate_cutout_icons_page(icon_items, page_number=1, total_pages=1,
                               with_bold_outline=True, with_grab_tab=True,
                               card_style=None):
    """
    Generate a page of cut-out sequencing icons (6 per page in 2x3 grid).
    
    Args:
        icon_items: List of dict with 'image' and 'label' keys (max 6)
        page_number: Current page number
        total_pages: Total number of pages
        with_bold_outline: Add 3px border for visibility
        with_grab_tab: Add scissors grab tab for fine motor support
        card_style: Optional dict with border_width, corner_radius, shadow
        
    Returns:
        PIL.Image: Generated cut-out page
    """
    # Create page
    page = create_page_canvas()
    draw = ImageDraw.Draw(page)
    
    # Default card style
    if card_style is None:
        card_style = {'border_width': 3 if with_bold_outline else 2, 'corner_radius': 10, 'shadow': False}
    
    # Grid layout: 2 rows x 3 columns
    icon_size = CARD_SIZES['standard']  # 750x750px
    cols = 3
    rows = 2
    spacing = 40
    
    # Calculate starting position to center grid
    total_width = cols * icon_size + (cols - 1) * spacing
    total_height = rows * icon_size + (rows - 1) * spacing
    start_x = (PAGE_WIDTH - total_width) // 2
    start_y = (PAGE_HEIGHT - total_height - 200) // 2  # Leave room for footer
    
    # Load resources
    image_loader = get_image_loader()
    
    # Draw each icon
    for idx, item in enumerate(icon_items[:6]):  # Max 6 icons
        row = idx // cols
        col = idx % cols
        
        # Calculate position
        icon_x = start_x + col * (icon_size + spacing)
        icon_y = start_y + row * (icon_size + spacing)
        
        # Draw card background
        cell_rect = (icon_x, icon_y, icon_x + icon_size, icon_y + icon_size)
        draw_card_background(draw, cell_rect, card_style)
        
        # Load and scale image
        try:
            folder_type = item.get('folder_type', 'images')
            theme_image = image_loader.load_image(item['image'], folder_type)
        except Exception:
            theme_image = create_placeholder_image(icon_size, icon_size, item.get('label', 'Image'))
        
        # Scale image to fit
        scaled_img, (img_x, img_y) = scale_image_to_fit(
            theme_image,
            cell_rect,
            padding=5
        )
        
        # Paste image
        if scaled_img.mode == 'RGBA':
            page.paste(scaled_img, (img_x, img_y), scaled_img)
        else:
            page.paste(scaled_img, (img_x, img_y))
        
        # Add grab tab if enabled
        if with_grab_tab:
            tab_width = 80
            tab_height = 30
            tab_x = icon_x + icon_size - tab_width - 10
            tab_y = icon_y - tab_height + 5
            
            # Draw tab
            draw.rectangle(
                [(tab_x, tab_y), (tab_x + tab_width, tab_y + tab_height)],
                fill=COLORS['light_gray'],
                outline=COLORS['black'],
                width=2
            )
            
            # Draw scissors symbol
            try:
                font_manager = get_font_manager()
                font = font_manager.get_font('body', 20)
            except:
                font = None
            
            scissors_text = "✂"
            if font:
                bbox = draw.textbbox((0, 0), scissors_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = tab_x + (tab_width - text_width) // 2
                text_y = tab_y + (tab_height - text_height) // 2
                draw.text((text_x, text_y), scissors_text, fill=COLORS['black'], font=font)
    
    # Add page border
    add_page_border(page)
    
    # Add copyright footer
    draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
    
    # Add page number
    draw_page_number(draw, page_number, total_pages, PAGE_WIDTH, PAGE_HEIGHT)
    
    return page


def generate_sequencing_strips_set(sequences, theme_name='Theme', level=1,
                                   output_dir='output', with_lanyard=True,
                                   with_cutout_icons=True, include_storage_label=False,
                                   card_style=None):
    """
    Generate complete sequencing strips set with differentiation levels.
    
    Args:
        sequences: List of sequences, each with 'steps' (list of items) and 'title'
        theme_name: Theme name for file naming
        level: Differentiation level (1-4)
        output_dir: Output directory
        with_lanyard: Include lanyard strip with hole-punch
        with_cutout_icons: Generate separate cut-out icon pages
        include_storage_label: Generate storage labels
        card_style: Optional dict with border_width, corner_radius, shadow
        
    Returns:
        dict: Paths to generated files
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine level suffix
    level_names = {
        1: 'Errorless',
        2: 'Mixed',
        3: 'Cut_Paste',
        4: 'WH_Questions'
    }
    level_suffix = level_names.get(level, 'Level' + str(level))
    
    # Generate strip pages
    strip_pages = []
    all_icons = []
    
    for seq_idx, sequence in enumerate(sequences):
        steps = sequence.get('steps', [])
        
        # Apply level-specific transformations
        if level == 1:
            # Errorless: Keep correct order
            ordered_steps = steps
        elif level == 2:
            # Mixed order: Scramble
            ordered_steps = steps.copy()
            random.shuffle(ordered_steps)
        elif level == 3:
            # Cut-and-paste: Empty strip (will generate separate cutouts)
            ordered_steps = [{'image': 'placeholder.png', 'label': f'Step {i+1}'} for i in range(len(steps))]
        elif level == 4:
            # WH-version: Add "What happens next?" text
            ordered_steps = steps
        
        # Generate strip
        strip_page = generate_sequencing_strip(
            ordered_steps,
            strip_number=seq_idx + 1,
            total_strips=len(sequences),
            with_lanyard=with_lanyard,
            card_style=card_style,
            with_labels=(level != 3)
        )
        strip_pages.append(strip_page)
        
        # Collect icons for cutout page
        all_icons.extend(steps)
    
    # Save strip pages
    strips_filename = f'{theme_name}_Sequencing_Strips_{level_suffix}.pdf'
    strips_path = os.path.join(output_dir, strips_filename)
    save_images_as_pdf(strip_pages, strips_path)
    print(f"✓ Generated sequencing strips: {strips_path}")
    
    output_files = {'strips': strips_path}
    
    # Generate cut-out icon pages if requested
    if with_cutout_icons and all_icons:
        cutout_pages = []
        icons_per_page = 6
        
        for i in range(0, len(all_icons), icons_per_page):
            page_icons = all_icons[i:i + icons_per_page]
            cutout_page = generate_cutout_icons_page(
                page_icons,
                page_number=i // icons_per_page + 1,
                total_pages=(len(all_icons) + icons_per_page - 1) // icons_per_page,
                with_bold_outline=True,
                with_grab_tab=True,
                card_style=card_style
            )
            cutout_pages.append(cutout_page)
        
        # Save cutout pages
        cutouts_filename = f'{theme_name}_Sequencing_Icons_Cutouts.pdf'
        cutouts_path = os.path.join(output_dir, cutouts_filename)
        save_images_as_pdf(cutout_pages, cutouts_path)
        print(f"✓ Generated sequencing cutout icons: {cutouts_path}")
        
        output_files['cutouts'] = cutouts_path
    
    # Generate storage labels if requested
    if include_storage_label:
        # Label for strips
        strips_label_path = create_companion_label(
            main_pdf_path=strips_path,
            theme_name=theme_name,
            activity_name='Sequencing Strips',
            level=level if level in [1, 2, 3, 4] else None,
            icon_path=None
        )
        if strips_label_path:
            print(f"✓ Generated strips storage label: {strips_label_path}")
            output_files['strips_label'] = strips_label_path
        
        # Label for cutouts
        if with_cutout_icons and 'cutouts' in output_files:
            cutouts_label_path = create_companion_label(
                main_pdf_path=output_files['cutouts'],
                theme_name=theme_name,
                activity_name='Sequencing Icons Cutouts',
                level=None,
                icon_path=None
            )
            if cutouts_label_path:
                print(f"✓ Generated cutouts storage label: {cutouts_label_path}")
                output_files['cutouts_label'] = cutouts_label_path
    
    return output_files
