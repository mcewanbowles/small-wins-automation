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

from utils.UNIVERSAL_STANDARDS import SWS_GOLD, SWS_NAVY, SWS_TEAL, SWS_TEAL_LT
from utils.sws_design import DPI, _brand_font_pt, apply_small_wins_frame, generate_internal_cover_page, hex_to_rgb, shrink_font_to_fit_with_pt

PAGE_W_PT, PAGE_H_PT = letter
PAGE_W = int(PAGE_W_PT * DPI / 72)
PAGE_H = int(PAGE_H_PT * DPI / 72)
WHITE = "#FFFFFF"
TEXT = "#334E68"
PALE_GOLD = "#FFF8DF"


def _theme_dir(images_folder: str) -> Path:
    path = Path(images_folder).resolve()
    if path.name == "icons" and path.parent.name == ".sf_build":
        return path.parent.parent
    return path.parent


def _font(pt: int, bold: bool = False):
    return _brand_font_pt(pt, bold=bold, brand="poppins" if bold else "nunito")


def _fit(text: str, pt: int, width: int, minimum: int = 9, bold: bool = True):
    return shrink_font_to_fit_with_pt(text, base_pt=pt, max_width_px=width, bold=bold, brand="poppins" if bold else "nunito", min_pt=minimum)[0]


def _center(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font, fill):
    bounds = draw.textbbox((0, 0), text, font=font)
    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    x1, y1, x2, y2 = box
    draw.text((x1 + (x2 - x1 - width) // 2 - bounds[0], y1 + (y2 - y1 - height) // 2 - bounds[1]), text, font=font, fill=fill)


def _prepare_icon(image: Image.Image) -> Image.Image:
    icon = image.convert("RGBA")
    pixels = []
    source = icon.get_flattened_data() if hasattr(icon, "get_flattened_data") else icon.getdata()
    for red, green, blue, alpha in source:
        neutral = max(red, green, blue) - min(red, green, blue) < 12 and (red + green + blue) / 3 > 150
        pixels.append((red, green, blue, 0 if neutral else alpha))
    icon.putdata(pixels)
    bounds = icon.getchannel("A").getbbox()
    return icon.crop(bounds) if bounds else icon


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, width: int, lines: int = 3) -> list[str]:
    result, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if not current or draw.textbbox((0, 0), candidate, font=font)[2] <= width:
            current = candidate
        else:
            result.append(current); current = word
            if len(result) == lines:
                break
    if current and len(result) < lines:
        result.append(current)
    return result


def _center_wrapped(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font, fill, max_lines: int = 3):
    x1, y1, x2, y2 = box
    lines = _wrap(draw, text, font, x2 - x1, max_lines)
    heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
    y = y1 + max(0, (y2 - y1 - sum(heights) - 10 * (len(lines) - 1)) // 2)
    for line, height in zip(lines, heights):
        bounds = draw.textbbox((0, 0), line, font=font)
        width = bounds[2] - bounds[0]
        draw.text((x1 + (x2 - x1 - width) // 2 - bounds[0], y - bounds[1]), line, font=font, fill=fill)
        y += height + 10


def _reasoning_page(theme_name: str, pack_code: str, card: dict, icon: Image.Image, page_num: int, total_pages: int) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    apply_small_wins_frame(page, product_title="Clue - Think - Infer", subtitle=theme_name, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=None, draw_footer=True, draw_subtitle=True)
    draw = ImageDraw.Draw(page)
    question_box = (180, 500, PAGE_W - 180, 760)
    draw.rounded_rectangle(question_box, radius=42, fill=hex_to_rgb(SWS_TEAL), outline=hex_to_rgb(SWS_TEAL), width=4)
    _center_wrapped(draw, (260, 520, PAGE_W - 260, 740), card["question"], _fit(card["question"], 20, PAGE_W - 600, 12), hex_to_rgb(WHITE), 2)
    clue_box = (180, 850, 1020, 1900)
    draw.rounded_rectangle(clue_box, radius=42, fill=hex_to_rgb("#F8FCFC"), outline=hex_to_rgb(SWS_GOLD), width=5)
    clue = _prepare_icon(icon)
    if clue.width > 0 and clue.height > 0:
        ratio = min(650 / clue.width, 680 / clue.height)
        clue = clue.resize((max(1, int(clue.width * ratio)), max(1, int(clue.height * ratio))), Image.Resampling.LANCZOS)
    page.paste(clue, (clue_box[0] + (clue_box[2] - clue_box[0] - clue.width) // 2, clue_box[1] + 100), clue)
    _center(draw, (250, 1650, 950, 1820), "1  NOTICE THE CLUE", _font(13, True), hex_to_rgb(SWS_NAVY))
    think_box = (1110, 850, PAGE_W - 180, 1900)
    draw.rounded_rectangle(think_box, radius=42, fill=hex_to_rgb(PALE_GOLD), outline=hex_to_rgb(SWS_GOLD), width=5)
    _center(draw, (1170, 920, PAGE_W - 240, 1080), "2  WHAT DO I KNOW?", _font(14, True), hex_to_rgb(SWS_NAVY))
    choices = card.get("choices") or []
    top = 1160
    for index, choice in enumerate(choices[:2]):
        box = (1210, top, PAGE_W - 280, top + 230)
        draw.rounded_rectangle(box, radius=38, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_TEAL), width=4)
        _center_wrapped(draw, (1260, top + 20, PAGE_W - 330, top + 210), f"{chr(65 + index)}. {choice}", _fit(choice, 13, 780, 10), hex_to_rgb(TEXT), 2)
        top += 300
    infer_box = (180, 2020, PAGE_W - 180, 2800)
    draw.rounded_rectangle(infer_box, radius=42, fill=hex_to_rgb(SWS_TEAL_LT), outline=hex_to_rgb(SWS_TEAL), width=5)
    _center(draw, (250, 2080, PAGE_W - 250, 2240), "3  INFER AND EXPLAIN", _font(15, True), hex_to_rgb(SWS_NAVY))
    _center(draw, (280, 2310, PAGE_W - 280, 2430), "I think __________________ because __________________", _font(13, True), hex_to_rgb(SWS_NAVY))
    for y in (2550, 2700):
        draw.line((360, y, PAGE_W - 360, y), fill=hex_to_rgb(SWS_NAVY), width=3)
    return page


def _guide_page(theme_name: str, pack_code: str, cards: list[dict], page_num: int, total_pages: int) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    apply_small_wins_frame(page, product_title="Inference Discussion Guide", subtitle=theme_name, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=None, draw_footer=True, draw_subtitle=True)
    draw = ImageDraw.Draw(page)
    top = 570
    for index, card in enumerate(cards, start=1):
        box = (200, top, PAGE_W - 200, top + 560)
        draw.rounded_rectangle(box, radius=34, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_TEAL), width=4)
        _center(draw, (250, top + 35, 410, top + 150), str(index), _font(13, True), hex_to_rgb(SWS_NAVY))
        question = _fit(card["question"], 12, PAGE_W - 750, 9)
        _center_wrapped(draw, (450, top + 30, PAGE_W - 260, top + 175), card["question"], question, hex_to_rgb(SWS_NAVY), 2)
        _center_wrapped(draw, (300, top + 210, PAGE_W - 300, top + 500), card["answer_hint"], _font(10), hex_to_rgb(TEXT), 3)
        top += 610
    return page


def _save(path: Path, pages: list[Image.Image], preview: bool = False):
    pdf = canvas.Canvas(str(path), pagesize=letter)
    for page in pages:
        buffer = io.BytesIO(); page.save(buffer, "PNG", dpi=(DPI, DPI)); buffer.seek(0)
        pdf.drawImage(ImageReader(buffer), 0, 0, width=PAGE_W_PT, height=PAGE_H_PT)
        if preview:
            pdf.saveState(); pdf.setFont("Helvetica-Bold", 90)
            try: pdf.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.25)
            except Exception: pdf.setFillColorRGB(0.7, 0.7, 0.7)
            pdf.translate(PAGE_W_PT / 2, PAGE_H_PT / 2); pdf.rotate(42); pdf.drawCentredString(0, 0, "PREVIEW"); pdf.restoreState()
        pdf.showPage()
    pdf.save()


def generate_inferencing_reasoning_pack(images_folder: str, pack_code: str = "INF", theme_name: str = "Theme") -> bool:
    theme = _theme_dir(images_folder)
    source = theme / "config" / "inferencing.json"
    data = json.loads(source.read_text(encoding="utf-8")) if source.exists() else None
    cards = data.get("cards") if isinstance(data, dict) else None
    if not cards or len(cards) != 4 or data.get("reading_rope") != ["Verbal Reasoning", "Background Knowledge"]:
        print(f"ERROR: Four reviewed inference cards are required: {source}"); return False
    icons = []
    for card in cards:
        path = Path(images_folder) / f"{card.get('clue_image_key')}.png"
        if not path.exists() or not card.get("question") or len(card.get("choices") or []) != 2 or not card.get("answer_hint"):
            print(f"ERROR: Invalid inference card: {card}"); return False
        icons.append(Image.open(path).convert("RGBA"))
    total = 5
    # No cover page — teacher cover is added later during packaging
    pages = [_reasoning_page(theme_name, pack_code, card, icon, index + 1, total) for index, (card, icon) in enumerate(zip(cards, icons))]
    pages.append(_guide_page(theme_name, pack_code, cards, 5, total))
    output = theme / "OUTPUT"; output.mkdir(parents=True, exist_ok=True)
    color = output / f"{pack_code}_Inferencing_COLOR.pdf"; bw = output / f"{pack_code}_Inferencing_BW.pdf"; preview = output / f"{pack_code}_Inferencing_PREVIEW.pdf"
    _save(color, pages); _save(bw, [page.convert("L").convert("RGB") for page in pages]); _save(preview, pages[:3], True)
    thumbs = output / "thumbnails"; thumbs.mkdir(parents=True, exist_ok=True); thumb_paths = []
    for index, page in enumerate((pages[0], pages[4]), start=1):
        thumb = page.copy(); thumb.thumbnail((500, 647), Image.Resampling.LANCZOS); path = thumbs / f"{pack_code}_Inferencing_thumb{index}.png"; thumb.save(path); thumb_paths.append(str(path))
    manifest = {"schema_version": 1, "status": "pilot_review", "product_name": "Clue - Think - Infer", "slug": theme.name, "pack_code": pack_code, "page_count": len(pages), "reading_rope": data["reading_rope"], "teacher_review_required": True, "source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "files": {"color_pdf": str(color), "bw_pdf": str(bw), "preview_pdf": str(preview), "thumbnails": thumb_paths}, "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": []}}
    (output / f"{pack_code}_Inferencing_BuildResult.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return True
