"""
Image loading utilities for SPED resource generation.

Handles loading images from the three designated folders:
- /images for full-color theme images
- /Colour_images for black-and-white outline images
- /aac_images for AAC/PCS-style symbols
"""

import os
from PIL import Image
from utils.config import IMAGE_FOLDERS


class ImageLoader:
    """Manages loading and caching of images from designated folders."""
    
    def __init__(self, base_path='.'):
        """
        Initialize the image loader.
        
        Args:
            base_path: Base path where image folders are located
        """
        self.base_path = base_path
        self.image_cache = {}
    
    def _get_folder_path(self, folder_type):
        """
        Get the full path to an image folder.
        
        Args:
            folder_type: 'color', 'bw_outline', or 'aac'
            
        Returns:
            str: Full path to the folder
        """
        folder_name = IMAGE_FOLDERS.get(folder_type)
        if not folder_name:
            raise ValueError(f"Unknown folder type: {folder_type}")
        
        return os.path.join(self.base_path, folder_name)
    
    def load_image(self, filename, folder_type='color'):
        """
        Load an image from one of the designated folders.
        
        Args:
            filename: Name of the image file
            folder_type: 'color', 'bw_outline', or 'aac'
            
        Returns:
            PIL.Image: The loaded image with transparency preserved
        """
        cache_key = f"{folder_type}:{filename}"
        
        # Return cached image if available
        if cache_key in self.image_cache:
            return self.image_cache[cache_key].copy()
        
        # Construct full path
        folder_path = self._get_folder_path(folder_type)
        image_path = os.path.join(folder_path, filename)
        
        # Check if file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Load image and preserve transparency
        image = Image.open(image_path)
        
        # Convert to RGBA to preserve transparency
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Cache the image
        self.image_cache[cache_key] = image.copy()
        
        return image
    
    def list_images(self, folder_type='color', extensions=None):
        """
        List all images in a folder.
        
        Args:
            folder_type: 'color', 'bw_outline', or 'aac'
            extensions: List of file extensions to include (default: common image formats)
            
        Returns:
            list: List of image filenames
        """
        if extensions is None:
            extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        
        folder_path = self._get_folder_path(folder_type)
        
        if not os.path.exists(folder_path):
            return []
        
        images = []
        for filename in os.listdir(folder_path):
            if any(filename.lower().endswith(ext) for ext in extensions):
                images.append(filename)
        
        return sorted(images)
    
    def clear_cache(self):
        """Clear the image cache to free memory."""
        self.image_cache.clear()


# Global image loader instance
_image_loader = None

def get_image_loader(base_path='.'):
    """
    Get the global image loader instance.
    
    Args:
        base_path: Base path where image folders are located
        
    Returns:
        ImageLoader: The global image loader
    """
    global _image_loader
    if _image_loader is None:
        _image_loader = ImageLoader(base_path)
    return _image_loader
