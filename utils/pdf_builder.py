"""
PDF Builder Utility

High-level PDF building functions for SPED resources.
Extends pdf_export.py with additional PDF construction utilities.
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image
import io
import os
from utils.config import DPI
from utils.pdf_export import save_image_as_pdf, save_images_as_pdf


class PDFBuilder:
    """
    High-level PDF builder for creating multi-page SPED resources.
    """
    
    def __init__(self, output_path, title=None, page_size=letter):
        """
        Initialize PDF builder.
        
        Args:
            output_path: Path where PDF will be saved
            title: PDF document title
            page_size: Page size (default: letter)
        """
        self.output_path = output_path
        self.title = title
        self.page_size = page_size
        self.pages = []
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    def add_page(self, image):
        """
        Add a page to the PDF.
        
        Args:
            image: PIL Image representing the page
        """
        self.pages.append(image)
    
    def add_pages(self, images):
        """
        Add multiple pages to the PDF.
        
        Args:
            images: List of PIL Images
        """
        self.pages.extend(images)
    
    def build(self):
        """
        Build and save the PDF file.
        
        Returns:
            str: Path to saved PDF
        """
        if not self.pages:
            raise ValueError("No pages added to PDF")
        
        save_images_as_pdf(self.pages, self.output_path, title=self.title)
        return self.output_path
    
    def get_page_count(self):
        """Get number of pages in the PDF."""
        return len(self.pages)
    
    def clear_pages(self):
        """Clear all pages from the builder."""
        self.pages = []


def create_single_page_pdf(image, output_path, title=None):
    """
    Quickly create a single-page PDF.
    
    Args:
        image: PIL Image for the page
        output_path: Path to save PDF
        title: PDF title
        
    Returns:
        str: Path to saved PDF
    """
    return save_image_as_pdf(image, output_path, title)


def create_multi_page_pdf(images, output_path, title=None):
    """
    Quickly create a multi-page PDF.
    
    Args:
        images: List of PIL Images
        output_path: Path to save PDF
        title: PDF title
        
    Returns:
        str: Path to saved PDF
    """
    return save_images_as_pdf(images, output_path, title)


def merge_pdfs_from_images(image_groups, output_path, title=None):
    """
    Create a PDF by merging multiple groups of images.
    
    Args:
        image_groups: List of lists of PIL Images
        output_path: Path to save PDF
        title: PDF title
        
    Returns:
        str: Path to saved PDF
    """
    all_images = []
    for group in image_groups:
        all_images.extend(group)
    
    return save_images_as_pdf(all_images, output_path, title)


def create_booklet_pdf(pages, output_path, title=None):
    """
    Create a booklet-style PDF (pages arranged for duplex printing).
    
    Args:
        pages: List of PIL Images
        output_path: Path to save PDF
        title: PDF title
        
    Returns:
        str: Path to saved PDF
    """
    # For booklet: ensure even number of pages
    if len(pages) % 2 != 0:
        # Add blank page if odd number
        blank = Image.new('RGB', pages[0].size, (255, 255, 255))
        pages.append(blank)
    
    return save_images_as_pdf(pages, output_path, title)
