"""
Text Renderer Utility

Provides text rendering functions for SPED resources with accessibility considerations.
"""

from PIL import Image, ImageDraw, ImageFont
from utils.config import COLORS, FONT_SIZES


def render_text_on_image(image, text, position, font_size=24, font_color=(0, 0, 0, 255),
                         font_weight='normal', align='left'):
    """
    Render text on an image.
    
    Args:
        image: PIL Image to draw on
        text: Text string to render
        position: Tuple of (x, y) coordinates
        font_size: Size of font in points
        font_color: RGBA color tuple
        font_weight: 'normal' or 'bold'
        align: 'left', 'center', or 'right'
        
    Returns:
        PIL.Image: Image with text rendered
    """
    draw = ImageDraw.Draw(image)
    
    try:
        # Try to use a basic font
        font = ImageFont.load_default()
    except:
        font = None
    
    # Get text dimensions
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        text_width = len(text) * 8  # Rough estimate
        text_height = 16
    
    # Adjust position based on alignment
    x, y = position
    if align == 'center':
        x = x - (text_width // 2)
    elif align == 'right':
        x = x - text_width
    
    # Draw text
    draw.text((x, y), text, fill=font_color, font=font)
    
    return image


def create_text_image(text, width, height, font_size=24, font_color=(0, 0, 0, 255),
                      background_color=(255, 255, 255, 255), align='center', valign='middle'):
    """
    Create an image containing text.
    
    Args:
        text: Text to render
        width: Image width
        height: Image height
        font_size: Font size in points
        font_color: RGBA color for text
        background_color: RGBA color for background
        align: Horizontal alignment ('left', 'center', 'right')
        valign: Vertical alignment ('top', 'middle', 'bottom')
        
    Returns:
        PIL.Image: Image with text
    """
    image = Image.new('RGBA', (int(width), int(height)), background_color)
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # Get text dimensions
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        text_width = len(text) * 8
        text_height = 16
    
    # Calculate position
    if align == 'left':
        x = 10
    elif align == 'center':
        x = (width - text_width) // 2
    else:  # right
        x = width - text_width - 10
    
    if valign == 'top':
        y = 10
    elif valign == 'middle':
        y = (height - text_height) // 2
    else:  # bottom
        y = height - text_height - 10
    
    draw.text((x, y), text, fill=font_color, font=font)
    
    return image


def create_label(text, width=200, height=60, font_size=18):
    """
    Create a simple text label.
    
    Args:
        text: Label text
        width: Label width
        height: Label height
        font_size: Font size
        
    Returns:
        PIL.Image: Label image
    """
    return create_text_image(text, width, height, font_size,
                            font_color=COLORS['black'] + (255,),
                            background_color=COLORS['white'] + (255,))


def wrap_text(text, max_width, font=None):
    """
    Wrap text to fit within a maximum width.
    
    Args:
        text: Text to wrap
        max_width: Maximum width in pixels
        font: PIL Font object (uses default if None)
        
    Returns:
        list: List of text lines
    """
    if font is None:
        try:
            font = ImageFont.load_default()
        except:
            # Fallback: simple character-based wrapping
            chars_per_line = max_width // 8
            words = text.split()
            lines = []
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= chars_per_line:
                    current_line.append(word)
                    current_length += len(word) + 1
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return lines
    
    # Use font to calculate actual text width
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def render_multiline_text(image, text, position, max_width, font_size=24,
                          font_color=(0, 0, 0, 255), line_spacing=5):
    """
    Render text with automatic line wrapping.
    
    Args:
        image: PIL Image to draw on
        text: Text to render
        position: Starting (x, y) position
        max_width: Maximum width for text
        font_size: Font size
        font_color: Text color
        line_spacing: Space between lines
        
    Returns:
        PIL.Image: Image with text rendered
    """
    lines = wrap_text(text, max_width)
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    x, y = position
    line_height = font_size + line_spacing
    
    for line in lines:
        draw.text((x, y), line, fill=font_color, font=font)
        y += line_height
    
    return image
