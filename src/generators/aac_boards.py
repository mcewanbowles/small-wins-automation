"""
AAC (Augmentative and Alternative Communication) Boards Generator
Creates communication boards with symbols and text labels.
"""

from PIL import Image
from typing import List, Tuple, Optional
from ..utils import (
    SPEDLayout, get_font, load_image, create_placeholder_image,
    scale_image_to_fit, BLACK, WHITE, LARGE_FONT_SIZE,
    DEFAULT_FONT_SIZE, SMALL_FONT_SIZE, inches_to_pixels
)

# Layout constants for AAC boards
AAC_IMAGE_PADDING = 40
AAC_IMAGE_MARGIN = 20
AAC_CIRCLE_PADDING = 15
AAC_TEXT_BG_PADDING = 5


def generate_aac_board(items: List[Tuple[str, str]],
                      image_folder: str = 'aac_images',
                      title: str = "Communication Board",
                      grid_size: Tuple[int, int] = (3, 4),
                      output_path: str = None) -> Image.Image:
    """
    Generate an AAC communication board.
    
    Args:
        items: List of tuples (image_filename, label_text)
        image_folder: Folder to load AAC images from
        title: Title for the board
        grid_size: Tuple of (rows, cols)
        output_path: Path to save the board
        
    Returns:
        PIL Image of AAC board
    """
    rows, cols = grid_size
    
    # Create layout
    layout = SPEDLayout()
    
    # Add title
    layout.add_title(title, font_size=LARGE_FONT_SIZE, color=BLACK)
    
    # Add border
    layout.add_border(width=8)  # Thicker border for AAC boards
    
    # Calculate grid
    top_margin = inches_to_pixels(1.5)
    bottom_margin = inches_to_pixels(0.75)
    side_margin = inches_to_pixels(0.5)
    
    grid_width = layout.width - 2 * side_margin
    grid_height = layout.height - top_margin - bottom_margin
    
    cell_width = grid_width // cols
    cell_height = grid_height // rows
    
    # Draw grid
    for row in range(rows + 1):
        y = top_margin + row * cell_height
        layout.draw.line(
            [(side_margin, y), (side_margin + grid_width, y)],
            fill=BLACK,
            width=5
        )
    
    for col in range(cols + 1):
        x = side_margin + col * cell_width
        layout.draw.line(
            [(x, top_margin), (x, top_margin + grid_height)],
            fill=BLACK,
            width=5
        )
    
    # Fill cells with images and labels
    for idx, (image_file, label) in enumerate(items[:rows * cols]):
        row = idx // cols
        col = idx % cols
        
        cell_x = side_margin + col * cell_width
        cell_y = top_margin + row * cell_height
        
        # Load and scale image
        image = load_image(image_file, image_folder)
        if not image:
            # Create placeholder for AAC symbol
            image = create_placeholder_image(
                cell_width - AAC_IMAGE_PADDING,
                cell_height - 80,
                label[:10]
            )
        
        # Reserve space for label at bottom
        image_height = cell_height - inches_to_pixels(0.8)
        scaled_image = scale_image_to_fit(
            image.copy(),
            cell_width - AAC_IMAGE_PADDING,
            image_height - AAC_IMAGE_PADDING
        )
        
        # Center image in upper part of cell
        img_x = cell_x + (cell_width - scaled_image.width) // 2
        img_y = cell_y + AAC_IMAGE_MARGIN
        layout.paste_image(scaled_image, img_x, img_y)
        
        # Add label below image
        font = get_font(DEFAULT_FONT_SIZE, bold=True)
        bbox = layout.draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        
        # Truncate label if too long
        if text_width > cell_width - AAC_IMAGE_MARGIN:
            font = get_font(SMALL_FONT_SIZE, bold=True)
            display_label = label[:15]
        else:
            display_label = label
        
        bbox = layout.draw.textbbox((0, 0), display_label, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = cell_x + (cell_width - text_width) // 2
        text_y = cell_y + cell_height - text_height - AAC_CIRCLE_PADDING
        
        # Draw text with white background for better visibility
        layout.draw.rectangle(
            [text_x - AAC_TEXT_BG_PADDING, text_y - AAC_TEXT_BG_PADDING,
             text_x + text_width + AAC_TEXT_BG_PADDING, text_y + text_height + AAC_TEXT_BG_PADDING],
            fill=WHITE
        )
        layout.draw.text((text_x, text_y), display_label, fill=BLACK, font=font)
    
    # Add footer
    layout.add_footer("© Small Wins Studio")
    
    # Save if output path provided
    if output_path:
        layout.save(output_path)
    
    return layout.get_canvas()


def generate_aac_board_set(items_list: List[List[Tuple[str, str]]],
                          image_folder: str = 'aac_images',
                          titles: Optional[List[str]] = None,
                          grid_size: Tuple[int, int] = (3, 4),
                          output_dir: str = 'outputs') -> List[str]:
    """
    Generate a set of AAC boards.
    
    Args:
        items_list: List of item lists for each board
        image_folder: Folder to load AAC images from
        titles: Optional list of titles for each board
        grid_size: Grid size for boards
        output_dir: Directory to save boards
        
    Returns:
        List of output filenames
    """
    from ..utils import get_project_root
    
    output_files = []
    output_path = get_project_root() / output_dir
    output_path.mkdir(exist_ok=True)
    
    if titles is None:
        titles = [f"Communication Board {i+1}" for i in range(len(items_list))]
    
    for i, items in enumerate(items_list):
        filename = f"aac_board_{i+1}.png"
        filepath = output_path / filename
        
        title = titles[i] if i < len(titles) else f"Communication Board {i+1}"
        
        generate_aac_board(
            items,
            image_folder=image_folder,
            title=title,
            grid_size=grid_size,
            output_path=str(filepath)
        )
        
        output_files.append(str(filepath))
    
    return output_files
