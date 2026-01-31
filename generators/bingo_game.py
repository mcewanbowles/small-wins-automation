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
- Dual-mode output (color + black-and-white)
"""

import os
import random
from PIL import Image, ImageDraw
from utils.config import DPI, PAGE_WIDTH, PAGE_HEIGHT, MARGINS, COLORS
from utils.layout import create_page_canvas, add_footer
from utils.grid_layout import create_grid_positions
from utils.image_utils import scale_image_proportional, center_image_in_box
from utils.color_helpers import image_to_grayscale
from utils.fonts import FontManager
from utils.image_loader import load_image
from utils.pdf_export import save_images_as_pdf
from utils.storage_label_helper import create_companion_label

# Task box card sizing standard (4 cards per page, 2×2 grid)
TASK_BOX_CARD_WIDTH = int(5.25 * DPI)  # 1575px
TASK_BOX_CARD_HEIGHT = int(4 * DPI)  # 1200px

# Initialize font manager
font_manager = FontManager()


def generate_bingo_board(items, grid_size=(4, 4), board_type='standard', 
                         folder_type='images', board_num=1, mode='color'):
    """
    Generate a single bingo board.
    
    Args:
        items: List of item dicts with 'image' and 'label' keys
        grid_size: Tuple (rows, cols) for board size
        board_type: 'standard', 'errorless', 'real_images', 'boardmaker'
        folder_type: Image folder type
        board_num: Board number for randomization seed
        mode: 'color' or 'bw' for output mode
    
    Returns:
        PIL Image object
    """
    rows, cols = grid_size
    total_cells = rows * cols
    
    # Create page using modern layout utility
    page = create_page_canvas(mode=mode)
    draw = ImageDraw.Draw(page)
    
    # Title
    title = f"BINGO ({rows}×{cols})"
    if board_type == 'errorless':
        title += " - Errorless"
    elif board_type == 'real_images':
        title += " - Real Images"
    elif board_type == 'boardmaker':
        title += " - Boardmaker"
    
    title_font = font_manager.get_font('title', 48)
    
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
                free_font = font_manager.get_font('title', 36)
                
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
                    
                    # Calculate icon area with padding
                    icon_width = cell_size - 20
                    icon_height = cell_size - 20
                    
                    try:
                        img = load_image(item['image'], folder_type=folder_type)
                        if img:
                            # Convert to grayscale if BW mode
                            if mode == 'bw':
                                img = image_to_grayscale(img)
                            
                            # Scale image proportionally
                            scaled_img = scale_image_proportional(img, icon_width, icon_height)
                            
                            # Center image in cell
                            positioned_img = center_image_in_box(scaled_img, cell_size, cell_size)
                            
                            # Convert RGBA to RGB if needed
                            if positioned_img.mode == 'RGBA':
                                bg = Image.new('RGB', positioned_img.size, COLORS['white'])
                                bg.paste(positioned_img, mask=positioned_img.split()[3])
                                positioned_img = bg
                            
                            # Paste image onto page
                            page.paste(positioned_img, (x1 + (cell_size - positioned_img.width) // 2, 
                                                       y1 + (cell_size - positioned_img.height) // 2))
                    except:
                        pass  # Skip if image fails to load
                    
                    item_idx += 1
    
    # Add footer using modern layout utility
    add_footer(page, "Bingo Game", page_num=1, mode=mode)
    
    return page


def generate_calling_card(page, draw, card_rect, item, card_type='icon_only', 
                         folder_type='images', mode='color'):
    """
    Generate a single calling card within the given rectangle (task-box sized).
    
    Args:
        page: PIL Image object (page canvas)
        draw: PIL ImageDraw object
        card_rect: Tuple (x1, y1, x2, y2) defining card boundaries
        item: Dict with 'image' and 'label' keys
        card_type: 'icon_only', 'icon_word', or 'real_image'
        folder_type: Image folder type
        mode: 'color' or 'bw' for output mode
    """
    x1, y1, x2, y2 = card_rect
    card_width = x2 - x1
    card_height = y2 - y1
    
    # Draw card border
    draw.rectangle([x1, y1, x2, y2], outline=COLORS['black'], width=3)
    
    if card_type == 'icon_word':
        # Split card: top 70% icon, bottom 30% word
        icon_height = int(card_height * 0.70)
        icon_area_width = card_width - 40
        icon_area_height = icon_height - 30
        
        # Draw icon
        try:
            img = load_image(item['image'], folder_type=folder_type)
            if img:
                # Convert to grayscale if BW mode
                if mode == 'bw':
                    img = image_to_grayscale(img)
                
                # Scale image proportionally
                scaled_img = scale_image_proportional(img, icon_area_width, icon_area_height)
                
                # Center image in icon area
                icon_x = x1 + (card_width - scaled_img.width) // 2
                icon_y = y1 + 20 + (icon_area_height - scaled_img.height) // 2
                
                # Convert RGBA to RGB if needed
                if scaled_img.mode == 'RGBA':
                    bg = Image.new('RGB', scaled_img.size, COLORS['white'])
                    bg.paste(scaled_img, mask=scaled_img.split()[3])
                    scaled_img = bg
                
                page.paste(scaled_img, (icon_x, icon_y))
        except:
            pass  # Skip if image fails to load
        
        # Draw word
        word_y_start = y1 + icon_height
        word_font = font_manager.get_font('body', 40)
        
        bbox = draw.textbbox((0, 0), item['label'], font=word_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = x1 + (card_width - text_w) // 2
        text_y = word_y_start + ((card_height - icon_height) - text_h) // 2
        draw.text((text_x, text_y), item['label'], fill=COLORS['black'], font=word_font)
    else:
        # Icon only (full card)
        icon_area_width = card_width - 40
        icon_area_height = card_height - 40
        
        try:
            img = load_image(item['image'], folder_type=folder_type)
            if img:
                # Convert to grayscale if BW mode
                if mode == 'bw':
                    img = image_to_grayscale(img)
                
                # Scale image proportionally
                scaled_img = scale_image_proportional(img, icon_area_width, icon_area_height)
                
                # Center image in card
                icon_x = x1 + (card_width - scaled_img.width) // 2
                icon_y = y1 + (card_height - scaled_img.height) // 2
                
                # Convert RGBA to RGB if needed
                if scaled_img.mode == 'RGBA':
                    bg = Image.new('RGB', scaled_img.size, COLORS['white'])
                    bg.paste(scaled_img, mask=scaled_img.split()[3])
                    scaled_img = bg
                
                page.paste(scaled_img, (icon_x, icon_y))
        except:
            pass  # Skip if image fails to load


def generate_calling_cards_page(items, start_idx, card_type='icon_only', folder_type='images',
                                page_num=1, total_pages=1, mode='color'):
    """
    Generate a page with 4 calling cards in 2×2 grid (task-box standard).
    
    Args:
        items: List of item dicts
        start_idx: Starting index in items list
        card_type: Type of calling cards
        folder_type: Image folder type
        page_num: Current page number
        total_pages: Total number of pages
        mode: 'color' or 'bw' for output mode
    
    Returns:
        PIL Image object
    """
    # Create page using modern layout utility
    page = create_page_canvas(mode=mode)
    draw = ImageDraw.Draw(page)
    
    # Use grid layout utility for 2×2 positioning
    card_positions = create_grid_positions(2, 2)
    
    # Generate 4 calling cards
    for idx, (x, y) in enumerate(card_positions):
        item_idx = start_idx + idx
        if item_idx >= len(items):
            break
        
        # Calculate card rectangle from grid position
        card_rect = (x, y, x + TASK_BOX_CARD_WIDTH, y + TASK_BOX_CARD_HEIGHT)
        generate_calling_card(page, draw, card_rect, items[item_idx], card_type, folder_type, mode)
    
    # Add footer using modern layout utility
    add_footer(page, "Bingo Calling Cards", page_num=page_num, mode=mode)
    
    return page


def generate_bingo_game_set(items, theme_name, output_dir='output',
                            include_3x3=True, include_4x4=True, include_5x5=True,
                            include_errorless=True, include_real_images=False,
                            include_boardmaker=False, num_boards=6,
                            include_calling_cards=True, include_storage_label=True,
                            folder_type='images', mode='color'):
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
        mode: 'color' or 'bw' for output mode
    
    Returns:
        Dict with paths to generated files
    """
    os.makedirs(output_dir, exist_ok=True)
    output_files = {}
    
    # Add mode suffix to filenames
    mode_suffix = f"_{mode}" if mode else ""
    
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
            board = generate_bingo_board(items, grid_size, 'standard', folder_type, i + 1, mode)
            boards.append(board)
        
        output_path = os.path.join(output_dir, f"{theme_name}_Bingo_{size_name}{mode_suffix}.pdf")
        save_images_as_pdf(boards, output_path)
        output_files[f'bingo_{size_name}'] = output_path
        
        if include_storage_label:
            label_path = create_companion_label(output_path, theme_name, f"Bingo {size_name}")
            output_files[f'bingo_{size_name}_label'] = label_path
        
        # Errorless boards
        if include_errorless:
            boards = []
            for i in range(num_boards):
                board = generate_bingo_board(items, grid_size, 'errorless', folder_type, i + 1, mode)
                boards.append(board)
            
            output_path = os.path.join(output_dir, f"{theme_name}_Bingo_{size_name}_Errorless{mode_suffix}.pdf")
            save_images_as_pdf(boards, output_path)
            output_files[f'bingo_{size_name}_errorless'] = output_path
            
            if include_storage_label:
                label_path = create_companion_label(output_path, theme_name, f"Bingo {size_name} (Errorless)")
                output_files[f'bingo_{size_name}_errorless_label'] = label_path
        
        # Real image boards
        if include_real_images:
            boards = []
            for i in range(num_boards):
                board = generate_bingo_board(items, grid_size, 'real_images', 'real_images', i + 1, mode)
                boards.append(board)
            
            output_path = os.path.join(output_dir, f"{theme_name}_Bingo_{size_name}_Real_Images{mode_suffix}.pdf")
            save_images_as_pdf(boards, output_path)
            output_files[f'bingo_{size_name}_real'] = output_path
            
            if include_storage_label:
                label_path = create_companion_label(output_path, theme_name, f"Bingo {size_name} (Real Images)")
                output_files[f'bingo_{size_name}_real_label'] = label_path
        
        # Boardmaker boards
        if include_boardmaker:
            boards = []
            for i in range(num_boards):
                board = generate_bingo_board(items, grid_size, 'boardmaker', 'boardmaker', i + 1, mode)
                boards.append(board)
            
            output_path = os.path.join(output_dir, f"{theme_name}_Bingo_{size_name}_Boardmaker{mode_suffix}.pdf")
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
                                             page_num + 1, num_pages, mode)
            pages.append(page)
        
        output_path = os.path.join(output_dir, f"{theme_name}_Bingo_Calling_Cards_Icons{mode_suffix}.pdf")
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
                                             page_num + 1, num_pages, mode)
            pages.append(page)
        
        output_path = os.path.join(output_dir, f"{theme_name}_Bingo_Calling_Cards_Words{mode_suffix}.pdf")
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
                                                 page_num + 1, num_pages, mode)
                pages.append(page)
            
            output_path = os.path.join(output_dir, f"{theme_name}_Bingo_Calling_Cards_Real_Images{mode_suffix}.pdf")
            save_images_as_pdf(pages, output_path)
            output_files['calling_cards_real'] = output_path
            
            if include_storage_label:
                label_path = create_companion_label(output_path, theme_name, "Bingo Calling Cards (Real Images)")
                output_files['calling_cards_real_label'] = label_path
    
    return output_files


def generate_bingo_game_dual_mode(items, theme_name, output_dir='output', **kwargs):
    """
    Generate complete set of bingo boards and calling cards in both color and BW modes.
    
    Args:
        items: List of dicts with 'image' and 'label' keys
        theme_name: Name of theme for file naming
        output_dir: Output directory path
        **kwargs: Additional arguments passed to generate_bingo_game_set
    
    Returns:
        Dict with 'color' and 'bw' keys, each containing file paths
    """
    output_paths = {'color': {}, 'bw': {}}
    
    # Generate color version
    color_files = generate_bingo_game_set(items, theme_name, output_dir, mode='color', **kwargs)
    output_paths['color'] = color_files
    
    # Generate black-and-white version
    bw_files = generate_bingo_game_set(items, theme_name, output_dir, mode='bw', **kwargs)
    output_paths['bw'] = bw_files
    
    return output_paths
