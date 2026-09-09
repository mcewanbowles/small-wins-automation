# SWS-GEN-VERSION: 2026-07-07 (see CHANGELOG.md in this pack for what changed)
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
from datetime import datetime
import hashlib
import io
import json
import os

from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

from utils.sws_design import apply_small_wins_frame, shrink_font_to_fit_with_pt, hex_to_rgb, NAVY_HEX, DPI, safe_footer_inset_px
from utils.syllable_api import get_syllable_info
from utils.qa import assess_files


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
            f"Syllable Cards must not read from AAC core/global: {p}. Use assets/themes/<slug>/activity_images/."
        )
    files = [f for f in p.glob("*.png") if f.is_file() and not f.name.startswith(".")]
    if len(files) < 4:
        raise ValueError(f"Too few images in {p} — found {len(files)}, need at least 4.")


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


def _load_reviewed_items(images_folder: str) -> tuple[List[Tuple[str, Image.Image, int, str]], Path]:
    theme_dir = _theme_dir_for_images(images_folder)
    source = theme_dir / "config" / "syllables.json"
    if not source.exists():
        raise FileNotFoundError(f"Missing reviewed syllable data: {source}")
    data = json.loads(source.read_text(encoding="utf-8"))
    if data.get("reading_rope") != ["Phonological Awareness"]:
        raise ValueError("Syllable data must claim only Phonological Awareness")
    images = Path(images_folder)
    reviewed = []
    for entry in data.get("items") or []:
        key = str(entry.get("image_key") or "").strip()
        label = str(entry.get("label") or "").strip()
        count = entry.get("count")
        segmentation = str(entry.get("segmentation") or "").strip()
        path = images / f"{key}.png"
        if not path.exists() or not label or not isinstance(count, int) or count < 1 or not segmentation:
            raise ValueError(f"Invalid reviewed syllable item: {key or label or '(blank)'}")
        image = _prepare_icon(Image.open(path))
        reviewed.append((label, image, count, segmentation))
    if len(reviewed) < 4:
        raise ValueError("At least four reviewed syllable items are required")
    # Use all reviewed items (capped at 20) so the activity is not too small.
    return reviewed[:20], source


def _draw_syllable_cards_page(*, theme_name: str, pack_code: str, page_num: int, total_pages: int, index: int, items: List[Tuple[str, Image.Image, int, str]], header_left_icon: Image.Image | None) -> Image.Image:
    w = int(8.5 * DPI)
    h = int(11.0 * DPI)
    page = Image.new("RGB", (w, h), "white")
    apply_small_wins_frame(
        page,
        product_title="Syllable Cards",
        subtitle=f"{theme_name}",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        draw_footer=True,
        draw_subtitle=True,
        header_left_icon=header_left_icon,
        header_height_px=int(0.92 * DPI),
        accent_margin_px=int(0.12 * DPI),
        footer_y_offset_px=int(0.08 * DPI),
    )
    d = ImageDraw.Draw(page)
    instr = f"Clap the syllables: Set {index}"
    usable_w = int(w * 0.80)
    font, pt = shrink_font_to_fit_with_pt(instr, base_pt=20, max_width_px=usable_w, bold=True, brand="poppins", min_pt=12)
    tw, th = d.textbbox((0, 0), instr, font=font)[2:4]
    d.text(((w - tw) // 2, int(1.7 * DPI)), instr, fill=hex_to_rgb(NAVY_HEX), font=font)

    # Safe content bounds below header and above footer
    header_clear = int(1.80 * DPI)
    footer_inset = safe_footer_inset_px()
    top_y = max(int(2.2 * DPI), header_clear + int(12))
    bottom_y = h - footer_inset - int(12)

    # Four card boxes per page (2x2) with icons and segmented labels
    margin = int(0.8 * DPI)
    gap = int(0.35 * DPI)
    box_w = (w - (2 * margin) - gap) // 2
    # Fit two rows between top_y and bottom_y
    avail_h = max(1, (bottom_y - top_y))
    box_h = int((avail_h - gap) / 2)
    x0 = margin
    y0 = top_y
    inner_pad = int(0.18 * DPI)

    for r in range(2):
        for c in range(2):
            bx0 = x0 + c * (box_w + gap)
            by0 = y0 + r * (box_h + gap)
            # Box border
            d.rectangle([bx0, by0, bx0 + box_w, by0 + box_h], outline=(0, 0, 0), width=int(2 * (DPI / 72)))

            idx = r * 2 + c
            if idx < len(items):
                label, im, count, seg_text = items[idx]
                # Place icon
                try:
                    im_rgba = im if im.mode == "RGBA" else im.convert("RGBA")
                    img_max_w = box_w - 2 * inner_pad
                    img_max_h = int(box_h * 0.6)
                    iw, ih = im_rgba.size
                    if iw > 0 and ih > 0:
                        scale = min(img_max_w / iw, img_max_h / ih)
                        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
                        pim = im_rgba.resize((nw, nh), Image.Resampling.LANCZOS)
                        px = bx0 + (box_w - nw) // 2
                        py = by0 + inner_pad + max(0, (img_max_h - nh) // 2)
                        page.paste(pim, (px, py), pim)
                except Exception:
                    pass

                # Syllable info
                # Segmented label at bottom of box
                lab_max_w = box_w - 2 * inner_pad
                lab_y = by0 + box_h - inner_pad - int(0.2 * DPI)
                lab_font, _ = shrink_font_to_fit_with_pt(seg_text, base_pt=28, max_width_px=lab_max_w, bold=True, brand="poppins", min_pt=14)
                ltw, lth = d.textbbox((0, 0), seg_text, font=lab_font)[2:4]
                d.text((bx0 + (box_w - ltw) // 2, lab_y - lth), seg_text, fill=(0, 0, 0), font=lab_font)

                # Syllable count chip in top-right of box
                if count and isinstance(count, int) and count > 0:
                    diam = int(0.42 * DPI)
                    cx0 = bx0 + box_w - inner_pad - diam
                    cy0 = by0 + inner_pad
                    d.ellipse([cx0, cy0, cx0 + diam, cy0 + diam], fill=hex_to_rgb(NAVY_HEX))
                    txt = str(count)
                    chip_font, _ = shrink_font_to_fit_with_pt(txt, base_pt=26, max_width_px=diam - int(0.16 * DPI), bold=True, brand="poppins", min_pt=12)
                    bounds = d.textbbox((0, 0), txt, font=chip_font)
                    ttw, tth = bounds[2] - bounds[0], bounds[3] - bounds[1]
                    d.text((cx0 + (diam - ttw) // 2 - bounds[0], cy0 + (diam - tth) // 2 - bounds[1]), txt, fill=(255, 255, 255), font=chip_font)
    return page


def generate_syllable_cards_pack(images_folder: str, pack_code: str = "SYL01", theme_name: str = "Theme") -> bool:
    try:
        _validate_images_folder(images_folder)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    try:
        items, syllable_source = _load_reviewed_items(images_folder)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    # Guardrailed output path: Studioforge/OUTPUT/{pack_code}
    theme_dir = _theme_dir_for_images(images_folder)
    output_dir = theme_dir / "OUTPUT"
    if "_TLOT_ARCHIVED_DUPLICATE" in str(output_dir):
        print(f"❌ ERROR: Output path points into archived duplicate: {output_dir}")
        return False
    output_dir.mkdir(parents=True, exist_ok=True)

    # Split items into pages of up to 4 cards each (2x2 grid per page).
    ITEMS_PER_PAGE = 4
    page_count = max(1, (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    total_pages = page_count  # no teacher cover page

    # Resolve hero icon for the page header
    hero_path_str = None
    try:
        images_path = Path(images_folder).resolve()
        tdir = theme_dir
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
    except Exception:
        hero_path_str = None

    # Prepare header icon image (fallback to first activity image if no hero found)
    header_icon_img = None
    try:
        if hero_path_str:
            _im = Image.open(hero_path_str)
            header_icon_img = _prepare_icon(_im)
    except Exception:
        header_icon_img = None
    if header_icon_img is None and items:
        try:
            header_icon_img = items[0][1]
        except Exception:
            header_icon_img = None

    # Build one content page per chunk of up to 4 items.
    pages_content = []
    for i in range(page_count):
        chunk = items[i * ITEMS_PER_PAGE:(i + 1) * ITEMS_PER_PAGE]
        pages_content.append(
            _draw_syllable_cards_page(
                theme_name=theme_name,
                pack_code=pack_code,
                page_num=i + 1,  # content only, no cover
                total_pages=total_pages,
                index=i + 1,
                items=chunk,
                header_left_icon=header_icon_img,
            )
        )
    pages_color = pages_content

    # COLOR
    color_pdf = output_dir / f"{pack_code}_Syllable_Cards_COLOR.pdf"
    c = canvas.Canvas(str(color_pdf), pagesize=letter)
    for p in pages_color:
        buf = io.BytesIO()
        p.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    c.save()

    # BW
    bw_pdf = output_dir / f"{pack_code}_Syllable_Cards_BW.pdf"
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
    preview_pdf = output_dir / f"{pack_code}_Syllable_Cards_PREVIEW.pdf"
    c_prev = canvas.Canvas(str(preview_pdf), pagesize=letter)
    for p in pages_color:
        buf = io.BytesIO()
        p.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c_prev.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
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
            th.save(thumbs_dir / f"{pack_code}_Syllable_Cards_thumb{i}.png", "PNG")
    except Exception:
        pass

    # BuildResult
    try:
        thumbs = [str(p) for p in sorted((output_dir / "thumbnails").glob(f"{pack_code}_Syllable_Cards_thumb*.png"))]
        warnings = []
        try:
            warnings = assess_files(
                product_name="Syllable Cards",
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
            "product_name": "Syllable Awareness Cards",
            "slug": theme_dir.name,
            "pack_code": pack_code,
            "page_count": len(pages_color),
            "reading_rope": ["Phonological Awareness"],
            "teacher_review_required": True,
            "source": str(syllable_source),
            "source_sha256": hashlib.sha256(syllable_source.read_bytes()).hexdigest(),
            "files": {
                "color_pdf": str(color_pdf),
                "bw_pdf": str(bw_pdf),
                "preview_pdf": str(preview_pdf),
                "thumbnails": thumbs,
            },
            "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": warnings},
        }
        (output_dir / f"{pack_code}_Syllable_Cards_BuildResult.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass

    print(f"OK Generated: {color_pdf}")
    print(f"OK Generated: {bw_pdf}")
    print(f"OK Generated: {preview_pdf}")
    return True


def build_pdf(slug: str, book_title: str, pack_code: str) -> bool:
    """
    Adapter for GENERATE_ALL.py's BUILD_PDF_PRODUCTS convention, which passes
    (slug, book_title, pack_code) rather than a resolved images_folder path.
    Resolves the slug to a real folder the same way generate_all() does, then
    calls the real generator.
    """
    # Resolve via absolute repo root to avoid CWD issues
    repo_root = Path(__file__).resolve().parents[2]
    for folder in ("activity_images", "icons"):
        images_folder = repo_root / "assets" / "themes" / slug / folder
        if images_folder.exists():
            return generate_syllable_cards_pack(str(images_folder), pack_code=pack_code, theme_name=book_title)
    print(f"❌ No image folder found for slug '{slug}' (checked activity_images/icons)")
    return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        pack_code = sys.argv[1]
        theme_name = sys.argv[2]
    elif len(sys.argv) >= 2:
        pack_code = sys.argv[1]
        theme_name = "Theme"
    else:
        print("Usage: python SYLLABLE_CARDS.py <PACK_CODE> \"Theme Name\"")
        sys.exit(1)
    images_folder = os.path.join(os.getcwd(), "images")
    ok = generate_syllable_cards_pack(images_folder, pack_code, theme_name)
    sys.exit(0 if ok else 1)
