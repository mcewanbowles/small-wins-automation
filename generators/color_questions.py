"""
Color Questions Generator

Generates color identification questions with images.
Students identify or match colors with visual supports.
"""

from PIL import Image, ImageDraw
from utils.config import PAGE_WIDTH, PAGE_HEIGHT, MARGINS
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional
from utils.layout import create_page_canvas, add_page_border, add_footer, add_title_to_page
from utils.pdf_export import save_images_as_pdf


# Common colors for activities
COLORS = {
    'red': (255, 0, 0, 255),
    'blue': (0, 0, 255, 255),
    'yellow': (255, 255, 0, 255),
    'green': (0, 255, 0, 255),
    'orange': (255, 165, 0, 255),
    'purple': (128, 0, 128, 255),
    'pink': (255, 192, 203, 255),
    'brown': (139, 69, 19, 255),
    'black': (0, 0, 0, 255),
    'white': (255, 255, 255, 255),
}


def generate_color_question_card(image_filename, question_text, correct_color,
                                  color_choices=None, folder_type='color', level=1):
    """
    Generate a color identification question card.
    
    Args:
        image_filename: Filename of the image
        question_text: Question to ask (e.g., "What color is this?")
        correct_color: Name of correct color
        color_choices: List of color names to show (default: red, blue, yellow, green)
        folder_type: Image folder type
        level: Differentiation level (1=answer shown, 2=no answer)
        
    Returns:
        PIL.Image: Generated card
    """
    if color_choices is None:
        color_choices = ['red', 'blue', 'yellow', 'green']
    
    page = create_page_canvas()
    
    # Add question as title
    add_title_to_page(page, question_text)
    
    # Load and display image
    image_loader = get_image_loader()
    theme_image = image_loader.load_image(image_filename, folder_type)
    
    available_width = PAGE_WIDTH - (MARGINS['page'] * 2)
    scaled_image = scale_image_proportional(theme_image, max_width=available_width, max_height=1200)
    
    img_x = (PAGE_WIDTH - scaled_image.width) // 2
    img_y = 300
    page.paste(scaled_image, (int(img_x), int(img_y)), scaled_image)
    
    # Add color choices
    draw = ImageDraw.Draw(page)
    choices_y = PAGE_HEIGHT - 600
    
    # Determine layout based on number of choices
    if len(color_choices) <= 4:
        grid_cols = len(color_choices)
        grid_rows = 1
    else:
        grid_cols = 4
        grid_rows = (len(color_choices) + 3) // 4
    
    color_box_size = 150
    spacing = 50
    
    total_width = (color_box_size * grid_cols) + (spacing * (grid_cols - 1))
    start_x = (PAGE_WIDTH - total_width) // 2
    
    for idx, color_name in enumerate(color_choices):
        row = idx // grid_cols
        col = idx % grid_cols
        
        x = start_x + (col * (color_box_size + spacing))
        y = choices_y + (row * (color_box_size + spacing + 40))
        
        # Draw color box
        color_rgb = COLORS.get(color_name.lower(), (128, 128, 128, 255))
        
        # Add highlight if correct and Level 1
        border_width = 8 if (color_name == correct_color and level == 1) else 3
        
        draw.rectangle(
            [x, y, x + color_box_size, y + color_box_size],
            fill=color_rgb,
            outline=(0, 0, 0, 255),
            width=border_width
        )
        
        # Draw color name below box
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), color_name, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = x + (color_box_size - text_width) // 2
            text_y = y + color_box_size + 10
            draw.text((text_x, text_y), color_name, fill=(0, 0, 0, 255), font=font)
        except:
            pass
    
    add_page_border(page)
    add_footer(page)
    
    return page


def generate_color_questions_set(question_data, folder_type='color', level=1,
                                  theme_name='Theme', output_dir='output'):
    """
    Generate a set of color questions.
    
    Args:
        question_data: List of dicts with 'image', 'question', 'color', 'choices' keys
        folder_type: Image folder type
        level: Differentiation level
        theme_name: Theme name
        output_dir: Output directory
        
    Returns:
        list: Generated pages
    """
    pages = []
    
    for item in question_data:
        page = generate_color_question_card(
            item['image'],
            item['question'],
            item['color'],
            item.get('choices'),
            folder_type,
            level
        )
        pages.append(page)
    
    # Save PDF
    output_path = f"{output_dir}/{theme_name}_Color_Questions_Level{level}.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Color Questions")
    
    return pages


if __name__ == "__main__":
    print("Color Questions Generator")
    print("Use generate_color_question_card() or generate_color_questions_set()")
