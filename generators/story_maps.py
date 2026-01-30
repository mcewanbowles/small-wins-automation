"""
Story Maps Generator

Generates story map organizers for comprehension activities.
Includes sections for characters, setting, problem, and solution.
"""

from PIL import Image, ImageDraw
from utils.config import PAGE_WIDTH, PAGE_HEIGHT, MARGINS, DPI
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional
from utils.layout import create_page_canvas, add_page_border, add_footer, add_title_to_page
from utils.pdf_export import save_images_as_pdf


def generate_story_map(story_title, sections_data=None, folder_type='color', level=1):
    """
    Generate a story map organizer.
    
    Args:
        story_title: Title of the story
        sections_data: Dict with optional 'characters', 'setting', 'problem', 'solution' keys
                      Each containing image filenames or None
        folder_type: Image folder type
        level: Differentiation level (1=with images, 2=blank for writing)
        
    Returns:
        PIL.Image: Generated story map
    """
    page = create_page_canvas()
    
    # Add title
    add_title_to_page(page, f"Story Map: {story_title}")
    
    draw = ImageDraw.Draw(page)
    image_loader = get_image_loader()
    
    # Define sections
    section_labels = ['Characters', 'Setting', 'Problem', 'Solution']
    
    # Layout: 2x2 grid
    section_width = (PAGE_WIDTH - (MARGINS['page'] * 3)) // 2
    section_height = (PAGE_HEIGHT - 600) // 2
    
    start_y = 350
    spacing = MARGINS['page']
    
    for idx, label in enumerate(section_labels):
        row = idx // 2
        col = idx % 2
        
        x = MARGINS['page'] + (col * (section_width + spacing))
        y = start_y + (row * (section_height + spacing))
        
        # Draw section box
        draw.rectangle(
            [x, y, x + section_width, y + section_height],
            outline=(0, 0, 0, 255),
            width=5
        )
        
        # Draw label at top of section
        label_height = 60
        draw.rectangle(
            [x, y, x + section_width, y + label_height],
            fill=(220, 220, 255, 255),
            outline=(0, 0, 0, 255),
            width=3
        )
        
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = x + (section_width - text_width) // 2
            text_y = y + (label_height - text_height) // 2
            draw.text((text_x, text_y), label, fill=(0, 0, 0, 255), font=font)
        except:
            pass
        
        # Add image if provided and Level 1
        if level == 1 and sections_data:
            section_key = label.lower()
            if section_key in sections_data and sections_data[section_key]:
                try:
                    image_file = sections_data[section_key]
                    theme_image = image_loader.load_image(image_file, folder_type)
                    
                    # Scale image to fit in section
                    image_area_height = section_height - label_height - 20
                    scaled_image = scale_image_proportional(
                        theme_image,
                        max_width=section_width - 40,
                        max_height=image_area_height
                    )
                    
                    # Center image in section
                    img_x = x + (section_width - scaled_image.width) // 2
                    img_y = y + label_height + 10
                    page.paste(scaled_image, (int(img_x), int(img_y)), scaled_image)
                except:
                    pass
    
    add_page_border(page)
    add_footer(page)
    
    return page


def generate_story_maps_set(stories_data, folder_type='color', level=1,
                            theme_name='Theme', output_dir='output',
                            include_storage_label=False):
    """
    Generate a set of story maps.
    
    Args:
        stories_data: List of dicts with 'title' and optional 'sections' keys
        folder_type: Image folder type
        level: Differentiation level
        theme_name: Theme name
        output_dir: Output directory
        include_storage_label: If True, also generate a companion storage label PDF
        
    Returns:
        list: Generated pages
    """
    pages = []
    
    for story in stories_data:
        page = generate_story_map(
            story['title'],
            story.get('sections'),
            folder_type,
            level
        )
        pages.append(page)
    
    # Save PDF
    import os
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/{theme_name}_Story_Maps_Level{level}.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Story Maps")
    
    # Generate storage label if requested
    if include_storage_label:
        from utils.storage_label_helper import create_companion_label
        
        label_path = create_companion_label(
            main_pdf_path=output_path,
            theme_name=theme_name,
            activity_name="Story Maps",
            level=level
        )
        print(f"✓ Generated storage label")
        print(f"  Label: {label_path}")
    
    return pages


if __name__ == "__main__":
    print("Story Maps Generator")
    print("Use generate_story_map() or generate_story_maps_set()")
