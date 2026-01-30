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
from utils.draw_helpers import (
    scale_image_to_fit,
    draw_card_background,
    draw_page_number,
    draw_copyright_footer,
    draw_text_centered_in_rect,
    create_placeholder_image
)


def generate_stick_puppet(character_data, folder_type='images', with_grab_tab=True,
                          with_handle_strip=True, with_sentence_strip=False):
    """
    Generate a large stick puppet (12-15cm tall).
    
    Args:
        character_data: Dict with 'image' and 'label' keys
        folder_type: 'images', 'aac', or 'Colour_images'
        with_grab_tab: Include grab tab at bottom
        with_handle_strip: Include handle strip for craft stick
        with_sentence_strip: Include "I am the ___" sentence strip
    
    Returns:
        PIL Image of stick puppet page
    """
    # Page setup
    page = Image.new('RGB', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), 'white')
    draw = ImageDraw.Draw(page)
    
    # Puppet dimensions (12-15cm = 1417-1772px at 300 DPI, use 1500px tall)
    puppet_height = 1500
    puppet_y_start = 300  # Start position from top
    
    # Load character image
    img_path = character_data.get('image', '')
    label = character_data.get('label', 'Character')
    
    try:
        char_img = load_image(img_path, folder_type)
    except:
        char_img = create_placeholder_image(500, 500, label)
    
    # Scale image to fit puppet height while maintaining aspect ratio
    aspect_ratio = char_img.width / char_img.height
    puppet_width = int(puppet_height * aspect_ratio)
    
    # Ensure puppet fits on page width
    max_width = int(PAGE_WIDTH - 2 * MARGINS['page'])
    if puppet_width > max_width:
        puppet_width = max_width
        puppet_height = int(puppet_width / aspect_ratio)
    
    char_img = char_img.resize((puppet_width, puppet_height), Image.Resampling.LANCZOS)
    
    # Center puppet horizontally
    puppet_x = int((PAGE_WIDTH - puppet_width) / 2)
    
    # Paste character image
    page.paste(char_img, (puppet_x, puppet_y_start), char_img if char_img.mode == 'RGBA' else None)
    
    current_y = puppet_y_start + puppet_height + 20
    
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
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
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
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        draw.text((strip_x + strip_width//2, current_y + strip_height//2), 
                  'Glue\nto\nstick', fill='black', font=font, anchor='mm', align='center')
        
        current_y += strip_height + 20
    
    # Add sentence strip (if requested)
    if with_sentence_strip:
        sentence = f"I am the {label}"
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 32)
        
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


def generate_finger_puppet(character_data, folder_type='images', with_fold_tab=True):
    """
    Generate a small finger puppet (5-6cm tall).
    
    Args:
        character_data: Dict with 'image' and 'label' keys
        folder_type: 'images', 'aac', or 'Colour_images'
        with_fold_tab: Include fold-over tab for finger
    
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
    except:
        char_img = create_placeholder_image(300, 300, label)
    
    # Scale image
    aspect_ratio = char_img.width / char_img.height
    puppet_width = int(puppet_height * aspect_ratio)
    char_img = char_img.resize((puppet_width, puppet_height), Image.Resampling.LANCZOS)
    
    # Create puppet image with space for tab
    tab_height = 100 if with_fold_tab else 0
    total_height = puppet_height + tab_height
    
    puppet_img = Image.new('RGB', (puppet_width + 20, total_height + 20), 'white')
    draw = ImageDraw.Draw(puppet_img)
    
    # Paste character
    puppet_img.paste(char_img, (10, 10), char_img if char_img.mode == 'RGBA' else None)
    
    # Draw border around character
    draw.rectangle([(10, 10), (10 + puppet_width, 10 + puppet_height)], 
                   outline='black', width=2)
    
    # Add fold tab if requested
    if with_fold_tab:
        tab_y = 10 + puppet_height
        draw.rectangle([(10, tab_y), (10 + puppet_width, tab_y + tab_height)],
                       outline='black', fill='white', width=2)
        
        # Add "Fold here" text
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
        draw.text((10 + puppet_width//2, tab_y + tab_height//2), 
                  'Fold here', fill='black', font=font, anchor='mm')
    
    return puppet_img


def generate_velcro_character_card(character_data, folder_type='images', 
                                   with_bold_outline=True, with_grab_tab=True):
    """
    Generate a velcro character card (matching card size).
    
    Args:
        character_data: Dict with 'image' and 'label' keys
        folder_type: 'images', 'aac', or 'Colour_images'
        with_bold_outline: Add bold outline for visibility
        with_grab_tab: Include grab tab
    
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
    except:
        char_img = create_placeholder_image(card_size, card_size, label)
    
    # Calculate card dimensions with optional grab tab
    tab_height = 30 if with_grab_tab else 0
    card_height = card_size + 60 + tab_height  # 60 for label area
    card_width = card_size + 10  # Small padding
    
    # Create card
    card = Image.new('RGB', (card_width, card_height), 'white')
    draw = ImageDraw.Draw(card)
    
    # Scale and paste character image
    scaled_img, pos_x, pos_y = scale_image_to_fit(char_img, (5, 5, card_size + 5, card_size + 5), padding=5)
    card.paste(scaled_img, (int(pos_x), int(pos_y)), scaled_img if scaled_img.mode == 'RGBA' else None)
    
    # Draw border
    border_width = 3 if with_bold_outline else 1
    draw.rectangle([(5, 5), (card_size + 5, card_size + 5)], 
                   outline='black', width=border_width)
    
    # Add label
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
    label_y = card_size + 15
    draw.text((card_width//2, label_y + 20), label, fill='black', font=font, anchor='mm')
    
    # Add grab tab if requested
    if with_grab_tab:
        tab_y = card_size + 60
        tab_x = (card_width - 80) // 2
        
        draw.rectangle([(tab_x, tab_y), (tab_x + 80, tab_y + 30)],
                       outline='black', width=2)
        
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
        draw.text((tab_x + 40, tab_y + 15), '✂', fill='black', font=font_small, anchor='mm')
    
    return card


def generate_story_mat(num_zones=4, with_wh_prompts=True):
    """
    Generate a story mat with placement zones.
    
    Args:
        num_zones: Number of placement zones (3-6)
        with_wh_prompts: Include WH question prompts
    
    Returns:
        PIL Image of story mat page
    """
    page = Image.new('RGB', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), 'white')
    draw = ImageDraw.Draw(page)
    
    # Title
    font_title = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 48)
    draw.text((PAGE_WIDTH//2, 150), 'Story Mat', fill='black', font=font_title, anchor='mm')
    
    # Calculate zone layout
    zones_per_row = 2
    num_rows = (num_zones + 1) // 2
    
    zone_width = 800
    zone_height = 600
    spacing = 100
    
    start_x = int((PAGE_WIDTH - (2 * zone_width + spacing)) / 2)
    start_y = 400
    
    font_label = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28)
    font_prompt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    
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


def generate_lanyard_character(character_data, folder_type='images'):
    """
    Generate a small lanyard-friendly character icon.
    
    Args:
        character_data: Dict with 'image' and 'label' keys
        folder_type: 'images', 'aac', or 'Colour_images'
    
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
    
    # Scale and paste character image
    img_x = lanyard_strip_width + 10
    img_y = 10
    scaled_img, pos_x, pos_y = scale_image_to_fit(
        char_img, 
        (img_x, img_y, img_x + card_size, img_y + card_size), 
        padding=5
    )
    card.paste(scaled_img, (int(pos_x), int(pos_y)), 
               scaled_img if scaled_img.mode == 'RGBA' else None)
    
    # Draw border around image
    draw.rectangle([(img_x, img_y), (img_x + card_size, img_y + card_size)],
                   outline='black', width=2)
    
    # Add label
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
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
                                   folder_type='images'):
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
    
    Returns:
        Dict with paths to all generated files
    """
    os.makedirs(output_dir, exist_ok=True)
    output_files = {}
    
    # Generate stick puppets
    if include_stick_puppets:
        stick_pages = []
        for char in characters:
            page = generate_stick_puppet(char, folder_type=folder_type)
            
            # Add page number and copyright
            draw = ImageDraw.Draw(page)
            draw_page_number(draw, len(stick_pages) + 1, len(characters), 
                            PAGE_WIDTH, PAGE_HEIGHT)
            draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
            
            stick_pages.append(page)
        
        stick_path = os.path.join(output_dir, f'{theme_name}_Stick_Puppets.pdf')
        save_images_as_pdf(stick_pages, stick_path)
        output_files['stick_puppets'] = stick_path
        
        # Storage label
        if include_storage_label:
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
            puppet_img = generate_finger_puppet(char, folder_type=folder_type)
            page_puppets.append(puppet_img)
            
            if len(page_puppets) == puppets_per_page or i == len(characters) - 1:
                # Create page
                page = Image.new('RGB', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), 'white')
                
                # Arrange puppets in row
                spacing = 50
                total_width = sum(p.width for p in page_puppets) + spacing * (len(page_puppets) - 1)
                start_x = int((PAGE_WIDTH - total_width) / 2)
                y_pos = 400
                
                x_pos = start_x
                for puppet in page_puppets:
                    page.paste(puppet, (x_pos, y_pos))
                    x_pos += puppet.width + spacing
                
                # Add page elements
                draw = ImageDraw.Draw(page)
                draw_page_number(draw, len(finger_pages) + 1, 
                                (len(characters) + puppets_per_page - 1) // puppets_per_page,
                                PAGE_WIDTH, PAGE_HEIGHT)
                draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
                
                finger_pages.append(page)
                page_puppets = []
        
        finger_path = os.path.join(output_dir, f'{theme_name}_Finger_Puppets.pdf')
        save_images_as_pdf(finger_pages, finger_path)
        output_files['finger_puppets'] = finger_path
        
        # Storage label
        if include_storage_label:
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
            card_img = generate_velcro_character_card(char, folder_type=folder_type)
            page_cards.append(card_img)
            
            if len(page_cards) == cards_per_page or i == len(characters) - 1:
                # Create page with 2×3 grid
                page = Image.new('RGB', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), 'white')
                
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
                
                # Add page elements
                draw = ImageDraw.Draw(page)
                draw_page_number(draw, len(velcro_pages) + 1,
                                (len(characters) + cards_per_page - 1) // cards_per_page,
                                PAGE_WIDTH, PAGE_HEIGHT)
                draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
                
                velcro_pages.append(page)
                page_cards = []
        
        velcro_path = os.path.join(output_dir, f'{theme_name}_Velcro_Character_Cards.pdf')
        save_images_as_pdf(velcro_pages, velcro_path)
        output_files['velcro_cards'] = velcro_path
        
        # Storage label
        if include_storage_label:
            label_path = create_companion_label(
                velcro_path, theme_name, "Velcro Character Cards", output_dir=output_dir
            )
            output_files['velcro_cards_label'] = label_path
    
    # Generate story mat
    if include_story_mat:
        num_zones = min(len(characters), 6)
        mat_page = generate_story_mat(num_zones=num_zones, with_wh_prompts=True)
        
        # Add page elements
        draw = ImageDraw.Draw(mat_page)
        draw_page_number(draw, 1, 1, PAGE_WIDTH, PAGE_HEIGHT)
        draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
        
        mat_path = os.path.join(output_dir, f'{theme_name}_Story_Mat.pdf')
        save_images_as_pdf([mat_page], mat_path)
        output_files['story_mat'] = mat_path
        
        # Storage label
        if include_storage_label:
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
            card_img = generate_lanyard_character(char, folder_type=folder_type)
            page_cards.append(card_img)
            
            if len(page_cards) == cards_per_page or i == len(characters) - 1:
                # Create page
                page = Image.new('RGB', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), 'white')
                
                # Arrange cards vertically
                spacing = 100
                total_height = sum(c.height for c in page_cards) + spacing * (len(page_cards) - 1)
                start_y = int((PAGE_HEIGHT - total_height) / 2)
                
                y_pos = start_y
                for card in page_cards:
                    x_pos = int((PAGE_WIDTH - card.width) / 2)
                    page.paste(card, (x_pos, y_pos))
                    y_pos += card.height + spacing
                
                # Add page elements
                draw = ImageDraw.Draw(page)
                draw_page_number(draw, len(lanyard_pages) + 1,
                                (len(characters) + cards_per_page - 1) // cards_per_page,
                                PAGE_WIDTH, PAGE_HEIGHT)
                draw_copyright_footer(draw, PAGE_WIDTH, PAGE_HEIGHT)
                
                lanyard_pages.append(page)
                page_cards = []
        
        lanyard_path = os.path.join(output_dir, f'{theme_name}_Lanyard_Characters.pdf')
        save_images_as_pdf(lanyard_pages, lanyard_path)
        output_files['lanyard'] = lanyard_path
        
        # Storage label
        if include_storage_label:
            label_path = create_companion_label(
                lanyard_path, theme_name, "Lanyard Characters", output_dir=output_dir
            )
            output_files['lanyard_label'] = label_path
    
    return output_files


# Export main function
__all__ = ['generate_puppet_characters_set']
