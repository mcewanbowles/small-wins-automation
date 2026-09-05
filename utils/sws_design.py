from __future__ import annotations



from typing import Optional

from datetime import datetime



from PIL import Image, ImageDraw, ImageFont

import os

import sys

from pathlib import Path

import warnings

import math



DPI = 300



# Universal standards (single source of truth)

try:

    from utils.UNIVERSAL_STANDARDS import (

        BRAND_TEAL as US_BRAND_TEAL,

        BRAND_NAVY as US_BRAND_NAVY,

        STEEL_BLUE as US_STEEL_BLUE,

        SWS_TEAL_LT as US_SWS_TEAL_LT,

        LEVEL_1_GREEN, LEVEL_2_BLUE, LEVEL_3_AMBER, LEVEL_4_CORAL,

        BORDER_RADIUS_PT, FOOTER_BORDER_CLEARANCE, COPYRIGHT_YEAR as US_COPYRIGHT_YEAR,

        HEADER_ALWAYS_TEAL,

        STRAND_PILLS,

    )

    US_FALLBACK_ACTIVE = False

except Exception as e:

    # Loud but non-fatal fallback to keep builds running while surfacing issues

    warnings.warn(

        "UNIVERSAL_STANDARDS import failed; using safe fallback brand tokens. "

        f"This may not perfectly match brand specs. Error: {e}"

    )

    US_FALLBACK_ACTIVE = True

    # Safe fallback tokens (approximate brand values)

    US_BRAND_TEAL = "#31A8A0"

    US_BRAND_NAVY = "#0D2545"

    US_STEEL_BLUE = "#B0C4DE"

    US_SWS_TEAL_LT = "#E8F8F8"

    LEVEL_1_GREEN = "#5BBE72"

    LEVEL_2_BLUE = "#4AA3DF"

    LEVEL_3_AMBER = "#F2B441"

    LEVEL_4_CORAL = "#EF6A62"

    BORDER_RADIUS_PT = 12

    FOOTER_BORDER_CLEARANCE = 8

    US_COPYRIGHT_YEAR = str(datetime.now().year)

    HEADER_ALWAYS_TEAL = True

    STRAND_PILLS = {}



# Matching design constants (mapped to universal)

LIGHT_BLUE_BORDER_HEX = US_BRAND_TEAL

NAVY_HEX = US_BRAND_NAVY

WARM_ORANGE_HEX = "#F5A623"

DEFAULT_ACCENT_TEAL_HEX = US_BRAND_TEAL

SUBTITLE_DARK_GRAY = (51, 51, 51)



LEVEL_COLORS = {

    1: LEVEL_1_GREEN,

    2: LEVEL_2_BLUE,

    3: LEVEL_3_AMBER,

    4: LEVEL_4_CORAL,

}



SAFE_FOOTER_INSET_INCH = 0.80

ROW_GAP_INCH = 0.20



def _inch_to_px(inches: float) -> int:

    return int(round(inches * DPI))



def safe_footer_inset_px() -> int:

    return _inch_to_px(SAFE_FOOTER_INSET_INCH)



def row_gap_px() -> int:

    return _inch_to_px(ROW_GAP_INCH)



_FONT_COMIC = "C:/Windows/Fonts/comic.ttf"

_FONT_COMIC_BOLD = "C:/Windows/Fonts/comicbd.ttf"

_FONT_ARIAL = "C:/Windows/Fonts/arial.ttf"

_FONT_ARIAL_BOLD = "C:/Windows/Fonts/arialbd.ttf"





def _brand_font_pt(pt_size: int, *, bold: bool = False, brand: str | None = None) -> ImageFont.ImageFont:

    scale = DPI / 72

    px = int(pt_size * scale)

    brand_pref = (brand or os.environ.get("SWS_FONT") or "poppins").strip().lower()

    search_dirs: list[Path] = []

    if os.environ.get("SWS_FONT_DIR"):

        search_dirs.append(Path(os.environ["SWS_FONT_DIR"]))

    search_dirs.extend([

        Path(__file__).resolve().parents[1] / "assets" / "branding" / "fonts",

        Path(__file__).resolve().parents[1] / "Studioforge" / "Accurate generators" / "Internal covers",

        Path(__file__).resolve().parents[1] / "fonts",  # repo-root fonts folder

        Path("C:/Windows/Fonts"),

        Path("/Library/Fonts"),

        Path("/usr/share/fonts/truetype"),

        Path("/usr/share/fonts"),

    ])



    def find(names: list[str]) -> str | None:

        for d in search_dirs:

            try:

                for nm in names:

                    p = d / nm

                    if p.exists():

                        return str(p)

            except Exception:

                continue

        return None



    stacks = {

        "poppins": {

            True: ["Poppins-Bold.ttf", "Poppins-SemiBold.ttf", "Poppins-Medium.ttf"],

            False: ["Poppins-Regular.ttf", "Poppins-Medium.ttf", "Poppins-Light.ttf"],

        },

        "nunito": {

            True: ["Nunito-Bold.ttf", "Nunito-SemiBold.ttf", "Nunito-ExtraBold.ttf"],

            False: ["Nunito-Regular.ttf", "Nunito-Medium.ttf", "Nunito-Light.ttf"],

        },

        "comic": {

            True: ["comicbd.ttf"],

            False: ["comic.ttf"],

        },

        "arial": {

            True: ["arialbd.ttf"],

            False: ["arial.ttf"],

        },

        "dejavu": {

            True: ["DejaVuSans-Bold.ttf"],

            False: ["DejaVuSans.ttf"],

        },

        "noto": {

            True: ["NotoSans-Bold.ttf"],

            False: ["NotoSans-Regular.ttf"],

        },

    }



    for brand in [brand_pref, "arial", "dejavu", "noto", "comic"]:

        cand = stacks.get(brand, {}).get(bold, [])

        fp = find(cand)

        if fp:

            try:

                return ImageFont.truetype(fp, px)

            except Exception:

                pass

    return ImageFont.load_default()





def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:

    h = hex_color.lstrip("#")

    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))





def _load_fonts(*, title_pt: int, body_pt: int, small_pt: int) -> dict[str, ImageFont.ImageFont]:

    return {

        "title": _brand_font_pt(title_pt, bold=True, brand="poppins"),

        "body": _brand_font_pt(body_pt, bold=False, brand="poppins"),

        "small": _brand_font_pt(small_pt, bold=False, brand="poppins"),

        "small_bold": _brand_font_pt(small_pt, bold=True, brand="poppins"),

    }





def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:

    bbox = draw.textbbox((0, 0), text, font=font)

    return (bbox[2] - bbox[0], bbox[3] - bbox[1])





def normalize_text(s: str | None) -> str:

    if not s:

        return ""

    t = str(s)

    # Replace curly quotes/dashes and non-breaking/zero-width spaces

    repl = {

        "\u2018": "'", "\u2019": "'", "\u201C": '"', "\u201D": '"',

        "\u2013": "-", "\u2014": "-",

        "\xa0": " ", "\u200b": "", "\u200c": "", "\u200d": "",

    }

    for k, v in repl.items():

        t = t.replace(k, v)

    # Collapse whitespace

    t = " ".join(t.split())

    return t.strip()




def resolve_theme_assets(theme_slug: str) -> tuple[Image.Image | None, str | None, str | None]:
    base = Path(__file__).resolve().parents[1] / "assets" / "themes" / theme_slug
    hero_path = None
    for hp in [
        base / "hero_header.png",
        base / "heroes" / "hero_header.png",
        base / "characters" / "hero_header.png",
        base / "hero.png",
        base / "heroes" / "hero.png",
        base / "characters" / "hero.png",
        base / "header_icon.png",
    ]:
        if hp.exists():
            hero_path = hp
            break
    hero_img = None
    if hero_path and hero_path.exists():
        try:
            im = Image.open(hero_path)
            hero_img = im.convert("RGBA") if im.mode != "RGBA" else im
        except Exception:
            hero_img = None
    book_cover_path = None
    for sd in [base, base / "covers", base / "images", base / "marketing", base / "book"]:
        for nm in ["book_cover", "cover", "front_cover", "bookfront", "book", "cover_reference"]:
            for ex in ["png", "jpg", "jpeg", "webp"]:
                fp = sd / f"{nm}.{ex}"
                if fp.exists():
                    book_cover_path = str(fp)
                    break
            if book_cover_path:
                break
        if book_cover_path:
            break
    return hero_img, (str(hero_path) if hero_path else None), book_cover_path


def resolve_theme_assets_from_images_folder(images_folder: str) -> tuple[Image.Image | None, str | None, str | None]:
    try:
        slug = Path(images_folder).resolve().parent.name
    except Exception:
        slug = ""
    return resolve_theme_assets(slug) if slug else (None, None, None)


def _shrink_font_to_fit(

    text: str,

    *,

    base_pt: int,

    max_width_px: int,

    bold: bool,

    brand: str,

    min_pt: int = 8,

) -> ImageFont.ImageFont:

    """Return a font that fits text within max_width_px by shrinking down from base_pt."""

    meas = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    for pt in range(base_pt, max(min_pt, base_pt - 80), -1):

        f = _brand_font_pt(pt, bold=bold, brand=brand)

        w, _ = _text_size(meas, text, f)

        if w <= max_width_px:

            return f

    return _brand_font_pt(min_pt, bold=bold, brand=brand)





def shrink_font_to_fit_with_pt(

    text: str,

    *,

    base_pt: int,

    max_width_px: int,

    bold: bool,

    brand: str,

    min_pt: int = 8,

) -> tuple[ImageFont.ImageFont, int]:

    meas = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    for pt in range(base_pt, max(min_pt, base_pt - 80), -1):

        f = _brand_font_pt(pt, bold=bold, brand=brand)

        w, _ = _text_size(meas, text, f)

        if w <= max_width_px:

            return f, pt

    return _brand_font_pt(min_pt, bold=bold, brand=brand), min_pt





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





def _draw_dot_bullet(d: ImageDraw.ImageDraw, *, x: int, y_baseline: int, color: tuple[int, int, int], r: int) -> None:

    # Nudge 1px closer to baseline for tighter alignment with text
    cy = y_baseline - r - 1

    d.ellipse([x, cy - r, x + 2 * r, cy + r], fill=color)





def _draw_chevron_bullet(d: ImageDraw.ImageDraw, *, x: int, y_baseline: int, color: tuple[int, int, int], size: int) -> None:

    cy = y_baseline - size // 2 - 2

    d.line([(x, cy - size // 2), (x + size // 2, cy), (x, cy + size // 2)], fill=color, width=max(2, size // 3), joint="curve")





def _draw_scarborough_rope(d: ImageDraw.ImageDraw, *, x: int, y: int, w: int, h: int, highlighted_strand: str, teal: tuple[int, int, int], muted: tuple[int, int, int]) -> None:

    # Braided two-strand rope representation (Word Recognition vs Language Comprehension)

    # Draws interleaved diagonal bands to emulate braid; active strand uses teal and thicker bands.

    def _color_scale(rgb: tuple[int, int, int], s: float) -> tuple[int, int, int]:

        r, g, b = rgb

        return (max(0, min(255, int(r * s))), max(0, min(255, int(g * s))), max(0, min(255, int(b * s))))



    pad_x = max(4, int(0.04 * w))

    gap_y = max(2, int(0.02 * h))

    band_h = (h - gap_y) // 2

    # Top band and bottom band regions

    bands = [

        ("Word Recognition", y, y + band_h),

        ("Language Comprehension", y + band_h + gap_y, y + h),

    ]

    tiles = max(10, int(w / 28))

    for name, y1, y2 in bands:

        active = (name == highlighted_strand)

        base = teal if active else muted

        alt = _color_scale(base, 0.85)

        alt2 = _color_scale(base, 1.15 if active else 0.75)

        band_w = y2 - y1

        tile_w = max(8, int((w - pad_x * 2) / tiles))

        # Background to soften edges

        d.rounded_rectangle([x, y1, x + w, y2], radius=int(band_w * 0.15), fill=None, outline=None, width=0)

        # Draw interleaved diagonal ribbons across the band

        for i in range(tiles + 2):

            tx = x + pad_x + i * tile_w

            # Ribbon A (\ direction)

            cA = base if i % 2 == 0 else alt

            pA = [

                (tx - tile_w * 0.2, y2),

                (tx + tile_w * 0.55, y1),

                (tx + tile_w * 0.55 + band_w * 0.18, y1),

                (tx + band_w * 0.18, y2),

            ]

            d.polygon(pA, fill=cA)

            # Ribbon B (/ direction), drawn after to simulate over/under weave

            cB = alt2 if i % 2 == 0 else base

            tb = tx + tile_w * 0.5

            pB = [

                (tb - band_w * 0.18, y1),

                (tb + tile_w * 0.2, y2),

                (tb + tile_w * 0.2 + band_w * 0.18, y2),

                (tb + band_w * 0.18, y1),

            ]

            d.polygon(pB, fill=cB)

        # Edge mask lines for clarity

        edge_c = _color_scale(base, 0.7)

        d.line([(x + pad_x, y1 + 1), (x + w - pad_x, y1 + 1)], fill=edge_c, width=max(1, int(band_w * 0.06)))

        d.line([(x + pad_x, y2 - 1), (x + w - pad_x, y2 - 1)], fill=edge_c, width=max(1, int(band_w * 0.06)))





def apply_small_wins_frame(

    page: Image.Image,

    *,

    product_title: str,

    subtitle: str,

    instruction_text: Optional[str] = None,

    pack_code: str,

    page_num: int,

    total_pages: int,

    level: Optional[int] = None,

    accent_color_hex: str | None = None,

    footer_title: str | None = None,

    copyright_year: Optional[int] = None,

    header_left_icon: Image.Image | None = None,

    header_left_icon_flip: bool = False,

    header_left_icon_y_offset_px: int = 0,

    footer_y_offset_px: int = 0,

    header_height_px: int | None = None,

    draw_accent_strip: bool = True,

    draw_header: bool = True,

    draw_subtitle: bool = True,

    draw_footer: bool = True,
    draw_pcs_line: bool = True,

    footer_compact: bool = False,

    strand_key: Optional[str] = None,

    show_data_strip: bool = False,

    accent_margin_px: int | None = None,

) -> None:

    w, h = page.size

    d = ImageDraw.Draw(page)



    fonts = _load_fonts(title_pt=24, body_pt=14, small_pt=10)



    border_margin = int(0.25 * DPI)

    # Match ReportLab 3pt stroke used on activity pages.

    border_w = max(3, int(round(3 * (DPI / 72))))

    # Use universal border radius in pt

    border_r = int((BORDER_RADIUS_PT or 14) * (DPI / 72))

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

    has_instruction = False

    if instruction_text is not None:

        itxt = normalize_text(instruction_text)

        has_instruction = len(itxt) > 0

    accent_margin = int(0.08 * DPI) if accent_margin_px is None else int(accent_margin_px)

    accent_x1 = border_margin + accent_margin

    accent_y1 = border_margin + accent_margin

    accent_x2 = w - border_margin - accent_margin

    accent_y2 = accent_y1 + header_h

    if draw_accent_strip:

        # Header must always be teal per universal standard

        if accent_color_hex and not HEADER_ALWAYS_TEAL:

            accent_fill = hex_to_rgb(accent_color_hex)

        else:

            accent_fill = hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX)

        d.rounded_rectangle(

            [accent_x1, accent_y1, accent_x2, accent_y2],

            radius=int(0.12 * DPI),

            fill=accent_fill,

            outline=None,

        )



    # Optional level badge: flat rounded-rectangle in the header's top-right.

    # Simpler, on-brand, and fully contained within the accent stripe.

    badge_bounds = None

    if draw_accent_strip and level is not None:

        try:

            lvl_hex = LEVEL_COLORS.get(int(level))

        except Exception:

            lvl_hex = None

        if lvl_hex:

            lvl_fill = hex_to_rgb(lvl_hex)

            H = max(1, (accent_y2 - accent_y1))

            pad_x = int(0.18 * DPI)

            pad_y = int(0.16 * DPI)

            badge_h = int(max(18, H * 0.44))

            # Width sized to message with comfortable side padding

            try:

                lbl = f"Level {int(level)}"

            except Exception:

                lbl = str(level)

            fnt = _shrink_font_to_fit(lbl, base_pt=14, max_width_px=max(40, int((accent_x2 - accent_x1) * 0.44)), bold=True, brand="poppins")

            # Measure precise glyph box to center text optically within the pill
            _meas = ImageDraw.Draw(Image.new("RGB", (10, 10)))
            bb = _meas.textbbox((0, 0), lbl, font=fnt)
            tw = max(0, (bb[2] - bb[0]))
            th = max(0, (bb[3] - bb[1]))

            side_pad = int(badge_h * 0.40)

            badge_w = max(tw + side_pad * 2, int(badge_h * 2.2))

            bx2 = accent_x2 - pad_x

            bx1 = max(accent_x1 + pad_x, bx2 - badge_w)

            by1 = accent_y1 + pad_y

            by2 = min(accent_y2 - pad_y, by1 + badge_h)

            # Draw badge

            try:

                ImageDraw.Draw(page).rounded_rectangle([bx1, by1, bx2, by2], radius=int(badge_h * 0.4), fill=lvl_fill)

            except Exception:

                ImageDraw.Draw(page).rectangle([bx1, by1, bx2, by2], fill=lvl_fill)

            # Text centered both axes for optical balance

            r_, g_, b_ = lvl_fill

            luma = (0.299 * r_ + 0.587 * g_ + 0.114 * b_) / 255.0

            txt_rgb = hex_to_rgb(NAVY_HEX) if luma >= 0.75 else (255, 255, 255)

            # Offset by bbox origin to counter ascender/descender bearings for exact centering
            tx = bx1 + (bx2 - bx1 - tw) // 2 - bb[0]

            ty = by1 + (by2 - by1 - th) // 2 - bb[1]

            d.text((tx, ty), lbl, fill=txt_rgb, font=fnt)

            badge_bounds = (bx1, by1, bx2, by2)



    icon_right_edge = None

    if draw_accent_strip and header_left_icon is not None:

        icon = _make_near_white_transparent(header_left_icon.copy())

        if header_left_icon_flip:

            icon = icon.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        target_h = int(header_h * 0.78)

        icon.thumbnail((target_h * 2, target_h), Image.Resampling.LANCZOS)

        icon_x = accent_x1 + int(0.18 * DPI)

        icon_y = accent_y1 + (header_h - icon.height) // 2 + int(header_left_icon_y_offset_px)

        page.paste(icon, (icon_x, icon_y), icon)

        icon_right_edge = icon_x + icon.width



    # Usable width for header texts inside the accent stripe

    inner_margin = int(0.18 * DPI)

    usable_w = max(1, (accent_x2 - accent_x1) - inner_margin * 2)



    if draw_header:

        product_title = normalize_text(product_title)

        # Safe span excludes left icon and right level badge

        safe_left = accent_x1 + inner_margin

        try:

            if icon_right_edge:

                safe_left = max(safe_left, icon_right_edge + inner_margin)

        except Exception:

            pass

        safe_right = accent_x2 - inner_margin

        try:

            if badge_bounds:

                bx1, by1, bx2, by2 = badge_bounds

                safe_right = min(safe_right, bx1 - inner_margin)

        except Exception:

            pass

        safe_width = max(1, safe_right - safe_left)

        title_font = _shrink_font_to_fit(

            product_title,

            base_pt=24,

            max_width_px=safe_width,

            bold=True,

            brand="poppins",

        )

        tw, th = _text_size(d, product_title, title_font)

        title_x = safe_left + max(0, (safe_width - tw) // 2)



        if draw_subtitle and draw_accent_strip and subtitle:

            subtitle = normalize_text(subtitle)

            subtitle_font = _shrink_font_to_fit(

                subtitle,

                base_pt=14,

                max_width_px=safe_width,

                bold=True,

                brand="poppins",

            )

            sw, sh = _text_size(d, subtitle, subtitle_font)

            gap = max(1, int(header_h * 0.12))

            block_h = th + gap + sh

            block_y0 = accent_y1 + max(0, (header_h - block_h) // 2)

            title_y = block_y0

            sub_y = title_y + th + gap

            d.text((title_x, title_y), product_title, fill=(255, 255, 255), font=title_font)

            sub_x = safe_left + max(0, (safe_width - sw) // 2)

            d.text((sub_x, sub_y), subtitle, fill=hex_to_rgb(NAVY_HEX), font=subtitle_font)

        else:

            # Center vertically within the accent stripe.

            title_y = accent_y1 + (header_h - th) // 2

            d.text((title_x, title_y), product_title, fill=(255, 255, 255), font=title_font)



    elif draw_subtitle:

        # Subtitle without header (or without accent strip)

        sub_y = int(0.75 * DPI)

        subtitle = normalize_text(subtitle)

        subtitle_font = _shrink_font_to_fit(

            subtitle,

            base_pt=14,

            max_width_px=usable_w,

            bold=True,

            brand="poppins",

        )

        sw, sh = _text_size(d, subtitle, subtitle_font)

        d.text(((w - sw) // 2, sub_y), subtitle, fill=hex_to_rgb(NAVY_HEX), font=subtitle_font)



    # Instruction line sits BELOW the accent strip with padding, not inside it

    if has_instruction and draw_accent_strip:

        inst = normalize_text(instruction_text)

        inst_font = _shrink_font_to_fit(

            inst,

            base_pt=12,

            max_width_px=usable_w,

            bold=True,

            brand="poppins",

        )

        iw, ih = _text_size(d, inst, inst_font)

        inst_y = accent_y2 + int(0.14 * DPI)

        d.text(((w - iw) // 2, inst_y), inst, fill=hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX), font=inst_font)



    if draw_footer:

        # Build top footer line parts cleanly to avoid stray separators

        parts: list[str] = []

        footer_product = (footer_title if footer_title is not None else product_title) or ""
        # Sanitize: remove any 'Adapted Activities Bundle' token from footer product line
        try:
            _tokens = [seg.strip() for seg in str(footer_product).split("|")]
        except Exception:
            _tokens = [str(footer_product).strip()]
        _tokens = [t for t in _tokens if t and t.lower() != "adapted activities bundle"]
        footer_product = " | ".join(_tokens).strip()

        if footer_product.strip():

            parts.append(footer_product.strip())

        if isinstance(pack_code, str) and pack_code.strip():

            parts.append(pack_code.strip())

        # Top footer line: product [+ CODE]; page number handled separately

        footer_line_1 = " | ".join(parts)

        _yr = copyright_year if copyright_year is not None else US_COPYRIGHT_YEAR

        footer_line_2 = (
            f"PCS symbols used with active PCS Maker Personal License. | "
            f"© {_yr} Small Wins Studio"
        ) if draw_pcs_line else ""



        # Keep the footer visually close to the bottom border while ensuring it never

        # touches the border stroke. Some products (e.g., Bingo) may need this nudged

        # upward further.

        # Enforce minimum clearance from inner border edge

        clearance_px = int(max(FOOTER_BORDER_CLEARANCE, 12) * (DPI / 72))

        y2 = h - border_margin - clearance_px - int(footer_y_offset_px)

        y1 = y2 - int(0.14 * DPI)



        # Optional data strip above footer

        if show_data_strip:

            ds_gap = int(0.10 * DPI)

            ds_h = int(40 if DPI >= 300 else 20)

            ds_y2 = y1 - ds_gap

            ds_y1 = max(border_margin + 1, ds_y2 - ds_h)

            try:

                ds_fill = hex_to_rgb(US_SWS_TEAL_LT)

            except Exception:

                ds_fill = (232, 248, 248)

            d.rectangle([border_margin, ds_y1, w - border_margin, ds_y2], fill=ds_fill)

            ds_text = "Name: ____________  Date: _________  Level: (1) (2) (3) (4)  Prompt: I  G  V  M  P"

            fw_ds, fh_ds = _text_size(d, ds_text, fonts["small"])

            tx = border_margin + int(0.18 * DPI)

            ty = ds_y1 + (ds_h - fh_ds) // 2

            d.text((tx, ty), ds_text, fill=(153, 153, 153), font=fonts["small"])



        # Paint mask behind footer to ensure content never bleeds through

        try:

            pad_top = int(0.10 * DPI)

            pad_bot = int(0.24 * DPI)

            d.rectangle([border_margin, max(border_margin, y1 - pad_top), w - border_margin, min(h - border_margin, y2 + pad_bot)], fill=(255, 255, 255))

        except Exception:

            pass



        # Footer fonts: top 9pt bold, bottom 8pt regular

        footer1_font = _brand_font_pt(9, bold=True, brand="poppins")

        footer2_font = _brand_font_pt(8, bold=False, brand="poppins")

        fw1, fh1 = _text_size(d, footer_line_1, footer1_font)

        fw2, fh2 = _text_size(d, footer_line_2, footer2_font)

        # Load logo once for potential use beside the bottom PCS/brand line
        logo = None
        try:
            logo_candidates = [
                Path(__file__).resolve().parents[1] / "assets" / "branding" / "logos" / "logo_transparent.png",
                Path(__file__).resolve().parents[1] / "assets" / "branding" / "logos" / "small_wins_logo_with_text.png",
                Path(__file__).resolve().parents[1] / "Studioforge" / "Accurate generators" / "Internal covers" / "logo_transparent.png",
            ]
            for _lp in logo_candidates:
                if _lp.exists():
                    iml = Image.open(str(_lp))
                    logo = iml.convert("RGBA") if iml.mode != "RGBA" else iml
                    break
        except Exception:
            logo = None

        page_text = None

        if isinstance(page_num, int) and isinstance(total_pages, int) and page_num > 0 and total_pages > 0:

            page_text = f"Page {page_num}/{total_pages}"

        # Gold standard: Find & Cover Level 2 uses light grey for BOTH footer lines.

        footer_grey = (153, 153, 153)  # #999999



        # Optional left-aligned strand pill

        if False and isinstance(strand_key, str) and strand_key.strip():

            pill_h = int(0.22 * DPI)

            pill_y = y1 + ((y2 - y1) - pill_h) // 2

            pill_x1 = border_margin

            pill_x2 = pill_x1 + int(1.8 * DPI)

            try:

                meta = STRAND_PILLS.get(strand_key.upper()) or STRAND_PILLS.get(strand_key)

            except Exception:

                meta = None

            pill_fill = hex_to_rgb(US_BRAND_TEAL)

            d.rounded_rectangle([pill_x1, pill_y, pill_x2, pill_y + pill_h], radius=int(0.20 * pill_h), fill=pill_fill)

            try:

                lbl = (meta[0][0] if isinstance(meta, tuple) and meta and isinstance(meta[0], list) and meta[0] else "Strand").strip()

            except Exception:

                lbl = "Strand"

            avail_w = max(10, pill_x2 - pill_x1 - int(0.18 * DPI))

            _lbl_font = _shrink_font_to_fit(lbl, base_pt=10, max_width_px=avail_w, bold=True, brand="poppins")

            lw, lh = _text_size(d, lbl, _lbl_font)

            d.text((pill_x1 + (pill_x2 - pill_x1 - lw) // 2, pill_y + (pill_h - lh) // 2), lbl, fill=(255, 255, 255), font=_lbl_font)



        if footer_compact:

            # Single-line footer: Level + pack code + PCS/copyright

            lvl_txt = f"Level {int(level)}" if isinstance(level, int) else ""

            compact_prefix = pack_code.strip() if isinstance(pack_code, str) and pack_code.strip() else ""

            bits = [b for b in [lvl_txt, compact_prefix, footer_line_2] if b]

            one_line = " | ".join(bits)

            ow, oh = _text_size(d, one_line, footer2_font)

            d.text(((w - ow) // 2, y2), one_line, fill=footer_grey, font=footer2_font)

        else:

            # Top line: product/code only, centered text (no logo here)
            d.text(((w - fw1) // 2, y1), footer_line_1, fill=footer_grey, font=footer1_font)

            # Bottom line: PCS + © Small Wins Studio — place logo immediately to the RIGHT of the brand phrase; center as a group
            if draw_pcs_line and footer_line_2:
                gap_fx = int(0.02 * DPI)
                if logo is not None:
                    lg = logo.copy()
                    tgt_h = max(1, int(fh2 * 2.3))
                    try:
                        lg.thumbnail((tgt_h * 3, tgt_h), Image.Resampling.LANCZOS)
                    except Exception:
                        pass
                    lw, lh = lg.size
                    brand_phrase = "Small Wins Studio"
                    idx = footer_line_2.lower().find(brand_phrase.lower())
                    if idx >= 0:
                        pre = footer_line_2[:idx]
                        brand_txt = footer_line_2[idx: idx + len(brand_phrase)]
                        post = footer_line_2[idx + len(brand_phrase):]
                        pre_w, _ = _text_size(d, pre, footer2_font)
                        brand_w, _ = _text_size(d, brand_txt, footer2_font)
                        post_w, _ = _text_size(d, post, footer2_font)
                        total_w_grp = pre_w + brand_w + gap_fx + lw + post_w
                        gx = (w - total_w_grp) // 2
                        # Draw prefix
                        d.text((gx, y2), pre, fill=footer_grey, font=footer2_font)
                        # Draw brand phrase immediately after prefix
                        bx = gx + pre_w
                        d.text((bx, y2), brand_txt, fill=footer_grey, font=footer2_font)
                        # Draw logo immediately to the right of 'Small Wins Studio'
                        gy = y2 + int((fh2 - lh) // 2)
                        try:
                            page.paste(lg, (bx + brand_w + gap_fx, gy), lg)
                        except Exception:
                            pass
                        # Draw suffix after logo
                        sx = bx + brand_w + gap_fx + lw
                        d.text((sx, y2), post, fill=footer_grey, font=footer2_font)
                    else:
                        # Fallback: draw entire line text, then logo to the right
                        total_w_grp = fw2 + gap_fx + lw
                        gx = (w - total_w_grp) // 2
                        d.text((gx, y2), footer_line_2, fill=footer_grey, font=footer2_font)
                        gy = y2 + int((fh2 - lh) // 2)
                        try:
                            page.paste(lg, (gx + fw2 + gap_fx, gy), lg)
                        except Exception:
                            pass
                else:
                    d.text(((w - fw2) // 2, y2), footer_line_2, fill=footer_grey, font=footer2_font)

        # Page number placed bottom-right with extra horizontal inset to avoid clipping

        if page_text:

            pw, ph = _text_size(d, page_text, footer2_font)

            right_inset = max(clearance_px, int(0.12 * DPI))  # allow for double digits and corner radius

            d.text((w - border_margin - right_inset - pw, y2), page_text, fill=footer_grey, font=footer2_font)




    # Final pass: re-draw the rounded border on top to guarantee visibility
    # This prevents any footer/background paint from visually clipping the bottom edge.
    try:
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
    except Exception:
        pass


def apply_universal_page_frame(

    page: Image.Image,

    *,

    product_title: str,

    subtitle: str,

    pack_code: str,

    page_num: int,

    total_pages: int,

    level: int | None = None,

    footer_title: str | None = None,

) -> None:

    """Adapter to the canonical Small Wins page frame.



    Preferred entry point for generators per the Universal Page Frame brief.

    """

    apply_small_wins_frame(

        page,

        product_title=product_title,

        subtitle=subtitle,

        pack_code=pack_code,

        page_num=page_num,

        total_pages=total_pages,

        level=level,

        footer_title=footer_title,

    )



def build_cover_subtitle(product_name: str, level_count: int | None, page_count: int | None) -> str:

    bits: list[str] = []

    if product_name:

        bits.append(product_name)

    if isinstance(level_count, int) and level_count > 0:

        bits.append(f"{level_count} levels")

    if isinstance(page_count, int) and page_count > 0:

        bits.append(f"{page_count} pages")

    return " • ".join(bits)



def generate_internal_cover_page(

    *,

    theme_name: str,

    pack_code: str,

    product_name: str,

    page_count: int | None = None,

    level_count: int | None = None,

    hero_image: Image.Image | None = None,

    hero_image_path: str | None = None,

    draw_footer: bool = False,

    howto_bullets: list[str] | None = None,

) -> Image.Image:

    w = int(8.5 * DPI)

    h = int(11.0 * DPI)

    page = Image.new("RGB", (w, h), "white")

    # Create a single draw context for this function to avoid UnboundLocalError

    d = ImageDraw.Draw(page)

    # Omit page count from the subtitle shown in the accent strip on the cover
    subtitle = build_cover_subtitle(product_name, level_count, None)

    icon = None

    if hero_image is not None:

        icon = hero_image

    elif hero_image_path:

        p = Path(hero_image_path)

        if p.exists():

            try:

                im = Image.open(p)

                icon = im.convert("RGBA") if im.mode != "RGBA" else im

            except Exception:

                icon = None

    # Fallback: if no icon resolved, try to locate a header hero using a slugified theme_name

    if icon is None:

        try:

            raw = (theme_name or "").strip().lower()

            # basic slugify: keep alnum and convert spaces/dashes to underscores

            slug = "".join(ch if ch.isalnum() else "_" for ch in raw)

            while "__" in slug:

                slug = slug.replace("__", "_")

            slug = slug.strip("_")

            repo_root = Path(__file__).resolve().parents[1]

            tdir = repo_root / "assets" / "themes" / slug

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

                    try:

                        im = Image.open(str(hp))

                        icon = im.convert("RGBA") if im.mode != "RGBA" else im

                        break

                    except Exception:

                        continue

        except Exception:

            pass

    apply_small_wins_frame(

        page,

        product_title=theme_name,

        subtitle=subtitle,

        pack_code=pack_code,

        page_num=1,

        total_pages=(page_count or 0) + 1,

        level=None,

        header_left_icon=icon,

        header_left_icon_flip=False,

        header_left_icon_y_offset_px=0,

        draw_accent_strip=True,

        draw_header=True,

        draw_subtitle=True,

        draw_footer=bool(draw_footer),

        draw_pcs_line=False,

    )

    # Ensure a safe default for bottom anchor used later

    try:

        bot  # type: ignore[name-defined]

    except Exception:

        bot = int(h - (1.10 * DPI if draw_footer else 0.70 * DPI))

    try:

        body_img = None

        if hero_image is not None:

            body_img = hero_image.convert("RGBA") if hero_image.mode != "RGBA" else hero_image.copy()

        elif hero_image_path:

            p2 = Path(hero_image_path)

            if p2.exists():

                im2 = Image.open(p2)

                body_img = im2.convert("RGBA") if im2.mode != "RGBA" else im2

        if body_img is not None:

            body_img = _make_near_white_transparent(body_img)

            w, h = page.size

            top = int(1.60 * DPI)

            bot = h - (int(1.10 * DPI) if draw_footer else int(0.70 * DPI))

            left = int(0.60 * DPI)

            right = w - int(0.60 * DPI)

            area_w = max(1, right - left)

            area_h = max(1, bot - top)

            sf = min(area_w / max(1, body_img.width), area_h / max(1, body_img.height))

            new_w = max(1, int(round(body_img.width * sf)))

            new_h = max(1, int(round(body_img.height * sf)))

            if new_w != body_img.width or new_h != body_img.height:

                body_img = body_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            px = left + (area_w - body_img.width) // 2

            py = top + (area_h - body_img.height) // 2

            page.paste(body_img, (px, py), body_img)

    except Exception:

        pass

    # Ensure layout anchors exist even if earlier block errored

    try:

        left  # type: ignore[name-defined]

    except Exception:

        left = int(0.60 * DPI)

    try:

        hero_bottom  # type: ignore[name-defined]

    except Exception:

        hero_bottom = int(1.60 * DPI)

    try:

        left_w  # type: ignore[name-defined]

    except Exception:

        _w, _h = page.size

        left_w = max(1, _w - int(1.20 * DPI))

    # Left column: disclaimer directly under hero, then chips, then tips

    lx = left

    ly = hero_bottom + int(0.14 * DPI)

    def _wrap_text_left(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int) -> list[str]:

        words = (text or "").split()

        if not words:

            return []

        lines = []

        cur = words[0]

        for w2 in words[1:]:

            trial = f"{cur} {w2}"

            tw, _ = _text_size(draw, trial, font)

            if tw <= max_w:

                cur = trial

            else:

                lines.append(cur)

                cur = w2

        lines.append(cur)

        return lines

    # Only render this left-column disclaimer when no hero image is present.

    if body_img is None:

        note_font_left = _brand_font_pt(11, bold=False, brand="poppins")

        note = "Use with the separately purchased source book. Book not included."

        for ln in _wrap_text_left(d, note, note_font_left, left_w):

            d.text((lx, ly), ln, fill=(120, 130, 140), font=note_font_left)

            _, nh = _text_size(d, ln, note_font_left)

            ly += nh + int(0.02 * DPI)

        ly += int(0.12 * DPI)

    # Unify heading sizes across sections

    tag_hd_left = _brand_font_pt(18, bold=True, brand="poppins")

    left_tx = _brand_font_pt(16, bold=False, brand="poppins")

    # Safe default for 'Perfect for' chips list

    cfg_perfect: list[str] = []

    if cfg_perfect:

        d.text((lx, ly), "Perfect for:", fill=hex_to_rgb(NAVY_HEX), font=tag_hd_left)

        ly += int(0.26 * DPI)

        tag_pad_x = int(0.10 * DPI)

        tag_pad_y = int(0.06 * DPI)

        tag_gap = int(0.12 * DPI)

        tx = lx

        ty = ly

        for label in cfg_perfect:

            lw, lh = _text_size(d, label, fonts["body"])

            pill_w = lw + tag_pad_x * 2

            pill_h = lh + tag_pad_y * 2

            if tx + pill_w > lx + left_w:

                tx = lx

                ty += pill_h + tag_gap

            if ty + pill_h > bot - int(0.90 * DPI):

                break

            d.rounded_rectangle([tx, ty, tx + pill_w, ty + pill_h], radius=int(pill_h * 0.4), fill=hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX))

            d.text((tx + tag_pad_x, ty + tag_pad_y), label, fill=(255, 255, 255), font=fonts["body"])

            tx += pill_w + tag_gap

        ly = ty + pill_h + int(0.14 * DPI)

    # (Top tips rendered later with anchor-aware limits to avoid duplication)

    left_bottom = ly

    if howto_bullets:

        fonts = _load_fonts(title_pt=24, body_pt=14, small_pt=10)

        left = int(0.50 * DPI)

        right = page.width - int(0.50 * DPI)

        y = int(1.85 * DPI)

        max_w = max(1, right - left)



        def wrap_line(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:

            words = str(text or "").split()

            if not words:

                return []

            lines: list[str] = []

            cur = words[0]

            meas = ImageDraw.Draw(Image.new("RGB", (10, 10)))

            for w in words[1:]:

                trial = f"{cur} {w}"

                tw, _ = _text_size(meas, trial, font)

                if tw <= max_width:

                    cur = trial

                else:

                    lines.append(cur)

                    cur = w

            lines.append(cur)

            return lines



        bullet_gap = int(0.24 * DPI)

        line_gap = int(0.10 * DPI)

        for b in howto_bullets:

            line_font = fonts["body"]

            # Compute bullet indent and wrap width based on a teal dot rendered via vector, baseline-aligned
            # First, measure a typical line height
            meas = ImageDraw.Draw(Image.new("RGB", (10, 10)))
            sample = (b or "").split()
            probe = sample[0] if sample else "Text"
            tw0, th0 = _text_size(meas, probe, line_font)
            # Slightly smaller teal dot for visual balance (reduced further)
            r = max(2, min(int(0.028 * DPI), max(2, th0 // 4)))
            bullet_indent = r * 2 + int(0.08 * DPI)

            wrap_w = max(1, max_w - bullet_indent)
            lines = wrap_line(b, line_font, wrap_w)
            if not lines:
                continue

            # Baseline for the bullet is at y + th of the first line
            tw, th = _text_size(d, lines[0], line_font)
            _draw_dot_bullet(d, x=left, y_baseline=y + th, color=hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX), r=r)

            text_x = left + bullet_indent
            d.text((text_x, y), lines[0], fill=hex_to_rgb(NAVY_HEX), font=line_font)
            y += th + line_gap

            for ln in lines[1:]:
                tw2, th2 = _text_size(d, ln, line_font)
                d.text((text_x, y), ln, fill=hex_to_rgb(NAVY_HEX), font=line_font)
                y += th2 + line_gap

            y += bullet_gap



    return page





def generate_teacher_cover_page(

    *,

    theme_name: str,

    pack_code: str,

    product_name: str,

    page_count: int | None = None,

    level_count: int | None = None,

    hero_image: Image.Image | None = None,

    hero_image_path: str | None = None,

    book_cover_path: str | None = None,

    draw_footer: bool = False,

    whats_included: list[str] | None = None,

    also_included: list[str] | None = None,

    top_tips: list[str] | None = None,

    rope_strand: str | None = None,

    rope_skills: str | None = None,

    small_win_text: str | None = None,

    why_this_works: str | None = None,

    render_chips: bool = False,

) -> Image.Image:

    w = int(8.5 * DPI)

    h = int(11.0 * DPI)

    page = Image.new("RGB", (w, h), "white")

    # Do not include page count in the accent-strip subtitle on the cover
    subtitle = build_cover_subtitle(product_name, level_count, None)

    icon = None

    if hero_image is not None:

        icon = hero_image

    elif hero_image_path:

        p = Path(hero_image_path)

        if p.exists():

            try:

                im = Image.open(p)

                icon = im.convert("RGBA") if im.mode != "RGBA" else im

            except Exception:

                icon = None

    apply_small_wins_frame(

        page,

        product_title=theme_name,

        subtitle=subtitle,

        pack_code=pack_code,

        page_num=1,

        total_pages=(page_count or 0) + 1,

        level=None,

        header_left_icon=icon,

        header_left_icon_flip=False,

        header_left_icon_y_offset_px=0,

        draw_accent_strip=True,

        draw_header=True,

        draw_subtitle=True,

        draw_footer=draw_footer,
        footer_y_offset_px=int(0.08 * DPI),

        show_data_strip=False,

        accent_margin_px=int(0.20 * DPI),

    )

    d = ImageDraw.Draw(page)

    fonts = _load_fonts(title_pt=24, body_pt=14, small_pt=10)

    try:

        left_tx = _brand_font_pt(16, bold=False, brand="poppins")

    except Exception:

        left_tx = fonts.get("body", _brand_font_pt(16, bold=False, brand="poppins"))

    # Geometry aligned to archived COVER_GENERATOR_V2 (scaled from 150→300dpi)

    scale150 = DPI / 150.0

    border_margin = int(0.25 * DPI)

    accent_margin = int(0.20 * DPI)

    header_h = int(1.00 * DPI)

    accent_y1 = border_margin + accent_margin

    accent_y2 = accent_y1 + header_h

    # BODY_TOP/BODY_BOT mirror COVER_GENERATOR_V2 (150dpi → 300dpi)

    top = accent_y2 + int(28 * scale150)

    body_bot = h - int(100 * scale150)

    foot_top = body_bot + int(14 * scale150)

    foot_band_h = max(1, h - foot_top - int(18 * scale150))

    bot = body_bot

    # Horizontal margins anchored to the outer border, giving clear padding

    inner_pad = int(0.20 * DPI)

    left = border_margin + inner_pad

    right = w - (border_margin + inner_pad)

    safe_right = right - int(0.10 * DPI)

    # Increase spacing between hero image box (left) and right column stack
    gap = int(32 * scale150)

    left_w = int(w * 0.38)

    right_w = max(1, (safe_right - (left + left_w + gap)))

    # Copy per brief (activity-specific; allow overrides from caller)

    cfg_bullets = whats_included or [

        "4 differentiated levels (1–4)",

        "Errorless learning design, built for independent use",

        "Boardmaker PCS symbols throughout",

        "Full color and black & white versions",

    ]

    cfg_perfect = ["AAC Users", "Autism Support", "SPED Classrooms", "Speech Therapy"]

    cfg_also = also_included or ["Quick Start Guide", "Terms of Use"]

    scar_strand = (rope_strand or "Word Recognition").strip()

    scar_skills = (rope_skills or "Decoding · Sight Words · Orthographic Mapping").strip()

    # Left hero panel — larger square, white

    hero_side = min(left_w, int((bot - top) * 0.78))

    hero_top = top

    hero_left_x = left

    hero_right_x = hero_left_x + hero_side

    hero_bottom = hero_top + hero_side

    # Initialize column bottoms to safe defaults; will be updated as content renders

    left_bottom = hero_bottom

    right_bottom = top

    try:

        # Filled hero panel (clean white background); inner dotted box drawn later

        d.rounded_rectangle(

            [hero_left_x, hero_top, hero_right_x, hero_bottom],

            radius=int(12 * scale150),

            fill=(255, 255, 255),

            outline=None,

        )

    except Exception:

        pass

    try:

        body_img = None

        # Prefer explicit book cover image if provided

        if isinstance(book_cover_path, str) and book_cover_path:

            pbc = Path(book_cover_path)

            if pbc.exists():

                _imc = Image.open(str(pbc))

                body_img = _imc.convert("RGBA") if _imc.mode != "RGBA" else _imc

        # Fallback to hero image path

        if body_img is None and hero_image is not None:

            body_img = hero_image.convert("RGBA") if hero_image.mode != "RGBA" else hero_image.copy()

        elif body_img is None and hero_image_path:

            p2 = Path(hero_image_path)

            if p2.exists():

                im2 = Image.open(p2)

                body_img = im2.convert("RGBA") if im2.mode != "RGBA" else im2

        # Prepare disclaimer and fit image so disclaimer fits below it

        try:

            _disc_font = _brand_font_pt(8, bold=False, brand="poppins")

        except Exception:

            _disc_font = fonts.get("small", _brand_font_pt(8, bold=False, brand="poppins"))

        _disc_text = "Book not included — please purchase separately. These activities support engagement with the text."

        pad = int(12 * scale150)

        area_w = max(1, hero_side - pad * 2)

        # Reserve space for disclaimer if we have an image

        disc_gap = int(10 * scale150)

        top_extra = int(10 * scale150)

        bottom_extra = int(10 * scale150)

        def _wrap_para2(draw, text, font, max_w):

            words = (text or "").split()

            if not words:

                return []

            lines = []

            cur = words[0]

            for w2 in words[1:]:

                trial = f"{cur} {w2}"

                tw, _ = _text_size(draw, trial, font)

                if tw <= max_w:

                    cur = trial

                else:

                    lines.append(cur)

                    cur = w2

            lines.append(cur)

            return lines

        disc_lines = _wrap_para2(d, _disc_text, _disc_font, area_w)

        disc_total_h = 0

        for ln in disc_lines:

            _, th = _text_size(d, ln, _disc_font)

            disc_total_h += th + int(2 * scale150)

        disc_total_h += disc_gap



        if body_img is not None:

            body_img = _make_near_white_transparent(body_img)

            # Fit image to remaining height after reserving disclaimer area.

            # Enforce equal padding around the image inside the dotted box: left/right/top = pad.

            area_h_img = max(1, hero_side - pad * 2 - disc_total_h - top_extra - bottom_extra)

            sf = min(area_w / max(1, body_img.width), area_h_img / max(1, body_img.height))

            nw = max(1, int(round(body_img.width * sf)))

            nh = max(1, int(round(body_img.height * sf)))

            if nw != body_img.width or nh != body_img.height:

                body_img = body_img.resize((nw, nh), Image.Resampling.LANCZOS)

            # Equal left/right padding: center within inner width (hero_side - 2*pad)

            px = hero_left_x + pad + max(0, (area_w - body_img.width) // 2)

            # Equal top padding from dotted border; center the image vertically within the inner area

            # (above the disclaimer) so space above and below is balanced.

            extra_v = max(0, area_h_img - body_img.height)

            py = hero_top + pad + top_extra + extra_v // 2

            page.paste(body_img, (px, py), body_img)

            # Draw disclaimer beneath image and dotted box around both

            dot_r = max(1, int(2 * scale150))

            step = max(4, int(8 * scale150))

            teal = hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX)

            ty = py + body_img.height + disc_gap

            # Draw disclaimer left-aligned to the box padding so it wraps neatly inside the dotted border

            tx = hero_left_x + pad

            for ln in disc_lines:

                d.text((tx, ty), ln, fill=(120, 130, 140), font=_disc_font)

                _, th = _text_size(d, ln, _disc_font)

                ty += th + int(2 * scale150)

            # Dotted box with rounded corners, hugging the hero panel edges.

            # Bottom keeps at least `pad` below the disclaimer block.

            box_x1 = hero_left_x

            box_y1 = hero_top

            box_x2 = hero_right_x

            box_y2 = min(hero_bottom - pad, ty + pad + bottom_extra)

            # Use the same corner radius as the hero panel (rounded_rectangle above uses 12 * scale150)

            corner_r = max(int(12 * scale150), step)

            # Horizontal edges (skip corners)

            for x in range(box_x1 + corner_r, box_x2 - corner_r, step):

                d.ellipse([x - dot_r, box_y1 - dot_r, x + dot_r, box_y1 + dot_r], fill=teal)

                d.ellipse([x - dot_r, box_y2 - dot_r, x + dot_r, box_y2 + dot_r], fill=teal)

            # Vertical edges (skip corners)

            for y in range(box_y1 + corner_r, box_y2 - corner_r, step):

                d.ellipse([box_x1 - dot_r, y - dot_r, box_x1 + dot_r, y + dot_r], fill=teal)

                d.ellipse([box_x2 - dot_r, y - dot_r, box_x2 + dot_r, y + dot_r], fill=teal)

            # Corner arcs (quarter-circles)

            def _arc(cx: int, cy: int, a0: float, a1: float):

                # Angular step approximated so spacing resembles edge spacing

                ang_step = max(6.0, (step / max(1, corner_r)) * 57.2958)

                a = a0

                while a <= a1 + 0.1:

                    rad = math.radians(a)

                    px = int(round(cx + corner_r * math.cos(rad)))

                    py = int(round(cy + corner_r * math.sin(rad)))

                    d.ellipse([px - dot_r, py - dot_r, px + dot_r, py + dot_r], fill=teal)

                    a += ang_step

            # top-left (180->270)

            _arc(box_x1 + corner_r, box_y1 + corner_r, 180.0, 270.0)

            # top-right (270->360)

            _arc(box_x2 - corner_r, box_y1 + corner_r, 270.0, 360.0)

            # bottom-right (0->90)

            _arc(box_x2 - corner_r, box_y2 - corner_r, 0.0, 90.0)

            # bottom-left (90->180)

            _arc(box_x1 + corner_r, box_y2 - corner_r, 90.0, 180.0)

            left_bottom = max(left_bottom, box_y2)

        else:

            left_bottom = max(left_bottom, hero_bottom)

    except Exception:

        left_bottom = max(left_bottom, hero_bottom)



    # Left column: chips and tips to balance layout

    # Compute the same fixed anchor used later so left column never intrudes

    _step_h_target = int(0.80 * DPI)

    _howto_gap = int(24 * scale150)

    _footer_h = int(130 * scale150)

    _footer_top = h - _footer_h - int(8 * scale150)

    _banner_h = int(0.32 * DPI)

    _banner_gap = int(0.14 * DPI)

    _anchor_top = _footer_top - _howto_gap - _step_h_target - _banner_h - _banner_gap

    lx = hero_left_x

    ly = left_bottom + int(0.14 * DPI)

    # Keep air above footer/steps using the shared anchor

    _left_limit = _anchor_top - int(0.24 * DPI)



    # Perfect for — chips or simple bullets

    tag_hd = _brand_font_pt(18, bold=True, brand="poppins")

    if ly + int(0.30 * DPI) < _left_limit:

        d.text((lx, ly), "Perfect for:", fill=hex_to_rgb(NAVY_HEX), font=tag_hd)

        ly += int(0.30 * DPI)

        if render_chips:

            tag_pad_x = int(0.10 * DPI)

            tag_pad_y = int(0.04 * DPI)

            tag_gap = int(0.12 * DPI)

            tx = lx

            ty = ly

            for label in cfg_perfect:

                lw, lh = _text_size(d, label, fonts["body"])

                pill_w = lw + tag_pad_x * 2

                pill_h = lh + tag_pad_y * 2

                if tx + pill_w > lx + left_w:

                    tx = lx

                    ty += pill_h + tag_gap

                if ty + pill_h > _left_limit:

                    break

                d.rounded_rectangle([tx, ty, tx + pill_w, ty + pill_h], radius=int(pill_h * 0.4), fill=hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX))

                _ty_text = ty + max(0, (pill_h - lh) // 2)

                d.text((tx + tag_pad_x, _ty_text), label, fill=(255, 255, 255), font=fonts["body"])

                tx += pill_w + tag_gap

            ly = ty + pill_h + int(0.14 * DPI)

        else:

            # Render as bullet list with consistent teal dot bullets

            bullet_gap = int(0.12 * DPI)

            bullet_r = max(2, int(0.04 * DPI))

            indent = bullet_r * 2 + int(0.16 * DPI)

            for label in cfg_perfect:

                if ly >= _left_limit:

                    break

                _, lh = _text_size(d, label, left_tx)

                cy = ly + lh // 2

                d.ellipse([lx, cy - bullet_r, lx + bullet_r * 2, cy + bullet_r], fill=hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX))

                d.text((lx + indent, ly), label, fill=(60, 75, 85), font=left_tx)

                ly += lh + bullet_gap



    # Top tips — concise bullets (use provided top_tips if any)

    tips_hd = _brand_font_pt(18, bold=True, brand="poppins")

    if ly + int(0.28 * DPI) < _left_limit:

        d.text((lx, ly), "Top tips:", fill=hex_to_rgb(NAVY_HEX), font=tips_hd)

        ly += int(0.28 * DPI)

        tips = top_tips or [

            "Model core words during play to build AAC carryover.",

            "Start errorless, then fade prompts across levels.",

            "Mix icons and real photos for generalization.",

        ]

        bullet_r = max(2, int(0.04 * DPI))

        for tip in tips:

            if ly >= _left_limit:

                break

            words = tip.split()

            cur = words[0]

            lines = []

            max_w = max(1, left_w - (bullet_r * 2 + int(0.16 * DPI)))

            for w2 in words[1:]:

                trial = f"{cur} {w2}"

                tw, _ = _text_size(d, trial, left_tx)

                if tw <= max_w:

                    cur = trial

                else:

                    lines.append(cur)

                    cur = w2

            lines.append(cur)

            cy = ly + _text_size(d, lines[0], left_tx)[1] // 2

            d.ellipse([lx, cy - bullet_r, lx + bullet_r * 2, cy + bullet_r], fill=hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX))

            tx0 = lx + bullet_r * 2 + int(0.16 * DPI)

            for i, ln in enumerate(lines):

                d.text((tx0, ly), ln, fill=(60, 75, 85), font=left_tx)

                _, th = _text_size(d, ln, left_tx)

                ly += th + int(0.02 * DPI)

            ly += int(0.04 * DPI)



    left_bottom = ly





    # Right column: details stack (What's included, Also included, Scarborough)

    rx = left + left_w + gap

    y = hero_top

    # Unify heading sizes across sections

    sec_hd = _brand_font_pt(18, bold=True, brand="poppins")

    sec_tx = _brand_font_pt(16, bold=False, brand="poppins")

    d.text((rx, y), "What's included:", fill=hex_to_rgb(NAVY_HEX), font=sec_hd)

    y += int(0.42 * DPI)

    # Wrap helper for right column text

    def _wrap_right(text: str, font: ImageFont.ImageFont, max_w: int) -> list[str]:

        words = (text or "").split()

        if not words:

            return []

        lines: list[str] = []

        cur = words[0]

        for w2 in words[1:]:

            trial = f"{cur} {w2}"

            tw, _ = _text_size(d, trial, font)

            if tw <= max_w:

                cur = trial

            else:

                lines.append(cur)

                cur = w2

        lines.append(cur)

        return lines

    for b in cfg_bullets:

        bullet_r = max(2, int(0.04 * DPI))

        indent = bullet_r * 2 + int(0.16 * DPI)

        avail = max(1, right_w - indent)

        lines = _wrap_right(b, sec_tx, avail)

        if not lines:

            continue

        # First line gets the dot bullet

        th_first = _text_size(d, lines[0], sec_tx)[1]

        cy = y + th_first // 2

        d.ellipse([rx, cy - bullet_r, rx + bullet_r * 2, cy + bullet_r], fill=hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX))

        d.text((rx + indent, y), lines[0], fill=(60, 75, 85), font=sec_tx)

        y += th_first + int(0.04 * DPI)

        for ln in lines[1:]:

            tw_, th_ = _text_size(d, ln, sec_tx)

            d.text((rx + indent, y), ln, fill=(60, 75, 85), font=sec_tx)

            y += th_ + int(0.04 * DPI)

        y += int(0.06 * DPI)

    y += int(0.18 * DPI)

    d.text((rx, y), "Also included:", fill=hex_to_rgb(NAVY_HEX), font=sec_hd)

    y += int(0.38 * DPI)

    for a in cfg_also:

        bullet_r = max(2, int(0.04 * DPI))

        indent = bullet_r * 2 + int(0.16 * DPI)

        avail = max(1, right_w - indent)

        lines = _wrap_right(a, sec_tx, avail)

        if not lines:

            continue

        th_first = _text_size(d, lines[0], sec_tx)[1]

        cy = y + th_first // 2

        d.ellipse([rx, cy - bullet_r, rx + bullet_r * 2, cy + bullet_r], fill=hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX))

        d.text((rx + indent, y), lines[0], fill=(60, 75, 85), font=sec_tx)

        y += th_first + int(0.04 * DPI)

        for ln in lines[1:]:

            tw_, th_ = _text_size(d, ln, sec_tx)

            d.text((rx + indent, y), ln, fill=(60, 75, 85), font=sec_tx)

            y += th_ + int(0.04 * DPI)

        y += int(0.04 * DPI)

    y += int(0.10 * DPI)

    # Prepare rope card + 'Why this works' with an explicit bottom anchor check

    rope_hd = _brand_font_pt(18, bold=True, brand="poppins")

    rope_tx = _brand_font_pt(14, bold=False, brand="poppins")

    why_hd = _brand_font_pt(18, bold=True, brand="poppins")

    why_tx = _brand_font_pt(14, bold=False, brand="poppins")

    pad_x = int(12 * scale150)

    pad_y = int(18 * scale150)

    x0 = rx + pad_x

    avail_w = (rx + right_w - int(6 * scale150)) - x0 - int(6 * scale150)

    line_gap = int(2 * scale150)



    # Wrapped text measures

    def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int) -> list[str]:

        words = (text or "").split()

        if not words:

            return []

        lines: list[str] = []

        cur = words[0]

        for w2 in words[1:]:

            trial = f"{cur} {w2}"

            tw, _ = _text_size(draw, trial, font)

            if tw <= max_w:

                cur = trial

            else:

                lines.append(cur)

                cur = w2

        lines.append(cur)

        return lines



    head_h = _text_size(d, "Scarborough Reading Rope", rope_hd)[1]

    strand_lines = _wrap(d, f"Strand:  {scar_strand}", rope_tx, avail_w)

    skills_lines = _wrap(d, scar_skills, rope_tx, avail_w)



    # Prepare optional 'Why this works' content — render ONLY if per-activity copy provided

    why_copy_raw = normalize_text(why_this_works) if isinstance(why_this_works, str) else ""

    has_why = bool(why_copy_raw and why_copy_raw.strip())

    if has_why:

        why_copy = why_copy_raw

        why_lines = _wrap_right(why_copy, why_tx, right_w)

        why_nat_h = _text_size(d, "Why this works:", why_hd)[1] + int(0.28 * DPI)

        for ln in why_lines:

            _, th = _text_size(d, ln, why_tx)

            why_nat_h += th + int(0.02 * DPI)

        why_nat_h += int(0.10 * DPI)

    else:

        why_lines = []

        why_nat_h = 0



    # Determine the fixed anchor (top of step tiles)

    step_h_target = int(0.80 * DPI)

    howto_gap = int(46 * scale150)

    footer_h = int(160 * scale150)

    footer_top = h - footer_h - int(8 * scale150)

    banner_h = int(0.32 * DPI) + 1

    banner_gap = int(0.14 * DPI)

    anchor_top = footer_top - howto_gap - step_h_target - banner_h - banner_gap



    # Estimate rope diagram height for sizing calculations

    usable_w = (rx + right_w - int(6 * scale150)) - x0

    rope_key = ("word_recognition" if scar_strand == "Word Recognition" else "language_comprehension")

    # Prefer accurate rope artwork over placeholders

    rope_img = None

    variant_dirs = [

        # Highest priority: user-provided realistic rope art
        Path(__file__).resolve().parents[1] / "assets" / "branding" / "rope" / "realistic",

        Path(__file__).resolve().parents[1] / "assets" / "covers",

        # Existing locations
        Path(__file__).resolve().parents[1] / "assets" / "branding" / "rope",

        Path(__file__).resolve().parents[1] / "Studioforge" / "Accurate generators" / "Internal covers",

        Path(__file__).resolve().parent,

        Path(__file__).resolve().parents[1] / "Studioforge" / "Accurate generators",

    ]

    # Search patterns in order of preference (exclude any filename containing 'PLACEHOLDER')
    # Accept common raster extensions
    pref_patterns = [

        f"scarborough_rope_realistic_{rope_key}.*",

        f"realistic_scarborough_rope_{rope_key}.*",

        f"scarborough-rope-{rope_key}.*",

        f"rope_diagram_{rope_key}.*",

        "*Scarborough*Rope*.*",

        f"*{rope_key}*rope*.*",

    ]

    try:

        for vd in variant_dirs:

            if rope_img is not None:

                break

            if not vd.exists():

                continue

            for pat in pref_patterns:

                cands = [fp for fp in vd.glob(pat) if fp.is_file() and "PLACEHOLDER" not in fp.name.upper()]

                if cands:

                    _im = Image.open(str(cands[0]))

                    rope_img = _im.convert("RGBA") if _im.mode != "RGBA" else _im

                    break

        # Fallback to placeholder assets if no accurate art found

        if rope_img is None:

            for vd in variant_dirs:

                if not vd.exists():

                    continue

                cands = list(vd.glob(f"rope_diagram_{rope_key}_PLACEHOLDER*.*"))

                if cands:

                    _im = Image.open(str(cands[0]))

                    rope_img = _im.convert("RGBA") if _im.mode != "RGBA" else _im

                    break

    except Exception:

        rope_img = None

    # Estimate diagram height after scaling (no paste yet)

    if rope_img is not None:

        # Estimate height assuming a comfortable fit within width (leave a small pad)
        fit_pad_px = int(8 * scale150)

        _scale = min(1.0, max(1, (usable_w - fit_pad_px)) / max(1, rope_img.width))

        diag_est_h = int(rope_img.height * _scale)

    else:

        # Estimate height for braided fallback so the card sizes to content

        diag_est_h = int(110 * scale150)



    text_block_h = head_h + int(24 * scale150)

    for ln in strand_lines:

        _, th = _text_size(d, ln, rope_tx)

        text_block_h += th + line_gap

    for ln in skills_lines:

        _, th = _text_size(d, ln, rope_tx)

        text_block_h += th + line_gap

    line_h_m = _text_size(d, "Ag", rope_tx)[1]

    rope_extra = 2 * (line_h_m + line_gap)

    min_card_h = pad_y + text_block_h + diag_est_h + pad_y + rope_extra



    between_card_and_why = int(0.24 * DPI) if has_why else 0

    # Align the rope card bottom to the left column's bottom edge while respecting the anchor

    target_bottom = min(anchor_top, left_bottom + 2)

    y_aligned = max(y, target_bottom - min_card_h)

    space_for_card = max(1, target_bottom - y_aligned)

    scar_h = min(min_card_h, space_for_card)

    y = y_aligned

    why_allow = max(0, anchor_top - (y + scar_h + between_card_and_why)) if has_why else 0



    # Draw card now that height is known

    try:

        _scar_fill = hex_to_rgb(US_SWS_TEAL_LT)

    except Exception:

        _scar_fill = (232, 248, 248)

    d.rounded_rectangle([rx, y, rx + right_w, y + scar_h], radius=int(0.12 * DPI), fill=_scar_fill, outline=(200, 232, 232), width=1)

    d.text((x0, y + pad_y), "Scarborough Reading Rope", fill=hex_to_rgb(NAVY_HEX), font=rope_hd)

    d.line([(x0, y + pad_y + int(24 * scale150)), (rx + right_w - int(6 * scale150), y + pad_y + int(24 * scale150))], fill=(180, 210, 235), width=1)

    yy = y + pad_y + int(40 * scale150)

    for ln in strand_lines:

        d.text((x0, yy), ln, fill=(60, 75, 85), font=rope_tx)

        _, th = _text_size(d, ln, rope_tx)

        yy += th + line_gap

    for ln in skills_lines:

        d.text((x0, yy), ln, fill=(120, 140, 150), font=rope_tx)

        _, th = _text_size(d, ln, rope_tx)

        yy += th + line_gap

    # Rope diagram + legend per brief (now actually render inside the sized card)

    if rope_img is not None:

        # Allow the diagram to occupy more of the card while keeping a small visual margin
        fit_pad_px = int(8 * scale150)

        avail_h = max(1, (y + scar_h) - yy - int(12 * scale150))

        _scale2 = min(
            1.0,
            max(1, (usable_w - fit_pad_px)) / max(1, rope_img.width),
            max(1, (avail_h - fit_pad_px)) / max(1, rope_img.height),
        )

        new_w2 = int(rope_img.width * _scale2)

        new_h2 = int(rope_img.height * _scale2)

        if new_w2 != rope_img.width or new_h2 != rope_img.height:

            rope_img = rope_img.resize((new_w2, new_h2), Image.Resampling.LANCZOS)

        ox = x0 + max(0, (usable_w - rope_img.width) // 2)

        page.paste(rope_img, (ox, yy), rope_img)

        diagram_h = rope_img.height

        legend_y = min(yy + diagram_h - int(18 * scale150), y + scar_h - int(12 * scale150))

        first_label = f"{scar_strand} (this pack)"

        f_leg = _brand_font_pt(13, bold=False, brand="poppins")

        d.ellipse([x0, legend_y + 4, x0 + 10, legend_y + 14], fill=hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX))

        d.text((x0 + 16, legend_y), first_label, font=f_leg, fill=hex_to_rgb(NAVY_HEX))

        l1w, l1h = _text_size(d, first_label, f_leg)

        other_strand = ("Language Comprehension" if scar_strand == "Word Recognition" else "Word Recognition")

        safe_x_max = rx + right_w - int(12 * scale150)

        legend2_x = x0 + 16 + l1w + int(40 * scale150)

        l2w, l2h = _text_size(d, other_strand, f_leg)

        req_right = legend2_x + 10 + 16 + l2w

        if req_right > safe_x_max:

            legend2_x = x0

            legend_y = legend_y + l1h + int(8 * scale150)

        d.ellipse([legend2_x, legend_y + 4, legend2_x + 10, legend_y + 14], fill=(169, 201, 198))

        d.text((legend2_x + 16, legend_y), other_strand, font=f_leg, fill=(120, 130, 140))

    else:

        # Draw braided fallback when no accurate asset found

        _draw_scarborough_rope(d, x=x0, y=yy, w=usable_w, h=int(min(110 * scale150, max(1, (y + scar_h) - yy - int(12 * scale150)))), highlighted_strand=scar_strand, teal=hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX), muted=(169, 201, 198))

        diagram_h = int(min(110 * scale150, max(1, (y + scar_h) - yy - int(12 * scale150))))

    y += scar_h + between_card_and_why

    if has_why and why_allow > 0:

        # Render 'Why this works' within allowed height (never mid-sentence)

        header_h = _text_size(d, "Why this works:", why_hd)[1]

        avail_total = max(0, anchor_top - y)

        need_full = header_h + int(0.28 * DPI)

        for ln in why_lines:

            _, th_ = _text_size(d, ln, why_tx)

            need_full += th_ + int(0.02 * DPI)

        need_full += int(0.10 * DPI)

        if need_full <= avail_total:

            d.text((rx, y), "Why this works:", fill=hex_to_rgb(NAVY_HEX), font=why_hd)

            y += int(0.28 * DPI)

            for ln in why_lines:

                _, th_ = _text_size(d, ln, why_tx)

                d.text((rx, y), ln, fill=(60, 75, 85), font=why_tx)

                y += th_ + int(0.02 * DPI)

            y = min(y + int(0.10 * DPI), anchor_top)

        else:

            # Try concise version: first sentence of provided copy

            fallback = why_copy.split(".")[0].strip() + "." if "." in why_copy else why_copy

            wb_lines = _wrap_right(fallback, why_tx, right_w)

            need_fb = header_h + int(0.28 * DPI)

            for ln in wb_lines:

                _, th_ = _text_size(d, ln, why_tx)

                need_fb += th_ + int(0.02 * DPI)

            need_fb += int(0.10 * DPI)

            d.text((rx, y), "Why this works:", fill=hex_to_rgb(NAVY_HEX), font=why_hd)

            y += int(0.28 * DPI)

            for ln in wb_lines:

                if y >= anchor_top:

                    break

                _, th_ = _text_size(d, ln, why_tx)

                d.text((rx, y), ln, fill=(60, 75, 85), font=why_tx)

                y += th_ + int(0.02 * DPI)

            y = min(y + int(0.10 * DPI), anchor_top)

    right_bottom = y

    step_h = int(0.80 * DPI)

    cols = 3

    step_gap = int(10 * scale150)

    total_w = (safe_right - left)

    sw_cell = max(1, (total_w - (cols - 1) * step_gap) // cols)

    sw_total = sw_cell * cols + (cols - 1) * step_gap
    sx = left + (total_w - sw_total) // 2

    shd = _brand_font_pt(16, bold=True, brand="poppins")

    ssub = _brand_font_pt(14, bold=False, brand="poppins")

    steps = [("1. Print", "Color or B&W"), ("2. Laminate", "For durability"), ("3. Use!", "Any session")]

    # Place step row considering both columns; bottom-anchored to a plain footer per brief

    min_top = max(left_bottom, right_bottom) + int(0.18 * DPI)

    border_margin = int(0.25 * DPI)

    footer_h = int(130 * scale150)

    footer_top = h - footer_h - int(8 * scale150)

    howto_gap = 0

    banner_h = int(0.32 * DPI) + 1

    banner_gap = int(0.02 * DPI)

    anchor_top = footer_top - howto_gap - step_h - banner_h - banner_gap

    # Ensure steps always render at or above anchor_top, never below the footer

    y = max(min_top, anchor_top)

    inter_gap_top = int(0.16 * DPI)

    footer_clear = int(0.10 * DPI)

    banner_y_min = y + step_h + inter_gap_top

    banner_y_lower = footer_top - banner_h - footer_clear

    banner_y = max(banner_y_min, banner_y_lower)

    sw_total_w = sw_cell * cols + step_gap * (cols - 1)

    # Draw the "Small win" tagline banner ONLY if an explicit text is provided
    if True:
        bx1, by1 = left, banner_y
        bx2, by2 = min(safe_right, left + sw_total_w), banner_y + banner_h

        try:
            bw_fill = hex_to_rgb(US_SWS_TEAL_LT)
            bw_edge = hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX)
        except Exception:
            bw_fill, bw_edge = (232, 248, 248), (180, 200, 180)

        # Tagline banner without outline (prevents faint seam)
        d.rounded_rectangle([bx1, by1, bx2, by2], radius=int(0.14 * DPI), fill=bw_fill, outline=None, width=0)

        bw_font = _brand_font_pt(16, bold=True, brand="nunito")
        core = (small_win_text.strip() if isinstance(small_win_text, str) else "Small Wins")
        for _ch in ["⭐","🌟","★","☆","✦","✧","✩","✪","✫","✬","✭","✮","✯"]:
            core = core.replace(_ch, "")
        core = core.strip() or "Small Wins"
        core_w, core_h = _text_size(d, core, bw_font)
        gap = int(0.12 * DPI)
        gold = (225, 180, 45)

        def draw_star(cx: int, cy: int, r: int) -> int:
            import math as _m
            pts = []
            for i in range(10):
                ang = (i * 36.0 - 90.0) * _m.pi / 180.0
                rad = r if i % 2 == 0 else int(r * 0.42)
                pts.append((cx + int(rad * _m.cos(ang)), cy + int(rad * _m.sin(ang))))
            d.polygon(pts, fill=gold, outline=None)
            return r * 2

        total_w = core_w + gap * 2 + int(0.8 * banner_h)
        ox = bx1 + (bx2 - bx1 - total_w) // 2
        oy = by1 + (banner_h - core_h) // 2
        r = int(min(banner_h, core_h) * 0.6 / 2)
        draw_star(ox + r, by1 + banner_h // 2, r)
        ox += r * 2 + gap
        d.text((ox, oy), core, fill=hex_to_rgb(NAVY_HEX), font=bw_font)
        ox += core_w + gap
        draw_star(ox + r, by1 + banner_h // 2, r)

    for hd_, sub_ in steps:

        d.rounded_rectangle([sx, y, sx + sw_cell, y + step_h], radius=int(0.14 * DPI), fill=(232, 237, 240), outline=hex_to_rgb(DEFAULT_ACCENT_TEAL_HEX), width=1)

        d.text((sx + int(0.16 * DPI), y + int(0.16 * DPI)), hd_, fill=hex_to_rgb(NAVY_HEX), font=shd)

        d.text((sx + int(0.16 * DPI), y + int(0.40 * DPI)), sub_, fill=(140, 155, 165), font=ssub)

        sx += sw_cell + step_gap

    # Plain, light footer with inline logo + text; thin divider above
    # If universal footer is drawn via apply_small_wins_frame (draw_footer=True),
    # skip this custom footer to avoid duplicates/overlap.
    if not draw_footer:
        d.line([left, footer_top, safe_right, footer_top], fill=(255, 255, 255), width=2)

        try:

            logo = None

            logo_candidates = [

                Path(__file__).resolve().parents[1] / "Studioforge" / "Accurate generators" / "Internal covers" / "logo_transparent.png",

                Path(__file__).resolve().parents[1] / "Studioforge" / "Accurate generators" / "Internal covers" / "logo_transparent (1).png",

                Path(__file__).resolve().parents[1] / "Studioforge" / "Accurate generators" / "Internal covers" / "logo_transparent (2).png",

                Path(__file__).resolve().parents[1] / "assets" / "branding" / "logos" / "logo_transparent.png",

                Path(__file__).resolve().parents[1] / "assets" / "branding" / "logos" / "small_wins_logo_with_text.png",

            ]

            for _lp in logo_candidates:

                if _lp.exists():

                    iml = Image.open(str(_lp))

                    logo = iml.convert("RGBA") if iml.mode != "RGBA" else iml

                    break

        except Exception:

            logo = None

        # Footer uses shrink-to-fit to avoid clipping at both sides

        base_f1 = 16

        base_f2 = 16

        f_footer = _shrink_font_to_fit("Small Wins Studio — smallwinsstudio.com", base_pt=base_f1, max_width_px=int(safe_right - left - int(0.40 * DPI)), bold=False, brand="poppins")

        f_footer_small = _shrink_font_to_fit(f"PCS symbols used with active PCS Maker Personal License. | © {datetime.now().year} Small Wins Studio  •  {theme_name} | {pack_code}", base_pt=base_f2, max_width_px=int(safe_right - left - int(0.40 * DPI)), bold=False, brand="poppins")

        line1 = "Small Wins Studio — smallwinsstudio.com"

        t1w, t1h = _text_size(d, line1, f_footer)

        gap = int(0.10 * DPI)

        lw = 0

        lh = 0

        if logo is not None:

            lg = logo.copy()

            lg.thumbnail((int(0.22 * DPI), int(0.22 * DPI)), Image.Resampling.LANCZOS)

            lw, lh = lg.size

        # Remove the 'Small Wins Studio' footer line entirely; only render PCS line below

        row_w = 0

        row_x = 0

        # Position PCS line comfortably below the divider (1 line lower than before)

        row_y = footer_top + int(0.40 * DPI)

        # Sanitize theme name: drop any '| Adapted Activities Bundle' suffix
        try:
            _theme_tokens = [seg.strip() for seg in str(theme_name).split("|")]
        except Exception:
            _theme_tokens = [str(theme_name).strip()]
        _theme_tokens = [t for t in _theme_tokens if t and t.lower() != "adapted activities bundle"]
        _theme_clean = " | ".join(_theme_tokens).strip()
        line2 = f"PCS symbols used with active PCS Maker Personal License. | © {datetime.now().year} Small Wins Studio  •  {_theme_clean} | {pack_code}"

        t2w, t2h = _text_size(d, line2, f_footer_small)

        # Clamp to ensure we never clip into the bottom border

        bottom_clear = int(0.30 * DPI)

        row_y = min(row_y, h - bottom_clear - t2h)

        # Draw brand-split: place larger logo immediately to the RIGHT of 'Small Wins Studio'
        gap_fx = int(0.02 * DPI)
        if logo is not None:
            try:
                lg = logo.copy()
                tgt_h = max(1, int(t2h * 2.3))
                lg.thumbnail((tgt_h * 3, tgt_h), Image.Resampling.LANCZOS)
                lw, lh = lg.size
                brand_phrase = "Small Wins Studio"
                idx = line2.lower().find(brand_phrase.lower())
                if idx >= 0:
                    pre = line2[:idx]
                    brand_txt = line2[idx: idx + len(brand_phrase)]
                    post = line2[idx + len(brand_phrase):]
                    pre_w, _ = _text_size(d, pre, f_footer_small)
                    brand_w, _ = _text_size(d, brand_txt, f_footer_small)
                    post_w, _ = _text_size(d, post, f_footer_small)
                    total_w_grp = pre_w + brand_w + gap_fx + lw + post_w
                    gx = left + (safe_right - left - total_w_grp) // 2
                    # Draw prefix
                    d.text((gx, row_y), pre, fill=(120, 130, 140), font=f_footer_small)
                    # Draw brand phrase
                    bx = gx + pre_w
                    d.text((bx, row_y), brand_txt, fill=(120, 130, 140), font=f_footer_small)
                    # Draw logo to right of brand
                    gy = row_y + int((t2h - lh) // 2)
                    page.paste(lg, (bx + brand_w + gap_fx, gy), lg)
                    # Draw suffix after logo
                    sx = bx + brand_w + gap_fx + lw
                    d.text((sx, row_y), post, fill=(120, 130, 140), font=f_footer_small)
                else:
                    # Fallback: center text + logo after
                    total_w_grp = t2w + gap_fx + lw
                    gx = left + (safe_right - left - total_w_grp) // 2
                    d.text((gx, row_y), line2, fill=(120, 130, 140), font=f_footer_small)
                    gy = row_y + int((t2h - lh) // 2)
                    page.paste(lg, (gx + t2w + gap_fx, gy), lg)
            except Exception:
                d.text((left + (safe_right - left - t2w) // 2, row_y), line2, fill=(120, 130, 140), font=f_footer_small)
        else:
            d.text((left + (safe_right - left - t2w) // 2, row_y), line2, fill=(120, 130, 140), font=f_footer_small)

    # Footer is drawn by apply_small_wins_frame to match other activity pages

    return page



# AAC symbol strip — shared utility

def _sanitize_stem(s: str) -> str:

    t = normalize_text(s or "")

    t = t.lower().strip()

    for ch in [" ", "-", ",", ".", ":", ";", "!", "?", "'", '"', "/", "\\", "(", ")", "[", "]", "{", "}"]:

        t = t.replace(ch, "_")

    # collapse underscores

    while "__" in t:

        t = t.replace("__", "_")

    return t.strip("_")





def _symbols_root() -> Path:

    # Primary expected location per brief

    candidates = [

        Path("assets") / "symbols" / "png" / "Alpha",

        Path(__file__).resolve().parents[1] / "assets" / "symbols" / "png" / "Alpha",

    ]

    for c in candidates:

        if c.exists():

            return c

    # Fallback to assets root to allow rglob

    for c in [Path("assets"), Path(__file__).resolve().parents[1] / "assets"]:

        if c.exists():

            return c

    return Path(".")





def _find_symbol_png(word: str) -> Path | None:

    stem = _sanitize_stem(word)

    root = _symbols_root()

    try:

        # Exact stem first

        exact = list(root.rglob(f"{stem}.png"))

        if exact:

            return exact[0]

        # Prefix variants like word_1, word_dk

        pref = [p for p in root.rglob("*.png") if _sanitize_stem(p.stem) == stem or _sanitize_stem(p.stem).startswith(stem + "_")]

        if pref:

            return pref[0]

    except Exception:

        return None

    return None





def draw_aac_strip(page: Image.Image, *, words: list[str], bg_hex: str | None = None) -> None:

    """Draw an AAC symbol strip at the bottom of the given PIL page.



    - Background: SWS_TEAL_LT (#E8F8F8) at 60px (150dpi) → 120px at 300dpi

    - Symbol cell: 40px (150dpi) → 80px at 300dpi with label below

    - words: ordered list of words to render (include any fringe first or last as you prefer)

      Core words can be included by caller; this function just renders supplied list.

    """

    w, h = page.size

    d = ImageDraw.Draw(page)



    bar_h = int((60 if DPI == 150 else 120))

    y1 = h - bar_h

    # Resolve background colour

    if isinstance(bg_hex, str) and bg_hex.strip().startswith("#"):

        bg_tuple = hex_to_rgb(bg_hex.strip())

    else:

        try:

            bg_tuple = hex_to_rgb(US_SWS_TEAL_LT)

        except Exception:

            bg_tuple = (232, 248, 248)

    d.rectangle([0, y1, w, h], fill=bg_tuple)



    # Layout

    pad_x = int(0.20 * DPI)

    gap_x = int(0.16 * DPI)

    icon_px = int(80 if DPI >= 300 else 40)

    label_gap = int(0.06 * DPI)

    x = pad_x



    fonts = _load_fonts(title_pt=24, body_pt=14, small_pt=10)

    for word in words:

        if x + icon_px + pad_x > w:

            break

        # Try load symbol image

        img = None

        p = _find_symbol_png(word)

        if p and p.exists():

            try:

                im = Image.open(str(p))

                img = im.convert("RGBA") if im.mode != "RGBA" else im

                img.thumbnail((icon_px, icon_px), Image.Resampling.LANCZOS)

            except Exception:

                img = None

        if img is not None:

            icon_y = y1 + int(0.10 * DPI)

            page.paste(img, (x, icon_y), img)

            lbl_y = icon_y + img.height + label_gap

            lbl = normalize_text(str(word).strip())

            lw, lh = _text_size(d, lbl, fonts["small_bold"])  # use bold small for readability

            d.text((x + (icon_px - lw) // 2, lbl_y), lbl, fill=hex_to_rgb(NAVY_HEX), font=fonts["small_bold"])

        else:

            # Fallback: rounded pill with text

            pill_h = icon_px

            rx = int(0.18 * pill_h)

            d.rounded_rectangle([x, y1 + int(0.10 * DPI), x + icon_px, y1 + int(0.10 * DPI) + pill_h], radius=rx, fill=(229, 231, 235))

            lbl = normalize_text(str(word).strip())

            lw, lh = _text_size(d, lbl, fonts["small_bold"])  # bold small

            d.text((x + (icon_px - lw) // 2, y1 + int(0.10 * DPI) + (pill_h - lh) // 2), lbl, fill=hex_to_rgb(NAVY_HEX), font=fonts["small_bold"])



        x += icon_px + gap_x
