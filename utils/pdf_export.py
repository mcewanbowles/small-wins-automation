"""
PDF export utilities for SPED resources.

Handles conversion of PIL images to high-quality PDF files at 300 DPI.
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image
import io
import os
from utils.config import DPI, PAGE_WIDTH, PAGE_HEIGHT


def save_image_as_pdf(image, output_path, title=None):
    """
    Save a PIL image as a PDF file at 300 DPI.
    
    Args:
        image: PIL Image to save
        output_path: Path to save PDF file
        title: Optional PDF title metadata
        
    Returns:
        str: Path to saved PDF file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Convert image to RGB if it's RGBA (for PDF compatibility)
    if image.mode == 'RGBA':
        # Create white background
        rgb_image = Image.new('RGB', image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
        image = rgb_image
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Create PDF canvas
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Set title if provided
    if title:
        c.setTitle(title)
    
    # Convert image to ReportLab format
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='PNG', dpi=(DPI, DPI))
    img_buffer.seek(0)
    img_reader = ImageReader(img_buffer)
    
    # Calculate dimensions (letter size is 8.5 x 11 inches)
    width_inches = 8.5
    height_inches = 11
    width_points = width_inches * 72  # ReportLab uses points (72 per inch)
    height_points = height_inches * 72
    
    # Draw image to fill entire page
    c.drawImage(img_reader, 0, 0, width=width_points, height=height_points)
    
    # Save PDF
    c.save()
    
    return output_path


def save_images_as_pdf(images, output_path, title=None):
    """
    Save multiple PIL images as a multi-page PDF file at 300 DPI.
    
    Args:
        images: List of PIL Images to save
        output_path: Path to save PDF file
        title: Optional PDF title metadata
        
    Returns:
        str: Path to saved PDF file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Create PDF canvas
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Set title if provided
    if title:
        c.setTitle(title)
    
    # Calculate dimensions
    width_inches = 8.5
    height_inches = 11
    width_points = width_inches * 72
    height_points = height_inches * 72
    
    # Add each image as a page
    for idx, image in enumerate(images):
        # Convert image to RGB if needed
        if image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to ReportLab format
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG', dpi=(DPI, DPI))
        img_buffer.seek(0)
        img_reader = ImageReader(img_buffer)
        
        # Draw image
        c.drawImage(img_reader, 0, 0, width=width_points, height=height_points)
        
        # Add new page if not the last image
        if idx < len(images) - 1:
            c.showPage()
    
    # Save PDF
    c.save()
    
    return output_path


def create_output_directory(base_dir='output'):
    """
    Create output directory for generated PDFs.
    
    Args:
        base_dir: Base directory name
        
    Returns:
        str: Path to output directory
    """
    os.makedirs(base_dir, exist_ok=True)
    return base_dir
