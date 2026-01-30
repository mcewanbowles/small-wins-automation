"""
AAC Book Board Generator

Generates AAC (Augmentative and Alternative Communication) book boards with:
- Core vocabulary icons (I, you, want, like, see, go, etc.)
- Theme-specific fringe vocabulary
- Configurable grid layouts (5×6 or 6×6)
- Optional color coding by part of speech
- Copyright footer and page numbering
- Optional cut-out icon pages

Uses modular helper architecture from utils/draw_helpers.py for consistency.
"""

import os
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Optional, Tuple
from utils.config import DPI, PAGE_WIDTH, PAGE_HEIGHT, MARGINS, FONT_SIZES, COLORS, CARD_SIZES
from utils.image_loader import get_image_loader
from utils.draw_helpers import (
    calculate_cell_rect,
    scale_image_to_fit,
    draw_card_background,
    draw_page_number,
    draw_copyright_footer,
    draw_text_centered_in_rect,
    create_placeholder_image
)
from utils.pdf_export import save_pdf
from utils.storage_label_helper import create_companion_label


# Core vocabulary set (fixed icons used in most AAC boards)
CORE_VOCABULARY = [
    {'image': 'I.png', 'label': 'I', 'category': 'pronoun', 'color': (135, 206, 250)},  # Light blue
    {'image': 'you.png', 'label': 'you', 'category': 'pronoun', 'color': (135, 206, 250)},
    {'image': 'want.png', 'label': 'want', 'category': 'verb', 'color': (144, 238, 144)},  # Light green
    {'image': 'like.png', 'label': 'like', 'category': 'verb', 'color': (144, 238, 144)},
    {'image': 'see.png', 'label': 'see', 'category': 'verb', 'color': (144, 238, 144)},
    {'image': 'go.png', 'label': 'go', 'category': 'verb', 'color': (144, 238, 144)},
    {'image': 'put.png', 'label': 'put', 'category': 'verb', 'color': (144, 238, 144)},
    {'image': 'yes.png', 'label': 'yes', 'category': 'social', 'color': (255, 182, 193)},  # Light pink
    {'image': 'no.png', 'label': 'no', 'category': 'social', 'color': (255, 182, 193)},
    {'image': 'more.png', 'label': 'more', 'category': 'social', 'color': (255, 182, 193)},
    {'image': 'all_done.png', 'label': 'all done', 'category': 'social', 'color': (255, 182, 193)},
    {'image': 'big.png', 'label': 'big', 'category': 'adjective', 'color': (255, 255, 200)},  # Light yellow
    {'image': 'little.png', 'label': 'little', 'category': 'adjective', 'color': (255, 255, 200)},
    {'image': 'happy.png', 'label': 'happy', 'category': 'emotion', 'color': (255, 218, 185)},  # Peach
    {'image': 'sad.png', 'label': 'sad', 'category': 'emotion', 'color': (255, 218, 185)},
]


def generate_aac_board(
    fringe_vocab: List[Dict],
    theme_name: str = 'AAC_Board',
    grid_size: Tuple[int, int] = (5, 6),
    use_color_coding: bool = True,
    folder_type: str = 'aac',
    card_style: Optional[Dict] = None
) -> Image.Image:
    """
    Generate a single AAC communication board page.
    
    Args:
        fringe_vocab: List of theme-specific icons with 'image' and 'label' keys
        theme_name: Theme name for the board
        grid_size: Tuple of (rows, cols) for grid layout
        use_color_coding: Whether to use color coding by part of speech
        folder_type: Image folder ('aac', 'images', 'Colour_images')
        card_style: Optional styling dict for cards
        
    Returns:
        PIL Image of the AAC board page
    """
    rows, cols = grid_size
    
    # Default card style
    if card_style is None:
        card_style = {
            'border_width': 2,
            'corner_radius': 10,
            'shadow': False
        }
    
    # Create page
    page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
    draw = ImageDraw.Draw(page)
    
    # Combine core and fringe vocabulary
    all_icons = CORE_VOCABULARY.copy()
    
    # Add fringe vocabulary (theme-specific icons)
    for item in fringe_vocab:
        fringe_item = {
            'image': item['image'],
            'label': item['label'],
            'category': item.get('category', 'noun'),
            'color': item.get('color', (255, 200, 255))  # Light purple for nouns
        }
        all_icons.append(fringe_item)
    
    # Limit to grid capacity
    max_icons = rows * cols
    all_icons = all_icons[:max_icons]
    
    # Calculate cell positions
    cells = calculate_cell_rect(
        PAGE_WIDTH,
        PAGE_HEIGHT,
        rows,
        cols,
        padding=12,
        margin=MARGINS['page'],
        footer_height=80
    )
    
    # Load image loader
    image_loader = get_image_loader()
    
    # Draw each icon in grid
    for idx, icon_data in enumerate(all_icons):
        if idx >= len(cells):
            break
            
        x1, y1, x2, y2 = cells[idx]
        cell_rect = (x1, y1, x2, y2)
        
        # Determine background color
        if use_color_coding:
            bg_color = icon_data.get('color', COLORS['white'])
        else:
            bg_color = COLORS['white']
        
        # Draw card background with optional color coding
        custom_style = card_style.copy()
        custom_style['fill_color'] = bg_color
        draw_card_background(draw, cell_rect, custom_style)
        
        # Load and scale icon image
        try:
            icon_image = image_loader.load_image(icon_data['image'], folder_type=folder_type)
            if icon_image is None:
                icon_image = create_placeholder_image(
                    int(x2 - x1 - 20),
                    int(y2 - y1 - 60),
                    icon_data['label']
                )
        except:
            icon_image = create_placeholder_image(
                int(x2 - x1 - 20),
                int(y2 - y1 - 60),
                icon_data['label']
            )
        
        # Reserve space for label at bottom
        label_height = 40
        image_rect = (x1, y1, x2, y2 - label_height)
        
        # Scale and paste image
        scaled_img, img_pos = scale_image_to_fit(icon_image, image_rect, padding=10)
        page.paste(scaled_img, img_pos, scaled_img if scaled_img.mode == 'RGBA' else None)
        
        # Draw label text
        label_rect = (x1, y2 - label_height, x2, y2)
        draw_text_centered_in_rect(
            draw,
            icon_data['label'],
            label_rect,
            font_size=18,
            color=COLORS['black']
        )
    
    # Add copyright footer
    draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
    
    return page


def generate_aac_cutout_icons(
    fringe_vocab: List[Dict],
    theme_name: str = 'AAC_Board',
    folder_type: str = 'aac',
    card_style: Optional[Dict] = None
) -> List[Image.Image]:
    """
    Generate cut-out icon pages for AAC board.
    
    Args:
        fringe_vocab: List of theme-specific icons
        theme_name: Theme name
        folder_type: Image folder type
        card_style: Optional card styling
        
    Returns:
        List of PIL Images (one page per 6 icons)
    """
    # Default card style
    if card_style is None:
        card_style = {
            'border_width': 3,  # Bold outline
            'corner_radius': 10,
            'shadow': False
        }
    
    # Combine core and fringe vocab
    all_icons = CORE_VOCABULARY.copy()
    for item in fringe_vocab:
        all_icons.append({
            'image': item['image'],
            'label': item['label']
        })
    
    pages = []
    icons_per_page = 6
    
    # Create pages with 6 icons each (2×3 grid)
    for page_num in range(0, len(all_icons), icons_per_page):
        page_icons = all_icons[page_num:page_num + icons_per_page]
        
        # Create page
        page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), COLORS['white'])
        draw = ImageDraw.Draw(page)
        
        # Calculate grid positions (2×3)
        cells = calculate_cell_rect(
            PAGE_WIDTH,
            PAGE_HEIGHT,
            2, 3,
            padding=40,
            margin=MARGINS['page'],
            footer_height=80
        )
        
        # Load image loader
        image_loader = get_image_loader()
        
        # Draw icons
        for idx, icon_data in enumerate(page_icons):
            if idx >= len(cells):
                break
                
            x1, y1, x2, y2 = cells[idx]
            cell_rect = (x1, y1, x2, y2)
            
            # Draw card background
            draw_card_background(draw, cell_rect, card_style)
            
            # Load and scale image
            try:
                icon_image = image_loader.load_image(icon_data['image'], folder_type=folder_type)
                if icon_image is None:
                    icon_image = create_placeholder_image(
                        int(x2 - x1 - 20),
                        int(y2 - y1 - 20),
                        icon_data['label']
                    )
            except:
                icon_image = create_placeholder_image(
                    int(x2 - x1 - 20),
                    int(y2 - y1 - 20),
                    icon_data['label']
                )
            
            # Scale and paste
            scaled_img, img_pos = scale_image_to_fit(icon_image, cell_rect, padding=5)
            page.paste(scaled_img, img_pos, scaled_img if scaled_img.mode == 'RGBA' else None)
        
        # Add page number
        draw_page_number(draw, page_num // icons_per_page + 1, 
                        (len(all_icons) + icons_per_page - 1) // icons_per_page)
        
        # Add copyright footer
        draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
        
        pages.append(page)
    
    return pages


def generate_aac_board_set(
    fringe_vocab: List[Dict],
    theme_name: str = 'AAC_Board',
    output_dir: str = 'output',
    grid_size: Tuple[int, int] = (5, 6),
    use_color_coding: bool = True,
    with_cutout_icons: bool = False,
    folder_type: str = 'aac',
    include_storage_label: bool = False,
    card_style: Optional[Dict] = None
) -> Dict[str, str]:
    """
    Generate complete AAC board set with optional cut-out icons.
    
    Args:
        fringe_vocab: List of theme-specific vocabulary items
        theme_name: Theme name for output files
        output_dir: Output directory path
        grid_size: Grid dimensions (rows, cols)
        use_color_coding: Enable color coding by part of speech
        with_cutout_icons: Generate separate cut-out icon pages
        folder_type: Image folder type ('aac', 'images', 'Colour_images')
        include_storage_label: Generate storage labels
        card_style: Optional card styling dictionary
        
    Returns:
        Dictionary with paths to generated files
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    output_files = {}
    
    # Generate AAC board page
    print(f"Generating AAC board for {theme_name}...")
    board_page = generate_aac_board(
        fringe_vocab=fringe_vocab,
        theme_name=theme_name,
        grid_size=grid_size,
        use_color_coding=use_color_coding,
        folder_type=folder_type,
        card_style=card_style
    )
    
    # Save AAC board
    board_filename = f"{theme_name}_AAC_Board.pdf"
    board_path = os.path.join(output_dir, board_filename)
    save_pdf([board_page], board_path)
    output_files['board'] = board_path
    print(f"✓ Saved AAC board: {board_path}")
    
    # Generate storage label for board
    if include_storage_label:
        label_path = create_companion_label(
            main_pdf_path=board_path,
            theme_name=theme_name,
            activity_name='AAC Board',
            level=None
        )
        if label_path:
            output_files['board_label'] = label_path
            print(f"✓ Generated storage label: {label_path}")
    
    # Generate cut-out icon pages if requested
    if with_cutout_icons:
        print(f"Generating cut-out icons...")
        cutout_pages = generate_aac_cutout_icons(
            fringe_vocab=fringe_vocab,
            theme_name=theme_name,
            folder_type=folder_type,
            card_style=card_style
        )
        
        # Save cut-out icons
        cutout_filename = f"{theme_name}_AAC_Icons_Cutouts.pdf"
        cutout_path = os.path.join(output_dir, cutout_filename)
        save_pdf(cutout_pages, cutout_path)
        output_files['cutouts'] = cutout_path
        print(f"✓ Saved cut-out icons: {cutout_path}")
        
        # Generate storage label for cutouts
        if include_storage_label:
            cutout_label_path = create_companion_label(
                main_pdf_path=cutout_path,
                theme_name=theme_name,
                activity_name='AAC Icons',
                level=None
            )
            if cutout_label_path:
                output_files['cutouts_label'] = cutout_label_path
                print(f"✓ Generated storage label: {cutout_label_path}")
    
    print(f"\n✅ AAC board generation complete!")
    return output_files


if __name__ == '__main__':
    # Demo usage
    sample_fringe_vocab = [
        {'image': 'bear.png', 'label': 'bear', 'category': 'noun'},
        {'image': 'duck.png', 'label': 'duck', 'category': 'noun'},
        {'image': 'frog.png', 'label': 'frog', 'category': 'noun'},
        {'image': 'cat.png', 'label': 'cat', 'category': 'noun'},
        {'image': 'dog.png', 'label': 'dog', 'category': 'noun'},
    ]
    
    output_files = generate_aac_board_set(
        fringe_vocab=sample_fringe_vocab,
        theme_name='Brown_Bear',
        output_dir='output',
        grid_size=(5, 6),
        use_color_coding=True,
        with_cutout_icons=True,
        include_storage_label=True
    )
    
    print("\nGenerated files:")
    for key, path in output_files.items():
        print(f"  {key}: {path}")
