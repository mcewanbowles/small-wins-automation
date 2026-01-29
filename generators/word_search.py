"""
Word Search Generator

Generates word search puzzles with theme words and visual support.
Simplified grids for accessibility (8x8 or 10x10).
"""

from PIL import Image, ImageDraw
from utils.config import PAGE_WIDTH, PAGE_HEIGHT, MARGINS, DPI
from utils.layout import create_page_canvas, add_page_border, add_footer, add_title_to_page
from utils.pdf_export import save_images_as_pdf
import random


def generate_word_search(words, theme_name='Theme', grid_size=10, show_answers=False):
    """
    Generate a word search puzzle.
    
    Args:
        words: List of words to include (max 10 words recommended)
        theme_name: Theme name
        grid_size: Size of grid (8, 10, or 12)
        show_answers: Whether to highlight answers
        
    Returns:
        PIL.Image: Generated word search
    """
    page = create_page_canvas()
    
    # Add title
    add_title_to_page(page, f"{theme_name} Word Search")
    
    draw = ImageDraw.Draw(page)
    
    # Create grid
    grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
    placed_words = []
    
    # Place words in grid
    for word in words[:10]:  # Limit to 10 words
        word = word.upper()
        placed = False
        attempts = 0
        
        while not placed and attempts < 50:
            attempts += 1
            # Random direction: 0=horizontal, 1=vertical
            direction = random.choice([0, 1])
            
            if direction == 0:  # Horizontal
                if len(word) <= grid_size:
                    row = random.randint(0, grid_size - 1)
                    col = random.randint(0, grid_size - len(word))
                    
                    # Check if space is available
                    can_place = True
                    for i in range(len(word)):
                        if grid[row][col + i] != '' and grid[row][col + i] != word[i]:
                            can_place = False
                            break
                    
                    if can_place:
                        for i in range(len(word)):
                            grid[row][col + i] = word[i]
                        placed_words.append((word, row, col, direction))
                        placed = True
            
            else:  # Vertical
                if len(word) <= grid_size:
                    row = random.randint(0, grid_size - len(word))
                    col = random.randint(0, grid_size - 1)
                    
                    # Check if space is available
                    can_place = True
                    for i in range(len(word)):
                        if grid[row + i][col] != '' and grid[row + i][col] != word[i]:
                            can_place = False
                            break
                    
                    if can_place:
                        for i in range(len(word)):
                            grid[row + i][col] = word[i]
                        placed_words.append((word, row, col, direction))
                        placed = True
    
    # Fill empty spaces with random letters
    for row in range(grid_size):
        for col in range(grid_size):
            if grid[row][col] == '':
                grid[row][col] = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    # Draw grid
    cell_size = 60
    grid_total_size = cell_size * grid_size
    grid_start_x = (PAGE_WIDTH - grid_total_size) // 2
    grid_start_y = 400
    
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
        
        for row in range(grid_size):
            for col in range(grid_size):
                x = grid_start_x + (col * cell_size)
                y = grid_start_y + (row * cell_size)
                
                # Draw cell border
                draw.rectangle(
                    [x, y, x + cell_size, y + cell_size],
                    outline=(0, 0, 0, 255),
                    width=2
                )
                
                # Draw letter
                letter = grid[row][col]
                bbox = draw.textbbox((0, 0), letter, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = x + (cell_size - text_width) // 2
                text_y = y + (cell_size - text_height) // 2
                draw.text((text_x, text_y), letter, fill=(0, 0, 0, 255), font=font)
    except:
        pass
    
    # Draw word list
    word_list_y = grid_start_y + grid_total_size + 50
    word_spacing = 150
    
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
        
        for idx, word in enumerate(words[:10]):
            col_num = idx % 5
            row_num = idx // 5
            
            x = MARGINS['page'] + (col_num * word_spacing)
            y = word_list_y + (row_num * 40)
            
            draw.text((x, y), word.upper(), fill=(0, 0, 0, 255), font=font)
    except:
        pass
    
    add_page_border(page)
    add_footer(page)
    
    return page


def generate_word_search_set(word_lists, theme_name='Theme', grid_size=10,
                             output_dir='output'):
    """
    Generate a set of word searches.
    
    Args:
        word_lists: List of word lists (one puzzle per list)
        theme_name: Theme name
        grid_size: Grid size
        output_dir: Output directory
        
    Returns:
        list: Generated pages
    """
    pages = []
    
    for words in word_lists:
        page = generate_word_search(words, theme_name, grid_size, show_answers=False)
        pages.append(page)
        
        # Optionally add answer key
        answer_page = generate_word_search(words, f"{theme_name} (Answer Key)", grid_size, show_answers=True)
        pages.append(answer_page)
    
    # Save PDF
    output_path = f"{output_dir}/{theme_name}_Word_Search.pdf"
    save_images_as_pdf(pages, output_path, title=f"{theme_name} Word Search")
    
    return pages


if __name__ == "__main__":
    print("Word Search Generator")
    print("Use generate_word_search() or generate_word_search_set()")
