#!/usr/bin/env python3
"""
Generate simple but functional Brown Bear samples that demonstrate:
1. Theme loading with /assets/ structure
2. Icon and image access
3. Dual-mode (color + BW) PDF generation
4. Professional layout
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

sys.path.insert(0, str(Path(__file__).parent))

from themes.theme_loader import load_theme
from utils.color_helpers import image_to_grayscale


def create_vocab_flashcards(theme, output_dir, mode='color'):
    """Create simple vocabulary flashcards"""
    pdf_path = os.path.join(output_dir, f'brown_bear_vocab_flashcards_{mode}.pdf')
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Title page
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 100, f"Brown Bear Vocabulary Flashcards")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, height - 130, f"Mode: {mode.upper()}")
    c.drawCentredString(width/2, height - 150, f"{len(theme.vocab)} animals from the story")
    
    y_pos = height - 200
    c.setFont("Helvetica", 12)
    for i, word in enumerate(theme.vocab, 1):
        c.drawString(100, y_pos, f"{i}. {word.capitalize()}")
        y_pos -= 25
        if y_pos < 100:
            c.showPage()
            y_pos = height - 100
    
    # Card pages - 4 cards per page (2x2 grid)
    card_width = 2.5 * inch
    card_height = 3 * inch
    margin = 0.5 * inch
    
    for i, word in enumerate(theme.vocab):
        if i % 4 == 0 and i > 0:
            c.showPage()
        
        # Calculate position in grid
        row = (i % 4) // 2
        col = (i % 4) % 2
        
        x = margin + col * (card_width + 0.5*inch)
        y = height - margin - (row + 1) * (card_height + 0.5*inch)
        
        # Draw card border
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(2)
        c.rect(x, y, card_width, card_height)
        
        # Try to load and draw image
        icon_path = theme.get_icon_path(f'{word}.png')
        if not icon_path:
            # Try with capitalize
            icon_path = theme.get_icon_path(f'{word.capitalize()}.png')
        if not icon_path:
            # Try to find in icons list
            for icon_file in theme.icons:
                if word.lower() in icon_file.lower():
                    icon_path = theme.get_icon_path(icon_file)
                    break
        
        if icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                if mode == 'bw':
                    img = image_to_grayscale(img)
                
                # Resize to fit in card
                img.thumbnail((int(card_width * 0.8), int(card_height * 0.6)), Image.Resampling.LANCZOS)
                
                # Save temp file
                temp_path = f'/tmp/temp_icon_{i}.png'
                img.save(temp_path)
                
                # Draw image centered
                img_x = x + (card_width - img.width) / 2
                img_y = y + card_height - img.height - 20
                c.drawImage(temp_path, img_x, img_y, width=img.width, height=img.height)
                
                os.remove(temp_path)
            except Exception as e:
                print(f"Warning: Could not load image for {word}: {e}")
                # Draw placeholder
                c.setFillColorRGB(0.9, 0.9, 0.9)
                c.rect(x + 20, y + card_height - 120, card_width - 40, 100, fill=1)
        
        # Draw word label
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 18)
        text_width = c.stringWidth(word.capitalize(), "Helvetica-Bold", 18)
        c.drawString(x + (card_width - text_width) / 2, y + 30, word.capitalize())
    
    c.save()
    print(f"✓ Created: {pdf_path}")
    return pdf_path


def create_matching_activity(theme, output_dir, mode='color'):
    """Create a simple matching activity"""
    pdf_path = os.path.join(output_dir, f'brown_bear_matching_{mode}.pdf')
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 60, "Brown Bear Matching Activity")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 85, "Match the animals with their names")
    
    # Create two columns - images on left, words on right
    left_x = 100
    right_x = 400
    y_start = height - 150
    item_height = 80
    
    # Use first 6 words
    words_to_use = theme.vocab[:6]
    
    for i, word in enumerate(words_to_use):
        y_pos = y_start - (i * item_height)
        
        # Draw image on left
        icon_path = theme.get_icon_path(f'{word}.png')
        if not icon_path:
            icon_path = theme.get_icon_path(f'{word.capitalize()}.png')
        if not icon_path:
            for icon_file in theme.icons:
                if word.lower() in icon_file.lower():
                    icon_path = theme.get_icon_path(icon_file)
                    break
        
        if icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                if mode == 'bw':
                    img = image_to_grayscale(img)
                
                img.thumbnail((60, 60), Image.Resampling.LANCZOS)
                temp_path = f'/tmp/match_icon_{i}.png'
                img.save(temp_path)
                c.drawImage(temp_path, left_x, y_pos, width=60, height=60)
                os.remove(temp_path)
            except:
                pass
        
        # Draw line from image
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.line(left_x + 70, y_pos + 30, left_x + 120, y_pos + 30)
        
        # Draw word on right (shuffled slightly)
        word_index = (i + 2) % len(words_to_use)
        shuffled_word = words_to_use[word_index]
        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 16)
        c.drawString(right_x, y_pos + 25, shuffled_word.capitalize())
    
    c.save()
    print(f"✓ Created: {pdf_path}")
    return pdf_path


def create_yes_no_cards(theme, output_dir, mode='color'):
    """Create simple yes/no identification cards"""
    pdf_path = os.path.join(output_dir, f'brown_bear_yes_no_{mode}.pdf')
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Title page
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 60, "Brown Bear Yes/No Cards")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 85, "Circle YES or NO for each animal")
    
    # 2 cards per page
    card_height = 3.5 * inch
    margin = 0.75 * inch
    
    for i, word in enumerate(theme.vocab):
        if i > 0 and i % 2 == 0:
            c.showPage()
        
        row = i % 2
        y = height - margin - (row + 1) * (card_height + 0.5*inch)
        
        # Card border
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(2)
        c.rect(margin, y, width - 2*margin, card_height)
        
        # Question
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, y + card_height - 40, f"Is this a {word}?")
        
        # Image
        icon_path = theme.get_icon_path(f'{word}.png')
        if not icon_path:
            icon_path = theme.get_icon_path(f'{word.capitalize()}.png')
        if not icon_path:
            for icon_file in theme.icons:
                if word.lower() in icon_file.lower():
                    icon_path = theme.get_icon_path(icon_file)
                    break
        
        if icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                if mode == 'bw':
                    img = image_to_grayscale(img)
                
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                temp_path = f'/tmp/yesno_icon_{i}.png'
                img.save(temp_path)
                
                img_x = (width - img.width) / 2
                img_y = y + card_height/2
                c.drawImage(temp_path, img_x, img_y, width=img.width, height=img.height)
                os.remove(temp_path)
            except:
                pass
        
        # YES/NO buttons
        button_y = y + 50
        button_width = 100
        button_height = 40
        
        # YES button
        yes_x = width/2 - button_width - 20
        c.setStrokeColorRGB(0, 0.6, 0)
        c.setLineWidth(3)
        c.rect(yes_x, button_y, button_width, button_height)
        c.setFillColorRGB(0, 0.6, 0)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(yes_x + button_width/2, button_y + 12, "YES")
        
        # NO button
        no_x = width/2 + 20
        c.setStrokeColorRGB(0.8, 0, 0)
        c.rect(no_x, button_y, button_width, button_height)
        c.setFillColorRGB(0.8, 0, 0)
        c.drawCentredString(no_x + button_width/2, button_y + 12, "NO")
    
    c.save()
    print(f"✓ Created: {pdf_path}")
    return pdf_path


def create_aac_board(theme, output_dir, mode='color'):
    """Create a simple AAC communication board"""
    pdf_path = os.path.join(output_dir, f'brown_bear_aac_board_{mode}.pdf')
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 40, "Brown Bear AAC Communication Board")
    
    # 3x3 grid of vocabulary
    grid_cols = 3
    grid_rows = 3
    cell_width = (width - 2*inch) / grid_cols
    cell_height = (height - 3*inch) / grid_rows
    start_x = inch
    start_y = height - 2*inch
    
    for i, word in enumerate(theme.vocab[:9]):  # 3x3 = 9 cells
        row = i // grid_cols
        col = i % grid_cols
        
        x = start_x + col * cell_width
        y = start_y - (row + 1) * cell_height
        
        # Cell border
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1.5)
        c.rect(x, y, cell_width, cell_height)
        
        # Icon
        icon_path = theme.get_icon_path(f'{word}.png')
        if not icon_path:
            icon_path = theme.get_icon_path(f'{word.capitalize()}.png')
        if not icon_path:
            for icon_file in theme.icons:
                if word.lower() in icon_file.lower():
                    icon_path = theme.get_icon_path(icon_file)
                    break
        
        if icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                if mode == 'bw':
                    img = image_to_grayscale(img)
                
                img.thumbnail((int(cell_width * 0.7), int(cell_height * 0.6)), Image.Resampling.LANCZOS)
                temp_path = f'/tmp/aac_icon_{i}.png'
                img.save(temp_path)
                
                img_x = x + (cell_width - img.width) / 2
                img_y = y + cell_height - img.height - 10
                c.drawImage(temp_path, img_x, img_y, width=img.width, height=img.height)
                os.remove(temp_path)
            except:
                pass
        
        # Label
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 14)
        text_width = c.stringWidth(word.capitalize(), "Helvetica-Bold", 14)
        c.drawString(x + (cell_width - text_width) / 2, y + 15, word.capitalize())
    
    c.save()
    print(f"✓ Created: {pdf_path}")
    return pdf_path


def main():
    print("="*60)
    print("BROWN BEAR SAMPLE GENERATION - Simple Demonstration")
    print("="*60)
    print()
    
    # Load theme
    print("Loading Brown Bear theme...")
    theme = load_theme('brown_bear', mode='color')
    print(f"✓ Theme: {theme.name}")
    print(f"  - {len(theme.vocab)} vocabulary words")
    print(f"  - {len(theme.icons)} icons available")
    print()
    
    # Create output directory
    output_dir = 'samples/brown_bear'
    os.makedirs(output_dir, exist_ok=True)
    print(f"✓ Output directory: {output_dir}")
    print()
    
    # Generate samples in both modes
    print("Generating COLOR versions...")
    create_vocab_flashcards(theme, output_dir, 'color')
    create_matching_activity(theme, output_dir, 'color')
    create_yes_no_cards(theme, output_dir, 'color')
    create_aac_board(theme, output_dir, 'color')
    
    print("\nGenerating BLACK-AND-WHITE versions...")
    create_vocab_flashcards(theme, output_dir, 'bw')
    create_matching_activity(theme, output_dir, 'bw')
    create_yes_no_cards(theme, output_dir, 'bw')
    create_aac_board(theme, output_dir, 'bw')
    
    print()
    print("="*60)
    print("GENERATION COMPLETE")
    print("="*60)
    print(f"\n✓ 8 PDF files generated in {output_dir}/")
    print("  - Vocab Flashcards (color + BW)")
    print("  - Matching Activity (color + BW)")
    print("  - Yes/No Cards (color + BW)")
    print("  - AAC Communication Board (color + BW)")
    print()
    print("These demonstrate:")
    print("  ✓ Theme loading from /assets/ structure")
    print("  ✓ Icon retrieval with intelligent fallback")
    print("  ✓ Dual-mode (color + BW) generation")
    print("  ✓ Professional PDF layout")
    print("  ✓ Grayscale conversion for BW mode")


if __name__ == '__main__':
    main()
