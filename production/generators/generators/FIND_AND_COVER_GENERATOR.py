"""
FIND AND COVER GENERATOR - COMBINED L1 + L2 + L3
Creates complete Find & Cover product with all 3 differentiated levels

OUTPUT STRUCTURE (15 pages):
- Pages 1-4: Level 1 (Target + 1 distractor) - Supported
- Pages 5-8: Level 2 (Target + 2 distractors) - Developing  
- Pages 9-12: Level 3 (Target + 3 distractors) - Independent
- Pages 13-15: Storage Labels (one per level)

FULLY REUSABLE - Works with ANY theme!
"""

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
import io
import random
import zipfile
import json
from datetime import datetime
from utils.sws_design import LEVEL_COLORS, generate_teacher_cover_page, shrink_font_to_fit_with_pt, normalize_text, draw_aac_strip, _brand_font_pt
from utils.UNIVERSAL_STANDARDS import SWS_TEAL, SWS_NAVY, SWS_TEAL_LT, MID_GRAY
from utils.qa import assess_files

# Page dimensions
PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

# Colors (from universal tokens)
TITLE_BLUE = SWS_TEAL
NAVY_BLUE = SWS_NAVY
STEEL_BLUE = MID_GRAY
BORDER_NAVY = SWS_NAVY
PURPLE = SWS_TEAL  # For decorative corner accents

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def load_fonts():
    # Use brand fonts (Poppins) consistently; utils handles discovery and fallbacks
    return {
        'title': _brand_font_pt(30, bold=True, brand='poppins'),
        'instruction': _brand_font_pt(18, bold=False, brand='poppins'),
        'footer': _brand_font_pt(16, bold=False, brand='poppins'),
        'copyright': _brand_font_pt(10, bold=False, brand='poppins'),
        'storage_title': _brand_font_pt(36, bold=True, brand='poppins'),
        'storage_label': _brand_font_pt(14, bold=True, brand='poppins'),
        'storage_small': _brand_font_pt(11, bold=False, brand='poppins'),
        'storage_skill': _brand_font_pt(12, bold=False, brand='poppins'),
    }


def _validate_images_folder(images_folder: str) -> None:
    p = Path(images_folder)
    if not p.exists():
        raise FileNotFoundError(f"Folder not found: {images_folder}")
    sp = str(p).lower()
    if "_tlot_archived_duplicate" in sp:
        raise ValueError(
            f"Images folder is inside the archived duplicate tree: {p}. Use assets/themes/<slug>/activity_images/."
        )
    if any(k in sp for k in ["aac_core", "aac_core_text", "global"]):
        raise ValueError(
            f"Find & Cover must not read from AAC core or global folders: {p}. Use assets/themes/<slug>/activity_images/."
        )
    files = [f for f in p.glob("*.png") if f.is_file() and not f.name.startswith(".")]
    if len(files) < 4:
        raise ValueError(f"Too few images in {p} — found {len(files)}, need at least 4.")


def create_find_cover_page(loaded_images, images_list, target_index, distractor_indices, 
                           level, page_num, pack_code, theme_name, total_pages=15, fit_warnings: list[str] | None = None):
    """Create a Find and Cover page for any level"""
    
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
    
    # Top accent stripe (per-level accent)
    accent_height = int(8 * scale)
    draw.rounded_rectangle(
        [border_margin, border_margin, img_width - border_margin, border_margin + accent_height],
        radius=border_radius,
        fill=hex_to_rgb(level_color),
        outline=None
    )

    # Level badge — top right
    try:
        level_labels = {1: 'Supported', 2: 'Developing', 3: 'Independent'}
        badge_text = f"Level {level} · {level_labels.get(level, '')}".strip().rstrip('·')
        badge_w = int(200 * scale)
        badge_h = int(30 * scale)
        badge_x = img_width - border_margin - badge_w - int(10 * scale)
        badge_y = border_margin + int(12 * scale)
        draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=int(8 * scale), fill=hex_to_rgb(level_color))
        bb = draw.textbbox((0, 0), badge_text, font=fonts['instruction'])
        draw.text((badge_x + (badge_w - (bb[2]-bb[0])) // 2, badge_y + (badge_h - (bb[3]-bb[1])) // 2), badge_text, fill=(255, 255, 255), font=fonts['instruction'])
    except Exception:
        pass
    
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
    
    target_image = loaded_images[target_index]
    target_name = Path(images_list[target_index]).stem.replace('_', ' ').replace('-', ' ').title()
    
    # Title (shrink-to-fit) — centered in area excluding level badge
    title_text = normalize_text("Find and Cover")
    badge_clearance = int(220 * scale)  # badge width + padding
    usable_title_w = img_width - 2 * border_margin - badge_clearance - int(10 * scale)
    title_font, title_pt = shrink_font_to_fit_with_pt(
        title_text,
        base_pt=30,
        max_width_px=usable_title_w,
        bold=True,
        brand="poppins",
        min_pt=18,
    )
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    # Center in the area left of the badge
    title_area_left = border_margin + int(10 * scale)
    title_area_right = img_width - border_margin - badge_clearance
    title_x = (title_area_left + title_area_right - title_width) // 2
    title_y = int(25 * scale)
    draw.text((title_x, title_y), title_text, fill=hex_to_rgb(TITLE_BLUE), font=title_font)
    if fit_warnings is not None and title_pt <= 28:
        fit_warnings.append(f"Title shrunk to {title_pt}pt on page {page_num}: '{title_text}'")
    
    # Instruction (shrink-to-fit) — "Find and Cover" is a visual scanning task:
    # student finds all instances of the target in the grid and covers them with tokens
    instruction_text = normalize_text(f"Find and cover all the {target_name}")
    usable_instr_w = img_width - 2 * border_margin - int(20 * scale)
    instr_font, instr_pt = shrink_font_to_fit_with_pt(
        instruction_text,
        base_pt=18,
        max_width_px=usable_instr_w,
        bold=False,
        brand="poppins",
        min_pt=12,
    )
    instruction_bbox = draw.textbbox((0, 0), instruction_text, font=instr_font)
    instruction_width = instruction_bbox[2] - instruction_bbox[0]
    instruction_x = (img_width - instruction_width) // 2
    instruction_y = int(60 * scale)
    draw.text((instruction_x, instruction_y), instruction_text, fill=hex_to_rgb(NAVY_BLUE), font=instr_font)
    if fit_warnings is not None and instr_pt <= 14:
        fit_warnings.append(f"Instruction shrunk to {instr_pt}pt on page {page_num}: '{instruction_text}'")
    
    # Target image box
    target_box_size = int(80 * scale)
    target_box_x = (img_width - target_box_size) // 2
    target_box_y = int(85 * scale)
    
    draw.rectangle(
        [target_box_x, target_box_y, target_box_x + target_box_size, target_box_y + target_box_size],
        outline=hex_to_rgb(NAVY_BLUE),
        width=int(3 * scale)
    )
    
    target_img = target_image.copy()
    padding = int(3 * scale)  # REDUCED PADDING FOR BIGGER IMAGES
    img_size = target_box_size - (2 * padding)
    target_img.thumbnail((img_size, img_size), Image.Resampling.LANCZOS)
    
    img_x = target_box_x + padding + (img_size - target_img.width) // 2
    img_y = target_box_y + padding + (img_size - target_img.height) // 2
    page.paste(target_img, (img_x, img_y), target_img)
    
    # Grid setup - OPTIMIZED for larger grid
    grid_size = 4
    total_cells = grid_size * grid_size
    
    grid_start_y = int(170 * scale)  # REDUCED from 185pt - more space for grid
    available_height = img_height - grid_start_y - int(120 * scale)  # INCREASED bottom margin for footer+border
    available_width = int(img_width * 0.92)  # INCREASED from 0.9 - use more page width
    
    cell_size = min(available_width // grid_size, available_height // grid_size)
    grid_width = cell_size * grid_size
    grid_start_x = (img_width - grid_width) // 2
    
    # Create cell assignments based on level
    # Find & Cover is a visual scanning task: student finds ALL targets in the grid.
    # Distractors are other icons mixed in — the ratio of target-to-distractor
    # decreases with each level to increase visual scanning load.
    cell_assignments = []

    if level == 1:
        # Level 1: Errorless — ALL cells show the target icon
        for _ in range(total_cells):
            cell_assignments.append(target_index)
    elif level == 2:
        # Level 2: Target 10x, each distractor 3x (even distribution)
        for _ in range(10):
            cell_assignments.append(target_index)
        per_dist = (total_cells - 10) // len(distractor_indices)
        remainder = (total_cells - 10) % len(distractor_indices)
        for i, dist_idx in enumerate(distractor_indices):
            for _ in range(per_dist + (1 if i < remainder else 0)):
                cell_assignments.append(dist_idx)
    else:  # Level 3
        # Level 3: Target 8x, distractors evenly distributed across remaining 8
        for _ in range(8):
            cell_assignments.append(target_index)
        per_dist = (total_cells - 8) // len(distractor_indices)
        remainder = (total_cells - 8) % len(distractor_indices)
        for i, dist_idx in enumerate(distractor_indices):
            for _ in range(per_dist + (1 if i < remainder else 0)):
                cell_assignments.append(dist_idx)

    # Shuffle with row-awareness: avoid placing the same icon type
    # in adjacent cells within the same row where possible
    def _shuffle_no_adjacent_same(assignments, grid_sz, max_attempts=200):
        for _ in range(max_attempts):
            random.shuffle(assignments)
            ok = True
            for row in range(grid_sz):
                for col in range(1, grid_sz):
                    idx = row * grid_sz + col
                    if assignments[idx] == assignments[idx - 1]:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                return assignments
        # Fallback: just return the last shuffle
        return assignments

    if level > 1:
        cell_assignments = _shuffle_no_adjacent_same(cell_assignments, grid_size)
    
    # Draw grid cells with images
    for row in range(grid_size):
        for col in range(grid_size):
            cell_index = row * grid_size + col
            image_index = cell_assignments[cell_index]
            
            x = grid_start_x + (col * cell_size)
            y = grid_start_y + (row * cell_size)
            
            draw.rectangle([x, y, x + cell_size, y + cell_size], fill='white')
            
            img_to_draw = loaded_images[image_index].copy()
            padding = int(3 * scale)  # REDUCED PADDING FOR BIGGER IMAGES
            img_size = cell_size - (2 * padding)
            img_to_draw.thumbnail((img_size, img_size), Image.Resampling.LANCZOS)
            
            img_x = x + padding + (img_size - img_to_draw.width) // 2
            img_y = y + padding + (img_size - img_to_draw.height) // 2
            page.paste(img_to_draw, (img_x, img_y), img_to_draw)
    
    # Steel blue gridlines
    grid_color = hex_to_rgb(STEEL_BLUE)
    grid_line_width = int(2 * scale)
    
    for i in range(grid_size + 1):
        x = grid_start_x + (i * cell_size)
        draw.line([(x, grid_start_y), (x, grid_start_y + grid_width)], fill=grid_color, width=grid_line_width)
        y = grid_start_y + (i * cell_size)
        draw.line([(grid_start_x, y), (grid_start_x + grid_width, y)], fill=grid_color, width=grid_line_width)
    
    # Navy border around grid
    border_color = hex_to_rgb(BORDER_NAVY)
    border_width = int(4 * scale)
    
    draw.rectangle(
        [grid_start_x - border_width//2, 
         grid_start_y - border_width//2, 
         grid_start_x + grid_width + border_width//2, 
         grid_start_y + grid_width + border_width//2],
        outline=border_color,
        width=border_width
    )
    
    try:
        fringe_words = [target_name] + [Path(images_list[i]).stem.replace('_', ' ').replace('-', ' ').title() for i in distractor_indices]
        draw_aac_strip(page, words=fringe_words)
    except Exception:
        pass

    # Footer - Page info (main)
    footer_text = f"{theme_name} - {pack_code} | Find and Cover | Page {page_num}/{total_pages}"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=fonts['footer'])
    footer_width = footer_bbox[2] - footer_bbox[0]
    footer_x = (img_width - footer_width) // 2
    footer_y = img_height - int(55 * scale)
    draw.text((footer_x, footer_y), footer_text, fill=hex_to_rgb(NAVY_BLUE), font=fonts['footer'])
    
    # Copyright - Subtle branding (smaller, lighter, less prominent)
    copyright_text = "© 2026 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License"
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_width = copyright_bbox[2] - copyright_bbox[0]
    copyright_x = (img_width - copyright_width) // 2
    copyright_y = img_height - int(30 * scale)  # subtle branding at very bottom
    draw.text((copyright_x, copyright_y), copyright_text, fill='#999999', font=fonts['copyright'])  # Lighter gray
    
    return page


def create_storage_labels_page(image_paths, image_names, level, pack_code, theme_name, page_num=0, total_pages=15, fit_warnings: list[str] | None = None):
    """Create storage labels page for Find & Cover (no pieces label needed)"""
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), '#FDFCF8')  # SWS Cream
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    # Level info
    level_info = {
        1: ("Level 1 — Supported", "2-Choice Visual Scanning (1 vs 1)"),
        2: ("Level 2 — Developing", "3-Choice Visual Scanning (1 vs 2)"),
        3: ("Level 3 — Independent", "4-Choice Visual Scanning (1 vs 3)")
    }
    
    level_name, skill_text = level_info[level]
    
    # Title (shrink-to-fit)
    title_text = normalize_text(f"Storage Labels - {level_name}")
    usable_title_w = img_width - int(2 * 40 * scale)
    storage_title_font, storage_title_pt = shrink_font_to_fit_with_pt(
        title_text,
        base_pt=36,
        max_width_px=usable_title_w,
        bold=True,
        brand="poppins",
        min_pt=18,
    )
    title_bbox = draw.textbbox((0, 0), title_text, font=storage_title_font)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, int(25 * scale)), title_text, fill=hex_to_rgb(NAVY_BLUE), font=storage_title_font)
    if fit_warnings is not None and storage_title_pt <= 28:
        fit_warnings.append(f"Storage labels title shrunk to {storage_title_pt}pt on page {page_num}: '{title_text}'")
    
    # Skill description
    skill_bbox = draw.textbbox((0, 0), skill_text, font=fonts['storage_skill'])
    skill_w = skill_bbox[2] - skill_bbox[0]
    draw.text(((img_width - skill_w) // 2, int(65 * scale)), skill_text, fill=hex_to_rgb(TITLE_BLUE), font=fonts['storage_skill'])
    
    # Load images
    loaded_images = []
    for img_path in image_paths:
        img = Image.open(img_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        loaded_images.append(img)
    
    margin = int(40 * scale)
    
    # 4 folder labels (2x2 grid)
    label_width = (img_width - 2 * margin - int(20 * scale)) // 2
    label_height = int(160 * scale)
    start_y = int(100 * scale)
    
    for idx, (img, name) in enumerate(zip(loaded_images[:4], image_names[:4])):
        row = idx // 2
        col = idx % 2
        
        x = margin + col * (label_width + int(20 * scale))
        y = start_y + row * (label_height + int(15 * scale))
        
        draw.rounded_rectangle(
            [x, y, x + label_width, y + label_height],
            radius=int(10 * scale),
            fill='#E8ECF0',
            outline='#5C5C3D',
            width=int(2 * scale)
        )
        
        # Image
        img_size = int(80 * scale)
        img_copy = img.copy()
        img_copy.thumbnail((img_size, img_size), Image.Resampling.LANCZOS)
        img_x = x + (label_width - img_copy.width) // 2
        img_y = y + int(15 * scale)
        page.paste(img_copy, (img_x, img_y), img_copy)
        
        # Name (shrink-to-fit)
        name_txt = normalize_text(name)
        usable_name_w = label_width - int(20 * scale)
        name_font, name_pt = shrink_font_to_fit_with_pt(
            name_txt,
            base_pt=14,
            max_width_px=usable_name_w,
            bold=True,
            brand="poppins",
            min_pt=8,
        )
        name_bbox = draw.textbbox((0, 0), name_txt, font=name_font)
        name_w = name_bbox[2] - name_bbox[0]
        name_x = x + (label_width - name_w) // 2
        name_y = y + label_height - int(50 * scale)
        draw.text((name_x, name_y), name_txt, fill=hex_to_rgb(NAVY_BLUE), font=name_font)
        if fit_warnings is not None and name_pt <= 10:
            fit_warnings.append(f"Storage label '{name_txt}' shrunk to {name_pt}pt on page {page_num}")
        
        # Pack code
        pack_text = f"Find & Cover {level_name} - {pack_code}"
        pack_bbox = draw.textbbox((0, 0), pack_text, font=fonts['storage_small'])
        pack_x = x + (label_width - pack_bbox[2]) // 2
        pack_y = y + label_height - int(25 * scale)
        draw.text((pack_x, pack_y), pack_text, fill='#666666', font=fonts['storage_small'])
    
    # Instructions
    instr_y = start_y + 2 * (label_height + int(15 * scale)) + int(30 * scale)
    instr_text = "Cut out labels and attach to folders. Teacher provides chips/counters for covering."
    instr_bbox = draw.textbbox((0, 0), instr_text, font=fonts['storage_small'])
    instr_w = instr_bbox[2] - instr_bbox[0]
    draw.text(((img_width - instr_w) // 2, instr_y), instr_text, fill='#555555', font=fonts['storage_small'])
    
    # Footer - Page info (main)
    footer_y = img_height - int(55 * scale)
    footer_text = f"{theme_name} - {pack_code} | Find and Cover | Page {page_num}/{total_pages}"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=fonts['footer'])
    footer_w = footer_bbox[2] - footer_bbox[0]
    draw.text(((img_width - footer_w) // 2, footer_y), footer_text, fill=hex_to_rgb(NAVY_BLUE), font=fonts['footer'])
    
    # Copyright - Subtle branding at very bottom (with PCS attribution — labels use PCS icons)
    copyright_y = img_height - int(30 * scale)  # subtle branding
    copyright_text = "© 2026 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License"
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_w = copyright_bbox[2] - copyright_bbox[0]
    draw.text(((img_width - copyright_w) // 2, copyright_y), copyright_text, fill='#999999', font=fonts['copyright'])  # Lighter gray
    
    return page


def generate_find_and_cover_pack(images_folder, pack_code="WAN1-A", theme_name="Winter Animals", output_dir: str | None = None):
    """Generate complete Find and Cover pack with L1 + L2 + L3"""
    
    print(f"\n{'='*70}")
    print(f"  🔍 GENERATING FIND AND COVER (L1 + L2 + L3): {pack_code}")
    print(f"  Theme: {theme_name}")
    print(f"{'='*70}\n")
    
    try:
        _validate_images_folder(images_folder)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    images_path = Path(images_folder)
    image_files = sorted([
        f for f in images_path.glob("*.png")
        if f.is_file() and not f.name.startswith(".")
        and not any(k in str(f).lower() for k in ["aac_core", "aac_core_text", "global"])
    ])
    if not image_files or len(image_files) < 4:
        print(f"❌ Need at least 4 images!")
        return False
    
    # Use all available icons (no 4-icon cap)
    n_icons = len(image_files)
    
    # Derive the book's OUTPUT directory from the images folder path
    images_path = Path(images_folder).resolve()
    if images_path.name == "icons" and images_path.parent.name == ".sf_build":
        theme_dir = images_path.parent.parent
    else:
        theme_dir = images_path.parent
    out_dir = (Path(output_dir) if output_dir else (theme_dir / "OUTPUT"))
    if "_TLOT_ARCHIVED_DUPLICATE" in str(out_dir):
        print(f"❌ ERROR: Output path points into archived duplicate: {out_dir}")
        return False
    out_dir.mkdir(parents=True, exist_ok=True)
    
    activity_names = [img.stem.replace('_', ' ').replace('-', ' ').title() for img in image_files]
    
    # Load all images once
    loaded_images = []
    for img_file in image_files:
        img = Image.open(img_file)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        loaded_images.append(img)
    
    print(f"📝 Pack Details:")
    print(f"   Code: {pack_code}")
    print(f"   Theme: {theme_name}")
    print(f"   Images: {', '.join(activity_names)}\n")
    
    # Dynamic page count: (n_icons pages per level × 3 levels) + 3 storage labels
    page_count = (n_icons * 3) + 3
    total_pages = page_count + 1
    # Load per-activity cover config (find_and_cover.json, with shared.json fallback or legacy single file)
    cover_cfg: dict = {}
    try:
        theme_dir = images_path.resolve().parent
        cc_dir = theme_dir / "cover_config"
        # Try multiple common filenames
        cand = [
            cc_dir / "find_and_cover.json",
            cc_dir / "find-cover.json",
            cc_dir / "findcover.json",
        ]
        shared = cc_dir / "shared.json"
        pd: dict | None = None
        for p in cand:
            if p.exists():
                obj = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(obj, dict):
                    pd = obj
                    break
        if pd is not None:
            merged = {}
            if shared.exists():
                try:
                    sobj = json.loads(shared.read_text(encoding="utf-8"))
                    if isinstance(sobj, dict):
                        merged.update(sobj)
                except Exception:
                    pass
            merged.update(pd)
            # CRITICAL: why_this_works must be per-activity only; remove if only from shared
            if "why_this_works" not in pd:
                merged.pop("why_this_works", None)
            cover_cfg = merged
        else:
            legacy = theme_dir / "cover_config.json"
            if legacy.exists():
                obj = json.loads(legacy.read_text(encoding="utf-8"))
                if isinstance(obj, dict):
                    for k in ["find_and_cover", "find-cover", "findcover"]:
                        if k in obj and isinstance(obj[k], dict):
                            merged = {}
                            if isinstance(obj.get("shared"), dict):
                                merged.update(obj["shared"])  # type: ignore[index]
                            merged.update(obj[k])  # type: ignore[index]
                            # Keep why_this_works only when present in the product section
                            if "why_this_works" not in obj[k]:  # type: ignore[index]
                                merged.pop("why_this_works", None)
                            cover_cfg = merged
                            break
                    if not cover_cfg:
                        # Top-level legacy should NOT contribute why_this_works
                        cover_cfg = obj.copy()
                        cover_cfg.pop("why_this_works", None)
    except Exception:
        cover_cfg = {}
    rope = cover_cfg.get("rope") if isinstance(cover_cfg, dict) else None
    hero_path_str = None
    book_cover_path_str = None
    try:
        theme_dir = images_path.resolve().parent
        hero_candidates = [
            # Prefer explicit character heroes first (avoid generic placeholders)
            theme_dir / "characters" / "llama_llama.png",
            theme_dir / "characters" / "mama_llama.png",
            theme_dir / "hero_header.png",
            theme_dir / "heroes" / "hero_header.png",
            theme_dir / "characters" / "hero_header.png",
            theme_dir / "characters" / "header_icon.png",
            theme_dir / "header_icon.png",
            theme_dir / "hero.png",
            theme_dir / "heroes" / "hero.png",
            theme_dir / "characters" / "hero.png",
        ]
        for hp in hero_candidates:
            if hp.exists():
                hero_path_str = str(hp)
                break
        cover_names = ["book_cover", "cover", "front_cover", "bookfront", "book", "cover_reference"]
        cover_subdirs = [theme_dir, theme_dir / "covers", theme_dir / "images", theme_dir / "marketing", theme_dir / "book"]
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
    # Build dynamic default bullets if not provided in config
    _wi = None
    try:
        if isinstance(cover_cfg, dict) and isinstance(cover_cfg.get("whats_included"), list):
            _wi = cover_cfg.get("whats_included")
        else:
            lvl_cnt = 3
            _wi = [
                f"{lvl_cnt} levels (1–{lvl_cnt})",
                "Supported learning design, built for independent use",
                "Boardmaker PCS symbols throughout",
                "Full color and black & white versions",
            ]
    except Exception:
        _wi = None
    cover_page = generate_teacher_cover_page(
        theme_name=theme_name,
        pack_code=pack_code,
        product_name="Find & Cover",
        page_count=page_count,
        level_count=3,
        hero_image=None,
        hero_image_path=hero_path_str,
        book_cover_path=book_cover_path_str,
        draw_footer=True,
        whats_included=_wi,
        also_included=cover_cfg.get("also_included") if isinstance(cover_cfg, dict) else None,
        top_tips=cover_cfg.get("top_tips") if isinstance(cover_cfg, dict) else None,
        rope_strand=(rope.get("strand") if isinstance(rope, dict) else cover_cfg.get("rope_strand") if isinstance(cover_cfg, dict) else None),
        rope_skills=(rope.get("skills") if isinstance(rope, dict) else cover_cfg.get("rope_skills") if isinstance(cover_cfg, dict) else None),
        small_win_text=(cover_cfg.get("small_win_text") if isinstance(cover_cfg, dict) and cover_cfg.get("small_win_text") else "⭐ Small Wins ⭐"),
        render_chips=False,
        why_this_works=cover_cfg.get("why_this_works") if isinstance(cover_cfg, dict) else None,
    )
    saved_pages = [cover_page]
    text_fit_warnings: list[str] = []
    page_num = 2
    
    # Level 1: Target + 1 distractor (Pages 2-5)
    print(f"📄 Creating Level 1 pages ({n_icons} pages) - 1 distractor...")
    for idx in range(n_icons):
        target_index = idx
        distractor_indices = [(idx + 1) % n_icons]  # Next image as distractor
        
        print(f"   Page {page_num}: Find the {activity_names[idx]} (vs {activity_names[distractor_indices[0]]})")
        
        page = create_find_cover_page(
            loaded_images, [str(f) for f in image_files],
            target_index, distractor_indices,
            1, page_num, pack_code, theme_name, total_pages,
            fit_warnings=text_fit_warnings,
        )
        saved_pages.append(page)
        page_num += 1
    
    # Level 2: Target + 2 distractors (Pages 6-9)
    print(f"\n📄 Creating Level 2 pages ({n_icons} pages) - 2 distractors...")
    for idx in range(n_icons):
        target_index = idx
        # Two distinct distractors that are not the target
        distractor_indices = [(idx + 1) % n_icons, (idx + 2) % n_icons]
        
        dist_names = [activity_names[i] for i in distractor_indices]
        print(f"   Page {page_num}: Find the {activity_names[idx]} (vs {', '.join(dist_names)})")
        
        page = create_find_cover_page(
            loaded_images, [str(f) for f in image_files],
            target_index, distractor_indices,
            2, page_num, pack_code, theme_name, total_pages,
            fit_warnings=text_fit_warnings,
        )
        saved_pages.append(page)
        page_num += 1
    
    # Level 3: Target + 3 distractors (Pages 10-13)
    print(f"\n📄 Creating Level 3 pages ({n_icons} pages) - 3 distractors...")
    for idx in range(n_icons):
        target_index = idx
        distractor_indices = [i for i in range(n_icons) if i != target_index]
        
        print(f"   Page {page_num}: Find the {activity_names[idx]} (vs all others)")
        
        page = create_find_cover_page(
            loaded_images, [str(f) for f in image_files],
            target_index, distractor_indices,
            3, page_num, pack_code, theme_name, total_pages,
            fit_warnings=text_fit_warnings,
        )
        saved_pages.append(page)
        page_num += 1
    
    # Storage Labels (Pages 14-16)
    print(f"\n📄 Creating Storage Labels (3 pages)...")
    for level in [1, 2, 3]:
        print(f"   Page {page_num}: Level {level} Storage Labels")
        labels = create_storage_labels_page([str(f) for f in image_files], activity_names, level, pack_code, theme_name, page_num, total_pages, fit_warnings=text_fit_warnings)
        saved_pages.append(labels)
        page_num += 1
    
    print(f"\n   ✅ {len(saved_pages)} pages generated\n")
    
    # Create COLOR PDF
    print(f"📄 Creating COLOR PDF...")
    color_pdf = str(out_dir / f"{pack_code}_FindAndCover_COLOR.pdf")
    c = canvas.Canvas(color_pdf, pagesize=letter)
    for page in saved_pages:
        img_buffer = io.BytesIO()
        page.save(img_buffer, format='PNG', dpi=(DPI, DPI))
        img_buffer.seek(0)
        c.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    c.save()
    print(f"   ✅ {color_pdf}")
    
    # Create B&W PDF
    print(f"\n🖤 Creating B&W PDF...")
    bw_pdf = str(out_dir / f"{pack_code}_FindAndCover_BW.pdf")
    c_bw = canvas.Canvas(bw_pdf, pagesize=letter)
    for page in saved_pages:
        gray_page = page.convert('L')
        img_buffer = io.BytesIO()
        gray_page.save(img_buffer, format='PNG', dpi=(DPI, DPI))
        img_buffer.seek(0)
        c_bw.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c_bw.showPage()
    c_bw.save()
    print(f"   ✅ {bw_pdf}")
    
    # Create PREVIEW PDF
    print(f"\n🔒 Creating PREVIEW PDF...")
    preview_pdf = str(out_dir / f"{pack_code}_FindAndCover_PREVIEW.pdf")
    c_preview = canvas.Canvas(preview_pdf, pagesize=letter)
    # Show one page from each level: first L1, first L2, first L3
    # Cover is at index 0, then L1 pages [1..n_icons], L2 starts at 1+n_icons, L3 at 1+2*n_icons
    pidx = [1, 1 + n_icons, 1 + 2 * n_icons]
    preview_pages = [saved_pages[i] for i in pidx if 0 <= i < len(saved_pages)]
    for page in preview_pages:
        img_buffer = io.BytesIO()
        page.save(img_buffer, format='PNG', dpi=(DPI, DPI))
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
    print(f"   ✅ {preview_pdf}")
    
    # Create thumbnails
    print(f"\n🖼️  Creating thumbnails...")
    thumb_folder = out_dir / "thumbnails"
    thumb_folder.mkdir(parents=True, exist_ok=True)
    # One from each level + one storage label
    thumb_pages = [1, 5, 9, 13]
    for i, page_idx in enumerate(thumb_pages, 1):
        thumb = saved_pages[page_idx].copy()
        thumb.thumbnail((500, 647), Image.Resampling.LANCZOS)
        thumb_path = thumb_folder / f"{pack_code}_FindAndCover_thumb{i}.png"
        thumb.save(thumb_path, "PNG")
    print(f"   ✅ 4 thumbnails created")
    # Standard QA_OUT exports (cover + first + mid + last + calling_cards placeholder)
    try:
        qa_dir = out_dir / "QA_OUT"
        qa_dir.mkdir(parents=True, exist_ok=True)
        # cover
        saved_pages[0].save(qa_dir / "cover.png", format="PNG", dpi=(DPI, DPI))
        # first content page
        if len(saved_pages) > 1:
            saved_pages[1].save(qa_dir / "page_first.png", format="PNG", dpi=(DPI, DPI))
        # mid page
        mid_idx = max(0, len(saved_pages) // 2)
        saved_pages[min(mid_idx, len(saved_pages) - 1)].save(qa_dir / "page_mid.png", format="PNG", dpi=(DPI, DPI))
        # last page
        saved_pages[-1].save(qa_dir / "page_last.png", format="PNG", dpi=(DPI, DPI))
        # map labels page to calling_cards.png for consistent QA naming
        saved_pages[-1].save(qa_dir / "calling_cards.png", format="PNG", dpi=(DPI, DPI))
    except Exception:
        pass
    
    # Create TPT Description
    print(f"\n📝 Creating TPT description...")
    description = f"""FIND AND COVER (3 LEVELS) - {theme_name.upper()} - {pack_code}

🔍 COMPLETE VISUAL SCANNING ACTIVITY with 3 Levels

✨ WHAT'S INCLUDED (16 Pages):

⭐ LEVEL 1 (Pages 2-5)
• Target + 1 distractor only
• Target appears 10 times
• Skill: 2-Choice Visual Scanning

⭐⭐ LEVEL 2 (Pages 6-9)
• Target + 2 distractors
• Target appears 8 times
• Skill: 3-Choice Visual Scanning

⭐⭐⭐ LEVEL 3 (Pages 10-13)
• Target + 3 distractors (all 4 images)
• Target appears 6 times
• Skill: 4-Choice Visual Scanning

📁 STORAGE LABELS (Pages 14-16)
• Folder labels for each level
• Teacher provides chips/counters

🎯 ACTIVITIES:
{chr(10).join(f'• Find the {name}' for name in activity_names)}

💡 HOW TO USE:
1. Print and laminate pages
2. Student sees target in box at top
3. Find all matching images in grid
4. Cover with chips, counters, or mini erasers
5. Count to check!

🌟 SKILLS PRACTICED:
• Visual scanning
• Visual discrimination
• Attention to detail
• Focus & concentration
• Counting

✨ PERFECT FOR:
• Special education
• Autism programs
• Speech therapy
• Early childhood
• Work task boxes

📄 INCLUDES:
• 16-page COLOR PDF
• 16-page B&W PDF
• Storage labels for each level

© 2026 Small Wins Studio
PCS® symbols used with active PCS Maker Personal License.
"""
    
    desc_path = str(out_dir / f"{pack_code}_FindAndCover_TPT_Description.txt")
    with open(desc_path, 'w', encoding='utf-8') as f:
        f.write(description)
    print(f"   ✅ {desc_path}")
    
    # Create ZIP
    print(f"\n📦 Creating ZIP package...")
    zip_path = str(out_dir / f"{pack_code}_FindAndCover_Package.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(color_pdf, f"{pack_code}_FindAndCover/{pack_code}_FindAndCover_COLOR.pdf")
        zipf.write(bw_pdf, f"{pack_code}_FindAndCover/{pack_code}_FindAndCover_BW.pdf")
        for thumb_file in thumb_folder.glob(f"{pack_code}_FindAndCover*.png"):
            zipf.write(thumb_file, f"{pack_code}_FindAndCover/thumbnails/{thumb_file.name}")
    print(f"   ✅ {zip_path}")
    
    print(f"\n{'='*70}")
    print(f"  ✅ FIND AND COVER PACK COMPLETE! (16 pages)")
    print(f"{'='*70}\n")
    
    print(f"📦 Output Files:")
    print(f"   • {pack_code}_FindAndCover_COLOR.pdf (16 pages)")
    print(f"   • {pack_code}_FindAndCover_BW.pdf (16 pages)")
    print(f"   • {pack_code}_FindAndCover_PREVIEW.pdf (3 pages)")
    print(f"   • {pack_code}_FindAndCover_TPT_Description.txt")
    print(f"   • 4 thumbnails")
    print(f"   • {pack_code}_FindAndCover_Package.zip\n")
    
    try:
        thumbs = [str(p) for p in sorted((out_dir / "thumbnails").glob(f"{pack_code}_FindAndCover*.png"))]
        try:
            warnings = assess_files(
                product_name="Find & Cover",
                color_pdf=color_pdf,
                bw_pdf=bw_pdf,
                preview_pdf=preview_pdf,
                expected_pages=len(saved_pages),
            )
        except Exception:
            warnings = []
        try:
            warnings.extend(text_fit_warnings)
        except Exception:
            pass
        manifest = {
            "product_name": "Find & Cover",
            "slug": (Path(images_folder).resolve().parent.name if images_folder else None),
            "pack_code": pack_code,
            "page_count": len(saved_pages),
            "files": {
                "color_pdf": color_pdf,
                "bw_pdf": bw_pdf,
                "preview_pdf": preview_pdf,
                "thumbnails": thumbs,
            },
            "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": warnings},
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{pack_code}_FindAndCover_BuildResult.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass
    
    return True


if __name__ == "__main__":
    import sys
    
    pack_code = sys.argv[1] if len(sys.argv) > 1 else "WAN1-A"
    theme_name = sys.argv[2] if len(sys.argv) > 2 else "Winter Animals"
    
    success = generate_find_and_cover_pack("images", pack_code, theme_name)
    
    if success:
        print(f"{'='*70}")
        print(f"  🎉 ALL DONE! CHECK OUTPUT FOLDER!")
        print(f"{'='*70}\n")
    else:
        print("\n❌ FAILED - check error messages above")
        import sys
        sys.exit(1)

