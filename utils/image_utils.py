"""
Image manipulation utilities for SPED resources.

Provides functions for scaling, centering, and preserving transparency
while maintaining SPED design principles (proportional scaling, high quality).
"""

from PIL import Image, ImageDraw
from utils.config import DPI


def scale_image_proportional(image, target_width=None, target_height=None, max_width=None, max_height=None):
    """
    Scale an image proportionally to fit within target dimensions.
    
    Args:
        image: PIL Image to scale
        target_width: Exact width to scale to (maintains aspect ratio)
        target_height: Exact height to scale to (maintains aspect ratio)
        max_width: Maximum width (will scale down if larger)
        max_height: Maximum height (will scale down if larger)
        
    Returns:
        PIL.Image: Scaled image with transparency preserved
    """
    original_width, original_height = image.size
    
    # Calculate scaling factor
    if target_width and target_height:
        # Fit within both dimensions while maintaining aspect ratio
        scale_w = target_width / original_width
        scale_h = target_height / original_height
        scale = min(scale_w, scale_h)
    elif target_width:
        scale = target_width / original_width
    elif target_height:
        scale = target_height / original_height
    elif max_width and max_height:
        # Only scale down if image is larger than max dimensions
        scale_w = max_width / original_width if original_width > max_width else 1.0
        scale_h = max_height / original_height if original_height > max_height else 1.0
        scale = min(scale_w, scale_h)
    elif max_width:
        scale = max_width / original_width if original_width > max_width else 1.0
    elif max_height:
        scale = max_height / original_height if original_height > max_height else 1.0
    else:
        return image
    
    # Calculate new dimensions
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)
    
    # Scale using high-quality resampling
    scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return scaled_image


def center_image_in_box(image, box_width, box_height, background_color=(255, 255, 255, 0)):
    """
    Center an image within a box of specified dimensions.
    
    Args:
        image: PIL Image to center
        box_width: Width of the box
        box_height: Height of the box
        background_color: RGBA tuple for background (default: transparent)
        
    Returns:
        PIL.Image: New image with original centered in box
    """
    # Create new image with transparent background
    centered = Image.new('RGBA', (box_width, box_height), background_color)
    
    # Calculate position to center the image
    img_width, img_height = image.size
    x = (box_width - img_width) // 2
    y = (box_height - img_height) // 2
    
    # Paste image onto centered background
    centered.paste(image, (x, y), image if image.mode == 'RGBA' else None)
    
    return centered


def add_border(image, border_width=5, border_color=(0, 0, 0, 255)):
    """
    Add a border around an image.
    
    Args:
        image: PIL Image to add border to
        border_width: Width of border in pixels
        border_color: RGBA tuple for border color
        
    Returns:
        PIL.Image: Image with border added
    """
    width, height = image.size
    new_width = width + (border_width * 2)
    new_height = height + (border_width * 2)
    
    # Create new image with border color
    bordered = Image.new('RGBA', (new_width, new_height), border_color)
    
    # Paste original image in center
    bordered.paste(image, (border_width, border_width), image if image.mode == 'RGBA' else None)
    
    return bordered


def create_thumbnail(image, size=(300, 300)):
    """
    Create a thumbnail of an image while maintaining aspect ratio.
    
    Args:
        image: PIL Image to create thumbnail from
        size: Tuple of (max_width, max_height)
        
    Returns:
        PIL.Image: Thumbnail image
    """
    # Make a copy to avoid modifying original
    thumb = image.copy()
    thumb.thumbnail(size, Image.Resampling.LANCZOS)
    return thumb


def ensure_rgba(image):
    """
    Ensure image is in RGBA mode for transparency support.
    
    Args:
        image: PIL Image
        
    Returns:
        PIL.Image: Image in RGBA mode
    """
    if image.mode != 'RGBA':
        return image.convert('RGBA')
    return image


def paste_with_transparency(base_image, overlay_image, position):
    """
    Paste an image onto another with transparency support.
    
    Args:
        base_image: PIL Image to paste onto
        overlay_image: PIL Image to paste
        position: Tuple of (x, y) coordinates
        
    Returns:
        PIL.Image: Base image with overlay pasted
    """
    # Ensure both images support transparency
    base = ensure_rgba(base_image)
    overlay = ensure_rgba(overlay_image)
    
    # Paste with alpha channel as mask
    base.paste(overlay, position, overlay)
    
    return base


def create_grid_layout(images, grid_cols, grid_rows, cell_width, cell_height, 
                       spacing=0, background_color=(255, 255, 255, 255)):
    """
    Arrange images in a grid layout.
    
    Args:
        images: List of PIL Images
        grid_cols: Number of columns
        grid_rows: Number of rows
        cell_width: Width of each grid cell
        cell_height: Height of each grid cell
        spacing: Space between cells
        background_color: RGBA tuple for background
        
    Returns:
        PIL.Image: Combined image with grid layout
    """
    total_width = (cell_width * grid_cols) + (spacing * (grid_cols - 1))
    total_height = (cell_height * grid_rows) + (spacing * (grid_rows - 1))
    
    grid_image = Image.new('RGBA', (total_width, total_height), background_color)
    
    for idx, image in enumerate(images[:grid_cols * grid_rows]):
        row = idx // grid_cols
        col = idx % grid_cols
        
        x = col * (cell_width + spacing)
        y = row * (cell_height + spacing)
        
        # Center image in cell
        centered = center_image_in_box(image, cell_width, cell_height, (255, 255, 255, 0))
        grid_image.paste(centered, (x, y), centered)
    
    return grid_image
