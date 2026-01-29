"""
WH Questions Generator

Generates WH question cards (Who, What, Where, When, Why) with images.
Supports multiple choice answers for accessibility.
"""

from PIL import Image, ImageDraw
from utils.config import PAGE_WIDTH, PAGE_HEIGHT, MARGINS
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional
from utils.layout import create_page_canvas, add_page_border, add_footer, add_title_to_page
from utils.pdf_export import save_images_as_pdf


def generate_wh_question_card(image_filename, question_text, choices, correct_answer,
                               folder_type='color', level=1):
    """
    Generate a WH question card.
    
    Args:
        image_filename: Filename of the image
        question_text: Question to ask (e.g., "What is this?")
        choices: List of answer choices
        correct_answer: Index of correct answer (0-based)
        folder_type: Image folder type
        level: Differentiation level (1=answer shown, 2=no answer)
        
    Returns:
        PIL.Image: Generated card
    """
    page = create_page_canvas()
    
    # Add question as title
    add_title_to_page(page, question_text)
    
    # Load and display image
    image_loader = get_image_loader()
    theme_image = image_loader.load_image(image_filename, folder_type)
    
    available_width = PAGE_WIDTH - (MARGINS['page'] * 2)
    scaled_image = scale_image_proportional(theme_image, max_width=available_width, max_height=1000)
    
    img_x = (PAGE_WIDTH - scaled_image.width) // 2
    img_y = 300
    page.paste(scaled_image, (int(img_x), int(img_y)), scaled_image)
    
    # Add answer choices
    draw = ImageDraw.Draw(page)
    choices_y = img_y + scaled_image.height + 100
    choice_height = 120
    choice_spacing = 30
    
    for idx, choice in enumerate(choices):
        y = choices_y + (idx * (choice_height + choice_spacing))
        
        # Highlight correct answer if Level 1
        is_correct = (idx == correct_answer)
        fill_color = (200, 255, 200, 255) if (is_correct and level == 1) else (255, 255, 255, 255)
        
        # Draw choice box
        draw.rectangle(
            [MARGINS['page'], y, PAGE_WIDTH - MARGINS['page'], y + choice_height],
            fill=fill_color,
            outline=(0, 0, 0, 255),
            width=5
        )
        
        # Draw choice text
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
            text = f"{chr(65 + idx)}) {choice}"  # A), B), C), etc.
            bbox = draw.textbbox((0, 0), text, font=font)
            text_height = bbox[3] - bbox[1]
            text_x = MARGINS['page'] + 30
            text_y = y + (choice_height - text_height) // 2
            draw.text((text_x, text_y), text, fill=(0, 0, 0, 255), font=font)
        except:
            pass
    
    add_page_border(page)
    add_footer(page)
    
    return page


def generate_wh_questions_set(question_data, folder_type='color', level=1,
                               theme_name='Theme', output_dir='output'):
    """
    Generate a set of WH questions.
    
    Args:
        question_data: List of dicts with 'image', 'question', 'choices', 'answer' keys
        folder_type: Image folder type
        level: Differentiation level
        theme_name: Theme name
        output_dir: Output directory
        
    Returns:
        list: Generated pages
    """
    pages = []
    
    for item in question_data:
        page = generate_wh_question_card(
            item['image'],
            item['question'],
            item['choices'],
            item['answer'],
            folder_type,
            level
        )
        pages.append(page)
    
    # Save PDF
    output_path = f"{output_dir}/{theme_name}_WH_Questions_Level{level}.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} WH Questions")
    
    return pages


if __name__ == "__main__":
    print("WH Questions Generator")
    print("Use generate_wh_question_card() or generate_wh_questions_set()")
