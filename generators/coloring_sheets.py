"""
Full-Page Coloring Sheets Generator

Generates full-page coloring sheets with large outline images.
Perfect for students who need larger work areas.
"""

from PIL import Image, ImageDraw
from utils.config import PAGE_WIDTH, PAGE_HEIGHT, MARGINS, DPI
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional
from utils.layout import create_page_canvas, add_page_border, add_footer, add_title_to_page
from utils.pdf_export import save_images_as_pdf


def generate_coloring_sheet(image_filename, title_text=None, folder_type='bw_outline', mode='color'):
    """
    Generate a full-page coloring sheet.
    
    Args:
        image_filename: Filename of outline image
        title_text: Optional title text
        folder_type: Should be 'bw_outline' for coloring
        mode: 'color' or 'bw' for output mode
        
    Returns:
        PIL.Image: Generated coloring sheet
    """
    page = create_page_canvas(mode=mode)
    
    # Add title if provided
    if title_text:
        add_title_to_page(page, title_text)
        available_top = 250
    else:
        available_top = MARGINS['page']
    
    # Load and scale image to fill most of page
    image_loader = get_image_loader()
    theme_image = image_loader.load_image(image_filename, folder_type)
    
    available_width = PAGE_WIDTH - (MARGINS['page'] * 2)
    available_height = PAGE_HEIGHT - available_top - 200  # Leave space for footer
    
    scaled_image = scale_image_proportional(
        theme_image,
        max_width=available_width,
        max_height=available_height
    )
    
    # Center image on page
    img_x = (PAGE_WIDTH - scaled_image.width) // 2
    img_y = available_top + ((available_height - scaled_image.height) // 2)
    
    page.paste(scaled_image, (int(img_x), int(img_y)), scaled_image)
    
    # Add border and footer
    add_page_border(page)
    add_footer(page, mode=mode)
    
    return page


def generate_coloring_sheets_set(image_title_pairs, folder_type='bw_outline',
                                  theme_name='Theme', output_dir='output',
                                  include_storage_label=False, mode='color'):
    """
    Generate a set of coloring sheets.
    
    Args:
        image_title_pairs: List of tuples (image_filename, title_text)
        folder_type: Image folder type
        theme_name: Theme name
        output_dir: Output directory
        include_storage_label: If True, also generate a companion storage label PDF
        mode: 'color' or 'bw' for output mode
        
    Returns:
        list: Generated pages
    """
    pages = []
    
    for image_file, title in image_title_pairs:
        page = generate_coloring_sheet(image_file, title, folder_type, mode=mode)
        pages.append(page)
    
    # Save PDF
    import os
    os.makedirs(output_dir, exist_ok=True)
    mode_suffix = f"_{mode}" if mode else ""
    output_path = f"{output_dir}/{theme_name}_Coloring_Sheets{mode_suffix}.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Coloring Sheets")
    
    # Generate storage label if requested (only for color mode)
    if include_storage_label and mode == 'color':
        from utils.storage_label_helper import create_companion_label
        
        # Try to find an icon from first image
        icon_path = None
        if image_title_pairs:
            image_loader = get_image_loader()
            first_image = image_title_pairs[0][0] if isinstance(image_title_pairs[0], tuple) else image_title_pairs[0]
            potential_icon = image_loader.get_image_path(first_image, folder_type)
            if os.path.exists(potential_icon):
                icon_path = potential_icon
        
        label_path = create_companion_label(
            main_pdf_path=output_path,
            theme_name=theme_name,
            activity_name="Coloring Sheets",
            icon_path=icon_path
        )
        print(f"✓ Generated storage label")
        print(f"  Label: {label_path}")
    
    return output_path


def generate_coloring_sheets_dual_mode(image_title_pairs, folder_type='bw_outline',
                                       theme_name='Theme', output_dir='output',
                                       include_storage_label=False):
    """
    Generate coloring sheets in both color and black-and-white modes.
    
    Args:
        image_title_pairs: List of tuples (image_filename, title_text)
        folder_type: Image folder type
        theme_name: Theme name
        output_dir: Output directory
        include_storage_label: If True, also generate a companion storage label PDF
        
    Returns:
        dict: Paths to generated PDFs {'color': path, 'bw': path}
    """
    paths = {}
    
    # Generate color version
    color_path = generate_coloring_sheets_set(
        image_title_pairs=image_title_pairs,
        folder_type=folder_type,
        theme_name=theme_name,
        output_dir=output_dir,
        include_storage_label=include_storage_label,
        mode='color'
    )
    paths['color'] = color_path
    
    # Generate black-and-white version
    bw_path = generate_coloring_sheets_set(
        image_title_pairs=image_title_pairs,
        folder_type=folder_type,
        theme_name=theme_name,
        output_dir=output_dir,
        include_storage_label=False,  # Only for color version
        mode='bw'
    )
    paths['bw'] = bw_path
    
    return paths


if __name__ == "__main__":
    print("Coloring Sheets Generator")
    print("Use generate_coloring_sheet() or generate_coloring_sheets_set()")
