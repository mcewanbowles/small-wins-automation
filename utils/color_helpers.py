"""
Color and grayscale conversion utilities for dual-mode PDF generation.

This module provides utilities for converting colors, images, and palettes
between color and black-and-white modes to support accessibility and 
printing requirements for SPED resources.
"""

from PIL import Image, ImageEnhance
import io


def hex_to_grayscale(hex_color):
    """
    Convert a hex color to its grayscale equivalent.
    
    Uses the luminosity method: 0.299*R + 0.587*G + 0.114*B
    This provides perceptually accurate grayscale conversion.
    
    Args:
        hex_color (str): Hex color code (e.g., '#FF5733' or 'FF5733')
    
    Returns:
        str: Grayscale hex color
    
    Example:
        >>> hex_to_grayscale('#FF5733')
        '#7A7A7A'
    """
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    
    # Parse RGB values
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Calculate grayscale using luminosity method
    gray = int(0.299 * r + 0.587 * g + 0.114 * b)
    
    # Return as hex
    return f'#{gray:02X}{gray:02X}{gray:02X}'


def palette_to_grayscale(color_palette):
    """
    Convert a list of hex colors to grayscale equivalents.
    
    Args:
        color_palette (list): List of hex color codes
    
    Returns:
        list: List of grayscale hex colors
    
    Example:
        >>> palette_to_grayscale(['#FF0000', '#00FF00', '#0000FF'])
        ['#4C4C4C', '#969696', '#1D1D1D']
    """
    return [hex_to_grayscale(color) for color in color_palette]


def image_to_grayscale(image_path):
    """
    Convert an image file to grayscale.
    
    Args:
        image_path (str or PIL.Image): Path to the image file or PIL Image object
    
    Returns:
        PIL.Image: Grayscale image object
    
    Example:
        >>> img = image_to_grayscale('icon.png')
        >>> img.save('icon_bw.png')
    """
    if isinstance(image_path, Image.Image):
        img = image_path
    else:
        img = Image.open(image_path)
    
    # Convert to grayscale
    gray_img = img.convert('L')
    
    # Enhance contrast for better B&W printing
    enhancer = ImageEnhance.Contrast(gray_img)
    gray_img = enhancer.enhance(1.2)  # 20% contrast boost
    
    # Convert back to RGB mode for consistency
    return gray_img.convert('RGB')


def get_high_contrast_color(mode='color', base_color='#000000'):
    """
    Get a high-contrast color appropriate for the mode.
    
    Args:
        mode (str): 'color' or 'bw'
        base_color (str): Base color in color mode (default: black)
    
    Returns:
        str: Hex color code
    
    Example:
        >>> get_high_contrast_color('color', '#FF0000')
        '#FF0000'
        >>> get_high_contrast_color('bw', '#FF0000')
        '#000000'
    """
    if mode == 'bw':
        # Always use pure black for maximum contrast in BW mode
        return '#000000'
    return base_color


def adjust_for_bw_mode(color, mode='color'):
    """
    Adjust a color based on the output mode.
    
    In BW mode, returns grayscale equivalent.
    In color mode, returns original color.
    
    Args:
        color (str): Hex color code
        mode (str): 'color' or 'bw'
    
    Returns:
        str: Adjusted hex color
    
    Example:
        >>> adjust_for_bw_mode('#FF5733', 'color')
        '#FF5733'
        >>> adjust_for_bw_mode('#FF5733', 'bw')
        '#7A7A7A'
    """
    if mode == 'bw':
        return hex_to_grayscale(color)
    return color


def get_background_color(mode='color', theme_color='#FFFFFF'):
    """
    Get appropriate background color for the mode.
    
    In BW mode, always returns white for maximum contrast.
    In color mode, returns the theme color.
    
    Args:
        mode (str): 'color' or 'bw'
        theme_color (str): Theme background color
    
    Returns:
        str: Hex color code for background
    
    Example:
        >>> get_background_color('color', '#FFF5E1')
        '#FFF5E1'
        >>> get_background_color('bw', '#FFF5E1')
        '#FFFFFF'
    """
    if mode == 'bw':
        return '#FFFFFF'  # Pure white for BW mode
    return theme_color


def get_border_color(mode='color', theme_color='#000000'):
    """
    Get appropriate border color for the mode.
    
    In BW mode, always returns black for maximum contrast.
    In color mode, returns the theme color.
    
    Args:
        mode (str): 'color' or 'bw'
        theme_color (str): Theme border color
    
    Returns:
        str: Hex color code for border
    
    Example:
        >>> get_border_color('color', '#336699')
        '#336699'
        >>> get_border_color('bw', '#336699')
        '#000000'
    """
    if mode == 'bw':
        return '#000000'  # Pure black for BW mode
    return theme_color


def enhance_for_printing(image, mode='color'):
    """
    Enhance an image for optimal printing quality.
    
    In BW mode:
    - Increases contrast
    - Sharpens edges
    - Ensures high-contrast blacks and whites
    
    In color mode:
    - Slight contrast enhancement for clarity
    
    Args:
        image (PIL.Image): Input image
        mode (str): 'color' or 'bw'
    
    Returns:
        PIL.Image: Enhanced image
    """
    if mode == 'bw':
        # Convert to grayscale if not already
        if image.mode != 'L':
            image = image.convert('L')
        
        # Increase contrast significantly for BW printing
        contrast = ImageEnhance.Contrast(image)
        image = contrast.enhance(1.3)
        
        # Increase sharpness for crisp edges
        sharpness = ImageEnhance.Sharpness(image)
        image = sharpness.enhance(1.5)
        
        # Convert back to RGB for PDF compatibility
        image = image.convert('RGB')
    else:
        # Slight contrast boost for color printing
        contrast = ImageEnhance.Contrast(image)
        image = contrast.enhance(1.1)
    
    return image


def get_mode_suffix(mode='color'):
    """
    Get the file suffix for the given mode.
    
    Args:
        mode (str): 'color' or 'bw'
    
    Returns:
        str: File suffix ('_color' or '_bw')
    
    Example:
        >>> get_mode_suffix('color')
        '_color'
        >>> get_mode_suffix('bw')
        '_bw'
    """
    return '_color' if mode == 'color' else '_bw'


# Color constants for common uses
BLACK = '#000000'
WHITE = '#FFFFFF'
LIGHT_GRAY = '#CCCCCC'
DARK_GRAY = '#333333'
