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

from utils.sws_design import apply_small_wins_frame, generate_internal_cover_page, generate_teacher_cover_page, shrink_font_to_fit_with_pt, hex_to_rgb, NAVY_HEX, DPI
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


def _draw_syllable_cards_page(*, theme_name: str, pack_code: str, page_num: int, total_pages: int, index: int) -> Image.Image:
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
    )
    d = ImageDraw.Draw(page)
    instr = f"Clap the syllables: Set {index}"
    usable_w = int(w * 0.80)
    font, pt = shrink_font_to_fit_with_pt(instr, base_pt=20, max_width_px=usable_w, bold=True, brand="poppins", min_pt=12)
    tw, th = d.textbbox((0, 0), instr, font=font)[2:4]
    d.text(((w - tw) // 2, int(1.7 * DPI)), instr, fill=hex_to_rgb(NAVY_HEX), font=font)
    # Four card boxes per page (2x2)
    margin = int(0.8 * DPI)
    gap = int(0.35 * DPI)
    box_w = (w - (2 * margin) - gap) // 2
    box_h = int((h - int(3.2 * DPI) - margin - gap) / 2)
    x0 = margin
    y0 = int(2.2 * DPI)
    for r in range(2):
        for c in range(2):
            bx0 = x0 + c * (box_w + gap)
            by0 = y0 + r * (box_h + gap)
            d.rectangle([bx0, by0, bx0 + box_w, by0 + box_h], outline=(0, 0, 0), width=int(2 * (DPI / 72)))
    return page


def generate_syllable_cards_pack(images_folder: str, pack_code: str = "SYL01", theme_name: str = "Theme") -> bool:
    try:
        _validate_images_folder(images_folder)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    items = _read_icons(images_folder)
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
        images_path = Path(images_folder).resolve()
        slug_guess = images_path.parent.name if images_path.parent.name else None
        if slug_guess:
            tdir = Path(__file__).resolve().parents[1] / "assets" / "themes" / slug_guess
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

    cover = generate_teacher_cover_page(
        theme_name=theme_name,
        pack_code=pack_code,
        product_name="Syllable Cards",
        page_count=page_count,
        level_count=None,
        hero_image=None,
        hero_image_path=hero_path_str,
        book_cover_path=book_cover_path_str,
        draw_footer=False,
        whats_included=[
            "2 practice pages",
            "Symbol-supported prompts",
            "Colour + black & white versions",
        ],
        also_included=[
            "Quick Start Guide",
            "Terms of Use",
            "B&W version",
        ],
        top_tips=[
            "Clap and count syllables together.",
            "Use picture cues to support decoding.",
            "Mix easy and harder words for challenge.",
        ],
        rope_strand="Word Recognition",
        rope_skills="Decoding · Sight Words · Orthographic Mapping",
        render_chips=False,
    )
    pages_content = [
        _draw_syllable_cards_page(theme_name=theme_name, pack_code=pack_code, page_num=2, total_pages=total_pages, index=1),
        _draw_syllable_cards_page(theme_name=theme_name, pack_code=pack_code, page_num=3, total_pages=total_pages, index=2),
    ]
    pages_color = [cover] + pages_content

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
            "product_name": "Syllable Cards",
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
    for folder in ("activity_images", "icons_colored", "icons"):
        images_folder = repo_root / "assets" / "themes" / slug / folder
        if images_folder.exists():
            return generate_syllable_cards_pack(str(images_folder), pack_code=pack_code, theme_name=book_title)
    print(f"❌ No image folder found for slug '{slug}' (checked activity_images/icons_colored/icons)")
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
