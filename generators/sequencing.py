"""
Sequencing Cards Generator

Generates sequencing cards for teaching order and sequences.
Cards can be numbered or unnumbered based on differentiation level.
"""

from PIL import Image, ImageDraw
from utils.config import MARGINS, CARD_SIZES
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional
from utils.layout import create_card_background, create_page_canvas, add_page_border, add_footer
from utils.pdf_export import save_images_as_pdf


def generate_sequencing_card(image_filename, sequence_number=None, total_steps=None,
                             card_size='large', folder_type='color', level=1):
    """
    Generate a single sequencing card.
    
    Args:
        image_filename: Filename of the image
        sequence_number: Position in sequence (1, 2, 3...)
        total_steps: Total number of steps in sequence
        card_size: Card size
        folder_type: Image folder type
        level: Differentiation level (1=numbers shown, 2=no numbers, 3=more complex)
        
    Returns:
        PIL.Image: Generated card
    """
    width, height = CARD_SIZES[card_size]
    card = create_card_background(width, height, border=True)
    
    # Load image
    image_loader = get_image_loader()
    theme_image = image_loader.load_image(image_filename, folder_type)
    
    # Scale image
    image_height = height - 100 if level == 1 else height - 40
    scaled_image = scale_image_proportional(theme_image, max_width=width-40, max_height=image_height)
    
    # Center and place image
    img_x = (width - scaled_image.width) // 2
    img_y = 20
    card.paste(scaled_image, (img_x, img_y), scaled_image)
    
    # Add sequence number for Level 1
    if level == 1 and sequence_number:
        draw = ImageDraw.Draw(card)
        # Draw number circle at bottom
        circle_y = height - 70
        circle_x = width // 2
        circle_radius = 30
        
        draw.ellipse(
            [circle_x - circle_radius, circle_y - circle_radius,
             circle_x + circle_radius, circle_y + circle_radius],
            fill=(255, 255, 255, 255),
            outline=(0, 0, 0, 255),
            width=3
        )
        
        # Draw number
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
            text = str(sequence_number)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = circle_x - text_width // 2
            text_y = circle_y - text_height // 2
            draw.text((text_x, text_y), text, fill=(0, 0, 0, 255), font=font)
        except:
            pass
    
    return card


def generate_sequencing_set(image_sequence, theme_name='Sequence', card_size='large',
                            folder_type='color', level=1, output_dir='output'):
    """
    Generate a complete sequencing activity.
    
    Args:
        image_sequence: List of image filenames in order
        theme_name: Theme name
        card_size: Card size
        folder_type: Image folder type
        level: Differentiation level
        output_dir: Output directory
        
    Returns:
        list: Generated pages
    """
    total_steps = len(image_sequence)
    cards = []
    
    # Generate each card
    for idx, image_file in enumerate(image_sequence):
        card = generate_sequencing_card(
            image_file, idx + 1, total_steps, card_size, folder_type, level
        )
        cards.append(card)
    
    # Arrange cards on pages (4 per page)
    pages = []
    cards_per_page = 4
    width, height = CARD_SIZES[card_size]
    
    for page_start in range(0, len(cards), cards_per_page):
        page = create_page_canvas()
        page_cards = cards[page_start:page_start + cards_per_page]
        
        # 2x2 grid
        grid_cols, grid_rows = 2, 2
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
            
            page.paste(card, (int(x), int(y)), card)
        
        add_page_border(page)
        add_footer(page)
        pages.append(page)
    
    # Save PDF
    output_path = f"{output_dir}/{theme_name}_Sequencing_Level{level}.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Sequencing")
    
    return pages


if __name__ == "__main__":
    print("Sequencing Generator")
    print("Use generate_sequencing_card() or generate_sequencing_set()")
