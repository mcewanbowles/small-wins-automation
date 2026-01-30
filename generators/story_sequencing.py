"""
Story Sequencing Generator

Generates comprehensive story sequencing resources for comprehension and retelling.
Includes multiple page types:
- First → Next → Last (3-box layout with differentiation levels)
- Story Map (graphic organizer)
- Event Ordering (3-step and 4-step sequences)
- Retell Strips (lanyard-friendly)
- Story Summary (sentence starters)
- Cut-out icon pages

All icons match the exact size of matching cards for interchangeability.
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont
from utils.config import DPI, PAGE_WIDTH, PAGE_HEIGHT, MARGINS, CARD_SIZES, FONT_SIZES, COLORS
from utils.image_loader import get_image_loader
from utils.layout import create_page_canvas, add_page_border
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
from utils.storage_label_helper import create_companion_label


def generate_first_next_last_page(event_items, level=1, page_number=1, total_pages=1,
                                   card_style=None):
    """
    Generate a First → Next → Last page with 3-box layout.
    
    Args:
        event_items: List of 3 dicts with 'image' and 'label' keys
        level: 1=errorless (correct order), 2=mixed (scrambled), 3=cut-and-paste (empty boxes)
        page_number: Current page number
        total_pages: Total pages for numbering
        card_style: Optional dict with border_width, corner_radius, shadow
        
    Returns:
        PIL.Image: Generated page
    """
    # Create page
    page = create_page_canvas()
    draw = ImageDraw.Draw(page)
    add_page_border(page)
    
    # Default card style
    if card_style is None:
        card_style = {'border_width': 2, 'corner_radius': 10, 'shadow': False}
    
    # Constants
    box_width = 700
    box_height = 900
    label_height = 80
    spacing = 100
    
    # Calculate positions (3 boxes horizontally)
    total_width = 3 * box_width + 2 * spacing
    start_x = (PAGE_WIDTH - total_width) // 2
    start_y = MARGINS['page'] + 150
    
    # Labels
    labels = ["First", "Next", "Last"]
    font_mgr = get_font_manager()
    title_font = font_mgr.get_font('heading', FONT_SIZES['heading'])
    label_font = font_mgr.get_font('body', FONT_SIZES['large'])
    
    # Title
    title_text = "Story Sequence"
    if level == 1:
        title_text += " (Correct Order)"
    elif level == 2:
        title_text += " (Mixed Order)"
    elif level == 3:
        title_text += " (Cut and Paste)"
    
    draw_text_centered_in_rect(draw, (0, MARGINS['page'], PAGE_WIDTH, MARGINS['page'] + 100),
                               title_text, title_font, COLORS['black'])
    
    # Prepare event items based on level
    if level == 1:
        # Errorless: correct order
        display_items = event_items[:3]
    elif level == 2:
        # Mixed: scrambled order
        display_items = event_items[:3].copy()
        random.shuffle(display_items)
    else:
        # Cut-and-paste: empty boxes
        display_items = [None, None, None]
    
    # Get image loader
    img_loader = get_image_loader()
    
    # Draw 3 boxes
    for i, label in enumerate(labels):
        box_x = start_x + i * (box_width + spacing)
        box_y = start_y + label_height
        
        # Draw label above box
        label_rect = (box_x, start_y, box_x + box_width, start_y + label_height)
        draw.rectangle(label_rect, fill=COLORS['light_gray'], outline=COLORS['black'], width=3)
        draw_text_centered_in_rect(draw, label_rect, label, label_font, COLORS['black'])
        
        # Draw box with card background
        box_rect = (box_x, box_y, box_x + box_width, box_y + box_height)
        draw_card_background(draw, box_rect, card_style)
        
        # Draw icon if not cut-and-paste
        if display_items[i] is not None:
            item = display_items[i]
            folder_type = item.get('folder_type', 'images')
            
            try:
                icon_img = img_loader.load_image(item['image'], folder_type=folder_type)
            except:
                icon_img = create_placeholder_image(600, 600, item.get('label', 'Image'))
            
            # Scale and center icon in box
            scaled_img, img_x, img_y = scale_image_to_fit(icon_img, box_rect, padding=50)
            page.paste(scaled_img, (img_x, img_y), scaled_img if scaled_img.mode == 'RGBA' else None)
            
            # Draw label below icon
            text_y = box_y + box_height - 100
            text_rect = (box_x, text_y, box_x + box_width, box_y + box_height - 20)
            draw_text_centered_in_rect(draw, text_rect, item.get('label', ''), label_font, COLORS['black'])
    
    # Add page elements
    draw_page_number(draw, page_number, total_pages)
    draw_copyright_footer(draw)
    
    return page


def generate_story_map(story_data, page_number=1, total_pages=1):
    """
    Generate a one-page story map graphic organizer.
    
    Args:
        story_data: Dict with 'characters', 'setting', 'problem', 'events', 'solution'
        page_number: Current page number
        total_pages: Total pages for numbering
        
    Returns:
        PIL.Image: Generated page
    """
    # Create page
    page = create_page_canvas()
    draw = ImageDraw.Draw(page)
    add_page_border(page)
    
    # Fonts
    font_mgr = get_font_manager()
    title_font = font_mgr.get_font('heading', FONT_SIZES['heading'])
    section_font = font_mgr.get_font('heading', FONT_SIZES['large'])
    body_font = font_mgr.get_font('body', FONT_SIZES['body'])
    
    # Title
    draw_text_centered_in_rect(draw, (0, MARGINS['page'], PAGE_WIDTH, MARGINS['page'] + 100),
                               "Story Map", title_font, COLORS['black'])
    
    # Layout sections
    section_height = 350
    section_width = (PAGE_WIDTH - 2 * MARGINS['page'] - 80) // 2
    start_y = MARGINS['page'] + 150
    
    sections = [
        ('Characters', story_data.get('characters', [])),
        ('Setting', story_data.get('setting', [])),
        ('Problem', story_data.get('problem', [])),
        ('Events', story_data.get('events', [])),
        ('Solution', story_data.get('solution', []))
    ]
    
    # Draw sections in grid
    for idx, (section_name, section_content) in enumerate(sections):
        row = idx // 2
        col = idx % 2
        
        x = MARGINS['page'] + col * (section_width + 80)
        y = start_y + row * (section_height + 40)
        
        # Section box
        box_rect = (x, y, x + section_width, y + section_height)
        draw.rectangle(box_rect, fill=COLORS['white'], outline=COLORS['black'], width=3)
        
        # Section title
        title_rect = (x, y, x + section_width, y + 60)
        draw.rectangle(title_rect, fill=COLORS['light_gray'], outline=COLORS['black'], width=3)
        draw_text_centered_in_rect(draw, title_rect, section_name, section_font, COLORS['black'])
        
        # Section content
        content_y = y + 70
        if isinstance(section_content, list):
            for item in section_content[:3]:  # Limit to 3 items
                text = item if isinstance(item, str) else item.get('label', '')
                draw.text((x + 20, content_y), text, font=body_font, fill=COLORS['black'])
                content_y += 40
        else:
            draw.text((x + 20, content_y), str(section_content), font=body_font, fill=COLORS['black'])
    
    # Add page elements
    draw_page_number(draw, page_number, total_pages)
    draw_copyright_footer(draw)
    
    return page


def generate_event_ordering_page(events, layout='horizontal', page_number=1, total_pages=1,
                                 card_style=None):
    """
    Generate event ordering page with WH prompts.
    
    Args:
        events: List of 3-4 event dicts with 'image' and 'label'
        layout: 'horizontal' or 'vertical'
        page_number: Current page number
        total_pages: Total pages for numbering
        card_style: Optional dict with border_width, corner_radius, shadow
        
    Returns:
        PIL.Image: Generated page
    """
    # Create page
    page = create_page_canvas()
    draw = ImageDraw.Draw(page)
    add_page_border(page)
    
    # Default card style
    if card_style is None:
        card_style = {'border_width': 2, 'corner_radius': 10, 'shadow': False}
    
    # Constants
    num_events = len(events)
    icon_size = 600
    
    # Fonts
    font_mgr = get_font_manager()
    title_font = font_mgr.get_font('heading', FONT_SIZES['heading'])
    prompt_font = font_mgr.get_font('body', FONT_SIZES['large'])
    
    # Title
    draw_text_centered_in_rect(draw, (0, MARGINS['page'], PAGE_WIDTH, MARGINS['page'] + 80),
                               "What Happened?", title_font, COLORS['black'])
    
    # WH prompts
    if num_events == 3:
        prompts = ["What happened first?", "What happened next?", "What happened last?"]
    else:
        prompts = ["What happened first?", "What happened next?", "Then what?", "What happened last?"]
    
    # Get image loader
    img_loader = get_image_loader()
    
    # Layout
    if layout == 'horizontal':
        # Horizontal layout
        spacing = 80
        available_width = PAGE_WIDTH - 2 * MARGINS['page'] - (num_events - 1) * spacing
        icon_size = min(icon_size, available_width // num_events)
        
        start_x = (PAGE_WIDTH - (num_events * icon_size + (num_events - 1) * spacing)) // 2
        start_y = MARGINS['page'] + 200
        
        for i, (event, prompt) in enumerate(zip(events, prompts)):
            x = start_x + i * (icon_size + spacing)
            
            # Draw prompt
            prompt_rect = (x, start_y - 100, x + icon_size, start_y - 20)
            draw_text_centered_in_rect(draw, prompt_rect, prompt, prompt_font, COLORS['black'])
            
            # Draw box
            box_rect = (x, start_y, x + icon_size, start_y + icon_size)
            draw_card_background(draw, box_rect, card_style)
            
            # Load and draw icon
            folder_type = event.get('folder_type', 'images')
            try:
                icon_img = img_loader.load_image(event['image'], folder_type=folder_type)
            except:
                icon_img = create_placeholder_image(icon_size, icon_size, event.get('label', 'Event'))
            
            scaled_img, img_x, img_y = scale_image_to_fit(icon_img, box_rect, padding=30)
            page.paste(scaled_img, (img_x, img_y), scaled_img if scaled_img.mode == 'RGBA' else None)
            
            # Draw label
            label_y = start_y + icon_size + 20
            draw.text((x, label_y), event.get('label', ''), font=prompt_font, fill=COLORS['black'])
    else:
        # Vertical layout
        start_y = MARGINS['page'] + 150
        spacing = 60
        
        for i, (event, prompt) in enumerate(zip(events, prompts)):
            y = start_y + i * (icon_size + spacing + 100)
            x = (PAGE_WIDTH - icon_size) // 2
            
            # Draw prompt
            prompt_rect = (MARGINS['page'], y, PAGE_WIDTH - MARGINS['page'], y + 60)
            draw_text_centered_in_rect(draw, prompt_rect, prompt, prompt_font, COLORS['black'])
            
            # Draw box
            box_rect = (x, y + 70, x + icon_size, y + 70 + icon_size)
            draw_card_background(draw, box_rect, card_style)
            
            # Load and draw icon
            folder_type = event.get('folder_type', 'images')
            try:
                icon_img = img_loader.load_image(event['image'], folder_type=folder_type)
            except:
                icon_img = create_placeholder_image(icon_size, icon_size, event.get('label', 'Event'))
            
            scaled_img, img_x, img_y = scale_image_to_fit(icon_img, box_rect, padding=30)
            page.paste(scaled_img, (img_x, img_y), scaled_img if scaled_img.mode == 'RGBA' else None)
    
    # Add page elements
    draw_page_number(draw, page_number, total_pages)
    draw_copyright_footer(draw)
    
    return page


def generate_retell_strip(events, with_lanyard=True, card_style=None, page_number=1, total_pages=1):
    """
    Generate retell strip with lanyard-friendly design.
    
    Args:
        events: List of 3-4 event dicts with 'image' and 'label'
        with_lanyard: Include lanyard strip with hole-punch indicator
        card_style: Optional dict with border_width, corner_radius, shadow
        page_number: Current page number
        total_pages: Total pages for numbering
        
    Returns:
        PIL.Image: Generated page
    """
    # Create page
    page = create_page_canvas()
    draw = ImageDraw.Draw(page)
    add_page_border(page)
    
    # Default card style
    if card_style is None:
        card_style = {'border_width': 2, 'corner_radius': 10, 'shadow': False}
    
    # Constants
    num_slots = len(events)
    icon_size = CARD_SIZES['standard']  # 750x750px - same as matching cards
    label_height = 60
    
    # Lanyard strip specifications
    lanyard_width = 150 if with_lanyard else 0
    
    # Calculate strip dimensions
    strip_height = icon_size + label_height + 40  # 40px padding
    strip_width = PAGE_WIDTH - 2 * MARGINS['page']
    
    # Calculate icon area
    icon_area_width = strip_width - lanyard_width - 20  # 20px separator
    icon_spacing = 20
    total_icon_width = num_slots * icon_size + (num_slots - 1) * icon_spacing
    
    # Center the icons in available space
    start_x = MARGINS['page'] + lanyard_width + 20 + (icon_area_width - total_icon_width) // 2
    start_y = (PAGE_HEIGHT - strip_height - 200) // 2  # Leave room for footer
    
    # Draw lanyard strip if enabled
    if with_lanyard:
        lanyard_x = MARGINS['page']
        lanyard_y = start_y
        
        # Draw reinforced border
        draw.rectangle(
            [(lanyard_x, lanyard_y), (lanyard_x + lanyard_width, lanyard_y + strip_height)],
            outline=COLORS['black'],
            width=5
        )
        
        # Draw hole-punch indicator (centered)
        hole_center_x = lanyard_x + lanyard_width // 2
        hole_center_y = lanyard_y + strip_height // 2
        hole_radius = 15
        
        # Draw concentric circles for reinforcement pattern
        for r in range(hole_radius, hole_radius + 15, 3):
            draw.ellipse(
                [(hole_center_x - r, hole_center_y - r),
                 (hole_center_x + r, hole_center_y + r)],
                outline=COLORS['black'],
                width=2
            )
        
        # Draw vertical separator
        draw.line(
            [(lanyard_x + lanyard_width, lanyard_y),
             (lanyard_x + lanyard_width, lanyard_y + strip_height)],
            fill=COLORS['black'],
            width=3
        )
    
    # Get image loader and fonts
    img_loader = get_image_loader()
    font_mgr = get_font_manager()
    label_font = font_mgr.get_font('body', FONT_SIZES['body'])
    
    # Draw icons
    for i, event in enumerate(events):
        icon_x = start_x + i * (icon_size + icon_spacing)
        icon_y = start_y + 20
        
        # Draw card background
        card_rect = (icon_x, icon_y, icon_x + icon_size, icon_y + icon_size)
        draw_card_background(draw, card_rect, card_style)
        
        # Load and draw icon
        folder_type = event.get('folder_type', 'images')
        try:
            icon_img = img_loader.load_image(event['image'], folder_type=folder_type)
        except:
            icon_img = create_placeholder_image(icon_size, icon_size, event.get('label', 'Event'))
        
        scaled_img, img_x, img_y = scale_image_to_fit(icon_img, card_rect, padding=5)
        page.paste(scaled_img, (img_x, img_y), scaled_img if scaled_img.mode == 'RGBA' else None)
        
        # Draw label
        label_y = icon_y + icon_size + 10
        label_rect = (icon_x, label_y, icon_x + icon_size, label_y + label_height)
        draw_text_centered_in_rect(draw, label_rect, event.get('label', ''), label_font, COLORS['black'])
    
    # Add page elements
    draw_page_number(draw, page_number, total_pages)
    draw_copyright_footer(draw)
    
    return page


def generate_story_summary_page(page_number=1, total_pages=1):
    """
    Generate story summary page with sentence starters and writing lines.
    
    Args:
        page_number: Current page number
        total_pages: Total pages for numbering
        
    Returns:
        PIL.Image: Generated page
    """
    # Create page
    page = create_page_canvas()
    draw = ImageDraw.Draw(page)
    add_page_border(page)
    
    # Fonts
    font_mgr = get_font_manager()
    title_font = font_mgr.get_font('heading', FONT_SIZES['heading'])
    starter_font = font_mgr.get_font('body', FONT_SIZES['large'])
    
    # Title
    draw_text_centered_in_rect(draw, (0, MARGINS['page'], PAGE_WIDTH, MARGINS['page'] + 100),
                               "Story Summary", title_font, COLORS['black'])
    
    # Sentence starters
    starters = [
        "The story is about...",
        "First...",
        "Then...",
        "Last..."
    ]
    
    start_y = MARGINS['page'] + 200
    line_spacing = 300
    line_width = PAGE_WIDTH - 2 * MARGINS['page'] - 100
    
    for i, starter in enumerate(starters):
        y = start_y + i * line_spacing
        
        # Draw sentence starter
        draw.text((MARGINS['page'] + 50, y), starter, font=starter_font, fill=COLORS['black'])
        
        # Draw writing lines (3 lines per starter)
        for line_num in range(3):
            line_y = y + 60 + line_num * 50
            draw.line(
                [(MARGINS['page'] + 50, line_y), (MARGINS['page'] + 50 + line_width, line_y)],
                fill=COLORS['gray'],
                width=2
            )
    
    # Add page elements
    draw_page_number(draw, page_number, total_pages)
    draw_copyright_footer(draw)
    
    return page


def generate_cutout_icons_page(icons, page_number=1, total_pages=1, with_grab_tabs=True):
    """
    Generate a page of cut-out icons in 2x3 grid.
    
    Args:
        icons: List of dicts with 'image' and 'label' keys (max 6)
        page_number: Current page number
        total_pages: Total pages for numbering
        with_grab_tabs: Add scissors grab tabs for fine motor support
        
    Returns:
        PIL.Image: Generated page
    """
    # Create page
    page = create_page_canvas()
    draw = ImageDraw.Draw(page)
    add_page_border(page)
    
    # Constants
    icon_size = CARD_SIZES['standard']  # 750x750px - same as matching cards
    rows, cols = 2, 3
    spacing = 40
    
    # Calculate grid
    total_width = cols * icon_size + (cols - 1) * spacing
    total_height = rows * icon_size + (rows - 1) * spacing
    start_x = (PAGE_WIDTH - total_width) // 2
    start_y = (PAGE_HEIGHT - total_height - 150) // 2
    
    # Get image loader and font
    img_loader = get_image_loader()
    font_mgr = get_font_manager()
    label_font = font_mgr.get_font('body', FONT_SIZES['body'])
    
    # Card style with bold outline
    card_style = {'border_width': 3, 'corner_radius': 10, 'shadow': False}
    
    # Draw icons
    for idx, icon in enumerate(icons[:6]):  # Max 6 icons
        row = idx // cols
        col = idx % cols
        
        x = start_x + col * (icon_size + spacing)
        y = start_y + row * (icon_size + spacing)
        
        # Draw card background
        card_rect = (x, y, x + icon_size, y + icon_size)
        draw_card_background(draw, card_rect, card_style)
        
        # Load and draw icon
        folder_type = icon.get('folder_type', 'images')
        try:
            icon_img = img_loader.load_image(icon['image'], folder_type=folder_type)
        except:
            icon_img = create_placeholder_image(icon_size, icon_size, icon.get('label', 'Icon'))
        
        scaled_img, img_x, img_y = scale_image_to_fit(icon_img, card_rect, padding=5)
        page.paste(scaled_img, (img_x, img_y), scaled_img if scaled_img.mode == 'RGBA' else None)
        
        # Draw grab tab if enabled
        if with_grab_tabs:
            tab_width = 80
            tab_height = 30
            tab_x = x + icon_size - tab_width - 10
            tab_y = y - tab_height
            
            # Draw tab
            draw.rectangle(
                [(tab_x, tab_y), (tab_x + tab_width, tab_y + tab_height)],
                fill=COLORS['white'],
                outline=COLORS['black'],
                width=2
            )
            
            # Draw scissors symbol
            scissors_text = "✂"
            draw_text_centered_in_rect(draw, (tab_x, tab_y, tab_x + tab_width, tab_y + tab_height),
                                      scissors_text, label_font, COLORS['black'])
    
    # Add page elements
    draw_page_number(draw, page_number, total_pages)
    draw_copyright_footer(draw)
    
    return page


def generate_story_sequencing_set(story_data, theme_name, output_dir='output',
                                  include_storage_label=True):
    """
    Generate complete story sequencing resource set.
    
    Args:
        story_data: Dict with:
            - 'events': List of event dicts (3-4 items)
            - 'characters': List for story map
            - 'setting': List/str for story map
            - 'problem': str for story map
            - 'solution': str for story map
        theme_name: Theme name for file naming
        output_dir: Output directory path
        include_storage_label: Generate storage labels
        
    Returns:
        Dict with paths to generated PDFs
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract events
    events = story_data.get('events', [])
    if len(events) < 3:
        raise ValueError("Story must have at least 3 events")
    
    # Collect all pages
    pages = []
    page_types = []
    
    # 1. First → Next → Last pages (3 levels)
    for level in range(1, 4):
        fnl_page = generate_first_next_last_page(events, level=level, 
                                                 page_number=len(pages)+1, total_pages=99)
        pages.append(fnl_page)
        page_types.append(f'first_next_last_level{level}')
    
    # 2. Story Map
    story_map_page = generate_story_map(story_data, page_number=len(pages)+1, total_pages=99)
    pages.append(story_map_page)
    page_types.append('story_map')
    
    # 3. Event Ordering (horizontal and vertical)
    for layout in ['horizontal', 'vertical']:
        event_page = generate_event_ordering_page(events[:4], layout=layout,
                                                   page_number=len(pages)+1, total_pages=99)
        pages.append(event_page)
        page_types.append(f'event_ordering_{layout}')
    
    # 4. Retell Strip
    retell_page = generate_retell_strip(events[:4], with_lanyard=True,
                                       page_number=len(pages)+1, total_pages=99)
    pages.append(retell_page)
    page_types.append('retell_strip')
    
    # 5. Story Summary
    summary_page = generate_story_summary_page(page_number=len(pages)+1, total_pages=99)
    pages.append(summary_page)
    page_types.append('story_summary')
    
    # 6. Cut-out icons (multiple pages if needed)
    all_icons = events[:6]  # Limit to first 6 events
    cutout_pages = []
    for i in range(0, len(all_icons), 6):
        cutout_page = generate_cutout_icons_page(all_icons[i:i+6],
                                                 page_number=len(cutout_pages)+1,
                                                 total_pages=(len(all_icons) + 5) // 6,
                                                 with_grab_tabs=True)
        cutout_pages.append(cutout_page)
    
    # Update page numbers
    total_pages = len(pages)
    for i in range(total_pages):
        # Redraw page number with correct total
        draw = ImageDraw.Draw(pages[i])
        draw_page_number(draw, i + 1, total_pages)
    
    # Save PDFs
    output_files = {}
    
    # Main story sequencing pages
    main_pdf_path = os.path.join(output_dir, f"{theme_name}_Story_Sequencing.pdf")
    save_images_as_pdf(pages, main_pdf_path)
    output_files['story_sequencing'] = main_pdf_path
    print(f"Generated: {main_pdf_path}")
    
    # Cut-out icons
    if cutout_pages:
        cutout_pdf_path = os.path.join(output_dir, f"{theme_name}_Story_Icons_Cutouts.pdf")
        save_images_as_pdf(cutout_pages, cutout_pdf_path)
        output_files['cutouts'] = cutout_pdf_path
        print(f"Generated: {cutout_pdf_path}")
    
    # Storage labels
    if include_storage_label:
        # Main story sequencing label
        main_label_path = create_companion_label(
            main_pdf_path,
            theme_name=theme_name,
            activity_name="Story Sequencing"
        )
        if main_label_path:
            output_files['story_sequencing_label'] = main_label_path
            print(f"Generated: {main_label_path}")
        
        # Cutouts label
        if cutout_pages:
            cutouts_label_path = create_companion_label(
                cutout_pdf_path,
                theme_name=theme_name,
                activity_name="Story Icons Cutouts"
            )
            if cutouts_label_path:
                output_files['cutouts_label'] = cutouts_label_path
                print(f"Generated: {cutouts_label_path}")
    
    return output_files
