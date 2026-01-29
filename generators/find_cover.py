"""
Find & Cover Generator

Generates "Find and Cover" activity sheets where students find and cover
matching images using tokens or counters.
"""

from PIL import Image, ImageDraw
from utils.config import MARGINS, DPI, PAGE_WIDTH, PAGE_HEIGHT
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional
from utils.layout import create_page_canvas, add_page_border, add_footer, add_title_to_page
from utils.pdf_export import save_images_as_pdf
import random


def generate_find_cover_sheet(target_images, grid_images, theme_name='Theme',
                               grid_size=4, folder_type='color'):
    """
    Generate a Find & Cover activity sheet.
    
    Args:
        target_images: List of 3-5 target images to find
        grid_images: List of images to place in grid (includes targets + extras)
        theme_name: Theme name
        grid_size: Size of search grid (4x4, 5x5, etc.)
        folder_type: Image folder type
        
    Returns:
        PIL.Image: Generated activity sheet
    """
    page = create_page_canvas()
    
    # Add title
    add_title_to_page(page, f"Find and Cover: {theme_name}")
    
    # Draw target images at top (images to find)
    target_y = 200
    target_size = 200
    target_spacing = 30
    
    total_target_width = (target_size * len(target_images)) + (target_spacing * (len(target_images) - 1))
    target_start_x = (PAGE_WIDTH - total_target_width) // 2
    
    image_loader = get_image_loader()
    draw = ImageDraw.Draw(page)
    
    for idx, target_img in enumerate(target_images):
        x = target_start_x + (idx * (target_size + target_spacing))
        
        # Draw box for target
        draw.rectangle(
            [x, target_y, x + target_size, target_y + target_size],
            outline=(0, 0, 0, 255),
            width=5
        )
        
        # Load and place target image
        theme_image = image_loader.load_image(target_img, folder_type)
        scaled_image = scale_image_proportional(theme_image, max_width=target_size-20, max_height=target_size-20)
        
        img_x = x + (target_size - scaled_image.width) // 2
        img_y = target_y + (target_size - scaled_image.height) // 2
        
        page.paste(scaled_image, (int(img_x), int(img_y)), scaled_image)
    
    # Create search grid below
    grid_start_y = target_y + target_size + 100
    available_width = PAGE_WIDTH - (MARGINS['page'] * 2)
    available_height = PAGE_HEIGHT - grid_start_y - 200
    
    cell_spacing = 15
    cell_size = min(
        (available_width - (cell_spacing * (grid_size - 1))) // grid_size,
        (available_height - (cell_spacing * (grid_size - 1))) // grid_size
    )
    
    total_grid_size = (cell_size * grid_size) + (cell_spacing * (grid_size - 1))
    grid_start_x = (PAGE_WIDTH - total_grid_size) // 2
    
    # Shuffle grid images
    shuffled_images = grid_images.copy()
    random.shuffle(shuffled_images)
    
    # Place images in grid
    for row in range(grid_size):
        for col in range(grid_size):
            idx = row * grid_size + col
            if idx >= len(shuffled_images):
                break
            
            x = grid_start_x + (col * (cell_size + cell_spacing))
            y = grid_start_y + (row * (cell_size + cell_spacing))
            
            # Draw cell border
            draw.rectangle(
                [x, y, x + cell_size, y + cell_size],
                outline=(0, 0, 0, 255),
                width=3
            )
            
            # Load and place image
            theme_image = image_loader.load_image(shuffled_images[idx], folder_type)
            scaled_image = scale_image_proportional(theme_image, max_width=cell_size-20, max_height=cell_size-20)
            
            img_x = x + (cell_size - scaled_image.width) // 2
            img_y = y + (cell_size - scaled_image.height) // 2
            
            page.paste(scaled_image, (int(img_x), int(img_y)), scaled_image)
    
    add_page_border(page)
    add_footer(page)
    
    return page


def generate_find_cover_set(target_images, all_images, theme_name='Theme',
                            num_sheets=3, grid_size=4, folder_type='color', output_dir='output'):
    """
    Generate multiple Find & Cover sheets.
    
    Args:
        target_images: List of target images to find
        all_images: All available images (includes targets)
        theme_name: Theme name
        num_sheets: Number of sheets to generate
        grid_size: Grid size
        folder_type: Image folder type
        output_dir: Output directory
        
    Returns:
        list: Generated pages
    """
    pages = []
    
    for i in range(num_sheets):
        # Create grid with targets repeated and some distractors
        grid_images = target_images * 3  # Repeat targets
        # Add random distractors
        distractors = [img for img in all_images if img not in target_images]
        grid_images.extend(random.sample(distractors, min(len(distractors), grid_size)))
        
        page = generate_find_cover_sheet(target_images[:5], grid_images, theme_name, grid_size, folder_type)
        pages.append(page)
    
    # Save PDF
    output_path = f"{output_dir}/{theme_name}_Find_Cover.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Find & Cover")
    
    return pages


if __name__ == "__main__":
    print("Find & Cover Generator")
    print("Use generate_find_cover_sheet() or generate_find_cover_set()")
