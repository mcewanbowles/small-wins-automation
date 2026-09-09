from __future__ import annotations

from typing import Optional, Sequence
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
try:
    from utils.UNIVERSAL_STANDARDS import (
        SWS_TEAL, SWS_NAVY, SWS_GOLD, SWS_TEAL_LT, MID_GRAY,
        LEVEL_VIOLET, LEVEL_OCEAN, LEVEL_EMERALD, LEVEL_ROSE,
        STRAND_PILLS, COPYRIGHT_YEAR,
    )
except Exception:
    SWS_TEAL = "#31A8A0"
    SWS_NAVY = "#0D2545"
    SWS_GOLD = "#E1B42D"
    SWS_TEAL_LT = "#E8F8F8"
    MID_GRAY = "#E5E7EB"
    LEVEL_VIOLET = "#7C3AED"
    LEVEL_OCEAN = "#0284C7"
    LEVEL_EMERALD = "#059669"
    LEVEL_ROSE = "#E11D48"
    STRAND_PILLS = {}
    COPYRIGHT_YEAR = datetime.now().year

DPI = 300

LEVEL_NAME = {1: "Supported", 2: "Developing", 3: "Independent", 4: "Extended"}
LEVEL_COLOUR = {1: LEVEL_VIOLET, 2: LEVEL_OCEAN, 3: LEVEL_EMERALD, 4: LEVEL_ROSE}


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _font(pt: int, *, bold: bool = False) -> ImageFont.ImageFont:
    scale = DPI / 72
    size = max(1, int(pt * scale))
    stacks_b = [
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    stacks_r = [
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in (stacks_b if bold else stacks_r):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _txt(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, *, fill: str | tuple[int, int, int], font: ImageFont.ImageFont) -> None:
    draw.text(xy, text, fill=fill, font=font)


def _pill(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, *, fill: str | tuple[int, int, int]) -> None:
    draw.rounded_rectangle([x, y, x + w, y + h], radius=max(4, h // 3), fill=fill)


def _measure(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def draw_data_strip(page: Image.Image) -> None:
    w, h = page.size
    d = ImageDraw.Draw(page)
    strip_h = int(0.32 * DPI)
    y1 = h - strip_h - int(0.40 * DPI)  # ensure space above footer
    d.rectangle([0, y1, w, y1 + strip_h], fill=_hex_to_rgb(SWS_TEAL_LT))

    f_lbl = _font(7, bold=False)
    f_val = _font(7, bold=True)

    margin = int(0.35 * DPI)
    x = margin

    def field(lbl: str, box_w: int = int(1.0 * DPI)) -> None:
        nonlocal x
        _txt(d, (x, y1 + int(0.10 * DPI)), lbl, fill=_hex_to_rgb(SWS_NAVY), font=f_lbl)
        lw, lh = _measure(d, lbl, f_lbl)
        line_y = y1 + int(0.10 * DPI) + lh + int(0.04 * DPI)
        d.line([x, line_y, x + box_w, line_y], fill=_hex_to_rgb(MID_GRAY), width=max(1, int(DPI / 150)))
        x += box_w + int(0.30 * DPI)

    field("Name:", int(1.6 * DPI))
    field("Date:", int(1.2 * DPI))

    _txt(d, (x, y1 + int(0.10 * DPI)), "Level:", fill=_hex_to_rgb(SWS_NAVY), font=f_lbl)
    lw, lh = _measure(d, "Level:", f_lbl)
    x += lw + int(0.18 * DPI)
    r = int(0.09 * DPI)
    for i in range(1, 5):
        cx = x + (i - 1) * int(0.36 * DPI)
        cy = y1 + int(0.10 * DPI) + lh // 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=_hex_to_rgb(MID_GRAY), fill=(255, 255, 255))
        _txt(d, (cx - r, cy + int(0.10 * DPI)), str(i), fill=_hex_to_rgb(SWS_NAVY), font=f_lbl)
    x += int(4 * 0.36 * DPI) + int(0.30 * DPI)

    _txt(d, (x, y1 + int(0.10 * DPI)), "Prompt:", fill=_hex_to_rgb(SWS_NAVY), font=f_lbl)
    lw, lh = _measure(d, "Prompt:", f_lbl)
    x += lw + int(0.18 * DPI)
    for key in ["I", "G", "V", "M", "P", "FP"]:
        bx = x
        by = y1 + int(0.10 * DPI)
        bw = int(0.28 * DPI)
        bh = int(0.18 * DPI)
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=int(0.06 * DPI), outline=_hex_to_rgb(MID_GRAY), fill=(255, 255, 255))
        tw, th = _measure(d, key, f_val)
        _txt(d, (bx + (bw - tw) // 2, by + (bh - th) // 2), key, fill=_hex_to_rgb(SWS_NAVY), font=f_val)
        x += bw + int(0.08 * DPI)

    x += int(0.20 * DPI)
    _txt(d, (x, y1 + int(0.10 * DPI)), "Correct:", fill=_hex_to_rgb(SWS_NAVY), font=f_lbl)
    lw, lh = _measure(d, "Correct:", f_lbl)
    x += lw + int(0.10 * DPI)
    box_w = int(0.55 * DPI)
    line_y = y1 + int(0.10 * DPI) + lh + int(0.04 * DPI)
    d.line([x, line_y, x + box_w, line_y], fill=_hex_to_rgb(MID_GRAY), width=max(1, int(DPI / 150)))
    x += box_w + int(0.10 * DPI)
    _txt(d, (x, y1 + int(0.10 * DPI)), "/", fill=_hex_to_rgb(SWS_NAVY), font=f_val)
    x += int(0.14 * DPI)
    d.line([x, line_y, x + box_w, line_y], fill=_hex_to_rgb(MID_GRAY), width=max(1, int(DPI / 150)))


def _draw_strand_pill(d: ImageDraw.ImageDraw, x: int, y: int, label: str, color_hex: str) -> int:
    f = _font(8, bold=True)
    tw, th = _measure(d, label, f)
    pad_x = int(0.10 * DPI)
    h = th + int(0.08 * DPI)
    w = tw + pad_x * 2
    d.rounded_rectangle([x, y, x + w, y + h], radius=int(h / 2), fill=_hex_to_rgb(color_hex))
    _txt(d, (x + pad_x, y + (h - th) // 2), label, fill=(255, 255, 255), font=f)
    return w


def apply_sws_page_frame(
    page: Image.Image,
    *,
    activity_name: str,
    book_title: str,
    pack_code: str,
    page_num: int,
    total_pages: int,
    level: Optional[int] = None,
    strand_keys: Optional[Sequence[str]] = None,
    show_data_strip: bool = True,
) -> None:
    w, h = page.size
    d = ImageDraw.Draw(page)

    header_h = int(0.80 * DPI)
    d.rectangle([0, 0, w, header_h], fill=_hex_to_rgb(SWS_TEAL))

    f_title = _font(14, bold=True)
    f_meta = _font(8, bold=False)

    act = activity_name or "Activity"
    lvl_name = LEVEL_NAME.get(level or 0, "")
    left = act
    lt_w, lt_h = _measure(d, left, f_title)
    left_x = int(0.40 * DPI)
    left_y = (header_h - lt_h) // 2
    _txt(d, (left_x, left_y), left, fill=(255, 255, 255), font=f_title)
    if lvl_name:
        pill_h = max(10, int(header_h * 0.60))
        pad_x = int(0.16 * DPI)
        f_badge = _font(12, bold=True)
        tw, th = _measure(d, lvl_name, f_badge)
        pill_w = tw + pad_x * 2
        pill_y = (header_h - pill_h) // 2
        # Right-aligned pill with a small right margin
        pill_x = w - pill_w - int(0.40 * DPI)
        _pill(d, pill_x, pill_y, pill_w, pill_h, fill=_hex_to_rgb(LEVEL_COLOUR.get(level or 0, LEVEL_VIOLET)))
        _txt(d, (pill_x + pad_x, pill_y + (pill_h - th) // 2), lvl_name, fill=(255, 255, 255), font=f_badge)

    # Header right area: if a level is set, reserve the right edge for the level pill
    # (Bingo and some games). Otherwise, show the book_title · pack_code meta.
    if not lvl_name:
        right = f"{book_title} · {pack_code}".strip(" ·")
        rt_w, rt_h = _measure(d, right, f_meta)
        _txt(d, (w - rt_w - int(0.40 * DPI), header_h - rt_h - int(0.22 * DPI)), right, fill=(230, 254, 250), font=f_meta)

    d.line([0, header_h, w, header_h], fill=_hex_to_rgb(MID_GRAY), width=max(1, int(DPI / 144)))

    footer_h = int(0.42 * DPI)
    footer_y = h - footer_h
    d.rectangle([0, footer_y, w, h], fill=_hex_to_rgb(SWS_NAVY))

    f_small = _font(7, bold=False)
    centre = f"{pack_code} · Page {int(page_num)} of {int(total_pages)}"
    cw, ch = _measure(d, centre, f_small)
    _txt(d, ((w - cw) // 2, footer_y + (footer_h - ch) // 2), centre, fill=(200, 220, 218), font=f_small)

    right2 = f"© {COPYRIGHT_YEAR} Small Wins Studio · PCS® with active PCS Maker Personal License"
    rw, rh = _measure(d, right2, f_small)
    _txt(d, (w - rw - int(0.40 * DPI), footer_y + (footer_h - rh) // 2), right2, fill=(200, 220, 218), font=f_small)

    x = int(0.40 * DPI)
    if strand_keys:
        for sk in strand_keys:
            labels, _tier = STRAND_PILLS.get(sk, ([sk], ""))
            for i, lbl in enumerate(labels):
                color = LEVEL_VIOLET if i == 0 else LEVEL_OCEAN  # simple alternating default
                x += _draw_strand_pill(d, x, footer_y + int(0.12 * DPI), lbl, color) + int(0.10 * DPI)

    if show_data_strip:
        draw_data_strip(page)
