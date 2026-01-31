"""
Matching Cards Generator

Generates SPED-friendly matching card pairs with 4 differentiation levels:
- Level 1: Identical errorless matching (same image on both cards)
- Level 2: Outline-to-color matching (outline matches to color image)
- Level 3: AAC symbol to real image matching
- Level 4: AAC symbol to text matching

All cards follow SPED design principles: large images, high contrast,
minimal clutter, consistent spacing, and 300 DPI output.
"""

from PIL import Image, ImageDraw, ImageFont
from utils.config import MARGINS, CARD_SIZES, DPI, COLORS, FONT_SIZES, PAGE_WIDTH, PAGE_HEIGHT
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional, center_image_in_box
from utils.layout import create_card_background, add_page_border, add_footer, create_page_canvas
from utils.grid_layout import create_grid_positions, calculate_grid_dimensions
from utils.pdf_export import save_images_as_pdf
from utils.fonts import get_font_manager
import os


def generate_matching_card(image_filename, label_text=None, card_size='large',
                           folder_type='color', card_type='image', level=1, 
                           add_drop_shadow=False, label_font_size=None):
    """
    Generate a single matching card with enhanced layout consistency.
    
    Args:
        image_filename: Filename of the image (without folder path)
        label_text: Text label for the card
        card_size: 'standard', 'large', 'rectangle', or 'wide'
        folder_type: 'color', 'bw_outline', or 'aac'
        card_type: 'image' or 'text' (for Level 4)
        level: Differentiation level (1-4)
        add_drop_shadow: If True, add subtle drop shadow to card border
        label_font_size: Consistent font size for labels (defaults to FONT_SIZES['body'])
        
    Returns:
        PIL.Image: Generated card
    """
    # Get card dimensions
    width, height = CARD_SIZES[card_size]
    
    # Set consistent label font size
    if label_font_size is None:
        label_font_size = FONT_SIZES['body']
    
    # Create card background with border
    card = create_card_background(width, height, border=True)
    
    # Optional: Add drop shadow effect
    if add_drop_shadow:
        shadow_card = Image.new('RGBA', (width + 10, height + 10), (0, 0, 0, 0))
        draw_shadow = ImageDraw.Draw(shadow_card)
        # Draw subtle shadow
        for i in range(5):
            alpha = 30 - (i * 5)
            draw_shadow.rectangle(
                [5 + i, 5 + i, width + 5 - i, height + 5 - i],
                outline=(0, 0, 0, alpha)
            )
        # Composite shadow with card
        shadow_card.paste(card, (0, 0), card)
        card = shadow_card.crop((0, 0, width, height))
    
    if card_type == 'text':
        # Level 4: Text-only card with consistent font sizing
        draw = ImageDraw.Draw(card)
        
        # Get text content
        text = label_text if label_text else image_filename.replace('.png', '').replace('_', ' ').title()
        
        # Use default font (simpler approach for better compatibility)
        try:
            # Try to load a basic font
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=int(label_font_size))
        except:
            # Fallback to default if truetype not available
            font = ImageFont.load_default()
        
        # Draw text centered in card
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2
        draw.text((text_x, text_y), text, fill=COLORS['black'] + (255,), font=font)
        
        return card
    
    # Image-based card (Levels 1-3)
    image_loader = get_image_loader()
    
    try:
        theme_image = image_loader.load_image(image_filename, folder_type)
    except FileNotFoundError:
        # If image not found, create a consistent placeholder
        theme_image = Image.new('RGBA', (500, 500), (200, 200, 200, 255))
        draw = ImageDraw.Draw(theme_image)
        draw.rectangle([50, 50, 450, 450], outline=(100, 100, 100, 255), width=5)
        
        # Use default font for placeholder text (simpler approach)
        draw.text((100, 230), f"Missing:\n{image_filename}", 
                 fill=(100, 100, 100, 255))
    
    # Calculate image area with minimal padding (maximize image size)
    # Use smaller padding (10px instead of MARGINS['card']) for larger images
    minimal_padding = 10
    image_width = width - (minimal_padding * 2)
    image_height = height - (minimal_padding * 2)
    
    # Scale image proportionally
    scaled_image = scale_image_proportional(theme_image, max_width=image_width, max_height=image_height)
    
    # Center image in card using precise calculation
    img_x = (width - scaled_image.width) // 2
    img_y = (height - scaled_image.height) // 2
    
    # Paste with alpha channel support
    card.paste(scaled_image, (img_x, img_y), scaled_image)
    
    return card


def generate_matching_pair(image_base_name, label_text=None, level=1, card_size='large',
                          add_drop_shadow=False, label_font_size=None):
    """
    Generate a matching pair of cards based on differentiation level.
    
    Args:
        image_base_name: Base name of the image (e.g., 'bear')
        label_text: Text label for the item
        level: Differentiation level (1-4)
        card_size: Card size
        add_drop_shadow: If True, add drop shadow to cards
        label_font_size: Consistent font size for labels
        
    Returns:
        tuple: (card_a, card_b) - Two matching cards
    """
    if level == 1:
        # Level 1: Identical errorless matching (same color image on both cards)
        card_a = generate_matching_card(
            f"{image_base_name}.png",
            label_text,
            card_size,
            folder_type='color',
            card_type='image',
            level=level,
            add_drop_shadow=add_drop_shadow,
            label_font_size=label_font_size
        )
        card_b = card_a.copy()  # Identical card
        
    elif level == 2:
        # Level 2: Outline-to-color matching
        card_a = generate_matching_card(
            f"{image_base_name}.png",
            label_text,
            card_size,
            folder_type='bw_outline',  # Outline version
            card_type='image',
            level=level,
            add_drop_shadow=add_drop_shadow,
            label_font_size=label_font_size
        )
        card_b = generate_matching_card(
            f"{image_base_name}.png",
            label_text,
            card_size,
            folder_type='color',  # Color version
            card_type='image',
            level=level,
            add_drop_shadow=add_drop_shadow,
            label_font_size=label_font_size
        )
        
    elif level == 3:
        # Level 3: AAC symbol to real image matching
        card_a = generate_matching_card(
            f"{image_base_name}.png",
            label_text,
            card_size,
            folder_type='aac',  # AAC symbol
            card_type='image',
            level=level,
            add_drop_shadow=add_drop_shadow,
            label_font_size=label_font_size
        )
        card_b = generate_matching_card(
            f"{image_base_name}.png",
            label_text,
            card_size,
            folder_type='color',  # Real image
            card_type='image',
            level=level,
            add_drop_shadow=add_drop_shadow,
            label_font_size=label_font_size
        )
        
    elif level == 4:
        # Level 4: AAC symbol to text matching
        card_a = generate_matching_card(
            f"{image_base_name}.png",
            label_text,
            card_size,
            folder_type='aac',  # AAC symbol
            card_type='image',
            level=level,
            add_drop_shadow=add_drop_shadow,
            label_font_size=label_font_size
        )
        card_b = generate_matching_card(
            f"{image_base_name}.png",
            label_text,
            card_size,
            folder_type='color',  # Not used for text card
            card_type='text',  # Text card
            level=level,
            add_drop_shadow=add_drop_shadow,
            label_font_size=label_font_size
        )
    else:
        raise ValueError(f"Invalid level: {level}. Must be 1-4.")
    
    return (card_a, card_b)


def generate_matching_cards_set(items, level=1, card_size='large', 
                                 cards_per_page=6, output_dir='output', theme_name='Theme',
                                 include_storage_label=False, add_drop_shadow=False,
                                 custom_spacing=None, custom_margins=None):
    """
    Generate a complete set of matching cards at the specified difficulty level
    with enhanced layout consistency.
    
    Args:
        items: List of dicts with 'image' (base name) and 'label' keys
               e.g., [{'image': 'bear', 'label': 'Brown Bear'}, ...]
        level: Differentiation level (1-4)
        card_size: Size of cards
        cards_per_page: Number of cards per page (6, 8, or 9)
        output_dir: Output directory
        theme_name: Theme name for filename
        include_storage_label: If True, also generate a companion storage label PDF
        add_drop_shadow: If True, add subtle drop shadow to card borders
        custom_spacing: Custom spacing between cards (uses MARGINS['content'] if None)
        custom_margins: Custom page margins dict (uses MARGINS if None)
        
    Returns:
        list: List of generated pages
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Use configuration margins or custom ones
    margins = custom_margins if custom_margins else MARGINS
    spacing = custom_spacing if custom_spacing is not None else margins['content']
    
    # Consistent label font size across all cards
    label_font_size = FONT_SIZES['body']
    
    # Generate all card pairs
    all_cards = []
    for item in items:
        card_a, card_b = generate_matching_pair(
            item['image'],
            item.get('label'),
            level,
            card_size,
            add_drop_shadow=add_drop_shadow,
            label_font_size=label_font_size
        )
        all_cards.append(card_a)
        all_cards.append(card_b)
    
    # Determine optimal grid layout based on cards_per_page
    if cards_per_page == 6:
        grid_cols, grid_rows = 2, 3
    elif cards_per_page == 8:
        grid_cols, grid_rows = 2, 4
    elif cards_per_page == 9:
        grid_cols, grid_rows = 3, 3
    elif cards_per_page == 4:
        grid_cols, grid_rows = 2, 2
    else:
        # Auto-calculate grid dimensions for other values
        grid_cols, grid_rows = calculate_grid_dimensions(cards_per_page, max_cols=3)
    
    # Arrange cards on pages using grid layout utility
    pages = []
    card_width, card_height = CARD_SIZES[card_size]
    
    for page_start in range(0, len(all_cards), cards_per_page):
        page_cards = all_cards[page_start:page_start + cards_per_page]
        
        # Create page with proper background
        page = create_page_canvas()
        
        # Calculate available space for grid (accounting for page margins and footer)
        available_width = int(PAGE_WIDTH) - (margins['page'] * 2)
        available_height = int(PAGE_HEIGHT) - (margins['page'] * 2) - 100  # Reserve space for footer
        
        # Use grid layout utility to calculate positions
        grid_positions = create_grid_positions(
            cols=grid_cols,
            rows=grid_rows,
            cell_width=card_width,
            cell_height=card_height,
            spacing=spacing,
            container_width=available_width,
            container_height=available_height
        )
        
        # Adjust positions to account for page margins
        grid_positions = [(x + margins['page'], y + margins['page']) for x, y in grid_positions]
        
        # Place cards on page using calculated grid positions
        for idx, card in enumerate(page_cards):
            if idx < len(grid_positions):
                x, y = grid_positions[idx]
                page.paste(card, (int(x), int(y)), card)
        
        # Add consistent border and footer
        add_page_border(page)
        add_footer(page)
        
        pages.append(page)
    
    # Save as PDF with descriptive filename
    level_descriptions = {
        1: "Identical_Errorless",
        2: "Outline_to_Color",
        3: "AAC_to_Real_Image",
        4: "AAC_to_Text"
    }
    output_path = f"{output_dir}/{theme_name}_Matching_Level{level}_{level_descriptions[level]}.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Matching Cards - Level {level}")
    
    print(f"✓ Generated {len(pages)} pages with {len(all_cards)} cards")
    print(f"  Layout: {grid_cols}×{grid_rows} grid with {spacing}px spacing")
    print(f"  Output: {output_path}")
    
    # Generate storage label if requested
    if include_storage_label:
        from utils.storage_label_helper import create_companion_label
        
        # Try to get first image as icon
        icon_path = None
        if items:
            first_image = items[0]['image']
            # Try to find the image in the images folder
            potential_icon = f"images/{first_image}.png"
            if os.path.exists(potential_icon):
                icon_path = potential_icon
        
        label_path = create_companion_label(
            main_pdf_path=output_path,
            theme_name=theme_name,
            activity_name="Matching Cards",
            level=level,
            icon_path=icon_path
        )
        print(f"✓ Generated storage label")
        print(f"  Label: {label_path}")
    
    return pages


if __name__ == "__main__":
    print("Matching Cards Generator - 4 Differentiation Levels")
    print()
    print("Level 1: Identical errorless matching")
    print("Level 2: Outline-to-color matching")
    print("Level 3: AAC symbol to real image matching")
    print("Level 4: AAC symbol to text matching")
    print()
    print("Example usage:")
    print("""
from generators.matching_cards import generate_matching_cards_set

items = [
    {'image': 'bear', 'label': 'Brown Bear'},
    {'image': 'duck', 'label': 'Yellow Duck'},
    {'image': 'frog', 'label': 'Green Frog'},
]

# Generate Level 1 (identical matching)
pages = generate_matching_cards_set(items, level=1, theme_name='Brown Bear')
""")
