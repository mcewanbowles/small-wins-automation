"""
Label the Picture Generator

Generates vocabulary and comprehension cards where students label pictures
with cut-and-paste word cards or drag-and-drop labels.

Uses task-box sizing standard (5.25" x 4", 4 per page).
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.draw_helpers import (
    create_canvas, draw_task_box_grid, get_theme_fonts,
    get_theme_colors, add_footer, draw_storage_label
)


def generate_label_cards(theme_data, output_dir, card_type="cut_paste"):
    """
    Generate label the picture cards.
    
    Args:
        theme_data: Dictionary with theme configuration
        output_dir: Directory to save generated PDFs
        card_type: Type of card ('cut_paste', 'drag_drop', 'write_label', 'errorless')
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    theme_name = theme_data.get('name', 'Theme')
    fringe_icons = theme_data.get('fringe_icons', [])
    
    if not fringe_icons:
        print(f"No fringe icons found for {theme_name}")
        return
    
    fonts = get_theme_fonts(theme_data)
    colors = get_theme_colors(theme_data)
    
    # Task-box dimensions at 300 DPI
    card_width = 1575  # 5.25 inches
    card_height = 1200  # 4 inches
    
    cards = []
    page_num = 1
    
    for icon_data in fringe_icons:
        if isinstance(icon_data, dict):
            word = icon_data.get('word', 'item')
            icon_path = icon_data.get('icon_path', '')
        else:
            word = str(icon_data)
            icon_path = ''
        
        # Create card based on type
        if card_type == "cut_paste":
            card = create_cut_paste_card(word, icon_path, card_width, card_height, fonts, colors)
        elif card_type == "drag_drop":
            card = create_drag_drop_card(word, icon_path, card_width, card_height, fonts, colors)
        elif card_type == "write_label":
            card = create_write_label_card(word, icon_path, card_width, card_height, fonts, colors)
        elif card_type == "errorless":
            card = create_errorless_card(word, icon_path, card_width, card_height, fonts, colors)
        else:
            continue
        
        cards.append(card)
    
    # Arrange in 2x2 grid pages
    pages = []
    for i in range(0, len(cards), 4):
        page_cards = cards[i:i+4]
        
        # Create page with 2x2 grid
        page = create_canvas()
        page = draw_task_box_grid(page, page_cards)
        page = add_footer(page, theme_name, page_num)
        pages.append(page)
        page_num += 1
    
    # Save PDF
    card_type_names = {
        "cut_paste": "Cut and Paste Labels",
        "drag_drop": "Drag and Drop Labels",
        "write_label": "Write the Label",
        "errorless": "Errorless Labeling"
    }
    
    if pages:
        filename = f"{theme_name.replace(' ', '_')}_Label_Picture_{card_type}.pdf"
        filepath = output_path / filename
        pages[0].save(
            filepath,
            save_all=True,
            append_images=pages[1:] if len(pages) > 1 else [],
            resolution=300.0
        )
        print(f"Generated: {filepath}")
        
        # Generate storage label
        label_title = card_type_names.get(card_type, "Label Cards")
        label_path = output_path / f"{theme_name.replace(' ', '_')}_Label_{card_type}_storage_label.pdf"
        storage_label = draw_storage_label(theme_name, label_title, fonts, colors)
        storage_label.save(label_path, resolution=300.0)
        print(f"Generated storage label: {label_path}")


def create_cut_paste_card(word, icon_path, width, height, fonts, colors):
    """Create a cut-and-paste labeling card."""
    card = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(card)
    
    # Draw border
    border_color = colors.get('primary', '#333333')
    draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=4)
    
    # Title area (10% of height)
    title_height = int(height * 0.10)
    draw.text(
        (width//2, title_height//2),
        "Label the Picture",
        fill=border_color,
        font=fonts['title_small'],
        anchor="mm"
    )
    
    # Draw line under title
    draw.line([(20, title_height), (width-20, title_height)], 
              fill=border_color, width=2)
    
    # Icon area (50% of height)
    icon_top = title_height + 20
    icon_height = int(height * 0.50)
    icon_bottom = icon_top + icon_height
    
    # Draw icon placeholder box
    icon_box_margin = 100
    icon_box = [icon_box_margin, icon_top + 30, width - icon_box_margin, icon_bottom - 30]
    draw.rectangle(icon_box, outline=border_color, width=3)
    
    # Icon placeholder text
    draw.text(
        (width//2, (icon_top + icon_bottom)//2),
        f"[{word.upper()}]",
        fill='#888888',
        font=fonts['body'],
        anchor="mm"
    )
    
    # Label placement area (40% of height)
    label_area_top = icon_bottom + 10
    
    # Draw dotted box for label placement
    box_height = 80
    box_width = width - 200
    box_left = (width - box_width) // 2
    box_top = label_area_top + 20
    
    # Draw dashed rectangle
    draw_dashed_rectangle(draw, [box_left, box_top, box_left + box_width, box_top + box_height],
                          border_color, width=3, dash_length=10)
    
    # "Paste label here" text
    draw.text(
        (width//2, box_top + box_height//2),
        "Paste label here",
        fill='#BBBBBB',
        font=fonts['body_small'],
        anchor="mm"
    )
    
    return card


def create_drag_drop_card(word, icon_path, width, height, fonts, colors):
    """Create a drag-and-drop labeling card with multiple choice options."""
    card = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(card)
    
    border_color = colors.get('primary', '#333333')
    draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=4)
    
    # Title
    title_height = int(height * 0.10)
    draw.text(
        (width//2, title_height//2),
        "Which label matches?",
        fill=border_color,
        font=fonts['title_small'],
        anchor="mm"
    )
    draw.line([(20, title_height), (width-20, title_height)], 
              fill=border_color, width=2)
    
    # Icon area (45%)
    icon_top = title_height + 20
    icon_height = int(height * 0.45)
    icon_bottom = icon_top + icon_height
    
    icon_box_margin = 100
    icon_box = [icon_box_margin, icon_top + 20, width - icon_box_margin, icon_bottom - 20]
    draw.rectangle(icon_box, outline=border_color, width=3)
    
    draw.text(
        (width//2, (icon_top + icon_bottom)//2),
        f"[{word.upper()}]",
        fill='#888888',
        font=fonts['body'],
        anchor="mm"
    )
    
    # Choice boxes area (45%)
    choice_area_top = icon_bottom + 10
    choice_height = int(height * 0.45) - 20
    
    # Three choice boxes horizontally
    num_choices = 3
    choice_box_width = (width - 100) // num_choices
    choice_box_height = 70
    
    y_pos = choice_area_top + (choice_height - choice_box_height) // 2
    
    # Example choices (in practice, would use real alternatives)
    choices = [word, "word1", "word2"]
    
    for i in range(num_choices):
        x_left = 40 + (i * choice_box_width)
        x_right = x_left + choice_box_width - 20
        
        # Draw choice box
        draw.rectangle([x_left, y_pos, x_right, y_pos + choice_box_height],
                      outline=border_color, width=2)
        
        # Draw word (correct word in first position)
        choice_text = choices[i] if i < len(choices) else f"option{i+1}"
        draw.text(
            ((x_left + x_right)//2, y_pos + choice_box_height//2),
            choice_text,
            fill=border_color,
            font=fonts['body'],
            anchor="mm"
        )
    
    return card


def create_write_label_card(word, icon_path, width, height, fonts, colors):
    """Create a write-the-label card with writing lines."""
    card = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(card)
    
    border_color = colors.get('primary', '#333333')
    draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=4)
    
    # Title
    title_height = int(height * 0.10)
    draw.text(
        (width//2, title_height//2),
        "Write the Label",
        fill=border_color,
        font=fonts['title_small'],
        anchor="mm"
    )
    draw.line([(20, title_height), (width-20, title_height)], 
              fill=border_color, width=2)
    
    # Icon area (50%)
    icon_top = title_height + 20
    icon_height = int(height * 0.50)
    icon_bottom = icon_top + icon_height
    
    icon_box_margin = 100
    icon_box = [icon_box_margin, icon_top + 20, width - icon_box_margin, icon_bottom - 20]
    draw.rectangle(icon_box, outline=border_color, width=3)
    
    draw.text(
        (width//2, (icon_top + icon_bottom)//2),
        f"[{word.upper()}]",
        fill='#888888',
        font=fonts['body'],
        anchor="mm"
    )
    
    # Writing lines area (40%)
    line_area_top = icon_bottom + 20
    line_spacing = 50
    line_left = 100
    line_right = width - 100
    
    # Draw 3 writing lines
    for i in range(3):
        y = line_area_top + (i * line_spacing)
        # Baseline
        draw.line([(line_left, y), (line_right, y)], fill=border_color, width=2)
        # Midline (dashed)
        draw_dashed_line(draw, line_left, y - 20, line_right, y - 20, '#AAAAAA', width=1)
    
    return card


def create_errorless_card(word, icon_path, width, height, fonts, colors):
    """Create an errorless labeling card with only the correct answer."""
    card = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(card)
    
    border_color = colors.get('primary', '#333333')
    draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=4)
    
    # Title
    title_height = int(height * 0.10)
    draw.text(
        (width//2, title_height//2),
        "Match the Label",
        fill=border_color,
        font=fonts['title_small'],
        anchor="mm"
    )
    draw.line([(20, title_height), (width-20, title_height)], 
              fill=border_color, width=2)
    
    # Icon area (50%)
    icon_top = title_height + 20
    icon_height = int(height * 0.50)
    icon_bottom = icon_top + icon_height
    
    icon_box_margin = 100
    icon_box = [icon_box_margin, icon_top + 20, width - icon_box_margin, icon_bottom - 20]
    draw.rectangle(icon_box, outline=border_color, width=3)
    
    draw.text(
        (width//2, (icon_top + icon_bottom)//2),
        f"[{word.upper()}]",
        fill='#888888',
        font=fonts['body'],
        anchor="mm"
    )
    
    # Single choice box (errorless - only correct answer)
    choice_area_top = icon_bottom + 20
    box_width = width - 200
    box_height = 80
    box_left = (width - box_width) // 2
    box_top = choice_area_top + 20
    
    # Draw the answer box
    draw.rectangle([box_left, box_top, box_left + box_width, box_top + box_height],
                  outline=border_color, width=3, fill='#F0F0F0')
    
    # Draw the word
    draw.text(
        (width//2, box_top + box_height//2),
        word,
        fill=border_color,
        font=fonts['body_large'],
        anchor="mm"
    )
    
    return card


def draw_dashed_rectangle(draw, coords, color, width=1, dash_length=10):
    """Draw a dashed rectangle."""
    x1, y1, x2, y2 = coords
    
    # Top line
    draw_dashed_line(draw, x1, y1, x2, y1, color, width, dash_length)
    # Right line
    draw_dashed_line(draw, x2, y1, x2, y2, color, width, dash_length)
    # Bottom line
    draw_dashed_line(draw, x2, y2, x1, y2, color, width, dash_length)
    # Left line
    draw_dashed_line(draw, x1, y2, x1, y1, color, width, dash_length)


def draw_dashed_line(draw, x1, y1, x2, y2, color, width=1, dash_length=10):
    """Draw a dashed line."""
    import math
    
    # Calculate line length and angle
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx*dx + dy*dy)
    
    if length == 0:
        return
    
    # Normalize direction
    dx_norm = dx / length
    dy_norm = dy / length
    
    # Draw dashes
    pos = 0
    while pos < length:
        dash_end = min(pos + dash_length, length)
        
        start_x = x1 + dx_norm * pos
        start_y = y1 + dy_norm * pos
        end_x = x1 + dx_norm * dash_end
        end_y = y1 + dy_norm * dash_end
        
        draw.line([(start_x, start_y), (end_x, end_y)], fill=color, width=width)
        
        pos += dash_length * 2  # Skip gap


def generate_all_label_cards(theme_data, output_dir):
    """Generate all types of label the picture cards."""
    card_types = ["cut_paste", "drag_drop", "write_label", "errorless"]
    
    for card_type in card_types:
        generate_label_cards(theme_data, output_dir, card_type)


if __name__ == "__main__":
    # Example usage
    sample_theme = {
        "name": "Brown Bear",
        "fonts": {
            "title": "Arial-Bold",
            "body": "Arial"
        },
        "colors": {
            "primary": "#8B4513",
            "secondary": "#D2691E"
        },
        "fringe_icons": [
            {"word": "bear", "icon_path": ""},
            {"word": "bird", "icon_path": ""},
            {"word": "duck", "icon_path": ""},
            {"word": "horse", "icon_path": ""},
            {"word": "frog", "icon_path": ""},
            {"word": "cat", "icon_path": ""},
            {"word": "dog", "icon_path": ""},
            {"word": "sheep", "icon_path": ""}
        ]
    }
    
    output_directory = Path(__file__).parent.parent / "output" / "label_picture"
    generate_all_label_cards(sample_theme, output_directory)
    print("Label the Picture cards generation complete!")
