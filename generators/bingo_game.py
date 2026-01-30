"""
Bingo Game Generator for SPED Resources

Generates bingo boards and calling cards for vocabulary and receptive language practice.
Calling cards follow task-box sizing standard (4 cards per page, 2×2 grid).

Features:
- Multiple board sizes: 3×3, 4×4, 5×5
- Errorless bingo (all icons identical)
- Real Image and Boardmaker versions
- Task-box compatible calling cards (5.25" × 4")
- FREE space in center (except errorless)
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

# Task box card sizing standard (4 cards per page, 2×2 grid)
TASK_BOX_CARD_WIDTH = int(5.25 * DPI)  # 1575px
TASK_BOX_CARD_HEIGHT = int(4 * DPI)  # 1200px


def generate_bingo_board(items, grid_size=(4, 4), board_type='standard', 
                         folder_type='images', board_num=1):
    """
    Generate a single bingo board.
    
    Args:
        items: List of item dicts with 'image' and 'label' keys
        grid_size: Tuple (rows, cols) for board size
        board_type: 'standard', 'errorless', 'real_images', 'boardmaker'
        folder_type: Image folder type
        board_num: Board number for randomization seed
    
    Returns:
        PIL Image object
    """
    rows, cols = grid_size
    total_cells = rows * cols
    
    # Create page
    page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
    draw = ImageDraw.Draw(page)
    
    # Title
    title = f"BINGO ({rows}×{cols})"
    if board_type == 'errorless':
        title += " - Errorless"
    elif board_type == 'real_images':
        title += " - Real Images"
    elif board_type == 'boardmaker':
        title += " - Boardmaker"
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        title_font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_x = (PAGE_WIDTH - title_width) // 2
    draw.text((title_x, 60), title, fill=COLORS['black'], font=title_font)
    
    # Calculate board dimensions
    board_margin = 100
    footer_space = 150
    available_width = PAGE_WIDTH - 2 * board_margin
    available_height = PAGE_HEIGHT - 200 - footer_space  # Space for title and footer
    
    # Make board square (use smaller dimension)
    board_size = min(available_width, available_height)
    cell_size = board_size // max(rows, cols)
    
    # Center the board
    board_width = cell_size * cols
    board_height = cell_size * rows
    board_x = (PAGE_WIDTH - board_width) // 2
    board_y = 200  # Below title
    
    # Select items for this board
    if board_type == 'errorless':
        # All cells have the same icon
        if items:
            selected_items = [items[0]] * total_cells
        else:
            selected_items = []
    else:
        # Shuffle items for variety
        random.seed(board_num)  # Consistent randomization
        shuffled = items.copy()
        random.shuffle(shuffled)
        
        # Repeat items if necessary
        selected_items = []
        while len(selected_items) < total_cells:
            selected_items.extend(shuffled)
        selected_items = selected_items[:total_cells]
    
    # Determine FREE space position (center for odd grids)
    free_space = None
    if rows % 2 == 1 and cols % 2 == 1 and board_type != 'errorless':
        free_space = (rows // 2, cols // 2)
    
    # Draw grid and populate cells
    item_idx = 0
    for row in range(rows):
        for col in range(cols):
            x1 = board_x + col * cell_size
            y1 = board_y + row * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            
            # Draw cell border
            draw.rectangle([x1, y1, x2, y2], outline=COLORS['black'], width=3)
            
            # Check if FREE space
            if free_space and (row, col) == free_space:
                # Draw FREE space
                try:
                    free_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                except:
                    free_font = ImageFont.load_default()
                
                free_text = "FREE"
                bbox = draw.textbbox((0, 0), free_text, font=free_font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
                text_x = x1 + (cell_size - text_w) // 2
                text_y = y1 + (cell_size - text_h) // 2
                draw.text((text_x, text_y), free_text, fill=COLORS['black'], font=free_font)
            else:
                # Draw icon
                if item_idx < len(selected_items):
                    item = selected_items[item_idx]
                    icon_rect = (x1 + 10, y1 + 10, x2 - 10, y2 - 10)
                    
                    try:
                        img = load_image(item['image'], folder_type=folder_type)
                        if img:
                            scaled_coords = scale_image_to_fit(img, icon_rect, padding=5)
                            if scaled_coords:
                                paste_x, paste_y, paste_width, paste_height = scaled_coords
                                resized_img = img.resize((paste_width, paste_height), Image.Resampling.LANCZOS)
                                # Convert RGBA to RGB if needed
                                if resized_img.mode == 'RGBA':
                                    bg = Image.new('RGB', resized_img.size, COLORS['white'])
                                    bg.paste(resized_img, mask=resized_img.split()[3])
                                    resized_img = bg
                                page.paste(resized_img, (paste_x, paste_y))
                    except:
                        # Use placeholder
                        placeholder = create_placeholder_image(icon_rect[2] - icon_rect[0], 
                                                              icon_rect[3] - icon_rect[1], 
                                                              "No Image")
                        page.paste(placeholder, (icon_rect[0], icon_rect[1]))
                    
                    item_idx += 1
    
    # Add footer and page number
    draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
    draw_page_number(draw, 1, 1, PAGE_WIDTH, PAGE_HEIGHT)
    
    return page


def generate_calling_card(draw, card_rect, item, card_type='icon_only', folder_type='images'):
    """
    Generate a single calling card within the given rectangle (task-box sized).
    
    Args:
        draw: PIL ImageDraw object
        card_rect: Tuple (x1, y1, x2, y2) defining card boundaries
        item: Dict with 'image' and 'label' keys
        card_type: 'icon_only', 'icon_word', or 'real_image'
        folder_type: Image folder type
    """
    x1, y1, x2, y2 = card_rect
    card_width = x2 - x1
    card_height = y2 - y1
    
    # Draw card border
    draw.rectangle([x1, y1, x2, y2], outline=COLORS['black'], width=3)
    
    if card_type == 'icon_word':
        # Split card: top 70% icon, bottom 30% word
        icon_height = int(card_height * 0.70)
        icon_rect = (x1 + 20, y1 + 20, x2 - 20, y1 + icon_height - 10)
        
        # Draw icon
        try:
            img = load_image(item['image'], folder_type=folder_type)
            if img:
                scaled_coords = scale_image_to_fit(img, icon_rect, padding=10)
                if scaled_coords:
                    paste_x, paste_y, paste_width, paste_height = scaled_coords
                    resized_img = img.resize((paste_width, paste_height), Image.Resampling.LANCZOS)
                    # Convert RGBA to RGB if needed
                    if resized_img.mode == 'RGBA':
                        bg = Image.new('RGB', resized_img.size, COLORS['white'])
                        bg.paste(resized_img, mask=resized_img.split()[3])
                        resized_img = bg
                    # Paste onto the page
                    temp_page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
                    temp_page.paste(resized_img, (paste_x, paste_y))
                    draw._image.paste(temp_page.crop((paste_x, paste_y, paste_x + paste_width, paste_y + paste_height)), (paste_x, paste_y))
        except:
            placeholder = create_placeholder_image(icon_rect[2] - icon_rect[0], 
                                                  icon_rect[3] - icon_rect[1], 
                                                  "No Image")
            draw._image.paste(placeholder, (icon_rect[0], icon_rect[1]))
        
        # Draw word
        word_y_start = y1 + icon_height
        try:
            word_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except:
            word_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), item['label'], font=word_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = x1 + (card_width - text_w) // 2
        text_y = word_y_start + ((card_height - icon_height) - text_h) // 2
        draw.text((text_x, text_y), item['label'], fill=COLORS['black'], font=word_font)
    else:
        # Icon only (full card)
        icon_rect = (x1 + 20, y1 + 20, x2 - 20, y2 - 20)
        
        try:
            img = load_image(item['image'], folder_type=folder_type)
            if img:
                scaled_coords = scale_image_to_fit(img, icon_rect, padding=10)
                if scaled_coords:
                    paste_x, paste_y, paste_width, paste_height = scaled_coords
                    resized_img = img.resize((paste_width, paste_height), Image.Resampling.LANCZOS)
                    # Convert RGBA to RGB if needed
                    if resized_img.mode == 'RGBA':
                        bg = Image.new('RGB', resized_img.size, COLORS['white'])
                        bg.paste(resized_img, mask=resized_img.split()[3])
                        resized_img = bg
                    temp_page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
                    temp_page.paste(resized_img, (paste_x, paste_y))
                    draw._image.paste(temp_page.crop((paste_x, paste_y, paste_x + paste_width, paste_y + paste_height)), (paste_x, paste_y))
        except:
            placeholder = create_placeholder_image(icon_rect[2] - icon_rect[0], 
                                                  icon_rect[3] - icon_rect[1], 
                                                  "No Image")
            draw._image.paste(placeholder, (icon_rect[0], icon_rect[1]))


def generate_calling_cards_page(items, start_idx, card_type='icon_only', folder_type='images',
                                page_num=1, total_pages=1):
    """
    Generate a page with 4 calling cards in 2×2 grid (task-box standard).
    
    Args:
        items: List of item dicts
        start_idx: Starting index in items list
        card_type: Type of calling cards
        folder_type: Image folder type
        page_num: Current page number
        total_pages: Total number of pages
    
    Returns:
        PIL Image object
    """
    # Create page
    page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
    draw = ImageDraw.Draw(page)
    
    # Calculate card positions for 2×2 grid
    margin = MARGINS['page']
    available_width = PAGE_WIDTH - 2 * margin
    available_height = PAGE_HEIGHT - 2 * margin - MARGINS['page']
    
    card_width = available_width // 2
    card_height = available_height // 2
    
    # Generate 4 calling cards
    for row in range(2):
        for col in range(2):
            idx = start_idx + row * 2 + col
            if idx >= len(items):
                break
            
            x1 = margin + col * card_width
            y1 = margin + row * card_height
            x2 = x1 + card_width
            y2 = y1 + card_height
            
            card_rect = (x1, y1, x2, y2)
            generate_calling_card(draw, card_rect, items[idx], card_type, folder_type)
    
    # Add footer and page number
    draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
    draw_page_number(draw, page_num, total_pages, PAGE_WIDTH, PAGE_HEIGHT)
    
    return page


def generate_bingo_game_set(items, theme_name, output_dir='output',
                            include_3x3=True, include_4x4=True, include_5x5=True,
                            include_errorless=True, include_real_images=False,
                            include_boardmaker=False, num_boards=6,
                            include_calling_cards=True, include_storage_label=True,
                            folder_type='images'):
    """
    Generate complete set of bingo boards and calling cards.
    
    Args:
        items: List of dicts with 'image' and 'label' keys
        theme_name: Name of theme for file naming
        output_dir: Output directory path
        include_3x3: Generate 3×3 boards
        include_4x4: Generate 4×4 boards
        include_5x5: Generate 5×5 boards
        include_errorless: Generate errorless boards
        include_real_images: Generate real image boards
        include_boardmaker: Generate Boardmaker boards
        num_boards: Number of unique boards per type
        include_calling_cards: Generate calling cards
        include_storage_label: Generate storage labels
        folder_type: Default folder type for images
    
    Returns:
        Dict with paths to generated files
    """
    os.makedirs(output_dir, exist_ok=True)
    output_files = {}
    
    # Generate different board sizes
    board_configs = []
    if include_3x3:
        board_configs.append(((3, 3), '3x3'))
    if include_4x4:
        board_configs.append(((4, 4), '4x4'))
    if include_5x5:
        board_configs.append(((5, 5), '5x5'))
    
    for grid_size, size_name in board_configs:
        # Standard boards
        boards = []
        for i in range(num_boards):
            board = generate_bingo_board(items, grid_size, 'standard', folder_type, i + 1)
            boards.append(board)
        
        output_path = os.path.join(output_dir, f"{theme_name}_Bingo_{size_name}.pdf")
        save_images_as_pdf(boards, output_path)
        output_files[f'bingo_{size_name}'] = output_path
        
        if include_storage_label:
            label_path = create_companion_label(output_path, theme_name, f"Bingo {size_name}")
            output_files[f'bingo_{size_name}_label'] = label_path
        
        # Errorless boards
        if include_errorless:
            boards = []
            for i in range(num_boards):
                board = generate_bingo_board(items, grid_size, 'errorless', folder_type, i + 1)
                boards.append(board)
            
            output_path = os.path.join(output_dir, f"{theme_name}_Bingo_{size_name}_Errorless.pdf")
            save_images_as_pdf(boards, output_path)
            output_files[f'bingo_{size_name}_errorless'] = output_path
            
            if include_storage_label:
                label_path = create_companion_label(output_path, theme_name, f"Bingo {size_name} (Errorless)")
                output_files[f'bingo_{size_name}_errorless_label'] = label_path
        
        # Real image boards
        if include_real_images:
            boards = []
            for i in range(num_boards):
                board = generate_bingo_board(items, grid_size, 'real_images', 'real_images', i + 1)
                boards.append(board)
            
            output_path = os.path.join(output_dir, f"{theme_name}_Bingo_{size_name}_Real_Images.pdf")
            save_images_as_pdf(boards, output_path)
            output_files[f'bingo_{size_name}_real'] = output_path
            
            if include_storage_label:
                label_path = create_companion_label(output_path, theme_name, f"Bingo {size_name} (Real Images)")
                output_files[f'bingo_{size_name}_real_label'] = label_path
        
        # Boardmaker boards
        if include_boardmaker:
            boards = []
            for i in range(num_boards):
                board = generate_bingo_board(items, grid_size, 'boardmaker', 'boardmaker', i + 1)
                boards.append(board)
            
            output_path = os.path.join(output_dir, f"{theme_name}_Bingo_{size_name}_Boardmaker.pdf")
            save_images_as_pdf(boards, output_path)
            output_files[f'bingo_{size_name}_boardmaker'] = output_path
            
            if include_storage_label:
                label_path = create_companion_label(output_path, theme_name, f"Bingo {size_name} (Boardmaker)")
                output_files[f'bingo_{size_name}_boardmaker_label'] = label_path
    
    # Generate calling cards (task-box sized)
    if include_calling_cards:
        cards_per_page = 4
        num_pages = (len(items) + cards_per_page - 1) // cards_per_page
        
        # Icon only calling cards
        pages = []
        for page_num in range(num_pages):
            start_idx = page_num * cards_per_page
            page = generate_calling_cards_page(items, start_idx, 'icon_only', folder_type,
                                             page_num + 1, num_pages)
            pages.append(page)
        
        output_path = os.path.join(output_dir, f"{theme_name}_Bingo_Calling_Cards_Icons.pdf")
        save_images_as_pdf(pages, output_path)
        output_files['calling_cards_icons'] = output_path
        
        if include_storage_label:
            label_path = create_companion_label(output_path, theme_name, "Bingo Calling Cards (Icons)")
            output_files['calling_cards_icons_label'] = label_path
        
        # Icon + word calling cards
        pages = []
        for page_num in range(num_pages):
            start_idx = page_num * cards_per_page
            page = generate_calling_cards_page(items, start_idx, 'icon_word', folder_type,
                                             page_num + 1, num_pages)
            pages.append(page)
        
        output_path = os.path.join(output_dir, f"{theme_name}_Bingo_Calling_Cards_Words.pdf")
        save_images_as_pdf(pages, output_path)
        output_files['calling_cards_words'] = output_path
        
        if include_storage_label:
            label_path = create_companion_label(output_path, theme_name, "Bingo Calling Cards (Icons + Words)")
            output_files['calling_cards_words_label'] = label_path
        
        # Real image calling cards
        if include_real_images:
            pages = []
            for page_num in range(num_pages):
                start_idx = page_num * cards_per_page
                page = generate_calling_cards_page(items, start_idx, 'icon_only', 'real_images',
                                                 page_num + 1, num_pages)
                pages.append(page)
            
            output_path = os.path.join(output_dir, f"{theme_name}_Bingo_Calling_Cards_Real_Images.pdf")
            save_images_as_pdf(pages, output_path)
            output_files['calling_cards_real'] = output_path
            
            if include_storage_label:
                label_path = create_companion_label(output_path, theme_name, "Bingo Calling Cards (Real Images)")
                output_files['calling_cards_real_label'] = label_path
    
    return output_files
