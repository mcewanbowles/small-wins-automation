"""
Clip Cards Generator for SPED Resources

Generates clip cards for multiple-choice selection tasks with clothespins or clips.
Cards are task-box friendly with 4 cards per page in a 2×2 grid with shared borders
for easy guillotine cutting.

Features:
- Task-box compatible sizing (5.25" × 4" per card)
- 4 cards per page (2×2 grid)
- Shared borders for guillotine cutting
- Multiple card types: Identify Icon, Color, Count & Clip, Emotion
- Three answer choices per card
- Optional errorless versions (only correct answer)
- Real image and Boardmaker support
- SPED-compliant high contrast design
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont
from utils.config import DPI, PAGE_WIDTH, PAGE_HEIGHT, MARGINS, COLORS, FONT_SIZES, FOOTER_TEXT
from utils.image_loader import load_image
from utils.pdf_export import save_images_as_pdf
from utils.draw_helpers import (
    scale_image_to_fit,
    draw_page_number,
    draw_copyright_footer,
    create_placeholder_image
)
from utils.storage_label_helper import create_companion_label
from utils.color_helpers import adjust_for_bw_mode, image_to_grayscale

# Task box card sizing standard (4 cards per page, 2×2 grid)
# 5.25" × 4" at 300 DPI = 1575px × 1200px
TASK_BOX_CARD_WIDTH = int(5.25 * DPI)  # 1575px
TASK_BOX_CARD_HEIGHT = int(4 * DPI)  # 1200px


def generate_identify_icon_card(draw, card_rect, item, choices, errorless=False, folder_type='images', mode='color'):
    """
    Generate an "Identify the Icon" clip card.
    
    Args:
        draw: PIL ImageDraw object
        card_rect: Tuple (x1, y1, x2, y2) defining card boundaries
        item: Dict with 'image' and 'label' keys (correct answer)
        choices: List of 3 label strings (including correct answer)
        errorless: If True, only show correct answer
        folder_type: Image folder type ('images', 'real_images', etc.)
        mode: 'color' or 'bw' for output mode
    """
    x1, y1, x2, y2 = card_rect
    card_width = x2 - x1
    card_height = y2 - y1
    
    # Draw card border (mode-aware)
    border_color = adjust_for_bw_mode(COLORS['black'], mode)
    draw.rectangle([x1, y1, x2, y2], outline=border_color, width=3)
    
    # Layout: 50% icon, 20% question, 30% answer choices
    icon_area_height = int(card_height * 0.50)
    question_area_height = int(card_height * 0.20)
    choices_area_height = int(card_height * 0.30)
    
    # 1. Icon area (top 50%)
    icon_rect = (
        x1 + 30,
        y1 + 30,
        x2 - 30,
        y1 + icon_area_height - 20
    )
    
    try:
        img = load_image(item['image'], folder_type=folder_type)
        if img:
            # Convert to grayscale if BW mode
            if mode == 'bw':
                img = image_to_grayscale(img)
            
            scaled_coords = scale_image_to_fit(img, icon_rect, padding=15)
            if scaled_coords:
                paste_x, paste_y, paste_width, paste_height = scaled_coords
                resized_img = img.resize((paste_width, paste_height), Image.Resampling.LANCZOS)
                if resized_img.mode == 'RGBA':
                    bg = Image.new('RGB', resized_img.size, COLORS['white'])
                    bg.paste(resized_img, mask=resized_img.split()[3])
                    resized_img = bg
                temp_page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
                temp_page.paste(resized_img, (paste_x, paste_y))
                draw._image.paste(temp_page.crop((paste_x, paste_y, paste_x + paste_width, paste_y + paste_height)), (paste_x, paste_y))
    except:
        placeholder = create_placeholder_image(icon_rect[2] - icon_rect[0], icon_rect[3] - icon_rect[1], "Icon")
        draw._image.paste(placeholder, (icon_rect[0], icon_rect[1]))
    
    # 2. Question area
    question_y = y1 + icon_area_height + 10
    question_text = f"Which one is {item['label']}?"
    
    try:
        font_question = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except:
        font_question = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), question_text, font=font_question)
    text_width = bbox[2] - bbox[0]
    text_x = x1 + (card_width - text_width) // 2
    text_color = adjust_for_bw_mode(COLORS['black'], mode)
    draw.text((text_x, question_y), question_text, fill=text_color, font=font_question)
    
    # 3. Answer choices area (bottom 30%)
    choices_y_start = y1 + icon_area_height + question_area_height
    
    if errorless:
        # Only show correct answer
        display_choices = [item['label']]
    else:
        display_choices = choices
    
    choice_width = (card_width - 80) // len(display_choices)
    
    try:
        font_choice = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_choice = ImageFont.load_default()
    
    for i, choice in enumerate(display_choices):
        choice_x = x1 + 40 + (i * choice_width)
        choice_y = choices_y_start + 20
        
        # Draw circle for clip placement (mode-aware)
        circle_radius = 25
        circle_center_x = choice_x + choice_width // 2
        circle_center_y = choice_y
        
        circle_color = adjust_for_bw_mode(COLORS['black'], mode)
        draw.ellipse(
            [circle_center_x - circle_radius, circle_center_y - circle_radius,
             circle_center_x + circle_radius, circle_center_y + circle_radius],
            outline=circle_color, width=3
        )
        
        # Draw choice text below circle
        bbox = draw.textbbox((0, 0), choice, font=font_choice)
        text_width = bbox[2] - bbox[0]
        text_x = circle_center_x - text_width // 2
        text_y = circle_center_y + circle_radius + 10
        text_color = adjust_for_bw_mode(COLORS['black'], mode)
        draw.text((text_x, text_y), choice, fill=text_color, font=font_choice)


def generate_color_clip_card(draw, card_rect, item, color_name, color_choices, errorless=False, folder_type='images', mode='color'):
    """
    Generate a "Color Clip Card" where students identify the color.
    
    Args:
        draw: PIL ImageDraw object
        card_rect: Tuple (x1, y1, x2, y2) defining card boundaries
        item: Dict with 'image' and 'label' keys
        color_name: String of the correct color
        color_choices: List of 3 color name strings (including correct)
        errorless: If True, only show correct answer
        folder_type: Image folder type
        mode: 'color' or 'bw' for output mode
    """
    x1, y1, x2, y2 = card_rect
    card_width = x2 - x1
    card_height = y2 - y1
    
    # Draw card border (mode-aware)
    border_color = adjust_for_bw_mode(COLORS['black'], mode)
    draw.rectangle([x1, y1, x2, y2], outline=border_color, width=3)
    
    # Layout
    icon_area_height = int(card_height * 0.50)
    question_area_height = int(card_height * 0.20)
    choices_area_height = int(card_height * 0.30)
    
    # 1. Icon area
    icon_rect = (
        x1 + 30,
        y1 + 30,
        x2 - 30,
        y1 + icon_area_height - 20
    )
    
    try:
        img = load_image(item['image'], folder_type=folder_type)
        if img:
            # Convert to grayscale if BW mode
            if mode == 'bw':
                img = image_to_grayscale(img)
            
            scaled_coords = scale_image_to_fit(img, icon_rect, padding=15)
            if scaled_coords:
                paste_x, paste_y, paste_width, paste_height = scaled_coords
                resized_img = img.resize((paste_width, paste_height), Image.Resampling.LANCZOS)
                if resized_img.mode == 'RGBA':
                    bg = Image.new('RGB', resized_img.size, COLORS['white'])
                    bg.paste(resized_img, mask=resized_img.split()[3])
                    resized_img = bg
                temp_page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
                temp_page.paste(resized_img, (paste_x, paste_y))
                draw._image.paste(temp_page.crop((paste_x, paste_y, paste_x + paste_width, paste_y + paste_height)), (paste_x, paste_y))
    except:
        placeholder = create_placeholder_image(icon_rect[2] - icon_rect[0], icon_rect[3] - icon_rect[1], "Icon")
        draw._image.paste(placeholder, (icon_rect[0], icon_rect[1]))
    
    # 2. Question area
    question_y = y1 + icon_area_height + 10
    question_text = f"Which one is {color_name}?"
    
    try:
        font_question = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except:
        font_question = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), question_text, font=font_question)
    text_width = bbox[2] - bbox[0]
    text_x = x1 + (card_width - text_width) // 2
    text_color = adjust_for_bw_mode(COLORS['black'], mode)
    draw.text((text_x, question_y), question_text, fill=text_color, font=font_question)
    
    # 3. Answer choices
    choices_y_start = y1 + icon_area_height + question_area_height
    
    if errorless:
        display_choices = [color_name]
    else:
        display_choices = color_choices
    
    choice_width = (card_width - 80) // len(display_choices)
    
    try:
        font_choice = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_choice = ImageFont.load_default()
    
    for i, choice in enumerate(display_choices):
        choice_x = x1 + 40 + (i * choice_width)
        choice_y = choices_y_start + 20
        
        # Draw circle (mode-aware)
        circle_radius = 25
        circle_center_x = choice_x + choice_width // 2
        circle_center_y = choice_y
        
        circle_color = adjust_for_bw_mode(COLORS['black'], mode)
        draw.ellipse(
            [circle_center_x - circle_radius, circle_center_y - circle_radius,
             circle_center_x + circle_radius, circle_center_y + circle_radius],
            outline=circle_color, width=3
        )
        
        # Draw choice text
        bbox = draw.textbbox((0, 0), choice, font=font_choice)
        text_width = bbox[2] - bbox[0]
        text_x = circle_center_x - text_width // 2
        text_y = circle_center_y + circle_radius + 10
        text_color = adjust_for_bw_mode(COLORS['black'], mode)
        draw.text((text_x, text_y), choice, fill=text_color, font=font_choice)


def generate_count_clip_card(draw, card_rect, item, count, count_choices, errorless=False, folder_type='images', mode='color'):
    """
    Generate a "Count & Clip" card with multiple icons to count.
    
    Args:
        draw: PIL ImageDraw object
        card_rect: Tuple (x1, y1, x2, y2) defining card boundaries
        item: Dict with 'image' and 'label' keys
        count: Integer of correct count
        count_choices: List of 3 number strings (including correct)
        errorless: If True, only show correct answer
        folder_type: Image folder type
        mode: 'color' or 'bw' for output mode
    """
    x1, y1, x2, y2 = card_rect
    card_width = x2 - x1
    card_height = y2 - y1
    
    # Draw card border (mode-aware)
    border_color = adjust_for_bw_mode(COLORS['black'], mode)
    draw.rectangle([x1, y1, x2, y2], outline=border_color, width=3)
    
    # Layout
    icons_area_height = int(card_height * 0.60)
    question_area_height = int(card_height * 0.15)
    choices_area_height = int(card_height * 0.25)
    
    # 1. Icons area - arrange icons in a cluster
    icons_rect = (
        x1 + 30,
        y1 + 30,
        x2 - 30,
        y1 + icons_area_height - 20
    )
    
    try:
        img = load_image(item['image'], folder_type=folder_type)
        if img:
            # Convert to grayscale if BW mode
            if mode == 'bw':
                img = image_to_grayscale(img)
            
            # Calculate grid for icons
            cols = min(4, count)
            rows = (count + cols - 1) // cols
            
            icon_width = (icons_rect[2] - icons_rect[0] - 20 * (cols - 1)) // cols
            icon_height = (icons_rect[3] - icons_rect[1] - 20 * (rows - 1)) // rows
            icon_size = min(icon_width, icon_height, 150)
            
            # Place icons in grid
            for idx in range(count):
                row = idx // cols
                col = idx % cols
                
                icon_x = icons_rect[0] + col * (icon_size + 20)
                icon_y = icons_rect[1] + row * (icon_size + 20)
                
                resized_img = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
                if resized_img.mode == 'RGBA':
                    bg = Image.new('RGB', resized_img.size, COLORS['white'])
                    bg.paste(resized_img, mask=resized_img.split()[3])
                    resized_img = bg
                draw._image.paste(resized_img, (icon_x, icon_y))
    except:
        # Draw placeholder boxes
        placeholder_color = adjust_for_bw_mode(COLORS['gray'], mode)
        draw.rectangle([icons_rect[0], icons_rect[1], icons_rect[2], icons_rect[3]], 
                      outline=placeholder_color, width=2)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
        draw.text((icons_rect[0] + 20, icons_rect[1] + 20), f"{count} icons", fill=placeholder_color, font=font)
    
    # 2. Question area
    question_y = y1 + icons_area_height + 10
    question_text = "How many?"
    
    try:
        font_question = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except:
        font_question = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), question_text, font=font_question)
    text_width = bbox[2] - bbox[0]
    text_x = x1 + (card_width - text_width) // 2
    text_color = adjust_for_bw_mode(COLORS['black'], mode)
    draw.text((text_x, question_y), question_text, fill=text_color, font=font_question)
    
    # 3. Answer choices
    choices_y_start = y1 + icons_area_height + question_area_height
    
    if errorless:
        display_choices = [str(count)]
    else:
        display_choices = count_choices
    
    choice_width = (card_width - 80) // len(display_choices)
    
    try:
        font_choice = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except:
        font_choice = ImageFont.load_default()
    
    for i, choice in enumerate(display_choices):
        choice_x = x1 + 40 + (i * choice_width)
        choice_y = choices_y_start + 20
        
        # Draw circle (mode-aware)
        circle_radius = 30
        circle_center_x = choice_x + choice_width // 2
        circle_center_y = choice_y
        
        circle_color = adjust_for_bw_mode(COLORS['black'], mode)
        draw.ellipse(
            [circle_center_x - circle_radius, circle_center_y - circle_radius,
             circle_center_x + circle_radius, circle_center_y + circle_radius],
            outline=circle_color, width=3
        )
        
        # Draw number inside circle
        bbox = draw.textbbox((0, 0), choice, font=font_choice)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = circle_center_x - text_width // 2
        text_y = circle_center_y - text_height // 2
        text_color = adjust_for_bw_mode(COLORS['black'], mode)
        draw.text((text_x, text_y), choice, fill=text_color, font=font_choice)


def generate_clip_cards_page(theme_data, card_type='identify', items=None, errorless=False, folder_type='images', mode='color'):
    """
    Generate a page with 4 clip cards in task-box sizing (2×2 grid).
    
    Args:
        theme_data: Dictionary containing theme configuration
        card_type: Type of card ('identify', 'color', 'count', 'emotion')
        items: List of items to use (if None, uses first 4 from theme)
        errorless: If True, only show correct answers
        folder_type: Image folder type
        mode: 'color' or 'bw' for output mode
    
    Returns:
        PIL Image of the page
    """
    # Create page
    page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
    draw = ImageDraw.Draw(page)
    
    # Define 2×2 grid for 4 cards
    # Each card is 1575px × 1200px
    # Pages arranged: [0,1]
    #                 [2,3]
    cards = [
        (0, 0, TASK_BOX_CARD_WIDTH, TASK_BOX_CARD_HEIGHT),  # Top-left
        (TASK_BOX_CARD_WIDTH, 0, TASK_BOX_CARD_WIDTH * 2, TASK_BOX_CARD_HEIGHT),  # Top-right
        (0, TASK_BOX_CARD_HEIGHT, TASK_BOX_CARD_WIDTH, TASK_BOX_CARD_HEIGHT * 2),  # Bottom-left
        (TASK_BOX_CARD_WIDTH, TASK_BOX_CARD_HEIGHT, TASK_BOX_CARD_WIDTH * 2, TASK_BOX_CARD_HEIGHT * 2),  # Bottom-right
    ]
    
    # Get items
    if items is None:
        fringe_icons = theme_data.get('fringe_icons', [])
        items = fringe_icons[:4] if fringe_icons else []
    
    # Generate each card
    for i, card_rect in enumerate(cards):
        if i >= len(items):
            break
        
        item = items[i]
        
        if card_type == 'identify':
            # Create choices: correct answer + 2 random wrong answers
            all_labels = [it['label'] for it in items if it['label'] != item['label']]
            wrong_choices = random.sample(all_labels, min(2, len(all_labels)))
            choices = [item['label']] + wrong_choices
            random.shuffle(choices)
            generate_identify_icon_card(draw, card_rect, item, choices, errorless, folder_type, mode)
        
        elif card_type == 'color':
            # Use color_words from theme
            color_words = theme_data.get('colour_words', ['red', 'blue', 'green', 'yellow'])
            if color_words:
                correct_color = color_words[i % len(color_words)]
                wrong_colors = random.sample([c for c in color_words if c != correct_color], min(2, len(color_words) - 1))
                color_choices = [correct_color] + wrong_colors
                random.shuffle(color_choices)
                generate_color_clip_card(draw, card_rect, item, correct_color, color_choices, errorless, folder_type, mode)
        
        elif card_type == 'count':
            # Generate counting card
            count = random.randint(3, 10)
            wrong_counts = []
            for _ in range(2):
                wrong = count + random.choice([-2, -1, 1, 2])
                if wrong > 0 and wrong not in wrong_counts and wrong != count:
                    wrong_counts.append(str(wrong))
            count_choices = [str(count)] + wrong_counts
            random.shuffle(count_choices)
            generate_count_clip_card(draw, card_rect, item, count, count_choices, errorless, folder_type, mode)
        
        elif card_type == 'emotion':
            # Use emotion_words from theme if available
            emotion_words = theme_data.get('emotion_words', ['happy', 'sad', 'angry', 'surprised'])
            if emotion_words:
                correct_emotion = emotion_words[i % len(emotion_words)]
                wrong_emotions = random.sample([e for e in emotion_words if e != correct_emotion], min(2, len(emotion_words) - 1))
                emotion_choices = [correct_emotion] + wrong_emotions
                random.shuffle(emotion_choices)
                generate_identify_icon_card(draw, card_rect, item, emotion_choices, errorless, folder_type, mode)
    
    return page


def generate_clip_cards(theme_data, output_dir, mode='color'):
    """
    Generate all clip card variations for a theme.
    
    Args:
        theme_data: Dictionary containing theme configuration
        output_dir: Directory to save output PDFs
        mode: 'color' or 'bw' for output mode
    
    Returns:
        List of generated PDF file paths
    """
    generated_files = []
    theme_name = theme_data.get('name', 'Theme')
    
    # Add mode suffix to filenames
    mode_suffix = f"_{mode}" if mode in ['color', 'bw'] else ""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get icons
    fringe_icons = theme_data.get('fringe_icons', [])
    real_images = theme_data.get('real_image_icons', [])
    
    if not fringe_icons:
        print(f"No fringe icons found for theme {theme_name}")
        return generated_files
    
    # 1. Identify the Icon cards
    pages = []
    for i in range(0, len(fringe_icons), 4):
        batch = fringe_icons[i:i+4]
        page = generate_clip_cards_page(theme_data, 'identify', batch, errorless=False, folder_type='images', mode=mode)
        pages.append(page)
    
    if pages:
        # Add page numbers and footers
        for idx, page in enumerate(pages):
            draw = ImageDraw.Draw(page)
            draw_copyright_footer(draw, FOOTER_TEXT)
            draw_page_number(draw, idx + 1, len(pages))
        
        filename = f"{theme_name}_Clip_Cards_Identify_Icon{mode_suffix}.pdf"
        filepath = os.path.join(output_dir, filename)
        save_images_as_pdf(pages, filepath, f"{theme_name} - Identify Icon Clip Cards ({mode})")
        generated_files.append(filepath)
        print(f"Generated: {filename}")
    
    # 2. Color Clip Cards
    if theme_data.get('colour_words'):
        pages = []
        for i in range(0, min(len(fringe_icons), 8), 4):
            batch = fringe_icons[i:i+4]
            page = generate_clip_cards_page(theme_data, 'color', batch, errorless=False, folder_type='images', mode=mode)
            pages.append(page)
        
        if pages:
            for idx, page in enumerate(pages):
                draw = ImageDraw.Draw(page)
                draw_copyright_footer(draw, FOOTER_TEXT)
                draw_page_number(draw, idx + 1, len(pages))
            
            filename = f"{theme_name}_Clip_Cards_Color{mode_suffix}.pdf"
            filepath = os.path.join(output_dir, filename)
            save_images_as_pdf(pages, filepath, f"{theme_name} - Color Clip Cards ({mode})")
            generated_files.append(filepath)
            print(f"Generated: {filename}")
    
    # 3. Count & Clip Cards
    pages = []
    for i in range(0, min(len(fringe_icons), 8), 4):
        batch = fringe_icons[i:i+4]
        page = generate_clip_cards_page(theme_data, 'count', batch, errorless=False, folder_type='images', mode=mode)
        pages.append(page)
    
    if pages:
        for idx, page in enumerate(pages):
            draw = ImageDraw.Draw(page)
            draw_copyright_footer(draw, FOOTER_TEXT)
            draw_page_number(draw, idx + 1, len(pages))
        
        filename = f"{theme_name}_Clip_Cards_Count{mode_suffix}.pdf"
        filepath = os.path.join(output_dir, filename)
        save_images_as_pdf(pages, filepath, f"{theme_name} - Count & Clip Cards ({mode})")
        generated_files.append(filepath)
        print(f"Generated: {filename}")
    
    # 4. Errorless Identify Icon
    pages = []
    for i in range(0, min(len(fringe_icons), 8), 4):
        batch = fringe_icons[i:i+4]
        page = generate_clip_cards_page(theme_data, 'identify', batch, errorless=True, folder_type='images', mode=mode)
        pages.append(page)
    
    if pages:
        for idx, page in enumerate(pages):
            draw = ImageDraw.Draw(page)
            draw_copyright_footer(draw, FOOTER_TEXT)
            draw_page_number(draw, idx + 1, len(pages))
        
        filename = f"{theme_name}_Clip_Cards_Errorless{mode_suffix}.pdf"
        filepath = os.path.join(output_dir, filename)
        save_images_as_pdf(pages, filepath, f"{theme_name} - Errorless Clip Cards ({mode})")
        generated_files.append(filepath)
        print(f"Generated: {filename}")
    
    # 5. Real Image version (if available)
    if real_images:
        pages = []
        for i in range(0, min(len(real_images), 8), 4):
            batch = real_images[i:i+4]
            page = generate_clip_cards_page(theme_data, 'identify', batch, errorless=False, folder_type='real_images', mode=mode)
            pages.append(page)
        
        if pages:
            for idx, page in enumerate(pages):
                draw = ImageDraw.Draw(page)
                draw_copyright_footer(draw, FOOTER_TEXT)
                draw_page_number(draw, idx + 1, len(pages))
            
            filename = f"{theme_name}_Clip_Cards_Real_Images{mode_suffix}.pdf"
            filepath = os.path.join(output_dir, filename)
            save_images_as_pdf(pages, filepath, f"{theme_name} - Real Image Clip Cards ({mode})")
            generated_files.append(filepath)
            print(f"Generated: {filename}")
    
    # Generate storage label (only once, not mode-specific)
    if mode == 'color':
        label_path = create_companion_label(
            theme_data,
            "Clip Cards",
            "Multiple choice clip cards for identification, counting, and color recognition",
            output_dir
        )
        if label_path:
            generated_files.append(label_path)
    
    return generated_files


def generate_clip_cards_dual_mode(theme_data, output_dir):
    """
    Generate clip cards in both color and black-and-white modes.
    
    Args:
        theme_data: Dictionary containing theme configuration
        output_dir: Directory to save output PDFs
    
    Returns:
        Dictionary with 'color' and 'bw' keys containing lists of file paths
    """
    print(f"\n{'='*60}")
    print(f"Generating Clip Cards (Dual-Mode)")
    print(f"Theme: {theme_data.get('name', 'Unknown')}")
    print(f"{'='*60}\n")
    
    results = {
        'color': [],
        'bw': []
    }
    
    # Generate color version
    print("=== COLOR version ===")
    results['color'] = generate_clip_cards(theme_data, output_dir, mode='color')
    
    # Generate black-and-white version
    print("\n=== BLACK-AND-WHITE version ===")
    results['bw'] = generate_clip_cards(theme_data, output_dir, mode='bw')
    
    print(f"\n{'='*60}")
    print(f"Clip Cards Generation Complete")
    print(f"Color PDFs: {len(results['color'])}")
    print(f"BW PDFs: {len(results['bw'])}")
    print(f"{'='*60}\n")
    
    return results


if __name__ == "__main__":
    # Test with a sample theme
    test_theme = {
        'name': 'Test Theme',
        'fringe_icons': [
            {'image': 'apple.png', 'label': 'apple'},
            {'image': 'ball.png', 'label': 'ball'},
            {'image': 'cat.png', 'label': 'cat'},
            {'image': 'dog.png', 'label': 'dog'},
            {'image': 'elephant.png', 'label': 'elephant'},
            {'image': 'fish.png', 'label': 'fish'},
        ],
        'colour_words': ['red', 'blue', 'green', 'yellow', 'purple'],
        'emotion_words': ['happy', 'sad', 'angry', 'surprised']
    }
    
    output_directory = "output/clip_cards_test"
    files = generate_clip_cards(test_theme, output_directory)
    print(f"\nGenerated {len(files)} files:")
    for f in files:
        print(f"  - {f}")
