"""
Counting Mats Generator
Creates counting mats with numbers and space for objects.
"""

from PIL import Image, ImageDraw
from typing import List, Optional
from ..utils import (
    SPEDLayout, get_font, load_image, create_placeholder_image,
    scale_image_to_fit, BLACK, WHITE, BLUE, LARGE_FONT_SIZE,
    DEFAULT_FONT_SIZE, inches_to_pixels
)


def generate_counting_mat(number: int,
                         image_filename: Optional[str] = None,
                         image_folder: str = 'Colour_images',
                         title: str = None,
                         output_path: str = None) -> Image.Image:
    """
    Generate a counting mat for a specific number.
    
    Args:
        number: Number to practice counting
        image_filename: Optional image to use for counting objects
        image_folder: Folder to load image from
        title: Optional custom title
        output_path: Path to save the mat (if None, doesn't save)
        
    Returns:
        PIL Image of the counting mat
    """
    # Create layout
    layout = SPEDLayout()
    
    # Add title
    title_text = title or f"Count to {number}"
    layout.add_title(title_text, font_size=LARGE_FONT_SIZE, color=BLACK)
    
    # Add border
    layout.add_border()
    
    # Create large number on left side
    number_area_width = inches_to_pixels(3)
    number_x = layout.MARGIN + number_area_width // 2
    number_y = layout.height // 2
    
    # Draw large number
    number_font = get_font(200, bold=True)
    bbox = layout.draw.textbbox((0, 0), str(number), font=number_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    num_x = number_x - text_width // 2
    num_y = number_y - text_height // 2
    layout.draw.text((num_x, num_y), str(number), fill=BLUE, font=number_font)
    
    # Create counting area on right side
    counting_area_x = layout.MARGIN + number_area_width + inches_to_pixels(0.5)
    counting_area_y = layout.MARGIN + inches_to_pixels(1.5)
    counting_area_width = layout.width - counting_area_x - layout.MARGIN
    counting_area_height = layout.height - counting_area_y - layout.MARGIN - inches_to_pixels(0.5)
    
    # Draw rectangle for counting area
    layout.draw.rectangle(
        [counting_area_x, counting_area_y,
         counting_area_x + counting_area_width, counting_area_y + counting_area_height],
        outline=BLACK,
        width=5
    )
    
    # Add instruction text
    instruction_font = get_font(DEFAULT_FONT_SIZE)
    instruction = f"Place {number} objects here"
    bbox = layout.draw.textbbox((0, 0), instruction, font=instruction_font)
    inst_width = bbox[2] - bbox[0]
    
    inst_x = counting_area_x + (counting_area_width - inst_width) // 2
    inst_y = counting_area_y + inches_to_pixels(0.3)
    layout.draw.text((inst_x, inst_y), instruction, fill=BLACK, font=instruction_font)
    
    # Optionally add sample images
    if image_filename:
        image = load_image(image_filename, image_folder)
        if image:
            # Scale and show sample objects
            sample_size = min(
                counting_area_width // min(number, 5),
                counting_area_height // ((number + 4) // 5)
            )
            sample_size = min(sample_size, inches_to_pixels(1.5))
            
            object_image = scale_image_to_fit(
                image.copy(),
                sample_size - 20,
                sample_size - 20
            )
            
            # Arrange objects in grid
            objects_per_row = min(number, 5)
            rows = (number + objects_per_row - 1) // objects_per_row
            
            start_y = counting_area_y + inches_to_pixels(1)
            
            for i in range(number):
                row = i // objects_per_row
                col = i % objects_per_row
                
                x = counting_area_x + col * (counting_area_width // objects_per_row) + sample_size // 2
                y = start_y + row * sample_size + sample_size // 2
                
                layout.paste_image(object_image.copy(), x, y, centered=True)
    
    # Add footer
    layout.add_footer("© Small Wins Studio")
    
    # Save if output path provided
    if output_path:
        layout.save(output_path)
    
    return layout.get_canvas()


def generate_counting_mat_set(start: int = 1, end: int = 10,
                              image_filename: Optional[str] = None,
                              image_folder: str = 'Colour_images',
                              output_dir: str = 'outputs') -> List[str]:
    """
    Generate a set of counting mats.
    
    Args:
        start: Starting number
        end: Ending number (inclusive)
        image_filename: Optional image to use
        image_folder: Folder to load image from
        output_dir: Directory to save mats
        
    Returns:
        List of output filenames
    """
    from ..utils import get_project_root
    
    output_files = []
    output_path = get_project_root() / output_dir
    output_path.mkdir(exist_ok=True)
    
    for num in range(start, end + 1):
        filename = f"counting_mat_{num}.png"
        filepath = output_path / filename
        
        generate_counting_mat(
            num,
            image_filename=image_filename,
            image_folder=image_folder,
            output_path=str(filepath)
        )
        
        output_files.append(str(filepath))
    
    return output_files
