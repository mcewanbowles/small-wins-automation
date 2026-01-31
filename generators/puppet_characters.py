"""
Puppet Characters Generator

Generates various types of puppet resources for dramatic play and story retelling:
- Stick puppets (large, 12-15cm tall)
- Finger puppets (small, 5-6cm tall)
- Velcro character cards (matching card size)
- Story mat with placement zones
- Lanyard-friendly character icons

All resources include SPED-compliant design with high contrast, clear labels,
copyright footers, and page numbering.
"""

from PIL import Image, ImageDraw, ImageFont
import os
from utils.config import DPI, PAGE_WIDTH, PAGE_HEIGHT, MARGINS, COLORS, CARD_SIZES
from utils.image_loader import load_image
from utils.pdf_export import save_images_as_pdf
from utils.storage_label_helper import create_companion_label
from utils.layout import create_page_canvas, add_footer
from utils.image_utils import scale_image_proportional, center_image_in_box
from utils.color_helpers import image_to_grayscale
from utils.fonts import get_font
from utils.draw_helpers import (
    draw_card_background,
    draw_text_centered_in_rect,
    create_placeholder_image
)


def generate_stick_puppet(character_data, folder_type='images', with_grab_tab=True,
                          with_handle_strip=True, with_sentence_strip=False, mode='color'):
    """
    Generate a large stick puppet (12-15cm tall).
    
    Args:
        character_data: Dict with 'image' and 'label' keys
        folder_type: 'images', 'aac', or 'Colour_images'
        with_grab_tab: Include grab tab at bottom
        with_handle_strip: Include handle strip for craft stick
        with_sentence_strip: Include "I am the ___" sentence strip
        mode: 'color' or 'bw' for output mode
    
    Returns:
        PIL Image of stick puppet page
    """
    # Page setup using modern layout utility
    page = create_page_canvas(mode=mode)
    draw = ImageDraw.Draw(page)
    
    # Puppet dimensions (12-15cm = 1417-1772px at 300 DPI, use 1500px tall)
    puppet_height = 1500
    puppet_y_start = 300  # Start position from top
    
    # Load character image
    img_path = character_data.get('image', '')
    label = character_data.get('label', 'Character')
    
    try:
        char_img = load_image(img_path, folder_type)
        # Convert to grayscale if BW mode
        if mode == 'bw':
            char_img = image_to_grayscale(char_img)
    except:
        char_img = create_placeholder_image(500, 500, label)
    
    # Scale image proportionally and center
    scaled_img = scale_image_proportional(char_img, None, puppet_height)
    
    # Ensure puppet fits on page width
    max_width = int(PAGE_WIDTH - 2 * MARGINS['page'])
    if scaled_img.width > max_width:
        scaled_img = scale_image_proportional(char_img, max_width, None)
    
    # Center puppet horizontally and vertically in the allocated space
    centered_img = center_image_in_box(scaled_img, int(PAGE_WIDTH), puppet_height)
    puppet_x = int((PAGE_WIDTH - scaled_img.width) / 2)
    
    # Paste character image
    if char_img.mode == 'RGBA':
        page.paste(centered_img, (puppet_x, puppet_y_start), centered_img)
    else:
        page.paste(centered_img, (puppet_x, puppet_y_start))
    
    current_y = puppet_y_start + scaled_img.height + 20
    
    # Add grab tab at bottom (if requested)
    if with_grab_tab:
        tab_width = 100
        tab_height = 40
        tab_x = int((PAGE_WIDTH - tab_width) / 2)
        
        # Draw tab
        draw.rectangle(
            [(tab_x, current_y), (tab_x + tab_width, current_y + tab_height)],
            outline='black',
            width=3
        )
        
        # Draw scissors symbol
        font = get_font('body', 24)
        draw.text((tab_x + tab_width//2, current_y + tab_height//2), '✂', 
                  fill='black', font=font, anchor='mm')
        
        current_y += tab_height + 20
    
    # Add handle strip (if requested)
    if with_handle_strip:
        strip_width = 80
        strip_height = 400
        strip_x = int((PAGE_WIDTH - strip_width) / 2)
        
        # Draw handle strip
        draw.rectangle(
            [(strip_x, current_y), (strip_x + strip_width, current_y + strip_height)],
            outline='black',
            fill='white',
            width=3
        )
        
        # Add text "Glue to stick"
        font = get_font('body', 16)
        draw.text((strip_x + strip_width//2, current_y + strip_height//2), 
                  'Glue\nto\nstick', fill='black', font=font, anchor='mm', align='center')
        
        current_y += strip_height + 20
    
    # Add sentence strip (if requested)
    if with_sentence_strip:
        sentence = f"I am the {label}"
        font = get_font('heading', 32)
        
        # Calculate text size
        bbox = draw.textbbox((0, 0), sentence, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Draw text box
        box_padding = 20
        box_width = text_width + 2 * box_padding
        box_height = text_height + 2 * box_padding
        box_x = int((PAGE_WIDTH - box_width) / 2)
        
        draw.rectangle(
            [(box_x, current_y), (box_x + box_width, current_y + box_height)],
            outline='black',
            fill='white',
            width=2
        )
        
        draw.text((box_x + box_width//2, current_y + box_height//2), 
                  sentence, fill='black', font=font, anchor='mm')
    
    return page


def generate_finger_puppet(character_data, folder_type='images', with_fold_tab=True, mode='color'):
    """
    Generate a small finger puppet (5-6cm tall).
    
    Args:
        character_data: Dict with 'image' and 'label' keys
        folder_type: 'images', 'aac', or 'Colour_images'
        with_fold_tab: Include fold-over tab for finger
        mode: 'color' or 'bw' for output mode
    
    Returns:
        PIL Image of finger puppet
    """
    # Finger puppet dimensions (5-6cm = 591-709px at 300 DPI, use 650px tall)
    puppet_height = 650
    
    # Load character image
    img_path = character_data.get('image', '')
    label = character_data.get('label', 'Character')
    
    try:
        char_img = load_image(img_path, folder_type)
        # Convert to grayscale if BW mode
        if mode == 'bw':
            char_img = image_to_grayscale(char_img)
    except:
        char_img = create_placeholder_image(300, 300, label)
    
    # Scale image proportionally
    scaled_img = scale_image_proportional(char_img, None, puppet_height)
    puppet_width = scaled_img.width
    
    # Create puppet image with space for tab
    tab_height = 100 if with_fold_tab else 0
    total_height = puppet_height + tab_height
    
    puppet_img = Image.new('RGB', (puppet_width + 20, total_height + 20), 'white')
    draw = ImageDraw.Draw(puppet_img)
    
    # Paste character
    if scaled_img.mode == 'RGBA':
        puppet_img.paste(scaled_img, (10, 10), scaled_img)
    else:
        puppet_img.paste(scaled_img, (10, 10))
    
    # Draw border around character
    draw.rectangle([(10, 10), (10 + puppet_width, 10 + puppet_height)], 
                   outline='black', width=2)
    
    # Add fold tab if requested
    if with_fold_tab:
        tab_y = 10 + puppet_height
        draw.rectangle([(10, tab_y), (10 + puppet_width, tab_y + tab_height)],
                       outline='black', fill='white', width=2)
        
        # Add "Fold here" text
        font = get_font('body', 14)
        draw.text((10 + puppet_width//2, tab_y + tab_height//2), 
                  'Fold here', fill='black', font=font, anchor='mm')
    
    return puppet_img


def generate_velcro_character_card(character_data, folder_type='images', 
                                   with_bold_outline=True, with_grab_tab=True, mode='color'):
    """
    Generate a velcro character card (matching card size).
    
    Args:
        character_data: Dict with 'image' and 'label' keys
        folder_type: 'images', 'aac', or 'Colour_images'
        with_bold_outline: Add bold outline for visibility
        with_grab_tab: Include grab tab
        mode: 'color' or 'bw' for output mode
    
    Returns:
        PIL Image of character card
    """
    # Use standard card size
    card_size = CARD_SIZES['standard'][0]  # 750px
    
    # Load character image
    img_path = character_data.get('image', '')
    label = character_data.get('label', 'Character')
    
    try:
        char_img = load_image(img_path, folder_type)
        # Convert to grayscale if BW mode
        if mode == 'bw':
            char_img = image_to_grayscale(char_img)
    except:
        char_img = create_placeholder_image(card_size, card_size, label)
    
    # Calculate card dimensions with optional grab tab
    tab_height = 30 if with_grab_tab else 0
    card_height = card_size + 60 + tab_height  # 60 for label area
    card_width = card_size + 10  # Small padding
    
    # Create card
    card = Image.new('RGB', (card_width, card_height), 'white')
    draw = ImageDraw.Draw(card)
    
    # Scale and center image in card
    scaled_img = scale_image_proportional(char_img, card_size - 10, card_size - 10)
    centered_img = center_image_in_box(scaled_img, card_size, card_size)
    
    # Paste scaled image
    img_x = 5 + (card_size - scaled_img.width) // 2
    img_y = 5 + (card_size - scaled_img.height) // 2
    if scaled_img.mode == 'RGBA':
        card.paste(centered_img, (img_x, img_y), centered_img)
    else:
        card.paste(centered_img, (img_x, img_y))
    
    # Draw border
    border_width = 3 if with_bold_outline else 1
    draw.rectangle([(5, 5), (card_size + 5, card_size + 5)], 
                   outline='black', width=border_width)
    
    # Add label
    font = get_font('heading', 24)
    label_y = card_size + 15
    draw.text((card_width//2, label_y + 20), label, fill='black', font=font, anchor='mm')
    
    # Add grab tab if requested
    if with_grab_tab:
        tab_y = card_size + 60
        tab_x = (card_width - 80) // 2
        
        draw.rectangle([(tab_x, tab_y), (tab_x + 80, tab_y + 30)],
                       outline='black', width=2)
        
        font_small = get_font('body', 20)
        draw.text((tab_x + 40, tab_y + 15), '✂', fill='black', font=font_small, anchor='mm')
    
    return card


def generate_story_mat(num_zones=4, with_wh_prompts=True, mode='color'):
    """
    Generate a story mat with placement zones.
    
    Args:
        num_zones: Number of placement zones (3-6)
        with_wh_prompts: Include WH question prompts
        mode: 'color' or 'bw' for output mode
    
    Returns:
        PIL Image of story mat page
    """
    page = create_page_canvas(mode=mode)
    draw = ImageDraw.Draw(page)
    
    # Title
    font_title = get_font('heading', 48)
    draw.text((PAGE_WIDTH//2, 150), 'Story Mat', fill='black', font=font_title, anchor='mm')
    
    # Calculate zone layout
    zones_per_row = 2
    num_rows = (num_zones + 1) // 2
    
    zone_width = 800
    zone_height = 600
    spacing = 100
    
    start_x = int((PAGE_WIDTH - (2 * zone_width + spacing)) / 2)
    start_y = 400
    
    font_label = get_font('heading', 28)
    font_prompt = get_font('body', 20)
    
    prompts = [
        "Who is here?",
        "Where is the ___?",
        "What happens next?",
        "Who comes next?",
        "What do they do?",
        "How does it end?"
    ]
    
    for i in range(num_zones):
        row = i // zones_per_row
        col = i % zones_per_row
        
        x = start_x + col * (zone_width + spacing)
        y = start_y + row * (zone_height + spacing + 60)
        
        # Draw zone box
        draw.rectangle([(x, y), (x + zone_width, y + zone_height)],
                       outline='black', fill=(240, 240, 240), width=4)
        
        # Add zone number
        draw.text((x + zone_width//2, y + zone_height//2), 
                  f"Zone {i+1}", fill=(150, 150, 150), font=font_label, anchor='mm')
        
        # Add WH prompt if requested
        if with_wh_prompts and i < len(prompts):
            draw.text((x + zone_width//2, y + zone_height + 30),
                      prompts[i], fill='black', font=font_prompt, anchor='mm')
    
    return page


def generate_lanyard_character(character_data, folder_type='images', mode='color'):
    """
    Generate a small lanyard-friendly character icon.
    
    Args:
        character_data: Dict with 'image' and 'label' keys
        folder_type: 'images', 'aac', or 'Colour_images'
        mode: 'color' or 'bw' for output mode
    
    Returns:
        PIL Image of lanyard character card
    """
    # Lanyard card size (smaller than standard)
    card_size = 500
    lanyard_strip_width = 150
    
    # Load character image
    img_path = character_data.get('image', '')
    label = character_data.get('label', 'Character')
    
    try:
        char_img = load_image(img_path, folder_type)
        # Convert to grayscale if BW mode
        if mode == 'bw':
            char_img = image_to_grayscale(char_img)
    except:
        char_img = create_placeholder_image(card_size, card_size, label)
    
    # Create card with lanyard strip
    total_width = lanyard_strip_width + card_size + 20
    card_height = card_size + 80  # Extra for label
    
    card = Image.new('RGB', (total_width, card_height), 'white')
    draw = ImageDraw.Draw(card)
    
    # Draw lanyard strip
    draw.rectangle([(0, 0), (lanyard_strip_width, card_height)],
                   outline='black', fill='white', width=5)
    
    # Draw hole-punch indicator
    hole_x = lanyard_strip_width // 2
    hole_y = 50
    hole_radius = 15
    
    # Draw reinforcement circles
    for r in [hole_radius, hole_radius + 5, hole_radius + 10]:
        draw.ellipse([(hole_x - r, hole_y - r), (hole_x + r, hole_y + r)],
                     outline='black', width=2)
    
    # Fill innermost circle
    draw.ellipse([(hole_x - hole_radius, hole_y - hole_radius), 
                  (hole_x + hole_radius, hole_y + hole_radius)],
                 fill='white', outline='black', width=2)
    
    # Draw vertical separator
    draw.line([(lanyard_strip_width, 0), (lanyard_strip_width, card_height)],
              fill='black', width=3)
    
    # Scale and center image in card
    img_x = lanyard_strip_width + 10
    img_y = 10
    scaled_img = scale_image_proportional(char_img, card_size - 10, card_size - 10)
    centered_img = center_image_in_box(scaled_img, card_size, card_size)
    
    # Paste scaled image
    paste_x = img_x + (card_size - scaled_img.width) // 2
    paste_y = img_y + (card_size - scaled_img.height) // 2
    if scaled_img.mode == 'RGBA':
        card.paste(centered_img, (paste_x, paste_y), centered_img)
    else:
        card.paste(centered_img, (paste_x, paste_y))
    
    # Draw border around image
    draw.rectangle([(img_x, img_y), (img_x + card_size, img_y + card_size)],
                   outline='black', width=2)
    
    # Add label
    font = get_font('heading', 20)
    label_y = img_y + card_size + 20
    draw.text((img_x + card_size//2, label_y), label, fill='black', font=font, anchor='mm')
    
    return card


def generate_puppet_characters_set(characters, theme_name, output_dir='output',
                                   include_stick_puppets=True,
                                   include_finger_puppets=True,
                                   include_velcro_cards=True,
                                   include_story_mat=False,
                                   include_lanyard=True,
                                   include_storage_label=True,
                                   folder_type='images',
                                   mode='color'):
    """
    Generate complete puppet characters set.
    
    Args:
        characters: List of character dicts with 'image' and 'label'
        theme_name: Name of the theme for file naming
        output_dir: Output directory path
        include_stick_puppets: Generate stick puppet pages
        include_finger_puppets: Generate finger puppet pages
        include_velcro_cards: Generate velcro character cards
        include_story_mat: Generate story mat page
        include_lanyard: Generate lanyard character cards
        include_storage_label: Generate storage labels
        folder_type: Image folder type
        mode: 'color' or 'bw' for output mode
    
    Returns:
        Dict with paths to all generated files
    """
    os.makedirs(output_dir, exist_ok=True)
    output_files = {}
    
    # Determine file suffix based on mode
    mode_suffix = f"_{mode}" if mode != 'color' else ""
    
    # Generate stick puppets
    if include_stick_puppets:
        stick_pages = []
        for char in characters:
            page = generate_stick_puppet(char, folder_type=folder_type, mode=mode)
            
            # Add footer with page number
            add_footer(page, f"Stick Puppets - {char.get('label', 'Character')}", 
                      page_num=len(stick_pages) + 1, total_pages=len(characters), mode=mode)
            
            stick_pages.append(page)
        
        stick_path = os.path.join(output_dir, f'{theme_name}_Stick_Puppets{mode_suffix}.pdf')
        save_images_as_pdf(stick_pages, stick_path)
        output_files['stick_puppets'] = stick_path
        
        # Storage label
        if include_storage_label and mode == 'color':
            label_path = create_companion_label(
                stick_path, theme_name, "Stick Puppets", output_dir=output_dir
            )
            output_files['stick_puppets_label'] = label_path
    
    # Generate finger puppets (2-3 per page)
    if include_finger_puppets:
        finger_pages = []
        puppets_per_page = 3
        
        page_puppets = []
        for i, char in enumerate(characters):
            puppet_img = generate_finger_puppet(char, folder_type=folder_type, mode=mode)
            page_puppets.append(puppet_img)
            
            if len(page_puppets) == puppets_per_page or i == len(characters) - 1:
                # Create page
                page = create_page_canvas(mode=mode)
                
                # Arrange puppets in row
                spacing = 50
                total_width = sum(p.width for p in page_puppets) + spacing * (len(page_puppets) - 1)
                start_x = int((PAGE_WIDTH - total_width) / 2)
                y_pos = 400
                
                x_pos = start_x
                for puppet in page_puppets:
                    page.paste(puppet, (x_pos, y_pos))
                    x_pos += puppet.width + spacing
                
                # Add footer
                add_footer(page, "Finger Puppets", 
                          page_num=len(finger_pages) + 1,
                          total_pages=(len(characters) + puppets_per_page - 1) // puppets_per_page,
                          mode=mode)
                
                finger_pages.append(page)
                page_puppets = []
        
        finger_path = os.path.join(output_dir, f'{theme_name}_Finger_Puppets{mode_suffix}.pdf')
        save_images_as_pdf(finger_pages, finger_path)
        output_files['finger_puppets'] = finger_path
        
        # Storage label
        if include_storage_label and mode == 'color':
            label_path = create_companion_label(
                finger_path, theme_name, "Finger Puppets", output_dir=output_dir
            )
            output_files['finger_puppets_label'] = label_path
    
    # Generate velcro character cards (6 per page, 2×3 grid)
    if include_velcro_cards:
        velcro_pages = []
        cards_per_page = 6
        
        page_cards = []
        for i, char in enumerate(characters):
            card_img = generate_velcro_character_card(char, folder_type=folder_type, mode=mode)
            page_cards.append(card_img)
            
            if len(page_cards) == cards_per_page or i == len(characters) - 1:
                # Create page with 2×3 grid
                page = create_page_canvas(mode=mode)
                
                rows = 2
                cols = 3
                spacing = 40
                
                # Calculate grid positioning
                card_width = page_cards[0].width
                card_height = page_cards[0].height
                grid_width = cols * card_width + (cols - 1) * spacing
                grid_height = rows * card_height + (rows - 1) * spacing
                
                start_x = int((PAGE_WIDTH - grid_width) / 2)
                start_y = 200
                
                for idx, card in enumerate(page_cards):
                    row = idx // cols
                    col = idx % cols
                    x = start_x + col * (card_width + spacing)
                    y = start_y + row * (card_height + spacing)
                    page.paste(card, (x, y))
                
                # Add footer
                add_footer(page, "Velcro Character Cards",
                          page_num=len(velcro_pages) + 1,
                          total_pages=(len(characters) + cards_per_page - 1) // cards_per_page,
                          mode=mode)
                
                velcro_pages.append(page)
                page_cards = []
        
        velcro_path = os.path.join(output_dir, f'{theme_name}_Velcro_Character_Cards{mode_suffix}.pdf')
        save_images_as_pdf(velcro_pages, velcro_path)
        output_files['velcro_cards'] = velcro_path
        
        # Storage label
        if include_storage_label and mode == 'color':
            label_path = create_companion_label(
                velcro_path, theme_name, "Velcro Character Cards", output_dir=output_dir
            )
            output_files['velcro_cards_label'] = label_path
    
    # Generate story mat
    if include_story_mat:
        num_zones = min(len(characters), 6)
        mat_page = generate_story_mat(num_zones=num_zones, with_wh_prompts=True, mode=mode)
        
        # Add footer
        add_footer(mat_page, "Story Mat", page_num=1, total_pages=1, mode=mode)
        
        mat_path = os.path.join(output_dir, f'{theme_name}_Story_Mat{mode_suffix}.pdf')
        save_images_as_pdf([mat_page], mat_path)
        output_files['story_mat'] = mat_path
        
        # Storage label
        if include_storage_label and mode == 'color':
            label_path = create_companion_label(
                mat_path, theme_name, "Story Mat", output_dir=output_dir
            )
            output_files['story_mat_label'] = label_path
    
    # Generate lanyard characters (3 per page)
    if include_lanyard:
        lanyard_pages = []
        cards_per_page = 3
        
        page_cards = []
        for i, char in enumerate(characters):
            card_img = generate_lanyard_character(char, folder_type=folder_type, mode=mode)
            page_cards.append(card_img)
            
            if len(page_cards) == cards_per_page or i == len(characters) - 1:
                # Create page
                page = create_page_canvas(mode=mode)
                
                # Arrange cards vertically
                spacing = 100
                total_height = sum(c.height for c in page_cards) + spacing * (len(page_cards) - 1)
                start_y = int((PAGE_HEIGHT - total_height) / 2)
                
                y_pos = start_y
                for card in page_cards:
                    x_pos = int((PAGE_WIDTH - card.width) / 2)
                    page.paste(card, (x_pos, y_pos))
                    y_pos += card.height + spacing
                
                # Add footer
                add_footer(page, "Lanyard Characters",
                          page_num=len(lanyard_pages) + 1,
                          total_pages=(len(characters) + cards_per_page - 1) // cards_per_page,
                          mode=mode)
                
                lanyard_pages.append(page)
                page_cards = []
        
        lanyard_path = os.path.join(output_dir, f'{theme_name}_Lanyard_Characters{mode_suffix}.pdf')
        save_images_as_pdf(lanyard_pages, lanyard_path)
        output_files['lanyard'] = lanyard_path
        
        # Storage label
        if include_storage_label and mode == 'color':
            label_path = create_companion_label(
                lanyard_path, theme_name, "Lanyard Characters", output_dir=output_dir
            )
            output_files['lanyard_label'] = label_path
    
    return output_files


def generate_puppet_characters_dual_mode(characters, theme_name, output_dir='output',
                                         include_stick_puppets=True,
                                         include_finger_puppets=True,
                                         include_velcro_cards=True,
                                         include_story_mat=False,
                                         include_lanyard=True,
                                         include_storage_label=True,
                                         folder_type='images'):
    """
    Generate complete puppet characters set in BOTH color and black-and-white modes.
    
    Args:
        characters: List of character dicts with 'image' and 'label'
        theme_name: Name of the theme for file naming
        output_dir: Output directory path
        include_stick_puppets: Generate stick puppet pages
        include_finger_puppets: Generate finger puppet pages
        include_velcro_cards: Generate velcro character cards
        include_story_mat: Generate story mat page
        include_lanyard: Generate lanyard character cards
        include_storage_label: Generate storage labels
        folder_type: Image folder type
    
    Returns:
        Dict with 'color' and 'bw' keys, each containing paths to generated files
    """
    results = {}
    
    # Generate color version
    results['color'] = generate_puppet_characters_set(
        characters, theme_name, output_dir,
        include_stick_puppets=include_stick_puppets,
        include_finger_puppets=include_finger_puppets,
        include_velcro_cards=include_velcro_cards,
        include_story_mat=include_story_mat,
        include_lanyard=include_lanyard,
        include_storage_label=include_storage_label,
        folder_type=folder_type,
        mode='color'
    )
    
    # Generate black-and-white version
    results['bw'] = generate_puppet_characters_set(
        characters, theme_name, output_dir,
        include_stick_puppets=include_stick_puppets,
        include_finger_puppets=include_finger_puppets,
        include_velcro_cards=include_velcro_cards,
        include_story_mat=include_story_mat,
        include_lanyard=include_lanyard,
        include_storage_label=False,  # Only generate labels for color version
        folder_type=folder_type,
        mode='bw'
    )
    
    return results


# Export main functions
__all__ = ['generate_puppet_characters_set', 'generate_puppet_characters_dual_mode']
