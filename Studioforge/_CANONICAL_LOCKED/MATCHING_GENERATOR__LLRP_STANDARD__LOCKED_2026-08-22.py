# SWS-GEN-VERSION: 2026-07-07 (see CHANGELOG.md in this pack for what changed)
"""
MATCHING GENERATOR - 4 LEVELS (Original Portrait Layout)
Creates complete matching product with progressive difficulty

LAYOUT: 2 columns (LEFT: images, RIGHT: velcro boxes) - Portrait orientation

LEVEL STRUCTURE:
- Level 1: 5 targets, 0 distractors (Errorless - all rows match)
- Level 2: 4 targets, 1 distractor 
- Level 3: 3 targets, 2 distractors
- Level 4: 1 target, 4 distractors

OUTPUT STRUCTURE (19 pages):
- Pages 1-4: Level 1 (Errorless)
- Pages 5-8: Level 2 (1 distractor)
- Pages 9-12: Level 3 (2 distractors)
- Pages 13-16: Level 4 (4 distractors)
- Page 17: Cut-out Pieces
- Pages 18-19: Storage Labels
"""

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime
from utils.preview import make_preview_pdf_from_images, save_thumbnails_from_images
import io
import importlib
import importlib.util
import random
import zipfile

import os
import json
from UNIVERSAL_STANDARDS import SWS_NAVY, SWS_TEAL, COLORS
from utils.sws_design import apply_small_wins_frame, safe_footer_inset_px

# Page settings
PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

# Colors
# Brand colours — pulled from UNIVERSAL_STANDARDS.py (single source of truth).
# NAVY_BLUE and TITLE_BLUE were previously two different, both-wrong hex values
# doing the same "brand navy text/border" job — consolidated to SWS_NAVY.
# STEEL_BLUE matches the system-wide convention in utils/UNIVERSAL_STANDARDS.py,
# which explicitly aliases STEEL_BLUE to SWS_NAVY ("remapped to brand navy").
# PURPLE (velcro-box outline accent, NOT a level indicator) mapped to SWS_TEAL
# rather than a level colour, to avoid implying "Supported level" on a box
# that has nothing to do with levels.
NAVY_BLUE = SWS_NAVY
PURPLE = SWS_TEAL
TITLE_BLUE = SWS_NAVY
LIGHT_GRAY = COLORS['light_gray']
STEEL_BLUE = SWS_NAVY

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def load_fonts():
    """Load fonts with fallbacks"""
    scale = DPI / 72
    fonts = {}
    
    try:
        fonts['title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(48 * scale))
        fonts['subtitle'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(18 * scale))
        fonts['instruction'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(16 * scale))
        fonts['footer'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(11 * scale))
        fonts['velcro'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(8 * scale))
        fonts['copyright'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(7 * scale))
        fonts['cutout_title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(36 * scale))
        fonts['storage_title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(32 * scale))
        fonts['storage_label'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(14 * scale))
        fonts['storage_small'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(10 * scale))
    except:
        fonts['title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(48 * scale))
        fonts['subtitle'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(18 * scale))
        fonts['instruction'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(16 * scale))
        fonts['footer'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(11 * scale))
        fonts['velcro'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(8 * scale))
        fonts['copyright'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(7 * scale))
        fonts['cutout_title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(36 * scale))
        fonts['storage_title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(32 * scale))
        fonts['storage_label'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(14 * scale))
        fonts['storage_small'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(10 * scale))
    
    return fonts


def create_matching_page(loaded_images, image_names, target_index, level, page_num, pack_code, theme_name, qa_warnings=None, header_icon_img=None):
    """
    Create a matching page with 2-column portrait layout.
    LEFT column: 5 image boxes (mix of target and distractors)
    RIGHT column: 5 velcro boxes (student places pieces on matching rows)
    """
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    target_image = loaded_images[target_index]
    target_name = image_names[target_index]
    
    # Level configuration
    level_config = {
        1: {"targets": 5, "distractors": 0, "name": "Errorless"},
        2: {"targets": 4, "distractors": 1, "name": "1 Distractor"},
        3: {"targets": 3, "distractors": 2, "name": "2 Distractors"},
        4: {"targets": 1, "distractors": 4, "name": "4 Distractors"}
    }
    
    config = level_config[level]
    num_targets = config["targets"]
    num_distractors = config["distractors"]
    
    # Universal frame — consistent header/footer; no level pill
    apply_small_wins_frame(
        page,
        product_title="Matching Cards",
        subtitle=f"Level {level} — {theme_name}",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=19,  # static pack size per docstring
        level=None,
        footer_title=f"{theme_name} | Matching Cards",
        show_data_strip=False,
        footer_y_offset_px=int(0.08 * DPI),
        header_left_icon=header_icon_img,
        header_left_icon_flip=False,
        header_left_icon_y_offset_px=0,
        header_height_px=int(0.92 * DPI),
        accent_margin_px=int(0.12 * DPI),
    )

    # Content area inside frame
    content_pad = int(0.44 * DPI)
    # Reduce header clearance to move activity higher (hero now lives in header)
    header_clear = int(1.15 * DPI)
    content_left = content_pad
    content_right = img_width - content_pad
    content_top = header_clear + int(0.12 * DPI)
    content_bottom = img_height - safe_footer_inset_px()

    # Instruction at top of content (compact)
    instruction_text = f"Match the {target_name}"
    instruction_bbox = draw.textbbox((0, 0), instruction_text, font=fonts['subtitle'])
    instruction_w = instruction_bbox[2] - instruction_bbox[0]
    instruction_x = content_left + (content_right - content_left - instruction_w) // 2
    draw.text((instruction_x, content_top), instruction_text, fill=hex_to_rgb(NAVY_BLUE), font=fonts['subtitle'])
    # Reference target icon just beneath the instruction (required for non-readers)
    icon_size = int(0.42 * DPI)
    target_icon = target_image.copy()
    target_icon.thumbnail((icon_size, icon_size), Image.Resampling.LANCZOS)
    icon_x = content_left + (content_right - content_left - target_icon.width) // 2
    icon_y = content_top + (instruction_bbox[3] - instruction_bbox[1]) + int(0.12 * DPI) + 10
    icon_box_padding = int(5 * scale)
    draw.rounded_rectangle(
        [icon_x - icon_box_padding, icon_y - icon_box_padding,
         icon_x + target_icon.width + icon_box_padding, icon_y + target_icon.height + icon_box_padding],
        radius=int(8 * scale),
        fill='white',
        outline=hex_to_rgb(TITLE_BLUE),
        width=int(3 * scale)
    )
    page.paste(target_icon, (icon_x, icon_y), target_icon)
    
    # Create row assignments (which rows get target vs distractors)
    row_assignments = []
    
    # Add targets
    for _ in range(num_targets):
        row_assignments.append(target_index)
    
    # Add distractors (cycle through other images)
    other_indices = [i for i in range(len(loaded_images)) if i != target_index]
    for i in range(num_distractors):
        row_assignments.append(other_indices[i % len(other_indices)])
    
    # Shuffle the assignments
    random.shuffle(row_assignments)
    
    # Box layout within content area - 2 columns, 5 rows
    grid_top = icon_y + target_icon.height + int(0.22 * DPI)
    avail_w = max(1, content_right - content_left)
    avail_h = max(1, content_bottom - grid_top)
    gap_x = int(0.35 * DPI)
    gap_y = int(0.12 * DPI)
    box_size = min(
        int((avail_w - gap_x - int(0.2 * DPI)) // 2),
        int((avail_h - 4 * gap_y) // 5)
    )
    column_spacing = gap_x
    total_width = (box_size * 2) + column_spacing
    start_x = content_left + (avail_w - total_width) // 2

    left_x = start_x
    right_x = start_x + box_size + column_spacing

    start_y = grid_top
    row_spacing = gap_y
    corner_radius = int(10 * scale)
    border_width = int(3 * scale)
    
    # Draw 5 rows
    for i in range(5):
        y = start_y + i * (box_size + row_spacing)
        
        assigned_index = row_assignments[i]
        is_target = (assigned_index == target_index)
        
        # LEFT box with image
        draw.rounded_rectangle(
            [left_x, y, left_x + box_size, y + box_size],
            radius=corner_radius,
            fill='white',
            outline=hex_to_rgb(NAVY_BLUE),
            width=border_width
        )
        
        # Draw the assigned image
        img_copy = loaded_images[assigned_index].copy()
        img_copy.thumbnail((box_size - 12, box_size - 12), Image.Resampling.LANCZOS)
        img_x = left_x + (box_size - img_copy.width) // 2
        img_y = y + (box_size - img_copy.height) // 2
        page.paste(img_copy, (img_x, img_y), img_copy)
        
        # Redraw border over image
        draw.rounded_rectangle(
            [left_x, y, left_x + box_size, y + box_size],
            radius=corner_radius,
            fill=None,
            outline=hex_to_rgb(NAVY_BLUE),
            width=border_width
        )
        
        # RIGHT velcro box
        draw.rounded_rectangle(
            [right_x, y, right_x + box_size, y + box_size],
            radius=corner_radius,
            fill=hex_to_rgb(LIGHT_GRAY),
            outline=hex_to_rgb(PURPLE),
            width=border_width
        )
        
        # Velcro circle
        circle_radius = int(15 * scale)  # Reduced from 18
        circle_x = right_x + box_size // 2
        circle_y = y + box_size // 2
        draw.ellipse(
            [circle_x - circle_radius, circle_y - circle_radius,
             circle_x + circle_radius, circle_y + circle_radius],
            fill='#CCCCCC',
            outline='#999999',
            width=int(2 * scale)
        )
        
        velcro_text = "velcro"
        velcro_bbox = draw.textbbox((0, 0), velcro_text, font=fonts['velcro'])
        velcro_w = velcro_bbox[2] - velcro_bbox[0]
        velcro_h = velcro_bbox[3] - velcro_bbox[1]
        draw.text((circle_x - velcro_w // 2, circle_y - velcro_h // 2), velcro_text, fill='#666666', font=fonts['velcro'])
    
    # Brief hint above footer area
    
    if qa_warnings is not None:
        # Ensure instruction and icon don't overlap
        text_left = instruction_x
        text_top = content_top
        text_right = instruction_x + instruction_w
        text_bottom = content_top + (instruction_bbox[3] - instruction_bbox[1])
        icon_left = icon_x - icon_box_padding
        icon_top = icon_y - icon_box_padding
        icon_right = icon_x + target_icon.width + icon_box_padding
        icon_bottom = icon_y + target_icon.height + icon_box_padding
        overlap = not (text_right < icon_left or text_left > icon_right or text_bottom <= icon_top or text_top >= icon_bottom)
        if overlap:
            qa_warnings.append(f"Overlap on page {page_num}: header text and icon for '{target_name}'")
        last_grid_bottom = start_y + 4 * (box_size + row_spacing) + box_size
        footer_top = img_height - safe_footer_inset_px()
        if last_grid_bottom > footer_top:
            qa_warnings.append(f"Footer clearance risk on page {page_num}: grid bottom {last_grid_bottom} > footer top {footer_top}")
        if (right_x + box_size) > content_right or left_x < content_left or start_y < content_top or last_grid_bottom > content_bottom:
            qa_warnings.append(f"Content clipping risk on page {page_num}: content exceeds frame bounds")
    
    return page


def create_cutouts_page(loaded_images, image_names, page_num, pack_code, theme_name):
    """Create cut-outs page with 20 cards (5 of each image)"""
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    # Universal frame
    apply_small_wins_frame(
        page,
        product_title="Matching Cards",
        subtitle="Pieces — Cutouts",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=19,
        level=None,
        footer_title=f"{theme_name} | Matching Cards",
        show_data_strip=False,
    )

    # 4x5 grid within borders (20 boxes)
    cols = 4
    rows = 5
    content_pad = int(0.44 * DPI)
    header_clear = int(1.80 * DPI)
    x_left = content_pad
    x_right = img_width - content_pad
    y_top = header_clear + int(0.12 * DPI)
    y_bot = img_height - safe_footer_inset_px()
    spacing = int(0.10 * DPI)
    avail_w = max(1, x_right - x_left - (cols - 1) * spacing)
    avail_h = max(1, y_bot - y_top - (rows - 1) * spacing)
    box_size = min(avail_w // cols, avail_h // rows)
    start_x = x_left
    start_y = y_top
    
    for row in range(rows):
        for col in range(cols):
            x = start_x + col * (box_size + spacing)
            y = start_y + row * (box_size + spacing)
            
            draw.rounded_rectangle(
                [x, y, x + box_size, y + box_size],
                radius=int(10 * scale),
                fill='white',
                outline=hex_to_rgb(NAVY_BLUE),
                width=int(2 * scale)
            )
            
            if col < len(loaded_images):
                padding = int(6 * scale)
                inner_size = box_size - (2 * padding)
                
                img_copy = loaded_images[col].copy()
                img_copy.thumbnail((inner_size, inner_size), Image.Resampling.LANCZOS)
                
                img_x = x + padding + (inner_size - img_copy.width) // 2
                img_y = y + padding + (inner_size - img_copy.height) // 2
                page.paste(img_copy, (img_x, img_y), img_copy)
    
    # Instructions within content area bottom
    instr_y = y_bot - int(0.70 * DPI)
    instr_text = "Cut along lines. Use for all matching levels."
    instr_bbox = draw.textbbox((0, 0), instr_text, font=fonts['instruction'])
    instr_w = instr_bbox[2] - instr_bbox[0]
    draw.text(((img_width - instr_w) // 2, instr_y), instr_text, fill=hex_to_rgb(NAVY_BLUE), font=fonts['instruction'])
    
    # Tip
    tip_y = instr_y + int(0.22 * DPI)
    tip_text = "Tip: Level 1 uses 5 pieces, Level 4 uses 1 piece."
    tip_bbox = draw.textbbox((0, 0), tip_text, font=fonts['instruction'])
    tip_w = tip_bbox[2] - tip_bbox[0]
    draw.text(((img_width - tip_w) // 2, tip_y), tip_text, fill=hex_to_rgb(STEEL_BLUE), font=fonts['instruction'])
    
    return page


def create_storage_labels_page(loaded_images, image_names, levels, page_num, pack_code, theme_name):
    """Create storage labels page"""
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    # Universal frame
    apply_small_wins_frame(
        page,
        product_title="Matching Cards",
        subtitle=f"Storage Labels — Levels {levels}",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=19,
        level=None,
        footer_title=f"{theme_name} | Matching Cards",
        show_data_strip=False,
    )

    margin = int(0.55 * DPI)
    
    # 4 folder labels (2x2 grid)
    label_width = (img_width - 2 * margin - int(20 * scale)) // 2
    label_height = int(140 * scale)
    start_y = int(80 * scale)
    
    for idx, (img, name) in enumerate(zip(loaded_images[:4], image_names[:4])):
        row = idx // 2
        col = idx % 2
        
        x = margin + col * (label_width + int(20 * scale))
        y = start_y + row * (label_height + int(15 * scale))
        
        draw.rounded_rectangle(
            [x, y, x + label_width, y + label_height],
            radius=int(10 * scale),
            fill='#E8ECF0',
            outline=hex_to_rgb(SWS_TEAL),
            width=int(2 * scale)
        )
        
        img_size = int(70 * scale)
        img_copy = img.copy()
        img_copy.thumbnail((img_size, img_size), Image.Resampling.LANCZOS)
        img_x = x + (label_width - img_copy.width) // 2
        img_y = y + int(12 * scale)
        page.paste(img_copy, (img_x, img_y), img_copy)
        
        name_bbox = draw.textbbox((0, 0), name, font=fonts['storage_label'])
        name_w = name_bbox[2] - name_bbox[0]
        name_x = x + (label_width - name_w) // 2
        name_y = y + label_height - int(40 * scale)
        draw.text((name_x, name_y), name, fill=hex_to_rgb(NAVY_BLUE), font=fonts['storage_label'])
        
        level_text = f"Matching L{levels} - {pack_code}"
        level_bbox = draw.textbbox((0, 0), level_text, font=fonts['storage_small'])
        level_x = x + (label_width - level_bbox[2]) // 2
        level_y = y + label_height - int(20 * scale)
        draw.text((level_x, level_y), level_text, fill='#666666', font=fonts['storage_small'])
    
    # Pieces label
    pieces_y = start_y + 2 * (label_height + int(15 * scale)) + int(20 * scale)
    pieces_height = int(90 * scale)
    
    draw.rounded_rectangle(
        [margin, pieces_y, img_width - margin, pieces_y + pieces_height],
        radius=int(10 * scale),
        fill='#E8ECF0',
        outline=hex_to_rgb(SWS_TEAL),
        width=int(2 * scale)
    )
    
    pieces_text = f"Matching Pieces - Levels {levels}"
    pieces_bbox = draw.textbbox((0, 0), pieces_text, font=fonts['storage_title'])
    pieces_w = pieces_bbox[2] - pieces_bbox[0]
    draw.text(((img_width - pieces_w) // 2, pieces_y + int(15 * scale)), pieces_text, fill=hex_to_rgb(NAVY_BLUE), font=fonts['storage_title'])
    
    pack_info = f"{theme_name} - {pack_code}"
    pack_bbox = draw.textbbox((0, 0), pack_info, font=fonts['instruction'])
    pack_w = pack_bbox[2] - pack_bbox[0]
    draw.text(((img_width - pack_w) // 2, pieces_y + int(55 * scale)), pack_info, fill='#666666', font=fonts['instruction'])
    
    # Footer handled by frame
    
    return page


def generate_matching_pack(images_folder, pack_code="WAN1-A", theme_name="Winter Animals"):
    """Generate complete Matching pack with 4 levels"""
    
    print(f"\n{'='*70}")
    print(f"  ðŸŽ¯ GENERATING MATCHING PACK (4 LEVELS): {pack_code}")
    print(f"  Theme: {theme_name}")
    print(f"{'='*70}\n")
    
    images_path = Path(images_folder)
    if not images_path.exists():
        print(f"âŒ Error: Folder '{images_folder}' not found!")
        return False
    
    image_files = sorted(images_path.glob("*.png"))
    if not image_files or len(image_files) < 4:
        print(f"âŒ Need at least 4 images!")
        return False
    
    output_folder = Path("OUTPUT")
    output_folder.mkdir(exist_ok=True)
    
    def _brightness_stdev(im: Image.Image) -> float:
        small = im.convert('L').resize((128, 128), Image.BILINEAR)
        stat = ImageStat.Stat(small)
        m = stat.mean[0]
        v = stat.var[0] if stat.var else 0.0
        return (v ** 0.5)

    loaded_images = []
    image_names = []
    stems = []
    warn_msgs = []
    for img_file in image_files:
        img = Image.open(img_file)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        st = img_file.stem
        stems.append(st)
        loaded_images.append(img)
        nice = st.replace('_', ' ').replace('-', ' ').title()
        image_names.append(nice)
        try:
            sd = _brightness_stdev(img)
            if sd < 6.0:
                warn_msgs.append(f"Low-entropy icon: '{st}' (stdev={sd:.1f}) — page may look like a placeholder")
        except Exception:
            pass

    # Capture presence of alternatives before any dedupe/substitution (case-insensitive)
    stems_lc = [s.lower() for s in stems]
    has_alt_for_dark = ('dark' in stems_lc) and any(c in stems_lc for c in ('night', 'moon'))

    # Resolve a suitable hero/header icon early so we can place it in the accent strip
    header_icon_img = None
    header_icon_path_str = None
    try:
        slug_guess = None
        p = Path(images_folder).resolve()
        prev = None
        for _ in range(8):
            if p.name == "themes" and prev is not None:
                slug_guess = prev.name
                break
            if p.parent == p:
                break
            prev = p
            p = p.parent
        if slug_guess:
            repo_root = Path(__file__).resolve().parents[2]
            tdir = repo_root / "assets" / "themes" / slug_guess
            hero_candidates = [
                tdir / "hero_header.png",
                tdir / "heroes" / "hero_header.png",
                tdir / "characters" / "hero_header.png",
                tdir / "characters" / "llama_llama.png",
                tdir / "characters" / "main.png",
                tdir / "characters" / "mama_llama.png",
                tdir / "hero.png",
                tdir / "heroes" / "hero.png",
                tdir / "characters" / "hero.png",
                tdir / "header_icon.png",
            ]
            for hp in hero_candidates:
                if hp.exists():
                    try:
                        _im = Image.open(str(hp))
                        header_icon_img = _im.convert("RGBA") if _im.mode != "RGBA" else _im
                        header_icon_path_str = str(hp)
                        break
                    except Exception:
                        continue
    except Exception:
        header_icon_img = None
        header_icon_path_str = None

    # Swap flat 'dark.png' for a more distinctive 'night'/'moon' icon if present, without blocking build.
    try:
        if 'dark' in stems_lc:
            dark_idx = stems_lc.index('dark')
            alt_stem = None
            for cand in ('night', 'moon'):
                if cand in stems_lc:
                    alt_stem = cand
                    break
            # If alternative exists, replace the dark entry's image/name and optionally dedupe the original alt entry.
            if alt_stem is not None:
                alt_idx = stems_lc.index(alt_stem)
                loaded_images[dark_idx] = loaded_images[alt_idx].copy()
                image_names[dark_idx] = image_names[alt_idx]
                warn_msgs.append("Replaced flat 'dark' icon with more distinctive '" + alt_stem + "' icon for generation")
                # Remove duplicate alt entry if it is a separate image to avoid duplicates appearing twice
                if alt_idx != dark_idx:
                    del loaded_images[alt_idx]
                    del image_names[alt_idx]
                    del stems[alt_idx]
                    del stems_lc[alt_idx]
    except Exception:
        pass
    
    print(f"ðŸ“ Pack Details:")
    print(f"   Code: {pack_code}")
    print(f"   Theme: {theme_name}")
    print(f"   Images: {', '.join(image_names)}\n")
    if warn_msgs:
        print("\nâš ï¸ Warnings:")
        for w in warn_msgs:
            print(f"   - {w}")
        print()
    
    saved_pages = []
    qa_warnings: list[str] = []
    page_num = 1
    
    # Generate all 4 levels
    for level in range(1, 5):
        level_names = {1: "Errorless", 2: "Easy", 3: "Medium", 4: "Hard"}
        print(f"ðŸ“„ Level {level} - {level_names[level]} (Pages {page_num}-{page_num+3})...")

        # Option 2: For Level 1, skip 'dark' as a target if an alternative exists.
        if level == 1 and has_alt_for_dark:
            dark_idx = stems_lc.index('dark')
            level_indices = [i for i in range(len(loaded_images)) if i != dark_idx]
            print("   [L1] Skipping 'dark' as a Level 1 target (alternative present).")
            print("   [L1] Target order:", ", ".join(image_names[i] for i in level_indices))
        else:
            level_indices = list(range(len(loaded_images)))

        for idx in level_indices:
            targets = {1: 5, 2: 4, 3: 3, 4: 1}[level]
            distractors = 5 - targets
            print(f"   Page {page_num}: {image_names[idx]} ({targets} targets, {distractors} distractors)")
            page = create_matching_page(
                loaded_images, image_names, idx, level, page_num, pack_code, theme_name,
                qa_warnings=qa_warnings, header_icon_img=header_icon_img)
            saved_pages.append(page)
            page_num += 1
        print()
    
    # Cut-outs page
    print(f"ðŸ“„ Cut-out Pieces (Page {page_num})...")
    cutouts = create_cutouts_page(loaded_images, image_names, page_num, pack_code, theme_name)
    saved_pages.append(cutouts)
    page_num += 1
    
    # Storage Labels
    print(f"\nðŸ“„ Storage Labels (Pages {page_num}-{page_num+1})...")
    labels_1_2 = create_storage_labels_page(loaded_images, image_names, "1-2", page_num, pack_code, theme_name)
    saved_pages.append(labels_1_2)
    page_num += 1
    
    labels_3_4 = create_storage_labels_page(loaded_images, image_names, "3-4", page_num, pack_code, theme_name)
    saved_pages.append(labels_3_4)
    
    print(f"\n   âœ… {len(saved_pages)} pages generated\n")
    if qa_warnings:
        print("QA checks:")
        for w in qa_warnings:
            print(f"   - {w}")

    try:
        cov_img = None
        try:
            design_mod = importlib.import_module("utils.sws_design")
        except Exception:
            alt_path = Path(__file__).resolve().parents[2] / "utils" / "sws_design.py"
            design_mod = None
            if alt_path.exists():
                spec = importlib.util.spec_from_file_location("_SWS_SWS_DESIGN", str(alt_path))
                if spec and spec.loader:
                    _mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(_mod)
                    design_mod = _mod
        # Best-effort theme slug from images_folder to locate assets
        hero_path_str = None
        book_cover_path_str = None
        try:
            slug_guess = None
            p = Path(images_folder).resolve()
            prev = None
            for _ in range(8):
                if p.name == "themes" and prev is not None:
                    slug_guess = prev.name
                    break
                if p.parent == p:
                    break
                prev = p
                p = p.parent
            if slug_guess:
                repo_root = Path(__file__).resolve().parents[2]
                tdir = repo_root / "assets" / "themes" / slug_guess
                # Header hero for accent strip — prefer dedicated header art, then prominent character art,
                # then generic hero; only use header_icon as a last resort.
                hero_candidates = [
                    # Dedicated header-cropped hero
                    tdir / "hero_header.png",
                    tdir / "heroes" / "hero_header.png",
                    tdir / "characters" / "hero_header.png",
                    # Prominent character art (prefer full hero art over small icons)
                    tdir / "characters" / "llama_llama.png",
                    tdir / "characters" / "main.png",
                    tdir / "characters" / "mama_llama.png",
                    # Generic hero fallbacks
                    tdir / "hero.png",
                    tdir / "heroes" / "hero.png",
                    tdir / "characters" / "hero.png",
                    # Last resort
                    tdir / "header_icon.png",
                ]
                for hp in hero_candidates:
                    if hp.exists():
                        hero_path_str = str(hp)
                        break
                if hero_path_str is None:
                    # Fallback: only try well-known hero filenames; do NOT pick a random icon
                    for folder in [tdir / "characters", tdir / "heroes"]:
                        if folder.exists():
                            # Prefer specific names first
                            pref = [
                                folder / "llama_llama.png",
                                folder / "mama_llama.png",
                                folder / "main.png",
                            ]
                            chosen = None
                            for pth in pref:
                                if pth.exists():
                                    chosen = pth
                                    break
                            if chosen is not None:
                                hero_path_str = str(chosen)
                                break
                # Book cover for main left panel
                cover_names = [
                    "book_cover", "cover", "front_cover", "bookfront", "book", "cover_reference"
                ]
                cover_subdirs = [tdir, tdir / "covers", tdir / "images", tdir / "marketing", tdir / "book"]
                exts = ["png", "jpg", "jpeg", "webp"]
                for sd in cover_subdirs:
                    for nm in cover_names:
                        for ex in exts:
                            fp = sd / f"{nm}.{ex}"
                            if fp.exists():
                                book_cover_path_str = str(fp)
                                break
                        if book_cover_path_str:
                            break
                    if book_cover_path_str:
                        break
        except Exception:
            hero_path_str = None
            book_cover_path_str = None
        if design_mod is not None:
            # Prefer the full teacher cover (chips, Top Tips, rope, banner)
            gen_cov = getattr(design_mod, "generate_teacher_cover_page", None)
            if callable(gen_cov):
                whats = [
                    "4 differentiated levels (Errorless to 4-distractor)",
                    "Symbol-supported throughout",
                    "Colour + black & white versions",
                    "Cut-out pieces + storage labels",
                ]
                also = [
                    "Quick Start Guide",
                    "Terms of Use",
                    "B&W version",
                ]
                tips = [
                    "Model core words during play to build AAC carryover.",
                    "Start errorless, then fade prompts across levels.",
                    "Mix icons and real photos for generalization.",
                ]
                cov_img = gen_cov(
                    theme_name=theme_name,
                    pack_code=pack_code,
                    product_name="Matching Activities",
                    page_count=len(saved_pages),
                    level_count=4,
                    hero_image=None,
                    hero_image_path=hero_path_str,
                    book_cover_path=book_cover_path_str,
                    draw_footer=False,
                    whats_included=whats,
                    also_included=also,
                    top_tips=tips,
                    rope_strand="Word Recognition",
                    rope_skills="Decoding · Sight Words · Orthographic Mapping",
                    render_chips=False,
                )
            else:
                # Fallback to the simpler internal cover if teacher variant is unavailable
                gen_int = getattr(design_mod, "generate_internal_cover_page", None)
                if callable(gen_int):
                    cov_img = gen_int(
                        theme_name=theme_name,
                        pack_code=pack_code,
                        product_name="Matching Activities",
                        page_count=len(saved_pages),
                        level_count=4,
                        hero_image=None,
                        hero_image_path=book_cover_path_str or hero_path_str,
                        draw_footer=False,
                        howto_bullets=None,
                    )
    except Exception:
        cov_img = None
    
    print(f"ðŸ“„ Creating COLOR PDF...")
    color_pdf = f"OUTPUT/{pack_code}_Matching_COLOR.pdf"
    c = canvas.Canvas(color_pdf, pagesize=letter)
    if 'cov_img' in locals() and cov_img is not None:
        img_buffer = io.BytesIO()
        cov_img.save(img_buffer, format='PNG', dpi=(DPI, DPI))
        img_buffer.seek(0)
        c.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    for page in saved_pages:
        img_buffer = io.BytesIO()
        page.save(img_buffer, format='PNG', dpi=(DPI, DPI))
        img_buffer.seek(0)
        c.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    c.save()
    print(f"   âœ… {color_pdf}")
    
    print(f"\nðŸ–¤ Creating B&W PDF...")
    bw_pdf = f"OUTPUT/{pack_code}_Matching_BW.pdf"
    c_bw = canvas.Canvas(bw_pdf, pagesize=letter)
    if 'cov_img' in locals() and cov_img is not None:
        img_buffer = io.BytesIO()
        bw_cov = cov_img.convert('L')
        bw_cov.save(img_buffer, format='PNG', dpi=(DPI, DPI))
        img_buffer.seek(0)
        c_bw.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c_bw.showPage()
    for page in saved_pages:
        gray_page = page.convert('L')
        img_buffer = io.BytesIO()
        gray_page.save(img_buffer, format='PNG', dpi=(DPI, DPI))
        img_buffer.seek(0)
        c_bw.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c_bw.showPage()
    c_bw.save()
    print(f"   âœ… {bw_pdf}")

    # In-app full-res export of teacher cover + first two content pages (optional)
    try:
        review_dir = os.environ.get("SWS_REVIEW_DIR")
        if review_dir:
            rd = Path(review_dir)
            rd.mkdir(parents=True, exist_ok=True)
            activity = "Matching"
            if 'cov_img' in locals() and cov_img is not None:
                cov_path = rd / f"{activity}_cover.png"
                cov_img.save(cov_path, format='PNG', dpi=(DPI, DPI))
            if len(saved_pages) >= 1:
                p1_path = rd / f"{activity}_p1.png"
                saved_pages[0].save(p1_path, format='PNG', dpi=(DPI, DPI))
            if len(saved_pages) >= 2:
                p2_path = rd / f"{activity}_p2.png"
                saved_pages[1].save(p2_path, format='PNG', dpi=(DPI, DPI))
            print(f"   Exported review PNGs to {rd}")
    except Exception as e:
        print(f"   ! Review PNG export skipped: {e}")
    preview_pdf = None
    # PREVIEW PDF and thumbnails with provenance metadata (for QA tracing)
    try:
        preview_pdf = f"OUTPUT/{pack_code}_Matching_PREVIEW.pdf"
        preview_indices = list(range(len(saved_pages)))
        prov = {
            "product": "Matching",
            "slug": None,
            "pack_code": pack_code,
            "generator": str(Path(__file__).resolve()),
            "theme_name": theme_name,
            "images_folder": str(Path(images_folder).resolve()) if images_folder else None,
            "built_at": datetime.now().isoformat(timespec="seconds"),
        }
        try:
            # best-effort slug from images_folder path
            p = Path(images_folder).resolve()
            prev = None
            for _ in range(8):
                if p.name == "themes" and prev is not None:
                    prov["slug"] = prev.name
                    break
                if p.parent == p:
                    break
                prev = p
                p = p.parent
        except Exception:
            pass
        make_preview_pdf_from_images(saved_pages, preview_indices, preview_pdf, (PAGE_WIDTH, PAGE_HEIGHT), provenance=prov)
        thumb_dir = Path("OUTPUT") / "thumbnails"
        save_thumbnails_from_images(saved_pages, preview_indices, thumb_dir, f"{pack_code}_Matching", provenance=prov)
        print(f"   âœ… {preview_pdf}")
    except Exception:
        pass
    
    print(f"\n{'='*70}")
    try:
        thumb_dir = Path("OUTPUT") / "thumbnails"
        thumbs = [str(p) for p in sorted(thumb_dir.glob(f"{pack_code}_Matching_thumb*.png"))] if thumb_dir.exists() else []
        manifest = {
            "product_name": "Matching",
            "pack_code": pack_code,
            "theme_name": theme_name,
            "page_count": len(saved_pages) + (1 if 'cov_img' in locals() and cov_img is not None else 0),
            "files": {
                "color_pdf": color_pdf,
                "bw_pdf": bw_pdf,
                "preview_pdf": preview_pdf,
                "thumbnails": thumbs
            },
            "meta": {
                "built_at": datetime.now().isoformat(timespec="seconds"),
                "qa_warnings": qa_warnings
            }
        }
        (Path("OUTPUT") / f"{pack_code}_Matching_BuildResult.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    print(f"  âœ… MATCHING PACK COMPLETE! ({len(saved_pages)} pages)")
    print(f"{'='*70}\n")
    
    return True


if __name__ == "__main__":
    import sys
    
    pack_code = sys.argv[1] if len(sys.argv) > 1 else "WAN1-A"
    theme_name = sys.argv[2] if len(sys.argv) > 2 else "Winter Animals"
    
    success = generate_matching_pack("images", pack_code, theme_name)
    
    if success:
        print("ðŸŽ‰ ALL DONE! CHECK OUTPUT FOLDER!")
    else:
        print("\nâŒ FAILED - check error messages above")
        sys.exit(1)




