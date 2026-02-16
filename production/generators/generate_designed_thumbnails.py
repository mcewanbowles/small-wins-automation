#!/usr/bin/env python3
"""Generate TpT-optimized marketing thumbnails (no Canva/PowerPoint).

Outputs square PNG thumbnails designed for readability at small sizes.

- Per-level thumbnails use the level accent color and the cutout page from that level.
- Bundle thumbnail uses an overlapping collage of level cover pages.

Requires:
- Pillow
- pdf2image (and Poppler installed/available)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

# Optional deps (mirror style of existing generate_thumbnails.py)
try:
    from pdf2image import convert_from_path

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


REPO_ROOT = Path(__file__).resolve().parents[2]
THEME_ID = "brown_bear"
PRODUCT_ID = "matching"

FINAL_DIR = REPO_ROOT / "production" / "final_products" / THEME_ID / PRODUCT_ID
MARKETING_DIR = REPO_ROOT / "production" / "marketing" / THEME_ID / PRODUCT_ID / "thumbnails"

LEVELS = {
    1: {"name": "Errorless", "color": "#F4A259"},
    2: {"name": "Easy", "color": "#4A90E2"},
    3: {"name": "Medium", "color": "#7BC47F"},
    4: {"name": "Challenge", "color": "#9B59B6"},
    5: {"name": "Advanced", "color": "#E74C3C"},
}


@dataclass(frozen=True)
class Sizes:
    master: int = 1600
    tpt_min: int = 750
    s500: int = 500
    s280: int = 280


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow not available")

    # Try common Windows fonts first.
    candidates = [
        ("arialbd.ttf" if bold else "arial.ttf"),
        ("Calibri Bold.ttf" if bold else "Calibri.ttf"),
        ("segoeuib.ttf" if bold else "segoeui.ttf"),
    ]

    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue

    # Fallback
    return ImageFont.load_default()


def _render_pdf_page(pdf_path: Path, page_num_1_indexed: int, dpi: int = 220) -> Image.Image:
    if PYMUPDF_AVAILABLE:
        doc = fitz.open(str(pdf_path))
        page_index = page_num_1_indexed - 1
        if page_index < 0 or page_index >= doc.page_count:
            raise RuntimeError(f"Page {page_num_1_indexed} out of range for {pdf_path.name}")

        page = doc.load_page(page_index)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        doc.close()
        return img

    if not PDF2IMAGE_AVAILABLE:
        raise RuntimeError(
            "No PDF renderer available. Install one of: pip install pymupdf OR install pdf2image + Poppler."
        )

    images = convert_from_path(
        str(pdf_path),
        first_page=page_num_1_indexed,
        last_page=page_num_1_indexed,
        dpi=dpi,
    )
    if not images:
        raise RuntimeError(f"No pages rendered from {pdf_path}")
    return images[0].convert("RGB")


def _fit_into(img: Image.Image, box_w: int, box_h: int) -> Image.Image:
    """Resize to fit within box maintaining aspect ratio."""
    w, h = img.size
    scale = min(box_w / w, box_h / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


def _rounded_rect_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def _draw_chip(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], text: str, font: ImageFont.ImageFont):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=(255, 255, 255, 220))
    tw = draw.textlength(text, font=font)
    tx = x1 + (x2 - x1 - tw) / 2
    ty = y1 + (y2 - y1 - font.size) / 2 - 1
    draw.text((tx, ty), text, fill=(25, 35, 55), font=font)


def _safe_filename(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in s).strip("_")


def _level_final_pdf(level: int, mode: str) -> Path:
    level_name = LEVELS[level]["name"]
    return FINAL_DIR / f"brown_bear_matching_level{level}_{level_name}_{mode}_FINAL.pdf"


def _level_cover_pdf(level: int) -> Path:
    return FINAL_DIR / f"cover_level{level}_color_FINAL.pdf"


def _generate_level_thumbnail(level: int, sizes: Sizes) -> dict[int, Path]:
    level_name = LEVELS[level]["name"]
    accent_rgb = _hex_to_rgb(LEVELS[level]["color"])

    # Cutout page in FINAL: cover=1, then 12 activities (pages 2-13), then cutouts (14-15), storage (16)
    # Use cutout page 1 (page 14).
    src_pdf = _level_final_pdf(level, "color")
    cutout_img = _render_pdf_page(src_pdf, page_num_1_indexed=14, dpi=220)

    W = H = sizes.master
    base = Image.new("RGB", (W, H), accent_rgb)

    # Subtle vignette for depth
    vignette = Image.new("L", (W, H), 0)
    vdraw = ImageDraw.Draw(vignette)
    vdraw.ellipse((-W * 0.15, -H * 0.10, W * 1.15, H * 1.10), fill=160)
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=60))
    base = Image.composite(base, Image.new("RGB", (W, H), (18, 22, 35)), vignette)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Header
    header_h = int(H * 0.22)
    draw.rounded_rectangle((70, 60, W - 70, 60 + header_h), radius=42, fill=(255, 255, 255, 240))

    font_title = _load_font(72, bold=True)
    font_sub = _load_font(46, bold=False)
    font_badge = _load_font(44, bold=True)
    font_chip = _load_font(34, bold=False)

    title = "BROWN BEAR"
    product = "MATCHING"

    tx = 110
    ty = 90
    draw.text((tx, ty), title, fill=(25, 35, 55), font=font_title)
    draw.text((tx, ty + 82), product, fill=(25, 35, 55), font=font_sub)

    # Level badge
    badge_text = f"LEVEL {level}  •  {level_name.upper()}"
    badge_w = int(draw.textlength(badge_text, font=font_badge)) + 80
    badge_h = 90
    bx1 = W - 90 - badge_w
    by1 = 80
    draw.rounded_rectangle((bx1, by1, bx1 + badge_w, by1 + badge_h), radius=38, fill=accent_rgb + (255,))
    btx = bx1 + 40
    bty = by1 + 18
    draw.text((btx, bty), badge_text, fill=(255, 255, 255), font=font_badge)

    # Preview panel
    panel_x1 = 70
    panel_y1 = 60 + header_h + 35
    panel_x2 = W - 70
    panel_y2 = H - 210
    panel_w = panel_x2 - panel_x1
    panel_h = panel_y2 - panel_y1

    # Shadow
    shadow = Image.new("RGBA", (panel_w, panel_h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle((0, 0, panel_w, panel_h), radius=46, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=18))
    overlay.alpha_composite(shadow, (panel_x1 + 10, panel_y1 + 16))

    # White panel
    draw.rounded_rectangle((panel_x1, panel_y1, panel_x2, panel_y2), radius=46, fill=(255, 255, 255, 250))

    # Put cutout image inside panel
    inner_pad = 34
    target_w = panel_w - inner_pad * 2
    target_h = panel_h - inner_pad * 2
    fitted = _fit_into(cutout_img, target_w, target_h)

    # Add a slight border to the page image
    page_bg = Image.new("RGBA", (fitted.size[0] + 18, fitted.size[1] + 18), (245, 245, 245, 255))
    pdraw = ImageDraw.Draw(page_bg)
    pdraw.rounded_rectangle((0, 0, page_bg.size[0] - 1, page_bg.size[1] - 1), radius=18, outline=(210, 210, 210, 255), width=4)
    page_bg.alpha_composite(fitted.convert("RGBA"), (9, 9))

    px = panel_x1 + inner_pad + (target_w - page_bg.size[0]) // 2
    py = panel_y1 + inner_pad + (target_h - page_bg.size[1]) // 2
    overlay.alpha_composite(page_bg, (px, py))

    # Chips
    chips = ["Cutouts", "Color + B/W", "Low Prep"]
    chip_y = panel_y2 + 28
    chip_gap = 20
    chip_w = 300
    chip_h = 64
    start_x = 70

    for i, t in enumerate(chips):
        x1 = start_x + i * (chip_w + chip_gap)
        _draw_chip(draw, (x1, chip_y, x1 + chip_w, chip_y + chip_h), t, font_chip)

    # Footer brand (small)
    footer = "Small Wins Studio"
    fw = draw.textlength(footer, font=font_chip)
    draw.text((W - 70 - fw, chip_y + 6), footer, fill=(255, 255, 255, 220), font=font_chip)

    composed = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")

    MARKETING_DIR.mkdir(parents=True, exist_ok=True)

    out_paths: dict[int, Path] = {}
    stem = _safe_filename(f"{THEME_ID}_{PRODUCT_ID}_level{level}_{level_name}")

    master_path = MARKETING_DIR / f"{stem}_{sizes.master}x{sizes.master}.png"
    composed.save(master_path, format="PNG", optimize=True)
    out_paths[sizes.master] = master_path

    for side in (sizes.tpt_min, sizes.s500, sizes.s280):
        thumb = composed.resize((side, side), Image.Resampling.LANCZOS)
        out_path = MARKETING_DIR / f"{stem}_{side}x{side}.png"
        thumb.save(out_path, format="PNG", optimize=True)
        out_paths[side] = out_path

    return out_paths


def _generate_bundle_thumbnail(sizes: Sizes) -> dict[int, Path]:
    W = H = sizes.master
    navy = (18, 24, 40)
    teal = (42, 174, 174)

    base = Image.new("RGB", (W, H), navy)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Header
    header_h = int(H * 0.24)
    draw.rounded_rectangle((70, 60, W - 70, 60 + header_h), radius=42, fill=(255, 255, 255, 245))

    font_title = _load_font(68, bold=True)
    font_sub = _load_font(46, bold=False)
    font_badge = _load_font(52, bold=True)
    font_chip = _load_font(34, bold=False)

    draw.text((110, 90), "BROWN BEAR", fill=(25, 35, 55), font=font_title)
    draw.text((110, 90 + 82), "MATCHING", fill=(25, 35, 55), font=font_sub)

    # Mega bundle badge
    badge_text = "MATCHING MEGA BUNDLE"
    badge_w = int(draw.textlength(badge_text, font=font_badge)) + 90
    badge_h = 96
    bx1 = W - 90 - badge_w
    by1 = 82
    draw.rounded_rectangle((bx1, by1, bx1 + badge_w, by1 + badge_h), radius=40, fill=teal + (255,))
    draw.text((bx1 + 46, by1 + 18), badge_text, fill=(255, 255, 255), font=font_badge)

    # Collage panel
    panel_x1 = 70
    panel_y1 = 60 + header_h + 35
    panel_x2 = W - 70
    panel_y2 = H - 210
    panel_w = panel_x2 - panel_x1
    panel_h = panel_y2 - panel_y1

    # Shadow + panel
    shadow = Image.new("RGBA", (panel_w, panel_h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle((0, 0, panel_w, panel_h), radius=46, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=18))
    overlay.alpha_composite(shadow, (panel_x1 + 10, panel_y1 + 16))
    draw.rounded_rectangle((panel_x1, panel_y1, panel_x2, panel_y2), radius=46, fill=(255, 255, 255, 250))

    # Overlapping pages collage (use cover pages for each level)
    inner_pad = 46
    collage_box = (panel_x1 + inner_pad, panel_y1 + inner_pad, panel_x2 - inner_pad, panel_y2 - inner_pad)
    cb_w = collage_box[2] - collage_box[0]
    cb_h = collage_box[3] - collage_box[1]

    # Render covers
    pages: list[Image.Image] = []
    for lvl in range(1, 6):
        cover_pdf = _level_cover_pdf(lvl)
        try:
            img = _render_pdf_page(cover_pdf, 1, dpi=200)
        except Exception:
            # fallback to cutout page for this level
            img = _render_pdf_page(_level_final_pdf(lvl, "color"), 14, dpi=200)
        pages.append(img)

    # Place as a fanned stack
    stack_w = int(cb_w * 0.86)
    stack_h = int(cb_h * 0.92)
    cx = collage_box[0] + (cb_w - stack_w) // 2
    cy = collage_box[1] + (cb_h - stack_h) // 2

    angles = [-12, -6, 0, 6, 12]
    x_offsets = [-90, -45, 0, 45, 90]
    for img, ang, xo, lvl in zip(pages, angles, x_offsets, range(1, 6)):
        fitted = _fit_into(img, stack_w, stack_h)
        # page border
        page = Image.new("RGBA", (fitted.size[0] + 24, fitted.size[1] + 24), (250, 250, 250, 255))
        pdraw = ImageDraw.Draw(page)
        pdraw.rounded_rectangle((0, 0, page.size[0] - 1, page.size[1] - 1), radius=22, outline=(200, 200, 200, 255), width=4)
        page.alpha_composite(fitted.convert("RGBA"), (12, 12))

        rotated = page.rotate(ang, resample=Image.Resampling.BICUBIC, expand=True)
        px = cx + xo + (stack_w - rotated.size[0]) // 2
        py = cy + (stack_h - rotated.size[1]) // 2

        # subtle drop shadow per page
        sh = Image.new("RGBA", rotated.size, (0, 0, 0, 0))
        sh_draw = ImageDraw.Draw(sh)
        sh_draw.rectangle((0, 0, rotated.size[0], rotated.size[1]), fill=(0, 0, 0, 90))
        sh = sh.filter(ImageFilter.GaussianBlur(radius=14))
        overlay.alpha_composite(sh, (px + 10, py + 14))
        overlay.alpha_composite(rotated, (px, py))

        # level color tag
        tag_rgb = _hex_to_rgb(LEVELS[lvl]["color"])
        tag = Image.new("RGBA", (200, 56), (0, 0, 0, 0))
        tdraw = ImageDraw.Draw(tag)
        tdraw.rounded_rectangle((0, 0, 199, 55), radius=18, fill=tag_rgb + (255,))
        tfont = _load_font(30, bold=True)
        ttext = f"L{lvl}"
        tw = tdraw.textlength(ttext, font=tfont)
        tdraw.text(((200 - tw) / 2, 10), ttext, fill=(255, 255, 255), font=tfont)
        overlay.alpha_composite(tag, (px + 20, py + 20))

    # Chips
    chips = ["Levels 1-5", "Cutouts Included", "Color + B/W"]
    chip_y = panel_y2 + 28
    chip_gap = 20
    chip_w = 330
    chip_h = 64
    start_x = 70

    for i, t in enumerate(chips):
        x1 = start_x + i * (chip_w + chip_gap)
        _draw_chip(draw, (x1, chip_y, x1 + chip_w, chip_y + chip_h), t, font_chip)

    footer = "Small Wins Studio"
    fw = draw.textlength(footer, font=font_chip)
    draw.text((W - 70 - fw, chip_y + 6), footer, fill=(255, 255, 255, 220), font=font_chip)

    composed = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")

    MARKETING_DIR.mkdir(parents=True, exist_ok=True)

    out_paths: dict[int, Path] = {}
    stem = _safe_filename(f"{THEME_ID}_{PRODUCT_ID}_bundle_mega")

    master_path = MARKETING_DIR / f"{stem}_{sizes.master}x{sizes.master}.png"
    composed.save(master_path, format="PNG", optimize=True)
    out_paths[sizes.master] = master_path

    for side in (sizes.tpt_min, sizes.s500, sizes.s280):
        thumb = composed.resize((side, side), Image.Resampling.LANCZOS)
        out_path = MARKETING_DIR / f"{stem}_{side}x{side}.png"
        thumb.save(out_path, format="PNG", optimize=True)
        out_paths[side] = out_path

    return out_paths


def generate_all() -> None:
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow not available. Install with: pip install Pillow")
    if not (PYMUPDF_AVAILABLE or PDF2IMAGE_AVAILABLE):
        raise RuntimeError("Install pymupdf (recommended) OR pdf2image")

    sizes = Sizes()
    print(f"Output dir: {MARKETING_DIR}")

    # Levels
    for lvl in range(1, 6):
        print(f"Generating Level {lvl} thumbnail...")
        _generate_level_thumbnail(lvl, sizes)

    # Bundle
    print("Generating bundle thumbnail...")
    _generate_bundle_thumbnail(sizes)

    print("OK Designed thumbnails generated.")


if __name__ == "__main__":
    generate_all()
