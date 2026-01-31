"""
Matching Cards Generator (Refactored with Modular Helpers)

Generates SPED-friendly matching card pairs with 4 differentiation levels:
- Level 1: Identical errorless matching (same image on both cards)
- Level 2: Outline-to-color matching (outline matches to color image)
- Level 3: AAC symbol to real image matching
- Level 4: AAC symbol to text matching

All cards follow SPED design principles: large images, high contrast,
minimal clutter, consistent spacing, and 300 DPI output.

Refactored to use modular helper functions from utils/draw_helpers.py
for clean, maintainable code.
"""

from PIL import Image, ImageDraw
from utils.config import MARGINS, CARD_SIZES, DPI, COLORS, FONT_SIZES, PAGE_WIDTH, PAGE_HEIGHT
from utils.image_loader import get_image_loader
from utils.pdf_export import save_images_as_pdf
from utils.draw_helpers import (
    calculate_cell_rect,
    scale_image_to_fit,
    draw_card_background,
    draw_page_number,
    draw_copyright_footer,
    draw_text_centered_in_rect,
    create_placeholder_image
)
from utils.storage_label_helper import create_companion_label
import os


def generate_matching_card(image_filename, label_text=None, card_size='large',
                           folder_type='color', card_type='image', level=1,
                           card_style=None):
    """
    Generate a single matching card using modular helper functions.
    
    Args:
        image_filename: Filename of the image (without folder path)
        label_text: Text label for the card
        card_size: 'standard', 'large', 'rectangle', or 'wide'
        folder_type: 'color', 'bw_outline', or 'aac'
        card_type: 'image' or 'text' (for Level 4)
        level: Differentiation level (1-4)
        card_style: Optional dict with 'border_width', 'corner_radius', 'shadow'
        
    Returns:
        PIL.Image: Generated card
    """
    # Get card dimensions
    width, height = CARD_SIZES[card_size]
    
    # Create blank card
    card = Image.new('RGBA', (width, height), COLORS['white'] + (255,))
    draw = ImageDraw.Draw(card)
    
    # Draw card background with optional styling
    if card_style is None:
        card_style = {
            'border_width': 2,
            'corner_radius': 10,
            'shadow': False,
            'fill_color': COLORS['white']
        }
    
    draw_card_background(draw, (0, 0, width, height), card_style)
    
    if card_type == 'text':
        # Level 4: Text-only card
        text = label_text if label_text else image_filename.replace('.png', '').replace('_', ' ').title()
        draw_text_centered_in_rect(draw, text, (0, 0, width, height), font_size=FONT_SIZES['body'])
        return card
    
    # Image-based card (Levels 1-3)
    image_loader = get_image_loader()
    
    try:
        theme_image = image_loader.load_image(image_filename, folder_type)
    except FileNotFoundError:
        # Create consistent placeholder
        theme_image = create_placeholder_image(500, 500, f"Missing:\n{image_filename}")
    
    # Scale and position image using helper function
    # Use minimal padding (5px) for maximum image size
    scaled_image, img_x, img_y = scale_image_to_fit(
        theme_image,
        (0, 0, width, height),
        padding=5
    )
    
    # Paste with alpha channel support
    card.paste(scaled_image, (img_x, img_y), scaled_image)
    
    return card


def generate_matching_pair(image_base_name, label_text=None, level=1, card_size='large',
                           card_style=None):
    """
    Generate a matching pair of cards based on differentiation level.
    
    Args:
        image_base_name: Base name of the image (e.g., 'bear')
        label_text: Text label for the item
        level: Differentiation level (1-4)
        card_size: Card size
        card_style: Optional dict with card styling options
        
    Returns:
        tuple: (card_a, card_b) - Two matching cards
    """
    if level == 1:
        # Level 1: Identical errorless matching
        card_a = generate_matching_card(
            f"{image_base_name}.png", label_text, card_size,
            folder_type='color', card_type='image', level=level, card_style=card_style
        )
        card_b = card_a.copy()
        
    elif level == 2:
        # Level 2: Outline-to-color matching
        card_a = generate_matching_card(
            f"{image_base_name}.png", label_text, card_size,
            folder_type='bw_outline', card_type='image', level=level, card_style=card_style
        )
        card_b = generate_matching_card(
            f"{image_base_name}.png", label_text, card_size,
            folder_type='color', card_type='image', level=level, card_style=card_style
        )
        
    elif level == 3:
        # Level 3: AAC symbol to real image matching
        card_a = generate_matching_card(
            f"{image_base_name}.png", label_text, card_size,
            folder_type='aac', card_type='image', level=level, card_style=card_style
        )
        card_b = generate_matching_card(
            f"{image_base_name}.png", label_text, card_size,
            folder_type='color', card_type='image', level=level, card_style=card_style
        )
        
    elif level == 4:
        # Level 4: AAC symbol to text matching
        card_a = generate_matching_card(
            f"{image_base_name}.png", label_text, card_size,
            folder_type='aac', card_type='image', level=level, card_style=card_style
        )
        card_b = generate_matching_card(
            f"{image_base_name}.png", label_text, card_size,
            folder_type='color', card_type='text', level=level, card_style=card_style
        )
    else:
        raise ValueError(f"Invalid level: {level}. Must be 1-4.")
    
    return (card_a, card_b)


def generate_matching_cards_set(items, level=1, card_size='large', 
                                 cards_per_page=6, output_dir='output', theme_name='Theme',
                                 include_storage_label=False, card_style=None,
                                 custom_spacing=20, custom_margin=50):
    """
    Generate a complete set of matching cards using modular helper functions.
    
    Args:
        items: List of dicts with 'image' (base name) and 'label' keys
        level: Differentiation level (1-4)
        card_size: Size of cards
        cards_per_page: Number of cards per page (6, 8, or 9)
        output_dir: Output directory
        theme_name: Theme name for filename
        include_storage_label: If True, also generate a companion storage label PDF
        card_style: Optional dict with 'border_width', 'corner_radius', 'shadow'
        custom_spacing: Space between cards in pixels
        custom_margin: Page margin in pixels
        
    Returns:
        List[str]: Paths to generated PDF files
    """
    # Determine grid layout
    if cards_per_page == 6:
        rows, cols = 2, 3
    elif cards_per_page == 8:
        rows, cols = 2, 4
    elif cards_per_page == 9:
        rows, cols = 3, 3
    else:
        # Auto-calculate
        rows = int(cards_per_page ** 0.5)
        cols = (cards_per_page + rows - 1) // rows
    
    # Prepare card style
    if card_style is None:
        card_style = {
            'border_width': 2,
            'corner_radius': 10,
            'shadow': False
        }
    
    # Generate all cards
    all_cards = []
    for item in items:
        image_name = item.get('image', item.get('filename', 'unknown'))
        label = item.get('label', image_name.replace('_', ' ').title())
        
        card_a, card_b = generate_matching_pair(
            image_name, label, level, card_size, card_style
        )
        all_cards.extend([card_a, card_b])
    
    # Create pages with grid layout
    pages = []
    total_pages = (len(all_cards) + cards_per_page - 1) // cards_per_page
    
    for page_idx in range(total_pages):
        # Create page canvas
        page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
        draw = ImageDraw.Draw(page)
        
        # Calculate cell positions using helper
        cell_rects = calculate_cell_rect(
            PAGE_WIDTH, PAGE_HEIGHT,
            rows, cols,
            padding=custom_spacing,
            margin=custom_margin,
            footer_height=80
        )
        
        # Get cards for this page
        start_idx = page_idx * cards_per_page
        end_idx = min(start_idx + cards_per_page, len(all_cards))
        page_cards = all_cards[start_idx:end_idx]
        
        # Place cards in grid
        for card_idx, card in enumerate(page_cards):
            if card_idx < len(cell_rects):
                x1, y1, x2, y2 = cell_rects[card_idx]
                
                # Scale card to fit cell
                cell_width = x2 - x1
                cell_height = y2 - y1
                card_resized = card.resize((cell_width, cell_height), Image.Resampling.LANCZOS)
                
                # Paste card
                page.paste(card_resized, (x1, y1), card_resized if card_resized.mode == 'RGBA' else None)
        
        # Add page number
        draw_page_number(draw, page_idx + 1, total_pages, PAGE_WIDTH, PAGE_HEIGHT, custom_margin)
        
        # Add copyright footer
        draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT, custom_margin)
        
        pages.append(page)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    level_names = {
        1: 'Level1_Identical_Errorless',
        2: 'Level2_Outline_to_Color',
        3: 'Level3_AAC_to_Image',
        4: 'Level4_AAC_to_Text'
    }
    level_name = level_names.get(level, f'Level{level}')
    filename = f"{theme_name}_Matching_{level_name}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    # Save PDF
    save_images_as_pdf(pages, output_path)
    print(f"✓ Generated {len(pages)} pages with {len(all_cards)} cards: {output_path}")
    print(f"  Grid: {rows}×{cols}, Spacing: {custom_spacing}px, Margin: {custom_margin}px")
    
    result_paths = [output_path]
    
    # Generate storage label if requested
    if include_storage_label:
        try:
            # Try to get first image for icon
            first_item = items[0] if items else None
            icon_path = None
            if first_item:
                image_loader = get_image_loader()
                try:
                    first_image = image_loader.load_image(
                        f"{first_item.get('image', 'unknown')}.png",
                        'color'
                    )
                    icon_path = first_image
                except:
                    icon_path = None
            
            label_path = create_companion_label(
                output_path,
                theme_name,
                "Matching Cards",
                level=level,
                icon=icon_path
            )
            result_paths.append(label_path)
            print(f"✓ Generated storage label: {label_path}")
        except Exception as e:
            print(f"⚠ Could not generate storage label: {e}")
    
    return result_paths
