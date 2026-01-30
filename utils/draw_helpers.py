"""
Drawing Helper Functions

Reusable drawing utilities for SPED resource generators.
Provides modular functions for:
- Grid cell calculations
- Image scaling and fitting
- Card background styling
- Text fitting and rendering
- Page numbering
- Copyright footers
"""

from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Dict, Optional
from utils.config import COLORS, FONT_SIZES, MARGINS, DPI


def calculate_cell_rect(page_width: int, page_height: int, rows: int, cols: int,
                        padding: int = 20, margin: int = 50, 
                        footer_height: int = 60) -> List[Tuple[int, int, int, int]]:
    """
    Calculate bounding boxes for a grid of cells on a page.
    
    Args:
        page_width: Total page width in pixels
        page_height: Total page height in pixels
        rows: Number of rows in grid
        cols: Number of columns in grid
        padding: Space between cells in pixels
        margin: Page margin in pixels
        footer_height: Reserved space at bottom for footer
        
    Returns:
        List of (x1, y1, x2, y2) tuples representing cell bounding boxes
    """
    # Calculate available space
    available_width = page_width - (2 * margin)
    available_height = page_height - (2 * margin) - footer_height
    
    # Calculate cell dimensions including padding
    cell_width_with_padding = available_width / cols
    cell_height_with_padding = available_height / rows
    
    # Actual cell dimensions (subtracting padding)
    cell_width = cell_width_with_padding - padding
    cell_height = cell_height_with_padding - padding
    
    cells = []
    for row in range(rows):
        for col in range(cols):
            # Calculate cell position
            x1 = margin + (col * cell_width_with_padding) + (padding // 2)
            y1 = margin + (row * cell_height_with_padding) + (padding // 2)
            x2 = x1 + cell_width
            y2 = y1 + cell_height
            
            cells.append((int(x1), int(y1), int(x2), int(y2)))
    
    return cells


def scale_image_to_fit(image: Image.Image, cell_rect: Tuple[int, int, int, int],
                       padding: int = 5) -> Tuple[Image.Image, int, int]:
    """
    Scale an image proportionally to fit within a cell with minimal padding.
    
    Args:
        image: PIL Image to scale
        cell_rect: (x1, y1, x2, y2) bounding box of the cell
        padding: Minimal padding around image in pixels (default 5)
        
    Returns:
        Tuple of (scaled_image, center_x, center_y) for positioning
    """
    x1, y1, x2, y2 = cell_rect
    cell_width = x2 - x1
    cell_height = y2 - y1
    
    # Calculate maximum image dimensions
    max_width = cell_width - (2 * padding)
    max_height = cell_height - (2 * padding)
    
    # Get original dimensions
    orig_width, orig_height = image.size
    
    # Calculate scaling factor (maintain aspect ratio)
    width_ratio = max_width / orig_width
    height_ratio = max_height / orig_height
    scale_factor = min(width_ratio, height_ratio)
    
    # Calculate new dimensions
    new_width = int(orig_width * scale_factor)
    new_height = int(orig_height * scale_factor)
    
    # Scale image
    scaled = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Calculate centered position within cell - ensure integers
    center_x = int(x1 + (cell_width - new_width) // 2)
    center_y = int(y1 + (cell_height - new_height) // 2)
    
    return scaled, center_x, center_y


def draw_card_background(draw: ImageDraw.ImageDraw, cell_rect: Tuple[int, int, int, int],
                         style: Optional[Dict] = None) -> None:
    """
    Draw a styled card background with optional border, radius, and shadow.
    
    Args:
        draw: ImageDraw object to draw on
        cell_rect: (x1, y1, x2, y2) bounding box for the card
        style: Optional dict with 'border_width', 'corner_radius', 'shadow', 'fill_color'
    """
    if style is None:
        style = {
            'border_width': 2,
            'corner_radius': 10,
            'shadow': False,
            'fill_color': COLORS['white']
        }
    
    x1, y1, x2, y2 = cell_rect
    border_width = style.get('border_width', 2)
    corner_radius = style.get('corner_radius', 10)
    shadow = style.get('shadow', False)
    fill_color = style.get('fill_color', COLORS['white'])
    
    # Draw shadow if requested
    if shadow:
        shadow_offset = 3
        shadow_rect = (x1 + shadow_offset, y1 + shadow_offset,
                      x2 + shadow_offset, y2 + shadow_offset)
        draw.rounded_rectangle(
            shadow_rect,
            radius=corner_radius,
            fill=(200, 200, 200, 100),
            outline=None
        )
    
    # Draw card background
    draw.rounded_rectangle(
        cell_rect,
        radius=corner_radius,
        fill=fill_color + (255,),
        outline=COLORS['black'] + (255,),
        width=border_width
    )


def fit_text_to_width(text: str, font_path: str, initial_size: int,
                     max_width: int, min_size: int = 10) -> ImageFont.FreeTypeFont:
    """
    Auto-shrink font size to fit text within a maximum width.
    
    Args:
        text: Text to fit
        font_path: Path to font file
        initial_size: Starting font size
        max_width: Maximum allowed width in pixels
        min_size: Minimum font size to try
        
    Returns:
        ImageFont at appropriate size
    """
    current_size = initial_size
    
    while current_size >= min_size:
        try:
            font = ImageFont.truetype(font_path, current_size)
        except:
            # Fallback to default
            return ImageFont.load_default()
        
        # Create temp draw to measure text
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            return font
        
        current_size -= 2
    
    # Return minimum size font
    try:
        return ImageFont.truetype(font_path, min_size)
    except:
        return ImageFont.load_default()


def draw_page_number(draw: ImageDraw.ImageDraw, page_number: int, total_pages: int,
                     page_width: int, page_height: int, margin: int = 50,
                     font_size: int = 10) -> None:
    """
    Draw page number in bottom-right corner inside the border.
    
    Args:
        draw: ImageDraw object to draw on
        page_number: Current page number (1-indexed)
        total_pages: Total number of pages
        page_width: Page width in pixels
        page_height: Page height in pixels
        margin: Page margin in pixels
        font_size: Font size for page number
    """
    text = f"Page {page_number} of {total_pages}"
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Position in bottom-right, inside margin
    x = page_width - margin - text_width - 10
    y = page_height - margin - text_height - 10
    
    draw.text((x, y), text, fill=COLORS['dark_gray'] + (255,), font=font)


def draw_copyright_footer(draw: ImageDraw.ImageDraw, page_width: int, page_height: int,
                          margin: int = 50, font_size: int = 9,
                          copyright_text: Optional[str] = None) -> None:
    """
    Draw copyright and branding line at bottom-center of page.
    
    Args:
        draw: ImageDraw object to draw on
        page_width: Page width in pixels
        page_height: Page height in pixels
        margin: Page margin in pixels
        font_size: Font size for copyright text (8-10pt recommended)
        copyright_text: Custom copyright text (uses default if None)
    """
    if copyright_text is None:
        copyright_text = "© 2026 Small Wins Studio • PCS® symbols used with active PCS Maker Personal Licence — For classroom use only"
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Measure text
    bbox = draw.textbbox((0, 0), copyright_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center horizontally, near bottom
    x = (page_width - text_width) // 2
    y = page_height - margin - text_height - 5
    
    draw.text((x, y), copyright_text, fill=COLORS['dark_gray'] + (255,), font=font)


def draw_text_centered_in_rect(draw: ImageDraw.ImageDraw, text: str,
                               rect: Tuple[int, int, int, int],
                               font_size: int = 24, color: Tuple = None) -> None:
    """
    Draw text centered within a rectangle with automatic font sizing.
    
    Args:
        draw: ImageDraw object to draw on
        text: Text to draw
        rect: (x1, y1, x2, y2) bounding rectangle
        font_size: Initial font size (will be reduced if needed)
        color: Text color (defaults to black)
    """
    if color is None:
        color = COLORS['black'] + (255,)
    
    x1, y1, x2, y2 = rect
    rect_width = x2 - x1
    rect_height = y2 - y1
    
    # Fit text to 80% of rectangle width
    max_width = int(rect_width * 0.8)
    font = fit_text_to_width(
        text,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        font_size,
        max_width
    )
    
    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center in rectangle
    text_x = x1 + (rect_width - text_width) // 2
    text_y = y1 + (rect_height - text_height) // 2
    
    draw.text((text_x, text_y), text, fill=color, font=font)


def create_placeholder_image(width: int, height: int, text: str = "Missing Image") -> Image.Image:
    """
    Create a consistent placeholder image for missing resources.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        text: Text to display on placeholder
        
    Returns:
        PIL.Image: Placeholder image
    """
    # Create gray background
    img = Image.new('RGBA', (width, height), (220, 220, 220, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw border
    border_width = max(2, min(width, height) // 100)
    draw.rectangle(
        [border_width, border_width, width - border_width, height - border_width],
        outline=(150, 150, 150, 255),
        width=border_width
    )
    
    # Draw text centered
    try:
        font_size = min(width, height) // 10
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill=(100, 100, 100, 255), font=font)
    
    return img
