"""
Enhanced Sentence Strips (AAC) Generator

Generates lanyard-friendly sentence strips using AAC/PCS symbols for communication.
Features:
- Cut-out icons matching exact size of matching cards
- Lanyard-friendly design with hole-punch indicators
- Horizontal strip layout with 2-4 icon slots
- Cut-out icon pages with optional bold outlines and grab tabs
- Same card style and sizing as matching cards for interchangeability

Uses modular helper functions from utils/draw_helpers.py
"""

from PIL import Image, ImageDraw
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
from utils.fonts import get_font_manager
from utils.color_helpers import image_to_grayscale
from utils.layout import create_page_canvas, add_footer
import os


def generate_sentence_strip(symbol_data, strip_slots=4, with_lanyard_strip=True, 
                            card_style=None, mode="color"):
    """
    Generate a horizontal sentence strip with AAC symbols.
    
    Args:
        symbol_data: List of dicts with 'image', 'label', 'folder_type'
        strip_slots: Number of icon slots in the strip (2-4)
        with_lanyard_strip: If True, add left margin lanyard strip with hole punch
        card_style: Optional dict with 'border_width', 'corner_radius', 'shadow'
        mode: "color" or "bw" for dual-mode output
        
    Returns:
        PIL.Image: Generated sentence strip
    """
    # Calculate dimensions
    # Use standard card size (750x750) from matching cards for icons
    icon_size = CARD_SIZES['standard'][0]  # 750px (2.5" at 300 DPI)
    
    # Lanyard strip dimensions
    lanyard_width = 150 if with_lanyard_strip else 0
    
    # Strip dimensions: icon_size height, width depends on slots + lanyard
    icon_spacing = 20
    strip_width = lanyard_width + (icon_size * strip_slots) + (icon_spacing * (strip_slots + 1))
    strip_height = icon_size + (icon_spacing * 2)
    
    # Create strip canvas
    strip = Image.new('RGBA', (strip_width, strip_height), COLORS['white'] + (255,))
    draw = ImageDraw.Draw(strip)
    
    # Draw outer border
    border_style = card_style or {
        'border_width': 3,
        'corner_radius': 0,
        'shadow': False,
        'fill_color': COLORS['white']
    }
    draw_card_background(draw, (0, 0, strip_width, strip_height), border_style)
    
    # Draw lanyard strip if requested
    if with_lanyard_strip:
        # Reinforced border for lanyard area
        lanyard_rect = (0, 0, lanyard_width, strip_height)
        draw.rectangle(lanyard_rect, outline=COLORS['black'], width=5)
        
        # Vertical line separating lanyard area
        draw.line(
            [(lanyard_width, 0), (lanyard_width, strip_height)],
            fill=COLORS['black'],
            width=3
        )
        
        # Hole punch indicator (small circle)
        hole_y = strip_height // 2
        hole_x = lanyard_width // 2
        hole_radius = 15
        draw.ellipse(
            [hole_x - hole_radius, hole_y - hole_radius,
             hole_x + hole_radius, hole_y + hole_radius],
            fill=COLORS['white'],
            outline=COLORS['black'],
            width=3
        )
        
        # Add reinforcement pattern around hole
        for i in range(3):
            r = hole_radius + 10 + (i * 8)
            draw.ellipse(
                [hole_x - r, hole_y - r, hole_x + r, hole_y + r],
                outline=COLORS['light_gray'],
                width=1
            )
    
    # Place icon slots
    image_loader = get_image_loader()
    current_x = lanyard_width + icon_spacing
    
    for idx in range(strip_slots):
        # Calculate slot rectangle
        slot_x1 = current_x
        slot_y1 = icon_spacing
        slot_x2 = slot_x1 + icon_size
        slot_y2 = slot_y1 + icon_size
        
        # Draw slot border (matching card style)
        slot_style = card_style or {
            'border_width': 2,
            'corner_radius': 10,
            'shadow': False,
            'fill_color': COLORS['white']
        }
        draw_card_background(draw, (slot_x1, slot_y1, slot_x2, slot_y2), slot_style)
        
        # If we have symbol data for this slot, add it
        if idx < len(symbol_data):
            symbol_info = symbol_data[idx]
            image_file = symbol_info.get('image', '')
            label_text = symbol_info.get('label', '')
            folder_type = symbol_info.get('folder_type', 'aac')
            
            # Load image
            try:
                symbol_image = image_loader.load_image(image_file, folder_type)
                # Convert to grayscale if BW mode
                if mode == "bw":
                    symbol_image = image_to_grayscale(symbol_image)
            except FileNotFoundError:
                symbol_image = create_placeholder_image(500, 500, f"Missing:\n{image_file}")
            
            # Reserve space for label if provided
            if label_text:
                label_height = 60
                image_rect = (slot_x1, slot_y1, slot_x2, slot_y2 - label_height)
                label_rect = (slot_x1, slot_y2 - label_height, slot_x2, slot_y2)
            else:
                image_rect = (slot_x1, slot_y1, slot_x2, slot_y2)
            
            # Scale and place image (5px padding like matching cards)
            scaled_image, img_x, img_y = scale_image_to_fit(
                symbol_image,
                image_rect,
                padding=5
            )
            strip.paste(scaled_image, (img_x, img_y), scaled_image)
            
            # Draw label if provided
            if label_text:
                draw_text_centered_in_rect(
                    draw,
                    label_text,
                    label_rect,
                    font_size=FONT_SIZES['small']
                )
        
        current_x += icon_size + icon_spacing
    
    return strip


def generate_cutout_icons(symbol_data, icons_per_page=6, with_bold_outline=True,
                          with_grab_tab=True, card_style=None, mode="color"):
    """
    Generate cut-out icon pages matching exact size of matching cards.
    
    Args:
        symbol_data: List of dicts with 'image', 'label', 'folder_type'
        icons_per_page: Number of icons per page (default 6 for 2x3 grid)
        with_bold_outline: Add bold outline for visibility
        with_grab_tab: Add small tab for fine motor support
        card_style: Optional dict with 'border_width', 'corner_radius', 'shadow'
        mode: "color" or "bw" for dual-mode output
        
    Returns:
        list: Generated pages with cut-out icons
    """
    pages = []
    image_loader = get_image_loader()
    
    # Use standard card size from matching cards
    icon_size = CARD_SIZES['standard'][0]  # 750px (2.5" at 300 DPI)
    
    # Calculate grid layout
    if icons_per_page == 6:
        rows, cols = 2, 3
    elif icons_per_page == 9:
        rows, cols = 3, 3
    elif icons_per_page == 4:
        rows, cols = 2, 2
    else:
        rows, cols = 2, 3  # Default
    
    # Process icons in batches
    for page_start in range(0, len(symbol_data), icons_per_page):
        page = Image.new('RGBA', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), COLORS['white'] + (255,))
        draw = ImageDraw.Draw(page)
        
        page_symbols = symbol_data[page_start:page_start + icons_per_page]
        
        # Calculate cell positions
        spacing = 40
        margin = MARGINS['page']
        footer_height = 100
        
        available_width = PAGE_WIDTH - (2 * margin)
        available_height = PAGE_HEIGHT - (2 * margin) - footer_height
        
        cell_width_with_spacing = available_width / cols
        cell_height_with_spacing = available_height / rows
        
        # Center icons within cells
        for idx, symbol_info in enumerate(page_symbols):
            row = idx // cols
            col = idx % cols
            
            # Calculate cell center
            cell_center_x = margin + (col * cell_width_with_spacing) + (cell_width_with_spacing / 2)
            cell_center_y = margin + (row * cell_height_with_spacing) + (cell_height_with_spacing / 2)
            
            # Icon position (centered in cell)
            icon_x1 = int(cell_center_x - (icon_size / 2))
            icon_y1 = int(cell_center_y - (icon_size / 2))
            icon_x2 = icon_x1 + icon_size
            icon_y2 = icon_y1 + icon_size
            
            # Draw card background with matching card style
            icon_style = card_style or {
                'border_width': 3 if with_bold_outline else 2,
                'corner_radius': 10,
                'shadow': False,
                'fill_color': COLORS['white']
            }
            draw_card_background(draw, (icon_x1, icon_y1, icon_x2, icon_y2), icon_style)
            
            # Add grab tab if requested
            if with_grab_tab:
                tab_width = 80
                tab_height = 30
                tab_x1 = icon_x2 - tab_width - 10
                tab_y1 = icon_y1 - tab_height
                tab_x2 = icon_x2 - 10
                tab_y2 = icon_y1
                
                # Draw tab
                draw.rectangle(
                    [tab_x1, tab_y1, tab_x2, tab_y2],
                    fill=COLORS['light_gray'],
                    outline=COLORS['black'],
                    width=2
                )
                # Tab text
                font_mgr = get_font_manager()
                try:
                    small_font = font_mgr.get_font(FONT_SIZES['small'])
                    tab_text = "✂"
                    bbox = draw.textbbox((0, 0), tab_text, font=small_font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    text_x = tab_x1 + (tab_width - text_width) // 2
                    text_y = tab_y1 + (tab_height - text_height) // 2
                    draw.text((text_x, text_y), tab_text, fill=COLORS['black'], font=small_font)
                except:
                    pass
            
            # Load and place image
            image_file = symbol_info.get('image', '')
            label_text = symbol_info.get('label', '')
            folder_type = symbol_info.get('folder_type', 'aac')
            
            try:
                symbol_image = image_loader.load_image(image_file, folder_type)
                # Convert to grayscale if BW mode
                if mode == "bw":
                    symbol_image = image_to_grayscale(symbol_image)
            except FileNotFoundError:
                symbol_image = create_placeholder_image(500, 500, f"Missing:\n{image_file}")
            
            # Scale and place (5px padding like matching cards)
            scaled_image, img_x, img_y = scale_image_to_fit(
                symbol_image,
                (icon_x1, icon_y1, icon_x2, icon_y2),
                padding=5
            )
            page.paste(scaled_image, (img_x, img_y), scaled_image)
        
        # Add page number
        page_num = (page_start // icons_per_page) + 1
        total_pages = (len(symbol_data) + icons_per_page - 1) // icons_per_page
        draw_page_number(draw, page_num, total_pages)
        
        # Add copyright footer
        draw_copyright_footer(draw)
        
        pages.append(page)
    
    return pages


def generate_sentence_strips_set(sentence_data, icons_data=None, theme_name='Theme',
                                 output_dir='output', include_storage_label=False,
                                 with_lanyard=True, with_cutout_icons=True,
                                 card_style=None, mode="color"):
    """
    Generate complete sentence strips set with lanyard-friendly strips and cut-out icons.
    
    Args:
        sentence_data: List of dicts with sentence configurations
                      e.g., [{'symbols': [{'image': 'dog.png', 'label': 'dog', 'folder_type': 'aac'}, ...], 'slots': 4}]
        icons_data: Optional list of all icons to generate as cut-outs
                   If None, will extract from sentence_data
        theme_name: Theme name for output files
        output_dir: Output directory
        include_storage_label: Generate companion storage labels
        with_lanyard: Add lanyard strip to sentence strips
        with_cutout_icons: Generate cut-out icon pages
        card_style: Optional card styling dict
        mode: "color" or "bw" for dual-mode output
        
    Returns:
        dict: Paths to generated PDFs
    """
    os.makedirs(output_dir, exist_ok=True)
    output_files = {}
    
    # Generate sentence strip pages
    strip_pages = []
    strips_per_page = 3  # 3 strips per page
    
    for page_start in range(0, len(sentence_data), strips_per_page):
        page = Image.new('RGBA', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), COLORS['white'] + (255,))
        draw = ImageDraw.Draw(page)
        
        page_sentences = sentence_data[page_start:page_start + strips_per_page]
        
        # Generate strips
        strips = []
        for sentence in page_sentences:
            symbols = sentence.get('symbols', [])
            slots = sentence.get('slots', 4)
            
            strip = generate_sentence_strip(
                symbols,
                strip_slots=slots,
                with_lanyard_strip=with_lanyard,
                card_style=card_style,
                mode=mode
            )
            strips.append(strip)
        
        # Place strips on page with spacing
        strip_spacing = 80
        total_strip_height = sum(s.height for s in strips)
        total_spacing = strip_spacing * (len(strips) - 1)
        start_y = (PAGE_HEIGHT - total_strip_height - total_spacing - 100) // 2
        
        current_y = start_y
        for strip in strips:
            x = (PAGE_WIDTH - strip.width) // 2
            page.paste(strip, (int(x), int(current_y)), strip)
            current_y += strip.height + strip_spacing
        
        # Add page number
        page_num = (page_start // strips_per_page) + 1
        total_pages = (len(sentence_data) + strips_per_page - 1) // strips_per_page
        draw_page_number(draw, page_num, total_pages)
        
        # Add copyright footer
        draw_copyright_footer(draw)
        
        strip_pages.append(page)
    
    # Save sentence strips PDF
    mode_suffix = f"_{mode}" if mode else ""
    strips_path = f"{output_dir}/{theme_name}_Sentence_Strips{mode_suffix}.pdf"
    save_images_as_pdf(strip_pages, strips_path, title=f"{theme_name} Sentence Strips")
    output_files['strips'] = strips_path
    print(f"✓ Generated sentence strips: {strips_path}")
    
    # Generate cut-out icon pages if requested
    if with_cutout_icons:
        # Extract all unique icons from sentence data if not provided
        if icons_data is None:
            icons_data = []
            seen = set()
            for sentence in sentence_data:
                for symbol in sentence.get('symbols', []):
                    key = (symbol.get('image', ''), symbol.get('folder_type', 'aac'))
                    if key not in seen:
                        seen.add(key)
                        icons_data.append(symbol)
        
        if icons_data:
            icon_pages = generate_cutout_icons(
                icons_data,
                icons_per_page=6,
                with_bold_outline=True,
                with_grab_tab=True,
                card_style=card_style,
                mode=mode
            )
            
            icons_path = f"{output_dir}/{theme_name}_Sentence_Icons_Cutouts{mode_suffix}.pdf"
            save_images_as_pdf(icon_pages, icons_path, title=f"{theme_name} Sentence Icons")
            output_files['icons'] = icons_path
            print(f"✓ Generated cut-out icons: {icons_path}")
    
    # Generate storage labels if requested (only for color mode)
    if include_storage_label and mode == "color":
        from utils.storage_label_helper import create_companion_label
        
        # Try to find an icon from first symbol
        icon_path = None
        if sentence_data and sentence_data[0].get('symbols'):
            image_loader = get_image_loader()
            first_symbol = sentence_data[0]['symbols'][0]
            symbol_file = first_symbol.get('image', '')
            folder_type = first_symbol.get('folder_type', 'aac')
            potential_icon = image_loader.get_image_path(symbol_file, folder_type)
            if os.path.exists(potential_icon):
                icon_path = potential_icon
        
        # Label for strips
        label_path = create_companion_label(
            main_pdf_path=strips_path,
            theme_name=theme_name,
            activity_name="Sentence Strips",
            icon_path=icon_path
        )
        output_files['strips_label'] = label_path
        print(f"✓ Generated storage label: {label_path}")
        
        # Label for icons if generated
        if with_cutout_icons and 'icons' in output_files:
            icons_label_path = create_companion_label(
                main_pdf_path=output_files['icons'],
                theme_name=theme_name,
                activity_name="Sentence Icons",
                icon_path=icon_path
            )
            output_files['icons_label'] = icons_label_path
            print(f"✓ Generated storage label: {icons_label_path}")
    
    return output_files


def generate_sentence_strips_dual_mode(sentence_data, icons_data=None, theme_name='Theme',
                                       output_dir='output', include_storage_label=False,
                                       with_lanyard=True, with_cutout_icons=True,
                                       card_style=None):
    """
    Generate sentence strips in both color and black-and-white modes.
    
    Wrapper function that calls generate_sentence_strips_set() twice to create
    both color and BW versions automatically.
    
    Args:
        sentence_data: List of dicts with sentence configurations
        icons_data: Optional list of all icons to generate as cut-outs
        theme_name: Theme name for output files
        output_dir: Output directory
        include_storage_label: Generate companion storage labels (color only)
        with_lanyard: Add lanyard strip to sentence strips
        with_cutout_icons: Generate cut-out icon pages
        card_style: Optional card styling dict
        
    Returns:
        dict: {'color': {...}, 'bw': {...}} with paths to generated PDFs
    """
    results = {}
    
    # Generate color version
    print("Generating COLOR version...")
    results['color'] = generate_sentence_strips_set(
        sentence_data=sentence_data,
        icons_data=icons_data,
        theme_name=theme_name,
        output_dir=output_dir,
        include_storage_label=include_storage_label,
        with_lanyard=with_lanyard,
        with_cutout_icons=with_cutout_icons,
        card_style=card_style,
        mode="color"
    )
    
    # Generate black-and-white version
    print("\nGenerating BLACK-AND-WHITE version...")
    results['bw'] = generate_sentence_strips_set(
        sentence_data=sentence_data,
        icons_data=icons_data,
        theme_name=theme_name,
        output_dir=output_dir,
        include_storage_label=False,  # Storage labels only for color
        with_lanyard=with_lanyard,
        with_cutout_icons=with_cutout_icons,
        card_style=card_style,
        mode="bw"
    )
    
    return results


if __name__ == "__main__":
    print("Enhanced Sentence Strips (AAC) Generator")
    print("Features:")
    print("  - Lanyard-friendly design with hole-punch indicators")
    print("  - Icons match exact size of matching cards (interchangeable)")
    print("  - Cut-out icon pages with bold outlines and grab tabs")
    print("  - Copyright footer and page numbering")
    print("\nUse generate_sentence_strips_set() to generate complete sets")
