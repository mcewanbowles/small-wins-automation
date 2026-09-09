from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

from Studioforge._TRUTH.generate_book_participation_pieces import _activity_page, _center, _clean_hero, _fit, _font, _save_pdf, _theme_dir
from utils.UNIVERSAL_STANDARDS import SWS_GOLD, SWS_NAVY, SWS_TEAL, SWS_TEAL_LT
from utils.sws_design import DPI, generate_internal_cover_page, generate_teacher_cover_page, generate_storage_label_page, hex_to_rgb

PAGE_W = int(612 * DPI / 72)
PAGE_H = int(792 * DPI / 72)
WHITE = "#FFFFFF"
TEXT = "#334E68"


def _load(images_folder: str) -> tuple[dict, Path, dict[str, Image.Image]]:
    theme = _theme_dir(images_folder)
    source = theme / "config" / "sorting.json"
    data = json.loads(source.read_text(encoding="utf-8")) if source.exists() else None
    if not data or len(data.get("sets") or []) != 2:
        raise ValueError(f"Two reviewed sorting sets are required: {source}")
    keys = []
    for sorting_set in data["sets"]:
        keys.extend(sorting_set["left"]["items"])
        keys.extend(sorting_set["right"]["items"])
    icons = {}
    for key in dict.fromkeys(keys):
        path = Path(images_folder) / f"{key}.png"
        if not path.exists() or not data.get("labels", {}).get(key):
            raise ValueError(f"Missing reviewed sorting item: {key}")
        icons[key] = _clean_hero(Image.open(path))
    return data, source, icons


def _mat(theme_name: str, pack_code: str, sorting_set: dict, page_num: int, total_pages: int) -> Image.Image:
    page = _activity_page("Reason & Sort", f"{theme_name} — {sorting_set['title']}", pack_code, page_num, total_pages)
    draw = ImageDraw.Draw(page)
    prompt = "Choose a category for each card. Explain your rule."
    prompt_box = (220, 540, PAGE_W - 220, 725)
    draw.rounded_rectangle(prompt_box, radius=42, fill=hex_to_rgb(SWS_TEAL_LT), outline=hex_to_rgb(SWS_TEAL), width=4)
    _center(draw, prompt_box, prompt, _fit(prompt, 16, PAGE_W - 600, 11), hex_to_rgb(SWS_NAVY))
    boxes = [(180, 850, 1220, 2800), (1330, 850, PAGE_W - 180, 2800)]
    for side, box in zip((sorting_set["left"], sorting_set["right"]), boxes):
        draw.rounded_rectangle(box, radius=45, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_NAVY), width=5)
        header = (box[0] + 55, box[1] + 55, box[2] - 55, box[1] + 250)
        draw.rounded_rectangle(header, radius=40, fill=hex_to_rgb(SWS_TEAL), outline=hex_to_rgb(SWS_TEAL), width=3)
        _center(draw, header, side["label"], _fit(side["label"], 17, header[2] - header[0] - 60, 11), hex_to_rgb(WHITE))
        for y in (1220, 1590, 1960, 2330):
            marker = (box[0] + 180, y, box[2] - 180, y + 260)
            draw.rounded_rectangle(marker, radius=34, fill=hex_to_rgb("#F8FCFC"), outline=hex_to_rgb(SWS_GOLD), width=4)
            _center(draw, marker, "PLACE CARD", _font(10, True), hex_to_rgb(TEXT))
    return page


def _pieces(theme_name: str, pack_code: str, sorting_set: dict, labels: dict, icons: dict, page_num: int, total_pages: int) -> Image.Image:
    page = _activity_page("Reason & Sort", f"{sorting_set['title']} — Cut-Out Cards", pack_code, page_num, total_pages)
    draw = ImageDraw.Draw(page)
    keys = sorting_set["left"]["items"] + sorting_set["right"]["items"]
    positions = [(220, 650), (950, 650), (1680, 650), (220, 1700), (950, 1700), (1680, 1700)]
    for key, (x, y) in zip(keys, positions):
        box = (x, y, x + 650, y + 870)
        draw.rounded_rectangle(box, radius=38, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_NAVY), width=5)
        icon = icons[key].copy()
        if icon.width > 0 and icon.height > 0:
            ratio = min(470 / icon.width, 520 / icon.height)
            icon = icon.resize((max(1, int(icon.width * ratio)), max(1, int(icon.height * ratio))), Image.Resampling.LANCZOS)
        page.paste(icon, (x + (650 - icon.width) // 2, y + 70), icon)
        label_box = (x + 45, y + 660, x + 605, y + 810)
        draw.rounded_rectangle(label_box, radius=32, fill=hex_to_rgb(SWS_TEAL_LT), outline=hex_to_rgb(SWS_TEAL), width=3)
        _center(draw, label_box, labels[key], _fit(labels[key], 15, 500, 10), hex_to_rgb(SWS_NAVY))
    return page


def _key(theme_name: str, pack_code: str, sorting_set: dict, labels: dict, icons: dict, page_num: int, total_pages: int) -> Image.Image:
    page = _activity_page("Reason & Sort Answer Key", sorting_set["title"], pack_code, page_num, total_pages)
    draw = ImageDraw.Draw(page)
    columns = [(190, 620, 1210, 2880), (1340, 620, PAGE_W - 190, 2880)]
    for side, column in zip((sorting_set["left"], sorting_set["right"]), columns):
        draw.rounded_rectangle(column, radius=42, fill=hex_to_rgb("#F8FCFC"), outline=hex_to_rgb(SWS_TEAL), width=5)
        _center(draw, (column[0] + 50, 680, column[2] - 50, 850), side["label"], _fit(side["label"], 16, column[2] - column[0] - 150, 10), hex_to_rgb(SWS_NAVY))
        top = 930
        for key in side["items"]:
            row = (column[0] + 70, top, column[2] - 70, top + 420)
            draw.rounded_rectangle(row, radius=30, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_GOLD), width=3)
            icon = icons[key].copy()
            if icon.width > 0 and icon.height > 0:
                ratio = min(260 / icon.width, 260 / icon.height)
                icon = icon.resize((max(1, int(icon.width * ratio)), max(1, int(icon.height * ratio))), Image.Resampling.LANCZOS)
            page.paste(icon, (row[0] + 45, top + (420 - icon.height) // 2), icon)
            _center(draw, (row[0] + 350, top + 50, row[2] - 40, top + 370), labels[key], _fit(labels[key], 13, row[2] - row[0] - 450, 9), hex_to_rgb(SWS_NAVY))
            top += 480
    return page


def _open_sort_mat(theme_name: str, pack_code: str, categories: int, page_num: int, total_pages: int) -> Image.Image:
    page = _activity_page("Open Sort", f"{theme_name} — Choose {categories} Headers", pack_code, page_num, total_pages)
    draw = ImageDraw.Draw(page)
    cue = "Choose headers or write your own. Sort the cards, then explain your rule."
    cue_box = (190, 540, PAGE_W - 190, 735)
    draw.rounded_rectangle(cue_box, radius=42, fill=hex_to_rgb(SWS_TEAL_LT), outline=hex_to_rgb(SWS_TEAL), width=4)
    _center(draw, cue_box, cue, _fit(cue, 15, PAGE_W - 560, 10), hex_to_rgb(SWS_NAVY))
    gap = 65
    total_width = PAGE_W - 360 - gap * (categories - 1)
    column_width = total_width // categories
    for index in range(categories):
        x = 180 + index * (column_width + gap)
        box = (x, 870, x + column_width, 2820)
        draw.rounded_rectangle(box, radius=40, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_NAVY), width=5)
        header = (x + 55, 930, x + column_width - 55, 1160)
        draw.rounded_rectangle(header, radius=36, fill=hex_to_rgb("#F8FCFC"), outline=hex_to_rgb(SWS_GOLD), width=4)
        _center(draw, header, "PLACE OR WRITE HEADER", _fit("PLACE OR WRITE HEADER", 12, column_width - 160, 8), hex_to_rgb(SWS_NAVY))
        for row in range(4):
            target = (x + 100, 1300 + row * 370, x + column_width - 100, 1550 + row * 370)
            draw.rounded_rectangle(target, radius=32, fill=hex_to_rgb("#F8FCFC"), outline=hex_to_rgb(SWS_TEAL), width=3)
            _center(draw, target, "PLACE CARD", _font(9, True), hex_to_rgb(TEXT))
    return page


def _header_bank(theme_name: str, pack_code: str, headers: list[str], page_num: int, total_pages: int) -> Image.Image:
    page = _activity_page("Sorting Header Bank", theme_name, pack_code, page_num, total_pages)
    draw = ImageDraw.Draw(page)
    cols, rows = 2, 10
    gap_x, gap_y = 100, 45
    width = (PAGE_W - 440 - gap_x) // cols
    height = 205
    start_x, start_y = 220, 520
    for index, header in enumerate(headers[:20]):
        row, col = divmod(index, cols)
        x, y = start_x + col * (width + gap_x), start_y + row * (height + gap_y)
        cut_box = (x, y, x + width, y + height)
        draw.rounded_rectangle(cut_box, radius=34, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_NAVY), width=3)
        pill = (x + 35, y + 35, x + width - 35, y + height - 35)
        draw.rounded_rectangle(pill, radius=32, fill=hex_to_rgb(SWS_TEAL_LT), outline=hex_to_rgb(SWS_TEAL), width=3)
        _center(draw, pill, header, _fit(header, 13, width - 130, 9), hex_to_rgb(SWS_NAVY))
    return page


def _blank_headers(theme_name: str, pack_code: str, page_num: int, total_pages: int) -> Image.Image:
    page = _activity_page("Create Your Own Sorting Rule", theme_name, pack_code, page_num, total_pages)
    draw = ImageDraw.Draw(page)
    cue_box = (220, 550, PAGE_W - 220, 760)
    draw.rounded_rectangle(cue_box, radius=40, fill=hex_to_rgb(SWS_TEAL_LT), outline=hex_to_rgb(SWS_TEAL), width=4)
    _center(draw, cue_box, "Write a category on each header. More than one rule can be valid.", _fit("Write a category on each header. More than one rule can be valid.", 14, PAGE_W - 650, 10), hex_to_rgb(SWS_NAVY))
    positions = [(220, 930), (1330, 930), (220, 1500), (1330, 1500), (220, 2070), (1330, 2070)]
    for number, (x, y) in enumerate(positions, start=1):
        box = (x, y, x + 1000, y + 390)
        draw.rounded_rectangle(box, radius=38, fill=hex_to_rgb(WHITE), outline=hex_to_rgb(SWS_GOLD), width=4)
        _center(draw, (x + 50, y + 45, x + 210, y + 175), str(number), _font(12, True), hex_to_rgb(SWS_NAVY))
        draw.line((x + 230, y + 235, x + 920, y + 235), fill=hex_to_rgb(SWS_NAVY), width=3)
    return page


def generate_grounded_sorting_pack(images_folder: str, pack_code: str = "SORT", theme_name: str = "Theme") -> bool:
    try:
        data, source, icons = _load(images_folder)
    except Exception as exc:
        print(f"ERROR: {exc}"); return False
    total = 11  # 10 activity pages + 1 storage label
    pages = []
    for index, sorting_set in enumerate(data["sets"]):
        start = 1 + index * 3
        pages.extend([_mat(theme_name, pack_code, sorting_set, start, total), _pieces(theme_name, pack_code, sorting_set, data["labels"], icons, start + 1, total), _key(theme_name, pack_code, sorting_set, data["labels"], icons, start + 2, total)])
    pages.extend([
        _open_sort_mat(theme_name, pack_code, 2, 7, total),
        _open_sort_mat(theme_name, pack_code, 3, 8, total),
        _header_bank(theme_name, pack_code, data.get("header_bank") or [], 9, total),
        _blank_headers(theme_name, pack_code, 10, total),
    ])
    # Storage label page
    pages.append(generate_storage_label_page(
        product_title="Reason & Sort",
        theme_name=theme_name,
        pack_code=pack_code,
        page_num=11,
        total_pages=total,
        labels=[
            {"header": "Sorting Cards", "subtitle": "Category Sorting Pieces"},
            {"header": "Header Bank", "subtitle": "Sort Headers + Blank Headers"},
        ],
        footer_title=f"{theme_name} | Sorting",
    ))
    theme = _theme_dir(images_folder); output = theme / "OUTPUT"; output.mkdir(parents=True, exist_ok=True)
    color = output / f"{pack_code}_Sorting_COLOR.pdf"; bw = output / f"{pack_code}_Sorting_BW.pdf"; preview = output / f"{pack_code}_Sorting_PREVIEW.pdf"
    _save_pdf(color, pages); _save_pdf(bw, [page.convert("L").convert("RGB") for page in pages]); _save_pdf(preview, pages[:4], True)
    thumbs = output / "thumbnails"; thumbs.mkdir(parents=True, exist_ok=True); thumb_paths = []
    for index, page in enumerate((pages[0], pages[1], pages[2], pages[6], pages[7], pages[8], pages[9]), start=1):
        thumb = page.copy(); thumb.thumbnail((500, 647), Image.Resampling.LANCZOS); path = thumbs / f"{pack_code}_Sorting_thumb{index}.png"; thumb.save(path); thumb_paths.append(str(path))
    manifest = {"schema_version": 1, "status": "pilot_review", "product_name": "Reason & Sort", "slug": theme.name, "pack_code": pack_code, "page_count": len(pages), "guided_sort_count": 2, "open_sort_count": 2, "header_bank_count": len(data.get("header_bank") or []), "subjective_headers_have_answer_keys": False, "reading_rope": data["reading_rope"], "teacher_review_required": True, "source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "files": {"color_pdf": str(color), "bw_pdf": str(bw), "preview_pdf": str(preview), "thumbnails": thumb_paths}, "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": []}}
    (output / f"{pack_code}_Sorting_BuildResult.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return True
