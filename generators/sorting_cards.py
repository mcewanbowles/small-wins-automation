"""
Sorting Cards Generator

Generates sorting cards for categorization activities.
Cards can be sorted by category, attribute, or other criteria.
"""

from PIL import Image, ImageDraw
from utils.config import MARGINS, CARD_SIZES
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional
from utils.layout import create_card_background, create_page_canvas, add_page_border, add_footer
from utils.pdf_export import save_images_as_pdf


def generate_sorting_card(image_filename, category=None, card_size='standard',
                          folder_type='color', level=1):
    """
    Generate a single sorting card.
    
    Args:
        image_filename: Filename of the image
        category: Category label (shown only at Level 1)
        card_size: Card size
        folder_type: Image folder type
        level: Differentiation level
        
    Returns:
        PIL.Image: Generated card
    """
    width, height = CARD_SIZES[card_size]
    card = create_card_background(width, height, border=True)
    
    # Load image
    image_loader = get_image_loader()
    theme_image = image_loader.load_image(image_filename, folder_type)
    
    # Calculate image area
    if level == 1 and category:
        image_height = int(height * 0.8)
    else:
        image_height = height - 40
    
    scaled_image = scale_image_proportional(theme_image, max_width=width-40, max_height=image_height)
    
    # Center and place image
    img_x = (width - scaled_image.width) // 2
    img_y = 20
    card.paste(scaled_image, (img_x, img_y), scaled_image)
    
    # Add category label for Level 1
    if level == 1 and category:
        draw = ImageDraw.Draw(card)
        label_y = height - 100
        
        # Draw label area
        draw.rectangle(
            [10, label_y, width-10, height-10],
            fill=(240, 240, 240, 255),
            outline=(0, 0, 0, 255),
            width=2
        )
        
        # Draw text
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), category, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (width - text_width) // 2
            text_y = label_y + 20
            draw.text((text_x, text_y), category, fill=(0, 0, 0, 255), font=font)
        except:
            pass
    
    return card


def generate_category_header_card(category_name, card_size='large'):
    """
    Generate a category header card for sorting mats.
    
    Args:
        category_name: Name of the category
        card_size: Card size
        
    Returns:
        PIL.Image: Generated header card
    """
    width, height = CARD_SIZES[card_size]
    card = create_card_background(width, height, border=True, border_width=8)
    
    draw = ImageDraw.Draw(card)
    
    # Fill with light background
    draw.rectangle([8, 8, width-8, height-8], fill=(220, 220, 255, 255))
    
    # Draw category name
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), category_name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2
        draw.text((text_x, text_y), category_name, fill=(0, 0, 0, 255), font=font)
    except:
        pass
    
    return card


def generate_sorting_cards_set(categories_dict, card_size='standard', folder_type='color',
                                level=1, theme_name='Theme', output_dir='output'):
    """
    Generate a complete set of sorting cards with category headers.
    
    Args:
        categories_dict: Dict of {category_name: [image_filenames]}
        card_size: Card size
        folder_type: Image folder type
        level: Differentiation level
        theme_name: Theme name
        output_dir: Output directory
        
    Returns:
        list: Generated pages
    """
    all_cards = []
    
    # Generate header cards and sorting cards for each category
    for category, images in categories_dict.items():
        # Add category header
        header = generate_category_header_card(category, 'large')
        all_cards.append(header)
        
        # Add sorting cards
        for image_file in images:
            card = generate_sorting_card(image_file, category, card_size, folder_type, level)
            all_cards.append(card)
    
    # Arrange cards on pages (9 per page in 3x3 grid)
    pages = []
    cards_per_page = 9
    width, height = CARD_SIZES[card_size]
    
    for page_start in range(0, len(all_cards), cards_per_page):
        page = create_page_canvas()
        page_cards = all_cards[page_start:page_start + cards_per_page]
        
        grid_cols, grid_rows = 3, 3
        spacing = MARGINS['content']
        
        total_width = (width * grid_cols) + (spacing * (grid_cols - 1))
        total_height = (height * grid_rows) + (spacing * (grid_rows - 1))
        
        start_x = (int(page.width) - total_width) // 2
        start_y = (int(page.height) - total_height - 200) // 2
        
        for idx, card in enumerate(page_cards):
            row = idx // grid_cols
            col = idx % grid_cols
            
            x = start_x + (col * (width + spacing))
            y = start_y + (row * (height + spacing))
            
            # Scale card if it's a header (larger)
            if card.size != (width, height):
                card_to_paste = card.resize((width, height), Image.Resampling.LANCZOS)
            else:
                card_to_paste = card
            
            page.paste(card_to_paste, (int(x), int(y)), card_to_paste)
        
        add_page_border(page)
        add_footer(page)
        pages.append(page)
    
    # Save PDF
    output_path = f"{output_dir}/{theme_name}_Sorting_Cards_Level{level}.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Sorting Cards")
    
    return pages


if __name__ == "__main__":
    print("Sorting Cards Generator")
    print("Use generate_sorting_card() or generate_sorting_cards_set()")
