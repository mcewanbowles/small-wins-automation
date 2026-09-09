from __future__ import annotations

def _validate_images_folder(images_folder: str) -> None:
    p = Path(images_folder)
    if not p.exists():
        raise FileNotFoundError(f"Images folder not found: {images_folder}")
    sp = str(p).lower()
    if "_tlot_archived_duplicate" in sp:
        raise ValueError(
            f"Images folder is inside the archived duplicate tree: {p}. Use assets/themes/<slug>/activity_images/."
        )
    if any(k in sp for k in ["aac_core", "aac_core_text", "global"]):
        raise ValueError(
            f"Story Elements Mat must not read from AAC core/global: {p}. Use assets/themes/<slug>/activity_images/."
        )
    files = [f for f in p.glob("*.png") if f.is_file() and not f.name.startswith(".")]
    if len(files) < 4:
        raise ValueError(f"Too few images in {p} — found {len(files)}, need at least 4.")

from pathlib import Path
from typing import List, Tuple
from datetime import datetime
import io
import json
import os

from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

from utils.sws_design import apply_small_wins_frame, generate_internal_cover_page, generate_teacher_cover_page, shrink_font_to_fit_with_pt, hex_to_rgb, NAVY_HEX, DPI, safe_footer_inset_px
from utils.UNIVERSAL_STANDARDS import COLOUR_COMPREHENSION, COLOUR_PHONOLOGICAL, LEVEL_3_AMBER, COLOUR_GAMES, BRAND_TEAL
from utils.qa import assess_files

PAGE_WIDTH, PAGE_HEIGHT = letter


def _read_icons(images_folder: str) -> List[Tuple[str, Image.Image]]:
    items: List[Tuple[str, Image.Image]] = []
    base = Path(images_folder)
    if not base.exists():
        return items
    for p in sorted(base.glob("*.png")):
        sp = str(p).lower()
        if any(k in sp for k in ["aac_core", "aac_core_text", "global"]):
            continue
        try:
            im = Image.open(p)
            if im.mode != "RGBA":
                im = im.convert("RGBA")
            items.append((p.stem.replace("_", " ").title(), im))
        except Exception:
            continue
    return items


def _theme_dir_for_images(images_folder: str) -> Path:
    path = Path(images_folder).resolve()
    if path.name == "icons" and path.parent.name == ".sf_build":
        return path.parent.parent
    return path.parent


def _find_theme_assets_from_images_folder(images_folder: str) -> Tuple[Image.Image | None, str | None]:
    base = _theme_dir_for_images(images_folder)
    # Fallback to assets/themes/<slug> for hero/book cover if images come from a non-theme path
    try:
        repo_root = Path(__file__).resolve().parents[3]
        slug = Path(images_folder).resolve().name
        alt_dir = repo_root / "assets" / "themes" / slug
    except Exception:
        alt_dir = None
    hero_path = None
    for hp in [
        base / "hero_header.png",
        base / "heroes" / "hero_header.png",
        base / "characters" / "hero_header.png",
        base / "hero.png",
        base / "heroes" / "hero.png",
        base / "characters" / "hero.png",
        base / "header_icon.png",
    ] + (([
        alt_dir / "hero_header.png",
        alt_dir / "heroes" / "hero_header.png",
        alt_dir / "characters" / "hero_header.png",
        alt_dir / "hero.png",
        alt_dir / "heroes" / "hero.png",
        alt_dir / "characters" / "hero.png",
        alt_dir / "header_icon.png",
    ]) if alt_dir and alt_dir.exists() else []):
        if hp.exists():
            hero_path = hp
            break
    hero_img = None
    if hero_path and hero_path.exists():
        try:
            im = Image.open(hero_path)
            hero_img = im.convert("RGBA") if im.mode != "RGBA" else im
        except Exception:
            hero_img = None
    book_cover_path = None
    search_dirs = [base, base / "covers", base / "images", base / "marketing", base / "book"]
    if alt_dir and alt_dir.exists():
        search_dirs += [alt_dir, alt_dir / "covers", alt_dir / "images", alt_dir / "marketing", alt_dir / "book"]
    for sd in search_dirs:
        for nm in ["book_cover", "cover", "front_cover", "bookfront", "book", "cover_reference"]:
            for ex in ["png", "jpg", "jpeg", "webp"]:
                fp = sd / f"{nm}.{ex}"
                if fp.exists():
                    book_cover_path = str(fp)
                    break
            if book_cover_path:
                break
        if book_cover_path:
            break
    return hero_img, book_cover_path


def _draw_story_elements_page(*, theme_name: str, pack_code: str, page_num: int, total_pages: int, header_icon: Image.Image | None) -> Image.Image:
    w = int(8.5 * DPI)
    h = int(11.0 * DPI)
    page = Image.new("RGB", (w, h), "white")
    apply_small_wins_frame(
        page,
        product_title="Story Elements Mat",
        subtitle=f"{theme_name}",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        footer_title=f"{theme_name} | Story Elements Mat",
        header_left_icon=header_icon,
    )
    d = ImageDraw.Draw(page)
    # Guidance header
    instr = "CHARACTERS · SETTING · PROBLEM · EVENTS · FEELINGS · SOLUTION"
    usable_w = int(w * 0.82)
    font, _ = shrink_font_to_fit_with_pt(instr, base_pt=18, max_width_px=usable_w, bold=True, brand="poppins", min_pt=11)
    tw, th = d.textbbox((0, 0), instr, font=font)[2:4]
    d.text(((w - tw) // 2, int(1.65 * DPI)), instr, fill=hex_to_rgb(NAVY_HEX), font=font)

    # Four quadrants with coloured header strips and writing lines
    margin = int(0.65 * DPI)
    gap = int(0.20 * DPI)
    header_h = int(0.38 * DPI)
    box_w = (w - (margin * 2) - gap) // 2
    x0 = margin
    y0 = int(2.1 * DPI)
    bottom = h - safe_footer_inset_px() - int(0.20 * DPI)
    box_h = (bottom - y0 - gap * 2) // 3

    labels = [
        ("CHARACTERS", COLOUR_COMPREHENSION),
        ("SETTING", COLOUR_PHONOLOGICAL),
        ("PROBLEM", LEVEL_3_AMBER),
        ("KEY EVENTS", COLOUR_GAMES),
        ("FEELINGS", BRAND_TEAL),
        ("SOLUTION", COLOUR_COMPREHENSION),
    ]

    for i in range(6):
        r = i // 2
        c = i % 2
        bx0 = x0 + c * (box_w + gap)
        by0 = y0 + r * (box_h + gap)
        bx1 = bx0 + box_w
        by1 = by0 + box_h
        # Outer box
        d.rectangle([bx0, by0, bx1, by1], outline=hex_to_rgb(NAVY_HEX), width=int(2 * (DPI / 72)))
        # Header strip
        label, col = labels[i]
        d.rectangle([bx0, by0, bx1, by0 + header_h], fill=hex_to_rgb(col))
        # Header text (white)
        lb_font, _ = shrink_font_to_fit_with_pt(label, base_pt=15, max_width_px=box_w - int(0.4 * DPI), bold=True, brand="poppins", min_pt=10)
        bounds = d.textbbox((0, 0), label, font=lb_font)
        ltw, lth = bounds[2] - bounds[0], bounds[3] - bounds[1]
        d.text((bx0 + (box_w - ltw) // 2 - bounds[0], by0 + (header_h - lth) // 2 - bounds[1]), label, fill=(255, 255, 255), font=lb_font)
        # Writing lines (2 lines)
        content_h = box_h - header_h
        pad = int(0.22 * DPI)
        for fraction in (0.34, 0.67):
            line_y = by0 + header_h + int(fraction * content_h)
            d.line([(bx0 + pad, line_y), (bx1 - pad, line_y)], fill=hex_to_rgb(NAVY_HEX), width=1)
    return page


def generate_story_elements_mat_pack(images_folder: str, pack_code: str = "SEM01", theme_name: str = "Theme") -> bool:
    try:
        _validate_images_folder(images_folder)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    items = _read_icons(images_folder)
    images_path = Path(images_folder)
    # Guardrailed output path: Studioforge/OUTPUT/{pack_code}
    theme_dir = _theme_dir_for_images(images_folder)
    output_dir = theme_dir / "OUTPUT"
    if "_TLOT_ARCHIVED_DUPLICATE" in str(output_dir):
        print(f"❌ ERROR: Output path points into archived duplicate: {output_dir}")
        return False
    output_dir.mkdir(parents=True, exist_ok=True)

    page_count = 1
    total_pages = page_count  # No cover page in this PDF; cover added during packaging

    hero_img, book_cover_path = _find_theme_assets_from_images_folder(images_folder)
    if hero_img is None and items:
        hero_img = items[0][1]

    # No cover page — teacher cover is added later during packaging
    content = _draw_story_elements_page(theme_name=theme_name, pack_code=pack_code, page_num=1, total_pages=total_pages, header_icon=hero_img)

    pages_color = [content]

    # COLOR
    color_pdf = output_dir / f"{pack_code}_Story_Elements_Mat_COLOR.pdf"
    c = canvas.Canvas(str(color_pdf), pagesize=letter)
    for p in pages_color:
        buf = io.BytesIO()
        p.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    c.save()

    # BW
    bw_pdf = output_dir / f"{pack_code}_Story_Elements_Mat_BW.pdf"
    c_bw = canvas.Canvas(str(bw_pdf), pagesize=letter)
    for p in pages_color:
        g = p.convert("L").convert("RGB")
        buf = io.BytesIO()
        g.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c_bw.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c_bw.showPage()
    c_bw.save()

    # PREVIEW with watermark
    preview_pdf = output_dir / f"{pack_code}_Story_Elements_Mat_PREVIEW.pdf"
    c_prev = canvas.Canvas(str(preview_pdf), pagesize=letter)
    for p in pages_color:
        buf = io.BytesIO()
        p.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c_prev.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        # Watermark
        c_prev.saveState()
        try:
            c_prev.setFont("Helvetica-Bold", 140)
            c_prev.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
        except Exception:
            c_prev.setFont("Helvetica-Bold", 110)
            c_prev.setFillColorRGB(0.6, 0.6, 0.6)
        c_prev.translate(PAGE_WIDTH / 2, PAGE_HEIGHT / 2)
        c_prev.rotate(45)
        c_prev.drawCentredString(0, 0, "PREVIEW")
        c_prev.restoreState()
        c_prev.showPage()
    c_prev.save()

    # Thumbnails
    try:
        thumbs_dir = output_dir / "thumbnails"
        thumbs_dir.mkdir(parents=True, exist_ok=True)
        for i, p in enumerate(pages_color[:2], start=1):
            th = p.copy()
            th.thumbnail((500, 647), Image.Resampling.LANCZOS)
            th.save(thumbs_dir / f"{pack_code}_Story_Elements_Mat_thumb{i}.png", "PNG")
    except Exception:
        pass

    # BuildResult manifest and QA warnings
    try:
        thumbs = [str(p) for p in sorted((output_dir / "thumbnails").glob(f"{pack_code}_Story_Elements_Mat_thumb*.png"))]
        warnings = []
        try:
            warnings = assess_files(
                product_name="Story Elements Mat",
                color_pdf=str(color_pdf),
                bw_pdf=str(bw_pdf),
                preview_pdf=str(preview_pdf),
                expected_pages=None,
            )
        except Exception:
            warnings = []
        manifest = {
            "schema_version": 1,
            "status": "pilot_review",
            "product_name": "Story Elements Mat",
            "slug": theme_dir.name,
            "pack_code": pack_code,
            "page_count": len(pages_color),
            "reading_rope": ["Literacy Knowledge", "Language Structures", "Verbal Reasoning"],
            "teacher_review_required": True,
            "files": {
                "color_pdf": str(color_pdf),
                "bw_pdf": str(bw_pdf),
                "preview_pdf": str(preview_pdf),
                "thumbnails": thumbs,
            },
            "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": warnings},
        }
        (output_dir / f"{pack_code}_Story_Elements_Mat_BuildResult.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass

    print(f"OK Generated: {color_pdf}")
    print(f"OK Generated: {bw_pdf}")
    print(f"OK Generated: {preview_pdf}")
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        pack_code = sys.argv[1]
        theme_name = sys.argv[2]
    elif len(sys.argv) >= 2:
        pack_code = sys.argv[1]
        theme_name = "Theme"
    else:
        print("Usage: python STORY_ELEMENTS_MAT.py <PACK_CODE> \"Theme Name\"")
        sys.exit(1)
    images_folder = os.path.join(os.getcwd(), "images")
    ok = generate_story_elements_mat_pack(images_folder, pack_code, theme_name)
    sys.exit(0 if ok else 1)
