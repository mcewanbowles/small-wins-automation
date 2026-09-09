from __future__ import annotations

import hashlib
import io
import json
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from utils.UNIVERSAL_STANDARDS import COPYRIGHT_YEAR, SWS_GOLD, SWS_NAVY, SWS_TEAL, SWS_TEAL_LT
from utils.sws_design import DPI, _brand_font_pt, apply_small_wins_frame, generate_internal_cover_page, generate_teacher_cover_page, hex_to_rgb, shrink_font_to_fit_with_pt

PAGE_W_PT, PAGE_H_PT = letter
PAGE_W = int(PAGE_W_PT * DPI / 72)
PAGE_H = int(PAGE_H_PT * DPI / 72)
WHITE = "#FFFFFF"
TEXT = "#334E68"
PALE_GOLD = "#FFF8DF"


def _theme_dir(images_folder: str) -> Path:
    path = Path(images_folder)
    if path.name == "icons" and path.parent.name == ".sf_build":
        return path.parent.parent
    return path.parent


def _font(pt: int, bold: bool = False):
    return _brand_font_pt(pt, bold=bold, brand="poppins" if bold else "nunito")


def _fit(text: str, pt: int, width: int, minimum: int = 12, bold: bool = True):
    return shrink_font_to_fit_with_pt(text, base_pt=pt, max_width_px=width, bold=bold, brand="poppins" if bold else "nunito", min_pt=minimum)


def _center(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font, fill):
    bounds = draw.textbbox((0, 0), text, font=font)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    x1, y1, x2, y2 = box
    draw.text((x1 + (x2 - x1 - width) // 2 - bounds[0], y1 + (y2 - y1 - height) // 2 - bounds[1]), text, font=font, fill=fill)


def _validate(data: dict) -> list[str]:
    errors = []
    sets = data.get("sets")
    if not isinstance(sets, list) or not sets:
        errors.append("At least one decoding set is required")
    for set_index, group in enumerate(sets or [], start=1):
        words = group.get("words") if isinstance(group, dict) else None
        if not isinstance(words, list) or not words:
            errors.append(f"Set {set_index} has no words")
            continue
        for entry in words:
            word = str(entry.get("word") or "").strip().lower()
            graphemes = entry.get("graphemes") or []
            if not word or len(graphemes) < 2 or "".join(str(value) for value in graphemes).lower() != word:
                errors.append(f"Invalid grapheme mapping in set {set_index}: {word or '(blank)'}")
    if data.get("reading_rope") != ["Decoding"]:
        errors.append("Reading Rope claim must be exactly Decoding")
    return errors


ROW_HEIGHT = 660
ROW_SPACING = 720
ROW_TOPS = [700, 700 + ROW_SPACING, 700 + 2 * ROW_SPACING]


def _word_row(page: Image.Image, draw: ImageDraw.ImageDraw, entry: dict, top: int, row_number: int):
    left = 190
    right = PAGE_W - 190
    bottom = top + ROW_HEIGHT
    draw.rounded_rectangle((left, top, right, bottom), radius=34, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_TEAL), width=5)
    chip = (left + 34, top + 30, left + 118, top + 114)
    draw.ellipse(chip, fill=hex_to_rgb(SWS_NAVY))
    _center(draw, chip, str(row_number), _font(12, True), hex_to_rgb(WHITE))
    prompt = "Say each sound. Blend the word. Write it."
    prompt_font, _ = _fit(prompt, 14, right - left - 220, 11)
    _center(draw, (left + 140, top + 26, right - 35, top + 118), prompt, prompt_font, hex_to_rgb(SWS_NAVY))

    graphemes = [str(value) for value in entry["graphemes"]]
    tile_size = 200
    gap = 50
    total_width = len(graphemes) * tile_size + (len(graphemes) - 1) * gap
    tile_x = left + (right - left - total_width) // 2
    tile_y = top + 160
    colors = [SWS_TEAL_LT, PALE_GOLD, SWS_TEAL_LT]
    for index, grapheme in enumerate(graphemes):
        box = (tile_x, tile_y, tile_x + tile_size, tile_y + tile_size)
        draw.rounded_rectangle(box, radius=30, fill=hex_to_rgb(colors[index % len(colors)]), outline=hex_to_rgb(SWS_NAVY), width=5)
        letter_font, _ = _fit(grapheme, 40, tile_size - 50, 22)
        _center(draw, box, grapheme, letter_font, hex_to_rgb(SWS_NAVY))
        tile_x += tile_size + gap

    word = str(entry["word"]).lower()
    blend_box = (left + 260, top + 400, right - 260, top + 515)
    draw.rounded_rectangle(blend_box, radius=38, fill=hex_to_rgb(SWS_TEAL), outline=hex_to_rgb(SWS_TEAL), width=4)
    word_font, _ = _fit(word, 32, blend_box[2] - blend_box[0] - 50, 20)
    _center(draw, blend_box, word, word_font, hex_to_rgb(WHITE))
    line_y = top + 590
    draw.line((left + 320, line_y, right - 320, line_y), fill=hex_to_rgb(SWS_NAVY), width=4)


def _cover_page(theme_name: str, pack_code: str, total_pages: int) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), hex_to_rgb("#F8FCFC"))
    apply_small_wins_frame(page, product_title="CVC Decode & Build", subtitle=theme_name, pack_code=pack_code, page_num=1, total_pages=total_pages, level=None)
    draw = ImageDraw.Draw(page)
    title_box = (240, 650, PAGE_W - 240, 900)
    _center(draw, title_box, "Sound it. Blend it. Build it.", _fit("Sound it. Blend it. Build it.", 28, PAGE_W - 650, 18)[0], hex_to_rgb(SWS_NAVY))
    tile_size = 380
    gap = 120
    total_width = tile_size * 3 + gap * 2
    x = (PAGE_W - total_width) // 2
    for letter, fill in zip(("b", "e", "d"), (SWS_TEAL_LT, PALE_GOLD, SWS_TEAL_LT)):
        box = (x, 1120, x + tile_size, 1500)
        draw.rounded_rectangle(box, radius=46, fill=hex_to_rgb(fill), outline=hex_to_rgb(SWS_NAVY), width=6)
        _center(draw, box, letter, _font(52, True), hex_to_rgb(SWS_NAVY))
        x += tile_size + gap
    word_box = (650, 1700, PAGE_W - 650, 1900)
    draw.rounded_rectangle(word_box, radius=50, fill=hex_to_rgb(SWS_TEAL), outline=hex_to_rgb(SWS_TEAL), width=4)
    _center(draw, word_box, "bed", _font(38, True), hex_to_rgb(WHITE))
    steps = [("1", "Say each sound"), ("2", "Blend the word"), ("3", "Build or write")]
    y = 2200
    for number, text in steps:
        circle = (520, y, 650, y + 130)
        draw.ellipse(circle, fill=hex_to_rgb(SWS_NAVY))
        _center(draw, circle, number, _font(12, True), hex_to_rgb(WHITE))
        draw.text((730, y + 30), text, font=_font(16, True), fill=hex_to_rgb(TEXT))
        y += 220
    return page


def _activity_page(theme_name: str, pack_code: str, group: dict, page_num: int, total_pages: int, header_left_icon: Image.Image | None = None) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), hex_to_rgb("#F8FCFC"))
    apply_small_wins_frame(page, product_title="CVC Decode & Build", subtitle=theme_name, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=None, header_left_icon=header_left_icon)
    draw = ImageDraw.Draw(page)
    label = str(group.get("label") or "Decode and blend")
    label_font, _ = _fit(label, 22, PAGE_W - 560, 14)
    _center(draw, (180, 430, PAGE_W - 540, 600), label, label_font, hex_to_rgb(SWS_NAVY))
    pattern = str(group.get("pattern") or "CVC")
    pattern_box = (PAGE_W - 520, 455, PAGE_W - 210, 575)
    draw.rounded_rectangle(pattern_box, radius=36, fill=hex_to_rgb(PALE_GOLD), outline=hex_to_rgb(SWS_GOLD), width=4)
    _center(draw, pattern_box, pattern, _font(13, True), hex_to_rgb(SWS_NAVY))
    words = list(group.get("words") or [])[:3]
    for index, entry in enumerate(words):
        _word_row(page, draw, entry, ROW_TOPS[index], index + 1)
    return page


def _answer_page(theme_name: str, pack_code: str, groups: list[dict], page_num: int, total_pages: int, header_left_icon: Image.Image | None = None) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), hex_to_rgb("#F8FCFC"))
    apply_small_wins_frame(page, product_title="CVC Decode & Build", subtitle="Teacher check", pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=None, header_left_icon=header_left_icon)
    draw = ImageDraw.Draw(page)
    title_font, _ = _fit("Word and grapheme check", 25, PAGE_W - 400, 16)
    _center(draw, (180, 460, PAGE_W - 180, 620), "Word and grapheme check", title_font, hex_to_rgb(SWS_NAVY))
    top = 730
    for group in groups:
        box = (190, top, PAGE_W - 190, top + 390)
        draw.rounded_rectangle(box, radius=34, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_TEAL), width=4)
        label = str(group.get("label") or "Set")
        label_font, _ = _fit(label, 17, 650, 12)
        draw.text((245, top + 55), label, font=label_font, fill=hex_to_rgb(SWS_NAVY))
        words = [str(entry["word"]) for entry in group.get("words") or []]
        mappings = [" – ".join(str(value) for value in entry["graphemes"]) for entry in group.get("words") or []]
        value = "   |   ".join(f"{word}: {mapping}" for word, mapping in zip(words, mappings))
        value_font, _ = _fit(value, 15, PAGE_W - 540, 10, False)
        draw.text((245, top + 185), value, font=value_font, fill=hex_to_rgb(TEXT))
        top += 445
    return page


def _save_pdf(path: Path, pages: list[Image.Image], preview: bool = False):
    pdf = canvas.Canvas(str(path), pagesize=letter)
    for page in pages:
        buffer = io.BytesIO()
        page.save(buffer, "PNG", dpi=(DPI, DPI))
        buffer.seek(0)
        pdf.drawImage(ImageReader(buffer), 0, 0, width=PAGE_W_PT, height=PAGE_H_PT)
        if preview:
            pdf.saveState()
            pdf.setFont("Helvetica-Bold", 90)
            try:
                pdf.setFillColorRGB(0.45, 0.45, 0.45, alpha=0.25)
            except Exception:
                pdf.setFillColorRGB(0.7, 0.7, 0.7)
            pdf.translate(PAGE_W_PT / 2, PAGE_H_PT / 2)
            pdf.rotate(42)
            pdf.drawCentredString(0, 0, "PREVIEW")
            pdf.restoreState()
        pdf.showPage()
    pdf.save()


def generate_decoding_pack(images_folder: str, pack_code: str = "DEC01", theme_name: str = "Theme") -> bool:
    # Ensure title is title-cased (fixes lowercase slug leaking through)
    if theme_name and theme_name == theme_name.lower():
        theme_name = theme_name.title()
    theme_dir = _theme_dir(images_folder)
    source = theme_dir / "config" / "decoding.json"
    if not source.exists():
        print(f"ERROR: Missing reviewed decoding config: {source}")
        return False
    data = json.loads(source.read_text(encoding="utf-8"))
    errors = _validate(data)
    if errors:
        print("ERROR: " + "; ".join(errors))
        return False
    output_dir = theme_dir / "OUTPUT"
    output_dir.mkdir(parents=True, exist_ok=True)
    groups = list(data["sets"])
    total_pages = len(groups) + 1
    # Resolve hero/book cover for teacher cover and header accent icon
    hero_path_str = None
    book_cover_path_str = None
    hero_icon_img: Image.Image | None = None
    try:
        for hp in [theme_dir / "hero.png", theme_dir / "hero_header.png"]:
            if hp.exists():
                hero_path_str = str(hp)
                break
        for bc in [theme_dir / "book_cover.png", theme_dir / "config" / "book_image.png"]:
            if bc.exists():
                book_cover_path_str = str(bc)
                break
        if hero_path_str:
            im = Image.open(hero_path_str)
            hero_icon_img = im.convert("RGBA") if im.mode != "RGBA" else im
    except Exception:
        pass
    pages = [_activity_page(theme_name, pack_code, group, index + 1, total_pages, header_left_icon=hero_icon_img) for index, group in enumerate(groups)]
    pages.append(_answer_page(theme_name, pack_code, groups, total_pages, total_pages, header_left_icon=hero_icon_img))
    color_pdf = output_dir / f"{pack_code}_Decoding_COLOR.pdf"
    bw_pdf = output_dir / f"{pack_code}_Decoding_BW.pdf"
    preview_pdf = output_dir / f"{pack_code}_Decoding_PREVIEW.pdf"
    _save_pdf(color_pdf, pages)
    _save_pdf(bw_pdf, [page.convert("L").convert("RGB") for page in pages])
    _save_pdf(preview_pdf, pages[: min(3, len(pages))], preview=True)
    thumbs_dir = output_dir / "thumbnails"
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    thumbnails = []
    for index, page in enumerate(pages[:2], start=1):
        thumb = page.copy()
        thumb.thumbnail((500, 647), Image.Resampling.LANCZOS)
        thumb_path = thumbs_dir / f"{pack_code}_Decoding_thumb{index}.png"
        thumb.save(thumb_path, "PNG")
        thumbnails.append(str(thumb_path))
    manifest = {
        "schema_version": 1,
        "status": "pilot_review",
        "product_name": "CVC Decode & Build",
        "slug": theme_dir.name,
        "pack_code": pack_code,
        "page_count": len(pages),
        "reading_rope": ["Decoding"],
        "teacher_review_required": bool(data.get("teacher_review_required", True)),
        "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "files": {"color_pdf": str(color_pdf), "bw_pdf": str(bw_pdf), "preview_pdf": str(preview_pdf), "thumbnails": thumbnails},
        "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": []},
    }
    (output_dir / f"{pack_code}_Decoding_BuildResult.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated: {color_pdf}")
    return True
