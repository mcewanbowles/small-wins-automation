"""
Counting Mats Generator

Generates counting mats for numbers 1-10 (or customizable range) with visual
representations. Supports differentiation levels and SPED design principles.
"""

from PIL import Image, ImageDraw
from utils.config import (
    PAGE_WIDTH, PAGE_HEIGHT, MARGINS, CARD_SIZES, 
    DIFFERENTIATION_LEVELS, DPI
)
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional, center_image_in_box
from utils.layout import (
    create_page_canvas, add_page_border, add_footer,
    calculate_centered_position, add_title_to_page
)
from utils.pdf_export import save_image_as_pdf, save_images_as_pdf


def generate_counting_mat(number, image_filename, theme_name, level=1, 
                          folder_type='color', output_dir='output'):
    """
    Generate a single counting mat for a specific number.
    
    Args:
        number: Number to count (e.g., 1-10)
        image_filename: Filename of the theme image
        theme_name: Name of the theme (e.g., "Farm Animals")
        level: Differentiation level (1, 2, or 3)
        folder_type: 'color', 'bw_outline', or 'aac'
        output_dir: Directory to save output PDF
        
    Returns:
        PIL.Image: Generated counting mat page
    """
    # Create page canvas
    page = create_page_canvas()
    
    # Add title
    title_text = f"Count to {number}"
    add_title_to_page(page, title_text)
    
    # Load image
    image_loader = get_image_loader()
    theme_image = image_loader.load_image(image_filename, folder_type)
    
    # Determine layout based on number
    if number <= 5:
        grid_cols = number
        grid_rows = 1
    elif number <= 10:
        grid_cols = 5
        grid_rows = 2
    else:
        grid_cols = 5
        grid_rows = (number + 4) // 5
    
    # Calculate cell size
    available_width = PAGE_WIDTH - (MARGINS['page'] * 2)
    available_height = PAGE_HEIGHT - (MARGINS['page'] * 3) - 200  # Space for title
    
    cell_spacing = MARGINS['content']
    cell_width = (available_width - (cell_spacing * (grid_cols - 1))) // grid_cols
    cell_height = (available_height - (cell_spacing * (grid_rows - 1))) // grid_rows
    cell_size = min(cell_width, cell_height)
    
    # Scale theme image
    scaled_image = scale_image_proportional(theme_image, max_width=cell_size-40, max_height=cell_size-40)
    
    # Calculate starting position to center the grid
    total_width = (cell_size * grid_cols) + (cell_spacing * (grid_cols - 1))
    total_height = (cell_size * grid_rows) + (cell_spacing * (grid_rows - 1))
    start_x = (PAGE_WIDTH - total_width) // 2
    start_y = 300  # Below title
    
    # Place images in grid
    for i in range(number):
        row = i // grid_cols
        col = i % grid_cols
        
        x = start_x + (col * (cell_size + cell_spacing))
        y = start_y + (row * (cell_size + cell_spacing))
        
        # Center image in cell
        centered_img = center_image_in_box(scaled_image, cell_size, cell_size)
        page.paste(centered_img, (int(x), int(y)), centered_img)
    
    # Add visual cues for Level 1
    if level == 1:
        # Draw number boxes at bottom
        draw = ImageDraw.Draw(page)
        box_y = PAGE_HEIGHT - 400
        for i in range(1, 11):
            box_x = start_x + ((i-1) * 60)
            color = (0, 0, 0, 255) if i == number else (200, 200, 200, 255)
            draw.rectangle([box_x, box_y, box_x + 50, box_y + 50], outline=color, width=3)
            # Draw number in box (simplified - just the outline)
    
    # Add border and footer
    add_page_border(page)
    add_footer(page)
    
    return page


def generate_counting_mats_set(image_filenames, theme_name, number_range=(1, 10),
                                level=1, folder_type='color', output_dir='output',
                                include_storage_label=False):
    """
    Generate a complete set of counting mats.
    
    Args:
        image_filenames: List of image filenames (one per number)
        theme_name: Name of the theme
        number_range: Tuple of (start, end) numbers
        level: Differentiation level
        folder_type: Image folder type
        output_dir: Output directory
        include_storage_label: If True, also generate a companion storage label PDF
        
    Returns:
        list: List of generated pages
    """
    pages = []
    start_num, end_num = number_range
    
    for num in range(start_num, end_num + 1):
        # Use image for this number (cycle if not enough images)
        img_idx = (num - start_num) % len(image_filenames)
        image_file = image_filenames[img_idx]
        
        page = generate_counting_mat(num, image_file, theme_name, level, folder_type, output_dir)
        pages.append(page)
    
    # Save as multi-page PDF
    output_path = f"{output_dir}/{theme_name}_Counting_Mats_Level{level}.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Counting Mats")
    
    print(f"✓ Generated {len(pages)} counting mats")
    print(f"  Output: {output_path}")
    
    # Generate storage label if requested
    if include_storage_label:
        from utils.storage_label_helper import create_companion_label
        import os
        
        # Try to get first image as icon
        icon_path = None
        if image_filenames:
            first_image = image_filenames[0]
            # Try to find the image in the images folder
            potential_icon = f"images/{first_image}"
            if not potential_icon.endswith('.png'):
                potential_icon += '.png'
            if os.path.exists(potential_icon):
                icon_path = potential_icon
        
        label_path = create_companion_label(
            main_pdf_path=output_path,
            theme_name=theme_name,
            activity_name="Counting Mats",
            level=level,
            icon_path=icon_path
        )
        print(f"✓ Generated storage label")
        print(f"  Label: {label_path}")
    
    return pages


if __name__ == "__main__":
    # Example usage
    print("Counting Mats Generator")
    print("Use generate_counting_mat() or generate_counting_mats_set() in your code")
