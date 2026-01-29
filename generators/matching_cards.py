"""
Matching Cards Generator

Generates matching card pairs for memory games and matching activities.
Each card features a theme image with optional text label.
"""

from PIL import Image, ImageDraw
from utils.config import MARGINS, CARD_SIZES, DPI
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional, center_image_in_box, create_grid_layout
from utils.layout import create_card_background, add_page_border, add_footer, create_page_canvas
from utils.pdf_export import save_images_as_pdf


def generate_matching_card(image_filename, label_text=None, card_size='standard',
                           folder_type='color', level=1):
    """
    Generate a single matching card.
    
    Args:
        image_filename: Filename of the theme image
        label_text: Optional text label for the card
        card_size: 'standard', 'large', 'rectangle', or 'wide'
        folder_type: 'color', 'bw_outline', or 'aac'
        level: Differentiation level (affects whether text is shown)
        
    Returns:
        PIL.Image: Generated card
    """
    # Get card dimensions
    width, height = CARD_SIZES[card_size]
    
    # Create card background with border
    card = create_card_background(width, height, border=True)
    
    # Load and scale image
    image_loader = get_image_loader()
    theme_image = image_loader.load_image(image_filename, folder_type)
    
    # Calculate image area (leave space for label if level 1)
    if level == 1 and label_text:
        image_height = int(height * 0.75)
        label_height = int(height * 0.25)
    else:
        image_height = height - (MARGINS['card'] * 2)
        label_height = 0
    
    image_width = width - (MARGINS['card'] * 2)
    
    # Scale image proportionally
    scaled_image = scale_image_proportional(theme_image, max_width=image_width, max_height=image_height)
    
    # Center image in card
    img_x = (width - scaled_image.width) // 2
    img_y = MARGINS['card']
    
    card.paste(scaled_image, (img_x, img_y), scaled_image)
    
    # Add label for Level 1
    if level == 1 and label_text:
        draw = ImageDraw.Draw(card)
        label_y = img_y + image_height + 10
        # Simplified text rendering
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (width - text_width) // 2
            draw.text((text_x, label_y), label_text, fill=(0, 0, 0, 255), font=font)
        except:
            pass
    
    return card


def generate_matching_cards_sheet(image_label_pairs, cards_per_page=9, card_size='standard',
                                   folder_type='color', level=1, output_dir='output', theme_name='Theme'):
    """
    Generate sheets of matching cards (each card appears twice for matching).
    
    Args:
        image_label_pairs: List of tuples (image_filename, label_text)
        cards_per_page: Number of cards per page (6, 8, or 9 recommended)
        card_size: Size of cards
        folder_type: Image folder type
        level: Differentiation level
        output_dir: Output directory
        theme_name: Theme name for filename
        
    Returns:
        list: List of generated pages
    """
    # Generate pairs of cards
    cards = []
    for image_file, label in image_label_pairs:
        # Create two identical cards for matching
        card = generate_matching_card(image_file, label, card_size, folder_type, level)
        cards.append(card)
        cards.append(card.copy())
    
    # Arrange cards on pages
    pages = []
    
    # Determine grid layout based on cards_per_page
    if cards_per_page == 6:
        grid_cols, grid_rows = 2, 3
    elif cards_per_page == 8:
        grid_cols, grid_rows = 2, 4
    elif cards_per_page == 9:
        grid_cols, grid_rows = 3, 3
    else:
        grid_cols, grid_rows = 3, 3
    
    # Create pages
    for page_start in range(0, len(cards), cards_per_page):
        page_cards = cards[page_start:page_start + cards_per_page]
        
        # Create page
        page = create_page_canvas()
        
        # Calculate card placement
        card_width, card_height = CARD_SIZES[card_size]
        spacing = MARGINS['content']
        
        total_grid_width = (card_width * grid_cols) + (spacing * (grid_cols - 1))
        total_grid_height = (card_height * grid_rows) + (spacing * (grid_rows - 1))
        
        start_x = (int(page.width) - total_grid_width) // 2
        start_y = (int(page.height) - total_grid_height - 200) // 2
        
        # Place cards
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
    output_path = f"{output_dir}/{theme_name}_Matching_Cards_Level{level}.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Matching Cards")
    
    return pages


if __name__ == "__main__":
    print("Matching Cards Generator")
    print("Use generate_matching_card() or generate_matching_cards_sheet() in your code")
