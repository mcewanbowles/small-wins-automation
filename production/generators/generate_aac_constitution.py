#!/usr/bin/env python3

from __future__ import annotations

import io
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# Add repo root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.sws_design import DPI, apply_small_wins_frame
from utils.sws_design import SUBTITLE_DARK_GRAY


_THEME_ID = "brown_bear"
_THEME_TITLE = "Brown Bear"
_PRODUCT_ID = "aac"
_PACK_CODE = "BB-AAC"

_FONT_ARIAL = "C:/Windows/Fonts/arial.ttf"


@dataclass(frozen=True)
class PageSpec:
    name: str
    width_pt: float
    height_pt: float

    @property
    def size_px(self) -> tuple[int, int]:
        w_px = int(self.width_pt * DPI / 72)
        h_px = int(self.height_pt * DPI / 72)
        return (w_px, h_px)


_PORTRAIT = PageSpec(name="portrait", width_pt=letter[0], height_pt=letter[1])
_LANDSCAPE = PageSpec(name="landscape", width_pt=landscape(letter)[0], height_pt=landscape(letter)[1])


def _load_font(px: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype(_FONT_ARIAL, px)
    except Exception:
        return ImageFont.load_default()


def _cover_fit(img: Image.Image, w: int, h: int) -> Image.Image:
    src_w, src_h = img.size
    if src_w <= 0 or src_h <= 0:
        return img
    scale = max(w / src_w, h / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = max(0, (new_w - w) // 2)
    top = max(0, (new_h - h) // 2)
    return resized.crop((left, top, left + w, top + h))


def _contain_fit(img: Image.Image, w: int, h: int) -> Image.Image:
    work = img.copy()
    work.thumbnail((max(1, w), max(1, h)), Image.Resampling.LANCZOS)
    return work


def _iter_core_icons() -> list[tuple[str, Path, Path | None]]:
    root = Path(__file__).resolve().parents[2]
    core_dir = root / "assets" / "global" / "aac_core"
    core_text_dir = root / "assets" / "global" / "aac_core_text"

    if not core_dir.exists():
        raise FileNotFoundError(str(core_dir))

    icons: list[tuple[str, Path, Path | None]] = []
    for p in sorted(core_dir.glob("*.png")):
        if not p.is_file():
            continue
        name = p.stem.replace("_", " ").strip()
        alt = core_text_dir / p.name
        icons.append((name, p, alt if alt.exists() else None))
    if not icons:
        raise RuntimeError(f"No AAC core icons found in {core_dir}")
    return icons


def _norm_key(s: str) -> str:
    return "".join(ch for ch in s.lower().strip() if ch.isalnum())


def _core_icon_lookup() -> dict[str, tuple[str, Path, Path | None]]:
    items = _iter_core_icons()
    out: dict[str, tuple[str, Path, Path | None]] = {}
    for name, src, alt in items:
        out[_norm_key(name)] = (name, src, alt)
    return out


def _pick_icons(keys: list[str]) -> list[tuple[str, Path, Path | None]]:
    lookup = _core_icon_lookup()
    picked: list[tuple[str, Path, Path | None]] = []
    for k in keys:
        item = lookup.get(_norm_key(k))
        if item is not None:
            picked.append(item)
    return picked


def _page_base(
    *,
    spec: PageSpec,
    title: str,
    subtitle: str,
    page_num: int,
    total_pages: int,
    draw_header_footer: bool,
    footer_y_offset_px: int = 0,
) -> Image.Image:
    w_px, h_px = spec.size_px
    page = Image.new("RGB", (w_px, h_px), "white")

    apply_small_wins_frame(
        page,
        product_title=title,
        subtitle=subtitle,
        pack_code=_PACK_CODE,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        accent_color_hex=None,
        footer_title=title,
        header_left_icon=None,
        header_left_icon_flip=False,
        footer_y_offset_px=int(footer_y_offset_px),
        draw_accent_strip=draw_header_footer,
        draw_header=draw_header_footer,
        draw_subtitle=draw_header_footer,
        draw_footer=draw_header_footer,
    )

    return page


def _content_rect_px(*, spec: PageSpec, with_header_footer: bool) -> tuple[int, int, int, int]:
    w_px, h_px = spec.size_px
    border_margin = int(0.25 * DPI)

    if not with_header_footer:
        # Just inset slightly inside the border.
        pad = int(0.06 * DPI)
        return (border_margin + pad, border_margin + pad, w_px - border_margin - pad, h_px - border_margin - pad)

    header_h = int(1.00 * DPI)
    accent_margin = int(0.08 * DPI)
    stripe_y2 = border_margin + accent_margin + header_h

    footer_room = int(0.55 * DPI)

    x0 = int(0.55 * DPI)
    x1 = w_px - int(0.55 * DPI)
    y0 = stripe_y2 + int(0.35 * DPI)
    y1 = h_px - border_margin - footer_room
    return (x0, y0, x1, y1)


def _render_core_board(*, spec: PageSpec, mode: str, page_num: int, total_pages: int) -> Image.Image:
    icons = _iter_core_icons()

    page = _page_base(
        spec=spec,
        title=f"{_THEME_TITLE} AAC",
        subtitle=f"Core Board ({spec.name.title()})",
        page_num=page_num,
        total_pages=total_pages,
        draw_header_footer=True,
    )

    x0, y0, x1, y1 = _content_rect_px(spec=spec, with_header_footer=True)
    w = max(1, x1 - x0)
    h = max(1, y1 - y0)

    cols = 6
    rows = 6

    pad = int(0.02 * min(w, h))
    gap = max(2, int(0.012 * min(w, h)))

    cell_w = (w - 2 * pad - gap * (cols - 1)) // cols
    cell_h = (h - 2 * pad - gap * (rows - 1)) // rows
    cell = max(1, min(cell_w, cell_h))

    grid_w = cols * cell + gap * (cols - 1)
    grid_h = rows * cell + gap * (rows - 1)

    start_x = x0 + (w - grid_w) // 2
    start_y = y0 + (h - grid_h) // 2

    d = ImageDraw.Draw(page)
    label_font = _load_font(int(12 * (DPI / 72)))

    for idx in range(min(len(icons), cols * rows)):
        name, src, alt = icons[idx]
        r = idx // cols
        c = idx % cols
        cx = start_x + c * (cell + gap)
        cy = start_y + r * (cell + gap)

        # Box
        radius = int(0.06 * cell)
        d.rounded_rectangle([cx, cy, cx + cell, cy + cell], radius=radius, outline=(30, 30, 30), width=max(1, int(2 * (DPI / 72))), fill="white")

        # Icon
        try:
            if mode == "bw" and alt is not None:
                im = Image.open(alt).convert("RGBA")
            else:
                im = Image.open(src).convert("RGBA")
                if mode == "bw":
                    im = im.convert("L").convert("RGBA")
        except Exception:
            continue

        # Label band (bottom)
        band_h = int(cell * 0.22)
        icon_area_h = cell - band_h

        icon_max = int(min(cell * 0.80, icon_area_h * 0.88))
        im = _contain_fit(im, icon_max, icon_max)
        ix = cx + (cell - im.width) // 2
        iy = cy + max(1, (icon_area_h - im.height) // 2)
        page.paste(im, (ix, iy), im)

        # Label
        label = name
        bbox = d.textbbox((0, 0), label, font=label_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = cx + (cell - tw) // 2
        ty = cy + icon_area_h + (band_h - th) // 2
        d.text((tx, ty), label, fill=(30, 30, 30), font=label_font)

    return page


def _render_strips_page(*, spec: PageSpec, mode: str, page_num: int, total_pages: int) -> Image.Image:
    # Curated groupings for functional communication (requesting, commenting,
    # rejecting, questioning). This is more useful than a purely alphabetical/asset order.
    # Each row is one "communication strip".
    curated_rows: list[list[str]] = [
        ["I", "want", "more", "help", "finished", "go"],
        ["yes", "no", "like", "dont like", "wait"],
        ["what", "where", "why", "choose", "color", "read"],
        ["look", "see", "same", "different", "think", "dont know"],
        ["uh oh", "you", "I, me", "want", "help", "finished"],
        ["what next", "go", "wait", "more", "help"],
    ]

    # Flatten for lookup but keep strip row semantics.
    row_icons: list[list[tuple[str, Path, Path | None]]] = [
        _pick_icons(row) for row in curated_rows
    ]

    page = _page_base(
        spec=spec,
        title=f"{_THEME_TITLE} AAC",
        subtitle=f"Communication Strips ({spec.name.title()})",
        page_num=page_num,
        total_pages=total_pages,
        draw_header_footer=True,
        footer_y_offset_px=int(0.06 * DPI),
    )

    x0, y0, x1, y1 = _content_rect_px(spec=spec, with_header_footer=True)
    w = max(1, x1 - x0)
    h = max(1, y1 - y0)

    d = ImageDraw.Draw(page)
    label_font = _load_font(int(12 * (DPI / 72)))

    strip_rows = len(row_icons)
    strip_gap = max(4, int(0.02 * h))
    strip_h = (h - strip_gap * (strip_rows - 1)) // strip_rows

    cols = 6
    cell_gap = max(3, int(0.02 * w))
    cell_w = (w - cell_gap * (cols - 1)) // cols

    for r in range(strip_rows):
        sy = y0 + r * (strip_h + strip_gap)
        # Strip outline
        d.rounded_rectangle([x0, sy, x1, sy + strip_h], radius=int(0.08 * strip_h), outline=(30, 30, 30), width=max(1, int(2 * (DPI / 72))), fill="white")

        for c in range(cols):
            row = row_icons[r] if r < len(row_icons) else []
            if c >= len(row):
                continue
            name, src, alt = row[c]

            cx = x0 + c * (cell_w + cell_gap)
            cy = sy

            # Cell interior
            pad = max(2, int(0.06 * cell_w))
            band_h = int(strip_h * 0.30)
            icon_h = strip_h - band_h

            try:
                if mode == "bw" and alt is not None:
                    im = Image.open(alt).convert("RGBA")
                else:
                    im = Image.open(src).convert("RGBA")
                    if mode == "bw":
                        im = im.convert("L").convert("RGBA")
            except Exception:
                continue

            icon_max = int(min(cell_w * 0.75, icon_h * 0.85))
            im = _contain_fit(im, icon_max, icon_max)
            ix = cx + (cell_w - im.width) // 2
            iy = cy + max(1, (icon_h - im.height) // 2)
            page.paste(im, (ix, iy), im)

            label = name
            bbox = d.textbbox((0, 0), label, font=label_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = cx + (cell_w - tw) // 2
            ty = cy + icon_h + (band_h - th) // 2
            d.text((tx, ty), label, fill=(30, 30, 30), font=label_font)

    return page


def _render_storage_labels(*, spec: PageSpec, mode: str, page_num: int, total_pages: int) -> Image.Image:
    icons = _iter_core_icons()

    page = _page_base(
        spec=spec,
        title=f"{_THEME_TITLE} AAC",
        subtitle=f"Storage Labels ({spec.name.title()})",
        page_num=page_num,
        total_pages=total_pages,
        draw_header_footer=True,
    )

    x0, y0, x1, y1 = _content_rect_px(spec=spec, with_header_footer=True)
    w = max(1, x1 - x0)
    h = max(1, y1 - y0)

    d = ImageDraw.Draw(page)
    label_font = _load_font(int(12 * (DPI / 72)))

    cols = 3
    rows = 8
    gap_x = max(6, int(0.02 * w))
    gap_y = max(6, int(0.015 * h))

    label_w = (w - gap_x * (cols - 1)) // cols
    label_h = (h - gap_y * (rows - 1)) // rows

    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= len(icons):
                break
            name, src, alt = icons[idx]
            idx += 1

            lx = x0 + c * (label_w + gap_x)
            ly = y0 + r * (label_h + gap_y)

            d.rounded_rectangle([lx, ly, lx + label_w, ly + label_h], radius=int(0.12 * label_h), outline=(30, 30, 30), width=max(1, int(2 * (DPI / 72))), fill="white")

            try:
                if mode == "bw" and alt is not None:
                    im = Image.open(alt).convert("RGBA")
                else:
                    im = Image.open(src).convert("RGBA")
                    if mode == "bw":
                        im = im.convert("L").convert("RGBA")
            except Exception:
                continue

            pad = max(2, int(0.08 * min(label_w, label_h)))
            band_h = int(label_h * 0.34)
            icon_h = label_h - band_h

            icon_max = int(min(label_w * 0.45, icon_h * 0.80))
            im = _contain_fit(im, icon_max, icon_max)
            ix = lx + pad
            iy = ly + max(1, (icon_h - im.height) // 2)
            page.paste(im, (ix, iy), im)

            label = name
            bbox = d.textbbox((0, 0), label, font=label_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = lx + (label_w - tw) // 2
            ty = ly + icon_h + (band_h - th) // 2
            d.text((tx, ty), label, fill=(30, 30, 30), font=label_font)

    return page


def _render_book_discussion_boards(*, spec: PageSpec, mode: str, page_num: int, total_pages: int) -> Image.Image:
    root = Path(__file__).resolve().parents[2]
    boards_dir = root / "assets" / "themes" / _THEME_ID / "AAC boards"
    pngs = sorted([p for p in boards_dir.glob("*.png") if p.is_file()])

    # This renderer returns a SINGLE page; caller loops.
    raise RuntimeError("Use _render_book_discussion_boards_pages")


def _render_book_discussion_boards_pages(*, spec: PageSpec, mode: str) -> list[Image.Image]:
    root = Path(__file__).resolve().parents[2]
    boards_dir = root / "assets" / "themes" / _THEME_ID / "AAC boards"
    pngs = sorted([p for p in boards_dir.glob("*.png") if p.is_file()])
    if not pngs:
        return []

    pages: list[Image.Image] = []
    total_pages = len(pngs)

    for i, p in enumerate(pngs, start=1):
        # Border only. We'll add a custom footer (no page numbers) for the Literacy Chat Board.
        w_px, h_px = spec.size_px
        page = Image.new("RGB", (w_px, h_px), "white")
        apply_small_wins_frame(
            page,
            product_title="",
            subtitle="",
            pack_code=_PACK_CODE,
            page_num=1,
            total_pages=1,
            level=None,
            draw_accent_strip=False,
            draw_header=False,
            draw_subtitle=False,
            draw_footer=False,
        )

        x0, y0, x1, y1 = _content_rect_px(spec=spec, with_header_footer=False)

        # For the landscape Literacy Chat Board, reserve space above the border
        # for the two-line footer so the board art is shifted upward.
        if spec.name == "landscape":
            footer_band = int(0.34 * DPI)
            y1 = max(y0 + 1, y1 - footer_band)
        bw = max(1, x1 - x0)
        bh = max(1, y1 - y0)

        board = Image.open(p).convert("RGBA")
        if mode == "bw":
            board = board.convert("L").convert("RGBA")

        fitted = _cover_fit(board, bw, bh)
        page.paste(fitted, (x0, y0), fitted)

        # Add required footer title + Small Wins footer text (no page numbers).
        if spec.name == "landscape":
            d = ImageDraw.Draw(page)
            s = DPI / 72
            font_small = _load_font(int(10 * s))

            border_margin = int(0.25 * DPI)
            y2 = h_px - border_margin - int(0.12 * DPI)
            y1 = y2 - int(0.13 * DPI)

            footer_line_1 = "Brown Bear - Literacy Chat Board"
            footer_line_2 = (
                f"Small Wins Studio | PCS symbols used with active PCS Maker Personal License. | "
                f"© 2026"
            )

            fw1 = d.textbbox((0, 0), footer_line_1, font=font_small)
            fw2 = d.textbbox((0, 0), footer_line_2, font=font_small)
            tw1 = fw1[2] - fw1[0]
            tw2 = fw2[2] - fw2[0]

            d.text(((w_px - tw1) // 2, y1), footer_line_1, fill=(60, 60, 60), font=font_small)
            d.text(((w_px - tw2) // 2, y2), footer_line_2, fill=(140, 140, 140), font=font_small)

        pages.append(page)

    return pages


def _save_pdf(*, pages: list[Image.Image], out_path: Path, page_spec: PageSpec) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out_path), pagesize=(page_spec.width_pt, page_spec.height_pt))
    for p in pages:
        buf = io.BytesIO()
        p.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=page_spec.width_pt, height=page_spec.height_pt)
        c.showPage()
    c.save()


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    out_dir = root / "production" / "final_products" / _THEME_ID / _PRODUCT_ID
    out_dir.mkdir(parents=True, exist_ok=True)

    page_specs = [_PORTRAIT, _LANDSCAPE]
    modes = ["color", "bw"]

    # Generate only:
    # - Communication strips (portrait + landscape)
    # - Literacy Chat Board (landscape only)
    for spec in page_specs:
        for mode in modes:
            strips_pages = [_render_strips_page(spec=spec, mode=mode, page_num=1, total_pages=1)]
            _save_pdf(pages=strips_pages, out_path=out_dir / f"brown_bear_aac_strips_{spec.name}_{mode}_FINAL.pdf", page_spec=spec)
            print(f"OK Generated: brown_bear_aac_strips_{spec.name}_{mode}_FINAL.pdf")

    for mode in modes:
        bd_pages = _render_book_discussion_boards_pages(spec=_LANDSCAPE, mode=mode)
        if bd_pages:
            _save_pdf(pages=bd_pages, out_path=out_dir / f"brown_bear_literacy_chat_board_landscape_{mode}_FINAL.pdf", page_spec=_LANDSCAPE)
            print(f"OK Generated: brown_bear_literacy_chat_board_landscape_{mode}_FINAL.pdf")

    print(f"\nOK AAC exports written to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
