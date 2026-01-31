"""
SPED-specific layout utilities for creating accessible educational materials.
Implements consistent borders, footers, high contrast, and predictable structure.
"""

from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional
from .image_utils import (
    DPI, get_font, BLACK, WHITE, DARK_GRAY, LIGHT_GRAY,
    LARGE_FONT_SIZE, SMALL_FONT_SIZE, inches_to_pixels
)


class SPEDLayout:
    """
    Base class for SPED-compliant layouts.
    Ensures high contrast, large clear fonts, and predictable structure.
    """
    
    # Standard page sizes at 300 DPI
    LETTER_WIDTH = inches_to_pixels(8.5)
    LETTER_HEIGHT = inches_to_pixels(11)
    HALF_LETTER_WIDTH = inches_to_pixels(8.5)
    HALF_LETTER_HEIGHT = inches_to_pixels(5.5)
    
    # Standard margins
    MARGIN = inches_to_pixels(0.5)
    BORDER_WIDTH = inches_to_pixels(0.1)
    
    def __init__(self, width: int = LETTER_WIDTH, height: int = LETTER_HEIGHT,
                 background_color: Tuple[int, int, int] = WHITE,
                 border_color: Tuple[int, int, int] = BLACK,
                 border_width: int = None):
        """
        Initialize a SPED layout.
        
        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
            background_color: Background color
            border_color: Border color
            border_width: Border width in pixels
        """
        self.width = width
        self.height = height
        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width or self.BORDER_WIDTH
        
        # Create canvas
        self.canvas = Image.new('RGB', (width, height), background_color)
        self.draw = ImageDraw.Draw(self.canvas)
        
    def add_border(self, color: Optional[Tuple[int, int, int]] = None,
                   width: Optional[int] = None):
        """
        Add a border around the entire canvas.
        
        Args:
            color: Border color (uses default if None)
            width: Border width in pixels (uses default if None)
        """
        color = color or self.border_color
        width = width or self.border_width
        
        # Draw rectangle border
        self.draw.rectangle(
            [0, 0, self.width - 1, self.height - 1],
            outline=color,
            width=width
        )
    
    def add_footer(self, text: str, 
                   font_size: int = SMALL_FONT_SIZE,
                   color: Tuple[int, int, int] = DARK_GRAY):
        """
        Add a footer with text at the bottom of the page.
        
        Args:
            text: Footer text
            font_size: Font size for footer
            color: Text color
        """
        font = get_font(font_size)
        
        # Calculate text position (centered at bottom)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.width - text_width) // 2
        y = self.height - text_height - self.MARGIN // 2
        
        self.draw.text((x, y), text, fill=color, font=font)
    
    def add_title(self, text: str,
                  font_size: int = LARGE_FONT_SIZE,
                  color: Tuple[int, int, int] = BLACK,
                  y_position: Optional[int] = None):
        """
        Add a centered title at the top of the page.
        
        Args:
            text: Title text
            font_size: Font size for title
            color: Text color
            y_position: Y position (uses default margin if None)
        """
        font = get_font(font_size, bold=True)
        
        # Calculate text position
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        x = (self.width - text_width) // 2
        y = y_position if y_position is not None else self.MARGIN
        
        self.draw.text((x, y), text, fill=color, font=font)
    
    def add_grid(self, rows: int, cols: int,
                 margin: Optional[int] = None,
                 grid_color: Tuple[int, int, int] = BLACK,
                 line_width: int = 3) -> list:
        """
        Add a grid layout and return cell coordinates.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            margin: Margin from edges (uses default if None)
            grid_color: Color of grid lines
            line_width: Width of grid lines
            
        Returns:
            List of tuples (x, y, width, height) for each cell
        """
        margin = margin or self.MARGIN
        
        # Calculate grid dimensions
        grid_width = self.width - 2 * margin
        grid_height = self.height - 2 * margin
        
        cell_width = grid_width // cols
        cell_height = grid_height // rows
        
        cells = []
        
        # Draw grid lines and collect cell coordinates
        for row in range(rows + 1):
            y = margin + row * cell_height
            self.draw.line(
                [(margin, y), (margin + grid_width, y)],
                fill=grid_color,
                width=line_width
            )
        
        for col in range(cols + 1):
            x = margin + col * cell_width
            self.draw.line(
                [(x, margin), (x, margin + grid_height)],
                fill=grid_color,
                width=line_width
            )
        
        # Collect cell coordinates
        for row in range(rows):
            for col in range(cols):
                x = margin + col * cell_width
                y = margin + row * cell_height
                cells.append((x, y, cell_width, cell_height))
        
        return cells
    
    def paste_image(self, image: Image.Image, x: int, y: int,
                   centered: bool = False):
        """
        Paste an image onto the canvas.
        
        Args:
            image: PIL Image to paste
            x: X coordinate (or center x if centered=True)
            y: Y coordinate (or center y if centered=True)
            centered: Whether to center the image at (x, y)
        """
        if centered:
            x = x - image.width // 2
            y = y - image.height // 2
        
        # Handle transparency
        if image.mode == 'RGBA':
            self.canvas.paste(image, (x, y), image)
        else:
            self.canvas.paste(image, (x, y))
    
    def save(self, filename: str, dpi: Tuple[int, int] = (DPI, DPI)):
        """
        Save the canvas to a file.
        
        Args:
            filename: Output filename
            dpi: DPI tuple (x, y)
        """
        self.canvas.save(filename, dpi=dpi)
        print(f"Saved: {filename}")
    
    def get_canvas(self) -> Image.Image:
        """Get the canvas image."""
        return self.canvas
