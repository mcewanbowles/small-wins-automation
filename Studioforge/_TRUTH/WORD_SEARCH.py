"""
WORD SEARCH GENERATOR - 4 LEVELS
Creates 4 differentiated levels + answer key (5 pages total)
Same words and images across all levels

Level 1: Symbol padding (●■▲★), horizontal/vertical only - Supported
Level 2: Letter padding, horizontal/vertical only - Developing
Level 3: Letter padding, includes diagonal - Independent
Level 4: Smaller cells, tighter grid - Extended
+ Answer Key page
"""

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import random
import string
import json
from datetime import datetime
from utils.sws_design import LEVEL_COLORS, generate_internal_cover_page, shrink_font_to_fit_with_pt, normalize_text, apply_small_wins_frame, draw_aac_strip
from utils.UNIVERSAL_STANDARDS import clean_label, SWS_TEAL, SWS_NAVY
from utils.qa import assess_files

# Page dimensions
PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

# Colors
TITLE_BLUE = SWS_TEAL
NAVY_BLUE = SWS_NAVY
GRID_GRAY = "#666666"  # Darker grid lines
CELL_BG = "#FFFFFF"
HIGHLIGHT_YELLOW = "#FFEB3B"
PURPLE = SWS_TEAL  # For decorative corner accents

# Simple shapes for padding (Level 1)
PADDING_SYMBOLS = ['●', '■', '▲', '★', '♦', '○', '□', '△']

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    paths = (
        [
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def load_fonts():
    scale = DPI / 72
    fonts = {}
    fonts['title'] = _load_font(int(26 * scale), bold=True)
    fonts['subtitle'] = _load_font(int(16 * scale), bold=False)
    fonts['level'] = _load_font(int(14 * scale), bold=True)
    fonts['grid'] = _load_font(int(18 * scale), bold=True)
    fonts['grid_small'] = _load_font(int(14 * scale), bold=True)
    fonts['word_list'] = _load_font(int(14 * scale), bold=True)
    fonts['label'] = _load_font(int(12 * scale), bold=False)
    fonts['footer'] = _load_font(int(12 * scale), bold=False)
    fonts['copyright'] = _load_font(int(8 * scale), bold=False)
    return fonts


def _validate_images_folder(images_folder: str) -> None:
    p = Path(images_folder)
    if not p.exists():
        raise FileNotFoundError(f"Images folder not found: {images_folder}")
    sp = str(p).lower()
    if "_tlot_archived_duplicate" in sp:
        raise ValueError(
            f"Images folder is inside archived duplicate: {p}. Use assets/themes/<slug>/activity_images/."
        )
    if any(k in sp for k in ["aac_core", "aac_core_text", "global"]):
        raise ValueError(
            f"Word Search must not read from AAC core/global: {p}. Use assets/themes/<slug>/activity_images/."
        )
    files = [f for f in p.glob("*.png") if f.is_file() and not f.name.startswith(".")]
    if len(files) < 4:
        raise ValueError(f"Too few images in {p} — found {len(files)}, need at least 4.")


def _theme_dir_for_images(images_folder: str) -> Path:
    path = Path(images_folder).resolve()
    if path.name == "icons" and path.parent.name == ".sf_build":
        return path.parent.parent
    return path.parent


def _prepare_icon(image: Image.Image) -> Image.Image:
    icon = image.convert("RGBA")
    edge = max(2, int(icon.width * 0.02))
    icon = icon.crop((edge, edge, icon.width - edge, icon.height - edge))
    pixels = []
    source = icon.get_flattened_data() if hasattr(icon, "get_flattened_data") else icon.getdata()
    for red, green, blue, alpha in source:
        neutral = max(red, green, blue) - min(red, green, blue) < 12 and (red + green + blue) / 3 > 150
        pixels.append((red, green, blue, 0 if neutral else alpha))
    icon.putdata(pixels)
    bounds = icon.getchannel("A").getbbox()
    return icon.crop(bounds) if bounds else icon


def create_word_search_grid(words, grid_size=8, use_symbols=False, allow_diagonal=False, isolate_words=False):
    """
    Create a word search grid
    isolate_words: If True, words won't touch other letters (for Level 1 beginner)
    """
    # Use larger grid when isolating words to ensure all fit
    if isolate_words:
        grid_size = max(grid_size, 9)
    
    grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]
    word_positions = {}

    def has_adjacent_letter(row, col, grid, grid_size):
        """Check if any adjacent cell has a letter (only orthogonal, not diagonal)"""
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < grid_size and 0 <= nc < grid_size:
                if grid[nr][nc] is not None and grid[nr][nc] not in PADDING_SYMBOLS:
                    return True
        return False

    def valid_dirs():
        dirs = [(0, 1), (1, 0)]  # H, V
        if allow_diagonal:
            dirs += [(1, 1), (-1, 1)]  # down-right, up-right
        return dirs

    sorted_words = sorted(words, key=len, reverse=True)

    # Deterministic placement with limited restarts to guarantee all words are included
    max_restarts = 30
    for restart in range(max_restarts):
        # reset grid and positions on each restart
        for r in range(grid_size):
            for c in range(grid_size):
                grid[r][c] = None
        word_positions.clear()

        success = True
        for word in sorted_words:
            w = word.upper()
            candidates: list[tuple[int, int, int, int]] = []
            for dr, dc in valid_dirs():
                # compute start bounds depending on direction
                min_row = 0 if dr >= 0 else (len(w) - 1)
                max_row = (grid_size - len(w)) if dr > 0 else (grid_size - 1)
                min_col = 0
                max_col = (grid_size - len(w)) if dc > 0 else (grid_size - 1)
                for row in range(min_row, max_row + 1):
                    for col in range(min_col, max_col + 1):
                        # boundary check for negative dr already handled by min_row
                        ok = True
                        for i, ch in enumerate(w):
                            rr = row + dr * i
                            cc = col + dc * i
                            if not (0 <= rr < grid_size and 0 <= cc < grid_size):
                                ok = False
                                break
                            cell = grid[rr][cc]
                            if cell is not None and cell != ch:
                                ok = False
                                break
                            if isolate_words and has_adjacent_letter(rr, cc, grid, grid_size) and cell is None:
                                ok = False
                                break
                        if ok:
                            candidates.append((row, col, dr, dc))

            if not candidates:
                success = False
                break

            # Choose a random valid placement for variety
            row, col, dr, dc = random.choice(candidates)
            positions = []
            for i, ch in enumerate(w):
                rr = row + dr * i
                cc = col + dc * i
                grid[rr][cc] = ch
                positions.append((rr, cc))
            word_positions[word] = positions

        if success:
            break

    if not success:
        # As a last resort (extremely unlikely with 4 words), place any remaining words sequentially horizontally
        for word in sorted_words:
            if word in word_positions:
                continue
            w = word.upper()
            placed = False
            for row in range(grid_size):
                for col in range(0, grid_size - len(w) + 1):
                    ok = True
                    for i, ch in enumerate(w):
                        if grid[row][col + i] not in (None, ch):
                            ok = False
                            break
                    if ok:
                        positions = []
                        for i, ch in enumerate(w):
                            grid[row][col + i] = ch
                            positions.append((row, col + i))
                        word_positions[word] = positions
                        placed = True
                        break
                if placed:
                    break

    # Fill empty cells
    for row in range(grid_size):
        for col in range(grid_size):
            if grid[row][col] is None:
                if use_symbols:
                    grid[row][col] = random.choice(PADDING_SYMBOLS)
                else:
                    grid[row][col] = random.choice(string.ascii_uppercase)

    return grid, word_positions


def verify_grid_solvable(grid: list[list[str]], words: list[str]) -> tuple[bool, list[str]]:
    """Verify every word can be found in the grid in one of 8 directions.

    Returns (all_found, list_of_missing_words). This is the automated
    solvability check that prevents shipping an unsolvable puzzle.
    """
    size = len(grid)
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    missing: list[str] = []

    for word in words:
        w = word.upper()
        found = False
        for row in range(size):
            for col in range(size):
                for dr, dc in directions:
                    ok = True
                    for i, ch in enumerate(w):
                        rr = row + dr * i
                        cc = col + dc * i
                        if not (0 <= rr < size and 0 <= cc < size):
                            ok = False
                            break
                        cell = grid[rr][cc]
                        if cell != ch:
                            ok = False
                            break
                    if ok:
                        found = True
                        break
                if found:
                    break
            if found:
                break
        if not found:
            missing.append(word)

    return (len(missing) == 0, missing)


def create_word_search_page(words, theme_images, theme_names, level, page_num,
                            pack_code, theme_name, total_pages=5, grid_size=8, use_symbols=False, 
                            allow_diagonal=False, cell_size_override=None, fit_warnings: list[str] | None = None):
    """Create a single word search page"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    level_color = LEVEL_COLORS.get(level, LEVEL_COLORS[1])
    
    # PROFESSIONAL DESIGN ELEMENT: Subtle page border with accent
    border_margin = int(15 * scale)
    border_radius = int(20 * scale)
    
    # Outer border (per-level accent)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, img_height - border_margin],
        radius=border_radius,
        outline=hex_to_rgb(level_color),
        width=int(2 * scale)
    )
    
    # Top accent stripe (header must always be teal per universal standard)
    accent_height = int(8 * scale)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, border_margin + accent_height],
        radius=border_radius,
        fill=hex_to_rgb(TITLE_BLUE),
        outline=None
    )

    # Level badge — top right
    level_labels = {1: 'Supported', 2: 'Developing', 3: 'Independent', 4: 'Extended'}
    
    # Small decorative corner elements
    corner_size = int(25 * scale)
    corner_offset = border_margin + int(5 * scale)
    
    # Bottom left corner accent
    draw.arc(
        [corner_offset, img_height - corner_offset - corner_size, 
         corner_offset + corner_size, img_height - corner_offset],
        start=90, end=180,
        fill=hex_to_rgb(PURPLE),
        width=int(3 * scale)
    )
    
    # Bottom right corner accent  
    draw.arc(
        [img_width - corner_offset - corner_size, img_height - corner_offset - corner_size,
         img_width - corner_offset, img_height - corner_offset],
        start=0, end=90,
        fill=hex_to_rgb(PURPLE),
        width=int(3 * scale)
    )
    
    margin = int(40 * scale)
    
    # Title (shrink-to-fit)
    title_text = normalize_text(f"{theme_name} Word Search")
    usable_title_w = img_width - 2 * border_margin - int(10 * scale)
    title_font, title_pt = shrink_font_to_fit_with_pt(
        title_text,
        base_pt=26,
        max_width_px=usable_title_w,
        bold=True,
        brand="poppins",
        min_pt=16,
    )
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (img_width - title_width) // 2
    title_y = int(20 * scale)
    draw.text((title_x, title_y), title_text, fill=hex_to_rgb(TITLE_BLUE), font=title_font)
    if fit_warnings is not None and title_pt <= 20:
        fit_warnings.append(f"Title shrunk to {title_pt}pt on page {page_num}: '{title_text}'")
    
    # Level indicator
    level_descriptions = {
        1: "Level 1 - Supported (Symbol Background)",
        2: "Level 2 - Developing (Letters, No Diagonals)",
        3: "Level 3 - Independent (Letters + Diagonals)",
        4: "Level 4 - Extended (Text-only, diagonals)"
    }
    level_text = level_descriptions.get(level, f"Level {level}")
    level_text = normalize_text(level_text)
    usable_level_w = img_width - 2 * border_margin - int(20 * scale)
    level_font, level_pt = shrink_font_to_fit_with_pt(
        level_text,
        base_pt=14,
        max_width_px=usable_level_w,
        bold=True,
        brand="poppins",
        min_pt=10,
    )
    level_bbox = draw.textbbox((0, 0), level_text, font=level_font)
    level_width = level_bbox[2] - level_bbox[0]
    level_x = (img_width - level_width) // 2
    level_y = int(50 * scale)
    draw.text((level_x, level_y), level_text, fill=hex_to_rgb(NAVY_BLUE), font=level_font)
    if fit_warnings is not None and level_pt <= 12:
        fit_warnings.append(f"Level line shrunk to {level_pt}pt on page {page_num}: '{level_text}'")
    
    # Subtitle — use level-specific directions per brief
    if use_symbols and not allow_diagonal:
        subtitle_text = "Find the words. Symbols background. Horizontal/Vertical only."
    elif (not use_symbols) and not allow_diagonal:
        subtitle_text = "Find the words. Letters only. Horizontal/Vertical only."
    else:
        subtitle_text = "Find the words. Letters + Diagonals."
    subtitle_text = normalize_text(subtitle_text)
    usable_sub_w = img_width - 2 * border_margin - int(20 * scale)
    sub_font, sub_pt = shrink_font_to_fit_with_pt(
        subtitle_text,
        base_pt=16,
        max_width_px=usable_sub_w,
        bold=False,
        brand="poppins",
        min_pt=10,
    )
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=sub_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (img_width - subtitle_width) // 2
    subtitle_y = int(72 * scale)
    draw.text((subtitle_x, subtitle_y), subtitle_text, fill=hex_to_rgb(NAVY_BLUE), font=sub_font)
    if fit_warnings is not None and sub_pt <= 12:
        fit_warnings.append(f"Subtitle shrunk to {sub_pt}pt on page {page_num}: '{subtitle_text}'")
    
    # Create grid - isolate words when using symbols (Level 1)
    grid, word_positions = create_word_search_grid(words, grid_size, use_symbols, allow_diagonal, isolate_words=use_symbols)
    # Update grid_size to the actual grid dimensions — create_word_search_grid may
    # enlarge the grid (e.g. 8→9) when isolate_words=True. Using the original value
    # for rendering would silently drop the last row(s), making words unsolvable.
    grid_size = len(grid)
    
    # Draw grid - with more space from subtitle
    grid_start_y = int(115 * scale)
    cell_size = cell_size_override if cell_size_override else int(50 * scale)  # Bigger cells
    grid_width = grid_size * cell_size
    grid_start_x = (img_width - grid_width) // 2
    
    grid_font = fonts['grid'] if cell_size >= int(40 * scale) else fonts['grid_small']
    
    # Draw outer border around entire grid (dark navy)
    border_padding = int(2 * scale)
    draw.rectangle(
        [grid_start_x - border_padding, grid_start_y - border_padding,
         grid_start_x + grid_width + border_padding, grid_start_y + (grid_size * cell_size) + border_padding],
        outline=hex_to_rgb(NAVY_BLUE),
        fill=None,
        width=int(3 * scale)
    )
    
    for row in range(grid_size):
        for col in range(grid_size):
            cell_x = grid_start_x + (col * cell_size)
            cell_y = grid_start_y + (row * cell_size)
            
            draw.rectangle(
                [cell_x, cell_y, cell_x + cell_size, cell_y + cell_size],
                outline=hex_to_rgb(GRID_GRAY),
                fill=hex_to_rgb(CELL_BG),
                width=2  # Thicker borders
            )
            
            content = grid[row][col]
            if content in PADDING_SYMBOLS:
                inset = int(cell_size * 0.36)
                shape_box = [cell_x + inset, cell_y + inset, cell_x + cell_size - inset, cell_y + cell_size - inset]
                shape_index = PADDING_SYMBOLS.index(content) % 4
                if shape_index == 0:
                    draw.ellipse(shape_box, fill=hex_to_rgb(GRID_GRAY))
                elif shape_index == 1:
                    draw.rectangle(shape_box, fill=hex_to_rgb(GRID_GRAY))
                elif shape_index == 2:
                    draw.polygon([(cell_x + cell_size // 2, shape_box[1]), (shape_box[0], shape_box[3]), (shape_box[2], shape_box[3])], fill=hex_to_rgb(GRID_GRAY))
                else:
                    draw.polygon([(cell_x + cell_size // 2, shape_box[1]), (shape_box[2], cell_y + cell_size // 2), (cell_x + cell_size // 2, shape_box[3]), (shape_box[0], cell_y + cell_size // 2)], fill=hex_to_rgb(GRID_GRAY))
            else:
                content_bbox = draw.textbbox((0, 0), content, font=grid_font)
                content_width = content_bbox[2] - content_bbox[0]
                content_height = content_bbox[3] - content_bbox[1]
                content_x = cell_x + (cell_size - content_width) // 2 - content_bbox[0]
                content_y = cell_y + (cell_size - content_height) // 2 - content_bbox[1]
                draw.text((content_x, content_y), content, fill=hex_to_rgb(NAVY_BLUE), font=grid_font)
    
    # Word list section - aligned with grid
    word_list_y = grid_start_y + (grid_size * cell_size) + int(35 * scale)
    
    label_text = "Find these words:"
    label_bbox = draw.textbbox((0, 0), label_text, font=fonts['label'])
    label_width = label_bbox[2] - label_bbox[0]
    label_x = (img_width - label_width) // 2
    draw.text((label_x, word_list_y), label_text, fill=hex_to_rgb(NAVY_BLUE), font=fonts['label'])
    
    word_list_y += int(30 * scale)
    
    # Calculate layout - align with grid width
    num_words = len(words)
    cols = 2
    icon_size = int(45 * scale)
    checkbox_size = int(16 * scale)
    
    # Use grid width for alignment
    entry_width = grid_width // 2
    entry_height = int(55 * scale)
    
    # Start at same x as grid
    list_start_x = grid_start_x
    
    for idx, word in enumerate(words):
        col = idx % cols
        row = idx // cols
        
        entry_x = list_start_x + (col * entry_width)
        entry_y = word_list_y + (row * entry_height)
        
        # Center content within each entry
        content_start_x = entry_x + int(10 * scale)
        
        # Checkbox
        draw.rectangle(
            [content_start_x, entry_y + (icon_size - checkbox_size) // 2,
             content_start_x + checkbox_size, entry_y + (icon_size - checkbox_size) // 2 + checkbox_size],
            outline=hex_to_rgb(NAVY_BLUE),
            fill='white',
            width=2
        )
        
        # Image icon
        if level != 4 and idx < len(theme_images):
            img = _prepare_icon(theme_images[idx])
            if img.width > 0 and img.height > 0:
                ratio = min(icon_size / img.width, icon_size / img.height)
                img = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), Image.Resampling.LANCZOS)
            img_x = content_start_x + checkbox_size + int(8 * scale)
            img_y = entry_y + (icon_size - img.height) // 2
            page.paste(img, (img_x, img_y), img if img.mode == 'RGBA' else None)
        
        # Word text - show the actual word in the grid
        word_text = word.upper()
        word_x = content_start_x + checkbox_size + (icon_size + int(20 * scale) if level != 4 else int(12 * scale))
        word_y = entry_y + (icon_size - int(14 * scale)) // 2
        draw.text((word_x, word_y), word_text, fill=hex_to_rgb(NAVY_BLUE), font=fonts['word_list'])
    try:
        pass
    except Exception:
        pass
    
    # Universal footer (consistent format, year, and clearance). Avoid duplicating pack code by excluding it from footer_title.
    apply_small_wins_frame(
        page,
        product_title="Word Search",
        subtitle="",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        draw_accent_strip=False,
        draw_header=False,
        draw_subtitle=False,
        draw_footer=True,
        footer_title=f"{theme_name} | Word Search",
        strand_key="WS",
    )

    return page, grid, word_positions


def create_answer_key_page(words, all_grids, all_positions, theme_name, pack_code, page_num: int = 5, total_pages: int = 5, fit_warnings: list[str] | None = None):
    """Create answer key showing all levels"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    # PROFESSIONAL DESIGN ELEMENT: Subtle page border with accent
    border_margin = int(15 * scale)
    border_radius = int(20 * scale)
    
    # Outer border (subtle gray)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, img_height - border_margin],
        radius=border_radius,
        outline='#D0D0D0',
        width=int(2 * scale)
    )
    
    # Top accent stripe (theme color)
    accent_height = int(8 * scale)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, border_margin + accent_height],
        radius=border_radius,
        fill=hex_to_rgb(TITLE_BLUE),
        outline=None
    )
    
    # Small decorative corner elements
    corner_size = int(25 * scale)
    corner_offset = border_margin + int(5 * scale)
    
    # Bottom left corner accent
    draw.arc(
        [corner_offset, img_height - corner_offset - corner_size, 
         corner_offset + corner_size, img_height - corner_offset],
        start=90, end=180,
        fill=hex_to_rgb(PURPLE),
        width=int(3 * scale)
    )
    
    # Bottom right corner accent  
    draw.arc(
        [img_width - corner_offset - corner_size, img_height - corner_offset - corner_size,
         img_width - corner_offset, img_height - corner_offset],
        start=0, end=90,
        fill=hex_to_rgb(PURPLE),
        width=int(3 * scale)
    )
    
    # Title (shrink-to-fit)
    title_text = normalize_text(f"{theme_name} Word Search - ANSWER KEY")
    usable_title_w = img_width - 2 * border_margin - int(10 * scale)
    title_font, title_pt = shrink_font_to_fit_with_pt(
        title_text,
        base_pt=26,
        max_width_px=usable_title_w,
        bold=True,
        brand="poppins",
        min_pt=16,
    )
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (img_width - title_width) // 2
    title_y = int(20 * scale)
    draw.text((title_x, title_y), title_text, fill=hex_to_rgb(TITLE_BLUE), font=title_font)
    if fit_warnings is not None and title_pt <= 20:
        fit_warnings.append(f"Answer key title shrunk to {title_pt}pt on page {page_num}: '{title_text}'")
    
    # Draw 4 mini grids (2x2 layout) - ALL SAME VISUAL SIZE
    # Each grid will be scaled to fit the same box size
    target_grid_pixel_size = int(170 * scale)  # Same visual size for all grids
    
    # Calculate positions for 2x2 grid layout - CENTERED ON PAGE
    h_spacing = int(50 * scale)  # Horizontal space between grids (increased)
    v_spacing = int(70 * scale)  # Vertical space between rows (increased for better balance)
    
    total_row_width = 2 * target_grid_pixel_size + h_spacing
    row_start_x = (img_width - total_row_width) // 2
    
    # BETTER VERTICAL CENTERING - calculate to center in available space
    # Available space: title ends ~60pt, footer starts ~680pt = 620pt available
    # Total height needed: (170 + label) * 2 + 70 spacing = ~460pt
    # To center: start at (620 - 460) / 2 + 60 = ~140pt
    start_y = int(140 * scale)  # MOVED DOWN for better centering
    
    for level_idx, (grid, positions) in enumerate(zip(all_grids, all_positions)):
        actual_grid_size = len(grid)
        
        # Calculate cell size to make this grid fill the target size
        mini_cell_size = target_grid_pixel_size // actual_grid_size
        actual_pixel_size = mini_cell_size * actual_grid_size
        
        col = level_idx % 2
        row_num = level_idx // 2
        
        # Fixed positions for perfect alignment
        grid_x = row_start_x + col * (target_grid_pixel_size + h_spacing)
        grid_y = start_y + row_num * (target_grid_pixel_size + v_spacing)
        
        # Center actual grid within target area (for any small rounding differences)
        offset_x = (target_grid_pixel_size - actual_pixel_size) // 2
        offset_y = (target_grid_pixel_size - actual_pixel_size) // 2
        
        # Level label - centered above grid box
        level_label = f"Level {level_idx + 1}"
        label_bbox = draw.textbbox((0, 0), level_label, font=fonts['level'])
        label_width = label_bbox[2] - label_bbox[0]
        label_x = grid_x + (target_grid_pixel_size - label_width) // 2
        draw.text((label_x, grid_y - int(22 * scale)), level_label, 
                  fill=hex_to_rgb(NAVY_BLUE), font=fonts['level'])
        
        # Highlighting: show solution paths for ALL levels in the answer key
        highlight_cells = set()
        for word, pos_list in positions.items():
            for pos in pos_list:
                highlight_cells.add(pos)
        
        # Draw outer border (same size for all)
        draw.rectangle(
            [grid_x + offset_x - 2, grid_y + offset_y - 2, 
             grid_x + offset_x + actual_pixel_size + 2, grid_y + offset_y + actual_pixel_size + 2],
            outline=hex_to_rgb(NAVY_BLUE),
            fill=None,
            width=2
        )
        
        # Draw cells
        for r in range(actual_grid_size):
            for c in range(actual_grid_size):
                cell_x = grid_x + offset_x + (c * mini_cell_size)
                cell_y = grid_y + offset_y + (r * mini_cell_size)
                
                fill_color = HIGHLIGHT_YELLOW if (r, c) in highlight_cells else CELL_BG
                
                draw.rectangle(
                    [cell_x, cell_y, cell_x + mini_cell_size, cell_y + mini_cell_size],
                    outline=hex_to_rgb(GRID_GRAY),
                    fill=fill_color,
                    width=1
                )
                
                content = grid[r][c]
                if content not in PADDING_SYMBOLS:
                    # Scale font size based on cell size
                    font_size = max(7, mini_cell_size // 7)
                    try:
                        small_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(font_size * scale))
                    except:
                        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(font_size * scale))
                    
                    content_bbox = draw.textbbox((0, 0), content, font=small_font)
                    content_width = content_bbox[2] - content_bbox[0]
                    content_height = content_bbox[3] - content_bbox[1]
                    content_x = cell_x + (mini_cell_size - content_width) // 2
                    content_y = cell_y + (mini_cell_size - content_height) // 2 - int(1 * scale)
                    draw.text((content_x, content_y), content, fill=hex_to_rgb(NAVY_BLUE), font=small_font)
    
    # Word list - centered
    word_list_y = img_height - int(60 * scale)
    words_text = "Words: " + ", ".join([clean_label(w).upper() for w in words])
    words_bbox = draw.textbbox((0, 0), words_text, font=fonts['word_list'])
    words_width = words_bbox[2] - words_bbox[0]
    words_x = (img_width - words_width) // 2
    draw.text((words_x, word_list_y), words_text, fill=hex_to_rgb(NAVY_BLUE), font=fonts['word_list'])
    
    # Universal footer (consistent format, year, and clearance). Avoid duplicating pack code by excluding it from footer_title.
    apply_small_wins_frame(
        page,
        product_title="Word Search",
        subtitle="",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        draw_accent_strip=False,
        draw_header=False,
        draw_subtitle=False,
        draw_footer=True,
        footer_title=f"{theme_name} | Word Search Answer Key",
        strand_key="WS",
    )

    return page


def generate_word_search(images_folder, pack_code="WAN1-A", theme_name="Winter Animals"):
    """Generate word search activity with 4 levels"""
    
    print(f"\n{'='*70}")
    print(f"  🔍 GENERATING WORD SEARCH (4 LEVELS): {pack_code}")
    print(f"  Theme: {theme_name}")
    print(f"{'='*70}\n")
    
    try:
        _validate_images_folder(images_folder)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    images_path = Path(images_folder)
    theme_dir = _theme_dir_for_images(images_folder)
    source = theme_dir / "config" / "word_search.json"
    data = json.loads(source.read_text(encoding="utf-8")) if source.exists() else None
    entries = data.get("words") if isinstance(data, dict) else None
    if not entries or not 4 <= len(entries) <= 8 or data.get("reading_rope") != ["Sight Recognition", "Vocabulary"]:
        print(f"❌ Reviewed Word Search data is missing or invalid: {source}")
        return False
    
    print(f"📥 Loading theme images...")
    theme_images = []
    theme_names_list = []
    words = []
    
    for entry in entries:
        word = str(entry.get("word") or "").strip().lower()
        image_key = str(entry.get("image_key") or "").strip()
        name = str(entry.get("label") or "").strip()
        img_file = images_path / f"{image_key}.png"
        if not word.isalpha() or len(word) > 8 or not name or not img_file.exists():
            print(f"❌ Invalid Word Search entry: {entry}")
            return False
        img = Image.open(img_file).convert("RGBA")
        theme_images.append(img)
        theme_names_list.append(name)
        words.append(word)
        print(f"   ✅ {name} → {word.upper()}")
    
    print()
    
    # Guardrailed output path: Studioforge/OUTPUT/{pack_code}
    out_dir = theme_dir / "OUTPUT"
    if "_TLOT_ARCHIVED_DUPLICATE" in str(out_dir):
        print(f"❌ ERROR: Output path points into archived duplicate: {out_dir}")
        return False
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📄 Generating word search pages...\n")
    
    # Internal cover page as Page 1
    saved_pages: list[Image.Image] = []
    text_fit_warnings: list[str] = []
    page_count = 5  # 4 levels + 1 answer key
    total_pages = page_count
    page_running = 1
    
    levels_config = [
        {"level": 1, "grid_size": 8, "use_symbols": True, "allow_diagonal": False, "cell_size": int(42 * DPI / 72)},
        {"level": 2, "grid_size": 8, "use_symbols": False, "allow_diagonal": False, "cell_size": None},
        {"level": 3, "grid_size": 9, "use_symbols": False, "allow_diagonal": True, "cell_size": int(42 * DPI / 72)},
        {"level": 4, "grid_size": 10, "use_symbols": False, "allow_diagonal": True, "cell_size": int(35 * DPI / 72)},
    ]
    
    all_grids = []
    all_positions = []
    
    for config in levels_config:
        print(f"   Level {config['level']}...")
        
        page, grid, positions = create_word_search_page(
            words, theme_images, theme_names_list,
            config['level'], page_running,
            pack_code, theme_name, total_pages,
            grid_size=config['grid_size'],
            use_symbols=config['use_symbols'],
            allow_diagonal=config['allow_diagonal'],
            cell_size_override=config['cell_size'],
            fit_warnings=text_fit_warnings,
        )
        
        saved_pages.append(page)
        all_grids.append(grid)
        all_positions.append(positions)

        # Solvability check — refuse to ship an unsolvable puzzle
        solvable, missing = verify_grid_solvable(grid, words)
        if not solvable:
            print(f"   ❌ Level {config['level']} FAILED solvability check — missing: {missing}")
            return False

        page_running += 1
    
    print(f"   Answer Key...")
    answer_page = create_answer_key_page(words, all_grids, all_positions, theme_name, pack_code, page_num=page_running, total_pages=total_pages, fit_warnings=text_fit_warnings)
    saved_pages.append(answer_page)
    
    print(f"\n   ✅ 6 pages generated\n")
    
    print(f"📄 Creating PDF...")
    pdf_path = str(out_dir / f"{pack_code}_WordSearch_COLOR.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    for page in saved_pages:
        img_buffer = io.BytesIO()
        page.save(img_buffer, format='PNG', dpi=(DPI, DPI))
        img_buffer.seek(0)
        c.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    
    c.save()
    print(f"   ✅ {pdf_path}\n")
    
    print(f"🖤 Creating B&W version...")
    bw_pdf = str(out_dir / f"{pack_code}_WordSearch_BW.pdf")
    c_bw = canvas.Canvas(bw_pdf, pagesize=letter)
    
    for page in saved_pages:
        gray_page = page.convert('L').convert('RGB')
        img_buffer = io.BytesIO()
        gray_page.save(img_buffer, format='PNG', dpi=(DPI, DPI))
        img_buffer.seek(0)
        c_bw.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c_bw.showPage()
    
    c_bw.save()
    print(f"   ✅ {bw_pdf}\n")
    
    print(f"🔒 Creating PREVIEW...")
    preview_pdf = str(out_dir / f"{pack_code}_WordSearch_PREVIEW.pdf")
    c_preview = canvas.Canvas(preview_pdf, pagesize=letter)
    
    img_buffer = io.BytesIO()
    saved_pages[1].save(img_buffer, format='PNG', dpi=(DPI, DPI))
    img_buffer.seek(0)
    c_preview.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
    
    c_preview.saveState()
    c_preview.setFont("Helvetica-Bold", 140)
    c_preview.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
    c_preview.translate(PAGE_WIDTH/2, PAGE_HEIGHT/2)
    c_preview.rotate(45)
    c_preview.drawCentredString(0, 0, "PREVIEW")
    c_preview.restoreState()
    c_preview.showPage()
    
    c_preview.save()
    print(f"   ✅ {preview_pdf}\n")
    
    print(f"🖼️  Creating thumbnails...")
    thumb_folder = out_dir / "thumbnails"
    thumb_folder.mkdir(parents=True, exist_ok=True)
    
    thumb = saved_pages[1].copy()
    thumb.thumbnail((500, 647), Image.Resampling.LANCZOS)
    thumb_path = thumb_folder / f"{pack_code}_WordSearch_thumb.png"
    thumb.save(thumb_path, "PNG")
    print(f"   ✅ Thumbnail created\n")
    
    # BuildResult manifest with warnings
    try:
        try:
            warnings = assess_files(
                product_name="Word Search",
                color_pdf=pdf_path,
                bw_pdf=bw_pdf,
                preview_pdf=preview_pdf,
                expected_pages=None,
            )
        except Exception:
            warnings = []
        try:
            warnings.extend(text_fit_warnings)
        except Exception:
            pass
        thumbs_dir = out_dir / "thumbnails"
        thumbs = [str(thumbs_dir / f"{pack_code}_WordSearch_thumb.png")]
        manifest = {
            "schema_version": 1,
            "status": "pilot_review",
            "product_name": "Differentiated Word Search",
            "slug": theme_dir.name,
            "pack_code": pack_code,
            "page_count": len(saved_pages),
            "reading_rope": ["Sight Recognition", "Vocabulary"],
            "teacher_review_required": True,
            "source": str(source),
            "files": {
                "color_pdf": pdf_path,
                "bw_pdf": bw_pdf,
                "preview_pdf": preview_pdf,
                "thumbnails": thumbs,
            },
            "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": warnings},
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{pack_code}_WordSearch_BuildResult.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass
    
    print(f"📝 Creating TPT description...")
    
    description = f"""WORD SEARCH 4 LEVELS - {theme_name.upper()} - {pack_code}

🔍 DIFFERENTIATED WORD SEARCH with 4 Difficulty Levels!

✨ WHAT'S INCLUDED:
• 4 Word Search pages (4 differentiated levels)
• 1 Answer Key page
• Same words across all levels
• Picture icons next to each word
• B&W version included

📊 DIFFICULTY LEVELS:

⭐ LEVEL 1 - BEGINNER
• Symbol padding (●■▲★) instead of letters
• Words STAND OUT clearly
• Horizontal & vertical only

⭐⭐ LEVEL 2 - EASY  
• Letter padding
• Horizontal & vertical only

⭐⭐⭐ LEVEL 3 - MEDIUM
• Letter padding
• Includes DIAGONAL words

⭐⭐⭐⭐ LEVEL 4 - INDEPENDENT READER
• Text-only focus
• Diagonal words included

🎯 WORDS: {', '.join([w.upper() for w in words])}

© 2026 Small Wins Studio
"""
    
    desc_path = str(out_dir / f"{pack_code}_WordSearch_TPT_Description.txt")
    with open(desc_path, 'w', encoding='utf-8') as f:
        f.write(description)
    print(f"   ✅ {desc_path}\n")
    
    print(f"📦 Creating ZIP package...")
    zip_path = str(out_dir / f"{pack_code}_WordSearch_Package.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(pdf_path, f"{pack_code}_WordSearch/{pack_code}_WordSearch_5Pages.pdf")
        zipf.write(bw_pdf, f"{pack_code}_WordSearch/{pack_code}_WordSearch_5Pages_BW.pdf")
    
    print(f"   ✅ {zip_path}\n")
    
    print(f"{'='*70}")
    print(f"  ✅ WORD SEARCH (4 LEVELS) COMPLETE!")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    import sys
    
    pack_code = sys.argv[1] if len(sys.argv) > 1 else "WAN1-A"
    theme_name = sys.argv[2] if len(sys.argv) > 2 else "Winter Animals"
    
    success = generate_word_search("images", pack_code, theme_name)
    
    if success:
        print("🎉 ALL DONE!")
    else:
        print("\n❌ FAILED - check error messages above")
        sys.exit(1)
