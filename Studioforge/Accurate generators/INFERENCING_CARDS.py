# SWS-GEN-VERSION: 2026-07-07 (see CHANGELOG.md in this pack for what changed)
from __future__ import annotations

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

from utils.sws_design import apply_small_wins_frame, generate_teacher_cover_page, shrink_font_to_fit_with_pt, hex_to_rgb, NAVY_HEX, DPI
from utils.sws_design import safe_footer_inset_px
from utils.inference_api import get_inference_prompts
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
            f"Inferencing Cards must not read from AAC core/global: {p}. Use assets/themes/<slug>/activity_images/."
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


def _draw_inferencing_cards_page(*, theme_name: str, pack_code: str, page_num: int, total_pages: int, index: int, items: List[Tuple[str, Image.Image]], header_left_icon: Image.Image | None) -> Image.Image:
    w = int(8.5 * DPI)
    h = int(11.0 * DPI)
    page = Image.new("RGB", (w, h), "white")
    apply_small_wins_frame(
        page,
        product_title="Inferencing Cards",
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
    instr = f"Use clues to infer: Card set {index}"
    usable_w = int(w * 0.80)
    font, pt = shrink_font_to_fit_with_pt(instr, base_pt=20, max_width_px=usable_w, bold=True, brand="poppins", min_pt=12)
    tw, th = d.textbbox((0, 0), instr, font=font)[2:4]
    d.text(((w - tw) // 2, int(1.7 * DPI)), instr, fill=hex_to_rgb(NAVY_HEX), font=font)
    # Safe bounds below header and above footer
    header_clear = int(1.80 * DPI)
    footer_inset = safe_footer_inset_px()
    top_y = max(int(2.2 * DPI), header_clear + int(12))
    bottom_y = h - footer_inset - int(12)

    # Two large card boxes with icon and prompts
    margin = int(0.9 * DPI)
    gap = int(0.35 * DPI)
    box_w = w - 2 * margin
    avail_h = max(1, (bottom_y - top_y))
    box_h = int((avail_h - gap) / 2)
    x0 = margin
    y0 = top_y
    inner_pad = int(0.2 * DPI)
    lines_color = (0, 0, 0)

    for i in range(2):
        by0 = y0 + i * (box_h + gap)
        d.rectangle([x0, by0, x0 + box_w, by0 + box_h], outline=lines_color, width=int(2 * (DPI / 72)))
        # Icon zone ~60% height
        icon_max_h = int(box_h * 0.6)
        icon_max_w = box_w - 2 * inner_pad
        if i < len(items):
            label, im = items[i]
            try:
                im_rgba = im if im.mode == "RGBA" else im.convert("RGBA")
                iw, ih = im_rgba.size
                if iw > 0 and ih > 0:
                    scale = min(icon_max_w / iw, icon_max_h / ih)
                    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
                    pim = im_rgba.resize((nw, nh), Image.Resampling.LANCZOS)
                    px = x0 + (box_w - nw) // 2
                    py = by0 + inner_pad + max(0, (icon_max_h - nh) // 2)
                    page.paste(pim, (px, py), pim)
            except Exception:
                pass

            # Prompts below icon
            try:
                prompts = get_inference_prompts(label) or []
            except Exception:
                prompts = []
            if not prompts:
                prompts = [
                    "What can you infer?",
                    "Which clues helped you?",
                ]
            # Draw up to 2 prompt lines, then add Write/Speak response areas
            prompt_zone_top = by0 + inner_pad + icon_max_h + int(0.1 * DPI)
            prompt_left = x0 + inner_pad
            prompt_right = x0 + box_w - inner_pad
            max_w = prompt_right - prompt_left
            base_pt = 22
            cur_y = prompt_zone_top
            last_pth = int(0.14 * DPI)
            for txt in prompts[:2]:
                pfont, _ = shrink_font_to_fit_with_pt(txt, base_pt=base_pt, max_width_px=max_w, bold=False, brand="poppins", min_pt=12)
                ptw, pth = d.textbbox((0, 0), txt, font=pfont)[2:4]
                d.text((x0 + (box_w - ptw) // 2, cur_y), txt, fill=lines_color, font=pfont)
                cur_y += pth + int(0.12 * DPI)
                last_pth = pth

            # Response areas (clamped to avoid negative geometry)
            resp_top = cur_y + int(0.08 * DPI)
            resp_bot = by0 + box_h - inner_pad
            resp_h = max(0, resp_bot - resp_top)
            if resp_h > int(0.6 * DPI):
                write_h = int(resp_h * 0.45)
                speak_h = resp_h - write_h - int(0.12 * DPI)
            else:
                write_h = max(0, int(resp_h * 0.5))
                speak_h = max(0, resp_h - write_h)

            # Write area: label + ruled lines
            try:
                wlabel = "Write your idea:"
                wfont, _ = shrink_font_to_fit_with_pt(wlabel, base_pt=18, max_width_px=max_w, bold=False, brand="poppins", min_pt=12)
            except Exception:
                wfont = None
            wy = resp_top
            if write_h >= int(0.3 * DPI):
                if wfont is not None:
                    ltw, lth = d.textbbox((0, 0), wlabel, font=wfont)[2:4]
                    d.text((x0 + (box_w - ltw) // 2, wy), wlabel, fill=lines_color, font=wfont)
                    wy += lth + int(0.06 * DPI)
                lines_area_h = max(0, write_h - (wy - resp_top))
                gap_y = int(0.18 * DPI)
                if lines_area_h >= gap_y:
                    line_count = max(1, min(5, lines_area_h // gap_y))
                    ly = wy
                    for _ in range(line_count):
                        d.line([x0 + inner_pad, ly, x0 + box_w - inner_pad, ly], fill=lines_color, width=1)
                        ly += gap_y

            # Speak area: label + rounded rectangle
            sy = resp_top + write_h + int(0.12 * DPI)
            if speak_h >= int(0.28 * DPI):
                slabel = "Speak it:"
                try:
                    sfont, _ = shrink_font_to_fit_with_pt(slabel, base_pt=18, max_width_px=max_w, bold=False, brand="poppins", min_pt=12)
                except Exception:
                    sfont = None
                if sfont is not None:
                    stw, sth = d.textbbox((0, 0), slabel, font=sfont)[2:4]
                    d.text((x0 + (box_w - stw) // 2, sy), slabel, fill=lines_color, font=sfont)
                    sy += sth + int(0.06 * DPI)
                speak_top = sy
                speak_bot = min(resp_bot, speak_top + speak_h)
                if speak_bot > speak_top + 4:
                    rr = int(10 * (DPI / 72))
                    d.rounded_rectangle([x0 + inner_pad, speak_top, x0 + box_w - inner_pad, speak_bot], radius=rr, outline=lines_color, width=int(2 * (DPI / 72)))
    return page


def generate_inferencing_cards_pack(images_folder: str, pack_code: str = "INF01", theme_name: str = "Theme") -> bool:
    try:
        _validate_images_folder(images_folder)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    items = _read_icons(images_folder)
    images_path = Path(images_folder)
    # Guardrailed output path: Studioforge/OUTPUT/{pack_code}
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = repo_root / "Studioforge" / "OUTPUT" / pack_code
    if "_TLOT_ARCHIVED_DUPLICATE" in str(output_dir):
        print(f"❌ ERROR: Output path points into archived duplicate: {output_dir}")
        return False
    output_dir.mkdir(parents=True, exist_ok=True)

    page_count = 2
    total_pages = page_count + 1

    # Resolve hero/book assets for teacher cover
    hero_path_str = None
    book_cover_path_str = None
    try:
        # derive slug from images path
        images_path = Path(images_folder).resolve()
        slug_guess = images_path.parent.name if images_path.parent.name else None
        if slug_guess:
            tdir = Path(__file__).resolve().parents[2] / "assets" / "themes" / slug_guess
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
            cover_names = ["book_cover", "cover", "front_cover", "bookfront", "book", "cover_reference"]
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

    # Prepare header icon image (prefer hero path, fallback to first activity image)
    header_icon_img = None
    try:
        if hero_path_str:
            _im = Image.open(hero_path_str)
            header_icon_img = _im.convert("RGBA") if _im.mode != "RGBA" else _im
    except Exception:
        header_icon_img = None
    if header_icon_img is None and items:
        try:
            header_icon_img = items[0][1]
        except Exception:
            header_icon_img = None

    cover = generate_teacher_cover_page(
        theme_name=theme_name,
        pack_code=pack_code,
        product_name="Inferencing Cards",
        page_count=page_count,
        level_count=None,
        hero_image=header_icon_img,
        hero_image_path=hero_path_str,
        book_cover_path=book_cover_path_str,
        draw_footer=True,
        whats_included=[
            "2 practice sets",
            "Symbol-supported prompts",
            "Colour + black & white versions",
        ],
        also_included=[
            "Quick Start Guide",
            "Terms of Use",
            "B&W version",
        ],
        top_tips=[
            "Use clues in images to infer answers.",
            "Model think-aloud strategies.",
            "Fade prompts as independence grows.",
        ],
        rope_strand="Language Comprehension",
        rope_skills="Oral Language · Inference · Evidence",
        render_chips=False,
    )
    # header_icon_img already prepared above (with fallback)

    # Prepare items for two pages (2 boxes per page)
    items_page1 = items[:2]
    items_page2 = items[2:4]
    pages_content = [
        _draw_inferencing_cards_page(theme_name=theme_name, pack_code=pack_code, page_num=2, total_pages=total_pages, index=1, items=items_page1, header_left_icon=header_icon_img),
        _draw_inferencing_cards_page(theme_name=theme_name, pack_code=pack_code, page_num=3, total_pages=total_pages, index=2, items=items_page2, header_left_icon=header_icon_img),
    ]
    pages_color = [cover] + pages_content

    # COLOR
    color_pdf = output_dir / f"{pack_code}_Inferencing_Cards_COLOR.pdf"
    c = canvas.Canvas(str(color_pdf), pagesize=letter)
    for p in pages_color:
        buf = io.BytesIO()
        p.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    c.save()

    # BW
    bw_pdf = output_dir / f"{pack_code}_Inferencing_Cards_BW.pdf"
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
    preview_pdf = output_dir / f"{pack_code}_Inferencing_Cards_PREVIEW.pdf"
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
            th.save(thumbs_dir / f"{pack_code}_Inferencing_Cards_thumb{i}.png", "PNG")
    except Exception:
        pass

    # BuildResult
    try:
        thumbs = [str(p) for p in sorted((output_dir / "thumbnails").glob(f"{pack_code}_Inferencing_Cards_thumb*.png"))]
        warnings = []
        try:
            warnings = assess_files(
                product_name="Inferencing Cards",
                color_pdf=str(color_pdf),
                bw_pdf=str(bw_pdf),
                preview_pdf=str(preview_pdf),
                expected_pages=None,
            )
        except Exception:
            warnings = []
        manifest = {
            "product_name": "Inferencing Cards",
            "slug": images_path.parent.name,
            "pack_code": pack_code,
            "page_count": len(pages_color),
            "files": {
                "color_pdf": str(color_pdf),
                "bw_pdf": str(bw_pdf),
                "preview_pdf": str(preview_pdf),
                "thumbnails": thumbs,
            },
            "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": warnings},
        }
        (output_dir / f"{pack_code}_Inferencing_Cards_BuildResult.json").write_text(
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
    """
    repo_root = Path(__file__).resolve().parents[2]
    for folder in ("activity_images", "icons"):
        images_folder = repo_root / "assets" / "themes" / slug / folder
        if images_folder.exists():
            return generate_inferencing_cards_pack(str(images_folder), pack_code=pack_code, theme_name=book_title)
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
        print("Usage: python INFERENCING_CARDS.py <PACK_CODE> \"Theme Name\"")
        sys.exit(1)
    images_folder = os.path.join(os.getcwd(), "images")
    ok = generate_inferencing_cards_pack(images_folder, pack_code, theme_name)
    sys.exit(0 if ok else 1)
