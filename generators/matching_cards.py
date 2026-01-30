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
from utils.config import MARGINS, CARD_SIZES, DPI, COLORS
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional, center_image_in_box
from utils.layout import create_card_background, add_page_border, add_footer, create_page_canvas
from utils.pdf_export import save_images_as_pdf
import os


def generate_matching_card(image_filename, label_text=None, card_size='large',
                           folder_type='color', card_type='image', level=1):
    """
    Generate a single matching card.
    
    Args:
        image_filename: Filename of the image (without folder path)
        label_text: Text label for the card
        card_size: 'standard', 'large', 'rectangle', or 'wide'
        folder_type: 'color', 'bw_outline', or 'aac'
        card_type: 'image' or 'text' (for Level 4)
        level: Differentiation level (1-4)
        
    Returns:
        PIL.Image: Generated card
    """
    # Get card dimensions
    width, height = CARD_SIZES[card_size]
    
    # Create card background with border
    card = create_card_background(width, height, border=True)
    
    if card_type == 'text':
        # Level 4: Text-only card
        draw = ImageDraw.Draw(card)
        try:
            # Use default font for now (can be enhanced with custom fonts)
            font = ImageFont.load_default()
            
            # Draw text in center of card
            text = label_text if label_text else image_filename.replace('.png', '').replace('_', ' ').title()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = (width - text_width) // 2
            text_y = (height - text_height) // 2
            draw.text((text_x, text_y), text, fill=COLORS['black'] + (255,), font=font)
        except Exception as e:
            # Fallback if font loading fails
            pass
        
        return card
    
    # Image-based card (Levels 1-3)
    image_loader = get_image_loader()
    
    try:
        theme_image = image_loader.load_image(image_filename, folder_type)
    except FileNotFoundError:
        # If image not found, create a placeholder
        theme_image = Image.new('RGBA', (500, 500), (200, 200, 200, 255))
        draw = ImageDraw.Draw(theme_image)
        draw.rectangle([50, 50, 450, 450], outline=(100, 100, 100, 255), width=5)
        draw.text((100, 230), f"Missing:\n{image_filename}", fill=(100, 100, 100, 255))
    
    # Calculate image area
    image_width = width - (MARGINS['card'] * 2)
    image_height = height - (MARGINS['card'] * 2)
    
    # Scale image proportionally
    scaled_image = scale_image_proportional(theme_image, max_width=image_width, max_height=image_height)
    
    # Center image in card
    img_x = (width - scaled_image.width) // 2
    img_y = (height - scaled_image.height) // 2
    
    card.paste(scaled_image, (img_x, img_y), scaled_image)
    
    return card


def generate_matching_pair(image_base_name, label_text=None, level=1, card_size='large'):
    """
    Generate a matching pair of cards based on differentiation level.
    
    Args:
        image_base_name: Base name of the image (e.g., 'bear')
        label_text: Text label for the item
        level: Differentiation level (1-4)
        card_size: Card size
        
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
            level=level
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
            level=level
        )
        card_b = generate_matching_card(
            f"{image_base_name}.png",
            label_text,
            card_size,
            folder_type='color',  # Color version
            card_type='image',
            level=level
        )
        
    elif level == 3:
        # Level 3: AAC symbol to real image matching
        card_a = generate_matching_card(
            f"{image_base_name}.png",
            label_text,
            card_size,
            folder_type='aac',  # AAC symbol
            card_type='image',
            level=level
        )
        card_b = generate_matching_card(
            f"{image_base_name}.png",
            label_text,
            card_size,
            folder_type='color',  # Real image
            card_type='image',
            level=level
        )
        
    elif level == 4:
        # Level 4: AAC symbol to text matching
        card_a = generate_matching_card(
            f"{image_base_name}.png",
            label_text,
            card_size,
            folder_type='aac',  # AAC symbol
            card_type='image',
            level=level
        )
        card_b = generate_matching_card(
            f"{image_base_name}.png",
            label_text,
            card_size,
            folder_type='color',  # Not used for text card
            card_type='text',  # Text card
            level=level
        )
    else:
        raise ValueError(f"Invalid level: {level}. Must be 1-4.")
    
    return (card_a, card_b)


def generate_matching_cards_set(items, level=1, card_size='large', 
                                 cards_per_page=6, output_dir='output', theme_name='Theme'):
    """
    Generate a complete set of matching cards at the specified difficulty level.
    
    Args:
        items: List of dicts with 'image' (base name) and 'label' keys
               e.g., [{'image': 'bear', 'label': 'Brown Bear'}, ...]
        level: Differentiation level (1-4)
        card_size: Size of cards
        cards_per_page: Number of cards per page (6, 8, or 9)
        output_dir: Output directory
        theme_name: Theme name for filename
        
    Returns:
        list: List of generated pages
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate all card pairs
    all_cards = []
    for item in items:
        card_a, card_b = generate_matching_pair(
            item['image'],
            item.get('label'),
            level,
            card_size
        )
        all_cards.append(card_a)
        all_cards.append(card_b)
    
    # Determine grid layout based on cards_per_page
    if cards_per_page == 6:
        grid_cols, grid_rows = 2, 3
    elif cards_per_page == 8:
        grid_cols, grid_rows = 2, 4
    elif cards_per_page == 9:
        grid_cols, grid_rows = 3, 3
    else:
        grid_cols, grid_rows = 2, 3
    
    # Arrange cards on pages
    pages = []
    card_width, card_height = CARD_SIZES[card_size]
    
    for page_start in range(0, len(all_cards), cards_per_page):
        page_cards = all_cards[page_start:page_start + cards_per_page]
        
        # Create page
        page = create_page_canvas()
        
        # Calculate card placement
        spacing = MARGINS['content']
        
        total_grid_width = (card_width * grid_cols) + (spacing * (grid_cols - 1))
        total_grid_height = (card_height * grid_rows) + (spacing * (grid_rows - 1))
        
        start_x = (int(page.width) - total_grid_width) // 2
        start_y = (int(page.height) - total_grid_height - 200) // 2
        
        # Place cards on page
        for idx, card in enumerate(page_cards):
            row = idx // grid_cols
            col = idx % grid_cols
            
            x = start_x + (col * (card_width + spacing))
            y = start_y + (row * (card_height + spacing))
            
            page.paste(card, (int(x), int(y)), card)
        
        # Add border and footer
        add_page_border(page)
        add_footer(page)
        
        pages.append(page)
    
    # Save as PDF
    level_descriptions = {
        1: "Identical_Errorless",
        2: "Outline_to_Color",
        3: "AAC_to_Real_Image",
        4: "AAC_to_Text"
    }
    output_path = f"{output_dir}/{theme_name}_Matching_Level{level}_{level_descriptions[level]}.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Matching Cards - Level {level}")
    
    print(f"✓ Generated {len(pages)} pages with {len(all_cards)} cards")
    print(f"  Output: {output_path}")
    
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
