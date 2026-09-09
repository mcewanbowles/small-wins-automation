# SWS-GEN-VERSION: 2026-07-07 (see CHANGELOG.md in this pack for what changed)
"""
AAC SENTENCE STRIPS GENERATOR - v5 (ENHANCED FOR BROWN BEAR)
10 pages total with 20 AAC core words and 8 sentence patterns

Structure:
- Pages 1-8: Eight different sentence patterns
- Page 9: Cut-out pieces (20 words in 4×5 grid)
- Page 10: Storage labels

SENTENCE PATTERNS:
1. I see ___
2. I want ___
3. I like ___
4. I don't like ___
5. ___ is big
6. ___ is small
7. I want more ___
8. ___ can go

20 AAC CORE WORDS REQUIRED:
I, see, want, like, don't like, big, small, good, more, 
go, stop, help, eat, drink, play, happy, sad, hot, cold, turn
"""

from pathlib import Path
import hashlib
import shutil
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
import traceback
import json
from datetime import datetime
from utils.sws_design import (
    shrink_font_to_fit_with_pt,
    normalize_text,
    apply_small_wins_frame,
    safe_footer_inset_px,
)
from utils.sws_design_utils import apply_sws_page_frame
from utils.qa import assess_files
from utils.UNIVERSAL_STANDARDS import SWS_TEAL, SWS_NAVY, SWS_TEAL_LT, MID_GRAY

PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

TITLE_BLUE = SWS_TEAL
NAVY_BLUE = SWS_NAVY
LIGHT_GRAY = MID_GRAY
LIGHT_BLUE = SWS_TEAL_LT
PURPLE = SWS_TEAL

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def load_fonts():
    scale = DPI / 72
    fonts = {}
    try:
        fonts['title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(42 * scale))
        fonts['subtitle'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(22 * scale))
        fonts['word_name'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(14 * scale))
        fonts['label'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(14 * scale))
        fonts['footer'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(7 * scale))
        fonts['cutout_title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(36 * scale))
        fonts['storage_title'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(32 * scale))
        fonts['storage_label'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(14 * scale))
        fonts['storage_small'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(10 * scale))
        fonts['instruction'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(14 * scale))
    except:
        fonts['title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(42 * scale))
        fonts['subtitle'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(22 * scale))
        fonts['word_name'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(14 * scale))
        fonts['label'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(14 * scale))
        fonts['footer'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(7 * scale))
        fonts['cutout_title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(36 * scale))
        fonts['storage_title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(32 * scale))
        fonts['storage_label'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(14 * scale))
        fonts['storage_small'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(10 * scale))
        fonts['instruction'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(14 * scale))
    return fonts


def make_faint_image(img, opacity=0.15):
    """Create a faint/shadow version of an image"""
    img_copy = img.copy().convert('RGBA')
    alpha = img_copy.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    img_copy.putalpha(alpha)
    return img_copy


def create_sentence_strip_page(sentence_pattern, aac_symbols_needed, theme_images, 
                                theme_names, page_num, pack_code, theme_name, *, total_pages: int, fit_warnings: list[str] | None = None,
                                header_left_icon_img: Image.Image | None = None, strips_per_page: int = 6,
                                show_cut_guides: bool = True,
                                show_pattern_labels_on_strip: bool = True,
                                show_trim_marks: bool = True,
                                show_aac_labels: bool = False):
    """
    Create a sentence strip page with 4 strips spread out vertically
    
    Args:
        sentence_pattern: Dict with 'display', 'description', 'words' keys
        aac_symbols_needed: List of AAC symbol keys needed for this pattern
        theme_images: List of theme images
        theme_names: List of theme names
        page_num: Page number
        pack_code: Pack code (e.g., BB01)
        theme_name: Theme name (e.g., "Brown Bear")
    """
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    header_h = int(0.80 * DPI)
    
    margin_left = int(30 * scale)
    margin_right = int(30 * scale)
    content_width = img_width - margin_left - margin_right
    
    
    
    # Subtitle with pattern display
    subtitle_y = header_h + int(60 * scale)
    subtitle_text = normalize_text(sentence_pattern['display'])
    usable_sub_w = img_width - int(2 * 30 * scale)
    sub_font, sub_pt = shrink_font_to_fit_with_pt(
        subtitle_text,
        base_pt=22,
        max_width_px=usable_sub_w,
        bold=True,
        brand="poppins",
        min_pt=12,
    )
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=sub_font)
    subtitle_w = subtitle_bbox[2] - subtitle_bbox[0]
    draw.text(((img_width - subtitle_w) // 2, subtitle_y), subtitle_text, 
              fill=hex_to_rgb(NAVY_BLUE), font=sub_font)
    if fit_warnings is not None and sub_pt <= 14:
        fit_warnings.append(f"Subtitle shrunk to {sub_pt}pt on page {page_num}: '{subtitle_text}'")
    
    # Description
    desc_y = header_h + int(90 * scale)
    desc_text = normalize_text(sentence_pattern['description'])
    usable_desc_w = img_width - int(2 * 40 * scale)
    desc_font, desc_pt = shrink_font_to_fit_with_pt(
        desc_text,
        base_pt=14,
        max_width_px=usable_desc_w,
        bold=False,
        brand="poppins",
        min_pt=10,
    )
    desc_bbox = draw.textbbox((0, 0), desc_text, font=desc_font)
    desc_w = desc_bbox[2] - desc_bbox[0]
    draw.text(((img_width - desc_w) // 2, desc_y), desc_text, 
              fill=hex_to_rgb(NAVY_BLUE), font=desc_font)
    if fit_warnings is not None and desc_pt <= 12:
        fit_warnings.append(f"Description shrunk to {desc_pt}pt on page {page_num}: '{desc_text}'")
    
    # Calculate strip dimensions (fit to available area above footer)
    strips_start_y = header_h + int(125 * scale)
    footer_inset = safe_footer_inset_px()
    avail_h = img_height - footer_inset - strips_start_y - int(40 * scale)
    strips_per_page = max(3, min(8, int(strips_per_page or 6)))
    strip_spacing = int((10 if strips_per_page <= 4 else 8) * scale)
    strip_height = max(int(70 * scale), (avail_h - (strips_per_page - 1) * strip_spacing) // strips_per_page)
    
    # Helpers for visual guides
    def _draw_dashed_h(y: int, x0: int, x1: int, dash: int = int(12 * scale), gap: int = int(10 * scale), color=(160,160,160), width: int = int(2*scale)):
        xx = x0
        while xx < x1:
            x_end = min(xx + dash, x1)
            draw.line([(xx, y), (x_end, y)], fill=color, width=width)
            xx = x_end + gap

    def _draw_trim_marks(color=(150,150,150)):
        off = int(18 * scale)
        ln  = int(22 * scale)
        w   = int(2 * scale)
        # TL
        draw.line([(off, off), (off + ln, off)], fill=color, width=w)
        draw.line([(off, off), (off, off + ln)], fill=color, width=w)
        # TR
        draw.line([(img_width - off, off), (img_width - off - ln, off)], fill=color, width=w)
        draw.line([(img_width - off, off), (img_width - off, off + ln)], fill=color, width=w)
        # BL
        draw.line([(off, img_height - off), (off + ln, img_height - off)], fill=color, width=w)
        draw.line([(off, img_height - off), (off, img_height - off - ln)], fill=color, width=w)
        # BR
        draw.line([(img_width - off, img_height - off), (img_width - off - ln, img_height - off)], fill=color, width=w)
        draw.line([(img_width - off, img_height - off), (img_width - off, img_height - off - ln)], fill=color, width=w)

    # Create N sentence strips
    for strip_idx in range(strips_per_page):
        strip_y = strips_start_y + strip_idx * (strip_height + strip_spacing)
        
        # Strip background
        draw.rounded_rectangle(
            [margin_left, strip_y, img_width - margin_right, strip_y + strip_height],
            radius=int(8 * scale),
            fill=hex_to_rgb(LIGHT_BLUE),
            outline=hex_to_rgb(NAVY_BLUE),
            width=int(2 * scale)
        )
        # Pattern label on strip (top-left)
        if show_pattern_labels_on_strip:
            lbl_text = normalize_text(sentence_pattern['display'])
            usable_lbl_w = content_width - int(20 * scale)
            lbl_font, _ = shrink_font_to_fit_with_pt(
                lbl_text,
                base_pt=16,
                max_width_px=usable_lbl_w,
                bold=True,
                brand="poppins",
                min_pt=10,
            )
            draw.text((margin_left + int(10 * scale), strip_y + int(8 * scale)), lbl_text, 
                      fill=hex_to_rgb(NAVY_BLUE), font=lbl_font)
        
        # Calculate positions for sentence components
        # Component types: 'aac' (AAC symbol box), 'theme' (theme image box), 'text' (text-only word, no icon needed)
        label_space = int(17 * scale) if show_aac_labels else 0
        box_size = min(int(105 * scale), strip_height - int(18 * scale) - label_space)
        box_spacing = int(10 * scale)
        # Text-only cells are narrower since they just contain a word
        text_box_width = int(70 * scale)

        # Compute per-component widths
        comp_widths = []
        for component in sentence_pattern['components']:
            if component['type'] == 'text':
                comp_widths.append(text_box_width)
            else:
                comp_widths.append(box_size)
        n_boxes = len(comp_widths)
        total_width = sum(comp_widths) + (n_boxes - 1) * box_spacing
        start_x = margin_left + (content_width - total_width) // 2

        current_x = start_x

        # Place AAC symbols, theme images, and text words according to pattern
        for comp_idx, component in enumerate(sentence_pattern['components']):
            cw = comp_widths[comp_idx]
            box_y = strip_y + (strip_height - box_size - label_space) // 2

            # Draw box
            draw.rounded_rectangle(
                [current_x, box_y, current_x + cw, box_y + box_size],
                radius=int(6 * scale),
                fill='white',
                outline=hex_to_rgb(PURPLE),
                width=int(2 * scale)
            )
            
            if component['type'] == 'aac':
                # Place AAC symbol
                aac_key = component['word']
                if aac_key in aac_symbols:
                    img_copy = aac_symbols[aac_key].copy()
                    img_size = min(int(0.82 * box_size), int(80 * scale))
                    img_copy.thumbnail((img_size, img_size), Image.Resampling.LANCZOS)
                    img_x = current_x + (cw - img_copy.width) // 2
                    img_y = box_y + (box_size - img_copy.height) // 2
                    page.paste(img_copy, (img_x, img_y), img_copy)
                if show_aac_labels:
                    aac_label = normalize_text(component['word'].replace('_', ' '))
                    usable_nm_w = cw - int(10 * scale)
                    nm_font, _ = shrink_font_to_fit_with_pt(
                        aac_label,
                        base_pt=12,
                        max_width_px=usable_nm_w,
                        bold=False,
                        brand="poppins",
                        min_pt=8,
                    )
                    name_bbox = draw.textbbox((0, 0), aac_label, font=nm_font)
                    name_w = name_bbox[2] - name_bbox[0]
                    name_x = current_x + (cw - name_w) // 2
                    name_h = name_bbox[3] - name_bbox[1]
                    name_y = box_y + box_size + max(0, (label_space - name_h) // 2) - name_bbox[1]
                    draw.text((name_x, name_y), aac_label,
                              fill=hex_to_rgb(NAVY_BLUE), font=nm_font)

            elif component['type'] == 'text':
                # Text-only word (e.g. "am", "feel", "a") — no icon needed, just print the word centered in the cell
                text_word = normalize_text(str(component.get('word') or '').replace('_', ' '))
                usable_tw = cw - int(8 * scale)
                t_font, t_pt = shrink_font_to_fit_with_pt(
                    text_word,
                    base_pt=22,
                    max_width_px=usable_tw,
                    bold=True,
                    brand="poppins",
                    min_pt=12,
                )
                t_bbox = draw.textbbox((0, 0), text_word, font=t_font)
                t_w = t_bbox[2] - t_bbox[0]
                t_h = t_bbox[3] - t_bbox[1]
                t_x = current_x + (cw - t_w) // 2
                t_y = box_y + (box_size - t_h) // 2 - t_bbox[1]
                draw.text((t_x, t_y), text_word,
                          fill=hex_to_rgb(NAVY_BLUE), font=t_font)

            elif component['type'] == 'theme':
                # Place theme image (rotates through theme images)
                theme_img = theme_images[strip_idx % len(theme_images)]
                theme_copy = theme_img.copy()
                img_size = min(int(0.82 * box_size), int(80 * scale))
                theme_copy.thumbnail((img_size, img_size), Image.Resampling.LANCZOS)
                img_x = current_x + (cw - theme_copy.width) // 2
                img_y = box_y + (box_size - theme_copy.height) // 2
                page.paste(theme_copy, (img_x, img_y),
                          theme_copy if theme_copy.mode == 'RGBA' else None)

                # Add theme name below box
                theme_name_text = normalize_text(theme_names[strip_idx % len(theme_names)])
                usable_nm_w = cw - int(10 * scale)
                nm_font, nm_pt = shrink_font_to_fit_with_pt(
                    theme_name_text,
                    base_pt=12,
                    max_width_px=usable_nm_w,
                    bold=True,
                    brand="poppins",
                    min_pt=10,
                )
                name_bbox = draw.textbbox((0, 0), theme_name_text, font=nm_font)
                name_w = name_bbox[2] - name_bbox[0]
                name_x = current_x + (cw - name_w) // 2
                name_h = name_bbox[3] - name_bbox[1]
                name_y = box_y + box_size + max(0, (label_space - name_h) // 2) - name_bbox[1]
                draw.text((name_x, name_y), theme_name_text,
                         fill=hex_to_rgb(NAVY_BLUE), font=nm_font)
                if fit_warnings is not None and nm_pt < 10:
                    fit_warnings.append(f"Theme label '{theme_name_text}' shrunk to {nm_pt}pt on page {page_num}")

            current_x += cw + box_spacing

        # Cut guides between strips
        if show_cut_guides and strip_idx < strips_per_page - 1:
            y_mid = strip_y + strip_height + strip_spacing // 2
            _draw_dashed_h(y_mid, margin_left, img_width - margin_right)
            try:
                draw.text((margin_left + int(4 * scale), y_mid - int(8 * scale)), "Cut", fill=(150,150,150), font=fonts['instruction'])
            except Exception:
                pass
    
    # Instructions
    instr_y = strips_start_y + strips_per_page * (strip_height + strip_spacing) + int(10 * scale)
    instr_text = normalize_text("Cut sentence strip cards. Place AAC pieces in boxes to make sentences.")
    usable_instr_w = img_width - int(2 * 40 * scale)
    instr_font, instr_pt = shrink_font_to_fit_with_pt(
        instr_text,
        base_pt=14,
        max_width_px=usable_instr_w,
        bold=False,
        brand="poppins",
        min_pt=10,
    )
    instr_bbox = draw.textbbox((0, 0), instr_text, font=instr_font)
    instr_w = instr_bbox[2] - instr_bbox[0]
    draw.text(((img_width - instr_w) // 2, instr_y), instr_text, 
              fill=hex_to_rgb(NAVY_BLUE), font=instr_font)
    if fit_warnings is not None and instr_pt <= 12:
        fit_warnings.append(f"Instruction shrunk to {instr_pt}pt on page {page_num}: '{instr_text}'")
    
    # Universal header + footer frame with hero icon
    apply_small_wins_frame(
        page,
        product_title="AAC Sentence Strips",
        subtitle=theme_name,
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        draw_footer=True,
        draw_subtitle=True,
        header_left_icon=header_left_icon_img,
        header_height_px=int(0.92 * DPI),
        accent_margin_px=int(0.12 * DPI),
        footer_y_offset_px=int(0.08 * DPI),
    )
    # Trim/crop marks at page corners
    if show_trim_marks:
        _draw_trim_marks()
    
    return page


def create_cutouts_page(aac_symbols, theme_images, theme_names, page_num, pack_code, theme_name, *, total_pages: int, fit_warnings: list[str] | None = None,
                        header_left_icon_img: Image.Image | None = None, show_trim_marks: bool = True):
    """Create cut-out pieces page with 20 AAC symbols (4×5 grid)"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    header_h = int(0.80 * DPI)
    
    # Title (shrink-to-fit)
    title_text = normalize_text("Cut-Out Sentence Pieces")
    usable_title_w = img_width - int(2 * 30 * scale)
    title_font, title_pt = shrink_font_to_fit_with_pt(
        title_text,
        base_pt=24,
        max_width_px=usable_title_w,
        bold=True,
        brand="poppins",
        min_pt=18,
    )
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (img_width - title_w) // 2 - title_bbox[0]
    title_y = int(1.38 * DPI) - title_bbox[1]
    draw.text((title_x, title_y), title_text, fill=hex_to_rgb(TITLE_BLUE), font=title_font)
    if fit_warnings is not None and title_pt < 18:
        fit_warnings.append(f"Cutouts title shrunk to {title_pt}pt on page {page_num}: '{title_text}'")
    
    # Grid: 4 columns × 5 rows = 20 pieces
    cols = 4
    rows = 4
    spacing = int(12 * scale)
    start_y = int(1.82 * DPI)
    grid_bottom = img_height - safe_footer_inset_px() - int(0.42 * DPI)
    available_width = img_width - int(0.70 * DPI)
    available_height = grid_bottom - start_y
    box_size = min((available_width - (cols - 1) * spacing) // cols, (available_height - (rows - 1) * spacing) // rows)
    
    grid_width = cols * box_size + (cols - 1) * spacing
    grid_height = rows * box_size + (rows - 1) * spacing
    
    start_x = (img_width - grid_width) // 2
    
    # AAC word order (20 words)
    core_keys = ['I', 'see', 'want', 'like', 'dont_like']
    pieces = [(key.replace('_', ' '), aac_symbols.get(key)) for key in core_keys]
    pieces.extend((name, image) for name, image in zip(theme_names, theme_images))
    
    for idx in range(cols * rows):
        row = idx // cols
        col = idx % cols
        
        x = start_x + col * (box_size + spacing)
        y = start_y + row * (box_size + spacing)
        
        # Draw box
        draw.rounded_rectangle(
            [x, y, x + box_size, y + box_size],
            radius=int(10 * scale),
            fill='white',
            outline=hex_to_rgb(NAVY_BLUE),
            width=int(2 * scale)
        )
        
        # Place AAC symbol if available
        if idx < len(pieces):
            label, piece_image = pieces[idx]
            if piece_image is not None:
                padding = int(10 * scale)
                label_space = int(19 * scale)
                inner_size = box_size - (2 * padding) - label_space
                
                img_copy = piece_image.copy()
                if img_copy.width > 0 and img_copy.height > 0:
                    ratio = min(inner_size / img_copy.width, inner_size / img_copy.height)
                    img_copy = img_copy.resize((max(1, int(img_copy.width * ratio)), max(1, int(img_copy.height * ratio))), Image.Resampling.LANCZOS)
                
                img_x = x + (box_size - img_copy.width) // 2
                img_y = y + padding + max(0, (inner_size - img_copy.height) // 2)
                page.paste(img_copy, (img_x, img_y), img_copy)
                label = normalize_text(label)
                label_font, _ = shrink_font_to_fit_with_pt(label, base_pt=10, max_width_px=box_size - 2 * padding, bold=True, brand="poppins", min_pt=8)
                bounds = draw.textbbox((0, 0), label, font=label_font)
                label_w, label_h = bounds[2] - bounds[0], bounds[3] - bounds[1]
                label_x = x + (box_size - label_w) // 2 - bounds[0]
                label_y = y + box_size - padding - label_h - bounds[1]
                draw.text((label_x, label_y), label, fill=hex_to_rgb(NAVY_BLUE), font=label_font)
    
    # Instructions
    instr_y = start_y + grid_height + int(15 * scale)
    instr_text = normalize_text("Cut out the core and theme pieces. Place them over the matching strip guides.")
    usable_instr_w = img_width - int(2 * 30 * scale)
    instr_font, instr_pt = shrink_font_to_fit_with_pt(
        instr_text,
        base_pt=14,
        max_width_px=usable_instr_w,
        bold=False,
        brand="poppins",
        min_pt=10,
    )
    instr_bbox = draw.textbbox((0, 0), instr_text, font=instr_font)
    instr_w = instr_bbox[2] - instr_bbox[0]
    draw.text(((img_width - instr_w) // 2, instr_y), instr_text, 
              fill=hex_to_rgb(NAVY_BLUE), font=instr_font)
    if fit_warnings is not None and instr_pt <= 12:
        fit_warnings.append(f"Instruction shrunk to {instr_pt}pt on page {page_num}: '{instr_text}'")
    
    # Universal header/footer frame
    apply_small_wins_frame(
        page,
        product_title="Sentence Pieces",
        subtitle=theme_name,
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        draw_footer=True,
        draw_subtitle=True,
        header_left_icon=header_left_icon_img,
        header_height_px=int(0.92 * DPI),
        accent_margin_px=int(0.12 * DPI),
        footer_y_offset_px=int(0.08 * DPI),
    )
    if show_trim_marks:
        # simple trim marks
        draw.line([(20, 20), (60, 20)], fill=(150,150,150), width=int(2*scale))
        draw.line([(20, 20), (20, 60)], fill=(150,150,150), width=int(2*scale))
        draw.line([(img_width-20, 20), (img_width-60, 20)], fill=(150,150,150), width=int(2*scale))
        draw.line([(img_width-20, 20), (img_width-20, 60)], fill=(150,150,150), width=int(2*scale))
        draw.line([(20, img_height-20), (60, img_height-20)], fill=(150,150,150), width=int(2*scale))
        draw.line([(20, img_height-20), (20, img_height-60)], fill=(150,150,150), width=int(2*scale))
        draw.line([(img_width-20, img_height-20), (img_width-60, img_height-20)], fill=(150,150,150), width=int(2*scale))
        draw.line([(img_width-20, img_height-20), (img_width-20, img_height-60)], fill=(150,150,150), width=int(2*scale))
    
    return page


def create_storage_labels_page(page_num, pack_code, theme_name, *, total_pages: int, fit_warnings: list[str] | None = None,
                               header_left_icon_img: Image.Image | None = None, show_trim_marks: bool = True):
    """Create storage labels page"""
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    header_h = int(0.80 * DPI)
    
    # Title (shrink-to-fit)
    title_text = normalize_text("Organise Your Materials")
    usable_title_w = img_width - int(2 * 40 * scale)
    storage_title_font, storage_title_pt = shrink_font_to_fit_with_pt(
        title_text,
        base_pt=32,
        max_width_px=usable_title_w,
        bold=True,
        brand="poppins",
        min_pt=18,
    )
    title_bbox = draw.textbbox((0, 0), title_text, font=storage_title_font)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, int(1.22 * DPI)), title_text, 
              fill=hex_to_rgb(NAVY_BLUE), font=storage_title_font)
    if fit_warnings is not None and storage_title_pt <= 28:
        fit_warnings.append(f"Storage labels title shrunk to {storage_title_pt}pt on page {page_num}: '{title_text}'")
    
    # Two labels: AAC Pieces + Sentence Strips
    label_height = int(150 * scale)
    label_margin = int(40 * scale)
    labels_y = header_h + int(70 * scale)
    
    labels = [
        ("Sentence Pieces", "Core + Theme Words"),
        ("Sentence Strips", "Reviewed Patterns")
    ]
    
    for idx, (label_text, subtitle) in enumerate(labels):
        label_y = labels_y + idx * (label_height + int(30 * scale))
        
        # Label background
        draw.rounded_rectangle(
            [label_margin, label_y, img_width - label_margin, label_y + label_height],
            radius=int(15 * scale),
            fill='#EBF9F7',
            outline=hex_to_rgb(NAVY_BLUE),
            width=int(3 * scale)
        )
        
        # Label text (shrink-to-fit)
        lbl_txt = normalize_text(label_text)
        usable_lbl_w = img_width - 2 * label_margin - int(20 * scale)
        lbl_font, lbl_pt = shrink_font_to_fit_with_pt(
            lbl_txt,
            base_pt=32,
            max_width_px=usable_lbl_w,
            bold=True,
            brand="poppins",
            min_pt=18,
        )
        text_bbox = draw.textbbox((0, 0), lbl_txt, font=lbl_font)
        text_w = text_bbox[2] - text_bbox[0]
        draw.text(((img_width - text_w) // 2, label_y + int(30 * scale)), lbl_txt, 
                  fill=hex_to_rgb(NAVY_BLUE), font=lbl_font)
        if fit_warnings is not None and lbl_pt <= 28:
            fit_warnings.append(f"Storage label header shrunk to {lbl_pt}pt on page {page_num}: '{lbl_txt}'")
        
        # Subtitle (shrink-to-fit)
        sub_txt = normalize_text(subtitle)
        usable_sub_w = img_width - 2 * label_margin - int(30 * scale)
        sub_font, sub_pt = shrink_font_to_fit_with_pt(
            sub_txt,
            base_pt=14,
            max_width_px=usable_sub_w,
            bold=False,
            brand="poppins",
            min_pt=8,
        )
        sub_bbox = draw.textbbox((0, 0), sub_txt, font=sub_font)
        sub_w = sub_bbox[2] - sub_bbox[0]
        draw.text(((img_width - sub_w) // 2, label_y + int(75 * scale)), sub_txt, 
                  fill='#666666', font=sub_font)
        if fit_warnings is not None and sub_pt <= 10:
            fit_warnings.append(f"Storage label subtitle shrunk to {sub_pt}pt on page {page_num}: '{sub_txt}'")
        
        # Pack info (shrink-to-fit, no warning)
        pack_info = normalize_text(f"{theme_name} - {pack_code}")
        usable_pack_w = img_width - 2 * label_margin - int(30 * scale)
        pack_font, _ = shrink_font_to_fit_with_pt(
            pack_info,
            base_pt=10,
            max_width_px=usable_pack_w,
            bold=False,
            brand="poppins",
            min_pt=8,
        )
        pack_bbox = draw.textbbox((0, 0), pack_info, font=pack_font)
        pack_w = pack_bbox[2] - pack_bbox[0]
        draw.text(((img_width - pack_w) // 2, label_y + int(110 * scale)), pack_info, 
                  fill='#888888', font=pack_font)
    
    # Universal header/footer frame
    apply_small_wins_frame(
        page,
        product_title="Storage Labels",
        subtitle=theme_name,
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        draw_footer=True,
        draw_subtitle=True,
        header_left_icon=header_left_icon_img,
        header_height_px=int(0.92 * DPI),
        accent_margin_px=int(0.12 * DPI),
        footer_y_offset_px=int(0.08 * DPI),
    )
    if show_trim_marks:
        # simple trim marks
        draw.line([(20, 20), (60, 20)], fill=(150,150,150), width=int(2*scale))
        draw.line([(20, 20), (20, 60)], fill=(150,150,150), width=int(2*scale))
        draw.line([(img_width-20, 20), (img_width-60, 20)], fill=(150,150,150), width=int(2*scale))
        draw.line([(img_width-20, 20), (img_width-20, 60)], fill=(150,150,150), width=int(2*scale))
        draw.line([(20, img_height-20), (60, img_height-20)], fill=(150,150,150), width=int(2*scale))
        draw.line([(20, img_height-20), (20, img_height-60)], fill=(150,150,150), width=int(2*scale))
        draw.line([(img_width-20, img_height-20), (img_width-60, img_height-20)], fill=(150,150,150), width=int(2*scale))
        draw.line([(img_width-20, img_height-20), (img_width-20, img_height-60)], fill=(150,150,150), width=int(2*scale))
    
    return page


# Define 8 sentence patterns
SENTENCE_PATTERNS = [
    {
        'display': 'I see ___',
        'description': 'Practice identifying and naming',
        'components': [
            {'type': 'aac', 'word': 'I'},
            {'type': 'aac', 'word': 'see'},
            {'type': 'theme', 'word': None}
        ],
        'aac_words': ['I', 'see']
    },
    {
        'display': 'I want ___',
        'description': 'Practice requesting',
        'components': [
            {'type': 'aac', 'word': 'I'},
            {'type': 'aac', 'word': 'want'},
            {'type': 'theme', 'word': None}
        ],
        'aac_words': ['I', 'want']
    },
    {
        'display': 'I like ___',
        'description': 'Practice expressing preferences',
        'components': [
            {'type': 'aac', 'word': 'I'},
            {'type': 'aac', 'word': 'like'},
            {'type': 'theme', 'word': None}
        ],
        'aac_words': ['I', 'like']
    },
    {
        'display': "I don't like ___",
        'description': 'Practice expressing dislikes',
        'components': [
            {'type': 'aac', 'word': 'I'},
            {'type': 'aac', 'word': 'dont_like'},
            {'type': 'theme', 'word': None}
        ],
        'aac_words': ['I', 'dont_like']
    },
    {
        'display': '___ is big',
        'description': 'Practice describing size',
        'components': [
            {'type': 'theme', 'word': None},
            {'type': 'aac', 'word': 'big'}
        ],
        'aac_words': ['big']
    },
    {
        'display': '___ is small',
        'description': 'Practice describing size',
        'components': [
            {'type': 'theme', 'word': None},
            {'type': 'aac', 'word': 'small'}
        ],
        'aac_words': ['small']
    },
    {
        'display': 'I want more ___',
        'description': 'Practice requesting more',
        'components': [
            {'type': 'aac', 'word': 'I'},
            {'type': 'aac', 'word': 'want'},
            {'type': 'aac', 'word': 'more'},
            {'type': 'theme', 'word': None}
        ],
        'aac_words': ['I', 'want', 'more']
    },
    {
        'display': '___ can go',
        'description': 'Practice action words',
        'components': [
            {'type': 'theme', 'word': None},
            {'type': 'aac', 'word': 'go'}
        ],
        'aac_words': ['go']
    },
    {
        'display': 'I am ___',
        'description': 'Practice expressing identity and states (e.g. I am scared)',
        'components': [
            {'type': 'aac', 'word': 'I'},
            {'type': 'text', 'word': 'am'},
            {'type': 'theme', 'word': None}
        ],
        'aac_words': ['I']
    },
    {
        'display': 'I feel ___',
        'description': 'Practice expressing feelings (e.g. I feel scared, I feel happy)',
        'components': [
            {'type': 'aac', 'word': 'I'},
            {'type': 'text', 'word': 'feel'},
            {'type': 'theme', 'word': None}
        ],
        'aac_words': ['I']
    }
]


def _theme_dir_for_images(images_folder):
    path = Path(images_folder).resolve()
    if path.name == "icons" and path.parent.name == ".sf_build":
        return path.parent.parent
    return path.parent


def _load_sentence_building_config(images_folder):
    source = _theme_dir_for_images(images_folder) / "config" / "sentence_building.json"
    if not source.exists():
        raise FileNotFoundError(f"Missing reviewed sentence-building data: {source}")
    data = json.loads(source.read_text(encoding="utf-8"))
    if data.get("reading_rope") != ["Language Structures", "Vocabulary"]:
        raise ValueError("Sentence-building data has an invalid Reading Rope claim")
    return data, source


def generate_aac_pack(images_folder, pack_code="BB01", theme_name="Brown Bear", *,
                      strips_per_page: int = 6,
                      show_cut_guides: bool = True,
                      show_pattern_labels_on_strip: bool = True,
                      show_trim_marks: bool = True,
                      show_aac_labels: bool = False):
    """Generate complete AAC Sentence Strips pack with 20 AAC words"""
    
    global aac_symbols

    try:
        print(f"\n{'='*70}")
        print(f"  📱 GENERATING AAC SENTENCE BUILDING STRIPS: {pack_code}")
        print(f"  Theme: {theme_name}")
        print(f"  Reviewed sentence patterns with core and theme pieces")
        print(f"{'='*70}\n")
        sentence_config, sentence_source = _load_sentence_building_config(images_folder)

        # Find AAC folder
        studioforge_root = Path(__file__).resolve().parents[1]
        project_root = studioforge_root.parent
        search_paths = [
            # relative to current working directory (when run from a book folder)
            Path("../aac_core_words"),
            Path("../AAC_core_words"),
            Path("aac_core_words"),
            Path("AAC_core_words"),
            Path("../AAC_CORE_WORDS"),
            Path("AAC_CORE_WORDS"),
            # relative to Studioforge root
            studioforge_root / "aac_core_words",
            studioforge_root / "AAC_core_words",
            studioforge_root / "assets" / "aac_core_words",
            studioforge_root / "assets" / "AAC_core_words",
            studioforge_root / "assets" / "AAC_CORE_WORDS",
            # BoardReady legacy under Studioforge
            studioforge_root / "BoardReady" / "boardready" / "aac_core_words",
            studioforge_root / "BoardReady" / "boardready" / "AAC_core_words",
            # Canonical assets at project root
            project_root / "assets" / "global" / "aac_core",
            project_root / "assets" / "global" / "aac_core_text",
            # Fallbacks directly under project root
            project_root / "aac_core_words",
            project_root / "AAC_core_words",
            project_root / "assets" / "aac_core_words",
            project_root / "assets" / "AAC_core_words",
            project_root / "assets" / "AAC_CORE_WORDS",
            project_root / "BoardReady" / "boardready" / "aac_core_words",
            project_root / "BoardReady" / "boardready" / "AAC_core_words",
        ]

        aac_folder = None
        for path in search_paths:
            try:
                if path.exists():
                    aac_folder = path
                    break
            except Exception:
                continue

        if not aac_folder:
            print(f"❌ ERROR: AAC symbols folder not found!")
            print(f"   Looked in:")
            for p in search_paths:
                try:
                    print(f"   - {str(p)}")
                except Exception:
                    pass
            print(f"\n   Please create a folder 'aac_core_words' with 20 AAC symbol PNGs")
            print(f"   Required words: I, see, want, like, don't like, big, small,")
            print(f"                   good, more, go, stop, help, eat, drink, play,")
            print(f"                   happy, sad, hot, cold, turn")
            return False

        print(f"📁 Found AAC folder: {aac_folder}")

        symbols_root = studioforge_root / "assets" / "symbols" / "png"
        if not symbols_root.exists():
            symbols_root = project_root / "assets" / "symbols" / "png"
        symbol_index: dict[str, Path] = {}
        if symbols_root.exists():
            try:
                for p in symbols_root.rglob("*.png"):
                    stem = p.stem.lower().replace(" ", "_").replace("-", "_")
                    if stem not in symbol_index:
                        symbol_index[stem] = p
            except Exception:
                symbol_index = {}

        def _find_symbol_anywhere(filename: str) -> Path | None:
            want = str(filename).strip()
            if want.lower().endswith(".png"):
                want = want[:-4]
            want_norm = want.lower().replace(" ", "_").replace("-", "_")
            return symbol_index.get(want_norm)

        # Load all 20 AAC symbols
        core_words = {
        'I': ['I.png', 'i.png'],
        'see': ['see.png', 'See.png'],
        'want': ['want.png', 'Want.png'],
        'like': ['like.png', 'Like.png'],
        'dont_like': ['dont_like.png', 'Dont_like.png', 'dont-like.png', "don't like.png"],
        'big': ['big.png', 'Big.png'],
        'small': ['small.png', 'Small.png'],
        'good': ['good.png', 'Good.png'],
        'more': ['more.png', 'More.png'],
        'go': ['go.png', 'Go.png'],
        'stop': ['stop.png', 'Stop.png'],
        'help': ['help.png', 'Help.png'],
        'eat': ['eat.png', 'Eat.png'],
        'drink': ['drink.png', 'Drink.png'],
        'play': ['play.png', 'Play.png'],
        'happy': ['happy.png', 'Happy.png'],
        'sad': ['sad.png', 'Sad.png'],
        'hot': ['hot.png', 'Hot.png'],
        'cold': ['cold.png', 'Cold.png'],
        'turn': ['turn.png', 'Turn.png']
        }

        aac_symbols = {}
        missing_words = []

        for word, filenames in core_words.items():
            found = False
            for filename in filenames:
                symbol_path = aac_folder / filename
                if symbol_path.exists():
                    img = Image.open(symbol_path)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    aac_symbols[word] = img
                    print(f"   ✓ {word}")
                    found = True
                    break
                alt = _find_symbol_anywhere(filename)
                if alt and alt.exists():
                    img = Image.open(alt)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    aac_symbols[word] = img
                    print(f"   ✓ {word}")
                    # Auto-copy fallback into canonical aac_core to prevent future warnings
                    try:
                        canonical_dir = project_root / "assets" / "global" / "aac_core"
                        canonical_dir.mkdir(parents=True, exist_ok=True)
                        dest = canonical_dir / filename
                        if not dest.exists():
                            shutil.copyfile(alt, dest)
                            print(f"     ↳ copied to canonical aac_core: {dest.name}")
                    except Exception:
                        pass
                    found = True
                    break
            if not found:
                missing_words.append(word)
                print(f"   ⚠ Missing: {word}")

        if missing_words:
            print(f"\n⚠️  WARNING: Missing {len(missing_words)} AAC symbols")
            print(f"   Missing: {', '.join(missing_words)}")
            print(f"   Continuing with available symbols...")

        if 'I' not in aac_symbols:
            print(f"\n❌ ERROR: 'I' symbol is required!")
            return False

        # Load theme images
        images_path = Path(images_folder)
        if not images_path.exists():
            print(f"❌ ERROR: Images folder not found: {images_folder}")
            return False

        theme_images = []
        theme_names = []
        theme_keys = []
        for entry in sentence_config.get("theme_items") or []:
            key = str(entry.get("image_key") or "").strip()
            label = str(entry.get("label") or "").strip()
            img_file = images_path / f"{key}.png"
            if not key or not label or not img_file.exists():
                print(f"❌ ERROR: Missing reviewed sentence-building image: {key or label or '(blank)'}")
                return False
            img = Image.open(img_file)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            theme_keys.append(key)
            theme_images.append(img)
            theme_names.append(label)
        if len(theme_images) < 4:
            print(f"❌ ERROR: Need at least 4 reviewed images, found {len(theme_images)}")
            return False

        print(f"\n📝 Theme images: {', '.join(theme_names)}\n")

        # Create OUTPUT folder
        out_dir = _theme_dir_for_images(images_folder) / "OUTPUT"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Compute total pages (cover + patterns + cutouts + storage)
        pattern_configs = {str(entry.get("display") or ""): entry for entry in sentence_config.get("patterns") or []}
        active_patterns = [pattern for pattern in SENTENCE_PATTERNS if pattern["display"] in pattern_configs]
        if not active_patterns:
            print("❌ ERROR: No reviewed sentence patterns were selected")
            return False
        content_pages = len(active_patterns) + 2
        total_pages = content_pages  # no teacher cover

        # Resolve header icon for the page accent strip
        hero_path_str = None
        header_icon_img = None
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
                assets_base = Path(__file__).resolve().parents[1] / "assets"
                if not assets_base.exists():
                    assets_base = Path(__file__).resolve().parents[2] / "assets"
                tdir = assets_base / "themes" / slug_guess
                hero_candidates = [
                    tdir / "hero_header.png",
                    tdir / "heroes" / "hero_header.png",
                    tdir / "characters" / "hero_header.png",
                    tdir / "hero.png",
                    tdir / "heroes" / "hero.png",
                    tdir / "characters" / "hero.png",
                    tdir / "header_icon.png",
                ]
                for hp in hero_candidates:
                    if hp.exists():
                        hero_path_str = str(hp)
                        break
            # Open header icon if available
            try:
                if hero_path_str:
                    _im = Image.open(hero_path_str)
                    header_icon_img = _im.convert('RGBA') if _im.mode != 'RGBA' else _im
            except Exception:
                header_icon_img = None
        except Exception:
            hero_path_str = None
            header_icon_img = None

        saved_pages: list = []
        text_fit_warnings: list[str] = []
        page_num = 1

        # Generate 8 sentence pattern pages
        for idx, pattern in enumerate(active_patterns, 1):
            print(f"📄 Page {page_num}: {pattern['display']}...")
            allowed = set(pattern_configs[pattern["display"]].get("items") or [])
            selected = [(image, name) for key, image, name in zip(theme_keys, theme_images, theme_names) if key in allowed]
            if not selected:
                print(f"❌ ERROR: No reviewed theme items for pattern: {pattern['display']}")
                return False
            pattern_images = [image for image, _name in selected]
            pattern_names = [name for _image, name in selected]
            page = create_sentence_strip_page(
                pattern,
                pattern['aac_words'],
                pattern_images,
                pattern_names,
                page_num,
                pack_code,
                theme_name,
                total_pages=total_pages,
                fit_warnings=text_fit_warnings,
                header_left_icon_img=header_icon_img,
                strips_per_page=strips_per_page,
                show_cut_guides=show_cut_guides,
                show_pattern_labels_on_strip=show_pattern_labels_on_strip,
                show_trim_marks=show_trim_marks,
                show_aac_labels=show_aac_labels,
            )
            saved_pages.append(page)
            page_num += 1

        # Cut-outs page
        print(f"\n📄 Page {page_num}: Cut-out core and theme pieces...")
        cutouts = create_cutouts_page(
            aac_symbols, theme_images, theme_names, page_num, pack_code, theme_name,
            total_pages=total_pages, fit_warnings=text_fit_warnings,
            header_left_icon_img=header_icon_img, show_trim_marks=show_trim_marks
        )
        saved_pages.append(cutouts)
        page_num += 1

        # Storage labels
        print(f"📄 Page {page_num}: Storage labels...")
        storage = create_storage_labels_page(
            page_num, pack_code, theme_name, total_pages=total_pages,
            fit_warnings=text_fit_warnings, header_left_icon_img=header_icon_img,
            show_trim_marks=show_trim_marks
        )
        saved_pages.append(storage)

        print(f"\n   ✅ {len(saved_pages)} pages generated\n")

        # Create COLOR PDF
        print(f"📄 Creating COLOR PDF...")
        color_pdf = out_dir / f"{pack_code}_AAC_SentenceStrips_COLOR.pdf"
        c = canvas.Canvas(str(color_pdf), pagesize=letter)
        for page in saved_pages:
            img_buffer = io.BytesIO()
            page.save(img_buffer, format='PNG', dpi=(DPI, DPI))
            img_buffer.seek(0)
            c.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
            c.showPage()
        c.save()
        print(f"   ✅ {str(color_pdf)}")

        # Create B&W PDF
        print(f"\n🖤 Creating B&W PDF...")
        bw_pdf = out_dir / f"{pack_code}_AAC_SentenceStrips_BW.pdf"
        c_bw = canvas.Canvas(str(bw_pdf), pagesize=letter)
        for page in saved_pages:
            gray_page = page.convert('L')
            img_buffer = io.BytesIO()
            gray_page.save(img_buffer, format='PNG', dpi=(DPI, DPI))
            img_buffer.seek(0)
            c_bw.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
            c_bw.showPage()
        c_bw.save()
        print(f"   ✅ {str(bw_pdf)}")

        # Create PREVIEW PDF
        print(f"\n🔒 Creating PREVIEW PDF...")
        preview_pdf = out_dir / f"{pack_code}_AAC_SentenceStrips_PREVIEW.pdf"
        c_prev = canvas.Canvas(str(preview_pdf), pagesize=letter)
        preview_indices = [1, 3, 5]  # cover + two sample strips
        for idx in preview_indices:
            if 0 <= idx < len(saved_pages):
                img_buffer = io.BytesIO()
                saved_pages[idx].save(img_buffer, format='PNG', dpi=(DPI, DPI))
                img_buffer.seek(0)
                c_prev.drawImage(ImageReader(img_buffer), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
                c_prev.saveState()
                try:
                    c_prev.setFont("Helvetica-Bold", 140)
                    c_prev.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
                except Exception:
                    c_prev.setFont("Helvetica-Bold", 110)
                    c_prev.setFillColorRGB(0.6, 0.6, 0.6)
                c_prev.translate(PAGE_WIDTH/2, PAGE_HEIGHT/2)
                c_prev.rotate(45)
                c_prev.drawCentredString(0, 0, "PREVIEW")
                c_prev.restoreState()
                c_prev.showPage()
        c_prev.save()
        print(f"   ✅ {str(preview_pdf)}")

        # BuildResult manifest with warnings
        try:
            thumbs = [str(p) for p in sorted((out_dir / "thumbnails").glob(f"{pack_code}_AAC_thumb*.png"))]
            try:
                warnings = assess_files(
                    product_name="AAC Sentence Strips",
                    color_pdf=str(color_pdf),
                    bw_pdf=str(bw_pdf),
                    preview_pdf=str(preview_pdf),
                    expected_pages=None,
                )
            except Exception:
                warnings = []
            try:
                warnings.extend(text_fit_warnings)
            except Exception:
                pass
            manifest = {
                "schema_version": 1,
                "status": "pilot_review",
                "product_name": "AAC Sentence Building Strips",
                "slug": _theme_dir_for_images(images_folder).name if images_folder else None,
                "pack_code": pack_code,
                "page_count": len(saved_pages),
                "reading_rope": ["Language Structures", "Vocabulary"],
                "teacher_review_required": True,
                "source": str(sentence_source),
                "source_sha256": hashlib.sha256(sentence_source.read_bytes()).hexdigest(),
                "files": {
                    "color_pdf": str(color_pdf),
                    "bw_pdf": str(bw_pdf),
                    "preview_pdf": str(preview_pdf),
                    "thumbnails": thumbs,
                },
                "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": warnings},
            }
            (out_dir / f"{pack_code}_AAC_SentenceStrips_BuildResult.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

        # Thumbnails
        thumb_dir = out_dir / "thumbnails"
        thumb_dir.mkdir(parents=True, exist_ok=True)
        for i, idx in enumerate(preview_indices, 1):
            if 0 <= idx < len(saved_pages):
                im = saved_pages[idx].copy()
                im.thumbnail((500, 647), Image.Resampling.LANCZOS)
                im.save(thumb_dir / f"{pack_code}_AAC_thumb{i}.png", "PNG")

        print(f"\n{'='*70}")
        print(f"  ✅ AAC SENTENCE STRIPS COMPLETE!")
        print(f"  📱 {len(saved_pages)} pages with {len(active_patterns)} reviewed patterns and matching pieces")
        print(f"{'='*70}\n")

        return True
    except Exception:
        print("\n❌ ERROR: AAC Sentence Strips generator crashed")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate AAC Sentence Strips pack")
    parser.add_argument("pack_code", nargs="?", default="BB01", help="Pack code, e.g., STEL-AAC")
    parser.add_argument("theme_name", nargs="?", default="Brown Bear", help="Theme/book title")
    parser.add_argument("--images", default="images", help="Images folder path")
    parser.add_argument("--strips", type=int, default=6, help="Strips per page (3-8)")
    parser.add_argument("--aac-labels", action="store_true", help="Show AAC word labels under symbols")
    parser.add_argument("--no-cut-guides", action="store_true", help="Hide dashed cut guides between strips")
    parser.add_argument("--no-trim-marks", action="store_true", help="Hide trim/crop marks at corners")
    parser.add_argument("--no-strip-labels", action="store_true", help="Hide pattern label on each strip")
    args = parser.parse_args()

    success = generate_aac_pack(
        args.images,
        args.pack_code,
        args.theme_name,
        strips_per_page=args.strips,
        show_cut_guides=not args.no_cut_guides,
        show_pattern_labels_on_strip=not args.no_strip_labels,
        show_trim_marks=not args.no_trim_marks,
        show_aac_labels=args.aac_labels,
    )

    if success:
        print("🎉 ALL DONE! CHECK OUTPUT FOLDER!")
    else:
        print("\n❌ FAILED - check error messages above")
        import sys
        sys.exit(1)
