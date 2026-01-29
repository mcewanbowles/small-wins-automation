"""
Sentence Strips (AAC) Generator

Generates sentence strips using AAC/PCS symbols for communication.
Supports core vocabulary and customizable sentence frames.
"""

from PIL import Image, ImageDraw
from utils.config import MARGINS, DPI, PAGE_WIDTH
from utils.image_loader import get_image_loader
from utils.image_utils import scale_image_proportional
from utils.layout import create_page_canvas, add_page_border, add_footer
from utils.pdf_export import save_images_as_pdf


def generate_sentence_strip(symbol_word_pairs, sentence_starter=None, folder_type='aac'):
    """
    Generate a single sentence strip with AAC symbols.
    
    Args:
        symbol_word_pairs: List of tuples (symbol_filename, word_text)
        sentence_starter: Optional sentence starter text (e.g., "I see")
        folder_type: Should be 'aac' for AAC symbols
        
    Returns:
        PIL.Image: Generated sentence strip
    """
    # Strip dimensions: 2.5" high x 8.5" wide at 300 DPI
    strip_width = int(8.5 * DPI)
    strip_height = int(2.5 * DPI)
    
    strip = Image.new('RGBA', (strip_width, strip_height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(strip)
    
    # Draw border
    for i in range(5):
        draw.rectangle(
            [i, i, strip_width - 1 - i, strip_height - 1 - i],
            outline=(0, 0, 0, 255)
        )
    
    # Calculate cell size
    num_cells = len(symbol_word_pairs) + (1 if sentence_starter else 0)
    cell_width = (strip_width - 40) // num_cells
    cell_height = strip_height - 20
    
    image_loader = get_image_loader()
    current_x = 20
    
    # Add sentence starter if provided
    if sentence_starter:
        # Draw cell border
        draw.rectangle(
            [current_x, 10, current_x + cell_width, 10 + cell_height],
            outline=(0, 0, 0, 255),
            width=3
        )
        
        # Draw text
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), sentence_starter, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = current_x + (cell_width - text_width) // 2
            text_y = 10 + (cell_height - text_height) // 2
            draw.text((text_x, text_y), sentence_starter, fill=(0, 0, 0, 255), font=font)
        except:
            pass
        
        current_x += cell_width
    
    # Add symbol cells
    for symbol_file, word in symbol_word_pairs:
        # Draw cell border
        draw.rectangle(
            [current_x, 10, current_x + cell_width, 10 + cell_height],
            outline=(0, 0, 0, 255),
            width=3
        )
        
        # Load and place symbol
        try:
            symbol_image = image_loader.load_image(symbol_file, folder_type)
            
            # Reserve space for word below symbol
            symbol_height = int(cell_height * 0.7)
            scaled_symbol = scale_image_proportional(symbol_image, max_width=cell_width-20, max_height=symbol_height)
            
            # Center symbol in cell
            sym_x = current_x + (cell_width - scaled_symbol.width) // 2
            sym_y = 15
            strip.paste(scaled_symbol, (sym_x, sym_y), scaled_symbol)
            
            # Add word below symbol
            try:
                from PIL import ImageFont
                font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), word, font=font)
                text_width = bbox[2] - bbox[0]
                text_x = current_x + (cell_width - text_width) // 2
                text_y = 15 + symbol_height + 10
                draw.text((text_x, text_y), word, fill=(0, 0, 0, 255), font=font)
            except:
                pass
        except FileNotFoundError:
            # If symbol not found, just draw the word
            try:
                from PIL import ImageFont
                font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), word, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = current_x + (cell_width - text_width) // 2
                text_y = 10 + (cell_height - text_height) // 2
                draw.text((text_x, text_y), word, fill=(0, 0, 0, 255), font=font)
            except:
                pass
        
        current_x += cell_width
    
    return strip


def generate_sentence_strips_set(sentence_templates, folder_type='aac',
                                  theme_name='Theme', output_dir='output'):
    """
    Generate a set of sentence strips.
    
    Args:
        sentence_templates: List of dicts with 'starter' and 'symbols' keys
                          e.g., [{'starter': 'I see', 'symbols': [('dog.png', 'dog'), ('cat.png', 'cat')]}]
        folder_type: Image folder type
        theme_name: Theme name
        output_dir: Output directory
        
    Returns:
        list: Generated pages
    """
    pages = []
    strips_per_page = 4
    
    for page_start in range(0, len(sentence_templates), strips_per_page):
        page = create_page_canvas()
        page_templates = sentence_templates[page_start:page_start + strips_per_page]
        
        # Generate strips
        strips = []
        for template in page_templates:
            strip = generate_sentence_strip(
                template['symbols'],
                template.get('starter')
            )
            strips.append(strip)
        
        # Place strips on page
        strip_height = int(2.5 * DPI)
        spacing = 80
        total_height = (strip_height * len(strips)) + (spacing * (len(strips) - 1))
        start_y = (int(page.height) - total_height) // 2
        
        for idx, strip in enumerate(strips):
            y = start_y + (idx * (strip_height + spacing))
            x = (int(page.width) - strip.width) // 2
            page.paste(strip, (x, y), strip)
        
        add_page_border(page)
        add_footer(page)
        pages.append(page)
    
    # Save PDF
    output_path = f"{output_dir}/{theme_name}_Sentence_Strips.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Sentence Strips")
    
    return pages


if __name__ == "__main__":
    print("Sentence Strips (AAC) Generator")
    print("Use generate_sentence_strip() or generate_sentence_strips_set()")
