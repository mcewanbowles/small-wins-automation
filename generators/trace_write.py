"""
Trace & Write Cards Generator

Creates handwriting practice cards for SPED learners with tracing and writing activities.
Uses task-box sizing standard (4 cards per page in 2×2 grid).

Card Types:
1. Word Tracing - Trace individual vocabulary words
2. Sentence Tracing - Trace simple sentences with sentence frames
3. Color & Trace - Color the icon, then trace the word
4. Write the Word - Independent writing with visual support
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from utils.draw_helpers import (
    create_taskbox_page,
    draw_taskbox_card,
    draw_text_with_wrapping,
    get_theme_fonts,
    get_theme_colors
)

# Constants for task-box sizing
CARD_WIDTH_INCHES = 5.25
CARD_HEIGHT_INCHES = 4
DPI = 300
CARD_WIDTH = int(CARD_WIDTH_INCHES * DPI)
CARD_HEIGHT = int(CARD_HEIGHT_INCHES * DPI)

def draw_traced_text(draw, text, x, y, font, color="#000000", dashed=True):
    """
    Draw text with dashed/traced style for handwriting practice.
    
    Args:
        draw: PIL ImageDraw object
        text: Text to draw
        x, y: Position
        font: Font to use
        color: Text color
        dashed: Whether to use dashed outline style
    """
    if dashed:
        # Draw dashed outline for tracing
        bbox = draw.textbbox((x, y), text, font=font)
        # Draw light gray guide
        draw.text((x, y), text, fill="#CCCCCC", font=font)
        # Draw dashed border
        for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x + offset[0], y + offset[1]), text, fill="#999999", font=font)
    else:
        # Regular text
        draw.text((x, y), text, fill=color, font=font)

def draw_writing_lines(draw, x, y, width, height, line_spacing=100):
    """
    Draw handwriting practice lines (baseline, midline, top line).
    
    Args:
        draw: PIL ImageDraw object
        x, y: Starting position
        width: Width of writing area
        height: Height of writing area
        line_spacing: Space between baselines
    """
    line_color = "#999999"
    
    # Calculate number of lines that fit
    num_lines = max(1, height // line_spacing)
    
    for i in range(num_lines):
        baseline_y = y + (i * line_spacing) + line_spacing // 2
        
        # Draw top line (thin)
        draw.line([(x, baseline_y - 60), (x + width, baseline_y - 60)], 
                 fill="#DDDDDD", width=2)
        
        # Draw midline/dashed line (thin, dashed effect)
        for dash_x in range(x, x + width, 20):
            draw.line([(dash_x, baseline_y - 30), (min(dash_x + 10, x + width), baseline_y - 30)], 
                     fill="#CCCCCC", width=2)
        
        # Draw baseline (thicker)
        draw.line([(x, baseline_y), (x + width, baseline_y)], 
                 fill=line_color, width=3)

def create_word_trace_card(theme_data, word, icon_path=None, use_real_image=False):
    """Create a word tracing card."""
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), 'white')
    draw = ImageDraw.Draw(img)
    
    # Get theme styling
    fonts = get_theme_fonts(theme_data)
    colors = get_theme_colors(theme_data)
    
    title_font = fonts.get('title', ImageFont.truetype("arial.ttf", 60))
    word_font = fonts.get('body', ImageFont.truetype("arial.ttf", 80))
    
    # Title
    title_text = "Trace the Word"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((CARD_WIDTH - title_width) // 2, 40), title_text, 
             fill=colors.get('primary', '#000000'), font=title_font)
    
    # Icon area (if provided)
    icon_y = 150
    icon_size = 300
    if icon_path and Path(icon_path).exists():
        try:
            icon = Image.open(icon_path)
            icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            icon_x = (CARD_WIDTH - icon_size) // 2
            img.paste(icon, (icon_x, icon_y), icon if icon.mode == 'RGBA' else None)
        except Exception:
            pass
    
    # Word to trace
    trace_y = icon_y + icon_size + 60
    word_bbox = draw.textbbox((0, 0), word, font=word_font)
    word_width = word_bbox[2] - word_bbox[0]
    word_x = (CARD_WIDTH - word_width) // 2
    
    # Draw tracing guide
    draw_traced_text(draw, word, word_x, trace_y, word_font, 
                    color=colors.get('primary', '#000000'), dashed=True)
    
    # Writing lines below
    lines_y = trace_y + 150
    draw_writing_lines(draw, 100, lines_y, CARD_WIDTH - 200, 180, line_spacing=90)
    
    return img

def create_sentence_trace_card(theme_data, sentence, icon_path=None):
    """Create a sentence tracing card."""
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), 'white')
    draw = ImageDraw.Draw(img)
    
    fonts = get_theme_fonts(theme_data)
    colors = get_theme_colors(theme_data)
    
    title_font = fonts.get('title', ImageFont.truetype("arial.ttf", 55))
    sentence_font = fonts.get('body', ImageFont.truetype("arial.ttf", 60))
    
    # Title
    title_text = "Trace the Sentence"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((CARD_WIDTH - title_width) // 2, 40), title_text, 
             fill=colors.get('primary', '#000000'), font=title_font)
    
    # Small icon (if provided)
    icon_y = 140
    icon_size = 200
    if icon_path and Path(icon_path).exists():
        try:
            icon = Image.open(icon_path)
            icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            icon_x = (CARD_WIDTH - icon_size) // 2
            img.paste(icon, (icon_x, icon_y), icon if icon.mode == 'RGBA' else None)
        except Exception:
            pass
    
    # Sentence to trace
    trace_y = icon_y + icon_size + 40
    
    # Word wrap if needed
    words = sentence.split()
    if len(sentence) > 25:
        # Split into two lines
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        
        for i, line in enumerate([line1, line2]):
            line_bbox = draw.textbbox((0, 0), line, font=sentence_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (CARD_WIDTH - line_width) // 2
            draw_traced_text(draw, line, line_x, trace_y + (i * 80), 
                           sentence_font, color=colors.get('primary', '#000000'), dashed=True)
    else:
        sent_bbox = draw.textbbox((0, 0), sentence, font=sentence_font)
        sent_width = sent_bbox[2] - sent_bbox[0]
        sent_x = (CARD_WIDTH - sent_width) // 2
        draw_traced_text(draw, sentence, sent_x, trace_y, sentence_font, 
                        color=colors.get('primary', '#000000'), dashed=True)
    
    # Writing lines
    lines_y = trace_y + 200
    draw_writing_lines(draw, 80, lines_y, CARD_WIDTH - 160, 220, line_spacing=110)
    
    return img

def create_color_trace_card(theme_data, word, icon_path=None):
    """Create a color-and-trace card."""
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), 'white')
    draw = ImageDraw.Draw(img)
    
    fonts = get_theme_fonts(theme_data)
    colors = get_theme_colors(theme_data)
    
    title_font = fonts.get('title', ImageFont.truetype("arial.ttf", 55))
    instruction_font = fonts.get('body', ImageFont.truetype("arial.ttf", 45))
    word_font = fonts.get('body', ImageFont.truetype("arial.ttf", 75))
    
    # Title
    title_text = "Color & Trace"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((CARD_WIDTH - title_width) // 2, 30), title_text, 
             fill=colors.get('primary', '#000000'), font=title_font)
    
    # Instruction
    inst_text = "1. Color the picture"
    inst_bbox = draw.textbbox((0, 0), inst_text, font=instruction_font)
    inst_width = inst_bbox[2] - inst_bbox[0]
    draw.text(((CARD_WIDTH - inst_width) // 2, 110), inst_text, 
             fill="#333333", font=instruction_font)
    
    # Coloring icon (outline only)
    icon_y = 190
    icon_size = 280
    if icon_path and Path(icon_path).exists():
        try:
            icon = Image.open(icon_path).convert('L')  # Grayscale for outline
            icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            # Create outline effect
            icon_outline = icon.point(lambda x: 255 if x > 200 else 0)
            icon_rgb = Image.new('RGB', (icon_size, icon_size), 'white')
            icon_rgb.paste(icon_outline, (0, 0))
            icon_x = (CARD_WIDTH - icon_size) // 2
            img.paste(icon_rgb, (icon_x, icon_y))
        except Exception:
            # Draw placeholder
            icon_x = (CARD_WIDTH - icon_size) // 2
            draw.rectangle([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size],
                         outline="#CCCCCC", width=3)
    
    # Instruction 2
    inst2_text = "2. Trace the word"
    inst2_bbox = draw.textbbox((0, 0), inst2_text, font=instruction_font)
    inst2_width = inst2_bbox[2] - inst2_bbox[0]
    draw.text(((CARD_WIDTH - inst2_width) // 2, icon_y + icon_size + 20), 
             inst2_text, fill="#333333", font=instruction_font)
    
    # Word to trace
    trace_y = icon_y + icon_size + 90
    word_bbox = draw.textbbox((0, 0), word, font=word_font)
    word_width = word_bbox[2] - word_bbox[0]
    word_x = (CARD_WIDTH - word_width) // 2
    draw_traced_text(draw, word, word_x, trace_y, word_font, 
                    color=colors.get('primary', '#000000'), dashed=True)
    
    return img

def create_write_word_card(theme_data, word, icon_path=None):
    """Create an independent writing card with visual support."""
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), 'white')
    draw = ImageDraw.Draw(img)
    
    fonts = get_theme_fonts(theme_data)
    colors = get_theme_colors(theme_data)
    
    title_font = fonts.get('title', ImageFont.truetype("arial.ttf", 60))
    word_font = fonts.get('body', ImageFont.truetype("arial.ttf", 65))
    
    # Title
    title_text = "Write the Word"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((CARD_WIDTH - title_width) // 2, 40), title_text, 
             fill=colors.get('primary', '#000000'), font=title_font)
    
    # Icon reference
    icon_y = 150
    icon_size = 280
    if icon_path and Path(icon_path).exists():
        try:
            icon = Image.open(icon_path)
            icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            icon_x = (CARD_WIDTH - icon_size) // 2
            img.paste(icon, (icon_x, icon_y), icon if icon.mode == 'RGBA' else None)
        except Exception:
            pass
    
    # Model word (small, at top for reference)
    model_y = icon_y + icon_size + 30
    word_bbox = draw.textbbox((0, 0), word, font=word_font)
    word_width = word_bbox[2] - word_bbox[0]
    word_x = (CARD_WIDTH - word_width) // 2
    draw.text((word_x, model_y), word, fill="#AAAAAA", font=word_font)
    
    # Writing lines for independent practice
    lines_y = model_y + 120
    draw_writing_lines(draw, 100, lines_y, CARD_WIDTH - 200, 250, line_spacing=125)
    
    return img

def create_storage_label(theme_data, card_type):
    """Create a storage label for the card set."""
    from generators.storage_labels import create_label
    
    theme_name = theme_data.get('theme_name', 'Theme')
    label_text = f"{theme_name}\nTrace & Write\n{card_type}"
    
    return create_label(label_text, theme_data)

def generate_trace_write_cards(theme_json_path, output_dir):
    """
    Generate all trace & write card types for a theme.
    
    Args:
        theme_json_path: Path to theme JSON file
        output_dir: Directory to save generated PDFs
    """
    # Load theme data
    with open(theme_json_path, 'r') as f:
        theme_data = json.load(f)
    
    theme_name = theme_data.get('theme_name', 'theme')
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get icons and words
    fringe_icons = theme_data.get('fringe_icons', [])
    if not fringe_icons:
        print(f"No fringe_icons found in theme {theme_name}")
        return
    
    # Sentence frame for sentence tracing
    sentence_frame = theme_data.get('book_adaptation', {}).get('sentence_frame', 'I see a {}.')
    
    # Generate each card type
    card_types = {
        'word_trace': ('Word Tracing', create_word_trace_card),
        'sentence_trace': ('Sentence Tracing', create_sentence_trace_card),
        'color_trace': ('Color & Trace', create_color_trace_card),
        'write_word': ('Write the Word', create_write_word_card)
    }
    
    for card_key, (card_name, card_func) in card_types.items():
        print(f"Generating {card_name} cards...")
        
        pages = []
        current_page_cards = []
        
        for item in fringe_icons:
            word = item.get('word', item.get('name', ''))
            icon_path = item.get('icon_path', item.get('path', ''))
            
            if not word:
                continue
            
            # Create card based on type
            if card_key == 'word_trace':
                card = create_word_trace_card(theme_data, word, icon_path)
            elif card_key == 'sentence_trace':
                sentence = sentence_frame.format(word)
                card = create_sentence_trace_card(theme_data, sentence, icon_path)
            elif card_key == 'color_trace':
                card = create_color_trace_card(theme_data, word, icon_path)
            elif card_key == 'write_word':
                card = create_write_word_card(theme_data, word, icon_path)
            else:
                continue
            
            current_page_cards.append(card)
            
            # When we have 4 cards, create a page
            if len(current_page_cards) == 4:
                page = create_taskbox_page(current_page_cards, theme_data, 
                                          f"{card_name} - Page {len(pages) + 1}")
                pages.append(page)
                current_page_cards = []
        
        # Handle remaining cards
        if current_page_cards:
            # Pad with blank cards if needed
            while len(current_page_cards) < 4:
                blank = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), 'white')
                current_page_cards.append(blank)
            page = create_taskbox_page(current_page_cards, theme_data, 
                                      f"{card_name} - Page {len(pages) + 1}")
            pages.append(page)
        
        # Add storage label as final page
        if pages:
            label = create_storage_label(theme_data, card_name)
            pages.append(label)
            
            # Save PDF
            pdf_name = f"{theme_name}_trace_write_{card_key}.pdf"
            pdf_path = output_path / pdf_name
            pages[0].save(pdf_path, save_all=True, append_images=pages[1:], 
                         resolution=DPI, quality=95)
            print(f"Saved: {pdf_path}")
    
    print(f"Trace & Write card generation complete for {theme_name}!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python trace_write.py <theme_json_path> [output_dir]")
        sys.exit(1)
    
    theme_json = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "output/trace_write"
    
    generate_trace_write_cards(theme_json, output)
