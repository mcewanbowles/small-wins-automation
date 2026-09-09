from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from PIL import Image, ImageDraw, ImageOps
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from utils.UNIVERSAL_STANDARDS import SWS_GOLD, SWS_NAVY, SWS_TEAL, SWS_TEAL_LT
from utils.sws_design import DPI, _brand_font_pt, apply_small_wins_frame, hex_to_rgb, shrink_font_to_fit_with_pt

PAGE_W_PT, PAGE_H_PT = letter
PAGE_W = int(PAGE_W_PT * DPI / 72)
PAGE_H = int(PAGE_H_PT * DPI / 72)
WHITE = "#FFFFFF"
PAGE_BG = "#F8FCFC"
TEXT_GRAY = "#52606D"
MID_GRAY = "#D4DEDF"
PALE_GOLD = "#FFF8DF"


def _dedupe(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values or []:
        text = str(value).strip()
        key = re.sub(r"\s+", " ", text).casefold()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result


def format_page_summary(page_counts: dict) -> str:
    labels = (("color", "color"), ("bw", "B&W"), ("high_vis", "high-visibility"), ("preview", "preview"), ("digital", "digital"))
    parts = []
    for key, label in labels:
        count = page_counts.get(key)
        if isinstance(count, int) and count > 0:
            parts.append(f"{count} {label} page{'s' if count != 1 else ''}")
    return " · ".join(parts)


def normalize_overview(data: dict) -> dict:
    normalized = dict(data)
    formats = _dedupe(data.get("formats", []))
    included = _dedupe(data.get("included", []))
    format_keys = {value.casefold().replace("black and white", "b&w") for value in formats}
    included = [item for item in included if not ("version" in item.casefold() and any(key in item.casefold() for key in format_keys))]
    normalized.update({
        "formats": formats,
        "included": included,
        "levels": _dedupe(data.get("levels", [])),
        "best_for": _dedupe(data.get("best_for", [])),
        "access": _dedupe(data.get("access", [])),
        "book_companion": bool(data.get("book_companion", False)),
        "book_not_included": bool(data.get("book_companion", False) and data.get("book_not_included", True)),
        "pcs_used": bool(data.get("pcs_used", False)),
        "output_role": "standalone_teacher_support",
        "merge_into_activity_core": False,
    })
    return normalized


def validate_overview(data: dict) -> list[str]:
    errors = []
    for key in ("product_name", "theme_name", "product_code", "version", "page_counts", "included", "best_for", "preparation", "teaching_steps", "scarborough"):
        if not data.get(key):
            errors.append(f"Missing required field: {key}")
    if not any(isinstance(value, int) and value > 0 for value in data.get("page_counts", {}).values()):
        errors.append("At least one positive page count is required")
    if len(data.get("teaching_steps", [])) != 3:
        errors.append("Exactly three teaching steps are required")
    if not data.get("scarborough", {}).get("strands"):
        errors.append("At least one verified Scarborough strand is required")
    return errors


def _font(pt: int, bold: bool = False):
    return _brand_font_pt(pt, bold=bold, brand="poppins" if bold else "nunito")


def _fit(text: str, base_pt: int, max_width: int, minimum: int = 10, bold: bool = True):
    return shrink_font_to_fit_with_pt(text, base_pt=base_pt, max_width_px=max_width, bold=bold, brand="poppins" if bold else "nunito", min_pt=minimum)[0]


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, max_lines: int | None = None) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
            if max_lines and len(lines) >= max_lines:
                break
    if current and (not max_lines or len(lines) < max_lines):
        lines.append(current)
    return lines


def _draw_lines(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], font, fill, max_width: int, gap: int = 9, max_lines: int | None = None) -> int:
    x, y = xy
    for line in _wrap(draw, text, font, max_width, max_lines):
        draw.text((x, y), line, font=font, fill=fill)
        box = draw.textbbox((x, y), line or "Ag", font=font)
        y = box[3] + gap
    return y


def _line_block_height(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, gap: int = 9, max_lines: int | None = None) -> int:
    lines = _wrap(draw, text, font, max_width, max_lines)
    if not lines:
        return 0
    heights = [draw.textbbox((0, 0), line or "Ag", font=font)[3] for line in lines]
    return sum(heights) + gap * max(0, len(lines) - 1)


def _bullet_list_height(draw: ImageDraw.ImageDraw, items: list[str], width: int, font_pt: int = 12, max_items: int = 6) -> int:
    font = _font(font_pt)
    return sum(_line_block_height(draw, item, font, width - 48, 8, 3) + 14 for item in items[:max_items])


def _center_wrapped_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font, fill, max_lines: int = 4, gap: int = 6):
    x1, y1, x2, y2 = box
    lines = _wrap(draw, text, font, x2 - x1, max_lines)
    heights = [draw.textbbox((0, 0), line or "Ag", font=font)[3] for line in lines]
    total_height = sum(heights) + gap * max(0, len(lines) - 1)
    y = y1 + max(0, (y2 - y1 - total_height) // 2)
    for line, height in zip(lines, heights):
        bounds = draw.textbbox((0, 0), line, font=font)
        width = bounds[2] - bounds[0]
        draw.text((x1 + (x2 - x1 - width) // 2 - bounds[0], y - bounds[1]), line, font=font, fill=fill)
        y += height + gap


def _panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str = WHITE, outline: str = MID_GRAY, radius: int = 34, width: int = 4):
    draw.rounded_rectangle(box, radius=radius, fill=hex_to_rgb(fill), outline=hex_to_rgb(outline), width=width)


def _center_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font, fill):
    bounds = draw.textbbox((0, 0), text, font=font)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    x1, y1, x2, y2 = box
    draw.text((x1 + (x2 - x1 - width) // 2 - bounds[0], y1 + (y2 - y1 - height) // 2 - bounds[1]), text, font=font, fill=fill)


def _section_title(draw: ImageDraw.ImageDraw, x: int, y: int, title: str, width: int) -> int:
    draw.text((x, y), title, font=_font(17, True), fill=hex_to_rgb(SWS_NAVY))
    draw.line((x, y + 86, x + width, y + 86), fill=hex_to_rgb(SWS_TEAL), width=5)
    return y + 114


def _bullet_list(draw: ImageDraw.ImageDraw, items: list[str], x: int, y: int, width: int, font_pt: int = 12, max_items: int = 6) -> int:
    font = _font(font_pt)
    for item in items[:max_items]:
        draw.ellipse((x, y + 17, x + 24, y + 41), fill=hex_to_rgb(SWS_TEAL))
        y = _draw_lines(draw, item, (x + 48, y), font, hex_to_rgb(TEXT_GRAY), width - 48, 8, 3) + 14
    return y


def _load_preview(path_value: str | None) -> Image.Image | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.is_absolute():
        path = _BOOTSTRAP_ROOT / path
    if not path.exists():
        return None
    if path.suffix.lower() == ".pdf":
        try:
            import fitz
            document = fitz.open(path)
            page = document.load_page(0)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            document.close()
            return image
        except Exception:
            return None
    try:
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


def _paste_contain(page: Image.Image, image: Image.Image, box: tuple[int, int, int, int], padding: int = 35):
    x1, y1, x2, y2 = box
    fitted = ImageOps.contain(image, (x2 - x1 - padding * 2, y2 - y1 - padding * 2), Image.Resampling.LANCZOS)
    position = (x1 + (x2 - x1 - fitted.width) // 2, y1 + (y2 - y1 - fitted.height) // 2)
    page.paste(fitted, position, fitted if fitted.mode == "RGBA" else None)


def _load_hero_icon(data: dict) -> Image.Image | None:
    """Resolve the theme hero image (theme_dir / hero.png) for the standard frame icon."""
    hero_path = data.get("hero_image")
    if not hero_path:
        return None
    path = Path(hero_path)
    if not path.is_absolute():
        path = _BOOTSTRAP_ROOT / path
    if not path.exists():
        return None
    try:
        image = Image.open(path)
        return image.convert("RGBA") if image.mode != "RGBA" else image
    except Exception:
        return None


def _draw_rope_icon(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], tier: str):
    upper = ["#0D2545", "#0284C7", "#31A8A0", "#7C3AED", "#E11D48"]
    lower = ["#E1B42D", "#059669", "#E07B00"]
    colors = upper if tier == "upper" else lower if tier == "lower" else upper + lower
    x1, y1, x2, y2 = box
    center_y = (y1 + y2) // 2
    spacing = max(8, (y2 - y1 - 24) // max(1, len(colors) - 1))
    start_y = center_y - spacing * (len(colors) - 1) // 2
    for index, color in enumerate(colors):
        sy = start_y + index * spacing
        ey = center_y + ((index % 3) - 1) * 5
        draw.line((x1, sy, x1 + 95, sy, x1 + 185, ey, x2, ey), fill=hex_to_rgb(color), width=8, joint="curve")
    draw.ellipse((x2 - 15, center_y - 15, x2 + 15, center_y + 15), fill=hex_to_rgb(SWS_NAVY))


def _draw_chips(draw: ImageDraw.ImageDraw, data: dict, y: int):
    chips = list(data["formats"][:3])
    if data["levels"]:
        chips.append(f"{len(data['levels'])} levels")
    font = _font(10, True)
    widths = [draw.textbbox((0, 0), chip, font=font)[2] + 58 for chip in chips]
    gap = 18
    total_width = sum(widths) + gap * max(0, len(widths) - 1)
    x = (PAGE_W - total_width) // 2
    for chip, width in zip(chips, widths):
        chip_box = (x, y, x + width, y + 72)
        draw.rounded_rectangle(chip_box, radius=28, fill=hex_to_rgb(SWS_TEAL_LT), outline=hex_to_rgb(SWS_TEAL), width=3)
        _center_text(draw, chip_box, chip, font, hex_to_rgb(SWS_NAVY))
        x += width + gap


def render_teacher_overview(raw_data: dict) -> Image.Image:
    errors = validate_overview(raw_data)
    if errors:
        raise ValueError("Invalid Teacher Overview data:\n- " + "\n- ".join(errors))
    data = normalize_overview(raw_data)
    page = Image.new("RGB", (PAGE_W, PAGE_H), hex_to_rgb(PAGE_BG))
    hero_img = _load_hero_icon(data)
    apply_small_wins_frame(
        page,
        product_title="Teacher Overview",
        subtitle=data["theme_name"],
        pack_code=data["product_code"],
        page_num=1,
        total_pages=1,
        draw_footer=True,
        draw_pcs_line=True,
        header_left_icon=hero_img,
    )
    draw = ImageDraw.Draw(page)
    _draw_chips(draw, data, 565)

    preview_box = (105, 680, 965, 1855)
    _panel(draw, preview_box, WHITE, SWS_NAVY)
    preview = _load_preview(data.get("preview_image"))
    if preview:
        _paste_contain(page, preview, (130, 705, 940, 1690), 30)
    else:
        draw.text((250, 1110), "ACTIVITY PREVIEW", font=_font(16, True), fill=hex_to_rgb(TEXT_GRAY))
    caption = "Book not included · Purchase separately" if data["book_not_included"] else "Representative activity page"
    caption_font = _fit(caption, 10, 750, 8, False)
    caption_width = draw.textbbox((0, 0), caption, font=caption_font)[2]
    draw.text((preview_box[0] + (preview_box[2] - preview_box[0] - caption_width) // 2, 1755), caption, font=caption_font, fill=hex_to_rgb(TEXT_GRAY))

    info_box = (1005, 680, PAGE_W - 105, 1855)
    _panel(draw, info_box)
    info_width = info_box[2] - info_box[0] - 100
    included_height = _bullet_list_height(draw, data["included"], info_width, 12, 6)
    info_content_height = 114 + included_height + 40 + 135
    info_y = info_box[1] + max(55, (info_box[3] - info_box[1] - info_content_height) // 2)
    y = _section_title(draw, 1055, info_y, "What’s included", info_width)
    y = _bullet_list(draw, data["included"], 1055, y, info_width, 12, 6)
    summary_top = y + 40
    summary_box = (1055, summary_top, info_box[2] - 50, summary_top + 135)
    draw.rounded_rectangle(summary_box, radius=24, fill=hex_to_rgb(PALE_GOLD), outline=hex_to_rgb(SWS_GOLD), width=3)
    summary = format_page_summary(data["page_counts"])
    summary_font = _fit(summary, 10, info_box[2] - info_box[0] - 170, 8)
    _center_text(draw, summary_box, summary, summary_font, hex_to_rgb(SWS_NAVY))

    fit_box = (105, 1900, 1190, 2765)
    _panel(draw, fit_box)
    fit_width = fit_box[2] - fit_box[0] - 100
    best_y = _section_title(draw, 155, 1950, "Best for", fit_width)
    _bullet_list(draw, data["best_for"], 155, best_y, fit_width, 10, 4)
    access_y = _section_title(draw, 155, 2320, "Access & differentiation", fit_width)
    _bullet_list(draw, data["access"], 155, access_y, fit_width, 9, 3)

    teach_box = (1230, 1900, PAGE_W - 105, 2765)
    _panel(draw, teach_box)
    y = _section_title(draw, 1280, 1950, "Prepare & teach", teach_box[2] - teach_box[0] - 100)
    prep = data["preparation"]
    draw.text((1280, y), prep["label"], font=_font(12, True), fill=hex_to_rgb(SWS_NAVY))
    y = _draw_lines(draw, prep["materials"], (1280, y + 60), _font(9), hex_to_rgb(TEXT_GRAY), teach_box[2] - teach_box[0] - 100, 7, 2)
    draw.text((1280, y + 10), f"Preparation time: {prep['time']}", font=_font(9, True), fill=hex_to_rgb(SWS_TEAL))
    y += 100
    steps = data["teaching_steps"]
    card_gap = 20
    card_w = (teach_box[2] - teach_box[0] - 100 - card_gap * 2) // 3
    for index, step in enumerate(steps):
        x = 1280 + index * (card_w + card_gap)
        draw.rounded_rectangle((x, y, x + card_w, y + 310), radius=24, fill=hex_to_rgb(SWS_TEAL_LT), outline=hex_to_rgb(SWS_TEAL), width=3)
        number_box = (x + 25, y + 25, x + 88, y + 88)
        draw.ellipse(number_box, fill=hex_to_rgb(SWS_NAVY))
        number = str(index + 1)
        number_font = _font(10, True)
        _center_text(draw, number_box, number, number_font, hex_to_rgb(WHITE))
        title_font = _fit(step["title"], 10, card_w - 130, 8)
        _center_text(draw, (x + 100, y + 20, x + card_w - 20, y + 96), step["title"], title_font, hex_to_rgb(SWS_NAVY))
        _center_wrapped_text(draw, (x + 25, y + 112, x + card_w - 25, y + 285), step["detail"], _font(8), hex_to_rgb(TEXT_GRAY), 4, 6)

    rope_box = (105, 2810, PAGE_W - 105, 3075)
    _panel(draw, rope_box, SWS_TEAL_LT, SWS_TEAL)
    _draw_rope_icon(draw, (155, 2860, 440, 3015), data["scarborough"].get("tier", "both"))
    draw.text((495, 2850), "SCARBOROUGH ALIGNMENT", font=_font(10, True), fill=hex_to_rgb(SWS_TEAL))
    strands = " · ".join(data["scarborough"]["strands"])
    _draw_lines(draw, strands, (495, 2900), _font(11, True), hex_to_rgb(SWS_NAVY), 930, 7, 2)
    _draw_lines(draw, data["scarborough"]["statement"], (1550, 2875), _font(9), hex_to_rgb(TEXT_GRAY), 790, 6, 3)

    return page


def build_teacher_overview(data_path: Path | str, output_dir: Path | str | None = None) -> dict:
    source = Path(data_path).resolve()
    raw_data = json.loads(source.read_text(encoding="utf-8"))
    data = normalize_overview(raw_data)
    errors = validate_overview(data)
    if errors:
        raise ValueError("Invalid Teacher Overview data:\n- " + "\n- ".join(errors))
    out = Path(output_dir) if output_dir else _BOOTSTRAP_ROOT / "Studioforge" / "OUTPUT" / data["product_code"] / "support"
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{data['product_code']}_Teacher_Overview"
    png_path = out / f"{stem}.png"
    pdf_path = out / f"{stem}.pdf"
    manifest_path = out / f"{stem}_BuildResult.json"
    page = render_teacher_overview(data)
    page.save(png_path, "PNG", dpi=(DPI, DPI))
    pdf = canvas.Canvas(str(pdf_path), pagesize=letter)
    pdf.setTitle(f"{data['product_name']} Teacher Overview")
    pdf.setAuthor("Small Wins Studio")
    buffer = io.BytesIO()
    page.save(buffer, "PNG", dpi=(DPI, DPI))
    buffer.seek(0)
    pdf.drawImage(ImageReader(buffer), 0, 0, width=PAGE_W_PT, height=PAGE_H_PT)
    pdf.showPage()
    pdf.save()
    manifest = {
        "product_name": data["product_name"],
        "product_code": data["product_code"],
        "output_role": "standalone_teacher_support",
        "merge_into_activity_core": False,
        "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "generator": str(Path(__file__).resolve()),
        "files": {"pdf": str(pdf_path.resolve()), "png": str(png_path.resolve())},
        "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": []},
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a standardized standalone Small Wins Teacher Overview")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(build_teacher_overview(args.data, args.output_dir)["files"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
