"""
Yes/No Questions Generator

Generates yes/no question cards with images for visual support.
Students answer simple yes/no questions about images.
"""

from PIL import Image, ImageDraw
from utils.config import PAGE_WIDTH, PAGE_HEIGHT, MARGINS, DPI
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional
from utils.layout import create_page_canvas, add_page_border, add_footer, add_title_to_page
from utils.pdf_export import save_images_as_pdf
from utils.color_helpers import image_to_grayscale


def generate_yes_no_question_card(image_filename, question_text, answer,
                                   folder_type='color', level=1, mode='color'):
    """
    Generate a yes/no question card.
    
    Args:
        image_filename: Filename of the image
        question_text: Question to ask (e.g., "Is this a dog?")
        answer: True for Yes, False for No
        folder_type: Image folder type
        level: Differentiation level (1=answer shown, 2=no answer)
        mode: Output mode ('color' or 'bw')
        
    Returns:
        PIL.Image: Generated card
    """
    page = create_page_canvas(mode=mode)
    
    # Add question as title
    add_title_to_page(page, question_text)
    
    # Load and display image
    image_loader = get_image_loader()
    theme_image = image_loader.load_image(image_filename, folder_type)
    
    # Convert to grayscale if in BW mode
    if mode == 'bw':
        theme_image = image_to_grayscale(theme_image)
    
    available_width = PAGE_WIDTH - (MARGINS['page'] * 2)
    available_height = PAGE_HEIGHT - 600
    
    scaled_image = scale_image_proportional(theme_image, max_width=available_width, max_height=available_height)
    
    img_x = (PAGE_WIDTH - scaled_image.width) // 2
    img_y = 300
    page.paste(scaled_image, (int(img_x), int(img_y)), scaled_image)
    
    # Add Yes/No options
    draw = ImageDraw.Draw(page)
    options_y = PAGE_HEIGHT - 500
    
    # Yes button
    yes_x = PAGE_WIDTH // 2 - 400
    draw.rectangle(
        [yes_x, options_y, yes_x + 300, options_y + 150],
        fill=(200, 255, 200, 255) if (answer and level == 1) else (255, 255, 255, 255),
        outline=(0, 0, 0, 255),
        width=5
    )
    
    # No button
    no_x = PAGE_WIDTH // 2 + 100
    draw.rectangle(
        [no_x, options_y, no_x + 300, options_y + 150],
        fill=(255, 200, 200, 255) if (not answer and level == 1) else (255, 255, 255, 255),
        outline=(0, 0, 0, 255),
        width=5
    )
    
    # Draw text
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
        
        # Yes text
        bbox = draw.textbbox((0, 0), "YES", font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = yes_x + (300 - text_width) // 2
        text_y = options_y + (150 - text_height) // 2
        draw.text((text_x, text_y), "YES", fill=(0, 0, 0, 255), font=font)
        
        # No text
        bbox = draw.textbbox((0, 0), "NO", font=font)
        text_width = bbox[2] - bbox[0]
        text_x = no_x + (300 - text_width) // 2
        draw.text((text_x, text_y), "NO", fill=(0, 0, 0, 255), font=font)
    except:
        pass
    
    add_page_border(page, mode=mode)
    add_footer(page, mode=mode)
    
    return page


def generate_yes_no_questions_set(question_data, folder_type='color', level=1,
                                   theme_name='Theme', output_dir='output',
                                   include_storage_label=False, mode='color'):
    """
    Generate a set of yes/no questions.
    
    Args:
        question_data: List of dicts with 'image', 'question', 'answer' keys
        folder_type: Image folder type
        level: Differentiation level
        theme_name: Theme name
        output_dir: Output directory
        include_storage_label: If True, also generate a companion storage label PDF
        mode: Output mode ('color' or 'bw')
        
    Returns:
        str: Path to generated PDF
    """
    pages = []
    
    for item in question_data:
        page = generate_yes_no_question_card(
            item['image'],
            item['question'],
            item['answer'],
            folder_type,
            level,
            mode
        )
        pages.append(page)
    
    # Save PDF
    import os
    os.makedirs(output_dir, exist_ok=True)
    mode_suffix = f"_{mode}" if mode else ""
    output_path = f"{output_dir}/{theme_name}_Yes_No_Questions_Level{level}{mode_suffix}.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Yes/No Questions")
    
    # Generate storage label if requested (only for color mode)
    if include_storage_label and mode == 'color':
        from utils.storage_label_helper import create_companion_label
        
        # Try to find an icon from first question
        icon_path = None
        if question_data and 'image' in question_data[0]:
            image_loader = get_image_loader()
            potential_icon = image_loader.get_image_path(question_data[0]['image'], folder_type)
            if os.path.exists(potential_icon):
                icon_path = potential_icon
        
        label_path = create_companion_label(
            main_pdf_path=output_path,
            theme_name=theme_name,
            activity_name="Yes/No Questions",
            level=level,
            icon_path=icon_path
        )
        print(f"✓ Generated storage label")
        print(f"  Label: {label_path}")
    
    return output_path


def generate_yes_no_questions_dual_mode(question_data, folder_type='color', level=1,
                                        theme_name='Theme', output_dir='output',
                                        include_storage_label=False):
    """
    Generate yes/no questions in both color and black-and-white modes.
    
    Args:
        question_data: List of dicts with 'image', 'question', 'answer' keys
        folder_type: Image folder type
        level: Differentiation level
        theme_name: Theme name
        output_dir: Output directory
        include_storage_label: If True, generate storage label for color version
        
    Returns:
        dict: Paths to generated PDFs {'color': path, 'bw': path}
    """
    paths = {}
    
    # Generate color version
    paths['color'] = generate_yes_no_questions_set(
        question_data=question_data,
        folder_type=folder_type,
        level=level,
        theme_name=theme_name,
        output_dir=output_dir,
        include_storage_label=include_storage_label,
        mode='color'
    )
    
    # Generate black-and-white version
    paths['bw'] = generate_yes_no_questions_set(
        question_data=question_data,
        folder_type=folder_type,
        level=level,
        theme_name=theme_name,
        output_dir=output_dir,
        include_storage_label=False,  # No label for BW version
        mode='bw'
    )
    
    return paths


if __name__ == "__main__":
    print("Yes/No Questions Generator")
    print("Use generate_yes_no_question_card() or generate_yes_no_questions_set()")
