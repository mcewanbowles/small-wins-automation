#!/usr/bin/env python3
"""Generate TPT-ready bundle listing thumbnails for the Llama Llama Red Pajama
14-product literacy/AAC suite.

Modeled on generate_designed_thumbnails.py:
- Pillow drawing, PyMuPDF (fitz) PDF rendering with pdf2image fallback
- Square 1600px master plus 750/500/280 resized outputs
- Rounded panels, navy/teal brand colors
- Grid collage of Teacher Overview first pages (fallback: product COLOR pdf,
  then a plain labeled tile)

Outputs to:
  assets/themes/llama_llama_red_pajama/marketing/bundle_thumbnails/
    llrp_bundle_thumbnail_{size}x{size}.png        (4x4 grid variant)
    llrp_bundle_thumbnail_alt_{size}x{size}.png    (5x3 grid variant)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

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
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


REPO_ROOT = Path(__file__).resolve().parents[2]
THEME_DIR = REPO_ROOT / "assets" / "themes" / "llama_llama_red_pajama"
TO_ROOT = (
    REPO_ROOT
    / "Studioforge"
    / "_REVIEW"
    / "Teacher Overview Template 04-09"
)
OUTPUT_DIR = THEME_DIR / "OUTPUT"
MARKETING_DIR = THEME_DIR / "marketing" / "bundle_thumbnails"

NAVY = (13, 37, 69)      # #0D2545
TEAL = (49, 168, 160)    # #31A8A0
GOLD = (225, 180, 45)    # #E1B42D
INK = (25, 35, 55)

# subfolder -> (teacher overview filename, short label, pack prefix for fallback)
PRODUCTS: list[tuple[str, str, str, str]] = [
    ("boardready_aac", "LLRP-AAC-REVIEW_Teacher_Overview.pdf", "AAC Board", "LLRP-AAC-REVIEW"),
    ("matching", "LLRP-MATCH-REVIEW_Teacher_Overview.pdf", "Matching", "LLRP-MATCH-REVIEW"),
    ("book_participation_pieces", "LLRP-BPP-LAUNCH_Teacher_Overview.pdf", "Book Pieces", "LLRP-BPP-LAUNCH"),
    ("sentence_building", "LLRP-SENT-LAUNCH_Teacher_Overview.pdf", "Sentence Build", "LLRP-SENT-LAUNCH"),
    ("sequencing", "LLRP-SEQ-LAUNCH_Teacher_Overview.pdf", "Sequencing", "LLRP-SEQ-LAUNCH"),
    ("yes_no_questions", "LLRP-YN-LAUNCH_Teacher_Overview.pdf", "Yes/No", "LLRP-YN-LAUNCH"),
    ("inferencing_cards", "LLRP-INF-LAUNCH_Teacher_Overview.pdf", "Inferencing", "LLRP-INF-LAUNCH"),
    ("vocabulary_snap", "LLRP-VWW-LAUNCH_Teacher_Overview.pdf", "Vocab Snap", "LLRP-VWW-LAUNCH"),
    ("syllable_awareness", "LLRP-SYL-LAUNCH_Teacher_Overview.pdf", "Syllables", "LLRP-SYL-LAUNCH"),
    ("decoding", "LLRP-DEC-LAUNCH_Teacher_Overview.pdf", "CVC Decode", "LLRP-DEC-LAUNCH"),
    ("story_grammar", "LLRP-SGM-LAUNCH_Teacher_Overview.pdf", "Story Grammar", "LLRP-SGM-LAUNCH"),
    ("word_search", "LLRP-WS-LAUNCH_Teacher_Overview.pdf", "Word Search", "LLRP-WS-LAUNCH"),
    ("bingo", "LLRP-BINGO-LAUNCH_Teacher_Overview.pdf", "Bingo", "LLRP-BINGO-LAUNCH"),
    ("sorting", "LLRP-SORT-LAUNCH_Teacher_Overview.pdf", "Sorting", "LLRP-SORT-LAUNCH"),
    ("print_detective", "LLRP-PD-LAUNCH_Teacher_Overview.pdf", "Print Detective", "LLRP-PD-LAUNCH"),
]


@dataclass(frozen=True)
class Sizes:
    master: int = 1600
    tpt_min: int = 750
    s500: int = 500
    s280: int = 280


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow not available")
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
    return ImageFont.load_default()


def _render_pdf_page(pdf_path: Path, page_num_1_indexed: int, dpi: int = 200) -> Image.Image:
    if PYMUPDF_AVAILABLE:
        doc = fitz.open(str(pdf_path))
        page_index = page_num_1_indexed - 1
        if page_index < 0 or page_index >= doc.page_count:
            doc.close()
            raise RuntimeError(f"Page {page_num_1_indexed} out of range for {pdf_path.name}")
        page = doc.load_page(page_index)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        doc.close()
        return img

    if not PDF2IMAGE_AVAILABLE:
        raise RuntimeError("No PDF renderer available (install pymupdf or pdf2image+poppler)")

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
    w, h = img.size
    scale = min(box_w / w, box_h / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


def _draw_chip(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], text: str,
               font: ImageFont.ImageFont) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=(255, 255, 255, 220))
    tw = draw.textlength(text, font=font)
    tx = x1 + (x2 - x1 - tw) / 2
    ty = y1 + (y2 - y1 - font.size) / 2 - 1
    draw.text((tx, ty), text, fill=INK, font=font)


def _find_color_pdf(pack_prefix: str) -> Path | None:
    """Find a COLOR pdf in OUTPUT dir by pack-code prefix, preferring plain COLOR."""
    if not OUTPUT_DIR.exists():
        return None
    matches = sorted(OUTPUT_DIR.glob(f"{pack_prefix}*_COLOR.pdf"))
    if not matches:
        matches = sorted(OUTPUT_DIR.glob(f"{pack_prefix}*COLOR*.pdf"))
    if not matches:
        # try looser prefix (first two segments, e.g. LLRP-MATCH)
        parts = pack_prefix.split("-")
        if len(parts) > 2:
            short = "-".join(parts[:2])
            matches = sorted(OUTPUT_DIR.glob(f"{short}*_COLOR.pdf"))
    return matches[0] if matches else None


def _product_tile_image(subfolder: str, to_name: str, label: str,
                        pack_prefix: str, tile_w: int, tile_h: int,
                        label_font: ImageFont.ImageFont,
                        fallbacks: list[str]) -> Image.Image:
    """Return a tile image (RGB) sized tile_w x tile_h."""
    to_pdf = TO_ROOT / subfolder / to_name
    img: Image.Image | None = None
    try:
        img = _render_pdf_page(to_pdf, 1, dpi=160)
    except Exception:
        color_pdf = _find_color_pdf(pack_prefix)
        if color_pdf is not None:
            try:
                img = _render_pdf_page(color_pdf, 1, dpi=160)
                fallbacks.append(f"{label}: COLOR fallback ({color_pdf.name})")
            except Exception:
                img = None
    if img is None:
        fallbacks.append(f"{label}: label-only tile (no PDF)")
        tile = Image.new("RGB", (tile_w, tile_h), (255, 255, 255))
        tdraw = ImageDraw.Draw(tile)
        tw = tdraw.textlength(label, font=label_font)
        tdraw.text(((tile_w - tw) / 2, (tile_h - label_font.size) / 2 - 4),
                   label, fill=INK, font=label_font)
        return tile

    fitted = _fit_into(img, tile_w, tile_h)
    tile = Image.new("RGB", (tile_w, tile_h), (255, 255, 255))
    tile.paste(fitted, ((tile_w - fitted.size[0]) // 2, (tile_h - fitted.size[1]) // 2))
    return tile


def _filler_tile(text: str, tile_w: int, tile_h: int,
                 font: ImageFont.ImageFont) -> Image.Image:
    tile = Image.new("RGB", (tile_w, tile_h), GOLD)
    tdraw = ImageDraw.Draw(tile)
    # Wrap to up to 2 lines and shrink until it fits inside the tile.
    words = text.split()
    size = font.size
    while size > 14:
        f = _load_font(size, bold=True)
        lines: list[str] = []
        line = ""
        for w in words:
            cand = f"{line} {w}".strip()
            if not line or tdraw.textlength(cand, font=f) <= tile_w - 40:
                line = cand
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)
        if len(lines) <= 2 and all(tdraw.textlength(l, font=f) <= tile_w - 40 for l in lines):
            break
        size -= 2
    f = _load_font(size, bold=True)
    line_h = int(size * 1.25)
    y = (tile_h - line_h * len(lines)) / 2
    for l in lines[:2]:
        tw = tdraw.textlength(l, font=f)
        tdraw.text(((tile_w - tw) / 2, y), l, fill=NAVY, font=f)
        y += line_h
    return tile


def _generate_bundle_thumbnail(sizes: Sizes, cols: int, rows: int,
                               stem: str, fillers: list[str]) -> dict[int, Path]:
    """cols x rows grid. First len(PRODUCTS) cells are products, rest are fillers."""
    W = H = sizes.master

    base = Image.new("RGB", (W, H), NAVY)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Header
    header_h = int(H * 0.20)
    draw.rounded_rectangle((70, 60, W - 70, 60 + header_h), radius=42,
                           fill=(255, 255, 255, 245))

    font_title = _load_font(68, bold=True)
    font_sub = _load_font(50, bold=False)
    font_badge = _load_font(46, bold=True)
    font_chip = _load_font(32, bold=False)
    font_tile_label = _load_font(30, bold=True)
    font_filler = _load_font(34, bold=True)

    draw.text((110, 92), "LLAMA LLAMA", fill=INK, font=font_title)
    draw.text((110, 92 + 82), "RED PAJAMA", fill=INK, font=font_sub)

    badge_text = "COMPLETE BUNDLE"
    badge_w = int(draw.textlength(badge_text, font=font_badge)) + 90
    badge_h = 96
    bx1 = W - 90 - badge_w
    by1 = 82
    draw.rounded_rectangle((bx1, by1, bx1 + badge_w, by1 + badge_h), radius=40,
                           fill=TEAL + (255,))
    draw.text((bx1 + 45, by1 + 20), badge_text, fill=(255, 255, 255), font=font_badge)

    # Collage panel
    panel_x1 = 70
    panel_y1 = 60 + header_h + 35
    panel_x2 = W - 70
    panel_y2 = H - 210
    panel_w = panel_x2 - panel_x1
    panel_h = panel_y2 - panel_y1

    shadow = Image.new("RGBA", (panel_w, panel_h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle((0, 0, panel_w, panel_h), radius=46, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=18))
    overlay.alpha_composite(shadow, (panel_x1 + 10, panel_y1 + 16))
    draw.rounded_rectangle((panel_x1, panel_y1, panel_x2, panel_y2), radius=46,
                           fill=(255, 255, 255, 250))

    # Grid collage
    pad = 40
    gap = 18
    label_h = 44          # space for the label chip under each tile
    gx1 = panel_x1 + pad
    gy1 = panel_y1 + pad
    gx2 = panel_x2 - pad
    gy2 = panel_y2 - pad
    cell_w = (gx2 - gx1 - gap * (cols - 1)) // cols
    cell_h = (gy2 - gy1 - gap * (rows - 1)) // rows
    tile_w = cell_w
    tile_h = cell_h - label_h

    fallbacks: list[str] = []
    cells: list[tuple[str, Image.Image | None]] = []  # (label, image or None for filler)

    for subfolder, to_name, label, pack_prefix in PRODUCTS:
        tile = _product_tile_image(subfolder, to_name, label, pack_prefix,
                                   tile_w, tile_h, font_tile_label, fallbacks)
        cells.append((label, tile))

    for filler_text in fillers:
        cells.append(("", _filler_tile(filler_text, tile_w, tile_h, font_filler)))

    # truncate or pad defensively to cols*rows
    cells = cells[: cols * rows]
    while len(cells) < cols * rows:
        cells.append(("", _filler_tile("Small Wins", tile_w, tile_h, font_filler)))

    font_label = _load_font(24, bold=True)
    for i, (label, tile) in enumerate(cells):
        r, c = divmod(i, cols)
        x = gx1 + c * (cell_w + gap)
        y = gy1 + r * (cell_h + gap)

        # tile with subtle border + shadow
        framed = Image.new("RGBA", (tile_w + 8, tile_h + 8), (250, 250, 250, 255))
        fdraw = ImageDraw.Draw(framed)
        fdraw.rounded_rectangle((0, 0, framed.size[0] - 1, framed.size[1] - 1),
                                radius=10, outline=(200, 200, 200, 255), width=2)
        framed.paste(tile.convert("RGBA"), (4, 4))
        overlay.alpha_composite(framed, (x - 4, y - 4))

        # label chip under tile
        if label:
            lw = draw.textlength(label, font=font_label)
            chip_x1 = x + (cell_w - int(lw) - 28) // 2
            chip_x2 = chip_x1 + int(lw) + 28
            chip_y1 = y + tile_h + 6
            chip_y2 = chip_y1 + label_h - 10
            _draw_chip(draw, (chip_x1, chip_y1, chip_x2, chip_y2), label, font_label)

    # Chips row
    chips = ["15 Activities", "Color + B&W", "Differentiated", "AAC + Literacy"]
    chip_y = panel_y2 + 28
    chip_gap = 18
    chip_h = 64
    total_w = W - 140
    chip_w = (total_w - chip_gap * (len(chips) - 1)) // len(chips)
    start_x = 70
    for i, t in enumerate(chips):
        x1 = start_x + i * (chip_w + chip_gap)
        _draw_chip(draw, (x1, chip_y, x1 + chip_w, chip_y + chip_h), t, font_chip)

    footer = "Small Wins Studio"
    fw = draw.textlength(footer, font=font_chip)
    draw.text(((W - fw) / 2, chip_y + chip_h + 12), footer,
              fill=(255, 255, 255, 220), font=font_chip)

    composed = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")

    MARKETING_DIR.mkdir(parents=True, exist_ok=True)
    out_paths: dict[int, Path] = {}

    master_path = MARKETING_DIR / f"{stem}_{sizes.master}x{sizes.master}.png"
    composed.save(master_path, format="PNG", optimize=True)
    out_paths[sizes.master] = master_path

    for side in (sizes.tpt_min, sizes.s500, sizes.s280):
        thumb = composed.resize((side, side), Image.Resampling.LANCZOS)
        out_path = MARKETING_DIR / f"{stem}_{side}x{side}.png"
        thumb.save(out_path, format="PNG", optimize=True)
        out_paths[side] = out_path

    if fallbacks:
        print(f"[{stem}] Fallback tiles:")
        for fb in fallbacks:
            print(f"  - {fb}")
    else:
        print(f"[{stem}] All {len(PRODUCTS)} tiles rendered from Teacher Overview PDFs.")

    return out_paths


def generate_all() -> None:
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow not available. Install with: pip install Pillow")
    if not (PYMUPDF_AVAILABLE or PDF2IMAGE_AVAILABLE):
        raise RuntimeError("Install pymupdf (recommended) OR pdf2image")

    sizes = Sizes()
    print(f"Output dir: {MARKETING_DIR}")

    print("Generating 4x4 bundle thumbnail...")
    _generate_bundle_thumbnail(
        sizes, cols=4, rows=4, stem="llrp_bundle_thumbnail",
        fillers=["BONUS: Start Here + IEP Sheet"],
    )

    print("Generating 5x3 alt bundle thumbnail...")
    _generate_bundle_thumbnail(
        sizes, cols=5, rows=3, stem="llrp_bundle_thumbnail_alt",
        fillers=[],
    )

    print("OK LLRP bundle thumbnails generated.")


if __name__ == "__main__":
    generate_all()
