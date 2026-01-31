"""
I Spy / Find & Count Generator
Creates visual discrimination and counting activities using task-box sizing standard.
Supports dual-mode output: color and black-and-white.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from utils.draw_helpers import (
    draw_task_box_grid,
    draw_footer,
    add_storage_label,
    get_theme_colors
)
import os


def hex_to_grayscale_reportlab(hex_color):
    """Convert hex color to grayscale using luminosity method."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    return colors.Color(gray, gray, gray)


def generate_i_spy_cards(theme_data, output_folder, mode='color'):
    """
    Generate I Spy and Find & Count activity cards.
    
    Card Types:
    1. I Spy - Find all instances of target icon
    2. Find & Count - Count specific icons and write/select number
    3. How Many? - Count and select from multiple choice
    4. Errorless Count - Only correct number option shown
    
    Args:
        theme_data: Theme data dictionary
        output_folder: Output directory path
        mode: 'color' or 'bw' for black-and-white mode
    """
    
    theme_name = theme_data.get("theme_name", "Theme")
    theme_colors = get_theme_colors(theme_data)
    
    # Convert colors to grayscale in BW mode
    if mode == 'bw':
        theme_colors = {
            k: hex_to_grayscale_reportlab(v) if isinstance(v, str) else colors.black
            for k, v in theme_colors.items()
        }
    
    fringe_icons = theme_data.get("fringe_icons", [])
    
    if not fringe_icons or len(fringe_icons) < 3:
        print(f"Warning: Need at least 3 fringe icons for {theme_name}")
        return
    
    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Generate all card types
    _generate_i_spy_cards(theme_data, output_folder, theme_colors, mode)
    _generate_find_and_count_cards(theme_data, output_folder, theme_colors, mode)
    _generate_how_many_cards(theme_data, output_folder, theme_colors, mode)
    _generate_errorless_count_cards(theme_data, output_folder, theme_colors, mode)
    
    print(f"✓ I Spy / Find & Count cards generated for {theme_name} ({mode} mode)")


def _generate_i_spy_cards(theme_data, output_folder, theme_colors, mode='color'):
    """Generate I Spy cards - find all instances of target icon."""
    
    theme_name = theme_data.get("theme_name", "Theme")
    fringe_icons = theme_data.get("fringe_icons", [])
    
    mode_suffix = f"_{mode}" if mode else ""
    filename = os.path.join(output_folder, f"{theme_name}_I_Spy_Cards{mode_suffix}.pdf")
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    page_num = 1
    cards_on_page = 0
    
    # Use first 8 icons for variety
    target_icons = fringe_icons[:8]
    
    for icon_data in target_icons:
        icon_name = icon_data.get("name", "Item")
        icon_path = icon_data.get("path", "")
        
        # Get position for this card in 2x2 grid
        row = cards_on_page // 2
        col = cards_on_page % 2
        
        # Draw task box borders
        if cards_on_page == 0:
            draw_task_box_grid(c)
        
        # Calculate card position
        card_width = 5.25 * inch
        card_height = 4 * inch
        x = 0.5 * inch + (col * card_width)
        y = height - (0.5 * inch + card_height) - (row * card_height)
        
        # Draw card content
        _draw_i_spy_card(c, x, y, card_width, card_height, icon_name, icon_path, 
                        theme_colors, fringe_icons)
        
        cards_on_page += 1
        
        # New page after 4 cards
        if cards_on_page >= 4:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            cards_on_page = 0
    
    # Final page
    if cards_on_page > 0:
        draw_footer(c, page_num)
    
    c.save()
    
    # Add storage label
    add_storage_label(filename, f"{theme_name} - I Spy Cards")


def _draw_i_spy_card(c, x, y, width, height, target_name, target_path, 
                     theme_colors, all_icons):
    """Draw an individual I Spy card."""
    
    # Title area (15% of card)
    title_height = height * 0.15
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.black)
    title_text = f"I Spy {target_name}!"
    text_width = c.stringWidth(title_text, "Helvetica-Bold", 18)
    c.drawString(x + (width - text_width) / 2, y + height - title_height / 2 - 6, title_text)
    
    # Target icon area (20% of card) - show what to find
    target_area_y = y + height - title_height - (height * 0.20)
    c.setFont("Helvetica", 12)
    c.drawString(x + 10, target_area_y + 50, "Find:")
    
    # Placeholder for target icon
    icon_box_size = 60
    icon_x = x + width / 2 - icon_box_size / 2
    c.setStrokeColor(theme_colors["primary"])
    c.setLineWidth(2)
    c.rect(icon_x, target_area_y, icon_box_size, icon_box_size, stroke=1, fill=0)
    c.setFont("Helvetica", 10)
    c.drawCentredString(icon_x + icon_box_size / 2, target_area_y + icon_box_size / 2 - 5, 
                       target_name[:15])
    
    # Search area (60% of card) - scattered icons including target
    search_area_y = y + 20
    search_area_height = height * 0.60
    
    c.setStrokeColor(colors.grey)
    c.setLineWidth(1)
    c.rect(x + 10, search_area_y, width - 20, search_area_height, stroke=1, fill=0)
    
    # Place icons in grid pattern (3x4 = 12 icons, 3-5 are target)
    import random
    random.seed(hash(target_name))  # Consistent placement
    
    num_targets = random.randint(3, 5)
    num_distractors = 12 - num_targets
    
    # Create list of icons to place
    icons_to_place = [target_name] * num_targets
    
    # Add distractor icons
    distractor_pool = [icon.get("name", "") for icon in all_icons if icon.get("name") != target_name]
    if distractor_pool:
        for _ in range(num_distractors):
            icons_to_place.append(random.choice(distractor_pool[:6]))
    
    random.shuffle(icons_to_place)
    
    # Draw icons in 4x3 grid
    icon_size = 40
    spacing_x = (width - 20 - (3 * icon_size)) / 4
    spacing_y = (search_area_height - (4 * icon_size)) / 5
    
    idx = 0
    for row in range(4):
        for col in range(3):
            if idx >= len(icons_to_place):
                break
            
            icon_x = x + 10 + spacing_x + col * (icon_size + spacing_x)
            icon_y = search_area_y + search_area_height - spacing_y - (row + 1) * (icon_size + spacing_y)
            
            # Draw icon placeholder
            c.setStrokeColor(colors.grey)
            c.setLineWidth(0.5)
            c.rect(icon_x, icon_y, icon_size, icon_size, stroke=1, fill=0)
            
            # Label
            c.setFont("Helvetica", 6)
            c.drawCentredString(icon_x + icon_size / 2, icon_y + icon_size / 2 - 3, 
                               icons_to_place[idx][:10])
            
            idx += 1
    
    # Count circles at bottom
    c.setFont("Helvetica", 10)
    c.drawString(x + 10, y + 5, f"I found: ___ {target_name}")


def _generate_find_and_count_cards(theme_data, output_folder, theme_colors, mode='color'):
    """Generate Find & Count cards - count and write the number."""
    
    theme_name = theme_data.get("theme_name", "Theme")
    fringe_icons = theme_data.get("fringe_icons", [])
    
    mode_suffix = f"_{mode}" if mode else ""
    filename = os.path.join(output_folder, f"{theme_name}_Find_Count_Cards{mode_suffix}.pdf")
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    page_num = 1
    cards_on_page = 0
    
    # Use icons for counting (3-10 instances)
    for icon_data in fringe_icons[:8]:
        icon_name = icon_data.get("name", "Item")
        
        import random
        random.seed(hash(icon_name))
        count_target = random.randint(3, 10)
        
        # Get position
        row = cards_on_page // 2
        col = cards_on_page % 2
        
        if cards_on_page == 0:
            draw_task_box_grid(c)
        
        card_width = 5.25 * inch
        card_height = 4 * inch
        x = 0.5 * inch + (col * card_width)
        y = height - (0.5 * inch + card_height) - (row * card_height)
        
        _draw_find_count_card(c, x, y, card_width, card_height, icon_name, 
                             count_target, theme_colors)
        
        cards_on_page += 1
        
        if cards_on_page >= 4:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            cards_on_page = 0
    
    if cards_on_page > 0:
        draw_footer(c, page_num)
    
    c.save()
    add_storage_label(filename, f"{theme_name} - Find & Count Cards")


def _draw_find_count_card(c, x, y, width, height, icon_name, count, theme_colors):
    """Draw Find & Count card."""
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.black)
    title = f"Count the {icon_name}"
    text_width = c.stringWidth(title, "Helvetica-Bold", 16)
    c.drawString(x + (width - text_width) / 2, y + height - 30, title)
    
    # Icon display area (65% of card)
    display_height = height * 0.65
    display_y = y + height * 0.25
    
    c.setStrokeColor(colors.grey)
    c.setLineWidth(1)
    c.rect(x + 10, display_y, width - 20, display_height, stroke=1, fill=0)
    
    # Place icons in scattered pattern
    import random
    random.seed(hash(icon_name + str(count)))
    
    icon_size = 35
    positions_used = []
    
    for i in range(count):
        # Find non-overlapping position
        max_attempts = 50
        for attempt in range(max_attempts):
            pos_x = x + 10 + random.randint(5, int(width - 20 - icon_size - 5))
            pos_y = display_y + random.randint(5, int(display_height - icon_size - 5))
            
            # Check overlap
            overlap = False
            for prev_x, prev_y in positions_used:
                if abs(pos_x - prev_x) < icon_size + 5 and abs(pos_y - prev_y) < icon_size + 5:
                    overlap = True
                    break
            
            if not overlap or attempt == max_attempts - 1:
                positions_used.append((pos_x, pos_y))
                break
        
        # Draw icon
        c.setStrokeColor(theme_colors["primary"])
        c.setLineWidth(1)
        c.rect(pos_x, pos_y, icon_size, icon_size, stroke=1, fill=0)
        c.setFont("Helvetica", 6)
        c.drawCentredString(pos_x + icon_size / 2, pos_y + icon_size / 2 - 3, icon_name[:8])
    
    # Answer area (20% of card)
    answer_y = y + 20
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x + 20, answer_y + 40, "How many?")
    
    # Writing lines
    line_y = answer_y + 15
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    
    # Number writing box
    box_width = 80
    box_x = x + width / 2 - box_width / 2
    c.rect(box_x, line_y - 5, box_width, 30, stroke=1, fill=0)
    
    c.setFont("Helvetica", 10)
    c.drawString(box_x + box_width + 10, line_y + 5, icon_name)


def _generate_how_many_cards(theme_data, output_folder, theme_colors, mode='color'):
    """Generate How Many cards - multiple choice counting."""
    
    theme_name = theme_data.get("theme_name", "Theme")
    fringe_icons = theme_data.get("fringe_icons", [])
    
    mode_suffix = f"_{mode}" if mode else ""
    filename = os.path.join(output_folder, f"{theme_name}_How_Many_Cards{mode_suffix}.pdf")
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    page_num = 1
    cards_on_page = 0
    
    for icon_data in fringe_icons[:8]:
        icon_name = icon_data.get("name", "Item")
        
        import random
        random.seed(hash(icon_name + "howmany"))
        count_target = random.randint(4, 9)
        
        row = cards_on_page // 2
        col = cards_on_page % 2
        
        if cards_on_page == 0:
            draw_task_box_grid(c)
        
        card_width = 5.25 * inch
        card_height = 4 * inch
        x = 0.5 * inch + (col * card_width)
        y = height - (0.5 * inch + card_height) - (row * card_height)
        
        _draw_how_many_card(c, x, y, card_width, card_height, icon_name, 
                           count_target, theme_colors)
        
        cards_on_page += 1
        
        if cards_on_page >= 4:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            cards_on_page = 0
    
    if cards_on_page > 0:
        draw_footer(c, page_num)
    
    c.save()
    add_storage_label(filename, f"{theme_name} - How Many Cards")


def _draw_how_many_card(c, x, y, width, height, icon_name, correct_count, theme_colors):
    """Draw How Many card with multiple choice."""
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    title = f"How many {icon_name}?"
    text_width = c.stringWidth(title, "Helvetica-Bold", 16)
    c.drawString(x + (width - text_width) / 2, y + height - 30, title)
    
    # Icon display area
    display_height = height * 0.55
    display_y = y + height * 0.30
    
    c.setStrokeColor(colors.grey)
    c.setLineWidth(1)
    c.rect(x + 10, display_y, width - 20, display_height, stroke=1, fill=0)
    
    # Place icons (similar to find & count)
    import random
    random.seed(hash(icon_name + str(correct_count) + "mc"))
    
    icon_size = 30
    positions = []
    
    for i in range(correct_count):
        for attempt in range(50):
            pos_x = x + 10 + random.randint(5, int(width - 20 - icon_size - 5))
            pos_y = display_y + random.randint(5, int(display_height - icon_size - 5))
            
            overlap = False
            for prev_x, prev_y in positions:
                if abs(pos_x - prev_x) < icon_size + 5 and abs(pos_y - prev_y) < icon_size + 5:
                    overlap = True
                    break
            
            if not overlap or attempt == 49:
                positions.append((pos_x, pos_y))
                break
        
        # Draw icon
        c.setStrokeColor(theme_colors["primary"])
        c.rect(pos_x, pos_y, icon_size, icon_size, stroke=1, fill=0)
        c.setFont("Helvetica", 5)
        c.drawCentredString(pos_x + icon_size / 2, pos_y + icon_size / 2 - 2, icon_name[:8])
    
    # Multiple choice area (25% of card)
    choice_y = y + 15
    
    # Generate 3 choices
    choices = [correct_count]
    while len(choices) < 3:
        distractor = correct_count + random.randint(-3, 3)
        if distractor > 0 and distractor != correct_count and distractor not in choices:
            choices.append(distractor)
    
    random.shuffle(choices)
    
    # Draw choice circles
    circle_spacing = (width - 40) / 3
    for i, num in enumerate(choices):
        circle_x = x + 20 + i * circle_spacing + circle_spacing / 2
        circle_y = choice_y + 30
        
        # Circle
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.circle(circle_x, circle_y, 15, stroke=1, fill=0)
        
        # Number
        c.setFont("Helvetica-Bold", 16)
        num_str = str(num)
        num_width = c.stringWidth(num_str, "Helvetica-Bold", 16)
        c.drawString(circle_x - num_width / 2, circle_y - 6, num_str)


def _generate_errorless_count_cards(theme_data, output_folder, theme_colors, mode='color'):
    """Generate Errorless Count cards - only correct answer shown."""
    
    theme_name = theme_data.get("theme_name", "Theme")
    fringe_icons = theme_data.get("fringe_icons", [])
    
    mode_suffix = f"_{mode}" if mode else ""
    filename = os.path.join(output_folder, f"{theme_name}_Errorless_Count_Cards{mode_suffix}.pdf")
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    page_num = 1
    cards_on_page = 0
    
    for icon_data in fringe_icons[:8]:
        icon_name = icon_data.get("name", "Item")
        
        import random
        random.seed(hash(icon_name + "errorless"))
        count_target = random.randint(3, 8)
        
        row = cards_on_page // 2
        col = cards_on_page % 2
        
        if cards_on_page == 0:
            draw_task_box_grid(c)
        
        card_width = 5.25 * inch
        card_height = 4 * inch
        x = 0.5 * inch + (col * card_width)
        y = height - (0.5 * inch + card_height) - (row * card_height)
        
        _draw_errorless_count_card(c, x, y, card_width, card_height, icon_name, 
                                   count_target, theme_colors)
        
        cards_on_page += 1
        
        if cards_on_page >= 4:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            cards_on_page = 0
    
    if cards_on_page > 0:
        draw_footer(c, page_num)
    
    c.save()
    add_storage_label(filename, f"{theme_name} - Errorless Count Cards")


def _draw_errorless_count_card(c, x, y, width, height, icon_name, count, theme_colors):
    """Draw Errorless Count card."""
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    title = f"Count the {icon_name}"
    text_width = c.stringWidth(title, "Helvetica-Bold", 16)
    c.drawString(x + (width - text_width) / 2, y + height - 30, title)
    
    # Icon display area
    display_height = height * 0.55
    display_y = y + height * 0.30
    
    c.setStrokeColor(colors.grey)
    c.setLineWidth(1)
    c.rect(x + 10, display_y, width - 20, display_height, stroke=1, fill=0)
    
    # Place icons in organized rows
    icon_size = 35
    icons_per_row = min(count, 4)
    num_rows = (count + icons_per_row - 1) // icons_per_row
    
    spacing_x = (width - 20 - (icons_per_row * icon_size)) / (icons_per_row + 1)
    spacing_y = (display_height - (num_rows * icon_size)) / (num_rows + 1)
    
    idx = 0
    for row in range(num_rows):
        icons_in_row = min(icons_per_row, count - idx)
        for col in range(icons_in_row):
            icon_x = x + 10 + spacing_x + col * (icon_size + spacing_x)
            icon_y = display_y + display_height - spacing_y - (row + 1) * (icon_size + spacing_y)
            
            c.setStrokeColor(theme_colors["primary"])
            c.setLineWidth(1)
            c.rect(icon_x, icon_y, icon_size, icon_size, stroke=1, fill=0)
            c.setFont("Helvetica", 6)
            c.drawCentredString(icon_x + icon_size / 2, icon_y + icon_size / 2 - 3, icon_name[:8])
            
            idx += 1
    
    # Answer area - single correct choice
    answer_y = y + 20
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x + 20, answer_y + 40, "How many?")
    
    # Single answer circle with correct number
    circle_x = x + width / 2
    circle_y = answer_y + 20
    
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.lightgrey)
    c.setLineWidth(2)
    c.circle(circle_x, circle_y, 20, stroke=1, fill=1)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 20)
    num_str = str(count)
    num_width = c.stringWidth(num_str, "Helvetica-Bold", 20)
    c.drawString(circle_x - num_width / 2, circle_y - 7, num_str)


def generate_i_spy_dual_mode(theme_data, output_folder):
    """
    Generate I Spy / Find & Count cards in both color and black-and-white modes.
    
    Args:
        theme_data: Theme data dictionary
        output_folder: Output directory path
    
    Returns:
        dict: Paths to generated PDFs {'color': [...], 'bw': [...]}
    """
    color_files = []
    bw_files = []
    
    # Generate color version
    print("=== Generating COLOR version ===")
    generate_i_spy_cards(theme_data, output_folder, mode='color')
    
    # Generate black-and-white version
    print("=== Generating BLACK-AND-WHITE version ===")
    generate_i_spy_cards(theme_data, output_folder, mode='bw')
    
    theme_name = theme_data.get("theme_name", "Theme")
    
    # Collect generated file paths
    card_types = ["I_Spy_Cards", "Find_Count_Cards", "How_Many_Cards", "Errorless_Count_Cards"]
    
    for card_type in card_types:
        color_files.append(os.path.join(output_folder, f"{theme_name}_{card_type}_color.pdf"))
        bw_files.append(os.path.join(output_folder, f"{theme_name}_{card_type}_bw.pdf"))
    
    return {'color': color_files, 'bw': bw_files}
