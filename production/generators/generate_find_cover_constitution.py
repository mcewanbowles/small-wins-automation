#!/usr/bin/env python3
import os
import shutil
from io import BytesIO
from pathlib import Path

from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw

import io
import sys


THEME_ID = "brown_bear"
PRODUCT = "find_cover"

LEVEL_LABELS = {
    1: "Errorless",
    2: "Supported",
    3: "Independent",
    4: "Generalization",
    5: "Extension",
}


# Ensure repo root is importable so `import utils` works when running this script directly.
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from utils.sws_design import DPI  # noqa: E402
from utils.sws_design import LEVEL_COLORS as SWS_LEVEL_COLORS  # noqa: E402
from utils.sws_design import apply_small_wins_frame  # noqa: E402


LEVEL_COLORS = {
    1: "#FF8C42",
    2: "#4A90E2",
    3: "#7CB342",
    4: "#9C27B0",
    5: "#E74C3C",
}


def _icon_path() -> Path:
    root = _get_project_root()
    icons_colored_dir = root / "assets" / "themes" / THEME_ID / "icons_colored"
    legacy_icons_dir = root / "assets" / "themes" / THEME_ID / "icons"
    icons_dir = icons_colored_dir if icons_colored_dir.exists() else legacy_icons_dir
    p = icons_dir / "Brown bear.png"
    if not p.exists():
        p = icons_dir / "Brown Bear.png"
    return p


def _level_accent_hex(level: int, mode: str) -> str:
    if mode == "bw":
        return "#808080"
    return SWS_LEVEL_COLORS.get(level, "#2CA6A4")


def _render_find_cover_cover_page(
    *,
    level: int,
    level_label: str,
    mode: str,
    theme_name: str,
    pack_code: str,
    page_num: int,
    total_pages: int,
    activity_pages: int | None,
) -> Image.Image:
    w = int(letter[0] * DPI / 72)
    h = int(letter[1] * DPI / 72)
    page = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(page)

    icon = None
    p = _icon_path()
    if p.exists():
        try:
            icon = Image.open(p).convert("RGBA")
            if mode == "bw":
                icon = icon.convert("L").convert("RGBA")
        except Exception:
            icon = None

    apply_small_wins_frame(
        page,
        product_title=f"{theme_name} Find & Cover",
        subtitle=f"Level {level} — {level_label}",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        accent_color_hex=_level_accent_hex(level, mode),
        footer_title=f"{theme_name} Find & Cover | Level {level}",
        header_left_icon=icon,
        header_left_icon_flip=False,
        header_left_icon_y_offset_px=int(0.06 * DPI),
        footer_y_offset_px=int(0.08 * DPI),
        draw_subtitle=True,
        draw_footer=True,
    )

    s = DPI / 72

    art_box = int(3.05 * DPI)
    art_x = (w - art_box) // 2
    art_y = int(2.35 * DPI)
    draw.rounded_rectangle(
        [art_x, art_y, art_x + art_box, art_y + art_box],
        radius=int(0.20 * DPI),
        outline=apply_small_wins_frame.__globals__["hex_to_rgb"](_level_accent_hex(level, mode)),
        width=max(1, int(4 * s)),
        fill="white",
    )

    if icon is not None:
        from utils.sws_design import _make_near_white_transparent
        icon_work = _make_near_white_transparent(icon.copy())
        try:
            bbox = icon_work.split()[3].getbbox()
            if bbox:
                icon_work = icon_work.crop(bbox)
        except Exception:
            pass

        # Scale to fill 80% of art box (resize UP since source icons are small)
        target = int(art_box * 0.80)
        iw, ih = icon_work.size
        scale_factor = min(target / iw, target / ih)
        icon_work = icon_work.resize((int(iw * scale_factor), int(ih * scale_factor)), Image.Resampling.LANCZOS)
        page.paste(
            icon_work,
            (art_x + (art_box - icon_work.width) // 2, art_y + (art_box - icon_work.height) // 2),
            icon_work,
        )

    from PIL import ImageFont
    from utils.sws_design import hex_to_rgb

    _FONT_COMIC = "C:/Windows/Fonts/comic.ttf"
    _FONT_COMIC_BOLD = "C:/Windows/Fonts/comicbd.ttf"
    heading_font = ImageFont.truetype(_FONT_COMIC_BOLD, int(14 * (DPI / 72)))
    bullet_font = ImageFont.truetype(_FONT_COMIC, int(11 * (DPI / 72)))

    def _ts(t: str, f):
        bbox = draw.textbbox((0, 0), t, font=f)
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])

    def _fit_font_local(text, *, max_px, min_px, max_w, max_h):
        for px in range(max_px, min_px - 1, -1):
            f = ImageFont.truetype(_FONT_COMIC, px)
            tw, th = _ts(text, f)
            if tw <= max_w and th <= max_h:
                return f
        return ImageFont.truetype(_FONT_COMIC, min_px)

    accent_rgb = hex_to_rgb(_level_accent_hex(level, mode))
    navy_rgb = hex_to_rgb("#1E3A5F")

    # --- Layout below artwork box (matches Bingo gold standard) ---
    left = art_x
    right_limit = art_x + art_box
    text_width = right_limit - left

    # 1) Tagline
    y = art_y + art_box + int(0.18 * DPI)
    desc = "Print, play, and practice\u2014differentiated levels for SPED learners"
    fitted_desc = _fit_font_local(
        desc,
        max_px=int(32 * (DPI / 72)),
        min_px=int(16 * (DPI / 72)),
        max_w=text_width,
        max_h=int(0.45 * DPI),
    )
    dw, dh = _ts(desc, fitted_desc)
    draw.text((left + (text_width - dw) // 2, y), desc, fill=navy_rgb, font=fitted_desc)
    y += dh + int(0.18 * DPI)

    # 2) "What\u2019s Included" heading
    heading = "What\u2019s Included"
    hw, hh = _ts(heading, heading_font)
    draw.text((left, y), heading, fill=accent_rgb, font=heading_font)
    y += hh + int(0.06 * DPI)

    # 3) Bullet list
    activity_line = f"{activity_pages} activity pages" if activity_pages is not None else "Activity pages included"
    bullets = [
        activity_line,
        "Print-ready cutout pieces",
        "Storage labels",
        "Color + black & white",
        "Optional laminate for reuse",
    ]
    bullet_indent = left + int(0.12 * DPI)
    for b in bullets:
        line = f"\u2022  {b}"
        draw.text((bullet_indent, y), line, fill=navy_rgb, font=bullet_font)
        y += int(0.19 * DPI)

    # 4) "Quick Start" heading
    y += int(0.10 * DPI)
    quick = "Quick Start"
    qw, qh = _ts(quick, heading_font)
    draw.text((left, y), quick, fill=accent_rgb, font=heading_font)
    y += qh + int(0.06 * DPI)

    # 5) Quick Start bullet points
    qs_bullets = [
        "Print activity pages and cutouts",
        "Cover matches with tokens or dabbers",
        "Store extras using the included labels",
    ]
    qs_indent = left + int(0.12 * DPI)
    for qb in qs_bullets:
        qline = f"\u2022  {qb}"
        draw.text((qs_indent, y), qline, fill=navy_rgb, font=bullet_font)
        y += int(0.19 * DPI)

    return page


def _pil_page_to_pdf_page(img: Image.Image):
    buf_png = io.BytesIO()
    img.save(buf_png, format="PNG", dpi=(DPI, DPI))
    buf_png.seek(0)

    buf_pdf = io.BytesIO()
    c = canvas.Canvas(buf_pdf, pagesize=letter)
    c.drawImage(ImageReader(buf_png), 0, 0, width=letter[0], height=letter[1])
    c.showPage()
    c.save()
    buf_pdf.seek(0)
    return PdfReader(buf_pdf).pages[0]


def _get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def add_preview_watermark(input_pdf_path: str, output_pdf_path: str) -> str:
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    width, height = letter
    can.saveState()
    # Keep PREVIEW fully inside the page border.
    can.setFont("Helvetica-Bold", 140)
    can.setFillColor(HexColor("#8A8A8A"))
    try:
        can.setFillAlpha(0.18)
    except Exception:
        pass

    watermark_text = "PREVIEW"
    # Move the watermark down so it covers the main activity area (grid) rather than the header strip.
    can.translate(width / 2, (height / 2) - 55)
    can.rotate(32)
    can.drawCentredString(0, 0, watermark_text)

    can.restoreState()
    can.save()

    packet.seek(0)
    watermark_pdf = PdfReader(packet)
    watermark_page = watermark_pdf.pages[0]

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        page.merge_page(watermark_page)
        writer.add_page(page)

    with open(output_pdf_path, "wb") as output_file:
        writer.write(output_file)

    print(f"OK Created preview PDF: {output_pdf_path}")
    return output_pdf_path


def _copy_and_rename_level_pdfs(samples_dir: Path, final_dir: Path) -> dict:
    outputs: dict[str, Path] = {"levels": {}, "storage": {}, "quick_start": None}

    # Quick start
    quick_start_src = samples_dir / "brown_bear_find_cover_quick_start.pdf"
    if quick_start_src.exists():
        quick_start_dst = final_dir / "brown_bear_find_cover_quick_start.pdf"
        shutil.copy2(quick_start_src, quick_start_dst)
        outputs["quick_start"] = quick_start_dst

    # Storage labels
    for mode in ["color", "bw"]:
        src = samples_dir / f"brown_bear_find_cover_storage_labels_{mode}.pdf"
        if src.exists():
            dst = final_dir / f"brown_bear_find_cover_storage_labels_{mode}_FINAL.pdf"
            shutil.copy2(src, dst)
            outputs["storage"][mode] = dst

    # Level PDFs
    for level in range(1, 6):
        for mode in ["color", "bw"]:
            src = samples_dir / f"brown_bear_find_cover_level{level}_{mode}.pdf"
            if not src.exists():
                raise FileNotFoundError(str(src))
            label = LEVEL_LABELS[level]
            dst = final_dir / f"brown_bear_find_cover_level{level}_{label}_{mode}_FINAL.pdf"
            shutil.copy2(src, dst)
            outputs["levels"][(level, mode)] = dst

    return outputs


def _merge_full_product(level_pdfs: list[Path], output_path: Path) -> Path:
    merger = PdfMerger()
    for p in level_pdfs:
        merger.append(str(p))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        merger.write(f)
    merger.close()
    return output_path


def _merge_level_with_cover_and_storage(
    *,
    cover_page,
    level_pdf: Path,
    storage_labels_pdf: Path,
    storage_level_index: int,
    output_path: Path,
) -> Path:
    writer = PdfWriter()

    # Cover
    writer.add_page(cover_page)

    # Level PDF (activities + cutouts)
    level_reader = PdfReader(str(level_pdf))
    for p in level_reader.pages:
        # Sorting labels were removed from the product spec.
        # If an older PDF still contains a Sorting Labels page, drop it here.
        try:
            extracted = (p.extract_text() or "")
            if "Sorting Labels" in extracted:
                continue
            # Drop empty cutout pages if they contain no images.
            if "Cutout Pieces" in extracted:
                try:
                    resources = p.get("/Resources") or {}
                    xobj = resources.get("/XObject") or {}
                    if not bool(getattr(xobj, "keys", lambda: [])()):
                        continue
                except Exception:
                    pass
        except Exception:
            pass

        writer.add_page(p)

    # Storage labels (single page per level)
    storage_reader = PdfReader(str(storage_labels_pdf))
    if storage_level_index < 0 or storage_level_index >= len(storage_reader.pages):
        raise IndexError(f"Storage labels page index out of range: {storage_level_index}")
    writer.add_page(storage_reader.pages[storage_level_index])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def main() -> int:
    project_root = _get_project_root()

    samples_dir = project_root / "samples" / THEME_ID / PRODUCT
    final_dir = project_root / "production" / "final_products" / THEME_ID / PRODUCT
    os.makedirs(final_dir, exist_ok=True)

    if not samples_dir.exists():
        raise SystemExit(f"Missing samples dir: {samples_dir}")

    print("=" * 60)
    print("Brown Bear Find & Cover - Production Export")
    print("=" * 60)

    outputs = _copy_and_rename_level_pdfs(samples_dir, final_dir)

    merged_levels: dict[tuple[int, str], Path] = {}

    # Make per-level FINAL PDFs self-contained: cover + level + storage labels
    for lvl in range(1, 6):
        label = LEVEL_LABELS[lvl]
        for mode in ["color", "bw"]:
            level_pdf = outputs["levels"][(lvl, mode)]
            storage_pdf = outputs["storage"].get(mode)
            if storage_pdf is None or not storage_pdf.exists():
                raise FileNotFoundError(str(storage_pdf) if storage_pdf else f"missing storage labels for {mode}")

            activity_pages = None
            try:
                total_pages = len(PdfReader(str(level_pdf)).pages)
                # Level PDFs include: activity pages + 1 cutout pieces page.
                # (The cover is added separately in this production exporter.)
                activity_pages = max(1, total_pages - 1)
            except Exception:
                activity_pages = None

            cover_img = _render_find_cover_cover_page(
                level=lvl,
                level_label=label,
                mode=mode,
                theme_name="Brown Bear",
                pack_code="BB04",
                page_num=1,
                total_pages=(len(PdfReader(str(level_pdf)).pages) + 1) if level_pdf.exists() else 1,
                activity_pages=activity_pages,
            )
            cover_page = _pil_page_to_pdf_page(cover_img)

            # Windows can lock PDFs that are open in viewers/preview panes, which makes os.replace fail.
            # Write the merged, self-contained PDF to a separate filename and let packagers prefer it.
            merged_out = final_dir / f"brown_bear_find_cover_level{lvl}_{label}_{mode}_INTEGRATED_FINAL.pdf"
            _merge_level_with_cover_and_storage(
                cover_page=cover_page,
                level_pdf=level_pdf,
                storage_labels_pdf=storage_pdf,
                storage_level_index=lvl - 1,
                output_path=merged_out,
            )
            merged_levels[(lvl, mode)] = merged_out

    # Full merged products (optional but useful for previews)
    color_levels = [merged_levels.get((lvl, "color"), outputs["levels"][(lvl, "color")]) for lvl in range(1, 6)]
    bw_levels = [merged_levels.get((lvl, "bw"), outputs["levels"][(lvl, "bw")]) for lvl in range(1, 6)]

    color_full = _merge_full_product(color_levels, final_dir / "brown_bear_find_cover_color_FINAL.pdf")
    bw_full = _merge_full_product(bw_levels, final_dir / "brown_bear_find_cover_bw_FINAL.pdf")

    # Full PREVIEW PDFs
    add_preview_watermark(str(color_full), str(final_dir / "brown_bear_find_cover_color_PREVIEW.pdf"))
    add_preview_watermark(str(bw_full), str(final_dir / "brown_bear_find_cover_bw_PREVIEW.pdf"))

    # Per-level PREVIEW PDFs (based on integrated color FINAL when available)
    for lvl in range(1, 6):
        label = LEVEL_LABELS[lvl]
        src = merged_levels.get((lvl, "color"), outputs["levels"][(lvl, "color")])
        dst = final_dir / f"brown_bear_find_cover_level{lvl}_preview.pdf"
        add_preview_watermark(str(src), str(dst))
        print(f"OK Level {lvl} preview: {dst.name}")

    print("\nOK Final products exported to:")
    print(f"  {final_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
