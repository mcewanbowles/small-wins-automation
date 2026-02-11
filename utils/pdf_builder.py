"""
PDF generation utilities for TpT Automation System

Creates PDFs at 300 DPI with proper page setup following Design Constitution.
Uses reportlab for PDF generation.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from pathlib import Path
from typing import Tuple, Optional


# Page constants from Design Constitution
PAGE_WIDTH, PAGE_HEIGHT = letter  # 8.5" × 11" (US Letter)
DPI = 300  # Required for print quality
MARGIN = 0.5 * inch  # 0.5" margins on all sides

# Usable area after margins
USABLE_WIDTH = PAGE_WIDTH - (2 * MARGIN)
USABLE_HEIGHT = PAGE_HEIGHT - (2 * MARGIN)


class PDFBuilder:
    """
    Builder class for creating TpT resource PDFs.
    
    Handles page setup, margins, and 300 DPI output following Design Constitution.
    """
    
    def __init__(self, output_path: Path, title: str = "TpT Resource"):
        """
        Initialize PDF builder.
        
        Args:
            output_path: Path where PDF will be saved
            title: PDF document title
        """
        self.output_path = output_path
        self.canvas = canvas.Canvas(str(output_path), pagesize=letter)
        self.canvas.setTitle(title)
        
        # Set high quality
        self.canvas.setPageCompression(1)
        
        self.current_page = 0
    
    def add_page(self):
        """Add a new page to the PDF."""
        if self.current_page > 0:
            self.canvas.showPage()
        self.current_page += 1
    
    def get_canvas(self) -> canvas.Canvas:
        """Get the underlying reportlab canvas for direct drawing."""
        return self.canvas
    
    def get_usable_area(self) -> Tuple[float, float, float, float]:
        """
        Get the usable area coordinates (accounting for margins).
        
        Returns:
            Tuple of (x, y, width, height) for the usable area
        """
        return (MARGIN, MARGIN, USABLE_WIDTH, USABLE_HEIGHT)
    
    def draw_border(self, x: float, y: float, width: float, height: float,
                   color: Tuple[float, float, float] = (0, 0, 0),
                   thickness: float = 1.0, rounded: bool = True,
                   corner_radius: float = 0.12 * inch):
        """
        Draw a border (optionally rounded).
        
        Args:
            x, y: Bottom-left corner coordinates
            width, height: Dimensions of the border
            color: RGB color tuple (0-1 range)
            thickness: Line thickness in points
            rounded: Whether to use rounded corners
            corner_radius: Radius for rounded corners (default 0.12" per specs)
        """
        c = self.canvas
        c.setStrokeColorRGB(*color)
        c.setLineWidth(thickness)
        
        if rounded:
            c.roundRect(x, y, width, height, corner_radius)
        else:
            c.rect(x, y, width, height)
    
    def draw_text(self, text: str, x: float, y: float,
                 font_name: str = "Helvetica", font_size: float = 12,
                 color: Tuple[float, float, float] = (0, 0, 0),
                 align: str = "left"):
        """
        Draw text on the canvas.
        
        Args:
            text: Text to draw
            x, y: Position coordinates
            font_name: Font name
            font_size: Font size in points
            color: RGB color tuple (0-1 range)
            align: Text alignment ("left", "center", "right")
        """
        c = self.canvas
        c.setFont(font_name, font_size)
        c.setFillColorRGB(*color)
        
        if align == "center":
            c.drawCentredString(x, y, text)
        elif align == "right":
            c.drawRightString(x, y, text)
        else:
            c.drawString(x, y, text)
    
    def draw_image(self, image_path: Path, x: float, y: float,
                  width: Optional[float] = None, height: Optional[float] = None,
                  preserve_aspect: bool = True):
        """
        Draw an image on the canvas.
        
        Args:
            image_path: Path to the image file
            x, y: Bottom-left corner coordinates
            width: Image width (None to use original)
            height: Image height (None to use original)
            preserve_aspect: Whether to preserve aspect ratio
        """
        c = self.canvas
        
        if width is not None and height is not None and preserve_aspect:
            c.drawImage(str(image_path), x, y, width, height, 
                       preserveAspectRatio=True, mask='auto')
        elif width is not None and height is not None:
            c.drawImage(str(image_path), x, y, width, height, mask='auto')
        else:
            c.drawImage(str(image_path), x, y, mask='auto')
    
    def save(self):
        """Save and close the PDF file."""
        self.canvas.save()
        print(f"✓ PDF saved: {self.output_path}")


def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """
    Convert hex color code to RGB tuple (0-1 range for reportlab).
    
    Args:
        hex_color: Hex color code (e.g., "#1E3A5F" or "1E3A5F")
        
    Returns:
        RGB tuple with values from 0 to 1
    """
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB (0-255)
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Convert to 0-1 range
    return (r / 255.0, g / 255.0, b / 255.0)


def inches_to_points(inches: float) -> float:
    """Convert inches to points (72 points = 1 inch)."""
    return inches * 72.0


def points_to_inches(points: float) -> float:
    """Convert points to inches."""
    return points / 72.0
