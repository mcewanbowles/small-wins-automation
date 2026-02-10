"""
Image loading utilities for TpT Automation System

Handles loading images from theme folders (/icons, /Colour_images, /aac_images, /real_images)
with proper transparency preservation and error handling.
"""

from PIL import Image
from pathlib import Path
from typing import Optional, Tuple
import os


def load_image(image_path: Path, preserve_transparency: bool = True) -> Optional[Image.Image]:
    """
    Load an image with optional transparency preservation.
    
    Args:
        image_path: Path to the image file
        preserve_transparency: Whether to preserve alpha channel (default True)
        
    Returns:
        PIL Image object or None if loading fails
    """
    try:
        img = Image.open(image_path)
        
        if preserve_transparency:
            # Convert to RGBA to preserve transparency
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
        else:
            # Convert to RGB (no transparency)
            if img.mode != 'RGB':
                img = img.convert('RGB')
        
        return img
        
    except FileNotFoundError:
        print(f"Warning: Image not found: {image_path}")
        return None
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None


def find_theme_image(theme_name: str, image_name: str, image_folder: str = "icons") -> Optional[Path]:
    """
    Find an image in a theme's image folders.
    
    Args:
        theme_name: Name of the theme (e.g., "brown_bear")
        image_name: Name of the image file (with or without extension)
        image_folder: Folder type ("icons", "Colour_images", "aac_images", "real_images")
        
    Returns:
        Path to the image file or None if not found
    """
    # Get project root (assuming we're in utils/)
    from .config import get_project_root
    root = get_project_root()
    
    # Try both with and without common extensions
    extensions = ['', '.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']
    
    # Check in theme-specific folder
    theme_folder = root / "assets" / "themes" / theme_name / image_folder
    for ext in extensions:
        image_path = theme_folder / f"{image_name}{ext}"
        if image_path.exists():
            return image_path
    
    # Check in root-level image folders (legacy structure)
    for folder_name in [image_folder, image_folder.lower()]:
        root_folder = root / folder_name
        if root_folder.exists():
            for ext in extensions:
                image_path = root_folder / f"{image_name}{ext}"
                if image_path.exists():
                    return image_path
    
    return None


def load_theme_image(theme_name: str, image_name: str, 
                    image_folder: str = "icons", 
                    preserve_transparency: bool = True) -> Optional[Image.Image]:
    """
    Load an image from a theme's image folders.
    
    Args:
        theme_name: Name of the theme (e.g., "brown_bear")
        image_name: Name of the image file
        image_folder: Folder type ("icons", "Colour_images", "aac_images", "real_images")
        preserve_transparency: Whether to preserve alpha channel
        
    Returns:
        PIL Image object or None if not found
    """
    image_path = find_theme_image(theme_name, image_name, image_folder)
    
    if image_path is None:
        print(f"Warning: Image '{image_name}' not found in {image_folder} for theme '{theme_name}'")
        return None
    
    return load_image(image_path, preserve_transparency)


def resize_image_proportional(img: Image.Image, max_width: int, max_height: int) -> Image.Image:
    """
    Resize image proportionally to fit within max dimensions.
    
    Args:
        img: PIL Image to resize
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        
    Returns:
        Resized PIL Image
    """
    # Get current dimensions
    orig_width, orig_height = img.size
    
    # Calculate aspect ratio
    ratio = min(max_width / orig_width, max_height / orig_height)
    
    # Don't upscale, only downscale
    if ratio >= 1.0:
        return img
    
    # Calculate new dimensions
    new_width = int(orig_width * ratio)
    new_height = int(orig_height * ratio)
    
    # Resize with high-quality resampling
    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)


def get_image_center_position(img_width: int, img_height: int, 
                              box_width: int, box_height: int) -> Tuple[int, int]:
    """
    Calculate position to center an image within a box.
    
    Args:
        img_width: Width of the image
        img_height: Height of the image
        box_width: Width of the containing box
        box_height: Height of the containing box
        
    Returns:
        Tuple of (x, y) coordinates for top-left corner of centered image
    """
    x = (box_width - img_width) // 2
    y = (box_height - img_height) // 2
    
    return (x, y)
