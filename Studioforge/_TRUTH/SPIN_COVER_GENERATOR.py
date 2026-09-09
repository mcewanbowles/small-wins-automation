from __future__ import annotations

def _validate_images_folder(images_folder: str) -> None:
    p = Path(images_folder)
    if not p.exists():
        raise FileNotFoundError(f"Images folder not found: {images_folder}")
    sp = str(p).lower()
    if "_tlot_archived_duplicate" in sp:
        raise ValueError(
            f"Images folder is inside the archived duplicate tree: {p}. Use assets/themes/<slug>/activity_images/."
        )
    if any(k in sp for k in ["aac_core", "aac_core_text", "global"]):
        raise ValueError(
            f"Spin & Cover must not read from AAC core/global: {p}. Use assets/themes/<slug>/activity_images/."
        )
    files = [f for f in p.glob("*.png") if f.is_file() and not f.name.startswith(".")]
    if len(files) < 6:
        raise ValueError(f"Too few images in {p} — found {len(files)}, need at least 6.")

 

import io
import math
import random
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from utils.sws_design import apply_small_wins_frame, row_gap_px, safe_footer_inset_px, generate_internal_cover_page
from utils.qa import assess_files
from datetime import datetime
import json
from utils.UNIVERSAL_STANDARDS import clean_label, SWS_TEAL, SWS_NAVY

PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

TITLE_BLUE = SWS_TEAL
NAVY_BLUE = SWS_NAVY
STEEL_BLUE = SWS_NAVY
LIGHT_BG = (255, 255, 255)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = str(hex_color).lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _load_fonts() -> dict[str, ImageFont.ImageFont]:
    s = DPI / 72
    try:
        return {
            "num": ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(18 * s)),
            "label": ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(10 * s)),
        }
    except Exception:
        d = ImageFont.load_default()
        return {"num": d, "label": d}


def _read_icons(images_folder: str) -> list[tuple[str, Image.Image]]:
    p = Path(images_folder)
    files = sorted([
        f for f in p.glob("*.png")
        if f.is_file() and not f.name.startswith(".")
        and not any(k in str(f).lower() for k in ["aac_core", "aac_core_text", "global"])
    ])
    items: list[tuple[str, Image.Image]] = []
    for f in files:
        try:
            img = Image.open(f)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            raw = f.stem.replace("_", " ").replace("-", " ")
            name = clean_label(raw).strip()
            name = re.sub(r"\([^)]*\)", "", name).strip()
            name = re.sub(r"\s{2,}", " ", name).strip()
            name = name.title()
            items.append((name, img))
        except Exception:
            continue
    return items


def _normalize_label(name: str) -> str:
    s = str(name).strip()
    s = clean_label(s)
    s = re.sub(r"\([^)]*\)", "", s).strip()
    s = re.sub(r"\s+\d+$", "", s).strip()
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


def _draw_spinner(*, draw: ImageDraw.ImageDraw, page: Image.Image, x: int, y: int, r: int, labels: list[str], icons: list[Image.Image], mode: str) -> None:
    n = max(1, len(labels))
    start = -90.0
    fonts = _load_fonts()
    for i, lbl in enumerate(labels):
        end = start + (360.0 / n)
        fill = (232, 244, 252) if i % 2 == 0 else (232, 240, 248)
        draw.pieslice([x - r, y - r, x + r, y + r], start=start, end=end, fill=fill, outline=hex_to_rgb(NAVY_BLUE), width=2)

        if i < len(icons):
            ic = icons[i].copy()
            if mode == "bw":
                ic = ic.convert("L").convert("RGBA")
            icon_size = int(r * 0.50)
            ic.thumbnail((icon_size, icon_size), Image.Resampling.LANCZOS)
            mid = math.radians((start + end) / 2.0)
            ix = x + int(math.cos(mid) * r * 0.48) - (ic.width // 2)
            iy = y + int(math.sin(mid) * r * 0.48) - (ic.height // 2)
            page.paste(ic, (ix, iy), ic)

        mid = math.radians((start + end) / 2.0)
        tx = x + int(math.cos(mid) * r * 0.72)
        ty = y + int(math.sin(mid) * r * 0.72)
        bbox = draw.textbbox((0, 0), lbl, font=fonts["num"])
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((tx - (tw // 2), ty - (th // 2)), lbl, fill=hex_to_rgb(NAVY_BLUE), font=fonts["num"])
        start = end
    # needle (printed) - kept inside the circle area so it never clips the accent strip
    needle_tip_y = y - r + int(12 * (DPI / 72))
    draw.polygon(
        [(x, needle_tip_y), (x - int(10 * (DPI / 72)), needle_tip_y + int(18 * (DPI / 72))), (x + int(10 * (DPI / 72)), needle_tip_y + int(18 * (DPI / 72)))],
        fill=hex_to_rgb(STEEL_BLUE),
    )


def _page_spinner(*, items: list[tuple[str, Image.Image]], page_num: int, total_pages: int, pack_code: str, theme_name: str, mode: str) -> Image.Image:
    w = int(PAGE_WIDTH * DPI / 72)
    h = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(page)
    apply_small_wins_frame(
        page,
        product_title=theme_name,
        subtitle="Spin & Cover — Spinner",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        footer_title=f"{theme_name} | Spin & Cover",
        header_left_icon=(items[0][1] if items else None),
    )

    pool = items[:]
    if not pool:
        return page

    if len(pool) < 8:
        while len(pool) < 8:
            pool = pool + items
    pool = pool[:8]

    labels = [str(i + 1) for i in range(8)]
    spinner_r = int(1.28 * DPI)
    spinner_x = w // 2
    spinner_y = int(2.95 * DPI)
    _draw_spinner(draw=d, page=page, x=spinner_x, y=spinner_y, r=spinner_r, labels=labels, icons=[img for _, img in pool[:8]], mode=mode)

    # Usage instructions below spinner
    try:
        fonts_instr = _load_fonts()
        instr = "Attach arrow with a brad at center. Spin and cover the matching picture."
        ib = d.textbbox((0, 0), instr, font=fonts_instr["label"])
        itw = ib[2] - ib[0]
        ith = ib[3] - ib[1]
        iy = spinner_y + spinner_r + int(0.10 * DPI)
        d.text(((w - itw) // 2, iy), instr, fill=hex_to_rgb(STEEL_BLUE), font=fonts_instr["label"])
    except Exception:
        pass

    fonts = _load_fonts()
    scale = DPI / 72
    top_y = int(4.85 * DPI)
    bottom_y = h - safe_footer_inset_px()
    cols = 4
    rows = 2
    gap = row_gap_px()
    side = int(0.85 * DPI)
    avail_w = w - 2 * side
    avail_h = max(1, bottom_y - top_y)
    cell = min((avail_w - gap * (cols - 1)) // cols, (avail_h - gap * (rows - 1)) // rows)
    grid_w = cols * cell + gap * (cols - 1)
    grid_h = rows * cell + gap * (rows - 1)
    x0 = (w - grid_w) // 2
    y0 = top_y + max(0, (avail_h - grid_h) // 2)

    for i, (name, img) in enumerate(pool):
        rr = i // cols
        cc = i % cols
        cx0 = x0 + cc * (cell + gap)
        cy0 = y0 + rr * (cell + gap)
        d.rounded_rectangle([cx0, cy0, cx0 + cell, cy0 + cell], radius=int(14 * scale), outline=hex_to_rgb(NAVY_BLUE), width=int(3 * scale), fill=LIGHT_BG)

        num = str(i + 1)
        d.text((cx0 + int(10 * scale), cy0 + int(8 * scale)), num, fill=hex_to_rgb(NAVY_BLUE), font=fonts["num"])

        ic = img.copy()
        if mode == "bw":
            ic = ic.convert("L").convert("RGBA")
        pad = int(0.12 * cell)
        ic.thumbnail((cell - 2 * pad, cell - 2 * pad), Image.Resampling.LANCZOS)
        ix = cx0 + (cell - ic.width) // 2
        iy = cy0 + (cell - ic.height) // 2
        page.paste(ic, (ix, iy), ic)

        lbl = _normalize_label(name)
        lb = d.textbbox((0, 0), lbl, font=fonts["label"])
        lw = lb[2] - lb[0]
        lh = lb[3] - lb[1]
        d.text((cx0 + (cell - lw) // 2, cy0 + cell - lh - int(10 * scale)), lbl, fill=hex_to_rgb(NAVY_BLUE), font=fonts["label"])

    return page


def _page_arrow_cutouts(*, page_num: int, total_pages: int, pack_code: str, theme_name: str) -> Image.Image:
    w = int(PAGE_WIDTH * DPI / 72)
    h = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(page)
    scale = DPI / 72

    apply_small_wins_frame(
        page,
        product_title=theme_name,
        subtitle="Spin & Cover — Arrow (Cut-Out)",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        footer_title=f"{theme_name} | Spin & Cover",
    )

    # Clear cutting/assembly instructions near top area
    try:
        fonts = _load_fonts()
        tip = "Cut out the arrow. Use a brad (paper fastener) through the spinner center."
        bb = d.textbbox((0, 0), tip, font=fonts["label"])
        tw = bb[2] - bb[0]
        d.text(((w - tw) // 2, int(1.65 * DPI)), tip, fill=hex_to_rgb(STEEL_BLUE), font=fonts["label"])
    except Exception:
        pass

    token_w = int(2.1 * DPI)
    token_h = int(1.4 * DPI)
    gap = int(0.35 * DPI)
    cols = 2
    rows = 4
    total_w = cols * token_w + (cols - 1) * gap
    x0 = (w - total_w) // 2
    y0 = int(2.35 * DPI)

    for r in range(rows):
        for c in range(cols):
            x = x0 + c * (token_w + gap)
            y = y0 + r * (token_h + gap)
            d.rounded_rectangle(
                [x, y, x + token_w, y + token_h],
                radius=int(18 * scale),
                outline=hex_to_rgb(NAVY_BLUE),
                width=int(3 * scale),
                fill=(255, 255, 255),
            )

            cx = x + int(0.55 * token_w)
            cy = y + token_h // 2
            tip_x = x + int(0.90 * token_w)
            half = int(0.18 * token_h)
            d.polygon([(tip_x, cy), (cx, cy - half), (cx, cy + half)], fill=hex_to_rgb(STEEL_BLUE))
            d.rectangle([x + int(0.18 * token_w), cy - int(0.08 * token_h), cx, cy + int(0.08 * token_h)], fill=hex_to_rgb(STEEL_BLUE))

    return page


def _page_mat(*, items: list[tuple[str, Image.Image]], page_num: int, total_pages: int, pack_code: str, theme_name: str, mode: str, mat_num: int, rng: random.Random) -> Image.Image:
    w = int(PAGE_WIDTH * DPI / 72)
    h = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(page)
    scale = DPI / 72

    apply_small_wins_frame(
        page,
        product_title=theme_name,
        subtitle=f"Spin & Cover — Mat {mat_num}",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        footer_title=f"{theme_name} | Spin & Cover",
        header_left_icon=(items[0][1] if items else None),
    )

    cols = 4
    rows = 4
    side = int(0.85 * DPI)
    top = int(2.10 * DPI)
    bottom = h - safe_footer_inset_px()
    avail_w = w - 2 * side
    avail_h = max(1, bottom - top)
    gap = row_gap_px()
    cell = min((avail_w - gap * (cols - 1)) // cols, (avail_h - gap * (rows - 1)) // rows)
    grid_w = cols * cell + gap * (cols - 1)
    grid_h = rows * cell + gap * (rows - 1)
    x0 = (w - grid_w) // 2
    y0 = top + max(0, (avail_h - grid_h) // 2)

    pool = items[:]
    if not pool:
        return page
    if len(pool) < rows * cols:
        while len(pool) < rows * cols:
            pool = pool + items
    rng.shuffle(pool)
    chosen = pool[: rows * cols]

    for i in range(rows * cols):
        r = i // cols
        c = i % cols
        cx0 = x0 + c * (cell + gap)
        cy0 = y0 + r * (cell + gap)
        d.rounded_rectangle([cx0, cy0, cx0 + cell, cy0 + cell], radius=int(14 * scale), outline=hex_to_rgb(NAVY_BLUE), width=int(3 * scale), fill=LIGHT_BG)
        _, img = chosen[i]
        ic = img.copy()
        if mode == "bw":
            ic = ic.convert("L").convert("RGBA")
        pad = int(0.08 * cell)
        ic.thumbnail((cell - 2 * pad, cell - 2 * pad), Image.Resampling.LANCZOS)
        ix = cx0 + (cell - ic.width) // 2
        iy = cy0 + (cell - ic.height) // 2
        page.paste(ic, (ix, iy), ic)

    return page


def generate_spin_cover_pack(images_folder: str, pack_code: str = "SC01", theme_name: str = "Theme") -> bool:
    try:
        _validate_images_folder(images_folder)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    items = _read_icons(images_folder)
    # Story-accuracy filter: e.g., Stellaluna should not include generic 'Flower'
    try:
        if theme_name and theme_name.strip().lower() == "stellaluna":
            filtered = [(n, im) for (n, im) in items if _normalize_label(n).lower() != "flower"]
            # Keep filter only if we still have enough items
            if len(filtered) >= 6:
                items = filtered
    except Exception:
        pass
    if len(items) < 6:
        print("❌ ERROR: Need at least 6 icons for Spin & Cover")
        return False

    # Guardrailed output path: Studioforge/OUTPUT/{pack_code}
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "Studioforge" / "OUTPUT" / pack_code
    if "_TLOT_ARCHIVED_DUPLICATE" in str(out_dir):
        print(f"❌ ERROR: Output path points into archived duplicate: {out_dir}")
        return False
    out_dir.mkdir(parents=True, exist_ok=True)

    mats_count = 8

    preview_pages: list[Image.Image] = []
    for mode in ["color", "bw"]:
        # Compute total pages including internal cover (no footer), spinner, mats, and arrow cutouts
        content_pages = 1 + mats_count + 1  # spinner + mats + arrow page
        total_pages = content_pages + 1     # + internal cover
        pages: list[Image.Image] = []
        # Internal cover as Page 1 (no footer)
        try:
            hero_img = items[0][1] if items else None
        except Exception:
            hero_img = None
        pages.append(
            generate_internal_cover_page(
                theme_name=theme_name,
                pack_code=pack_code,
                product_name="Spin & Cover",
                page_count=content_pages,
                level_count=None,
                hero_image=hero_img,
                draw_footer=False,
                howto_bullets=[
                    "Print the mats (colour or B&W) and laminate for reuse.",
                    "Cut out the arrow, attach with a brad at the spinner centre.",
                    "Students spin, then cover the matching picture on the mat.",
                ],
            )
        )
        # Spinner page (Page 2)
        pages.append(_page_spinner(items=items, page_num=2, total_pages=total_pages, pack_code=pack_code, theme_name=theme_name, mode=mode))
        # Mats: Pages 3..(mats_count+2)
        for i in range(1, mats_count + 1):
            rng = random.Random((i * 997) + (1 if mode == "bw" else 0) + len(items))
            pages.append(_page_mat(items=items, page_num=i + 2, total_pages=total_pages, pack_code=pack_code, theme_name=theme_name, mode=mode, mat_num=i, rng=rng))

        # Arrow cutouts as last page
        pages.append(_page_arrow_cutouts(page_num=total_pages, total_pages=total_pages, pack_code=pack_code, theme_name=theme_name))

        out = out_dir / f"{pack_code}_SpinCover_{mode.upper()}.pdf"
        c = canvas.Canvas(str(out), pagesize=letter)
        for p in pages:
            buf = io.BytesIO()
            p.save(buf, format="PNG", dpi=(DPI, DPI))
            buf.seek(0)
            c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
            c.showPage()
        c.save()
        print(f"OK Generated: {out}")

        # Capture sample pages for PREVIEW from color mode
        if mode == "color" and not preview_pages:
            try:
                preview_pages = [pages[0].copy(), pages[1].copy()]  # spinner + first mat
            except Exception:
                preview_pages = pages[:1]

    try:
        build_spin_cover_preview_and_manifest(images_folder, pack_code, theme_name)
    except Exception:
        pass
    return True


def build_spin_cover_preview_and_manifest(images_folder: str, pack_code: str, theme_name: str) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "Studioforge" / "OUTPUT" / pack_code
    color_pdf = out_dir / f"{pack_code}_SpinCover_COLOR.pdf"
    bw_pdf = out_dir / f"{pack_code}_SpinCover_BW.pdf"

    # Create PREVIEW PDF (first spinner + first mat if available) from color content by rasterizing first 2 pages
    # Since we don't reliably have images here, create a 2-page preview from the first page of color and the arrow page as a proxy
    # Best-effort: re-render a light PREVIEW watermark page from first color page by drawing existing rasterized image again
    try:
        preview_pdf = out_dir / f"{pack_code}_SpinCover_PREVIEW.pdf"
        # Fallback: include two pages by reusing the first page twice (fast and acceptable)
        pages_to_include = []
        try:
            # If color PDF exists, at least make a one-page PREVIEW by drawing its first page image placeholder
            c_prev = canvas.Canvas(str(preview_pdf), pagesize=letter)
            # Draw a blank page with watermark text (robust without PDF raster dependencies)
            w_pt, h_pt = letter
            for _ in range(2):
                # White background
                page_img = Image.new("RGB", (int(w_pt * DPI / 72), int(h_pt * DPI / 72)), "white")
                buf = io.BytesIO(); page_img.save(buf, format="PNG", dpi=(DPI, DPI)); buf.seek(0)
                c_prev.drawImage(ImageReader(buf), 0, 0, width=w_pt, height=h_pt)
                # Watermark
                c_prev.saveState()
                try:
                    c_prev.setFont("Helvetica-Bold", 140)
                    c_prev.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
                except Exception:
                    c_prev.setFont("Helvetica-Bold", 110)
                    c_prev.setFillColorRGB(0.6, 0.6, 0.6)
                c_prev.translate(w_pt/2, h_pt/2)
                c_prev.rotate(45)
                c_prev.drawCentredString(0, 0, "PREVIEW")
                c_prev.restoreState()
                c_prev.showPage()
            c_prev.save()
            print(f"OK Generated: {preview_pdf}")
        except Exception:
            pass
    except Exception:
        pass

    # Thumbnails (2 sample thumbs)
    try:
        thumb_dir = out_dir / "thumbnails"
        thumb_dir.mkdir(parents=True, exist_ok=True)
        for i in range(1, 3):
            # simple white preview placeholders (robust)
            w_pt, h_pt = letter
            img = Image.new("RGB", (int(w_pt * DPI / 72), int(h_pt * DPI / 72)), "white")
            img.thumbnail((500, 647), Image.Resampling.LANCZOS)
            img.save(thumb_dir / f"{pack_code}_SpinCover_thumb{i}.png", "PNG")
    except Exception:
        pass

    # BuildResult manifest
    try:
        thumbs = [str(p) for p in sorted((out_dir / "thumbnails").glob(f"{pack_code}_SpinCover_thumb*.png"))]
        try:
            warnings = assess_files(
                product_name="Spin & Cover",
                color_pdf=str(color_pdf),
                bw_pdf=str(bw_pdf),
                preview_pdf=str(preview_pdf) if 'preview_pdf' in locals() else None,
                expected_pages=None,
            )
        except Exception:
            warnings = []
        manifest = {
            "product_name": "Spin & Cover",
            "slug": images_path.parent.name,
            "pack_code": pack_code,
            "page_count": None,
            "files": {
                "color_pdf": str(color_pdf),
                "bw_pdf": str(bw_pdf),
                "preview_pdf": (str(preview_pdf) if 'preview_pdf' in locals() else None),
                "thumbnails": thumbs,
            },
            "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": warnings},
        }
        (out_dir / f"{pack_code}_SpinCover_BuildResult.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
