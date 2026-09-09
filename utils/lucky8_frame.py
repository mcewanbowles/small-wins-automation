from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

try:
    # Canonical brand tokens
    from utils.UNIVERSAL_STANDARDS import (
        SWS_TEAL,
        SWS_NAVY,
        SWS_GOLD,
        SWS_TEAL_LT,
        MID_GRAY,
        LEVEL_VIOLET,
        LEVEL_OCEAN,
        LEVEL_EMERALD,
        LEVEL_ROSE,
        COPYRIGHT_YEAR,
    )
except Exception:
    # Safe fallbacks if standards are unavailable at import time
    SWS_TEAL = "#31A8A0"
    SWS_NAVY = "#0D2545"
    SWS_GOLD = "#E1B42D"
    SWS_TEAL_LT = "#E8F8F8"
    MID_GRAY = "#E5E7EB"
    LEVEL_VIOLET = "#7C3AED"
    LEVEL_OCEAN = "#0284C7"
    LEVEL_EMERALD = "#059669"
    LEVEL_ROSE = "#E11D48"
    COPYRIGHT_YEAR = datetime.now().year

DPI = 300

LEVEL_NAME = {1: "Supported", 2: "Developing", 3: "Independent", 4: "Extended"}
LEVEL_COLOUR = {1: LEVEL_VIOLET, 2: LEVEL_OCEAN, 3: LEVEL_EMERALD, 4: LEVEL_ROSE}


def px(pt: float, dpi: int = DPI) -> int:
    return int(round(pt * dpi / 72.0))


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Fonts: Prefer brand fonts from assets/branding/fonts; fallback gracefully
_DEF_ROOT = Path(__file__).resolve().parents[1]
_BRAND_FONTS = _DEF_ROOT / "assets" / "branding" / "fonts"


def _load_font(name: str, pt: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    size = max(1, px(pt))
    preferred = []
    if name.lower() == "title":
        preferred = [
            _BRAND_FONTS / "Poppins-Bold.ttf",
            _BRAND_FONTS / "Poppins-SemiBold.ttf",
            _BRAND_FONTS / "Poppins-Medium.ttf",
        ]
    elif name.lower() in {"meta", "footer", "body", "pill"}:
        preferred = [
            _BRAND_FONTS / ("Poppins-Bold.ttf" if bold else "Poppins-Regular.ttf"),
            _BRAND_FONTS / ("Poppins-SemiBold.ttf" if bold else "Poppins-Medium.ttf"),
        ]

    # OS fallbacks
    fallbacks = [
        Path("C:/Windows/Fonts/arialbd.ttf") if bold else Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") if bold else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]

    for p in list(map(Path, preferred)) + fallbacks:
        try:
            if p and p.exists():
                return ImageFont.truetype(str(p), size)
        except Exception:
            continue
    # Final safety
    return ImageFont.load_default()


def _measure(d: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bb = d.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def _txt(d: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, *, fill: str | tuple[int, int, int], font: ImageFont.ImageFont) -> None:
    d.text(xy, text, fill=fill, font=font)


def apply_lucky8_frame(
    page: Image.Image,
    *,
    activity_name: str,
    book_title: str,
    pack_code: str,
    page_num: int,
    total_pages: int,
    level: Optional[int] = None,
    show_icon_row: bool = False,
    fill_background: bool = False,
    book_cover: Optional[Image.Image] = None,
    subtitle_text: Optional[str] = None,
    accent_text: Optional[str] = None,
    show_level_badge: bool = False,
) -> None:
    """
    Apply the Lucky 8 universal page frame (header strip, border, footer) to an existing page image.
    This function assumes content may already be drawn. To avoid occlusion, background fill is off by default.
    The footer text is built as one f-string with explicit numeric coercion to avoid glyph concatenation bugs.
    """
    w, h = page.size
    d = ImageDraw.Draw(page)

    # Optional interior background fill (disabled by default to avoid covering existing content)
    if fill_background:
        d.rounded_rectangle([px(26), px(26), w - px(26), h - px(26)], radius=px(14), fill=_hex_to_rgb(SWS_TEAL_LT))

    # Border outline
    d.rounded_rectangle([px(26), px(26), w - px(26), h - px(26)], radius=px(14), outline=_hex_to_rgb(SWS_TEAL), width=px(5))

    # Header: teal strip inside border with rounded corners and interior padding
    header_pad_x = px(14)
    header_pad_y = px(14)
    header_top = px(26) + header_pad_y
    header_h = px(88)
    f_title = _load_font("title", 26, bold=True)
    f_meta = _load_font("meta", 13, bold=False)
    f_sub = _load_font("meta", 10, bold=False)
    d.rounded_rectangle([px(26) + header_pad_x, header_top, w - px(26) - header_pad_x, header_top + header_h], radius=px(14), fill=_hex_to_rgb(SWS_TEAL))

    # Optional small hero/cover icon on the left inside the strip (bigger)
    # Size the icon relative to the banner height with a small vertical margin
    cover_side = max(px(48), header_h - px(20))
    cover_gap = px(12)
    cursor_left = px(26) + header_pad_x + px(14)
    if book_cover is not None:
        try:
            cov = book_cover.convert("RGBA").copy()
            cov.thumbnail((cover_side, cover_side), Image.Resampling.LANCZOS)
            page.paste(cov, (cursor_left, header_top + (header_h - cov.height) // 2), cov)
        except Exception:
            pass

    # Centered activity title and book title (title higher, book title lower inside the banner)
    title_main = activity_name or "Activity"
    tm_w, tm_h = _measure(d, title_main, f_title)
    bt_w = bt_h = 0
    gap = px(12)
    if book_title:
        bt_w, bt_h = _measure(d, book_title, f_meta)
    title_y = header_top + px(12)
    _txt(d, ((w - tm_w) // 2, title_y), title_main, fill=(255, 255, 255), font=f_title)
    if book_title:
        book_y = header_top + header_h - px(28) - bt_h
        _txt(d, ((w - bt_w) // 2, book_y), book_title, fill=(240, 255, 253), font=f_meta)

    # Right-aligned level pill (suppressed by default)
    lvl_name = LEVEL_NAME.get(level or 0, "")
    if show_level_badge and lvl_name:
        pad_x = px(10)
        pill_h = max(px(22), int(header_h * 0.60))
        lw, lh = _measure(d, lvl_name, f_meta)
        pill_w = lw + pad_x * 2
        pill_x2 = w - px(26) - header_pad_x - px(10)
        pill_x1 = pill_x2 - pill_w
        pill_y1 = header_top + (header_h - pill_h) // 2
        pill_y2 = pill_y1 + pill_h
        d.rounded_rectangle([pill_x1, pill_y1, pill_x2, pill_y2], radius=int(pill_h / 2), fill=_hex_to_rgb(LEVEL_COLOUR.get(level or 0, LEVEL_VIOLET)))
        _txt(d, (pill_x1 + pad_x, pill_y1 + (pill_h - lh) // 2), lvl_name, fill=(255, 255, 255), font=f_meta)

    # Subtitle just below strip (e.g., "Match Stellaluna")
    below_y = header_top + header_h
    if subtitle_text:
        sw, sh = _measure(d, subtitle_text, f_sub)
        _txt(d, ((w - sw) // 2, below_y + px(12)), subtitle_text, fill=_hex_to_rgb(SWS_NAVY), font=f_sub)
        below_y += px(12) + sh

    # Thin rule under header group
    rule_y = below_y + px(12)
    d.line([px(26) + px(8), rule_y, w - px(26) - px(8), rule_y], fill=_hex_to_rgb(MID_GRAY), width=max(1, int(DPI / 144)))

    # Footer (no coloured bar) — both lines centered with safe padding
    f_footer = _load_font("footer", 8, bold=False)
    f_footer_small = _load_font("footer", 7, bold=False)

    line2_y = h - px(26) - px(16)
    line1_y = line2_y - px(14)

    # First line: centered meta with page count inline
    lvl_txt = f"Level {int(level)}" if isinstance(level, int) and level > 0 else None
    parts = [p for p in [book_title, lvl_txt, pack_code, f"Page {int(page_num)}/{int(total_pages)}"] if p and str(p).strip()]
    first_line = " | ".join(parts)
    fl_w, fl_h = _measure(d, first_line, f_footer)
    _txt(d, ((w - fl_w) // 2, line1_y), first_line, fill=_hex_to_rgb(SWS_NAVY), font=f_footer)

    # Second line: copyright/PCS credit, small (sample style)
    credit = f"PCS® symbols used with active PCS Maker Personal License. © {COPYRIGHT_YEAR} Small Wins Studio"
    cr_w, cr_h = _measure(d, credit, f_footer_small)
    _txt(d, ((w - cr_w) // 2, line2_y), credit, fill=_hex_to_rgb(SWS_NAVY), font=f_footer_small)

    # Optional icon row placeholder (no-op by default)
    if show_icon_row:
        pass
