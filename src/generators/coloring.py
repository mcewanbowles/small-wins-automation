"""
Coloring Generator
Creates simple coloring pages with outlines.
"""

from PIL import Image, ImageFilter, ImageOps
from typing import Optional
from ..utils import (
    SPEDLayout, get_font, load_image, create_placeholder_image,
    BLACK, WHITE, LARGE_FONT_SIZE, inches_to_pixels
)


def generate_coloring_page(image_filename: str,
                          image_folder: str = 'images',
                          title: str = None,
                          edge_width: int = 3,
                          output_path: str = None) -> Image.Image:
    """
    Generate a coloring page from an image by converting to outline.
    
    Args:
        image_filename: Image file to convert to coloring page
        image_folder: Folder to load image from
        title: Optional title for the page
        edge_width: Width of edges (1-10, higher = thicker lines)
        output_path: Path to save the coloring page
        
    Returns:
        PIL Image of coloring page
    """
    # Create layout
    layout = SPEDLayout()
    
    # Add title if provided
    if title:
        layout.add_title(title, font_size=LARGE_FONT_SIZE, color=BLACK)
        top_margin = inches_to_pixels(1.5)
    else:
        top_margin = inches_to_pixels(0.75)
    
    # Add border
    layout.add_border()
    
    # Load image
    image = load_image(image_filename, image_folder)
    if not image:
        # Create placeholder
        image = create_placeholder_image(
            inches_to_pixels(5),
            inches_to_pixels(5),
            "No Image"
        )
    
    # Convert to outline
    outline_image = _create_outline(image, edge_width)
    
    # Calculate size to fit on page
    side_margin = inches_to_pixels(0.75)
    bottom_margin = inches_to_pixels(0.75)
    
    max_width = layout.width - 2 * side_margin
    max_height = layout.height - top_margin - bottom_margin
    
    # Resize outline to fit
    outline_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    
    # Center the image
    x = (layout.width - outline_image.width) // 2
    y = top_margin + (max_height - outline_image.height) // 2
    
    # Paste the outline
    layout.paste_image(outline_image, x, y)
    
    # Add footer
    layout.add_footer("© Small Wins Studio")
    
    # Save if output path provided
    if output_path:
        layout.save(output_path)
    
    return layout.get_canvas()


def _create_outline(image: Image.Image, edge_width: int = 3) -> Image.Image:
    """
    Convert an image to a simple outline suitable for coloring.
    
    Args:
        image: PIL Image to convert
        edge_width: Edge detection intensity
        
    Returns:
        Outline image
    """
    # Convert to grayscale
    gray = image.convert('L')
    
    # Find edges using filter
    edges = gray.filter(ImageFilter.FIND_EDGES)
    
    # Enhance edges
    edges = edges.filter(ImageFilter.EDGE_ENHANCE_MORE)
    
    # Invert so we have black lines on white
    edges = ImageOps.invert(edges)
    
    # Threshold to create clean black and white
    threshold = 200
    edges = edges.point(lambda x: 255 if x > threshold else 0, mode='1')
    
    # Convert back to RGB for consistency
    edges = edges.convert('RGB')
    
    # Optionally thicken lines
    if edge_width > 1:
        from PIL import ImageFilter
        for _ in range(edge_width - 1):
            edges = edges.filter(ImageFilter.MinFilter(3))
    
    return edges


def generate_coloring_set(image_filenames: list,
                         image_folder: str = 'images',
                         titles: Optional[list] = None,
                         output_dir: str = 'outputs') -> list:
    """
    Generate a set of coloring pages.
    
    Args:
        image_filenames: List of image files
        image_folder: Folder to load images from
        titles: Optional list of titles (same length as image_filenames)
        output_dir: Directory to save coloring pages
        
    Returns:
        List of output filenames
    """
    from ..utils import get_project_root
    
    output_files = []
    output_path = get_project_root() / output_dir
    output_path.mkdir(exist_ok=True)
    
    if titles is None:
        titles = [None] * len(image_filenames)
    
    for i, image_file in enumerate(image_filenames):
        filename = f"coloring_page_{i+1}.png"
        filepath = output_path / filename
        
        title = titles[i] if i < len(titles) else None
        
        generate_coloring_page(
            image_file,
            image_folder=image_folder,
            title=title,
            output_path=str(filepath)
        )
        
        output_files.append(str(filepath))
    
    return output_files
