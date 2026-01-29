"""
Bingo Generator

Generates bingo cards with theme images in a 3x3, 4x4, or 5x5 grid.
Includes calling cards for the teacher.
"""

from PIL import Image, ImageDraw
from utils.config import MARGINS, DPI, PAGE_WIDTH, PAGE_HEIGHT
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional, center_image_in_box
from utils.layout import create_page_canvas, add_page_border, add_footer, add_title_to_page
from utils.pdf_export import save_images_as_pdf
import random


def generate_bingo_card(image_filenames, grid_size=3, folder_type='color',
                        theme_name='Theme', free_space=True):
    """
    Generate a single bingo card.
    
    Args:
        image_filenames: List of image filenames to use
        grid_size: Size of grid (3, 4, or 5)
        folder_type: Image folder type
        theme_name: Theme name
        free_space: Whether to include a FREE space in center
        
    Returns:
        PIL.Image: Generated bingo card
    """
    # Create page
    page = create_page_canvas()
    
    # Add title
    add_title_to_page(page, f"{theme_name} Bingo")
    
    # Calculate cell size
    available_width = PAGE_WIDTH - (MARGINS['page'] * 2)
    available_height = PAGE_HEIGHT - (MARGINS['page'] * 3) - 300  # Space for title and footer
    
    cell_spacing = 10
    cell_size = min(
        (available_width - (cell_spacing * (grid_size - 1))) // grid_size,
        (available_height - (cell_spacing * (grid_size - 1))) // grid_size
    )
    
    # Calculate starting position
    total_size = (cell_size * grid_size) + (cell_spacing * (grid_size - 1))
    start_x = (PAGE_WIDTH - total_size) // 2
    start_y = 250
    
    # Shuffle images for randomization
    selected_images = random.sample(image_filenames, min(len(image_filenames), grid_size * grid_size))
    
    # Load image loader
    image_loader = get_image_loader()
    
    # Draw grid
    draw = ImageDraw.Draw(page)
    idx = 0
    
    for row in range(grid_size):
        for col in range(grid_size):
            x = start_x + (col * (cell_size + cell_spacing))
            y = start_y + (row * (cell_size + cell_spacing))
            
            # Draw cell border
            draw.rectangle(
                [x, y, x + cell_size, y + cell_size],
                outline=(0, 0, 0, 255),
                width=3
            )
            
            # Check if this is the center free space
            is_free_space = free_space and row == grid_size // 2 and col == grid_size // 2
            
            if is_free_space:
                # Draw "FREE" text
                try:
                    from PIL import ImageFont
                    font = ImageFont.load_default()
                    text = "FREE"
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    text_x = x + (cell_size - text_width) // 2
                    text_y = y + (cell_size - text_height) // 2
                    draw.text((text_x, text_y), text, fill=(0, 0, 0, 255), font=font)
                except:
                    pass
            else:
                # Load and place image
                if idx < len(selected_images):
                    theme_image = image_loader.load_image(selected_images[idx], folder_type)
                    scaled_image = scale_image_proportional(
                        theme_image, 
                        max_width=cell_size - 20, 
                        max_height=cell_size - 20
                    )
                    
                    # Center image in cell
                    img_x = x + (cell_size - scaled_image.width) // 2
                    img_y = y + (cell_size - scaled_image.height) // 2
                    
                    page.paste(scaled_image, (int(img_x), int(img_y)), scaled_image)
                    idx += 1
    
    # Add border and footer
    add_page_border(page)
    add_footer(page)
    
    return page


def generate_bingo_calling_cards(image_filenames, folder_type='color', theme_name='Theme'):
    """
    Generate calling cards for the teacher to use with bingo.
    
    Args:
        image_filenames: List of image filenames
        folder_type: Image folder type
        theme_name: Theme name
        
    Returns:
        list: List of pages with calling cards
    """
    pages = []
    image_loader = get_image_loader()
    
    # 6 calling cards per page (2 cols x 3 rows)
    cards_per_page = 6
    card_width = 900
    card_height = 600
    
    for page_start in range(0, len(image_filenames), cards_per_page):
        page = create_page_canvas()
        page_images = image_filenames[page_start:page_start + cards_per_page]
        
        # Grid layout: 2 columns, 3 rows
        grid_cols, grid_rows = 2, 3
        spacing = MARGINS['content']
        
        total_width = (card_width * grid_cols) + (spacing * (grid_cols - 1))
        total_height = (card_height * grid_rows) + (spacing * (grid_rows - 1))
        
        start_x = (PAGE_WIDTH - total_width) // 2
        start_y = (PAGE_HEIGHT - total_height - 200) // 2
        
        draw = ImageDraw.Draw(page)
        
        for idx, image_file in enumerate(page_images):
            row = idx // grid_cols
            col = idx % grid_cols
            
            x = start_x + (col * (card_width + spacing))
            y = start_y + (row * (card_height + spacing))
            
            # Draw card border
            draw.rectangle(
                [x, y, x + card_width, y + card_height],
                outline=(0, 0, 0, 255),
                width=5
            )
            
            # Load and place image
            theme_image = image_loader.load_image(image_file, folder_type)
            scaled_image = scale_image_proportional(
                theme_image,
                max_width=card_width - 40,
                max_height=card_height - 40
            )
            
            img_x = x + (card_width - scaled_image.width) // 2
            img_y = y + (card_height - scaled_image.height) // 2
            
            page.paste(scaled_image, (int(img_x), int(img_y)), scaled_image)
        
        add_page_border(page)
        add_footer(page)
        pages.append(page)
    
    return pages


def generate_bingo_set(image_filenames, num_cards=6, grid_size=3, folder_type='color',
                       theme_name='Theme', output_dir='output'):
    """
    Generate a complete bingo set with multiple unique cards and calling cards.
    
    Args:
        image_filenames: List of image filenames
        num_cards: Number of unique bingo cards to generate
        grid_size: Grid size (3, 4, or 5)
        folder_type: Image folder type
        theme_name: Theme name
        output_dir: Output directory
        
    Returns:
        list: All generated pages
    """
    all_pages = []
    
    # Generate bingo cards
    for i in range(num_cards):
        card = generate_bingo_card(image_filenames, grid_size, folder_type, theme_name)
        all_pages.append(card)
    
    # Generate calling cards
    calling_cards = generate_bingo_calling_cards(image_filenames, folder_type, theme_name)
    all_pages.extend(calling_cards)
    
    # Save as PDF
    output_path = f"{output_dir}/{theme_name}_Bingo_{grid_size}x{grid_size}.pdf"
    save_images_as_pdf(all_pages, output_path, title=f"{theme_name} Bingo")
    
    return all_pages


if __name__ == "__main__":
    print("Bingo Generator")
    print("Use generate_bingo_card(), generate_bingo_calling_cards(), or generate_bingo_set()")
