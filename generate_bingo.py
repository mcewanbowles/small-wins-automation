#!/usr/bin/env python3
"""Generate Bingo Level PDFs for Brown Bear theme.

Outputs per-level PDFs (Levels 1-5) in both color and B&W modes.
- Level 1: 3x3 grid, real photos (player + caller), FREE center
- Level 2: 3x4 grid, player icons (no text); caller icons (no text)
- Level 3: 3x4 grid, player real photos; caller icons
- Level 4: 4x4 grid, player real photos + words; caller icons
- Level 5: 4x4 grid, text-only (player + caller)

Each level PDF contains 8 unique cards + 1 calling cards page.

Output:
  samples/brown_bear/bingo/brown_bear_bingo_level{N}_{mode}.pdf
Also copies to review_pdfs/ for convenience.
"""

from __future__ import annotations

import io
import random
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from utils.sws_design import apply_small_wins_frame


PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300


_FONT_COMIC = "C:/Windows/Fonts/comic.ttf"
_FONT_COMIC_BOLD = "C:/Windows/Fonts/comicbd.ttf"
_FONT_ARIAL = "C:/Windows/Fonts/arial.ttf"
_FONT_ARIAL_BOLD = "C:/Windows/Fonts/arialbd.ttf"

TITLE_BLUE = "#2B4C7E"
NAVY_BLUE = "#1E3A5F"
STEEL_BLUE = "#5B7AA0"
PURPLE = "#6B5BE2"
LIGHT_BLUE = "#EEF4FB"


LEVEL_COLORS = {
    1: "#FF8C42",
    2: "#4A90E2",
    3: "#7CB342",
    4: "#9C27B0",
    5: "#E74C3C",
}


def hex_to_rgb(h: str):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _display_name(name: str) -> str:
    normalized = " ".join(str(name).strip().split())
    if normalized.lower() == "see":
        return "Eyes"
    return normalized


def _load_fonts() -> dict[str, ImageFont.ImageFont]:
    s = DPI / 72
    try:
        return {
            'title': ImageFont.truetype(_FONT_COMIC_BOLD, int(28 * s)),
            'subtitle': ImageFont.truetype(_FONT_COMIC, int(14 * s)),
            'bingo': ImageFont.truetype(_FONT_COMIC_BOLD, int(48 * s)),
            'free': ImageFont.truetype(_FONT_COMIC_BOLD, int(20 * s)),
            'word': ImageFont.truetype(_FONT_COMIC_BOLD, int(11 * s)),
            'word_only': ImageFont.truetype(_FONT_COMIC_BOLD, int(14 * s)),
            'calling_big': ImageFont.truetype(_FONT_COMIC_BOLD, int(22 * s)),
            'calling_label': ImageFont.truetype(_FONT_COMIC_BOLD, int(12 * s)),
            'label': ImageFont.truetype(_FONT_COMIC, int(11 * s)),
            'footer': ImageFont.truetype(_FONT_COMIC, int(10 * s)),
            'copyright': ImageFont.truetype(_FONT_COMIC, int(8 * s)),
        }
    except Exception:
        return {
            'title': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(28 * s)),
            'subtitle': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(14 * s)),
            'bingo': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(48 * s)),
            'free': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(20 * s)),
            'word': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(11 * s)),
            'word_only': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(14 * s)),
            'calling_big': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(22 * s)),
            'calling_label': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(12 * s)),
            'label': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(11 * s)),
            'footer': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(10 * s)),
            'copyright': ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(8 * s)),
        }


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int, *, max_lines: int = 2) -> list[str]:
    words = [w for w in str(text).strip().split() if w]
    if not words:
        return [""]

    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        test = " ".join(cur + [w])
        tw, _ = _text_size(draw, test, font)
        if tw <= max_w or not cur:
            cur.append(w)
            continue
        lines.append(" ".join(cur))
        cur = [w]
        if len(lines) >= max_lines - 1:
            break

    if cur and len(lines) < max_lines:
        lines.append(" ".join(cur))

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    return lines


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    font_path: str,
    max_px: int,
    min_px: int,
    max_w: int,
    max_h: int,
) -> ImageFont.ImageFont:
    if max_w <= 0 or max_h <= 0:
        return ImageFont.truetype(font_path, min_px)

    lo = min_px
    hi = max(min_px, max_px)
    best = ImageFont.truetype(font_path, lo)

    while lo <= hi:
        mid = (lo + hi) // 2
        f = ImageFont.truetype(font_path, mid)
        tw, th = _text_size(draw, text, f)
        if tw <= max_w and th <= max_h:
            best = f
            lo = mid + 1
        else:
            hi = mid - 1

    return best


def _resize_cover(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resize to fill the target box (like CSS object-fit: cover), then center-crop."""
    target_w = max(1, int(target_w))
    target_h = max(1, int(target_h))
    if img.width <= 0 or img.height <= 0:
        return img

    scale = max(target_w / img.width, target_h / img.height)
    # Cap upscale to avoid blowing up small source images (keeps file sizes sane).
    scale = min(scale, 2.5)
    new_w = max(1, int(round(img.width * scale)))
    new_h = max(1, int(round(img.height * scale)))
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    left = max(0, (new_w - target_w) // 2)
    top = max(0, (new_h - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


@dataclass(frozen=True)
class BingoLevelSpec:
    level: int
    rows: int
    cols: int
    images: str  # 'icons' | 'real' | 'none'
    calling_images: str | None  # 'icons' | 'real' | None (defaults to player images)
    calling_style: str | None  # None | 'large_text_small_icon'
    words: bool
    free_center: bool
    label: str


LEVEL_SPECS: dict[int, BingoLevelSpec] = {
    1: BingoLevelSpec(1, 3, 3, 'real', None, None, False, True, 'Real_Photos'),
    2: BingoLevelSpec(2, 3, 4, 'icons', 'icons', None, False, False, 'Icons_Only'),
    3: BingoLevelSpec(3, 3, 4, 'real', 'icons', None, False, False, 'Real_Photos'),
    4: BingoLevelSpec(4, 4, 4, 'icons_with_labels', 'icons_with_labels', None, True, False, 'Icons_With_Labels'),
    5: BingoLevelSpec(5, 4, 4, 'none', None, None, True, False, 'Text_Only'),
}


def _load_items(theme_id: str, kind: str, *, mode: str) -> list[dict]:
    root = Path(__file__).parent
    if kind == 'icons':
        icons_colored_dir = root / 'assets' / 'themes' / theme_id / 'icons_colored'
        legacy_icons_dir = root / 'assets' / 'themes' / theme_id / 'icons'
        folder = icons_colored_dir if icons_colored_dir.exists() else legacy_icons_dir
    elif kind == 'icons_with_labels':
        labeled_dir = root / 'assets' / 'themes' / theme_id / 'icons_with_labels'
        icons_colored_dir = root / 'assets' / 'themes' / theme_id / 'icons_colored'
        legacy_icons_dir = root / 'assets' / 'themes' / theme_id / 'icons'
        if labeled_dir.exists():
            folder = labeled_dir
        else:
            folder = icons_colored_dir if icons_colored_dir.exists() else legacy_icons_dir
    elif kind == 'real':
        folder = root / 'assets' / 'themes' / theme_id / 'real_images'
    else:
        return []

    items: list[dict] = []
    for f in sorted(folder.glob('*.png')):
        if f.name.startswith('.'):
            continue
        name = _display_name(f.stem.replace('_', ' ').replace('-', ' ').title())
        img = Image.open(f).convert('RGBA')
        if mode == 'bw':
            img = img.convert('L').convert('RGBA')
        items.append({'name': name, 'img': img, 'path': f})
    return items


def _bear_icon_path(theme_id: str) -> Path:
    root = Path(__file__).parent
    icons_colored_dir = root / 'assets' / 'themes' / theme_id / 'icons_colored'
    legacy_icons_dir = root / 'assets' / 'themes' / theme_id / 'icons'
    folder = icons_colored_dir if icons_colored_dir.exists() else legacy_icons_dir
    p = folder / 'Brown bear.png'
    if not p.exists():
        p = folder / 'Brown Bear.png'
    return p


def _load_bear_icon(*, theme_id: str, mode: str) -> Image.Image | None:
    p = _bear_icon_path(theme_id)
    if not p.exists():
        return None

    img = Image.open(p).convert('RGBA')
    if mode == 'bw':
        img = img.convert('L').convert('RGBA')

    # Make near-white background transparent so the accent strip shows through.
    # (Boardmaker exports sometimes have a white rectangle.)
    r, g, b, _a = img.split()
    # Only treat pixels as "background" if all channels are near-white.
    bg = Image.eval(r, lambda v: 255 if v > 245 else 0)
    bg = ImageChops.multiply(bg, Image.eval(g, lambda v: 255 if v > 245 else 0))
    bg = ImageChops.multiply(bg, Image.eval(b, lambda v: 255 if v > 245 else 0))
    alpha = ImageOps.invert(bg.convert('L'))
    img.putalpha(alpha)

    # Flip so the nose points right.
    img = ImageOps.mirror(img)
    return img


def _trim_for_max_size(img: Image.Image) -> Image.Image:
    """Crop away transparent/near-white margins so differently-padded assets size consistently."""
    im = img.convert('RGBA')
    r, g, b, a = im.split()

    def _corner_bg_rgb(src: Image.Image) -> tuple[int, int, int]:
        w, h = src.size
        pts = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
        rgbs: list[tuple[int, int, int]] = []
        for x, y in pts:
            pr, pg, pb, pa = src.getpixel((x, y))
            if pa > 10:
                rgbs.append((pr, pg, pb))
        if not rgbs:
            return (255, 255, 255)
        rr = sum(p[0] for p in rgbs) // len(rgbs)
        gg = sum(p[1] for p in rgbs) // len(rgbs)
        bb = sum(p[2] for p in rgbs) // len(rgbs)
        return (rr, gg, bb)

    # Base opaque mask.
    opaque = a.point(lambda v: 255 if v > 10 else 0)

    # Trim transparent padding first.
    bbox_alpha = opaque.getbbox()
    work = im.crop(bbox_alpha) if bbox_alpha else im

    # Try trimming solid background padding (even if not white) using a corner-estimated bg color.
    bg_rgb = _corner_bg_rgb(work)
    bg_img = Image.new('RGB', work.size, bg_rgb)
    work_rgb = work.convert('RGB')
    diff = ImageChops.difference(work_rgb, bg_img).convert('L')

    # Keep pixels that differ from bg by a small threshold.
    diff = diff.point(lambda v: 255 if v > 18 else 0)

    # Also require opacity (avoid pulling in transparent pixels).
    work_a = work.split()[3]
    work_opaque = work_a.point(lambda v: 255 if v > 10 else 0)
    fg = ImageChops.multiply(diff, work_opaque)

    bbox = fg.getbbox()
    if bbox is None:
        # Fallback: trim near-white (helps some Boardmaker exports)
        rr, gg, bb, aa = work.split()
        not_white_r = rr.point(lambda v: 255 if v < 245 else 0)
        not_white_g = gg.point(lambda v: 255 if v < 245 else 0)
        not_white_b = bb.point(lambda v: 255 if v < 245 else 0)
        not_white = ImageChops.lighter(not_white_r, ImageChops.lighter(not_white_g, not_white_b))
        fg2 = ImageChops.multiply(not_white, work_opaque)
        bbox = fg2.getbbox()

    if bbox is None:
        return work

    return work.crop(bbox)


def _draw_bingo_card(
    *,
    items: list[dict],
    rows: int,
    cols: int,
    level: int,
    level_label: str,
    card_num: int,
    mode: str,
    theme_name: str,
    pack_code: str,
    page_num: int,
    total_pages: int,
    words: bool,
    images: bool,
    free_center: bool,
    accent_color_hex: str,
    image_fit: str = 'contain',
):
    w = int(PAGE_WIDTH * DPI / 72)
    h = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(page)
    s = DPI / 72
    fonts = _load_fonts()

    bear = _load_bear_icon(theme_id='brown_bear', mode=mode)
    apply_small_wins_frame(
        page,
        product_title=f"{theme_name} Bingo",
        subtitle="",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=level,
        accent_color_hex=accent_color_hex,
        footer_title=f"{theme_name} Bingo | Card {card_num}",
        header_left_icon=bear,
        header_left_icon_flip=False,
        footer_y_offset_px=int(0.08 * DPI),
        draw_subtitle=False,
        draw_footer=True,
    )

    border_margin = int(0.25 * DPI)
    header_h = int(1.00 * DPI)
    accent_margin = int(0.08 * DPI)
    stripe_y1 = border_margin + accent_margin + header_h

    # Fixed outer grid box size across all levels and centered vertically on the page.
    grid_margin = int(60 * s)
    grid_w = w - 2 * grid_margin
    avail_y0 = stripe_y1 + int(0.35 * DPI)
    avail_y1 = h - int(80 * s)
    avail_h = max(1, avail_y1 - avail_y0)
    grid_size_px = min(grid_w, avail_h)
    grid_x = (w - grid_size_px) // 2
    grid_y = avail_y0 + (avail_h - grid_size_px) // 2

    cell_w = grid_size_px // cols
    cell_h = grid_size_px // rows

    shuffled = list(items)
    random.shuffle(shuffled)

    # If this card includes labels, compute a single font size that fits ALL labels,
    # so the text is consistent across the grid (especially for Level 4).
    fitted_label_font: ImageFont.ImageFont | None = None
    if words and images:
        label_h = max(int(0.18 * cell_h), int(0.22 * DPI))
        label_pad_x = max(6, int(0.05 * cell_w))
        label_pad_y = max(4, int(0.18 * label_h))

        # Gather names that will be used on this card (exclude FREE center).
        max_needed = rows * cols - (1 if free_center and rows % 2 == 1 and cols % 2 == 1 else 0)
        names = [shuffled[i % len(shuffled)]['name'] for i in range(max_needed)]
        longest = max(names, key=lambda t: len(t)) if names else ''

        fitted_label_font = _fit_font(
            draw,
            longest,
            font_path=_FONT_COMIC_BOLD,
            max_px=int(20 * s),
            min_px=int(9 * s),
            max_w=cell_w - 2 * label_pad_x,
            max_h=label_h - 2 * label_pad_y,
        )

    idx = 0
    for row in range(rows):
        for col in range(cols):
            cx = grid_x + col * cell_w
            cy = grid_y + row * cell_h

            is_free = (
                free_center
                and rows % 2 == 1
                and cols % 2 == 1
                and row == (rows // 2)
                and col == (cols // 2)
            )

            if is_free:
                draw.rectangle([cx, cy, cx + cell_w, cy + cell_h], fill=hex_to_rgb(LIGHT_BLUE))
                ftw = draw.textbbox((0, 0), "FREE", font=fonts['free'])[2]
                fth = draw.textbbox((0, 0), "FREE", font=fonts['free'])[3]
                draw.text((cx + (cell_w - ftw) // 2, cy + (cell_h - fth) // 2), "FREE", fill=hex_to_rgb(NAVY_BLUE), font=fonts['free'])
                continue

            # Always fill all boxes (never leave blanks) even if item list is small.
            item = shuffled[idx % len(shuffled)]
            name = item['name']

            # Real photos: selectively boost a few smaller subjects.
            boost_names = {"frog", "bird", "horse", "sheep", "eye", "goldfish"}
            needs_boost = False
            if images:
                lname = str(name).lower()
                is_real = False
                try:
                    is_real = "real_images" in str(item.get('path', '')).lower()
                except Exception:
                    is_real = False
                if is_real and any(b in lname for b in boost_names):
                    needs_boost = True

            if images:
                # Baseline sizing (pre image-size experiments):
                # - no trimming
                # - no cover-fit
                # - simple contain scaling inside the cell
                a = item['img'].copy()
                pad = max(2, int(0.02 * min(cell_w, cell_h)))

                is_real = False
                try:
                    is_real = "real_images" in str(item.get('path', '')).lower()
                except Exception:
                    is_real = False

                if words:
                    label_band_h = max(int(0.20 * cell_h), int(0.24 * DPI))
                    avail_w = max(1, cell_w - 2 * pad)
                    avail_h = max(1, cell_h - label_band_h - 2 * pad)
                    scale = 1.0
                    if level == 4:
                        scale = min(1.0, scale * 2.0)
                    if needs_boost:
                        scale = min(1.0, scale * 2.0)
                    a.thumbnail((max(1, int(avail_w * scale)), max(1, int(avail_h * scale))), Image.Resampling.LANCZOS)
                    ax = cx + (cell_w - a.width) // 2
                    ay = cy + pad + (avail_h - a.height) // 2
                else:
                    avail_w = max(1, cell_w - 2 * pad)
                    avail_h = max(1, cell_h - 2 * pad)
                    scale = 0.82 if level == 1 else 0.78
                    if level in (2, 3, 4):
                        # Icon-based levels: make icons much larger by reducing padding and
                        # allowing them to fill the available area.
                        pad = max(1, pad // 6)
                        avail_w = max(1, cell_w - 2 * pad)
                        avail_h = max(1, cell_h - 2 * pad)
                        scale = 1.0
                    if is_real:
                        # Real photos: trim then contain-fit at 75% of cell.
                        # This balances well: large subjects (dog, cat) don't
                        # overwhelm cells, small subjects (bird, fish) still
                        # get a good size boost.
                        a = _trim_for_max_size(a)
                        target_w = max(1, int(avail_w * 0.75))
                        target_h = max(1, int(avail_h * 0.75))
                        a.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                    else:
                        if needs_boost:
                            scale = min(1.0, scale * 2.0)
                        # Boardmaker icons often include extra whitespace; trim so the drawn
                        # subject can scale up to match the new sizing.
                        a = _trim_for_max_size(a)
                        a.thumbnail((max(1, int(avail_w * scale)), max(1, int(avail_h * scale))), Image.Resampling.LANCZOS)
                    ax = cx + (cell_w - a.width) // 2
                    ay = cy + (cell_h - a.height) // 2

                page.paste(a, (ax, ay), a if a.mode == 'RGBA' else None)

            if words:
                if images:
                    # Slightly smaller label band + more padding so text doesn't touch borders.
                    label_h = max(int(0.18 * cell_h), int(0.22 * DPI))
                    label_y0 = cy + cell_h - label_h
                    label_pad_x = max(6, int(0.05 * cell_w))
                    label_pad_y = max(6, int(0.22 * label_h)) if level == 4 else max(4, int(0.18 * label_h))
                    fitted = fitted_label_font or _fit_font(
                        draw,
                        name,
                        font_path=_FONT_COMIC_BOLD,
                        max_px=int(18 * s) if level == 4 else int(20 * s),
                        min_px=int(9 * s),
                        max_w=cell_w - 2 * label_pad_x,
                        max_h=max(1, label_h - 2 * label_pad_y),
                    )
                    tw, th = _text_size(draw, name, fitted)
                    tx = cx + (cell_w - tw) // 2
                    inner_h = max(1, label_h - 2 * label_pad_y)
                    ty = label_y0 + label_pad_y + max(0, (inner_h - th) // 2)
                    draw.text((tx, ty), name, fill=hex_to_rgb(NAVY_BLUE), font=fitted)
                else:
                    pad_x = max(4, int(0.06 * cell_w))
                    pad_y = max(4, int(0.10 * cell_h))
                    font_max = int(42 * s)
                    font_min = int(12 * s)
                    fitted = _fit_font(
                        draw,
                        name,
                        font_path=_FONT_COMIC_BOLD,
                        max_px=font_max,
                        min_px=font_min,
                        max_w=cell_w - 2 * pad_x,
                        max_h=cell_h - 2 * pad_y,
                    )
                    tw, th = _text_size(draw, name, fitted)
                    draw.text(
                        (cx + (cell_w - tw) // 2, cy + (cell_h - th) // 2),
                        name,
                        fill=hex_to_rgb(NAVY_BLUE),
                        font=fitted,
                    )

            idx += 1

    # Draw grid lines once (prevents double-thick borders at shared edges)
    grid_outline_w = int(3 * s)
    grid_line_w = int(2 * s)
    draw.rectangle(
        [grid_x, grid_y, grid_x + grid_size_px, grid_y + grid_size_px],
        outline=hex_to_rgb(NAVY_BLUE),
        width=grid_outline_w,
    )
    for c_idx in range(1, cols):
        x = grid_x + c_idx * cell_w
        draw.line([x, grid_y, x, grid_y + grid_size_px], fill=hex_to_rgb(NAVY_BLUE), width=grid_line_w)
    for r_idx in range(1, rows):
        y = grid_y + r_idx * cell_h
        draw.line([grid_x, y, grid_x + grid_size_px, y], fill=hex_to_rgb(NAVY_BLUE), width=grid_line_w)

    return page


def _draw_bingo_storage_labels_page(
    *,
    level: int,
    mode: str,
    theme_name: str,
    pack_code: str,
) -> Image.Image:
    w = int(PAGE_WIDTH * DPI / 72)
    h = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(page)
    s = DPI / 72
    fonts = _load_fonts()

    bear = _load_bear_icon(theme_id='brown_bear', mode=mode)
    accent_color_hex = "#808080" if mode == "bw" else LEVEL_COLORS.get(level, TITLE_BLUE)

    apply_small_wins_frame(
        page,
        product_title=f"{theme_name} Bingo",
        subtitle="Storage Labels",
        pack_code=pack_code,
        page_num=1,
        total_pages=1,
        level=level,
        accent_color_hex=accent_color_hex,
        footer_title=f"{theme_name} Bingo | Storage Labels",
        header_left_icon=bear,
        header_left_icon_flip=False,
        footer_y_offset_px=int(0.08 * DPI),
        draw_subtitle=True,
        draw_footer=True,
    )

    # Grid area inside the frame.
    border_margin = int(0.25 * DPI)
    header_h = int(1.00 * DPI)
    accent_margin = int(0.08 * DPI)
    stripe_y1 = border_margin + accent_margin + header_h

    top = stripe_y1 + int(0.55 * DPI)
    bottom = h - border_margin - int(0.70 * DPI)
    left = border_margin + int(0.20 * DPI)
    right = w - border_margin - int(0.20 * DPI)

    cols = 3
    rows = 4
    gap_x = int(0.20 * DPI)
    gap_y = int(0.15 * DPI)
    box_w = int((right - left - gap_x * (cols - 1)) / cols)
    box_h = int((bottom - top - gap_y * (rows - 1)) / rows)

    strip_w = max(10, int(0.14 * DPI))
    r_border = int(8 * s)
    outline = hex_to_rgb(PURPLE)
    strip_rgb = hex_to_rgb(accent_color_hex)

    level_label = LEVEL_SPECS[level].label.replace('_', ' ')
    for i in range(cols * rows):
        row = i // cols
        col = i % cols
        x0 = left + col * (box_w + gap_x)
        y0 = top + row * (box_h + gap_y)
        x1 = x0 + box_w
        y1 = y0 + box_h

        # Outer rounded box
        draw.rounded_rectangle([x0, y0, x1, y1], radius=r_border, fill='white', outline=outline, width=max(1, int(2 * s)))
        # Left color strip
        draw.rectangle([x0, y0, x0 + strip_w, y1], fill=strip_rgb)

        tx = x0 + strip_w + int(10 * s)
        ty = y0 + int(10 * s)

        draw.text((tx, ty), "Bingo", fill=hex_to_rgb(NAVY_BLUE), font=fonts['calling_label'])
        ty += _text_size(draw, "Ag", fonts['calling_label'])[1] + int(2 * s)
        draw.text((tx, ty), f"{theme_name} | {pack_code}", fill=hex_to_rgb(STEEL_BLUE), font=fonts['label'])
        ty += _text_size(draw, "Ag", fonts['label'])[1] + int(2 * s)
        draw.text((tx, ty), f"Level {level}: {level_label}", fill=hex_to_rgb(NAVY_BLUE), font=fonts['label'])

        if bear is not None:
            icon = bear.copy()
            icon_w = int(0.55 * DPI)
            icon_h = int(0.55 * DPI)
            icon.thumbnail((icon_w, icon_h), Image.Resampling.LANCZOS)
            ix = x1 - icon.width - int(10 * s)
            iy = y0 + (box_h - icon.height) // 2
            page.paste(icon, (ix, iy), icon if icon.mode == 'RGBA' else None)

    return page


def generate_bingo_storage_labels_pdf(
    output_path: Path,
    *,
    mode: str,
    theme_name: str = 'Brown Bear',
    pack_code: str = 'BB-BINGO',
) -> Path:
    pages: list[Image.Image] = []
    for lvl in range(1, 6):
        pages.append(
            _draw_bingo_storage_labels_page(
                level=lvl,
                mode=mode,
                theme_name=theme_name,
                pack_code=pack_code,
            )
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=letter)
    for p in pages:
        buf = io.BytesIO()
        p.save(buf, format='PNG', dpi=(DPI, DPI))
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    c.save()

    print(f"OK Generated: {output_path}")
    return output_path


def _draw_bingo_cover(
    *,
    level: int,
    mode: str,
    theme_name: str,
    pack_code: str,
    page_num: int,
    total_pages: int,
    accent_color_hex: str,
    sample_items: list[dict],
    activity_pages: int,
    calling_pages: int,
    calling_label: str,
):
    w = int(PAGE_WIDTH * DPI / 72)
    h = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(page)
    s = DPI / 72
    fonts = _load_fonts()

    bear = _load_bear_icon(theme_id='brown_bear', mode=mode)
    apply_small_wins_frame(
        page,
        product_title=f"{theme_name} Bingo",
        subtitle=f"Level {level}",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        accent_color_hex=accent_color_hex,
        footer_title=f"{theme_name} Bingo | Level {level}",
        header_left_icon=bear,
        header_left_icon_flip=False,
        footer_y_offset_px=int(0.08 * DPI),
        draw_subtitle=True,
        draw_footer=True,
    )

    scale = DPI / 72
    # Center artwork box with a single representative icon (Find & Cover style)
    art_box = int(3.05 * DPI)
    art_x = (w - art_box) // 2
    art_y = int(2.35 * DPI)
    draw.rounded_rectangle(
        [art_x, art_y, art_x + art_box, art_y + art_box],
        radius=int(0.20 * DPI),
        outline=hex_to_rgb(accent_color_hex),
        width=max(1, int(4 * scale)),
        fill="white",
    )

    # Render a mini Bingo grid preview (more representative than a single icon).
    # Uses up to 9 sample icons.
    grid_icons = [it.get("img") for it in sample_items if it.get("img") is not None][:9]
    if grid_icons:
        cols = 3
        rows = (len(grid_icons) + cols - 1) // cols
        rows = max(1, min(3, rows))

        inner = int(art_box * 0.06)
        cell_gap = max(1, int(art_box * 0.03))
        cell = (art_box - 2 * inner - cell_gap * (cols - 1)) // cols
        grid_h = rows * cell + cell_gap * (rows - 1)
        start_x = art_x + inner
        start_y = art_y + (art_box - grid_h) // 2

        for idx, ic in enumerate(grid_icons[: cols * rows]):
            r = idx // cols
            cidx = idx % cols
            cx = start_x + cidx * (cell + cell_gap)
            cy = start_y + r * (cell + cell_gap)
            im = ic.copy()
            if mode == "bw":
                im = im.convert("L").convert("RGBA")
            im = _trim_for_max_size(im)
            im.thumbnail((cell, cell), Image.Resampling.LANCZOS)
            ix = cx + (cell - im.width) // 2
            iy = cy + (cell - im.height) // 2
            page.paste(im, (ix, iy), im)

    # --- Layout below artwork box ---
    # Align text blocks to the artwork box left edge for visual consistency.
    left = art_x
    right_limit = art_x + art_box  # right edge of artwork box
    text_width = right_limit - left

    heading_font = ImageFont.truetype(_FONT_COMIC_BOLD, int(14 * (DPI / 72)))
    bullet_font = ImageFont.truetype(_FONT_COMIC, int(11 * (DPI / 72)))

    # 1) Tagline — centered, sits just below the artwork box
    y = art_y + art_box + int(0.18 * DPI)
    desc = "Print, play, and practice\u2014differentiated levels for SPED learners"
    fitted_desc = _fit_font(
        draw,
        desc,
        font_path=_FONT_COMIC,
        max_px=int(32 * (DPI / 72)),
        min_px=int(16 * (DPI / 72)),
        max_w=text_width,
        max_h=int(0.45 * DPI),
    )
    dw, dh = _text_size(draw, desc, fitted_desc)
    draw.text((left + (text_width - dw) // 2, y), desc, fill=hex_to_rgb(NAVY_BLUE), font=fitted_desc)
    y += dh + int(0.18 * DPI)

    # 2) "What's Included" heading
    heading = "What\u2019s Included"
    hw, hh = _text_size(draw, heading, heading_font)
    draw.text((left, y), heading, fill=hex_to_rgb(accent_color_hex), font=heading_font)
    y += hh + int(0.06 * DPI)

    # 3) Bullet list
    cards_text = f"{activity_pages} activity pages" if activity_pages != 1 else "1 activity page"
    calling_text = f"Print-ready {calling_label.lower()}" if calling_pages == 1 else f"Print-ready {calling_label.lower()} ({calling_pages} pages)"
    bullets = [
        cards_text,
        calling_text,
        "Color + black & white",
        "Optional laminate for reuse",
        "Use tokens or dabbers",
        "Easy level differentiation",
    ]
    bullet_indent = left + int(0.12 * DPI)
    for b in bullets:
        line = f"\u2022  {b}"
        draw.text((bullet_indent, y), line, fill=hex_to_rgb(NAVY_BLUE), font=bullet_font)
        y += int(0.19 * DPI)

    # 4) "Quick Start" heading — moderate gap
    y += int(0.10 * DPI)
    quick = "Quick Start"
    qw, qh = _text_size(draw, quick, heading_font)
    draw.text((left, y), quick, fill=hex_to_rgb(accent_color_hex), font=heading_font)
    y += qh + int(0.06 * DPI)

    # 5) Quick Start bullet points
    qs_bullets = [
        "Print cards and calling cards",
        "Use chips, dabbers, or tokens to play",
        f"Cut the {calling_label.lower()} for drawing",
    ]
    qs_indent = left + int(0.12 * DPI)
    for qb in qs_bullets:
        qline = f"\u2022  {qb}"
        draw.text((qs_indent, y), qline, fill=hex_to_rgb(NAVY_BLUE), font=bullet_font)
        y += int(0.19 * DPI)

    return page


def _calling_cards_per_page(*, style: str | None) -> int:
    s = DPI / 72
    border_margin = int(0.25 * DPI)
    header_h = int(1.00 * DPI)
    accent_margin = int(0.08 * DPI)
    stripe_y1 = border_margin + accent_margin + header_h
    base_y0 = stripe_y1 + int(0.35 * DPI)
    footer_room = int(0.55 * DPI)
    base_y1 = int(PAGE_HEIGHT * DPI / 72) - border_margin - footer_room
    avail_h = max(1, base_y1 - base_y0)

    avail_x0 = int(0.55 * DPI)
    avail_x1 = int(PAGE_WIDTH * DPI / 72) - int(0.55 * DPI)
    avail_w = max(1, avail_x1 - avail_x0)

    if style == 'large_text_small_icon':
        card_w = int(235 * s)
        card_h = int(125 * s)
        gap = int(18 * s)
    else:
        card_w = int(110 * s)
        card_h = int(130 * s)
        gap = int(15 * s)

    cols = max(1, int((avail_w + gap) / (card_w + gap)))
    rows = max(1, int((avail_h + gap) / (card_h + gap)))
    return max(1, cols * rows)


def _draw_calling_cards(
    *,
    items: list[dict],
    theme_name: str,
    pack_code: str,
    page_num: int,
    total_pages: int,
    images: bool,
    level: int | None = None,
    style: str | None = None,
    show_labels: bool = True,
    start_index: int = 0,
    page_index: int = 1,
    page_count: int = 1,
):
    w = int(PAGE_WIDTH * DPI / 72)
    h = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(page)
    s = DPI / 72
    fonts = _load_fonts()

    bear = _load_bear_icon(theme_id='brown_bear', mode='color')
    accent = LEVEL_COLORS.get(level, LEVEL_COLORS[2]) if level is not None else LEVEL_COLORS[2]
    sub = "Cut Outs" if level == 5 else "Calling Cards"
    sub_footer = f"{sub} ({page_index}/{page_count})" if page_count > 1 else sub
    apply_small_wins_frame(
        page,
        product_title=f"{theme_name} Bingo",
        subtitle=sub,
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=level,
        accent_color_hex=accent,
        footer_title=f"{theme_name} Bingo | {sub_footer}",
        header_left_icon=bear,
        header_left_icon_flip=False,
        footer_y_offset_px=int(0.08 * DPI),
        draw_subtitle=True,
        draw_footer=True,
    )

    border_margin = int(0.25 * DPI)
    header_h = int(1.00 * DPI)
    accent_margin = int(0.08 * DPI)
    stripe_y1 = border_margin + accent_margin + header_h

    base_y0 = stripe_y1 + int(0.35 * DPI)
    footer_room = int(0.55 * DPI)
    base_y1 = h - border_margin - footer_room

    avail_x0 = int(0.55 * DPI)
    avail_x1 = w - int(0.55 * DPI)
    avail_w = max(1, avail_x1 - avail_x0)
    avail_h = max(1, base_y1 - base_y0)

    # Use consistent card sizing (prevents weird "4 huge cards" pages).
    if style == 'large_text_small_icon':
        card_w = int(235 * s)
        card_h = int(125 * s)
        gap = int(18 * s)
    else:
        card_w = int(110 * s)
        card_h = int(130 * s)
        gap = int(15 * s)

    cols = max(1, int((avail_w + gap) / (card_w + gap)))
    rows = max(1, int((avail_h + gap) / (card_h + gap)))
    per_page = max(1, cols * rows)

    page_items = items[start_index : start_index + per_page]
    rows_count = max(1, (len(page_items) + cols - 1) // cols)

    grid_w = cols * card_w + gap * (cols - 1)
    grid_h = rows_count * card_h + gap * (rows_count - 1)
    start_x = avail_x0 + max(0, (avail_w - grid_w) // 2)
    start_y = base_y0 + max(0, (avail_h - grid_h) // 2)

    for idx, item in enumerate(page_items):
        row = idx // cols
        col = idx % cols
        cx = start_x + col * (card_w + gap)
        cy = start_y + row * (card_h + gap)

        draw.rounded_rectangle(
            [cx, cy, cx + card_w, cy + card_h],
            radius=int(8 * s),
            fill='white',
            outline=hex_to_rgb(PURPLE),
            width=max(1, int(2 * s)),
        )

        name = item['name']
        if images:
            a = item['img'].copy()
            if style == 'large_text_small_icon':
                asize = int(48 * s)
                a.thumbnail((asize, asize), Image.Resampling.LANCZOS)
                ax = cx + int(14 * s)
                ay = cy + (card_h - a.height) // 2
                page.paste(a, (ax, ay), a if a.mode == 'RGBA' else None)

                text_x0 = ax + a.width + int(14 * s)
                text_w = max(1, card_w - (text_x0 - cx) - int(12 * s))
                text_h = max(1, card_h - int(16 * s))
                lines = _wrap_text(draw, name, fonts['calling_big'], text_w, max_lines=2)
                line_h = _text_size(draw, "Ag", fonts['calling_big'])[1]
                block_h = line_h * len(lines) + int(2 * s) * (len(lines) - 1)
                ty = cy + max(0, (card_h - block_h) // 2)
                for li in lines:
                    tw, _ = _text_size(draw, li, fonts['calling_big'])
                    tx = text_x0 + max(0, (text_w - tw) // 2)
                    draw.text((tx, ty), li, fill=hex_to_rgb(NAVY_BLUE), font=fonts['calling_big'])
                    ty += line_h + int(2 * s)
            else:
                pad = max(1, int(0.10 * min(card_w, card_h)))
                if level in (1, 2, 3):
                    n = str(item.get('name', '')).strip().lower()
                    if level != 1 or n not in {"cat", "dog"}:
                        pad = max(1, pad // 5)
                label_h = int(0.22 * card_h) if show_labels else 0
                target_w = max(1, card_w - 2 * pad)
                target_h = max(1, card_h - label_h - 2 * pad)
                is_real = False
                try:
                    is_real = "real_images" in str(item.get('path', '')).lower()
                except Exception:
                    is_real = False

                if is_real:
                    a = _trim_for_max_size(a)
                    real_w = max(1, int(target_w * 0.50))
                    real_h = max(1, int(target_h * 0.50))
                    inner_pad = max(2, int(0.03 * min(card_w, card_h)))
                    a.thumbnail((max(1, real_w - 2 * inner_pad), max(1, real_h - 2 * inner_pad)), Image.Resampling.LANCZOS)
                else:
                    a.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                ax = cx + (card_w - a.width) // 2
                ay = cy + pad + max(0, ((card_h - label_h - 2 * pad) - a.height) // 2)
                page.paste(a, (ax, ay), a if a.mode == 'RGBA' else None)

                if show_labels and label_h > 0:
                    label_y0 = cy + card_h - label_h
                    max_w = card_w - 2 * int(14 * s)
                    lines = _wrap_text(draw, name, fonts['calling_label'], max_w, max_lines=2)
                    line_h = _text_size(draw, "Ag", fonts['calling_label'])[1]
                    block_h = line_h * len(lines) + int(1 * s) * (len(lines) - 1)
                    ty = label_y0 + max(0, (label_h - block_h) // 2)
                    for li in lines:
                        tw, _ = _text_size(draw, li, fonts['calling_label'])
                        tx = cx + (card_w - tw) // 2
                        draw.text((tx, ty), li, fill=hex_to_rgb(NAVY_BLUE), font=fonts['calling_label'])
                        ty += line_h + int(1 * s)
        else:
            max_w = card_w - 2 * int(14 * s)
            lines = _wrap_text(draw, name, fonts['calling_big'], max_w, max_lines=2)
            line_h = _text_size(draw, "Ag", fonts['calling_big'])[1]
            block_h = line_h * len(lines) + int(2 * s) * (len(lines) - 1)
            ty = cy + max(0, (card_h - block_h) // 2)
            for li in lines:
                tw, _ = _text_size(draw, li, fonts['calling_big'])
                tx = cx + (card_w - tw) // 2
                draw.text((tx, ty), li, fill=hex_to_rgb(NAVY_BLUE), font=fonts['calling_big'])
                ty += line_h + int(2 * s)

    return page


def generate_bingo_level_pdf(output_path: Path, *, level: int, mode: str, theme_id: str = 'brown_bear', theme_name: str = 'Brown Bear', pack_code: str = 'BB-BINGO') -> Path:
    spec = LEVEL_SPECS[level]

    if spec.images == 'icons':
        board_items = _load_items(theme_id, 'icons', mode=mode)
    elif spec.images == 'real':
        board_items = _load_items(theme_id, 'real', mode=mode)
    else:
        # Text-only uses icon vocabulary list for names
        board_items = _load_items(theme_id, 'icons', mode=mode)

    calling_kind = spec.calling_images or spec.images
    if calling_kind == 'icons':
        calling_items = _load_items(theme_id, 'icons', mode=mode)
    elif calling_kind == 'real':
        calling_items = _load_items(theme_id, 'real', mode=mode)
    else:
        calling_items = board_items

    if not board_items:
        raise FileNotFoundError(f"No items found for kind={spec.images}")
    if not calling_items:
        raise FileNotFoundError(f"No items found for calling kind={calling_kind}")

    calling_per_page = _calling_cards_per_page(style=spec.calling_style)
    calling_pages = (len(calling_items) + calling_per_page - 1) // calling_per_page
    total_pages = 1 + 8 + max(1, calling_pages)
    pages: list[Image.Image] = []
    page_num = 1

    label = spec.label.replace('_', ' ')
    accent_color_hex = "#808080" if mode == "bw" else LEVEL_COLORS.get(level, TITLE_BLUE)

    cover_samples = _load_items(theme_id, 'icons', mode=mode)
    if not cover_samples:
        cover_samples = calling_items if calling_items else board_items

    calling_label = "Cut Outs" if level == 5 else "Calling Cards"
    pages.append(
        _draw_bingo_cover(
            level=level,
            mode=mode,
            theme_name=theme_name,
            pack_code=pack_code,
            page_num=page_num,
            total_pages=total_pages,
            accent_color_hex=accent_color_hex,
            sample_items=cover_samples,
            activity_pages=8,
            calling_pages=max(1, calling_pages),
            calling_label=calling_label,
        )
    )
    page_num += 1

    for card in range(1, 9):
        random.seed((level * 1000) + (card * 17) + (1 if mode == 'bw' else 0))
        pages.append(
            _draw_bingo_card(
                items=board_items,
                rows=spec.rows,
                cols=spec.cols,
                level=level,
                level_label=label,
                card_num=card,
                mode=mode,
                theme_name=theme_name,
                pack_code=pack_code,
                page_num=page_num,
                total_pages=total_pages,
                words=spec.words,
                images=(spec.images != 'none'),
                free_center=spec.free_center,
                accent_color_hex=accent_color_hex,
                image_fit='contain',
            )
        )
        page_num += 1

    for i in range(max(1, calling_pages)):
        pages.append(
            _draw_calling_cards(
                items=calling_items,
                theme_name=theme_name,
                pack_code=pack_code,
                page_num=page_num,
                total_pages=total_pages,
                images=(calling_kind != 'none'),
                level=level,
                style=spec.calling_style,
                show_labels=True,
                start_index=i * calling_per_page,
                page_index=i + 1,
                page_count=max(1, calling_pages),
            )
        )
        page_num += 1

    # Real-photo levels benefit from JPEG page encoding (much smaller files).
    use_jpeg = spec.images in ('real', 'icons_with_labels') or calling_kind == 'real'

    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=letter)
    for p in pages:
        buf = io.BytesIO()
        if use_jpeg:
            rgb_page = p.convert('RGB') if p.mode != 'RGB' else p
            rgb_page.save(buf, format='JPEG', quality=85, optimize=True, dpi=(DPI, DPI))
        else:
            p.save(buf, format='PNG', dpi=(DPI, DPI))
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    c.save()

    print(f"OK Generated: {output_path}")
    return output_path


def main() -> int:
    root = Path(__file__).parent
    samples_dir = root / 'samples' / 'brown_bear' / 'bingo'
    review_dir = root / 'review_pdfs'
    samples_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)

    for level in range(1, 6):
        for mode in ['color', 'bw']:
            out = samples_dir / f"brown_bear_bingo_level{level}_{mode}.pdf"
            generate_bingo_level_pdf(out, level=level, mode=mode)
            shutil.copy2(out, review_dir / out.name)

    for mode in ['color', 'bw']:
        out = samples_dir / f"brown_bear_bingo_storage_labels_{mode}.pdf"
        generate_bingo_storage_labels_pdf(out, mode=mode)
        shutil.copy2(out, review_dir / out.name)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
