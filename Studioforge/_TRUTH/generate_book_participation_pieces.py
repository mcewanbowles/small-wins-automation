from __future__ import annotations

import hashlib
import io
import json
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from utils.UNIVERSAL_STANDARDS import SWS_GOLD, SWS_NAVY, SWS_TEAL, SWS_TEAL_LT
from utils.sws_design import DPI, _brand_font_pt, apply_small_wins_frame, generate_internal_cover_page, generate_teacher_cover_page, hex_to_rgb, shrink_font_to_fit_with_pt

PAGE_W_PT, PAGE_H_PT = letter
PAGE_W = int(PAGE_W_PT * DPI / 72)
PAGE_H = int(PAGE_H_PT * DPI / 72)
WHITE = "#FFFFFF"
TEXT = "#334E68"


def _theme_dir(images_folder: str) -> Path:
    # Always resolve against the repo root so the theme dir is correct
    # even if the generator is called with a relative path or from a different cwd.
    path = Path(images_folder).resolve()
    if path.name == "icons" and path.parent.name == ".sf_build":
        return path.parent.parent
    return path.parent


def _font(pt: int, bold: bool = False):
    return _brand_font_pt(pt, bold=bold, brand="poppins" if bold else "nunito")


def _fit(text: str, pt: int, width: int, minimum: int = 10, bold: bool = True):
    return shrink_font_to_fit_with_pt(text, base_pt=pt, max_width_px=width, bold=bold, brand="poppins" if bold else "nunito", min_pt=minimum)[0]


def _center(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font, fill):
    bounds = draw.textbbox((0, 0), text, font=font)
    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    x1, y1, x2, y2 = box
    draw.text((x1 + (x2 - x1 - width) // 2 - bounds[0], y1 + (y2 - y1 - height) // 2 - bounds[1]), text, font=font, fill=fill)


def _clean_hero(image: Image.Image) -> Image.Image:
    hero = image.convert("RGBA")
    edge = max(3, int(hero.width * 0.025))
    hero = hero.crop((edge, 0, hero.width - edge, hero.height))
    pixels = []
    for red, green, blue, alpha in hero.getdata():
        pixels.append((red, green, blue, 0 if red >= 244 and green >= 244 and blue >= 244 else alpha))
    hero.putdata(pixels)
    bounds = hero.getchannel("A").getbbox()
    return hero.crop(bounds) if bounds else hero


def _resolve_core(word: str, root: Path) -> Image.Image | None:
    key = re.sub(r"[^a-z0-9]+", "_", word.lower()).strip("_")
    roots = [root / "assets" / "global" / "aac_core", root / "assets" / "symbols" / "png"]
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*.png"):
            stem = re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_")
            if stem == key or stem.startswith(key + "_"):
                try:
                    return Image.open(path).convert("RGBA")
                except Exception:
                    pass
    return None


def _activity_page(title: str, subtitle: str, pack_code: str, page_num: int, total_pages: int, header_left_icon: Image.Image | None = None) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    apply_small_wins_frame(page, product_title=title, subtitle=subtitle, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=None, draw_footer=True, draw_subtitle=True, header_left_icon=header_left_icon)
    return page


def _teacher_page(theme_name: str, pack_code: str, page_num: int, total_pages: int) -> Image.Image:
    page = _activity_page("Book Participation Pieces", f"{theme_name} — Teacher Guide", pack_code, page_num, total_pages)
    draw = ImageDraw.Draw(page)
    cards = [
        ("PURPOSE", "Add flexible visual participation prompts to a separately purchased trade book."),
        ("PREPARE", "Print, laminate and cut. Attach strips beside relevant pages with removable fasteners."),
        ("USE", "Pause during reading. Offer a vocabulary piece, question strip or communication piece."),
        ("ACCESS", "Accept pointing, placing, eye gaze, speech, sign, gesture, typing or AAC."),
        ("IMPORTANT", "Do not cover book text or illustrations. Placement may vary by edition."),
    ]
    top = 590
    for heading, body in cards:
        box = (220, top, PAGE_W - 220, top + 390)
        draw.rounded_rectangle(box, radius=34, fill=hex_to_rgb(SWS_TEAL_LT), outline=hex_to_rgb(SWS_TEAL), width=4)
        draw.text((270, top + 45), heading, font=_font(14, True), fill=hex_to_rgb(SWS_NAVY))
        words = body.split()
        lines, current = [], ""
        font = _font(11)
        for word in words:
            candidate = f"{current} {word}".strip()
            if not current or draw.textbbox((0, 0), candidate, font=font)[2] <= PAGE_W - 620:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        y = top + 145
        for line in lines[:3]:
            draw.text((270, y), line, font=font, fill=hex_to_rgb(TEXT))
            y += 70
        top += 440
    return page


def _vocab_page(theme_name: str, pack_code: str, items: list[tuple[str, Image.Image]], page_num: int, total_pages: int) -> Image.Image:
    page = _activity_page("Book Vocabulary Pieces", theme_name, pack_code, page_num, total_pages)
    draw = ImageDraw.Draw(page)
    positions = [(220, 650), (1325, 650), (220, 1740), (1325, 1740)]
    for (label, image), (x, y) in zip(items, positions):
        box = (x, y, x + 1000, y + 940)
        draw.rounded_rectangle(box, radius=42, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_NAVY), width=5)
        icon = image.copy()
        icon.thumbnail((650, 620), Image.Resampling.LANCZOS)
        page.paste(icon, (x + (1000 - icon.width) // 2, y + 75), icon)
        label_box = (x + 70, y + 735, x + 930, y + 875)
        draw.rounded_rectangle(label_box, radius=34, fill=hex_to_rgb(SWS_TEAL_LT), outline=hex_to_rgb(SWS_TEAL), width=3)
        _center(draw, label_box, label, _fit(label, 18, 780, 12), hex_to_rgb(SWS_NAVY))
    return page


def _question_page(theme_name: str, pack_code: str, questions: list[dict], page_num: int, total_pages: int) -> Image.Image:
    page = _activity_page("Flexible Question Strips", theme_name, pack_code, page_num, total_pages)
    draw = ImageDraw.Draw(page)
    top = 650
    for question in questions:
        box = (180, top, PAGE_W - 180, top + 880)
        draw.rounded_rectangle(box, radius=42, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_NAVY), width=5)
        prompt_box = (240, top + 70, PAGE_W - 240, top + 245)
        draw.rounded_rectangle(prompt_box, radius=42, fill=hex_to_rgb(SWS_TEAL), outline=hex_to_rgb(SWS_TEAL), width=3)
        _center(draw, prompt_box, question["prompt"], _fit(question["prompt"], 20, PAGE_W - 650, 13), hex_to_rgb(WHITE))
        response_box = (430, top + 350, PAGE_W - 430, top + 700)
        draw.rounded_rectangle(response_box, radius=40, fill=hex_to_rgb("#F8FCFC"), outline=hex_to_rgb(SWS_GOLD), width=5)
        _center(draw, response_box, "PLACE OR POINT HERE", _font(12, True), hex_to_rgb(SWS_NAVY))
        _center(draw, (300, top + 720, PAGE_W - 300, top + 825), question["response"], _fit(question["response"], 10, PAGE_W - 700, 8, False), hex_to_rgb(TEXT))
        top += 980
    return page


def _participation_page(theme_name: str, pack_code: str, pieces: list[tuple[str, Image.Image]], page_num: int, total_pages: int) -> Image.Image:
    page = _activity_page("Reading Participation Pieces", theme_name, pack_code, page_num, total_pages)
    draw = ImageDraw.Draw(page)
    cols, rows = 3, 3
    gap = 80
    cell = 620
    grid_w = cols * cell + (cols - 1) * gap
    x0 = (PAGE_W - grid_w) // 2
    y0 = 650
    for index, (label, image) in enumerate(pieces):
        row, col = divmod(index, cols)
        x, y = x0 + col * (cell + gap), y0 + row * (cell + gap)
        box = (x, y, x + cell, y + cell)
        draw.rounded_rectangle(box, radius=38, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_NAVY), width=5)
        icon = image.copy()
        icon.thumbnail((430, 390), Image.Resampling.LANCZOS)
        page.paste(icon, (x + (cell - icon.width) // 2, y + 45), icon)
        _center(draw, (x + 35, y + 465, x + cell - 35, y + 580), label, _fit(label, 13, cell - 100, 9), hex_to_rgb(SWS_NAVY))
    return page


def _early_access_page(theme_name: str, pack_code: str, profile: dict, hero: Image.Image, turn_page: Image.Image, page_num: int, total_pages: int) -> Image.Image:
    page = _activity_page("Hero Match & Turn", f"{theme_name} — Partner-Supported Access", pack_code, page_num, total_pages)
    draw = ImageDraw.Draw(page)
    cue = str(profile.get("cue") or "See the hero. Match the hero. Turn the page.")
    cue_box = (240, 560, PAGE_W - 240, 745)
    draw.rounded_rectangle(cue_box, radius=44, fill=hex_to_rgb(SWS_TEAL), outline=hex_to_rgb(SWS_TEAL), width=4)
    _center(draw, cue_box, cue, _fit(cue, 20, PAGE_W - 650, 12), hex_to_rgb(WHITE))
    step_y = 860
    step_w = 720
    step_h = 650
    step_gap = 180
    step_x = (PAGE_W - (step_w * 2 + step_gap)) // 2
    steps = [("1  MATCH LLAMA", hero), ("2  TURN THE PAGE", turn_page)]
    for index, (label, image) in enumerate(steps):
        x = step_x + index * (step_w + step_gap)
        box = (x, step_y, x + step_w, step_y + step_h)
        draw.rounded_rectangle(box, radius=42, fill=hex_to_rgb("#F8FCFC"), outline=hex_to_rgb(SWS_GOLD), width=5)
        icon = image.copy(); icon.thumbnail((430, 390), Image.Resampling.LANCZOS)
        page.paste(icon, (x + (step_w - icon.width) // 2, step_y + 70), icon)
        _center(draw, (x + 35, step_y + 490, x + step_w - 35, step_y + 610), label, _fit(label, 13, step_w - 100, 9), hex_to_rgb(SWS_NAVY))
    title_box = (300, 1580, PAGE_W - 300, 1710)
    _center(draw, title_box, "CUT-OUT MATCHING PIECES", _font(15, True), hex_to_rgb(SWS_NAVY))
    hero_copies = min(6, max(1, int(profile.get("hero_piece_copies", 6))))
    turn_copies = min(2, max(1, int(profile.get("turn_page_piece_copies", 2))))
    pieces = [(str(profile.get("hero_label") or "Hero"), hero)] * hero_copies + [("turn the page", turn_page)] * turn_copies
    cols = 4
    cell = 450
    gap = 70
    grid_w = cols * cell + (cols - 1) * gap
    x0 = (PAGE_W - grid_w) // 2
    y0 = 1760
    for index, (label, image) in enumerate(pieces[:8]):
        row, col = divmod(index, cols)
        x, y = x0 + col * (cell + gap), y0 + row * (cell + gap)
        box = (x, y, x + cell, y + cell)
        draw.rounded_rectangle(box, radius=34, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_NAVY), width=4)
        icon = image.copy(); icon.thumbnail((300, 280), Image.Resampling.LANCZOS)
        page.paste(icon, (x + (cell - icon.width) // 2, y + 35), icon)
        _center(draw, (x + 20, y + 330, x + cell - 20, y + 420), label, _fit(label, 10, cell - 60, 8), hex_to_rgb(SWS_NAVY))
    return page


def _answer_mat(theme_name: str, pack_code: str, labels: list[str], page_num: int, total_pages: int) -> Image.Image:
    page = _activity_page("Vocabulary Piece Storage Mat", theme_name, pack_code, page_num, total_pages)
    draw = ImageDraw.Draw(page)
    cols, rows = 2, 4
    gap = 65
    cell_w, cell_h = 930, 500
    grid_w = cols * cell_w + gap
    x0 = (PAGE_W - grid_w) // 2
    y0 = 620
    for index, label in enumerate(labels[:8]):
        row, col = divmod(index, cols)
        x, y = x0 + col * (cell_w + gap), y0 + row * (cell_h + gap)
        box = (x, y, x + cell_w, y + cell_h)
        draw.rounded_rectangle(box, radius=38, fill=hex_to_rgb("#F8FCFC"), outline=hex_to_rgb(SWS_TEAL), width=5)
        marker = (x + 65, y + 65, x + 185, y + 185)
        draw.ellipse(marker, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_GOLD), width=4)
        _center(draw, (x + 215, y + 50, x + cell_w - 50, y + 205), label, _fit(label, 17, cell_w - 320, 11), hex_to_rgb(SWS_NAVY))
        _center(draw, (x + 100, y + 245, x + cell_w - 100, y + 420), "PARK PIECE HERE", _font(10, True), hex_to_rgb(TEXT))
    return page


def _save_pdf(path: Path, pages: list[Image.Image], preview: bool = False):
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


def generate_book_participation_pack(images_folder: str, pack_code: str = "BPP", theme_name: str = "Theme") -> bool:
    theme_dir = _theme_dir(images_folder)
    source = theme_dir / "config" / "book_participation_pieces.json"
    data = json.loads(source.read_text(encoding="utf-8")) if source.exists() else None
    if not data or data.get("status") != "pilot_review" or not data.get("edition_neutral"):
        print(f"ERROR: Missing reviewed edition-neutral config: {source}"); return False
    vocab = []
    for entry in data.get("vocabulary") or []:
        path = Path(images_folder) / f"{entry.get('image_key')}.png"
        if entry.get("review_status") != "approved" or not path.exists():
            print(f"ERROR: Unapproved or missing vocabulary icon: {entry.get('image_key')}"); return False
        vocab.append((str(entry["label"]), Image.open(path).convert("RGBA")))
    root = Path(__file__).resolve().parents[2]
    participation = []
    for word in data.get("participation_words") or []:
        image = _resolve_core(word, root)
        if image is None:
            print(f"ERROR: Missing participation symbol: {word}"); return False
        participation.append((word.replace("_", " "), image))
    early_access = data.get("early_access") or {}
    hero_key = str(early_access.get("hero_image_key") or "").strip()
    hero_path = theme_dir / f"{hero_key}.png"
    if not hero_path.exists():
        hero_path = Path(images_folder) / f"{hero_key}.png"
    turn_page = next((image for label, image in participation if label == "turn the page"), None)
    if not early_access.get("enabled") or not hero_path.exists() or turn_page is None:
        print("ERROR: Enabled early-access profile requires hero and turn-the-page icons"); return False
    hero = _clean_hero(Image.open(hero_path))
    total_pages = 8
    pages = []
    pages.append(_teacher_page(theme_name, pack_code, 1, total_pages))
    pages.append(_vocab_page(theme_name, pack_code, vocab[:4], 2, total_pages))
    pages.append(_vocab_page(theme_name, pack_code, vocab[4:8], 3, total_pages))
    questions = list(data.get("question_strips") or [])
    pages.append(_question_page(theme_name, pack_code, questions[:2], 4, total_pages))
    pages.append(_question_page(theme_name, pack_code, questions[2:4], 5, total_pages))
    pages.append(_early_access_page(theme_name, pack_code, early_access, hero, turn_page, 6, total_pages))
    pages.append(_participation_page(theme_name, pack_code, participation, 7, total_pages))
    pages.append(_answer_mat(theme_name, pack_code, [label for label, _image in vocab], 8, total_pages))
    output = theme_dir / "OUTPUT"; output.mkdir(parents=True, exist_ok=True)
    color = output / f"{pack_code}_BookParticipation_COLOR.pdf"; bw = output / f"{pack_code}_BookParticipation_BW.pdf"; preview = output / f"{pack_code}_BookParticipation_PREVIEW.pdf"
    _save_pdf(color, pages); _save_pdf(bw, [page.convert("L").convert("RGB") for page in pages]); _save_pdf(preview, pages[:4], True)
    thumbs = output / "thumbnails"; thumbs.mkdir(parents=True, exist_ok=True); thumb_paths = []
    for index, page in enumerate((pages[1], pages[3], pages[5], pages[6], pages[7]), start=1):
        thumb = page.copy(); thumb.thumbnail((500, 647), Image.Resampling.LANCZOS); path = thumbs / f"{pack_code}_BookParticipation_thumb{index}.png"; thumb.save(path); thumb_paths.append(str(path))
    manifest = {"schema_version": 1, "status": "pilot_review", "product_name": "Interactive Book Participation Pieces", "slug": theme_dir.name, "pack_code": pack_code, "page_count": len(pages), "edition_neutral": True, "source_book_required": True, "early_access": {"hero_match": True, "turn_the_page": True}, "reading_rope": data["reading_rope"], "source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "files": {"color_pdf": str(color), "bw_pdf": str(bw), "preview_pdf": str(preview), "thumbnails": thumb_paths}, "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": []}}
    (output / f"{pack_code}_BookParticipation_BuildResult.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return True
