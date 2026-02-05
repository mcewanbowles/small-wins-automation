"""
Matching Generator
Creates matching activities with images or text pairs.
"""

from PIL import Image
from typing import List, Tuple, Optional
from ..utils import (
    SPEDLayout, get_font, load_image, create_placeholder_image,
    scale_image_to_fit, BLACK, WHITE, LARGE_FONT_SIZE,
    DEFAULT_FONT_SIZE, inches_to_pixels
)
import random

# Layout constants for matching activities
MATCHING_ROW_PADDING = 20
MATCHING_IMAGE_PADDING = 40
MATCHING_CIRCLE_RADIUS = 15
MATCHING_CIRCLE_WIDTH = 3


def generate_matching_activity(pairs: List[Tuple[str, str]],
                               left_folder: str = 'images',
                               right_folder: str = 'Colour_images',
                               use_images: bool = True,
                               title: str = "Match the Pairs",
                               output_path: str = None) -> Image.Image:
    """
    Generate a matching activity with two columns.
    
    Args:
        pairs: List of tuples (left_item, right_item)
        left_folder: Folder for left column images
        right_folder: Folder for right column images
        use_images: Whether to use images (True) or text (False)
        title: Title for the activity
        output_path: Path to save the activity
        
    Returns:
        PIL Image of matching activity
    """
    # Create layout
    layout = SPEDLayout()
    
    # Add title
    layout.add_title(title, font_size=LARGE_FONT_SIZE, color=BLACK)
    
    # Add border
    layout.add_border()
    
    # Calculate layout
    num_pairs = len(pairs)
    top_margin = inches_to_pixels(1.5)
    bottom_margin = inches_to_pixels(0.75)
    side_margin = inches_to_pixels(0.75)
    
    available_height = layout.height - top_margin - bottom_margin
    row_height = available_height // num_pairs
    
    # Column widths
    column_width = (layout.width - 2 * side_margin - inches_to_pixels(1)) // 2
    left_column_x = side_margin
    right_column_x = layout.width - side_margin - column_width
    
    # Shuffle right column for matching
    left_items = [pair[0] for pair in pairs]
    right_items = [pair[1] for pair in pairs]
    random.shuffle(right_items)
    
    # Draw items
    for idx in range(num_pairs):
        y = top_margin + idx * row_height
        center_y = y + row_height // 2
        
        # Draw left item
        left_item = left_items[idx]
        _draw_item(
            layout, left_item, left_column_x, center_y,
            column_width, row_height - MATCHING_ROW_PADDING,
            left_folder, use_images
        )
        
        # Draw circle for left side
        circle_x = left_column_x + column_width + inches_to_pixels(0.2)
        layout.draw.ellipse(
            [circle_x - MATCHING_CIRCLE_RADIUS, center_y - MATCHING_CIRCLE_RADIUS,
             circle_x + MATCHING_CIRCLE_RADIUS, center_y + MATCHING_CIRCLE_RADIUS],
            outline=BLACK,
            width=MATCHING_CIRCLE_WIDTH
        )
        
        # Draw right item
        right_item = right_items[idx]
        _draw_item(
            layout, right_item, right_column_x, center_y,
            column_width, row_height - MATCHING_ROW_PADDING,
            right_folder, use_images
        )
        
        # Draw circle for right side
        circle_x = right_column_x - inches_to_pixels(0.2)
        layout.draw.ellipse(
            [circle_x - MATCHING_CIRCLE_RADIUS, center_y - MATCHING_CIRCLE_RADIUS,
             circle_x + MATCHING_CIRCLE_RADIUS, center_y + MATCHING_CIRCLE_RADIUS],
            outline=BLACK,
            width=MATCHING_CIRCLE_WIDTH
        )
    
    # Add instruction
    instruction_font = get_font(DEFAULT_FONT_SIZE)
    instruction = "Draw a line to match the pairs"
    bbox = layout.draw.textbbox((0, 0), instruction, font=instruction_font)
    inst_width = bbox[2] - bbox[0]
    
    inst_x = (layout.width - inst_width) // 2
    inst_y = top_margin - inches_to_pixels(0.6)
    layout.draw.text((inst_x, inst_y), instruction, fill=BLACK, font=instruction_font)
    
    # Add footer
    layout.add_footer("© Small Wins Studio")
    
    # Save if output path provided
    if output_path:
        layout.save(output_path)
    
    return layout.get_canvas()


def _draw_item(layout: SPEDLayout, item: str, x: int, center_y: int,
               width: int, height: int, folder: str, use_images: bool):
    """Helper function to draw an item (image or text)."""
    if use_images:
        # Try to load image
        image = load_image(item, folder)
        if not image:
            image = create_placeholder_image(width, height, item.split('.')[0][:10])
        
        # Scale image
        scaled_image = scale_image_to_fit(image.copy(), width, height)
        
        # Center in available space
        img_x = x + (width - scaled_image.width) // 2
        img_y = center_y - scaled_image.height // 2
        
        layout.paste_image(scaled_image, img_x, img_y)
    else:
        # Display text
        font = get_font(DEFAULT_FONT_SIZE)
        bbox = layout.draw.textbbox((0, 0), item, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = x + (width - text_width) // 2
        text_y = center_y - text_height // 2
        layout.draw.text((text_x, text_y), item, fill=BLACK, font=font)


def generate_matching_set(pairs_list: List[List[Tuple[str, str]]],
                         left_folder: str = 'images',
                         right_folder: str = 'Colour_images',
                         use_images: bool = True,
                         output_dir: str = 'outputs') -> List[str]:
    """
    Generate a set of matching activities.
    
    Args:
        pairs_list: List of pair lists for each activity
        left_folder: Folder for left column images
        right_folder: Folder for right column images
        use_images: Whether to use images
        output_dir: Directory to save activities
        
    Returns:
        List of output filenames
    """
    from ..utils import get_project_root
    
    output_files = []
    output_path = get_project_root() / output_dir
    output_path.mkdir(exist_ok=True)
    
    for i, pairs in enumerate(pairs_list):
        filename = f"matching_activity_{i+1}.png"
        filepath = output_path / filename
        
        generate_matching_activity(
            pairs,
            left_folder=left_folder,
            right_folder=right_folder,
            use_images=use_images,
            output_path=str(filepath)
        )
        
        output_files.append(str(filepath))
    
    return output_files
