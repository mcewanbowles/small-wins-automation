from __future__ import annotations

from typing import Optional

from PIL import Image, ImageDraw, ImageFont

DPI = 300

# Matching design constants
LIGHT_BLUE_BORDER_HEX = "#A0C4E8"
NAVY_HEX = "#1E3A5F"
WARM_ORANGE_HEX = "#F5A623"
DEFAULT_ACCENT_TEAL_HEX = "#2CA6A4"
SUBTITLE_DARK_GRAY = (51, 51, 51)

LEVEL_COLORS = {
    1: "#F4A259",
    2: "#4A90E2",
    3: "#7BC47F",
    4: "#9B59B6",
    5: "#E74C3C",
}

_FONT_COMIC = "C:/Windows/Fonts/comic.ttf"
_FONT_COMIC_BOLD = "C:/Windows/Fonts/comicbd.ttf"
_FONT_ARIAL = "C:/Windows/Fonts/arial.ttf"
_FONT_ARIAL_BOLD = "C:/Windows/Fonts/arialbd.ttf"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _load_fonts(*, title_pt: int, body_pt: int, small_pt: int) -> dict[str, ImageFont.ImageFont]:
    scale = DPI / 72
    try:
        # Prefer Comic Sans MS throughout.
        return {
            "title": ImageFont.truetype(_FONT_COMIC_BOLD, int(title_pt * scale)),
            "body": ImageFont.truetype(_FONT_COMIC_BOLD, int(body_pt * scale)),
            "small": ImageFont.truetype(_FONT_COMIC, int(small_pt * scale)),
            "small_bold": ImageFont.truetype(_FONT_COMIC_BOLD, int(small_pt * scale)),
        }
    except Exception:
        pass

    try:
        return {
            "title": ImageFont.truetype(_FONT_ARIAL_BOLD, int(title_pt * scale)),
            "body": ImageFont.truetype(_FONT_ARIAL_BOLD, int(body_pt * scale)),
            "small": ImageFont.truetype(_FONT_ARIAL, int(small_pt * scale)),
            "small_bold": ImageFont.truetype(_FONT_ARIAL_BOLD, int(small_pt * scale)),
        }
    except Exception:
        f = ImageFont.load_default()
        return {"title": f, "body": f, "small": f, "small_bold": f}


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def _make_near_white_transparent(img: Image.Image, *, threshold: int = 245) -> Image.Image:
    work = img.convert("RGBA")
    px = list(work.getdata())
    out: list[tuple[int, int, int, int]] = []
    for r, g, b, a in px:
        if r > threshold and g > threshold and b > threshold:
            out.append((r, g, b, 0))
        else:
            out.append((r, g, b, a))
    work.putdata(out)
    return work


def apply_small_wins_frame(
    page: Image.Image,
    *,
    product_title: str,
    subtitle: str,
    pack_code: str,
    page_num: int,
    total_pages: int,
    level: Optional[int] = None,
    accent_color_hex: str | None = None,
    footer_title: str | None = None,
    copyright_year: int = 2026,
    header_left_icon: Image.Image | None = None,
    header_left_icon_flip: bool = False,
    header_left_icon_y_offset_px: int = 0,
    footer_y_offset_px: int = 0,
    header_height_px: int | None = None,
    draw_accent_strip: bool = True,
    draw_header: bool = True,
    draw_subtitle: bool = True,
    draw_footer: bool = True,
) -> None:
    w, h = page.size
    d = ImageDraw.Draw(page)

    fonts = _load_fonts(title_pt=24, body_pt=14, small_pt=10)

    border_margin = int(0.25 * DPI)
    # Match ReportLab 3pt stroke used on activity pages.
    border_w = max(3, int(round(3 * (DPI / 72))))
    border_r = int(0.18 * DPI)
    for i in range(border_w):
        d.rounded_rectangle(
            [
                border_margin + i,
                border_margin + i,
                w - border_margin - 1 - i,
                h - border_margin - 1 - i,
            ],
            radius=max(1, border_r - i),
            outline=hex_to_rgb(LIGHT_BLUE_BORDER_HEX),
            fill=None,
        )

    # Accent stripe (matching style): thick warm orange, not touching border.
    header_h = header_height_px if header_height_px is not None else int(1.00 * DPI)
    accent_margin = int(0.08 * DPI)
    accent_x1 = border_margin + accent_margin
    accent_y1 = border_margin + accent_margin
    accent_x2 = w - border_margin - accent_margin
    accent_y2 = accent_y1 + header_h
    if draw_accent_strip:
        if accent_color_hex:
            accent_fill = hex_to_rgb(accent_color_hex)
        else:
            accent_fill = (
                hex_to_rgb(LEVEL_COLORS.get(level, DEFAULT_ACCENT_TEAL_HEX))
                if level is not None
                else hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX)
            )
        d.rounded_rectangle(
            [accent_x1, accent_y1, accent_x2, accent_y2],
            radius=int(0.12 * DPI),
            fill=accent_fill,
            outline=None,
        )

    if draw_accent_strip and header_left_icon is not None:
        icon = _make_near_white_transparent(header_left_icon.copy())
        if header_left_icon_flip:
            icon = icon.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        target_h = int(header_h * 0.78)
        icon.thumbnail((target_h * 2, target_h), Image.Resampling.LANCZOS)
        icon_x = accent_x1 + int(0.18 * DPI)
        icon_y = accent_y1 + (header_h - icon.height) // 2 + int(header_left_icon_y_offset_px)
        page.paste(icon, (icon_x, icon_y), icon)

    if draw_header:
        tw, th = _text_size(d, product_title, fonts["title"])
        title_x = (w - tw) // 2

        if draw_subtitle and draw_accent_strip and subtitle:
            sw, sh = _text_size(d, subtitle, fonts["body"])
            gap = max(1, int(header_h * 0.12))
            block_h = th + gap + sh
            block_y0 = accent_y1 + max(0, (header_h - block_h) // 2)
            title_y = block_y0
            sub_y = block_y0 + th + gap
            d.text((title_x, title_y), product_title, fill=hex_to_rgb(NAVY_HEX), font=fonts["title"])
            d.text(((w - sw) // 2, sub_y), subtitle, fill=SUBTITLE_DARK_GRAY, font=fonts["body"])
        else:
            # Center vertically within the accent stripe.
            title_y = accent_y1 + (header_h - th) // 2
            d.text((title_x, title_y), product_title, fill=hex_to_rgb(NAVY_HEX), font=fonts["title"])

    elif draw_subtitle:
        # Subtitle without header (or without accent strip)
        sub_y = int(0.75 * DPI)
        sw, sh = _text_size(d, subtitle, fonts["body"])
        d.text(((w - sw) // 2, sub_y), subtitle, fill=hex_to_rgb(NAVY_HEX), font=fonts["body"])

    if draw_footer:
        level_text = f" | Level {level}" if level is not None else ""
        code_text = f" | {pack_code}" if pack_code else ""

        footer_product = footer_title if footer_title is not None else product_title

        footer_line_1 = f"{footer_product}{level_text}{code_text} | Page {page_num}/{total_pages}"
        footer_line_2 = (
            f"Small Wins Studio | PCS symbols used with active PCS Maker Personal License. | "
            f"© {copyright_year}"
        )

        # Keep the footer visually close to the bottom border while ensuring it never
        # touches the border stroke. Some products (e.g., Bingo) may need this nudged
        # upward further.
        y2 = h - border_margin - int(0.18 * DPI) - int(footer_y_offset_px)
        y1 = y2 - int(0.14 * DPI)

        fw1, fh1 = _text_size(d, footer_line_1, fonts["small_bold"])
        fw2, fh2 = _text_size(d, footer_line_2, fonts["small"])
        # Gold standard: Find & Cover Level 2 uses light grey for BOTH footer lines.
        footer_grey = (153, 153, 153)  # #999999
        d.text(((w - fw1) // 2, y1), footer_line_1, fill=footer_grey, font=fonts["small_bold"])
        d.text(((w - fw2) // 2, y2), footer_line_2, fill=footer_grey, font=fonts["small"])
