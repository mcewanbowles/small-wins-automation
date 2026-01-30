"""
Coloring Strips Generator

Generates coloring strips - narrow strips with outline images for coloring.
Ideal for students with limited fine motor skills.
"""

from PIL import Image, ImageDraw
from utils.config import MARGINS, DPI, PAGE_WIDTH, PAGE_HEIGHT
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional
from utils.layout import create_page_canvas, add_page_border, add_footer
from utils.pdf_export import save_images_as_pdf


def generate_coloring_strip(image_filename, label_text=None, folder_type='bw_outline'):
    """
    Generate a single coloring strip (2" x 8.5" strip).
    
    Args:
        image_filename: Filename of outline image
        label_text: Optional text label
        folder_type: Should be 'bw_outline' for coloring
        
    Returns:
        PIL.Image: Generated strip
    """
    # Strip dimensions: 2" high x 8.5" wide at 300 DPI
    strip_width = int(8.5 * DPI)
    strip_height = int(2 * DPI)
    
    strip = Image.new('RGBA', (strip_width, strip_height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(strip)
    
    # Draw border
    for i in range(5):
        draw.rectangle(
            [i, i, strip_width - 1 - i, strip_height - 1 - i],
            outline=(0, 0, 0, 255)
        )
    
    # Load and scale image
    image_loader = get_image_loader()
    theme_image = image_loader.load_image(image_filename, folder_type)
    
    # Reserve space for label if provided
    if label_text:
        image_width = strip_width - 400  # Reserve 400px for text
        text_area_x = strip_width - 380
    else:
        image_width = strip_width - 40
        text_area_x = None
    
    scaled_image = scale_image_proportional(
        theme_image,
        max_width=image_width,
        max_height=strip_height - 40
    )
    
    # Center image vertically, place on left
    img_x = 20
    img_y = (strip_height - scaled_image.height) // 2
    strip.paste(scaled_image, (img_x, img_y), scaled_image)
    
    # Add label if provided
    if label_text and text_area_x:
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = text_area_x
            text_y = (strip_height - text_height) // 2
            draw.text((text_x, text_y), label_text, fill=(0, 0, 0, 255), font=font)
        except:
            pass
    
    return strip


def generate_coloring_strips_page(image_label_pairs, folder_type='bw_outline',
                                   theme_name='Theme', output_dir='output',
                                   include_storage_label=False):
    """
    Generate pages of coloring strips (5 strips per page).
    
    Args:
        image_label_pairs: List of tuples (image_filename, label_text)
        folder_type: Image folder type
        theme_name: Theme name
        output_dir: Output directory
        include_storage_label: If True, also generate a companion storage label PDF
        
    Returns:
        list: Generated pages
    """
    strips_per_page = 5
    pages = []
    
    for page_start in range(0, len(image_label_pairs), strips_per_page):
        page = create_page_canvas()
        page_items = image_label_pairs[page_start:page_start + strips_per_page]
        
        # Generate strips
        strips = []
        for image_file, label in page_items:
            strip = generate_coloring_strip(image_file, label, folder_type)
            strips.append(strip)
        
        # Place strips on page with spacing
        strip_height = int(2 * DPI)
        spacing = 50
        total_height = (strip_height * len(strips)) + (spacing * (len(strips) - 1))
        start_y = (PAGE_HEIGHT - total_height) // 2
        
        for idx, strip in enumerate(strips):
            y = start_y + (idx * (strip_height + spacing))
            x = (PAGE_WIDTH - strip.width) // 2
            page.paste(strip, (int(x), int(y)), strip)
        
        add_page_border(page)
        add_footer(page)
        pages.append(page)
    
    # Save PDF
    import os
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/{theme_name}_Coloring_Strips.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Coloring Strips")
    
    # Generate storage label if requested
    if include_storage_label:
        from utils.storage_label_helper import create_companion_label
        
        # Try to find an icon from first image
        icon_path = None
        if image_label_pairs:
            image_loader = get_image_loader()
            first_image = image_label_pairs[0][0] if isinstance(image_label_pairs[0], tuple) else image_label_pairs[0]
            potential_icon = image_loader.get_image_path(first_image, folder_type)
            if os.path.exists(potential_icon):
                icon_path = potential_icon
        
        label_path = create_companion_label(
            main_pdf_path=output_path,
            theme_name=theme_name,
            activity_name="Coloring Strips",
            icon_path=icon_path
        )
        print(f"✓ Generated storage label")
        print(f"  Label: {label_path}")
    
    return pages


if __name__ == "__main__":
    print("Coloring Strips Generator")
    print("Use generate_coloring_strip() or generate_coloring_strips_page()")
