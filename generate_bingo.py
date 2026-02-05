#!/usr/bin/env python3
"""
Brown Bear Bingo Generator
Creates Bingo games with 4 difficulty levels using updated Small Wins Studio branding.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from PIL import Image
import random
from PyPDF2 import PdfReader, PdfWriter

# Brand colors
TURQUOISE = HexColor('#5DBECD')
ORANGE = HexColor('#F4A259')
BLUE = HexColor('#4A90E2')
GREEN = HexColor('#7BC47F')
PURPLE = HexColor('#B88DD9')
LIGHT_GRAY = HexColor('#F5F5F5')
DARK_GRAY = HexColor('#333333')

# Icons available (11 Brown Bear theme icons)
BROWN_BEAR_ICONS = [
    'brown_bear.png',
    'red_bird.png',
    'yellow_duck.png',
    'blue_horse.png',
    'green_frog.png',
    'purple_cat.png',
    'white_dog.png',
    'black_sheep.png',
    'goldfish.png',
    'children.png',
    'teacher.png'
]

# Level configurations
LEVELS = {
    1: {
        'name': 'Level 1',
        'grid': (3, 3),
        'icons_count': 9,
        'color': ORANGE,
        'color_name': 'Orange',
        'description': '3x3 Grid - Beginner'
    },
    2: {
        'name': 'Level 2',
        'grid': (4, 4),
        'icons_count': 10,
        'color': BLUE,
        'color_name': 'Blue',
        'description': '4x4 Grid - Easy'
    },
    3: {
        'name': 'Level 3',
        'grid': (5, 5),
        'icons_count': 11,
        'color': GREEN,
        'color_name': 'Green',
        'description': '5x5 Grid - Medium'
    },
    4: {
        'name': 'Level 4',
        'grid': (5, 5),
        'icons_count': 11,
        'color': PURPLE,
        'color_name': 'Purple',
        'description': '5x5 with FREE Space - Advanced',
        'free_space': True
    }
}


def create_bingo_board(c, rows, cols, icons, level_color, has_free=False, title="Brown Bear Bingo"):
    """Create a single bingo board on the canvas"""
    # Page setup
    width, height = letter
    
    # Border
    border_margin = 0.25 * inch
    c.setStrokeColor(HexColor('#CCCCCC'))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, 
                width - 2*border_margin, height - 2*border_margin, 10)
    
    # Turquoise accent stripe
    stripe_height = 0.35 * inch
    c.setFillColor(TURQUOISE)
    c.rect(border_margin, height - border_margin - stripe_height,
           width - 2*border_margin, stripe_height, fill=1, stroke=0)
    
    # Star logo and centered title on stripe
    star_logo_path = "assets/branding/small_wins_logo.png/star.png"
    if os.path.exists(star_logo_path):
        try:
            logo_height = 24
            logo_y = height - border_margin - stripe_height/2 - logo_height/2
            # Center the logo and title together
            c.drawImage(star_logo_path, width/2 - 150, logo_y, 
                       width=24, height=logo_height, preserveAspectRatio=True, mask='auto')
        except:
            pass
    
    # Title centered
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFont("Helvetica-Bold", 18)
    title_text = title
    title_width = c.stringWidth(title_text, "Helvetica-Bold", 18)
    c.drawString(width/2 - title_width/2 + 12, height - border_margin - stripe_height/2 - 6, title_text)
    
    # Calculate bingo grid area
    grid_top = height - border_margin - stripe_height - 0.3 * inch
    grid_bottom = border_margin + 0.5 * inch  # Space for footer
    grid_left = border_margin + 0.5 * inch
    grid_right = width - border_margin - 0.5 * inch
    
    grid_width = grid_right - grid_left
    grid_height = grid_top - grid_bottom
    
    # Make it square
    grid_size = min(grid_width, grid_height)
    grid_left = (width - grid_size) / 2
    grid_right = grid_left + grid_size
    
    cell_size = grid_size / cols
    
    # Draw bingo grid
    c.setStrokeColor(DARK_GRAY)
    c.setLineWidth(2)
    
    # Draw cells and place icons
    icon_index = 0
    for row in range(rows):
        for col in range(cols):
            x = grid_left + col * cell_size
            y = grid_top - (row + 1) * cell_size
            
            # Draw cell
            c.rect(x, y, cell_size, cell_size)
            
            # Check if this is the free space
            is_free_space = has_free and row == rows//2 and col == cols//2
            
            if is_free_space:
                # Draw FREE space
                c.setFillColor(level_color)
                c.rect(x, y, cell_size, cell_size, fill=1, stroke=1)
                c.setFillColor(HexColor('#FFFFFF'))
                c.setFont("Helvetica-Bold", 20)
                free_text = "FREE"
                text_width = c.stringWidth(free_text, "Helvetica-Bold", 20)
                c.drawString(x + cell_size/2 - text_width/2, y + cell_size/2 - 7, free_text)
            else:
                # Place icon
                if icon_index < len(icons):
                    icon_path = f"assets/themes/brown_bear/icons/{icons[icon_index]}"
                    if os.path.exists(icon_path):
                        try:
                            # Icon size with padding
                            icon_size = cell_size * 0.75
                            icon_x = x + (cell_size - icon_size) / 2
                            icon_y = y + (cell_size - icon_size) / 2
                            c.drawImage(icon_path, icon_x, icon_y, 
                                       width=icon_size, height=icon_size,
                                       preserveAspectRatio=True, mask='auto')
                        except Exception as e:
                            print(f"  Warning: Could not load {icon_path}: {e}")
                    icon_index += 1
    
    # Footer
    c.setFillColor(LIGHT_GRAY)
    c.rect(border_margin, border_margin, width - 2*border_margin, 0.4*inch, fill=1, stroke=0)
    
    # Footer text
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica", 9)
    footer_text = f"BB | Brown Bear Bingo | {title}"
    c.drawString(border_margin + 10, border_margin + 0.25*inch, footer_text)
    
    # Copyright with star logo
    c.setFont("Helvetica", 8)
    copyright_text = "© 2025     Small Wins Studio"
    c.drawString(border_margin + 10, border_margin + 0.1*inch, copyright_text)
    
    # Draw small star logo in footer
    if os.path.exists(star_logo_path):
        try:
            c.drawImage(star_logo_path, border_margin + 42, border_margin + 0.08*inch,
                       width=12, height=12, preserveAspectRatio=True, mask='auto')
        except:
            pass


def generate_random_boards(icons_pool, grid_size, count=6, has_free=False):
    """Generate multiple random bingo boards"""
    boards = []
    rows, cols = grid_size
    cells_needed = rows * cols
    if has_free:
        cells_needed -= 1  # One less for FREE space
    
    for _ in range(count):
        # Randomly select and shuffle icons
        board_icons = random.sample(icons_pool * 3, cells_needed)  # Multiply to allow repeats
        random.shuffle(board_icons)
        boards.append(board_icons)
    
    return boards


def create_calling_cards(c, icons, level_name, level_color):
    """Create calling cards page"""
    width, height = letter
    
    # Border and header (same as bingo boards)
    border_margin = 0.25 * inch
    c.setStrokeColor(HexColor('#CCCCCC'))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin,
                width - 2*border_margin, height - 2*border_margin, 10)
    
    # Turquoise stripe
    stripe_height = 0.35 * inch
    c.setFillColor(TURQUOISE)
    c.rect(border_margin, height - border_margin - stripe_height,
           width - 2*border_margin, stripe_height, fill=1, stroke=0)
    
    # Title
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFont("Helvetica-Bold", 18)
    title = f"Calling Cards - {level_name}"
    title_width = c.stringWidth(title, "Helvetica-Bold", 18)
    c.drawString(width/2 - title_width/2, height - border_margin - stripe_height/2 - 6, title)
    
    # Create grid of calling cards
    cards_per_row = 4
    card_size = 1.5 * inch
    spacing = 0.3 * inch
    
    start_x = border_margin + 0.5 * inch
    start_y = height - border_margin - stripe_height - 0.5 * inch
    
    for i, icon in enumerate(icons):
        row = i // cards_per_row
        col = i % cards_per_row
        
        x = start_x + col * (card_size + spacing)
        y = start_y - row * (card_size + spacing)
        
        # Draw card border
        c.setStrokeColor(DARK_GRAY)
        c.setLineWidth(2)
        c.rect(x, y - card_size, card_size, card_size)
        
        # Draw icon
        icon_path = f"assets/themes/brown_bear/icons/{icon}"
        if os.path.exists(icon_path):
            try:
                icon_size = card_size * 0.8
                icon_x = x + (card_size - icon_size) / 2
                icon_y = y - card_size + (card_size - icon_size) / 2
                c.drawImage(icon_path, icon_x, icon_y,
                           width=icon_size, height=icon_size,
                           preserveAspectRatio=True, mask='auto')
            except:
                pass
    
    # Footer
    c.setFillColor(LIGHT_GRAY)
    c.rect(border_margin, border_margin, width - 2*border_margin, 0.4*inch, fill=1, stroke=0)
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica", 9)
    c.drawString(border_margin + 10, border_margin + 0.25*inch, f"BB | Brown Bear Bingo | {level_name}")
    c.setFont("Helvetica", 8)
    c.drawString(border_margin + 10, border_margin + 0.1*inch, "© 2025 Small Wins Studio")


def generate_level(level_num, output_dir, grayscale=False):
    """Generate a complete Bingo product for one level"""
    level = LEVELS[level_num]
    rows, cols = level['grid']
    has_free = level.get('free_space', False)
    
    version = "bw" if grayscale else "color"
    filename = f"brown_bear_bingo_level{level_num}_{version}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    
    # Get icons for this level
    icons_pool = BROWN_BEAR_ICONS[:level['icons_count']]
    
    # Generate 6 board variations
    boards = generate_random_boards(icons_pool, level['grid'], count=6, has_free=has_free)
    
    print(f"  Creating {level['name']} - {level['description']}...")
    
    # Create each board
    for i, board_icons in enumerate(boards, 1):
        print(f"    Board {i}/6...")
        title = f"Brown Bear Bingo - {level['name']}"
        create_bingo_board(c, rows, cols, board_icons, level['color'], has_free, title)
        c.showPage()
    
    # Create calling cards (need 2 pages for 11 icons)
    print(f"    Creating calling cards...")
    create_calling_cards(c, icons_pool[:8], level['name'], level['color'])
    c.showPage()
    if len(icons_pool) > 8:
        create_calling_cards(c, icons_pool[8:], level['name'], level['color'])
        c.showPage()
    
    c.save()
    print(f"  ✓ Created: {filepath}")
    return filepath


def main():
    print("=" * 60)
    print("BROWN BEAR BINGO GENERATOR")
    print("Small Wins Studio")
    print("=" * 60)
    
    # Create output directory
    output_dir = "samples/brown_bear/bingo"
    os.makedirs(output_dir, exist_ok=True)
    print(f"✓ Output directory ready: {output_dir}")
    print()
    
    # Generate all levels
    for level_num in [1, 2, 3, 4]:
        print(f"Generating Level {level_num}...")
        
        # Color version
        print(f"  Color version...")
        generate_level(level_num, output_dir, grayscale=False)
        
        # BW version
        print(f"  Black & White version...")
        generate_level(level_num, output_dir, grayscale=True)
        
        print()
    
    print("=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print()
    print("Generated products:")
    for level_num in [1, 2, 3, 4]:
        print(f"  • Level {level_num}: brown_bear_bingo_level{level_num}_color.pdf")
        print(f"  • Level {level_num}: brown_bear_bingo_level{level_num}_bw.pdf")
    print()
    print("All Bingo products ready!")


if __name__ == "__main__":
    main()
