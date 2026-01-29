"""
Core utility functions for SPED TpT activity generation.
Provides helpers for fonts, scaling, centering, transparency, and image loading.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional


# Constants
DPI = 300
DEFAULT_FONT_SIZE = 48
LARGE_FONT_SIZE = 72
SMALL_FONT_SIZE = 36

# Standard SPED colors (high contrast)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)
BLUE = (0, 102, 204)
RED = (204, 0, 0)
GREEN = (0, 153, 0)
YELLOW = (255, 204, 0)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def get_font(size: int = DEFAULT_FONT_SIZE, bold: bool = False) -> ImageFont.FreeTypeFont:
    """
    Get a font suitable for SPED materials.
    Falls back to default font if custom fonts are not available.
    
    Args:
        size: Font size in points
        bold: Whether to use bold font
        
    Returns:
        ImageFont object
    """
    try:
        # Try to use Arial or Helvetica (common system fonts)
        font_name = "Arial-Bold" if bold else "Arial"
        return ImageFont.truetype(font_name, size)
    except OSError:
        try:
            font_name = "Helvetica-Bold" if bold else "Helvetica"
            return ImageFont.truetype(font_name, size)
        except OSError:
            try:
                # Try DejaVu Sans (common on Linux)
                font_name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
                return ImageFont.truetype(font_name, size)
            except OSError:
                # Fall back to default font
                return ImageFont.load_default()


def scale_image_to_fit(image: Image.Image, max_width: int, max_height: int, 
                       maintain_aspect: bool = True) -> Image.Image:
    """
    Scale an image to fit within the given dimensions.
    
    Args:
        image: PIL Image to scale
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        maintain_aspect: Whether to maintain aspect ratio
        
    Returns:
        Scaled PIL Image
    """
    if maintain_aspect:
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        return image
    else:
        return image.resize((max_width, max_height), Image.Resampling.LANCZOS)


def center_image(canvas_width: int, canvas_height: int, 
                image_width: int, image_height: int) -> Tuple[int, int]:
    """
    Calculate position to center an image on a canvas.
    
    Args:
        canvas_width: Width of the canvas
        canvas_height: Height of the canvas
        image_width: Width of the image
        image_height: Height of the image
        
    Returns:
        Tuple of (x, y) coordinates for top-left corner
    """
    x = (canvas_width - image_width) // 2
    y = (canvas_height - image_height) // 2
    return (x, y)


def add_transparency(image: Image.Image, alpha: int = 128) -> Image.Image:
    """
    Add transparency to an image.
    
    Args:
        image: PIL Image
        alpha: Transparency level (0-255, where 0 is fully transparent)
        
    Returns:
        Image with transparency
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Create a new image with adjusted alpha
    data = image.getdata()
    new_data = []
    for item in data:
        # Change all non-transparent pixels to have the specified alpha
        if len(item) == 4 and item[3] > 0:
            new_data.append((item[0], item[1], item[2], alpha))
        else:
            new_data.append(item)
    
    image.putdata(new_data)
    return image


def load_image(filename: str, folder: str = 'images') -> Optional[Image.Image]:
    """
    Load an image from the specified folder.
    
    Args:
        filename: Name of the image file
        folder: Folder name (images, Colour_images, or aac_images)
        
    Returns:
        PIL Image or None if file not found
    """
    root = get_project_root()
    image_path = root / folder / filename
    
    if not image_path.exists():
        print(f"Warning: Image not found at {image_path}")
        return None
    
    try:
        return Image.open(image_path)
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None


def create_placeholder_image(width: int, height: int, 
                            text: str = "Image", 
                            bg_color: Tuple[int, int, int] = LIGHT_GRAY) -> Image.Image:
    """
    Create a placeholder image when actual image is not available.
    
    Args:
        width: Image width
        height: Image height
        text: Text to display on placeholder
        bg_color: Background color
        
    Returns:
        PIL Image
    """
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Add border
    border_width = max(2, min(width, height) // 50)
    draw.rectangle([0, 0, width-1, height-1], outline=DARK_GRAY, width=border_width)
    
    # Add text
    font = get_font(min(width, height) // 10)
    
    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    
    draw.text((text_x, text_y), text, fill=DARK_GRAY, font=font)
    
    return image


def inches_to_pixels(inches: float, dpi: int = DPI) -> int:
    """
    Convert inches to pixels at the specified DPI.
    
    Args:
        inches: Measurement in inches
        dpi: Dots per inch
        
    Returns:
        Pixels
    """
    return int(inches * dpi)


def pixels_to_inches(pixels: int, dpi: int = DPI) -> float:
    """
    Convert pixels to inches at the specified DPI.
    
    Args:
        pixels: Measurement in pixels
        dpi: Dots per inch
        
    Returns:
        Inches
    """
    return pixels / dpi
