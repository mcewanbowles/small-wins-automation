"""
Find & Cover Generator

Generates differentiated "Find and Cover" activity sheets with 4 levels:
- Level 1: Errorless (all icons match target)
- Level 2: Mixed (50% match, 50% distractors)
- Level 3: Field of 6 distractors (more challenging)
- Level 4: Cut-and-paste version

Uses modular helper functions from utils/draw_helpers.py for consistent layout.
"""

from PIL import Image, ImageDraw, ImageFont
import os
from utils.config import (
    DPI, PAGE_WIDTH, PAGE_HEIGHT, MARGINS, FONT_SIZES,
    COLORS, CARD_SIZES
)
from utils.image_loader import get_image_loader
from utils.layout import create_page_canvas, add_page_border
from utils.pdf_export import save_images_as_pdf
from utils.draw_helpers import (
    calculate_cell_rect,
    scale_image_to_fit,
    draw_card_background,
    draw_text_centered_in_rect,
    draw_page_number,
    draw_copyright_footer,
    create_placeholder_image
)
from utils.fonts import get_font_manager
import random


def generate_find_cover_worksheet(
    target_image,
    target_label,
    grid_items,
    theme_name='Theme',
    level=1,
    grid_size=(4, 4),
    folder_type='color',
    page_number=1,
    total_pages=1,
    card_style=None
):
    """
    Generate a single Find & Cover worksheet.
    
    Args:
        target_image: Target image filename to find
        target_label: Label for target image
        grid_items: List of (image, label) tuples for grid
        theme_name: Theme name
        level: Differentiation level (1-4)
        grid_size: Tuple (rows, cols) for grid
        folder_type: Image folder type
        page_number: Current page number
        total_pages: Total number of pages
        card_style: Optional card styling dict
        
    Returns:
        PIL.Image: Generated worksheet
    """
    page = create_page_canvas()
    draw = ImageDraw.Draw(page)
    image_loader = get_image_loader()
    font_manager = get_font_manager()
    
    if card_style is None:
        card_style = {'border_width': 2, 'corner_radius': 0, 'shadow': False}
    
    # Calculate layout areas
    header_height = 180
    instruction_height = 60
    grid_margin_top = header_height + instruction_height + 20
    grid_margin_bottom = 120  # Space for footer and page number
    
    available_height = PAGE_HEIGHT - grid_margin_top - grid_margin_bottom
    available_width = PAGE_WIDTH - (MARGINS['page'] * 2)
    
    # Header area: Target icon
    target_box_size = 140
    target_x = (PAGE_WIDTH - target_box_size) // 2
    target_y = 60
    
    # Draw target box with label
    target_rect = (target_x, target_y, target_x + target_box_size, target_y + target_box_size)
    draw_card_background(draw, target_rect, card_style)
    
    # Load and display target image
    try:
        target_img = image_loader.load_image(target_image, folder_type)
        scaled_target, (tx, ty) = scale_image_to_fit(
            target_img, target_rect, padding=10
        )
        page.paste(scaled_target, (tx, ty), scaled_target if scaled_target.mode == 'RGBA' else None)
    except Exception as e:
        print(f"Warning: Could not load target image {target_image}: {e}")
        placeholder = create_placeholder_image(target_box_size - 20, target_box_size - 20, target_label[:10])
        page.paste(placeholder, (target_x + 10, target_y + 10))
    
    # Instruction text
    instruction_y = target_y + target_box_size + 15
    instruction_text = "Find and cover all matching icons"
    try:
        instruction_font = font_manager.get_font('title', FONT_SIZES['title'] - 6)
    except:
        instruction_font = ImageFont.load_default()
    
    # Center instruction text
    try:
        bbox = draw.textbbox((0, 0), instruction_text, font=instruction_font)
        text_width = bbox[2] - bbox[0]
    except:
        text_width = len(instruction_text) * 12
    
    instruction_x = (PAGE_WIDTH - text_width) // 2
    draw.text((instruction_x, instruction_y), instruction_text, 
              fill=COLORS['text'], font=instruction_font)
    
    # Calculate grid layout
    rows, cols = grid_size
    cell_spacing = 12
    
    # Calculate cell size to fit available space
    cell_width = (available_width - (cell_spacing * (cols - 1))) // cols
    cell_height = (available_height - (cell_spacing * (rows - 1))) // rows
    cell_size = min(cell_width, cell_height)
    
    # Center grid on page
    total_grid_width = (cell_size * cols) + (cell_spacing * (cols - 1))
    total_grid_height = (cell_size * rows) + (cell_spacing * (rows - 1))
    grid_start_x = (PAGE_WIDTH - total_grid_width) // 2
    grid_start_y = grid_margin_top
    
    # Generate grid items based on level
    total_cells = rows * cols
    grid_content = []
    
    if level == 1:
        # Level 1: Errorless - all match target
        grid_content = [(target_image, target_label)] * total_cells
        
    elif level == 2:
        # Level 2: Mixed - 50% match, 50% distractors
        num_matches = total_cells // 2
        grid_content = [(target_image, target_label)] * num_matches
        
        # Add distractors
        distractors = [item for item in grid_items if item[0] != target_image]
        while len(grid_content) < total_cells and distractors:
            grid_content.append(random.choice(distractors))
            
    elif level == 3:
        # Level 3: Field of 6 distractors - fewer matches
        num_matches = min(6, total_cells // 3)
        grid_content = [(target_image, target_label)] * num_matches
        
        # Add more distractors
        distractors = [item for item in grid_items if item[0] != target_image]
        while len(grid_content) < total_cells and distractors:
            grid_content.append(random.choice(distractors))
            
    elif level == 4:
        # Level 4: Cut-and-paste - empty grid, target shown separately
        # Grid is empty circles for pasting
        grid_content = [(None, "")] * total_cells
    
    # Shuffle grid content (except for level 4)
    if level != 4:
        random.shuffle(grid_content)
    
    # Draw grid
    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            if idx >= len(grid_content):
                break
            
            x1 = grid_start_x + (col * (cell_size + cell_spacing))
            y1 = grid_start_y + (row * (cell_size + cell_spacing))
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            cell_rect = (x1, y1, x2, y2)
            
            # Draw cell background
            if level == 4:
                # Empty circle for cut-and-paste
                draw_card_background(draw, cell_rect, {
                    'border_width': 2,
                    'corner_radius': cell_size // 2,  # Make circular
                    'shadow': False
                })
            else:
                draw_card_background(draw, cell_rect, card_style)
            
            # Place image in cell
            img_filename, img_label = grid_content[idx]
            if img_filename and level != 4:
                try:
                    cell_img = image_loader.load_image(img_filename, folder_type)
                    scaled_img, (cx, cy) = scale_image_to_fit(
                        cell_img, cell_rect, padding=5
                    )
                    page.paste(scaled_img, (cx, cy), scaled_img if scaled_img.mode == 'RGBA' else None)
                except Exception as e:
                    # Use placeholder for missing images
                    placeholder = create_placeholder_image(
                        cell_size - 10, cell_size - 10, 
                        img_label[:3] if img_label else "?"
                    )
                    page.paste(placeholder, (x1 + 5, y1 + 5))
    
    # Add page border
    add_page_border(page)
    
    # Add page number
    draw_page_number(draw, page_number, total_pages)
    
    # Add copyright footer
    draw_copyright_footer(draw)
    
    return page


def generate_find_cover_set(
    target_items,
    all_items,
    theme_name='Theme',
    level=1,
    grid_size=(4, 4),
    folder_type='color',
    output_dir='output',
    sheets_per_target=1,
    include_storage_label=False,
    card_style=None
):
    """
    Generate a set of Find & Cover worksheets.
    
    Args:
        target_items: List of dicts with 'image' and 'label' keys for target items
        all_items: List of all available items (includes targets + distractors)
        theme_name: Theme name for PDF naming
        level: Differentiation level (1-4)
        grid_size: Tuple (rows, cols) for grid layout
        folder_type: Image folder type ('color', 'outline', 'aac')
        output_dir: Output directory path
        sheets_per_target: Number of sheets to generate per target
        include_storage_label: If True, generate companion storage label
        card_style: Optional styling dict for cards
        
    Returns:
        list: Generated worksheet pages
    """
    pages = []
    level_names = {
        1: "Level1_Errorless",
        2: "Level2_Mixed",
        3: "Level3_Challenging",
        4: "Level4_Cut_Paste"
    }
    
    # Prepare grid items
    grid_items = [(item['image'], item['label']) for item in all_items]
    
    # Generate worksheets
    for target_item in target_items:
        target_image = target_item['image']
        target_label = target_item['label']
        
        for sheet_num in range(sheets_per_target):
            page = generate_find_cover_worksheet(
                target_image=target_image,
                target_label=target_label,
                grid_items=grid_items,
                theme_name=theme_name,
                level=level,
                grid_size=grid_size,
                folder_type=folder_type,
                page_number=len(pages) + 1,
                total_pages=len(target_items) * sheets_per_target,
                card_style=card_style
            )
            pages.append(page)
    
    # Save PDF
    os.makedirs(output_dir, exist_ok=True)
    level_name = level_names.get(level, f"Level{level}")
    output_filename = f"{theme_name}_Find_Cover_{level_name}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    save_images_as_pdf(
        pages,
        output_path,
        title=f"{theme_name} Find & Cover - {level_name}"
    )
    
    print(f"✓ Generated Find & Cover worksheets")
    print(f"  Level: {level} ({level_name})")
    print(f"  Pages: {len(pages)}")
    print(f"  Output: {output_path}")
    
    # Generate storage label if requested
    if include_storage_label:
        from utils.storage_label_helper import create_companion_label
        
        # Try to find icon from first target
        icon_path = None
        if target_items:
            image_loader = get_image_loader()
            try:
                potential_icon = image_loader.get_image_path(
                    target_items[0]['image'], folder_type
                )
                if os.path.exists(potential_icon):
                    icon_path = potential_icon
            except:
                pass
        
        label_path = create_companion_label(
            main_pdf_path=output_path,
            theme_name=theme_name,
            activity_name="Find & Cover",
            level=level,
            icon_path=icon_path
        )
        print(f"✓ Generated storage label: {label_path}")
    
    return pages


if __name__ == "__main__":
    print("Find & Cover Generator")
    print("=" * 50)
    print("\nDifferentiation Levels:")
    print("  Level 1: Errorless (all icons match)")
    print("  Level 2: Mixed (50% match, 50% distractors)")
    print("  Level 3: Challenging (field of 6 distractors)")
    print("  Level 4: Cut-and-paste version")
    print("\nUsage:")
    print("  from generators import generate_find_cover_set")
    print("  pages = generate_find_cover_set(target_items, all_items, level=1)")
