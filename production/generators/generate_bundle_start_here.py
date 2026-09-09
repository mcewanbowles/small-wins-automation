from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

from production.generators.generate_book_participation_pieces import _activity_page, _center, _fit, _font, _save_pdf
from utils.UNIVERSAL_STANDARDS import SWS_GOLD, SWS_NAVY, SWS_TEAL, SWS_TEAL_LT
from utils.sws_design import (
    DPI,
    apply_small_wins_frame,
    generate_internal_cover_page,
    generate_teacher_cover_page,
    hex_to_rgb,
)

PAGE_W = int(612 * DPI / 72)
PAGE_H = int(792 * DPI / 72)
WHITE = "#FFFFFF"
TEXT = "#334E68"


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, width: int, max_lines: int = 3) -> list[str]:
    lines, current = [], ""
    for word in str(text).split():
        candidate = f"{current} {word}".strip()
        if not current or draw.textbbox((0, 0), candidate, font=font)[2] <= width:
            current = candidate
        else:
            lines.append(current); current = word
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines


def _text(draw: ImageDraw.ImageDraw, text: str, box: tuple[int, int, int, int], pt: int = 11, bold: bool = False, max_lines: int = 3):
    font = _font(pt, bold)
    lines = _wrap(draw, text, font, box[2] - box[0], max_lines)
    y = box[1]
    for line in lines:
        draw.text((box[0], y), line, font=font, fill=hex_to_rgb(SWS_NAVY if bold else TEXT))
        y += draw.textbbox((0, 0), line, font=font)[3] + 10


def _page(title: str, subtitle: str, pack_code: str, page_num: int, total: int, hero_img: Image.Image | None = None) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    page = _activity_page(title, subtitle, pack_code, page_num, total, header_left_icon=hero_img)
    return page, ImageDraw.Draw(page)


def _bundle_cover(data: dict, pack_code: str, total: int, hero_img: Image.Image | None, hero_image_path: str | None, book_cover_path: str | None) -> Image.Image:
    top_tips = [
        "Choose an access pathway",
        "Select only relevant activities",
        "Review answer support before teaching",
    ]
    return generate_teacher_cover_page(
        theme_name=data.get("title", "Bundle Start Here"),
        product_name="Bundle Start Here",
        pack_code=pack_code,
        page_count=total,
        hero_image=hero_img,
        hero_image_path=hero_image_path,
        book_cover_path=book_cover_path,
        top_tips=top_tips,
        draw_footer=True,
    )


def _contents(data: dict, pack_code: str, page_num: int, total: int, hero_img: Image.Image | None = None) -> Image.Image:
    page, draw = _page("Bundle Start Here", "What is included", pack_code, page_num, total, hero_img)
    groups = {}
    for product in data["products"]:
        groups.setdefault(product["group"], []).append(product["name"])
    items = list(groups.items())
    cols = 2
    gap_x = 90
    card_w = (PAGE_W - 440 - gap_x) // cols
    card_h = 310
    for index, (group, products) in enumerate(items):
        row, col = divmod(index, cols)
        x = 220 + col * (card_w + gap_x)
        y = 540 + row * 355
        box = (x, y, x + card_w, y + card_h)
        draw.rounded_rectangle(box, radius=34, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_TEAL), width=4)
        _text(draw, group.upper(), (x + 45, y + 35, x + card_w - 45, y + 125), 10, True, 2)
        _text(draw, " · ".join(products), (x + 45, y + 145, x + card_w - 45, y + 270), 9, False, 3)
    return page


def _prep(data: dict, pack_code: str, page_num: int, total: int, hero_img: Image.Image | None = None) -> Image.Image:
    page, draw = _page("Bundle Start Here", "Preparation map", pack_code, page_num, total, hero_img)
    top = 520
    for index, product in enumerate(data["products"]):
        y = top + index * 175
        fill = SWS_TEAL_LT if index % 2 == 0 else WHITE
        draw.rounded_rectangle((180, y, PAGE_W - 180, y + 145), radius=24, fill=hex_to_rgb(fill), outline=hex_to_rgb(SWS_TEAL), width=2)
        _text(draw, product["name"], (230, y + 35, 1150, y + 120), 9, True, 1)
        _text(draw, product["prep"], (1200, y + 35, PAGE_W - 230, y + 120), 9, False, 1)
    return page


def _five_day(data: dict, pack_code: str, page_num: int, total: int, hero_img: Image.Image | None = None) -> Image.Image:
    page, draw = _page("Bundle Start Here", "Suggested five-day sequence", pack_code, page_num, total, hero_img)
    top = 580
    colors = [SWS_TEAL, SWS_GOLD, SWS_NAVY, SWS_TEAL, SWS_GOLD]
    for index, day in enumerate(data["five_day_sequence"]):
        box = (210, top, PAGE_W - 210, top + 440)
        draw.rounded_rectangle(box, radius=38, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(colors[index]), width=5)
        day_box = (260, top + 55, 610, top + 200)
        draw.rounded_rectangle(day_box, radius=36, fill=hex_to_rgb(colors[index]), outline=hex_to_rgb(colors[index]), width=3)
        _center(draw, day_box, day["day"], _font(13, True), hex_to_rgb(WHITE))
        _text(draw, day["focus"], (700, top + 55, PAGE_W - 280, top + 190), 14, True, 2)
        _text(draw, "Use: " + " · ".join(day["products"]), (300, top + 255, PAGE_W - 300, top + 390), 11, False, 2)
        top += 490
    return page


def _access(pack_code: str, page_num: int, total: int, hero_img: Image.Image | None = None) -> Image.Image:
    page, draw = _page("Bundle Start Here", "Choose an access pathway", pack_code, page_num, total, hero_img)
    pathways = [
        ("PARTNER-SUPPORTED", "AAC Board, hero-match pieces, one response choice, modelling and extended processing time."),
        ("SUPPORTED", "Picture matching, Level 1 Bingo, guided sorting, visual Yes/No and sentence models."),
        ("DEVELOPING", "Syllables, sequencing with labels, Word Search Levels 1–2 and supported inferencing choices."),
        ("INDEPENDENT", "CVC decoding, open sorting, text-only Word Search, retell writing and inference explanations."),
    ]
    top = 650
    for heading, body in pathways:
        box = (230, top, PAGE_W - 230, top + 520)
        draw.rounded_rectangle(box, radius=40, fill=hex_to_rgb(SWS_TEAL_LT), outline=hex_to_rgb(SWS_TEAL), width=4)
        _text(draw, heading, (300, top + 65, PAGE_W - 300, top + 180), 14, True, 1)
        _text(draw, body, (300, top + 220, PAGE_W - 300, top + 450), 11, False, 3)
        top += 580
    return page


def _rope(data: dict, pack_code: str, page_num: int, total: int, hero_img: Image.Image | None = None) -> Image.Image:
    page, draw = _page("Bundle Start Here", "Reading Rope coverage", pack_code, page_num, total, hero_img)
    sections = [
        ("STRONGLY REPRESENTED", data["reading_rope"]["strong"], SWS_TEAL),
        ("DEVELOPING COVERAGE", data["reading_rope"]["developing"], SWS_GOLD),
        ("NOT CLAIMED BY THIS BUNDLE", data["reading_rope"]["not_claimed"], SWS_NAVY),
    ]
    top = 700
    for heading, values, color in sections:
        box = (230, top, PAGE_W - 230, top + 650)
        draw.rounded_rectangle(box, radius=40, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(color), width=5)
        _text(draw, heading, (310, top + 70, PAGE_W - 310, top + 190), 14, True, 1)
        _text(draw, " · ".join(values), (310, top + 250, PAGE_W - 310, top + 540), 12, False, 4)
        top += 730
    return page


def _support(pack_code: str, page_num: int, total: int, hero_img: Image.Image | None = None) -> Image.Image:
    page, draw = _page("Bundle Start Here", "Answers, files and important notes", pack_code, page_num, total, hero_img)
    sections = [
        ("ANSWER SUPPORT", "Word Search, guided Sorting, CVC and Yes/No include teacher checks or answer keys. Open sorts and inference responses may have more than one defensible answer."),
        ("PRINTING", "Use actual size or 100%. Enable automatic portrait/landscape rotation. Print only the selected differentiation level when appropriate."),
        ("SOURCE BOOK", "The published source book is not included. Book Participation Pieces are used beside a separately purchased copy."),
        ("AAC", "Keep the learner's robust AAC system available. Model without requiring imitation and honor all intentional communication modes."),
        ("LICENSING", "Read the included Terms of Use and credits before sharing files. Do not extract or redistribute symbols as standalone clip art."),
    ]
    top = 560
    for heading, body in sections:
        box = (210, top, PAGE_W - 210, top + 465)
        draw.rounded_rectangle(box, radius=36, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_TEAL), width=4)
        _text(draw, heading, (275, top + 55, 880, top + 160), 12, True, 1)
        _text(draw, body, (900, top + 55, PAGE_W - 275, top + 390), 10, False, 4)
        top += 510
    return page


def _top_tips_page(pack_code: str, page_num: int, total: int, hero_img: Image.Image | None = None) -> Image.Image:
    """AAC communication partner tips page (amalgamated from standalone Top Tips)."""
    page, draw = _page("Bundle Start Here", "Top Tips for AAC Communication Partners", pack_code, page_num, total, hero_img)
    tips = [
        ("WAIT", "Allow 5-10 seconds of silence after each question or prompt. AAC users need time to navigate, select, and confirm their response."),
        ("MODEL", "Point to symbols on the board as you speak. AAC users learn language through repeated modelling, just as speaking children do."),
        ("OFFER CHOICES", "Present two clear options rather than open-ended questions. 'Book or toy?' is easier than 'What do you want?'"),
        ("CONFIRM", "Repeat back what the AAC user selected: 'You said bed. Yes, it is bedtime!' This validates their communication and builds confidence."),
        ("FOLLOW THEIR LEAD", "If the student points to an unexpected symbol, explore it. Communication is about connection, not just correct answers."),
        ("KEEP IT FUN", "Mix communication moments into play and reading. Celebrate every attempt - pointing, eye gaze, vocalisation, or symbol selection."),
        ("PARTNER WITH THE TEAM", "Share successful strategies with the speech pathologist, classroom teacher, and family. Consistency across settings accelerates progress."),
    ]
    margin = int(0.45 * DPI)
    content_w = PAGE_W - 2 * margin
    y = 560
    for label, body in tips:
        # Label pill
        label_font = _fit(label, 14, int(2.0 * DPI), bold=True)
        bbox = draw.textbbox((0, 0), label, font=label_font)
        label_w = bbox[2] - bbox[0] + int(0.3 * DPI)
        label_h = bbox[3] - bbox[1] + int(0.15 * DPI)
        pill_x1 = margin
        pill_y1 = y
        pill_x2 = pill_x1 + label_w
        pill_y2 = pill_y1 + label_h
        draw.rounded_rectangle([pill_x1, pill_y1, pill_x2, pill_y2], radius=int(0.06 * DPI), fill=hex_to_rgb(SWS_TEAL))
        tx = pill_x1 + (label_w - (bbox[2] - bbox[0])) // 2 - bbox[0]
        ty = pill_y1 + (label_h - (bbox[3] - bbox[1])) // 2 - bbox[1]
        draw.text((tx, ty), label, fill=(255, 255, 255), font=label_font)
        # Body text
        body_x = pill_x2 + int(0.15 * DPI)
        body_font = _font(11, bold=False)
        body_w = content_w - (body_x - margin)
        lines = _wrap_text(draw, body, body_font, body_w)
        body_y = pill_y1 + int(0.02 * DPI)
        for line in lines:
            draw.text((body_x, body_y), line, fill=hex_to_rgb(SWS_NAVY), font=body_font)
            body_y += int(0.16 * DPI)
        y = max(pill_y2, body_y) + int(0.10 * DPI)
    return page


def _wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def generate_bundle_start_here(slug: str = "llama_llama_red_pajama", pack_code: str = "LLRP-BUNDLE") -> Path:
    root = Path(__file__).resolve().parents[2]
    theme = root / "assets" / "themes" / slug
    source = theme / "config" / "bundle_start_here.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    total = 8  # was 7, now includes Top Tips page
    hero_path = theme / "hero.png"
    hero_img = None
    if hero_path.exists():
        try:
            im = Image.open(hero_path)
            hero_img = im.convert("RGBA") if im.mode != "RGBA" else im
        except Exception:
            hero_img = None
    hero_image_path = str(hero_path) if hero_path.exists() else None
    book_cover_path = None
    cover = _bundle_cover(data, pack_code, total, hero_img, hero_image_path, book_cover_path)
    pages = [
        cover,
        _contents(data, pack_code, 2, total, hero_img),
        _prep(data, pack_code, 3, total, hero_img),
        _five_day(data, pack_code, 4, total, hero_img),
        _access(pack_code, 5, total, hero_img),
        _rope(data, pack_code, 6, total, hero_img),
        _support(pack_code, 7, total, hero_img),
        _top_tips_page(pack_code, 8, total, hero_img),
    ]
    output = theme / "OUTPUT"
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{pack_code}_Bundle_Start_Here.pdf"
    bw_path = output / f"{pack_code}_Bundle_Start_Here_BW.pdf"
    preview_path = output / f"{pack_code}_Bundle_Start_Here_PREVIEW.pdf"
    _save_pdf(path, pages)
    _save_pdf(bw_path, [page.convert("L").convert("RGB") for page in pages])
    _save_pdf(preview_path, pages[:3], True)
    manifest = {
        "schema_version": 1,
        "status": "pilot_review",
        "product_name": "Bundle Start Here",
        "slug": slug,
        "pack_code": pack_code,
        "page_count": len(pages),
        "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "files": {"color_pdf": str(path), "bw_pdf": str(bw_path), "preview_pdf": str(preview_path)},
        "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": []},
    }
    (output / f"{pack_code}_Bundle_Start_Here_BuildResult.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    print(generate_bundle_start_here())
