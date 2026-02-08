"""
Storage Label Helper Utility

Provides reusable functions for generating SPED-friendly storage labels
that can be used across all generators.
"""

from PIL import Image, ImageDraw, ImageFont
from utils.config import DPI, COLORS
from utils.pdf_export import save_image_as_pdf
import os


def generate_storage_label(theme_name, activity_name, level=None, icon_path=None, 
                           output_path=None, label_size='standard'):
    """
    Generate a single storage label PDF for organizing resources.
    
    Creates a SPED-friendly label with:
    - High-contrast border
    - Theme name (large text)
    - Activity name (large text)
    - Level indicator (if provided)
    - Optional small icon
    
    Args:
        theme_name: Name of the theme (e.g., "Brown Bear")
        activity_name: Name of the activity (e.g., "Matching Cards")
        level: Differentiation level (1-4) or None
        icon_path: Path to optional icon image file
        output_path: Where to save the PDF (auto-generated if None)
        label_size: 'small' (3x2"), 'standard' (4x3"), 'large' (5x4")
        
    Returns:
        str: Path to generated PDF file
    """
    # Define label dimensions at 300 DPI
    sizes = {
        'small': (int(3 * DPI), int(2 * DPI)),      # 3" x 2"
        'standard': (int(4 * DPI), int(3 * DPI)),   # 4" x 3"
        'large': (int(5 * DPI), int(4 * DPI)),      # 5" x 4"
    }
    
    width, height = sizes.get(label_size, sizes['standard'])
    
    # Create label canvas
    label = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(label)
    
    # Draw high-contrast border (thick black border)
    border_width = 8
    for i in range(border_width):
        draw.rectangle(
            [i, i, width - 1 - i, height - 1 - i],
            outline=(0, 0, 0)
        )
    
    # Calculate layout areas
    margin = 30
    content_x = margin + border_width
    content_y = margin + border_width
    content_width = width - (2 * margin) - (2 * border_width)
    content_height = height - (2 * margin) - (2 * border_width)
    
    # Load icon if provided
    icon_size = 0
    if icon_path and os.path.exists(icon_path):
        try:
            icon = Image.open(icon_path).convert('RGBA')
            # Scale icon to fit in corner
            icon_max = min(int(content_height * 0.3), 150)
            icon.thumbnail((icon_max, icon_max), Image.Resampling.LANCZOS)
            
            # Paste icon in top-right corner
            icon_x = width - margin - border_width - icon.width - 10
            icon_y = content_y + 10
            
            # Convert RGBA to RGB for pasting
            if icon.mode == 'RGBA':
                bg = Image.new('RGB', icon.size, (255, 255, 255))
                bg.paste(icon, mask=icon.split()[3])
                label.paste(bg, (icon_x, icon_y))
            else:
                label.paste(icon, (icon_x, icon_y))
            
            icon_size = icon.width + 20
        except Exception as e:
            # If icon loading fails, continue without it
            pass
    
    # Set up text rendering
    try:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    except:
        font_large = font_medium = font_small = None
    
    # Calculate text layout
    text_x = content_x + 10
    text_area_width = content_width - icon_size - 20
    current_y = content_y + 20
    
    # Draw theme name (large, bold appearance via multiple draws)
    theme_text = theme_name.upper()
    if font_large:
        # Draw multiple times for bold effect
        for offset_x in range(-1, 2):
            for offset_y in range(-1, 2):
                draw.text((text_x + offset_x, current_y + offset_y), 
                         theme_text, fill=(0, 0, 0), font=font_large)
        
        bbox = draw.textbbox((0, 0), theme_text, font=font_large)
        text_height = bbox[3] - bbox[1]
        current_y += text_height + 20
    
    # Draw separator line
    draw.line(
        [(text_x, current_y), (text_x + text_area_width, current_y)],
        fill=(0, 0, 0),
        width=2
    )
    current_y += 15
    
    # Draw activity name (large)
    if font_medium:
        # Wrap activity name if too long
        activity_text = activity_name
        bbox = draw.textbbox((0, 0), activity_text, font=font_medium)
        text_width = bbox[2] - bbox[0]
        
        # Simple word wrapping
        if text_width > text_area_width:
            words = activity_text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font_medium)
                if bbox[2] - bbox[0] <= text_area_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines:
                draw.text((text_x, current_y), line, fill=(0, 0, 0), font=font_medium)
                bbox = draw.textbbox((0, 0), line, font=font_medium)
                current_y += (bbox[3] - bbox[1]) + 10
        else:
            draw.text((text_x, current_y), activity_text, fill=(0, 0, 0), font=font_medium)
            current_y += (bbox[3] - bbox[1]) + 15
    
    # Draw level indicator if provided
    if level is not None:
        level_text = f"LEVEL {level}"
        
        # Draw level in a box for emphasis
        if font_small:
            bbox = draw.textbbox((0, 0), level_text, font=font_small)
            level_width = bbox[2] - bbox[0] + 20
            level_height = bbox[3] - bbox[1] + 10
            
            # Draw level box
            box_x = text_x
            box_y = current_y
            draw.rectangle(
                [box_x, box_y, box_x + level_width, box_y + level_height],
                fill=(0, 0, 0),
                outline=(0, 0, 0)
            )
            
            # Draw level text in white
            draw.text((box_x + 10, box_y + 5), level_text, 
                     fill=(255, 255, 255), font=font_small)
    
    # Generate output path if not provided
    if output_path is None:
        from utils.file_naming import sanitize_filename
        base_name = f"{sanitize_filename(theme_name)}_{sanitize_filename(activity_name)}"
        if level:
            base_name += f"_Level{level}"
        base_name += "_LABEL.pdf"
        output_path = os.path.join('output', base_name)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Save as PDF
    save_image_as_pdf(label, output_path, title=f"{theme_name} - {activity_name} Storage Label")
    
    return output_path


def create_companion_label(main_pdf_path, theme_name, activity_name, level=None, icon=None):
    """
    Create a companion storage label PDF alongside an existing resource PDF.
    
    Automatically generates the label filename based on the main PDF path
    by appending "_LABEL" before the .pdf extension.
    
    Args:
        main_pdf_path: Path to the main resource PDF (e.g., "output/Theme_Activity.pdf")
        theme_name: Name of the theme
        activity_name: Name of the activity
        level: Differentiation level
        icon: Optional icon path or PIL Image
        
    Returns:
        str: Path to generated label PDF
    """
    # Generate label path from main PDF path
    base_path = main_pdf_path.rsplit('.pdf', 1)[0]
    label_path = f"{base_path}_LABEL.pdf"
    
    # Handle icon as path or PIL Image
    icon_path = None
    if icon is not None:
        if isinstance(icon, str):
            icon_path = icon
        # If it's a PIL Image, we skip using it for now (would need to save temp file)
    
    return generate_storage_label(
        theme_name=theme_name,
        activity_name=activity_name,
        level=level,
        icon_path=icon_path,
        output_path=label_path
    )


if __name__ == "__main__":
    print("Storage Label Helper Utility")
    print("Use generate_storage_label() to create storage labels")
