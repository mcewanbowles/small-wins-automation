"""
Bingo Generator
Creates bingo boards with images or text.
"""

from PIL import Image
from typing import List, Optional
from ..utils import (
    SPEDLayout, get_font, load_image, create_placeholder_image,
    scale_image_to_fit, BLACK, WHITE, LARGE_FONT_SIZE,
    DEFAULT_FONT_SIZE, inches_to_pixels
)
import random


def generate_bingo_board(items: List[str],
                        image_folder: str = 'images',
                        use_images: bool = True,
                        title: str = "BINGO",
                        free_space: bool = True,
                        output_path: str = None) -> Image.Image:
    """
    Generate a 5x5 bingo board.
    
    Args:
        items: List of item names (can be image filenames or text labels)
        image_folder: Folder to load images from
        use_images: Whether to use images (True) or text (False)
        title: Title for the board
        free_space: Whether to include a free space in center
        output_path: Path to save the board
        
    Returns:
        PIL Image of bingo board
    """
    # Create layout
    layout = SPEDLayout()
    
    # Add title
    layout.add_title(title, font_size=LARGE_FONT_SIZE, color=BLACK)
    
    # Add border
    layout.add_border()
    
    # Create 5x5 grid
    grid_margin = inches_to_pixels(0.75)
    grid_top = inches_to_pixels(1.5)
    grid_bottom = layout.height - inches_to_pixels(0.75)
    grid_height = grid_bottom - grid_top
    
    # Calculate cell size
    cell_size = (layout.width - 2 * grid_margin) // 5
    
    # Ensure we have enough items
    if len(items) < 24:  # 25 - 1 for free space
        items = items * ((24 // len(items)) + 1)
    
    # Shuffle and select items
    shuffled_items = random.sample(items, min(len(items), 24))
    
    # Insert free space at center (position 12)
    if free_space:
        shuffled_items.insert(12, "FREE")
    
    # Draw grid
    for row in range(6):
        y = grid_top + row * cell_size
        layout.draw.line(
            [(grid_margin, y), (layout.width - grid_margin, y)],
            fill=BLACK,
            width=5
        )
    
    for col in range(6):
        x = grid_margin + col * cell_size
        layout.draw.line(
            [(x, grid_top), (x, grid_top + 5 * cell_size)],
            fill=BLACK,
            width=5
        )
    
    # Fill cells
    for idx, item in enumerate(shuffled_items[:25]):
        row = idx // 5
        col = idx % 5
        
        cell_x = grid_margin + col * cell_size
        cell_y = grid_top + row * cell_size
        cell_center_x = cell_x + cell_size // 2
        cell_center_y = cell_y + cell_size // 2
        
        if item == "FREE":
            # Draw FREE space
            font = get_font(DEFAULT_FONT_SIZE, bold=True)
            bbox = layout.draw.textbbox((0, 0), "FREE", font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = cell_center_x - text_width // 2
            text_y = cell_center_y - text_height // 2
            layout.draw.text((text_x, text_y), "FREE", fill=BLACK, font=font)
        elif use_images:
            # Try to load and display image
            image = load_image(item, image_folder)
            if not image:
                # Create placeholder
                image = create_placeholder_image(
                    cell_size - 40,
                    cell_size - 40,
                    item.split('.')[0][:10]
                )
            
            # Scale image to fit cell
            scaled_image = scale_image_to_fit(
                image.copy(),
                cell_size - 40,
                cell_size - 40
            )
            
            # Paste image centered in cell
            layout.paste_image(scaled_image, cell_center_x, cell_center_y, centered=True)
        else:
            # Display text
            font = get_font(LARGE_FONT_SIZE // 2)
            # Truncate text if too long
            display_text = item[:15]
            bbox = layout.draw.textbbox((0, 0), display_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = cell_center_x - text_width // 2
            text_y = cell_center_y - text_height // 2
            layout.draw.text((text_x, text_y), display_text, fill=BLACK, font=font)
    
    # Add footer
    layout.add_footer("© Small Wins Studio")
    
    # Save if output path provided
    if output_path:
        layout.save(output_path)
    
    return layout.get_canvas()


def generate_bingo_set(items: List[str],
                      num_boards: int = 6,
                      image_folder: str = 'images',
                      use_images: bool = True,
                      output_dir: str = 'outputs') -> List[str]:
    """
    Generate a set of unique bingo boards.
    
    Args:
        items: List of items for bingo
        num_boards: Number of boards to generate
        image_folder: Folder to load images from
        use_images: Whether to use images
        output_dir: Directory to save boards
        
    Returns:
        List of output filenames
    """
    from ..utils import get_project_root
    
    output_files = []
    output_path = get_project_root() / output_dir
    output_path.mkdir(exist_ok=True)
    
    for i in range(num_boards):
        filename = f"bingo_board_{i+1}.png"
        filepath = output_path / filename
        
        generate_bingo_board(
            items,
            image_folder=image_folder,
            use_images=use_images,
            output_path=str(filepath)
        )
        
        output_files.append(str(filepath))
    
    return output_files
