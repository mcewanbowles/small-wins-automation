"""
Sorting Cards Generator (Modular Architecture)

Generates SPED-friendly sorting materials with differentiation levels:
- Sorting Mats: Category headers with drop zones and answer keys
- Sorting Cards: Cut-out cards to be sorted into categories

Supports 3 differentiation levels:
- Level 1: Real images with text labels (most support)
- Level 2: Real images only (less visual support)
- Level 3: Text only or AAC symbols (highest difficulty)

All materials follow SPED design principles: large images, high contrast,
minimal clutter, consistent spacing, and 300 DPI output.

Uses modular helper functions from utils/draw_helpers.py for maintainable code.
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
    fit_text_to_width,
    create_placeholder_image
)
from utils.storage_label_helper import create_companion_label
from utils.fonts import get_font_manager
from utils.color_helpers import image_to_grayscale
from utils.layout import create_page_canvas, add_footer
import os


def generate_sorting_mat(category_name, items, level=1, card_style=None, 
                         show_answer_key=True, mode='color'):
    """
    Generate a sorting mat with category header and drop zone.
    
    Args:
        category_name: Name of the category (e.g., "Animals", "Colors")
        items: List of items that belong to this category (for answer key)
        level: Differentiation level (1-3)
        card_style: Optional styling dict for borders/shadows
        show_answer_key: Whether to show watermarked answer key
        mode: 'color' or 'bw' for output mode
        
    Returns:
        PIL.Image: Generated sorting mat page
    """
    # Create page canvas
    page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
    draw = ImageDraw.Draw(page)
    
    # Default card style
    if card_style is None:
        card_style = {
            'border_width': 3,
            'corner_radius': 12,
            'shadow': True,
            'fill_color': COLORS['white']
        }
    
    # Calculate layout areas
    margin = MARGINS['page']
    title_height = 150
    answer_key_height = 200 if show_answer_key else 0
    drop_zone_y = margin + title_height + 30
    drop_zone_height = PAGE_HEIGHT - drop_zone_y - answer_key_height - margin - 60  # 60 for footer
    
    # Title bar with category name
    title_rect = (margin, margin, PAGE_WIDTH - margin, margin + title_height)
    title_style = card_style.copy()
    title_style['fill_color'] = COLORS['light_blue']
    draw_card_background(draw, title_rect, title_style)
    
    # Category name text
    font_manager = get_font_manager()
    try:
        title_font = font_manager.get_font('heading', FONT_SIZES['title'])
    except:
        title_font = None
    
    draw_text_centered_in_rect(draw, category_name.upper(), title_rect, 
                               font_size=FONT_SIZES['title'])
    
    # Drop zone area
    drop_zone_rect = (margin, drop_zone_y, PAGE_WIDTH - margin, 
                      drop_zone_y + drop_zone_height)
    drop_zone_style = card_style.copy()
    drop_zone_style['border_width'] = 4
    drop_zone_style['fill_color'] = (245, 245, 250)  # Very light blue-gray
    draw_card_background(draw, drop_zone_rect, drop_zone_style)
    
    # Add "Sort Here" text in drop zone
    try:
        drop_font = font_manager.get_font('body', FONT_SIZES['heading'])
    except:
        drop_font = None
    
    draw.text(
        (PAGE_WIDTH // 2, drop_zone_y + 40),
        "Sort Here ↓",
        fill=COLORS['medium_gray'],
        font=drop_font,
        anchor='mt'
    )
    
    # Answer key with watermarked images (if enabled)
    if show_answer_key and items:
        answer_key_y = drop_zone_y + drop_zone_height + 20
        
        # Answer key background
        answer_rect = (margin, answer_key_y, PAGE_WIDTH - margin, 
                      answer_key_y + answer_key_height)
        answer_style = {
            'border_width': 2,
            'corner_radius': 8,
            'shadow': False,
            'fill_color': (255, 255, 240)  # Light yellow
        }
        draw_card_background(draw, answer_rect, answer_style)
        
        # "Answer Key" label
        draw.text(
            (margin + 20, answer_key_y + 10),
            "Answer Key:",
            fill=COLORS['dark_gray'],
            font=drop_font,
            anchor='lt'
        )
        
        # Draw watermarked answer images
        image_loader = get_image_loader()
        num_items = min(len(items), 5)  # Max 5 items in answer key
        
        if num_items > 0:
            cell_width = (PAGE_WIDTH - 2 * margin - 150) // num_items
            cell_height = answer_key_height - 50
            
            for i, item in enumerate(items[:num_items]):
                try:
                    img_filename = item.get('image', item) if isinstance(item, dict) else item
                    if not img_filename.endswith('.png'):
                        img_filename += '.png'
                    
                    answer_img = image_loader.load_image(img_filename, 'color')
                    
                    # Scale and watermark
                    cell_rect = (
                        margin + 150 + i * cell_width,
                        answer_key_y + 40,
                        margin + 150 + (i + 1) * cell_width - 10,
                        answer_key_y + 40 + cell_height
                    )
                    
                    scaled_img, img_x, img_y = scale_image_to_fit(
                        answer_img, cell_rect, padding=5
                    )
                    
                    # Apply watermark effect (reduce opacity)
                    watermarked = scaled_img.copy()
                    watermarked.putalpha(128)  # 50% transparency
                    
                    page.paste(watermarked, (img_x, img_y), watermarked)
                    
                except (FileNotFoundError, Exception) as e:
                    # Skip missing images in answer key
                    pass
    
    # Add copyright footer
    draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
    
    return page


def generate_sorting_card(image_filename, label_text=None, card_size='standard',
                          folder_type='color', card_type='image', level=1,
                          card_style=None, mode='color'):
    """
    Generate a single sorting card using modular helper functions.
    
    Args:
        image_filename: Filename of the image (without folder path)
        label_text: Text label for the card
        card_size: 'standard', 'large', 'rectangle', or 'wide'
        folder_type: 'color', 'bw_outline', or 'aac'
        card_type: 'image' or 'text' (for Level 3)
        level: Differentiation level (1-3)
        card_style: Optional dict with 'border_width', 'corner_radius', 'shadow'
        mode: 'color' or 'bw' for output mode
        
    Returns:
        PIL.Image: Generated sorting card
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
        # Level 3: Text-only card
        text = label_text if label_text else image_filename.replace('.png', '').replace('_', ' ').title()
        draw_text_centered_in_rect(draw, text, (0, 0, width, height), 
                                   font_size=FONT_SIZES['body'])
        return card
    
    # Image-based card (Levels 1-2)
    image_loader = get_image_loader()
    
    try:
        theme_image = image_loader.load_image(image_filename, folder_type)
        # Convert to grayscale if in BW mode
        if mode == 'bw':
            theme_image = image_to_grayscale(theme_image)
    except FileNotFoundError:
        # Create consistent placeholder
        theme_image = create_placeholder_image(500, 500, f"Missing:\n{image_filename}")
    
    # Calculate image and label areas
    if level == 1 and label_text:
        # Level 1: Image + label
        label_height = 60
        image_rect = (0, 0, width, height - label_height)
        label_rect = (0, height - label_height, width, height)
        
        # Scale and position image
        scaled_image, img_x, img_y = scale_image_to_fit(
            theme_image, image_rect, padding=10
        )
        
        # Paste image with alpha channel support
        card.paste(scaled_image, (img_x, img_y), scaled_image)
        
        # Add label
        draw_text_centered_in_rect(draw, label_text, label_rect, 
                                   font_size=FONT_SIZES['body'])
    else:
        # Level 2+: Image only
        scaled_image, img_x, img_y = scale_image_to_fit(
            theme_image, (0, 0, width, height), padding=5
        )
        
        # Paste with alpha channel support
        card.paste(scaled_image, (img_x, img_y), scaled_image)
    
    return card


def generate_sorting_cards_set(categories, theme_name='Theme', level=1, 
                               card_size='standard', cards_per_page=6,
                               output_dir='output', include_storage_label=False,
                               card_style=None, mode='color'):
    """
    Generate a complete sorting cards set with mats and cut-out cards.
    
    Args:
        categories: Dict mapping category names to lists of items
                   e.g., {'Animals': [{'image': 'bear', 'label': 'Bear'}, ...],
                          'Colors': [...]}
        theme_name: Name of the theme for file naming
        level: Differentiation level (1-3)
        card_size: Size of sorting cards
        cards_per_page: Number of cards per page
        output_dir: Output directory for PDFs
        include_storage_label: Whether to generate storage label
        card_style: Optional styling dict for borders/shadows
        mode: 'color' or 'bw' for output mode
        
    Returns:
        List[str]: Paths to generated PDF files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine folder type and card type based on level
    if level == 1:
        folder_type = 'color'
        card_type = 'image'
        level_name = 'Level1_Images_With_Labels'
    elif level == 2:
        folder_type = 'color'
        card_type = 'image'
        level_name = 'Level2_Images_Only'
    else:  # level 3
        folder_type = 'aac'
        card_type = 'text'
        level_name = 'Level3_Text_Or_AAC'
    
    all_pages = []
    
    # Generate sorting mats (one per category)
    print(f"Generating sorting mats for {len(categories)} categories...")
    
    for category_name, items in categories.items():
        mat_page = generate_sorting_mat(
            category_name=category_name,
            items=items,
            level=level,
            card_style=card_style,
            show_answer_key=True,
            mode=mode
        )
        all_pages.append(mat_page)
    
    # Generate cut-out sorting cards
    print(f"Generating sorting cards (Level {level})...")
    
    current_page_cards = []
    page_number = len(all_pages) + 1  # Continue from mats
    
    # Collect all items from all categories
    all_items = []
    for category_name, items in categories.items():
        for item in items:
            item_with_category = item.copy() if isinstance(item, dict) else {'image': item}
            item_with_category['category'] = category_name
            all_items.append(item_with_category)
    
    # Generate cards
    for item in all_items:
        # Extract image and label
        if isinstance(item, dict):
            img_filename = item.get('image', '')
            label_text = item.get('label', '')
        else:
            img_filename = item
            label_text = ''
        
        # Ensure .png extension
        if img_filename and not img_filename.endswith('.png'):
            img_filename += '.png'
        
        # Generate card
        card = generate_sorting_card(
            image_filename=img_filename,
            label_text=label_text if level == 1 else None,
            card_size=card_size,
            folder_type=folder_type,
            card_type=card_type,
            level=level,
            card_style=card_style,
            mode=mode
        )
        
        current_page_cards.append(card)
        
        # Create page when we have enough cards
        if len(current_page_cards) >= cards_per_page:
            page = create_cards_page(current_page_cards, cards_per_page, 
                                    page_number, len(all_items) // cards_per_page + 1)
            all_pages.append(page)
            current_page_cards = []
            page_number += 1
    
    # Handle remaining cards
    if current_page_cards:
        page = create_cards_page(current_page_cards, cards_per_page, 
                                page_number, page_number)
        all_pages.append(page)
    
    # Save as PDF
    mode_suffix = f"_{mode}" if mode else ""
    output_filename = f"{theme_name}_Sorting_{level_name}{mode_suffix}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    save_images_as_pdf(all_pages, output_path)
    
    print(f"✓ Generated {output_path}")
    print(f"  - {len(categories)} sorting mats")
    print(f"  - {len(all_items)} sorting cards")
    print(f"  - {len(all_pages)} total pages")
    
    # Generate storage label if requested (color mode only)
    if include_storage_label and mode == 'color':
        try:
            # Try to get first image for icon
            first_item = all_items[0] if all_items else None
            icon_path = None
            
            if first_item:
                img_filename = first_item.get('image', '') if isinstance(first_item, dict) else first_item
                if img_filename and not img_filename.endswith('.png'):
                    img_filename += '.png'
                
                image_loader = get_image_loader()
                try:
                    icon_img = image_loader.load_image(img_filename, folder_type)
                    icon_path = f"/tmp/sorting_icon_{theme_name}.png"
                    icon_img.save(icon_path)
                except:
                    pass
            
            # Generate companion label
            create_companion_label(
                main_pdf_path=output_path,
                theme_name=theme_name,
                activity_name="Sorting Cards",
                level=level,
                icon_path=icon_path
            )
            
            print(f"✓ Generated storage label: {output_path.replace('.pdf', '_LABEL.pdf')}")
            
        except Exception as e:
            print(f"⚠ Warning: Could not generate storage label: {e}")
    
    return [output_path]


def create_cards_page(cards, cards_per_page, page_number, total_pages):
    """
    Create a page with multiple sorting cards arranged in a grid.
    
    Args:
        cards: List of card images
        cards_per_page: Target number of cards per page
        page_number: Current page number
        total_pages: Total number of pages
        
    Returns:
        PIL.Image: Page with arranged cards
    """
    # Create page canvas
    page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
    draw = ImageDraw.Draw(page)
    
    # Calculate grid layout
    if cards_per_page <= 4:
        rows, cols = 2, 2
    elif cards_per_page <= 6:
        rows, cols = 2, 3
    elif cards_per_page <= 9:
        rows, cols = 3, 3
    else:
        rows, cols = 3, 4
    
    # Calculate cell positions
    cells = calculate_cell_rect(
        PAGE_WIDTH, PAGE_HEIGHT,
        rows, cols,
        padding=20,
        margin=MARGINS['page'],
        footer_height=60
    )
    
    # Place cards in cells
    for i, card in enumerate(cards[:cards_per_page]):
        if i < len(cells):
            x1, y1, x2, y2 = cells[i]
            
            # Center card in cell
            card_x = x1 + (x2 - x1 - card.width) // 2
            card_y = y1 + (y2 - y1 - card.height) // 2
            
            # Paste card (handle RGBA)
            if card.mode == 'RGBA':
                page.paste(card, (card_x, card_y), card)
            else:
                page.paste(card, (card_x, card_y))
    
    # Add page number
    draw_page_number(draw, page_number, total_pages)
    
    # Add copyright footer
    draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
    
    return page


def generate_sorting_cards_dual_mode(categories, theme_name='Theme', level=1, 
                                     card_size='standard', cards_per_page=6,
                                     output_dir='output', include_storage_label=False,
                                     card_style=None):
    """
    Generate sorting cards in both color and black-and-white modes.
    
    Args:
        categories: Dict mapping category names to lists of items
        theme_name: Name of the theme for file naming
        level: Differentiation level (1-3)
        card_size: Size of sorting cards
        cards_per_page: Number of cards per page
        output_dir: Output directory for PDFs
        include_storage_label: Whether to generate storage label (color mode only)
        card_style: Optional styling dict for borders/shadows
        
    Returns:
        dict: Paths to generated PDFs {'color': path, 'bw': path}
    """
    paths = {}
    
    # Generate color version
    color_paths = generate_sorting_cards_set(
        categories=categories,
        theme_name=theme_name,
        level=level,
        card_size=card_size,
        cards_per_page=cards_per_page,
        output_dir=output_dir,
        include_storage_label=include_storage_label,
        card_style=card_style,
        mode='color'
    )
    paths['color'] = color_paths[0] if color_paths else None
    
    # Generate black-and-white version
    bw_paths = generate_sorting_cards_set(
        categories=categories,
        theme_name=theme_name,
        level=level,
        card_size=card_size,
        cards_per_page=cards_per_page,
        output_dir=output_dir,
        include_storage_label=False,  # No storage label for BW
        card_style=card_style,
        mode='bw'
    )
    paths['bw'] = bw_paths[0] if bw_paths else None
    
    return paths


# Example usage
if __name__ == '__main__':
    # Example categories for sorting
    example_categories = {
        'Animals': [
            {'image': 'bear', 'label': 'Bear'},
            {'image': 'duck', 'label': 'Duck'},
            {'image': 'frog', 'label': 'Frog'},
            {'image': 'cat', 'label': 'Cat'}
        ],
        'Colors': [
            {'image': 'bird', 'label': 'Red Bird'},
            {'image': 'duck', 'label': 'Yellow Duck'},
            {'image': 'frog', 'label': 'Green Frog'}
        ]
    }
    
    # Generate all three levels
    for level in range(1, 4):
        generate_sorting_cards_set(
            categories=example_categories,
            theme_name='Brown_Bear',
            level=level,
            cards_per_page=6,
            include_storage_label=True
        )
