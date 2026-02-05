"""
Image Resizer Utility

Provides specialized image resizing functions for SPED resources.
Works in conjunction with image_utils.py for comprehensive image manipulation.
"""

from PIL import Image
from utils.config import DPI


def resize_to_exact_dimensions(image, width, height, maintain_aspect=True):
    """
    Resize image to exact dimensions.
    
    Args:
        image: PIL Image to resize
        width: Target width in pixels
        height: Target height in pixels
        maintain_aspect: If True, maintains aspect ratio and fits within dimensions
        
    Returns:
        PIL.Image: Resized image
    """
    if maintain_aspect:
        # Calculate aspect-preserving dimensions
        original_width, original_height = image.size
        aspect_ratio = original_width / original_height
        target_aspect = width / height
        
        if aspect_ratio > target_aspect:
            # Image is wider - fit to width
            new_width = width
            new_height = int(width / aspect_ratio)
        else:
            # Image is taller - fit to height
            new_height = height
            new_width = int(height * aspect_ratio)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    else:
        # Stretch to exact dimensions
        return image.resize((width, height), Image.Resampling.LANCZOS)


def resize_by_percentage(image, scale_percent):
    """
    Resize image by percentage.
    
    Args:
        image: PIL Image to resize
        scale_percent: Percentage to scale (e.g., 50 for 50%, 200 for 200%)
        
    Returns:
        PIL.Image: Resized image
    """
    width, height = image.size
    new_width = int(width * scale_percent / 100)
    new_height = int(height * scale_percent / 100)
    
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def resize_for_print(image, width_inches, height_inches, dpi=DPI):
    """
    Resize image for printing at specific physical dimensions.
    
    Args:
        image: PIL Image to resize
        width_inches: Desired width in inches
        height_inches: Desired height in inches
        dpi: Target DPI (default from config)
        
    Returns:
        PIL.Image: Resized image at print resolution
    """
    target_width = int(width_inches * dpi)
    target_height = int(height_inches * dpi)
    
    return resize_to_exact_dimensions(image, target_width, target_height, maintain_aspect=True)


def batch_resize(images, target_size, maintain_aspect=True):
    """
    Resize multiple images to the same size.
    
    Args:
        images: List of PIL Images
        target_size: Tuple of (width, height)
        maintain_aspect: Whether to maintain aspect ratio
        
    Returns:
        list: List of resized PIL Images
    """
    width, height = target_size
    return [resize_to_exact_dimensions(img, width, height, maintain_aspect) for img in images]
