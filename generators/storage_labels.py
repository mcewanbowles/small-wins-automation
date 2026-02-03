"""
Storage Labels Generator

Generates labels for organizing and storing materials.
Includes images and text for easy identification.
"""

from PIL import Image, ImageDraw
from utils.config import MARGINS, DPI
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional
from utils.layout import create_page_canvas, add_page_border, add_footer
from utils.pdf_export import save_images_as_pdf
from utils.color_helpers import image_to_grayscale


def generate_storage_label(image_filename, label_text, label_size='medium', folder_type='color', mode='color'):
    """
    Generate a single storage label.
    
    Args:
        image_filename: Filename of the image
        label_text: Text for the label
        label_size: 'small' (2x3"), 'medium' (3x4"), or 'large' (4x5")
        folder_type: Image folder type
        mode: 'color' or 'bw' for output mode
        
    Returns:
        PIL.Image: Generated label
    """
    # Label dimensions at 300 DPI
    sizes = {
        'small': (int(2 * DPI), int(3 * DPI)),    # 2" x 3"
        'medium': (int(3 * DPI), int(4 * DPI)),   # 3" x 4"
        'large': (int(4 * DPI), int(5 * DPI)),    # 4" x 5"
    }
    
    width, height = sizes.get(label_size, sizes['medium'])
    
    label = Image.new('RGBA', (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(label)
    
    # Draw border
    for i in range(5):
        draw.rectangle(
            [i, i, width - 1 - i, height - 1 - i],
            outline=(0, 0, 0, 255)
        )
    
    # Load and scale image
    image_loader = get_image_loader()
    theme_image = image_loader.load_image(image_filename, folder_type)
    
    # Convert to grayscale if BW mode
    if mode == 'bw':
        theme_image = image_to_grayscale(theme_image)
    
    # Reserve space for text at bottom
    text_area_height = 100
    image_height = height - text_area_height - 40
    
    scaled_image = scale_image_proportional(
        theme_image,
        max_width=width - 40,
        max_height=image_height
    )
    
    # Center image at top
    img_x = (width - scaled_image.width) // 2
    img_y = 20
    label.paste(scaled_image, (img_x, img_y), scaled_image)
    
    # Add text at bottom
    text_y = height - text_area_height
    
    # Draw text background
    draw.rectangle(
        [10, text_y, width - 10, height - 10],
        fill=(240, 240, 240, 255)
    )
    
    # Draw text
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), label_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (width - text_width) // 2
        text_y_pos = text_y + (text_area_height - text_height) // 2
        draw.text((text_x, text_y_pos), label_text, fill=(0, 0, 0, 255), font=font)
    except:
        pass
    
    return label


def generate_storage_labels_sheet(label_data, label_size='medium', folder_type='color',
                                   theme_name='Theme', output_dir='output', mode='color'):
    """
    Generate sheets of storage labels.
    
    Args:
        label_data: List of tuples (image_filename, label_text)
        label_size: Size of labels
        folder_type: Image folder type
        theme_name: Theme name
        output_dir: Output directory
        mode: 'color' or 'bw' for output mode
        
    Returns:
        list: Generated pages
    """
    pages = []
    
    # Determine labels per page based on size
    if label_size == 'small':
        labels_per_page = 6  # 2x3 grid
        grid_cols, grid_rows = 2, 3
    elif label_size == 'medium':
        labels_per_page = 4  # 2x2 grid
        grid_cols, grid_rows = 2, 2
    else:  # large
        labels_per_page = 2  # 1x2 grid
        grid_cols, grid_rows = 1, 2
    
    # Generate labels
    all_labels = []
    for image_file, text in label_data:
        label = generate_storage_label(image_file, text, label_size, folder_type, mode)
        all_labels.append(label)
    
    # Arrange on pages
    for page_start in range(0, len(all_labels), labels_per_page):
        page = create_page_canvas(mode=mode)
        page_labels = all_labels[page_start:page_start + labels_per_page]
        
        label_width, label_height = all_labels[0].size
        spacing = MARGINS['content']
        
        total_width = (label_width * grid_cols) + (spacing * (grid_cols - 1))
        total_height = (label_height * grid_rows) + (spacing * (grid_rows - 1))
        
        start_x = (int(page.width) - total_width) // 2
        start_y = (int(page.height) - total_height - 200) // 2
        
        for idx, label in enumerate(page_labels):
            row = idx // grid_cols
            col = idx % grid_cols
            
            x = start_x + (col * (label_width + spacing))
            y = start_y + (row * (label_height + spacing))
            
            page.paste(label, (int(x), int(y)), label)
        
        add_page_border(page)
        add_footer(page, mode=mode)
        pages.append(page)
    
    # Save PDF with mode suffix
    mode_suffix = f"_{mode}" if mode else ""
    output_path = f"{output_dir}/{theme_name}_Storage_Labels{mode_suffix}.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Storage Labels")
    
    return pages


def generate_storage_labels_dual_mode(label_data, label_size='medium', folder_type='color',
                                       theme_name='Theme', output_dir='output'):
    """
    Generate storage labels in both color and BW modes.
    
    Args:
        label_data: List of tuples (image_filename, label_text)
        label_size: Size of labels
        folder_type: Image folder type
        theme_name: Theme name
        output_dir: Output directory
        
    Returns:
        dict: Paths to generated PDFs {'color': path, 'bw': path}
    """
    paths = {}
    
    # Generate color version
    generate_storage_labels_sheet(
        label_data, label_size, folder_type, theme_name, output_dir, mode='color'
    )
    paths['color'] = f"{output_dir}/{theme_name}_Storage_Labels_color.pdf"
    
    # Generate BW version
    generate_storage_labels_sheet(
        label_data, label_size, folder_type, theme_name, output_dir, mode='bw'
    )
    paths['bw'] = f"{output_dir}/{theme_name}_Storage_Labels_bw.pdf"
    
    return paths


if __name__ == "__main__":
    print("Storage Labels Generator")
    print("Use generate_storage_label() or generate_storage_labels_sheet()")
    print("Use generate_storage_labels_dual_mode() for both color and BW versions")
