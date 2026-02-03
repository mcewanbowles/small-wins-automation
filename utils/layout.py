"""
Layout utilities for SPED-compliant resources.

Provides functions for creating consistent borders, footers, spacing,
and centering that follow SPED design principles.
"""

from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from utils.config import (
    PAGE_WIDTH, PAGE_HEIGHT, MARGINS, COLORS, 
    FOOTER_HEIGHT, FOOTER_TEXT, DPI
)
from utils.fonts import get_font_manager
import io


def create_page_canvas(width=PAGE_WIDTH, height=PAGE_HEIGHT, background_color=COLORS['background']):
    """
    Create a blank page canvas with SPED-compliant background.
    
    Args:
        width: Page width in pixels
        height: Page height in pixels
        background_color: RGB tuple for background
        
    Returns:
        PIL.Image: Blank page canvas
    """
    # Convert RGB to RGBA
    bg_color = background_color + (255,) if len(background_color) == 3 else background_color
    return Image.new('RGBA', (int(width), int(height)), bg_color)


def add_page_border(image, border_width=None, border_color=None):
    """
    Add a consistent border around the entire page.
    
    Args:
        image: PIL Image to add border to
        border_width: Width of border (uses config default if None)
        border_color: Color of border (uses config default if None)
        
    Returns:
        PIL.Image: Image with border
    """
    if border_width is None:
        border_width = MARGINS['border']
    if border_color is None:
        border_color = COLORS['border'] + (255,)
    
    width, height = image.size
    draw = ImageDraw.Draw(image)
    
    # Draw border rectangle
    for i in range(border_width):
        draw.rectangle(
            [i, i, width - 1 - i, height - 1 - i],
            outline=border_color
        )
    
    return image


def add_footer(image, footer_text=None, font_manager=None):
    """
    Add a consistent footer to the page with copyright and branding.
    
    Args:
        image: PIL Image to add footer to
        footer_text: Text for footer (uses config default if None)
        font_manager: FontManager instance (creates new if None)
        
    Returns:
        PIL.Image: Image with footer
    """
    if footer_text is None:
        footer_text = FOOTER_TEXT
    if font_manager is None:
        font_manager = get_font_manager()
    
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    # Calculate footer position - place near bottom, inside the border
    footer_y = height - FOOTER_HEIGHT
    
    # Try to load a smaller font for the copyright line
    try:
        # Try to load a truetype font at footer size
        from utils.config import FONT_SIZES
        font_size = int(FONT_SIZES['footer'])
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=font_size)
    except:
        try:
            # Fallback to a basic truetype font
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=12)
        except:
            # Ultimate fallback to default
            font = ImageFont.load_default()
    
    try:
        # Get text size using textbbox
        bbox = draw.textbbox((0, 0), footer_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text horizontally, position near bottom
        text_x = (width - text_width) // 2
        text_y = footer_y + (FOOTER_HEIGHT - text_height) // 2
        
        # Draw copyright text in dark gray, centered
        draw.text((text_x, text_y), footer_text, fill=COLORS['dark_gray'] + (255,), font=font)
    except Exception as e:
        # If font/text rendering fails, just skip the footer text
        pass
    
    return image


def create_card_background(width, height, border=True, border_width=None, border_color=None):
    """
    Create a card background with optional border.
    
    Args:
        width: Card width in pixels
        height: Card height in pixels
        border: Whether to add border
        border_width: Border width (uses config default if None)
        border_color: Border color (uses config default if None)
        
    Returns:
        PIL.Image: Card background
    """
    card = Image.new('RGBA', (int(width), int(height)), COLORS['white'] + (255,))
    
    if border:
        if border_width is None:
            border_width = MARGINS['border']
        if border_color is None:
            border_color = COLORS['border'] + (255,)
        
        draw = ImageDraw.Draw(card)
        for i in range(border_width):
            draw.rectangle(
                [i, i, width - 1 - i, height - 1 - i],
                outline=border_color
            )
    
    return card


def calculate_centered_position(container_width, container_height, item_width, item_height):
    """
    Calculate the position to center an item within a container.
    
    Args:
        container_width: Width of container
        container_height: Height of container
        item_width: Width of item to center
        item_height: Height of item to center
        
    Returns:
        tuple: (x, y) position to place item
    """
    x = (container_width - item_width) // 2
    y = (container_height - item_height) // 2
    return (x, y)


def calculate_grid_positions(grid_cols, grid_rows, cell_width, cell_height, 
                             container_width, container_height, spacing=0):
    """
    Calculate positions for a grid of items centered in a container.
    
    Args:
        grid_cols: Number of columns
        grid_rows: Number of rows
        cell_width: Width of each cell
        cell_height: Height of each cell
        container_width: Width of container
        container_height: Height of container
        spacing: Space between cells
        
    Returns:
        list: List of (x, y) positions for each grid cell
    """
    total_width = (cell_width * grid_cols) + (spacing * (grid_cols - 1))
    total_height = (cell_height * grid_rows) + (spacing * (grid_rows - 1))
    
    # Calculate starting position to center grid
    start_x = (container_width - total_width) // 2
    start_y = (container_height - total_height) // 2
    
    positions = []
    for row in range(grid_rows):
        for col in range(grid_cols):
            x = start_x + (col * (cell_width + spacing))
            y = start_y + (row * (cell_height + spacing))
            positions.append((x, y))
    
    return positions


def add_title_to_page(image, title_text, font_manager=None):
    """
    Add a title at the top of a page.
    
    Args:
        image: PIL Image to add title to
        title_text: Title text
        font_manager: FontManager instance
        
    Returns:
        PIL.Image: Image with title
    """
    if font_manager is None:
        font_manager = get_font_manager()
    
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    try:
        font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), title_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text at top with margin
        text_x = (width - text_width) // 2
        text_y = MARGINS['page']
        
        draw.text((text_x, text_y), title_text, fill=COLORS['black'] + (255,), font=font)
    except Exception:
        pass
    
    return image
