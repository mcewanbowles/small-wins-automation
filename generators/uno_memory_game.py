"""
UNO & Memory Game Generator

Generates task-box sized UNO cards and Memory game cards for classroom use.

Features:
- UNO deck with color suits (red, yellow, blue, green) and action cards
- Memory game with paired icons for matching
- Task-box sizing (5.25" × 4", 4 per page in 2×2 grid)
- Theme-aware design with icons
- Storage labels for organization
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from utils.theme_loader import load_theme
from utils.draw_helpers import (
    draw_task_box_grid,
    draw_footer,
    draw_icon_placeholder,
    draw_storage_label
)
from utils.color_helpers import adjust_for_bw_mode


def generate_uno_cards(theme_name, output_dir, mode="color"):
    """
    Generate UNO deck with color suits and action cards.
    
    Args:
        theme_name: Name of the theme
        output_dir: Output directory for PDFs
        mode: Output mode - 'color' or 'bw' (black-and-white)
    """
    theme = load_theme(theme_name)
    fringe_icons = theme.get("fringe_icons", [])[:4]  # Use first 4 icons for suits
    
    # UNO card suits and numbers
    colors_suits = [
        ("Red", colors.HexColor("#E63946")),
        ("Yellow", colors.HexColor("#F4D03F")),
        ("Blue", colors.HexColor("#457B9D")),
        ("Green", colors.HexColor("#2A9D8F"))
    ]
    
    numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    action_cards = ["Skip", "Reverse", "Draw 2"]
    wild_cards = ["Wild", "Wild Draw 4"]
    
    # Task-box dimensions
    page_width, page_height = letter
    card_width = 5.25 * inch
    card_height = 4 * inch
    
    mode_suffix = f"_{mode}" if mode else ""
    filename = f"{theme_name}_uno_deck{mode_suffix}.pdf"
    filepath = os.path.join(output_dir, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    
    page_num = 1
    cards_on_page = []
    
    # Generate number cards for each color (2 of each except 0)
    for color_name, color_hex in colors_suits:
        for number in numbers:
            count = 1 if number == "0" else 2
            for _ in range(count):
                card_data = {
                    "type": "number",
                    "color": color_name,
                    "color_hex": color_hex,
                    "value": number
                }
                cards_on_page.append(card_data)
                
                if len(cards_on_page) == 4:
                    draw_uno_page(c, cards_on_page, page_num, theme, mode)
                    cards_on_page = []
                    c.showPage()
                    page_num += 1
    
    # Generate action cards for each color (2 of each)
    for color_name, color_hex in colors_suits:
        for action in action_cards:
            for _ in range(2):
                card_data = {
                    "type": "action",
                    "color": color_name,
                    "color_hex": color_hex,
                    "value": action
                }
                cards_on_page.append(card_data)
                
                if len(cards_on_page) == 4:
                    draw_uno_page(c, cards_on_page, page_num, theme, mode)
                    cards_on_page = []
                    c.showPage()
                    page_num += 1
    
    # Generate wild cards (4 of each)
    for wild_type in wild_cards:
        for _ in range(4):
            card_data = {
                "type": "wild",
                "color": "Wild",
                "color_hex": colors.black,
                "value": wild_type
            }
            cards_on_page.append(card_data)
            
            if len(cards_on_page) == 4:
                draw_uno_page(c, cards_on_page, page_num, theme, mode)
                cards_on_page = []
                c.showPage()
                page_num += 1
    
    # Draw remaining cards if any
    if cards_on_page:
        # Fill with blank cards if needed
        while len(cards_on_page) < 4:
            cards_on_page.append(None)
        draw_uno_page(c, cards_on_page, page_num, theme, mode)
    
    c.save()
    print(f"✓ Generated UNO deck: {filename}")
    return filepath


def draw_uno_page(c, cards, page_num, theme, mode="color"):
    """Draw a page of 4 UNO cards in task-box grid."""
    page_width, page_height = letter
    card_width = 5.25 * inch
    card_height = 4 * inch
    
    # Draw task-box grid
    draw_task_box_grid(c)
    
    # Card positions (top-left, top-right, bottom-left, bottom-right)
    positions = [
        (0, page_height - card_height),  # Top-left
        (card_width, page_height - card_height),  # Top-right
        (0, page_height - 2 * card_height),  # Bottom-left
        (card_width, page_height - 2 * card_height)  # Bottom-right
    ]
    
    for i, (card_data, (x, y)) in enumerate(zip(cards, positions)):
        if card_data is not None:
            draw_uno_card(c, card_data, x, y, card_width, card_height, mode)
    
    # Draw footer
    draw_footer(c, page_num, "UNO Deck")


def draw_uno_card(c, card_data, x, y, width, height, mode="color"):
    """Draw a single UNO card."""
    # Card background based on color - convert to grayscale in BW mode
    if card_data["type"] == "wild":
        # Rainbow gradient effect for wild cards
        c.setFillColor(colors.white)
    else:
        # Adjust color for mode
        original_color = card_data["color_hex"]
        if mode == "bw":
            # Convert to grayscale
            import colorsys
            # Extract RGB values
            if hasattr(original_color, 'rgb'):
                r, g, b = original_color.rgb()
            else:
                r, g, b = 0.5, 0.5, 0.5  # Default gray
            # Convert to grayscale using luminosity method
            gray_value = 0.299 * r + 0.587 * g + 0.114 * b
            c.setFillColor(colors.Color(gray_value, gray_value, gray_value))
        else:
            c.setFillColor(original_color)
    
    # Draw colored border
    border_width = 0.3 * inch
    c.rect(x + border_width, y + border_width, 
           width - 2 * border_width, height - 2 * border_width, 
           fill=1, stroke=0)
    
    # White center area
    c.setFillColor(colors.white)
    inner_margin = 0.5 * inch
    c.roundRect(x + inner_margin, y + inner_margin,
                width - 2 * inner_margin, height - 2 * inner_margin,
                0.2 * inch, fill=1, stroke=0)
    
    # Draw card value in center
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 48)
    
    value = card_data["value"]
    text_width = c.stringWidth(value, "Helvetica-Bold", 48)
    c.drawString(x + (width - text_width) / 2, 
                 y + height / 2 - 0.25 * inch, 
                 value)
    
    # Draw corner values (top-left and bottom-right)
    c.setFont("Helvetica-Bold", 24)
    corner_text = value if card_data["type"] != "wild" else "★"
    
    # Top-left corner
    c.drawString(x + 0.4 * inch, y + height - 0.6 * inch, corner_text)
    
    # Bottom-right corner (rotated)
    c.saveState()
    c.translate(x + width - 0.4 * inch, y + 0.4 * inch)
    c.rotate(180)
    c.drawString(0, 0, corner_text)
    c.restoreState()
    
    # Color indicator bar for wild cards
    if card_data["type"] == "wild":
        bar_height = 0.4 * inch
        bar_y = y + height - border_width - bar_height
        colors_list = [
            colors.HexColor("#E63946"),
            colors.HexColor("#F4D03F"),
            colors.HexColor("#457B9D"),
            colors.HexColor("#2A9D8F")
        ]
        bar_width = (width - 2 * border_width) / 4
        for i, col in enumerate(colors_list):
            c.setFillColor(col)
            c.rect(x + border_width + i * bar_width, bar_y, 
                   bar_width, bar_height, fill=1, stroke=0)


def generate_memory_game(theme_name, output_dir, mode="color"):
    """
    Generate Memory game cards with paired icons.
    
    Args:
        theme_name: Name of the theme
        output_dir: Output directory for PDFs
        mode: Output mode - 'color' or 'bw' (black-and-white)
    """
    theme = load_theme(theme_name)
    fringe_icons = theme.get("fringe_icons", [])
    
    # Use up to 12 icons for memory game (24 cards total)
    num_pairs = min(12, len(fringe_icons))
    icons_to_use = fringe_icons[:num_pairs]
    
    # Task-box dimensions
    page_width, page_height = letter
    card_width = 5.25 * inch
    card_height = 4 * inch
    
    mode_suffix = f"_{mode}" if mode else ""
    filename = f"{theme_name}_memory_game{mode_suffix}.pdf"
    filepath = os.path.join(output_dir, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    
    page_num = 1
    cards_on_page = []
    
    # Generate pairs of cards
    for icon_name in icons_to_use:
        # Each icon appears twice (a pair)
        for _ in range(2):
            cards_on_page.append(icon_name)
            
            if len(cards_on_page) == 4:
                draw_memory_page(c, cards_on_page, page_num, theme, mode)
                cards_on_page = []
                c.showPage()
                page_num += 1
    
    # Draw remaining cards if any
    if cards_on_page:
        # Fill with blank cards if needed
        while len(cards_on_page) < 4:
            cards_on_page.append(None)
        draw_memory_page(c, cards_on_page, page_num, theme, mode)
    
    c.save()
    print(f"✓ Generated Memory game: {filename}")
    
    # Generate card backs
    backs_file = f"{theme_name}_memory_backs{mode_suffix}.pdf"
    generate_memory_backs(theme_name, os.path.join(output_dir, backs_file), num_pairs * 2, mode)
    
    return [filepath, os.path.join(output_dir, backs_file)]


def draw_memory_page(c, cards, page_num, theme, mode="color"):
    """Draw a page of 4 memory game cards in task-box grid."""
    page_width, page_height = letter
    card_width = 5.25 * inch
    card_height = 4 * inch
    
    # Draw task-box grid
    draw_task_box_grid(c)
    
    # Card positions
    positions = [
        (0, page_height - card_height),  # Top-left
        (card_width, page_height - card_height),  # Top-right
        (0, page_height - 2 * card_height),  # Bottom-left
        (card_width, page_height - 2 * card_height)  # Bottom-right
    ]
    
    for i, (icon_name, (x, y)) in enumerate(zip(cards, positions)):
        if icon_name is not None:
            draw_memory_card(c, icon_name, x, y, card_width, card_height, theme, mode)
    
    # Draw footer
    draw_footer(c, page_num, "Memory Game - Fronts")


def draw_memory_card(c, icon_name, x, y, width, height, theme, mode="color"):
    """Draw a single memory game card front."""
    # Card background
    c.setFillColor(colors.white)
    c.rect(x, y, width, height, fill=1, stroke=0)
    
    # Draw border - adjust color for mode
    primary_color = theme.get("primary_color", colors.HexColor("#1D3557"))
    if mode == "bw":
        # Convert to grayscale
        if hasattr(primary_color, 'rgb'):
            r, g, b = primary_color.rgb()
            gray_value = 0.299 * r + 0.587 * g + 0.114 * b
            primary_color = colors.Color(gray_value, gray_value, gray_value)
        else:
            primary_color = colors.black
    c.setStrokeColor(primary_color)
    c.setLineWidth(2)
    c.rect(x + 0.1 * inch, y + 0.1 * inch, 
           width - 0.2 * inch, height - 0.2 * inch, 
           fill=0, stroke=1)
    
    # Icon in center (large)
    icon_size = 2.5 * inch
    icon_x = x + (width - icon_size) / 2
    icon_y = y + (height - icon_size) / 2
    
    draw_icon_placeholder(c, icon_x, icon_y, icon_size, icon_size, icon_name)
    
    # Icon name below
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 14)
    text_width = c.stringWidth(icon_name, "Helvetica", 14)
    c.drawString(x + (width - text_width) / 2, 
                 y + 0.3 * inch, 
                 icon_name)


def generate_memory_backs(theme_name, filepath, num_cards, mode="color"):
    """Generate card backs for memory game."""
    theme = load_theme(theme_name)
    
    page_width, page_height = letter
    card_width = 5.25 * inch
    card_height = 4 * inch
    
    c = canvas.Canvas(filepath, pagesize=letter)
    
    page_num = 1
    cards_count = 0
    
    while cards_count < num_cards:
        # Draw task-box grid
        draw_task_box_grid(c)
        
        # Card positions
        positions = [
            (0, page_height - card_height),
            (card_width, page_height - card_height),
            (0, page_height - 2 * card_height),
            (card_width, page_height - 2 * card_height)
        ]
        
        for x, y in positions:
            if cards_count >= num_cards:
                break
            
            # Draw card back with theme pattern
            primary_color = theme.get("primary_color", colors.HexColor("#1D3557"))
            if mode == "bw":
                # Convert to grayscale
                if hasattr(primary_color, 'rgb'):
                    r, g, b = primary_color.rgb()
                    gray_value = 0.299 * r + 0.587 * g + 0.114 * b
                    primary_color = colors.Color(gray_value, gray_value, gray_value)
                else:
                    primary_color = colors.black
            c.setFillColor(primary_color)
            c.rect(x, y, card_width, card_height, fill=1, stroke=0)
            
            # White border
            c.setFillColor(colors.white)
            c.setLineWidth(0.3 * inch)
            c.rect(x + 0.15 * inch, y + 0.15 * inch,
                   card_width - 0.3 * inch, card_height - 0.3 * inch,
                   fill=0, stroke=1)
            
            # Theme name in center
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 36)
            text = theme_name.upper()
            text_width = c.stringWidth(text, "Helvetica-Bold", 36)
            c.drawString(x + (card_width - text_width) / 2,
                        y + card_height / 2 - 0.2 * inch,
                        text)
            
            cards_count += 1
        
        # Draw footer
        draw_footer(c, page_num, "Memory Game - Backs")
        
        if cards_count < num_cards:
            c.showPage()
            page_num += 1
    
    c.save()
    print(f"✓ Generated Memory game backs: {os.path.basename(filepath)}")


def main(theme_name="brown_bear", output_dir="output"):
    """
    Main function to generate UNO and Memory game cards.
    
    Args:
        theme_name: Name of the theme to use
        output_dir: Directory to save generated PDFs
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"UNO & MEMORY GAME GENERATOR")
    print(f"Theme: {theme_name}")
    print(f"{'='*60}\n")
    
    # Generate UNO deck
    generate_uno_cards(theme_name, output_dir)
    
    # Generate Memory game
    generate_memory_game(theme_name, output_dir)
    
    print(f"\n{'='*60}")
    print(f"✓ All UNO & Memory game cards generated successfully!")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}\n")


def generate_uno_memory_dual_mode(theme_name, output_dir):
    """
    Generate UNO and Memory game cards in both color and black-and-white modes.
    
    Args:
        theme_name: Name of the theme to use
        output_dir: Directory to save generated PDFs
    
    Returns:
        Dictionary with 'color' and 'bw' lists of generated file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating UNO & Memory Game cards - DUAL MODE")
    
    # Generate color version
    print("\n=== COLOR version ===")
    uno_color = generate_uno_cards(theme_name, output_dir, mode="color")
    memory_color = generate_memory_game(theme_name, output_dir, mode="color")
    
    # Generate black-and-white version
    print("\n=== BLACK-AND-WHITE version ===")
    uno_bw = generate_uno_cards(theme_name, output_dir, mode="bw")
    memory_bw = generate_memory_game(theme_name, output_dir, mode="bw")
    
    return {
        'color': [uno_color] + memory_color,
        'bw': [uno_bw] + memory_bw
    }


if __name__ == "__main__":
    main()
