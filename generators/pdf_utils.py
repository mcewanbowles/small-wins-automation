"""PDF generation utilities for page layouts"""
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
from pathlib import Path


class PageLayout:
    """Helper class for creating page layouts according to Design Constitution"""
    
    def __init__(self, pdf_canvas, page_width, page_height, margin, border_radius):
        self.canvas = pdf_canvas
        self.page_width = page_width
        self.page_height = page_height
        self.margin = margin
        self.border_radius = border_radius
        
    def draw_page_border(self, stroke_width=2):
        """Draw the page border with rounded corners"""
        self.canvas.setStrokeColor(HexColor('#000000'))
        self.canvas.setLineWidth(stroke_width)
        self.canvas.setFillColor(HexColor('#FFFFFF'))
        
        # Draw rounded rectangle for border
        self.canvas.roundRect(
            self.margin,
            self.margin,
            self.page_width - 2 * self.margin,
            self.page_height - 2 * self.margin,
            self.border_radius,
            stroke=1,
            fill=0
        )
    
    def draw_header(self, pack_code: str, page_num: int, total_pages: int):
        """Draw header above border (pack code, page numbers, branding)"""
        header_y = self.page_height - self.margin + 15
        
        self.canvas.setFillColor(HexColor('#666666'))
        self.canvas.setFont('Helvetica', 8)
        
        # Pack code (left)
        self.canvas.drawString(self.margin, header_y, pack_code)
        
        # Page number (right)
        page_text = f"Page {page_num}/{total_pages}"
        page_width = self.canvas.stringWidth(page_text, 'Helvetica', 8)
        self.canvas.drawString(self.page_width - self.margin - page_width, header_y, page_text)
        
        # "Small Wins Studio" (center)
        self.canvas.setFillColor(HexColor('#999999'))
        self.canvas.setFont('Helvetica', 10)
        branding = "Small Wins Studio"
        branding_width = self.canvas.stringWidth(branding, 'Helvetica', 10)
        self.canvas.drawString((self.page_width - branding_width) / 2, header_y, branding)
    
    def draw_footer(self, year: int = 2025):
        """Draw footer inside border"""
        footer_y = self.margin + 20
        
        self.canvas.setFillColor(HexColor('#999999'))
        self.canvas.setFont('Helvetica', 8)
        
        footer_text = f"© {year} Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
        footer_width = self.canvas.stringWidth(footer_text, 'Helvetica', 8)
        self.canvas.drawString((self.page_width - footer_width) / 2, footer_y, footer_text)
    
    def draw_accent_stripe(self, title: str, subtitle: str, level_color: str, stripe_height: float, stripe_padding: float):
        """Draw the accent stripe with title and subtitle"""
        # Calculate stripe position (top of content area, inside border)
        stripe_y = self.page_height - self.margin - stripe_padding - stripe_height
        stripe_x = self.margin + stripe_padding
        stripe_width = self.page_width - 2 * (self.margin + stripe_padding)
        
        # Draw the stripe background
        self.canvas.setFillColor(HexColor(level_color))
        self.canvas.roundRect(
            stripe_x,
            stripe_y,
            stripe_width,
            stripe_height,
            self.border_radius,
            stroke=0,
            fill=1
        )
        
        # Draw title (centered)
        self.canvas.setFillColor(HexColor('#001F3F'))  # Navy
        self.canvas.setFont('Helvetica-Bold', 18)
        title_width = self.canvas.stringWidth(title, 'Helvetica-Bold', 18)
        title_x = stripe_x + (stripe_width - title_width) / 2
        title_y = stripe_y + stripe_height / 2 + 8
        self.canvas.drawString(title_x, title_y, title)
        
        # Draw subtitle (centered, below title)
        self.canvas.setFillColor(HexColor('#333333'))  # Dark grey
        self.canvas.setFont('Helvetica', 12)
        subtitle_width = self.canvas.stringWidth(subtitle, 'Helvetica', 12)
        subtitle_x = stripe_x + (stripe_width - subtitle_width) / 2
        subtitle_y = stripe_y + stripe_height / 2 - 12
        self.canvas.drawString(subtitle_x, subtitle_y, subtitle)
    
    def draw_image(self, image_path: Path, x: float, y: float, width: float, height: float, 
                   preserve_aspect: bool = True, center: bool = True):
        """Draw an image on the canvas
        
        Args:
            image_path: Path to the image file
            x, y: Position (bottom-left corner if not centered)
            width, height: Bounding box size
            preserve_aspect: Whether to preserve aspect ratio
            center: Whether to center image in bounding box
        """
        try:
            img = Image.open(image_path)
            img_width, img_height = img.size
            
            if preserve_aspect:
                # Calculate scaling to fit in bounding box
                scale = min(width / img_width, height / img_height)
                new_width = img_width * scale
                new_height = img_height * scale
                
                if center:
                    # Center in bounding box
                    x = x + (width - new_width) / 2
                    y = y + (height - new_height) / 2
                
                width = new_width
                height = new_height
            
            self.canvas.drawImage(
                str(image_path),
                x, y,
                width=width,
                height=height,
                preserveAspectRatio=preserve_aspect,
                mask='auto'
            )
        except Exception as e:
            print(f"Error drawing image {image_path}: {e}")
    
    def draw_rounded_box(self, x: float, y: float, width: float, height: float, 
                        corner_radius: float, stroke_color: str = '#000000', 
                        fill_color: str = None, stroke_width: float = 2):
        """Draw a rounded rectangle box"""
        self.canvas.setStrokeColor(HexColor(stroke_color))
        self.canvas.setLineWidth(stroke_width)
        
        if fill_color:
            self.canvas.setFillColor(HexColor(fill_color))
            self.canvas.roundRect(x, y, width, height, corner_radius, stroke=1, fill=1)
        else:
            self.canvas.roundRect(x, y, width, height, corner_radius, stroke=1, fill=0)
    
    def draw_velcro_dot(self, center_x: float, center_y: float, radius: float = 8):
        """Draw a velcro dot (small filled circle)"""
        self.canvas.setFillColor(HexColor('#666666'))
        self.canvas.circle(center_x, center_y, radius, stroke=0, fill=1)


def convert_to_grayscale(image_path: Path, output_path: Path):
    """Convert an image to grayscale"""
    img = Image.open(image_path)
    gray_img = img.convert('L')
    gray_img.save(output_path)
