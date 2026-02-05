"""
Vocabulary Cards Generator

Generates SPED-friendly vocabulary cards with 5 different versions:
- Standard Vocabulary Cards (AAC/PCS symbols with optional labels)
- Real Image Vocabulary Cards (real photographs with labels)
- Boardmaker Vocabulary Cards (Boardmaker symbols with labels)
- Cut-and-Paste Version (for hands-on activities)
- Lanyard-Friendly Version (smaller size for portable communication)

All cards follow SPED design principles: large images, high contrast,
minimal clutter, consistent spacing, and 300 DPI output.

Uses modular helper functions from utils/draw_helpers.py for clean, maintainable code.
"""

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from utils.config import MARGINS, CARD_SIZES, DPI, COLORS, FONT_SIZES, PAGE_WIDTH, PAGE_HEIGHT
from utils.image_loader import get_image_loader
from utils.pdf_export import save_images_as_pdf
from utils.draw_helpers import (
    scale_image_to_fit,
    draw_card_background,
    draw_page_number,
    draw_copyright_footer,
    draw_text_centered_in_rect,
    create_placeholder_image
)
from utils.storage_label_helper import create_companion_label
import os
import math


def hex_to_grayscale(hex_color):
    """Convert hex color to grayscale using luminosity method."""
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    
    # Convert hex to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Luminosity method: 0.299*R + 0.587*G + 0.114*B
    gray = int(0.299 * r + 0.587 * g + 0.114 * b)
    
    # Convert back to hex
    return f'#{gray:02x}{gray:02x}{gray:02x}'


def image_to_grayscale(image):
    """Convert PIL image to grayscale with contrast enhancement."""
    # Convert to grayscale
    gray_image = image.convert('L')
    
    # Enhance contrast for better printing
    enhancer = ImageEnhance.Contrast(gray_image)
    enhanced = enhancer.enhance(1.2)
    
    # Convert back to RGBA for transparency support
    return enhanced.convert('RGBA')


def generate_vocab_card(vocab_item, folder_type='aac', with_label=True, card_size='standard', card_style=None, mode='color'):
    """
    Generate a single vocabulary card.
    
    Args:
        vocab_item: Dict with 'image' and 'label' keys
        folder_type: 'aac', 'images' (real), or 'colour_images' (outline)
        with_label: Include text label under icon
        card_size: 'standard', 'large', etc.
        card_style: Optional dict with 'border_width', 'corner_radius', 'shadow'
        mode: 'color' or 'bw' for output mode
        
    Returns:
        PIL.Image: Generated vocabulary card
    """
    # Get card dimensions
    width, height = CARD_SIZES[card_size]
    
    # Create blank card
    card = Image.new('RGBA', (width, height), COLORS['white'] + (255,))
    draw = ImageDraw.Draw(card)
    
    # Draw card background with optional styling
    if card_style is None:
        card_style = {
            'border_width': 2,
            'corner_radius': 10,
            'shadow': False,
            'fill_color': COLORS['white']
        }
    
    # Adjust colors for BW mode
    if mode == 'bw':
        card_style['fill_color'] = COLORS['white']
        # Make borders black for high contrast
        border_color = COLORS['black']
    
    draw_card_background(draw, (0, 0, width, height), card_style)
    
    # Load image
    image_loader = get_image_loader()
    image_filename = vocab_item.get('image', '')
    label_text = vocab_item.get('label', '')
    
    try:
        theme_image = image_loader.load_image(image_filename, folder_type)
    except FileNotFoundError:
        # Create placeholder
        theme_image = create_placeholder_image(500, 500, f"Missing:\n{image_filename}")
    
    # Convert to grayscale for BW mode
    if mode == 'bw':
        theme_image = image_to_grayscale(theme_image)
    
    # Calculate areas for image and label
    label_height = 60 if with_label else 0
    image_area = (0, 0, width, height - label_height)
    
    # Scale and position image
    scaled_image, img_x, img_y = scale_image_to_fit(
        theme_image,
        image_area,
        padding=5
    )
    
    # Paste image
    card.paste(scaled_image, (img_x, img_y), scaled_image)
    
    # Add label if requested
    if with_label and label_text:
        label_area = (0, height - label_height, width, height)
        draw_text_centered_in_rect(draw, label_text, label_area, font_size=FONT_SIZES['body'])
    
    return card


def generate_vocab_grid_page(vocab_items, folder_type='aac', with_labels=True, 
                             cards_per_row=3, card_size='standard', page_num=1, total_pages=1, mode='color'):
    """
    Generate a page with vocabulary cards in a grid layout.
    
    Args:
        vocab_items: List of vocab item dicts
        folder_type: 'aac', 'images', or 'colour_images'
        with_labels: Include text labels under icons
        cards_per_row: Number of cards per row (2, 3, or 4)
        card_size: Size of each card
        page_num: Current page number
        total_pages: Total number of pages
        mode: 'color' or 'bw' for output mode
        
    Returns:
        PIL.Image: Page with grid of vocabulary cards
    """
    # Create page
    page = Image.new('RGB', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), COLORS['white'])
    draw = ImageDraw.Draw(page)
    
    # Calculate grid dimensions
    card_width, card_height = CARD_SIZES[card_size]
    spacing = 40  # Space between cards
    
    # Calculate number of rows needed
    cards_per_page = cards_per_row * math.floor((PAGE_HEIGHT - 200) / (card_height + spacing))
    rows = math.ceil(len(vocab_items) / cards_per_row)
    
    # Calculate starting positions to center grid
    total_width = (cards_per_row * card_width) + ((cards_per_row - 1) * spacing)
    total_height = (rows * card_height) + ((rows - 1) * spacing)
    start_x = int((PAGE_WIDTH - total_width) / 2)
    start_y = int((PAGE_HEIGHT - total_height - 150) / 2)  # Leave room for footer
    
    # Generate and place cards
    for idx, vocab_item in enumerate(vocab_items):
        row = idx // cards_per_row
        col = idx % cards_per_row
        
        x = int(start_x + col * (card_width + spacing))
        y = int(start_y + row * (card_height + spacing))
        
        # Generate card with mode
        card = generate_vocab_card(vocab_item, folder_type, with_labels, card_size, mode=mode)
        
        # Paste onto page
        page.paste(card, (x, y))
    
    # Add page number and copyright footer
    draw_page_number(draw, page_num, total_pages, int(PAGE_WIDTH), int(PAGE_HEIGHT))
    draw_copyright_footer(draw, int(PAGE_WIDTH), int(PAGE_HEIGHT))
    
    return page


def generate_cutout_vocab_page(vocab_items, folder_type='aac', page_num=1, total_pages=1, 
                                with_grab_tabs=True, bold_outline=True, mode='color'):
    """
    Generate a page of cut-out vocabulary cards.
    
    Args:
        vocab_items: List of vocab item dicts (max 6 per page)
        folder_type: 'aac', 'images', or 'colour_images'
        page_num: Current page number
        total_pages: Total number of pages
        with_grab_tabs: Include grab tabs for fine motor support
        bold_outline: Include bold border for visibility
        mode: 'color' or 'bw' for output mode
        
    Returns:
        PIL.Image: Page with cut-out cards in 2×3 grid
    """
    # Create page
    page = Image.new('RGB', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), COLORS['white'])
    draw = ImageDraw.Draw(page)
    
    # Use standard card size for cutouts
    card_width, card_height = CARD_SIZES['standard']
    
    # 2×3 grid layout
    spacing = 60
    cols = 2
    rows = 3
    
    # Center the grid
    total_grid_width = (cols * card_width) + ((cols - 1) * spacing)
    total_grid_height = (rows * card_height) + ((rows - 1) * spacing)
    start_x = int((PAGE_WIDTH - total_grid_width) / 2)
    start_y = int((PAGE_HEIGHT - total_grid_height - 150) / 2)
    
    # Card style with bold outline if requested
    card_style = {
        'border_width': 3 if bold_outline else 2,
        'corner_radius': 10,
        'shadow': False,
        'fill_color': COLORS['white']
    }
    
    # Generate up to 6 cards
    for idx, vocab_item in enumerate(vocab_items[:6]):
        row = idx // cols
        col = idx % cols
        
        x = int(start_x + col * (card_width + spacing))
        y = int(start_y + row * (card_height + spacing))
        
        # Generate card with mode
        card = generate_vocab_card(vocab_item, folder_type, with_label=True, 
                                   card_size='standard', card_style=card_style, mode=mode)
        
        # Add grab tab if requested
        if with_grab_tabs:
            # Draw grab tab with scissors symbol
            tab_width = 80
            tab_height = 30
            tab_x = x + (card_width - tab_width) // 2
            tab_y = y + card_height
            
            # Tab rectangle
            draw.rectangle(
                [tab_x, tab_y, tab_x + tab_width, tab_y + tab_height],
                fill=COLORS['light_gray'],
                outline=COLORS['black'],
                width=2
            )
            
            # Scissors symbol
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            scissors = "✂"
            bbox = draw.textbbox((0, 0), scissors, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = tab_x + (tab_width - text_width) // 2
            text_y = tab_y + (tab_height - text_height) // 2
            draw.text((text_x, text_y), scissors, fill=COLORS['black'], font=font)
        
        # Paste card
        page.paste(card, (x, y))
    
    # Add page number and copyright footer
    draw_page_number(draw, page_num, total_pages, int(PAGE_WIDTH), int(PAGE_HEIGHT))
    draw_copyright_footer(draw, int(PAGE_WIDTH), int(PAGE_HEIGHT))
    
    return page


def generate_lanyard_vocab_page(vocab_items, folder_type='aac', page_num=1, total_pages=1, mode='color'):
    """
    Generate lanyard-friendly vocabulary cards with hole-punch indicators.
    
    Args:
        vocab_items: List of vocab item dicts
        folder_type: 'aac', 'images', or 'colour_images'
        page_num: Current page number
        total_pages: Total number of pages
        mode: 'color' or 'bw' for output mode
        
    Returns:
        PIL.Image: Page with lanyard-friendly cards
    """
    # Create page
    page = Image.new('RGB', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), COLORS['white'])
    draw = ImageDraw.Draw(page)
    
    # Smaller card size for lanyard use
    lanyard_width = 500  # Approx 1.67" at 300 DPI
    lanyard_height = 500
    lanyard_strip_width = 150  # Left margin for hole punch
    
    # Calculate layout (3 cards per page)
    cards_per_page = 3
    spacing = 100
    
    # Center vertically
    total_height = (cards_per_page * (lanyard_height + lanyard_strip_width)) + ((cards_per_page - 1) * spacing)
    start_y = int((PAGE_HEIGHT - total_height) / 2)
    start_x = int((PAGE_WIDTH - (lanyard_strip_width + lanyard_width)) / 2)
    
    # Generate up to 3 lanyard cards
    for idx, vocab_item in enumerate(vocab_items[:cards_per_page]):
        y = int(start_y + idx * (lanyard_height + spacing))
        
        # Draw lanyard strip with hole-punch indicator
        strip_rect = (start_x, y, start_x + lanyard_strip_width, y + lanyard_height)
        draw.rectangle(strip_rect, fill=COLORS['white'], outline=COLORS['black'], width=5)
        
        # Hole-punch indicator (circle)
        hole_x = start_x + lanyard_strip_width // 2
        hole_y = y + 50
        hole_radius = 15
        
        # Draw reinforcement pattern
        for r in [hole_radius + 10, hole_radius + 5]:
            draw.ellipse(
                [hole_x - r, hole_y - r, hole_x + r, hole_y + r],
                outline=COLORS['black'],
                width=2
            )
        
        # Draw hole
        draw.ellipse(
            [hole_x - hole_radius, hole_y - hole_radius, 
             hole_x + hole_radius, hole_y + hole_radius],
            fill=COLORS['white'],
            outline=COLORS['black'],
            width=3
        )
        
        # Vertical separator line
        draw.line(
            [(start_x + lanyard_strip_width, y), 
             (start_x + lanyard_strip_width, y + lanyard_height)],
            fill=COLORS['black'],
            width=3
        )
        
        # Create vocab card
        card_img = Image.new('RGBA', (lanyard_width, lanyard_height), COLORS['white'] + (255,))
        card_draw = ImageDraw.Draw(card_img)
        
        # Load and scale image
        image_loader = get_image_loader()
        image_filename = vocab_item.get('image', '')
        label_text = vocab_item.get('label', '')
        
        try:
            theme_image = image_loader.load_image(image_filename, folder_type)
        except FileNotFoundError:
            theme_image = create_placeholder_image(400, 400, f"Missing:\n{image_filename}")
        
        # Convert to grayscale for BW mode
        if mode == 'bw':
            theme_image = image_to_grayscale(theme_image)
        
        # Scale image
        label_height = 60
        image_area = (0, 0, lanyard_width, lanyard_height - label_height)
        scaled_image, img_x, img_y = scale_image_to_fit(theme_image, image_area, padding=10)
        
        # Paste image
        card_img.paste(scaled_image, (img_x, img_y), scaled_image)
        
        # Add label
        if label_text:
            label_area = (0, lanyard_height - label_height, lanyard_width, lanyard_height)
            draw_text_centered_in_rect(card_draw, label_text, label_area, font_size=FONT_SIZES['small'])
        
        # Convert and paste
        card_rgb = card_img.convert('RGB')
        page.paste(card_rgb, (start_x + lanyard_strip_width, y))
        
        # Draw border around card
        draw.rectangle(
            [start_x + lanyard_strip_width, y, 
             start_x + lanyard_strip_width + lanyard_width, y + lanyard_height],
            outline=COLORS['black'],
            width=2
        )
    
    # Add page number and copyright footer
    draw_page_number(draw, page_num, total_pages, int(PAGE_WIDTH), int(PAGE_HEIGHT))
    draw_copyright_footer(draw, int(PAGE_WIDTH), int(PAGE_HEIGHT))
    
    return page


def generate_vocab_cards_set(fringe_vocab, theme_name, output_dir='output',
                             include_real_images=False, include_boardmaker=False,
                             include_cutouts=True, include_lanyard=True,
                             include_storage_label=True, cards_per_row=3, mode='color'):
    """
    Generate complete set of vocabulary cards with all versions.
    
    Args:
        fringe_vocab: List of vocab item dicts with 'image' and 'label'
        theme_name: Name of the theme (for file naming)
        output_dir: Directory for output files
        include_real_images: Generate real image version if available
        include_boardmaker: Generate Boardmaker version if available
        include_cutouts: Generate cut-and-paste version
        include_lanyard: Generate lanyard-friendly version
        include_storage_label: Generate storage labels
        cards_per_row: Number of cards per row (2, 3, or 4)
        mode: 'color' or 'bw' for output mode
        
    Returns:
        Dict with paths to generated files
    """
    os.makedirs(output_dir, exist_ok=True)
    output_files = {}
    
    # Add mode suffix to filenames
    mode_suffix = f"_{mode}" if mode else ""
    
    # Determine grid size based on number of items
    num_items = len(fringe_vocab)
    if num_items <= 4:
        cards_per_row = 2
    elif num_items <= 9:
        cards_per_row = 3
    else:
        cards_per_row = 4
    
    cards_per_page = cards_per_row * 3  # Assume 3 rows per page
    
    # 1. Standard Vocabulary Cards (AAC/PCS)
    standard_pages = []
    for page_start in range(0, num_items, cards_per_page):
        page_items = fringe_vocab[page_start:page_start + cards_per_page]
        page_num = (page_start // cards_per_page) + 1
        total_pages = math.ceil(num_items / cards_per_page)
        
        page = generate_vocab_grid_page(
            page_items,
            folder_type='aac',
            with_labels=True,
            cards_per_row=cards_per_row,
            card_size='standard',
            page_num=page_num,
            total_pages=total_pages,
            mode=mode
        )
        standard_pages.append(page)
    
    standard_path = os.path.join(output_dir, f"{theme_name}_Vocabulary_Cards{mode_suffix}.pdf")
    save_images_as_pdf(standard_pages, standard_path)
    output_files['standard'] = standard_path
    
    # Storage label for standard cards
    if include_storage_label:
        label_path = create_companion_label(
            standard_path,
            theme_name=theme_name,
            activity_name="Vocabulary Cards",
            level=None
        )
        output_files['standard_label'] = label_path
    
    # 2. Real Image Vocabulary Cards (if requested)
    if include_real_images:
        real_pages = []
        for page_start in range(0, num_items, cards_per_page):
            page_items = fringe_vocab[page_start:page_start + cards_per_page]
            page_num = (page_start // cards_per_page) + 1
            total_pages = math.ceil(num_items / cards_per_page)
            
            page = generate_vocab_grid_page(
                page_items,
                folder_type='images',  # Real images
                with_labels=True,
                cards_per_row=cards_per_row,
                card_size='standard',
                page_num=page_num,
                total_pages=total_pages,
                mode=mode
            )
            real_pages.append(page)
        
        real_path = os.path.join(output_dir, f"{theme_name}_Vocabulary_Cards_Real_Images{mode_suffix}.pdf")
        save_images_as_pdf(real_pages, real_path)
        output_files['real_images'] = real_path
        
        if include_storage_label:
            label_path = create_companion_label(
                real_path,
                theme_name=theme_name,
                activity_name="Vocabulary Cards (Real Images)"
            )
            output_files['real_images_label'] = label_path
    
    # 3. Boardmaker Vocabulary Cards (if requested)
    if include_boardmaker:
        bm_pages = []
        for page_start in range(0, num_items, cards_per_page):
            page_items = fringe_vocab[page_start:page_start + cards_per_page]
            page_num = (page_start // cards_per_page) + 1
            total_pages = math.ceil(num_items / cards_per_page)
            
            page = generate_vocab_grid_page(
                page_items,
                folder_type='colour_images',  # Boardmaker/outline
                with_labels=True,
                cards_per_row=cards_per_row,
                card_size='standard',
                page_num=page_num,
                total_pages=total_pages,
                mode=mode
            )
            bm_pages.append(page)
        
        bm_path = os.path.join(output_dir, f"{theme_name}_Vocabulary_Cards_Boardmaker{mode_suffix}.pdf")
        save_images_as_pdf(bm_pages, bm_path)
        output_files['boardmaker'] = bm_path
        
        if include_storage_label:
            label_path = create_companion_label(
                bm_path,
                theme_name=theme_name,
                activity_name="Vocabulary Cards (Boardmaker)"
            )
            output_files['boardmaker_label'] = label_path
    
    # 4. Cut-and-Paste Version
    if include_cutouts:
        cutout_pages = []
        items_per_page = 6  # 2×3 grid
        
        for page_start in range(0, num_items, items_per_page):
            page_items = fringe_vocab[page_start:page_start + items_per_page]
            page_num = (page_start // items_per_page) + 1
            total_pages = math.ceil(num_items / items_per_page)
            
            page = generate_cutout_vocab_page(
                page_items,
                folder_type='aac',
                page_num=page_num,
                total_pages=total_pages,
                with_grab_tabs=True,
                bold_outline=True,
                mode=mode
            )
            cutout_pages.append(page)
        
        cutout_path = os.path.join(output_dir, f"{theme_name}_Vocabulary_Cards_Cutouts{mode_suffix}.pdf")
        save_images_as_pdf(cutout_pages, cutout_path)
        output_files['cutouts'] = cutout_path
        
        if include_storage_label:
            label_path = create_companion_label(
                cutout_path,
                theme_name=theme_name,
                activity_name="Vocabulary Cards (Cut-outs)"
            )
            output_files['cutouts_label'] = label_path
    
    # 5. Lanyard-Friendly Version
    if include_lanyard:
        lanyard_pages = []
        items_per_page = 3  # 3 cards per page
        
        for page_start in range(0, num_items, items_per_page):
            page_items = fringe_vocab[page_start:page_start + items_per_page]
            page_num = (page_start // items_per_page) + 1
            total_pages = math.ceil(num_items / items_per_page)
            
            page = generate_lanyard_vocab_page(
                page_items,
                folder_type='aac',
                page_num=page_num,
                total_pages=total_pages,
                mode=mode
            )
            lanyard_pages.append(page)
        
        lanyard_path = os.path.join(output_dir, f"{theme_name}_Vocabulary_Cards_Lanyard{mode_suffix}.pdf")
        save_images_as_pdf(lanyard_pages, lanyard_path)
        output_files['lanyard'] = lanyard_path
        
        if include_storage_label:
            label_path = create_companion_label(
                lanyard_path,
                theme_name=theme_name,
                activity_name="Vocabulary Cards (Lanyard)"
            )
            output_files['lanyard_label'] = label_path
    
    return output_files


def generate_vocab_cards_dual_mode(fringe_vocab, theme_name, output_dir='output',
                                   include_real_images=False, include_boardmaker=False,
                                   include_cutouts=True, include_lanyard=True,
                                   include_storage_label=True, cards_per_row=3):
    """
    Generate vocabulary cards in both color and black-and-white modes.
    
    Args:
        fringe_vocab: List of vocab item dicts with 'image' and 'label'
        theme_name: Name of the theme (for file naming)
        output_dir: Directory for output files
        include_real_images: Generate real image version if available
        include_boardmaker: Generate Boardmaker version if available
        include_cutouts: Generate cut-and-paste version
        include_lanyard: Generate lanyard-friendly version
        include_storage_label: Generate storage labels
        cards_per_row: Number of cards per row (2, 3, or 4)
        
    Returns:
        Dict with paths to both color and BW files
    """
    # Generate color version
    color_files = generate_vocab_cards_set(
        fringe_vocab, theme_name, output_dir,
        include_real_images, include_boardmaker,
        include_cutouts, include_lanyard,
        include_storage_label, cards_per_row,
        mode='color'
    )
    
    # Generate black-and-white version
    bw_files = generate_vocab_cards_set(
        fringe_vocab, theme_name, output_dir,
        include_real_images, include_boardmaker,
        include_cutouts, include_lanyard,
        include_storage_label, cards_per_row,
        mode='bw'
    )
    
    return {
        'color': color_files,
        'bw': bw_files
    }


# For backward compatibility and testing
if __name__ == "__main__":
    # Test data
    test_vocab = [
        {'image': 'bear.png', 'label': 'Brown Bear'},
        {'image': 'duck.png', 'label': 'Yellow Duck'},
        {'image': 'frog.png', 'label': 'Green Frog'},
        {'image': 'cat.png', 'label': 'Red Cat'},
        {'image': 'dog.png', 'label': 'Purple Dog'},
        {'image': 'fish.png', 'label': 'Blue Fish'},
    ]
    
    output_files = generate_vocab_cards_set(
        fringe_vocab=test_vocab,
        theme_name='Test_Brown_Bear',
        output_dir='output',
        include_real_images=False,
        include_boardmaker=False,
        include_cutouts=True,
        include_lanyard=True,
        include_storage_label=True
    )
    
    print("Generated Vocabulary Cards:")
    for key, path in output_files.items():
        print(f"  {key}: {path}")
