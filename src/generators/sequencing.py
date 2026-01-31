"""
Sequencing Generator
Creates sequencing activities with numbered steps.
"""

from PIL import Image
from typing import List, Optional
from ..utils import (
    SPEDLayout, get_font, load_image, create_placeholder_image,
    scale_image_to_fit, BLACK, WHITE, BLUE, LARGE_FONT_SIZE,
    DEFAULT_FONT_SIZE, inches_to_pixels
)


def generate_sequencing_activity(steps: List[str],
                                 image_folder: str = 'images',
                                 use_images: bool = True,
                                 title: str = "Put in Order",
                                 output_path: str = None) -> Image.Image:
    """
    Generate a sequencing activity.
    
    Args:
        steps: List of step items (image filenames or text)
        image_folder: Folder to load images from
        use_images: Whether to use images (True) or text (False)
        title: Title for the activity
        output_path: Path to save the activity
        
    Returns:
        PIL Image of sequencing activity
    """
    # Create layout
    layout = SPEDLayout()
    
    # Add title
    layout.add_title(title, font_size=LARGE_FONT_SIZE, color=BLACK)
    
    # Add border
    layout.add_border()
    
    # Calculate layout
    num_steps = len(steps)
    top_margin = inches_to_pixels(1.5)
    bottom_margin = inches_to_pixels(0.75)
    side_margin = inches_to_pixels(0.75)
    
    # Arrange in grid (2 columns if more than 3 steps, else 1 column)
    if num_steps <= 3:
        cols = 1
        rows = num_steps
    else:
        cols = 2
        rows = (num_steps + 1) // 2
    
    available_width = layout.width - 2 * side_margin
    available_height = layout.height - top_margin - bottom_margin
    
    cell_width = available_width // cols
    cell_height = available_height // rows
    
    # Draw each step
    for idx, step in enumerate(steps):
        row = idx // cols
        col = idx % cols
        
        cell_x = side_margin + col * cell_width
        cell_y = top_margin + row * cell_height
        
        # Draw number circle
        number_size = inches_to_pixels(0.6)
        number_x = cell_x + inches_to_pixels(0.3)
        number_y = cell_y + inches_to_pixels(0.2)
        
        # Draw circle
        layout.draw.ellipse(
            [number_x, number_y, number_x + number_size, number_y + number_size],
            fill=BLUE,
            outline=BLACK,
            width=3
        )
        
        # Draw number
        number_font = get_font(DEFAULT_FONT_SIZE, bold=True)
        num_text = str(idx + 1)
        bbox = layout.draw.textbbox((0, 0), num_text, font=number_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        num_text_x = number_x + (number_size - text_width) // 2
        num_text_y = number_y + (number_size - text_height) // 2
        layout.draw.text((num_text_x, num_text_y), num_text, fill=WHITE, font=number_font)
        
        # Draw item
        item_x = cell_x + inches_to_pixels(1.2)
        item_y = cell_y + inches_to_pixels(0.2)
        item_width = cell_width - inches_to_pixels(1.5)
        item_height = cell_height - inches_to_pixels(0.5)
        
        if use_images:
            # Load and display image
            image = load_image(step, image_folder)
            if not image:
                image = create_placeholder_image(
                    item_width,
                    item_height,
                    step.split('.')[0][:10]
                )
            
            scaled_image = scale_image_to_fit(image.copy(), item_width, item_height)
            
            # Draw border around image
            border_x = item_x
            border_y = item_y
            layout.draw.rectangle(
                [border_x, border_y,
                 border_x + item_width, border_y + item_height],
                outline=BLACK,
                width=3
            )
            
            # Center image in box
            img_x = item_x + (item_width - scaled_image.width) // 2
            img_y = item_y + (item_height - scaled_image.height) // 2
            layout.paste_image(scaled_image, img_x, img_y)
        else:
            # Display text
            # Draw border
            layout.draw.rectangle(
                [item_x, item_y, item_x + item_width, item_y + item_height],
                outline=BLACK,
                width=3
            )
            
            font = get_font(DEFAULT_FONT_SIZE)
            bbox = layout.draw.textbbox((0, 0), step, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = item_x + (item_width - text_width) // 2
            text_y = item_y + (item_height - text_height) // 2
            layout.draw.text((text_x, text_y), step, fill=BLACK, font=font)
    
    # Add footer
    layout.add_footer("© Small Wins Studio")
    
    # Save if output path provided
    if output_path:
        layout.save(output_path)
    
    return layout.get_canvas()


def generate_sequencing_set(steps_list: List[List[str]],
                           image_folder: str = 'images',
                           use_images: bool = True,
                           output_dir: str = 'outputs') -> List[str]:
    """
    Generate a set of sequencing activities.
    
    Args:
        steps_list: List of step lists for each activity
        image_folder: Folder to load images from
        use_images: Whether to use images
        output_dir: Directory to save activities
        
    Returns:
        List of output filenames
    """
    from ..utils import get_project_root
    
    output_files = []
    output_path = get_project_root() / output_dir
    output_path.mkdir(exist_ok=True)
    
    for i, steps in enumerate(steps_list):
        filename = f"sequencing_activity_{i+1}.png"
        filepath = output_path / filename
        
        generate_sequencing_activity(
            steps,
            image_folder=image_folder,
            use_images=use_images,
            output_path=str(filepath)
        )
        
        output_files.append(str(filepath))
    
    return output_files
