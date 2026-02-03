"""
Labels Generator
Creates simple labels for classroom organization and identification.
"""

from PIL import Image, ImageDraw
from typing import List, Tuple, Optional
from ..utils import (
    SPEDLayout, get_font, load_image, create_placeholder_image,
    scale_image_to_fit, BLACK, WHITE, LARGE_FONT_SIZE,
    DEFAULT_FONT_SIZE, inches_to_pixels, DPI
)


def generate_label(text: str,
                  image_filename: Optional[str] = None,
                  image_folder: str = 'images',
                  size: Tuple[int, int] = None,
                  border_color: Tuple[int, int, int] = BLACK,
                  background_color: Tuple[int, int, int] = WHITE,
                  output_path: str = None) -> Image.Image:
    """
    Generate a single label.
    
    Args:
        text: Label text
        image_filename: Optional image for the label
        image_folder: Folder to load image from
        size: Label size as (width, height) in pixels, or None for default
        border_color: Border color
        background_color: Background color
        output_path: Path to save the label
        
    Returns:
        PIL Image of label
    """
    # Default size: 4" x 2" label
    if size is None:
        width = inches_to_pixels(4)
        height = inches_to_pixels(2)
    else:
        width, height = size
    
    # Create label
    label = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(label)
    
    # Add thick border
    border_width = max(5, min(width, height) // 40)
    draw.rectangle(
        [0, 0, width - 1, height - 1],
        outline=border_color,
        width=border_width
    )
    
    # If image provided, add it
    if image_filename:
        image = load_image(image_filename, image_folder)
        if image:
            # Image on left, text on right
            image_width = width // 3
            image_height = height - 40
            
            scaled_image = scale_image_to_fit(image.copy(), image_width, image_height)
            
            img_x = 20
            img_y = (height - scaled_image.height) // 2
            
            if scaled_image.mode == 'RGBA':
                label.paste(scaled_image, (img_x, img_y), scaled_image)
            else:
                label.paste(scaled_image, (img_x, img_y))
            
            # Adjust text position
            text_x = img_x + image_width + 20
            text_area_width = width - text_x - 20
        else:
            text_x = 20
            text_area_width = width - 40
    else:
        text_x = 20
        text_area_width = width - 40
    
    # Add text
    font = get_font(LARGE_FONT_SIZE, bold=True)
    
    # Check if text fits, reduce font size if needed
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    
    if text_width > text_area_width:
        font = get_font(DEFAULT_FONT_SIZE, bold=True)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
    
    text_height = bbox[3] - bbox[1]
    
    # Center text in available area
    final_text_x = text_x + (text_area_width - text_width) // 2
    final_text_y = (height - text_height) // 2
    
    draw.text((final_text_x, final_text_y), text, fill=BLACK, font=font)
    
    # Save if output path provided
    if output_path:
        label.save(output_path, dpi=(DPI, DPI))
        print(f"Saved: {output_path}")
    
    return label


def generate_label_sheet(labels: List[str],
                        images: Optional[List[str]] = None,
                        image_folder: str = 'images',
                        labels_per_page: int = 6,
                        output_path: str = None) -> Image.Image:
    """
    Generate a sheet of multiple labels.
    
    Args:
        labels: List of label texts
        images: Optional list of image filenames (same length as labels)
        image_folder: Folder to load images from
        labels_per_page: Number of labels per page (4, 6, or 8)
        output_path: Path to save the label sheet
        
    Returns:
        PIL Image of label sheet
    """
    # Create layout
    layout = SPEDLayout()
    
    # Determine grid layout
    if labels_per_page == 4:
        rows, cols = 2, 2
    elif labels_per_page == 6:
        rows, cols = 3, 2
    elif labels_per_page == 8:
        rows, cols = 4, 2
    else:
        rows, cols = 3, 2  # Default to 6
    
    # Calculate label dimensions
    margin = inches_to_pixels(0.5)
    spacing = inches_to_pixels(0.25)
    
    available_width = layout.width - 2 * margin - (cols - 1) * spacing
    available_height = layout.height - 2 * margin - (rows - 1) * spacing
    
    label_width = available_width // cols
    label_height = available_height // rows
    
    # Generate labels
    if images is None:
        images = [None] * len(labels)
    
    for idx, (text, image_file) in enumerate(zip(labels[:labels_per_page], images[:labels_per_page])):
        row = idx // cols
        col = idx % cols
        
        x = margin + col * (label_width + spacing)
        y = margin + row * (label_height + spacing)
        
        # Create individual label
        label = generate_label(
            text,
            image_filename=image_file,
            image_folder=image_folder,
            size=(label_width, label_height)
        )
        
        # Paste onto sheet
        layout.canvas.paste(label, (x, y))
    
    # Add footer
    layout.add_footer("© Small Wins Studio")
    
    # Save if output path provided
    if output_path:
        layout.save(output_path)
    
    return layout.get_canvas()


def generate_label_set(labels_list: List[List[str]],
                      images_list: Optional[List[List[str]]] = None,
                      image_folder: str = 'images',
                      labels_per_page: int = 6,
                      output_dir: str = 'outputs') -> List[str]:
    """
    Generate a set of label sheets.
    
    Args:
        labels_list: List of label lists for each sheet
        images_list: Optional list of image lists for each sheet
        image_folder: Folder to load images from
        labels_per_page: Number of labels per page
        output_dir: Directory to save label sheets
        
    Returns:
        List of output filenames
    """
    from ..utils import get_project_root
    
    output_files = []
    output_path = get_project_root() / output_dir
    output_path.mkdir(exist_ok=True)
    
    if images_list is None:
        images_list = [None] * len(labels_list)
    
    for i, (labels, images) in enumerate(zip(labels_list, images_list)):
        filename = f"label_sheet_{i+1}.png"
        filepath = output_path / filename
        
        generate_label_sheet(
            labels,
            images=images,
            image_folder=image_folder,
            labels_per_page=labels_per_page,
            output_path=str(filepath)
        )
        
        output_files.append(str(filepath))
    
    return output_files
