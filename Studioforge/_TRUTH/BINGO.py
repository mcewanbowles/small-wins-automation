from __future__ import annotations

import io
import random
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from utils.sws_design import (
    generate_internal_cover_page,
    generate_teacher_cover_page,
    shrink_font_to_fit_with_pt,
    normalize_text,
    draw_aac_strip,
    _brand_font_pt,
    apply_small_wins_frame,
    safe_footer_inset_px,
    resolve_theme_assets_from_images_folder,
    generate_storage_label_page,
)
from utils.qa import assess_files
import json
from datetime import datetime
from utils.UNIVERSAL_STANDARDS import SWS_TEAL, SWS_NAVY, SWS_TEAL_LT, MID_GRAY
# Lucky8 frame is deprecated for activity pages — use apply_small_wins_frame

PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

TITLE_BLUE = SWS_TEAL
NAVY_BLUE = SWS_NAVY
LIGHT_BLUE = SWS_TEAL_LT


def hex_to_rgb(hex_color: str):
    hex_color = str(hex_color).lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _load_fonts():
    s = DPI / 72
    return {
        "title": _brand_font_pt(int(28 * 72 / DPI * DPI / 72), bold=True, brand="poppins"),
        "subtitle": _brand_font_pt(int(14 * 72 / DPI * DPI / 72), bold=False, brand="poppins"),
        "label": _brand_font_pt(int(16 * 72 / DPI * DPI / 72), bold=True, brand="poppins"),
        "footer": _brand_font_pt(int(11 * 72 / DPI * DPI / 72), bold=False, brand="poppins"),
        "copyright": _brand_font_pt(int(8 * 72 / DPI * DPI / 72), bold=False, brand="poppins"),
    }


def _read_icons(images_folder: str) -> list[tuple[str, Image.Image]]:
    p = Path(images_folder)
    files = sorted([
        f for f in p.glob("*.png")
        if f.is_file()
        and not f.name.startswith(".")
        and not any(k in str(f).lower() for k in ["aac_core", "aac_core_text", "global"]) 
    ])
    items: list[tuple[str, Image.Image]] = []
    for f in files:
        try:
            img = Image.open(f)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            name = f.stem.replace("_", " ").replace("-", " ").title()
            items.append((name, img))
        except Exception:
            continue
    return items

def validate_images_folder(images_folder: str) -> list[Path]:
    p = Path(images_folder)
    if "_TLOT_ARCHIVED_DUPLICATE" in str(p):
        raise ValueError(
            f"Images folder is inside the archived duplicate tree: {p}\n"
            f"Use Studioforge/assets/themes/{'{slug}'}/activity_images/ instead."
        )
    sp = str(p).lower()
    if any(k in sp for k in ["aac_core", "aac_core_text", "global"]):
        raise ValueError(
            f"Bingo must not read from AAC core or global folders: {p}. Use assets/themes/<slug>/activity_images."
        )
    images = sorted(list(p.glob("*.png"))) + sorted(list(p.glob("*.jpg")))
    if len(images) < 4:
        raise ValueError(f"Too few images in {p} — found {len(images)}, need at least 4.")
    return images


def _load_header_icon(theme_slug: str) -> Image.Image | None:
    try:
        repo_root = Path(__file__).resolve().parents[3]
        theme_dir = repo_root / "assets" / "themes" / theme_slug
        # Prefer explicit hero assets used on covers
        hero_candidates = [
            # Character heroes first (avoid generic placeholders)
            theme_dir / "characters" / "llama_llama.png",
            theme_dir / "characters" / "mama_llama.png",
            theme_dir / "hero_header.png",
            theme_dir / "heroes" / "hero_header.png",
            theme_dir / "characters" / "hero_header.png",
            theme_dir / "characters" / "header_icon.png",
            theme_dir / "header_icon.png",
            theme_dir / "hero.png",
            theme_dir / "heroes" / "hero.png",
            theme_dir / "characters" / "hero.png",
        ]
        for hp in hero_candidates:
            if hp.exists():
                try:
                    im = Image.open(str(hp))
                    return _prepare_icon(im)
                except Exception:
                    continue
        # Fallback: prefer likely hero-like filenames (e.g., 'llama', 'hero', 'main', 'title'), else first PNG
        for sub in ["icons", "activity_images"]:
            p = theme_dir / sub
            if p.exists():
                files = sorted(p.glob("*.png"))
                prefs = [f for f in files if any(k in f.stem.lower() for k in ["llama", "hero", "main", "title"])]
                for f in prefs + files:
                    try:
                        im = Image.open(f)
                        return _prepare_icon(im)
                    except Exception:
                        continue
    except Exception:
        return None
    return None


def _normalize_label(name: str) -> str:
    s = str(name).strip()
    s = re.sub(r"\([^)]*\)", "", s).strip()
    s = re.sub(r"\s+\d+$", "", s).strip()
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


def _theme_dir_for_images(images_folder: str) -> Path:
    path = Path(images_folder).resolve()
    if path.name == "icons" and path.parent.name == ".sf_build":
        return path.parent.parent
    return path.parent


def _prepare_icon(image: Image.Image) -> Image.Image:
    icon = image.convert("RGBA")
    edge = max(2, int(icon.width * 0.02))
    icon = icon.crop((edge, edge, icon.width - edge, icon.height - edge))
    pixels = []
    source = icon.get_flattened_data() if hasattr(icon, "get_flattened_data") else icon.getdata()
    for red, green, blue, alpha in source:
        neutral = max(red, green, blue) - min(red, green, blue) < 12 and (red + green + blue) / 3 > 150
        pixels.append((red, green, blue, 0 if neutral else alpha))
    icon.putdata(pixels)
    bounds = icon.getchannel("A").getbbox()
    return icon.crop(bounds) if bounds else icon


def _load_reviewed_items(images_folder: str) -> tuple[list[tuple[str, Image.Image]], Path]:
    theme = _theme_dir_for_images(images_folder)
    source = theme / "config" / "bingo.json"
    data = json.loads(source.read_text(encoding="utf-8")) if source.exists() else None
    entries = data.get("items") if isinstance(data, dict) else None
    if not entries or len(entries) != 8:
        raise ValueError(f"Bingo requires exactly eight reviewed items: {source}")
    items = []
    for entry in entries:
        path = Path(images_folder) / f"{entry.get('image_key')}.png"
        label = str(entry.get("label") or "").strip()
        if not path.exists() or not label:
            raise ValueError(f"Missing reviewed Bingo item: {entry}")
        items.append((label, _prepare_icon(Image.open(path))))
    return items, source


def _draw_bingo_card(*, items: list[tuple[str, Image.Image]], rows: int, cols: int, page_num: int, total_pages: int, pack_code: str, theme_name: str, card_num: int) -> Image.Image:
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(page)
    fonts = _load_fonts()
    s = DPI / 72

    title = "Bingo"
    tb = draw.textbbox((0, 0), title, font=fonts["title"])
    draw.text(((img_width - (tb[2] - tb[0])) // 2, int(18 * s)), title, fill=hex_to_rgb(TITLE_BLUE), font=fonts["title"])

    subtitle = f"Card {card_num}"
    sb = draw.textbbox((0, 0), subtitle, font=fonts["subtitle"])
    draw.text(((img_width - (sb[2] - sb[0])) // 2, int(55 * s)), subtitle, fill=hex_to_rgb(NAVY_BLUE), font=fonts["subtitle"])

    border_margin = int(20 * s)
    grid_top = int(95 * s)
    grid_left = border_margin
    grid_right = img_width - border_margin
    grid_bottom = img_height - int(105 * s)

    grid_w = grid_right - grid_left
    grid_h = grid_bottom - grid_top

    cell = min(grid_w // cols, grid_h // rows)
    grid_w = cell * cols
    grid_h = cell * rows
    grid_left = (img_width - grid_w) // 2
    grid_top = grid_top + max(0, (grid_h - grid_h) // 2)

    # background panel
    draw.rounded_rectangle(
        [grid_left - int(8 * s), grid_top - int(8 * s), grid_left + grid_w + int(8 * s), grid_top + grid_h + int(8 * s)],
        radius=int(12 * s),
        fill=hex_to_rgb(LIGHT_BLUE),
        outline=hex_to_rgb(NAVY_BLUE),
        width=int(2 * s),
    )

    for r in range(rows):
        for c in range(cols):
            x0 = grid_left + c * cell
            y0 = grid_top + r * cell
            x1 = x0 + cell
            y1 = y0 + cell
            draw.rounded_rectangle([x0, y0, x1, y1], radius=int(8 * s), outline=hex_to_rgb(NAVY_BLUE), fill="white", width=int(2 * s))

    # Fill with random items
    need = rows * cols
    pool = items[:]
    if len(pool) < need:
        while len(pool) < need:
            pool = pool + items
    random.shuffle(pool)
    chosen = pool[:need]

    for idx, (name, img) in enumerate(chosen):
        r = idx // cols
        c = idx % cols
        x0 = grid_left + c * cell
        y0 = grid_top + r * cell

        if text_only:
            txt = normalize_text(_normalize_label(name))
            max_w = int(0.86 * cell)
            f_lbl, pt = shrink_font_to_fit_with_pt(
                txt,
                base_pt=16,
                max_width_px=max_w,
                bold=True,
                brand="poppins",
                min_pt=8,
            )
            bb = draw.textbbox((0, 0), txt, font=f_lbl)
            tw = bb[2] - bb[0]
            th = bb[3] - bb[1]
            draw.text((x0 + (cell - tw) // 2, y0 + (cell - th) // 2), txt, fill=hex_to_rgb(NAVY_BLUE), font=f_lbl)
            if fit_warnings is not None and pt <= 12:
                fit_warnings.append(f"Bingo text-only label shrunk to {pt}pt on page {page_num}: '{txt}'")
            continue

        icon_size = max(1, int(0.70 * cell))
        ic = img.copy()
        ic.thumbnail((icon_size, icon_size), Image.Resampling.LANCZOS)
        ix = x0 + (cell - ic.width) // 2
        iy = y0 + (cell - ic.height) // 2
        page.paste(ic, (ix, iy), ic)

        if show_labels:
            lbl = normalize_text(_normalize_label(name))
            max_w = int(0.86 * cell)
            f_sub, pt = shrink_font_to_fit_with_pt(
                lbl,
                base_pt=14,
                max_width_px=max_w,
                bold=True,
                brand="poppins",
                min_pt=8,
            )
            lb = draw.textbbox((0, 0), lbl, font=f_sub)
            lw = lb[2] - lb[0]
            lh = lb[3] - lb[1]
            draw.text(
                (x0 + (cell - lw) // 2, y0 + cell - lh - int(0.08 * cell)),
                lbl,
                fill=hex_to_rgb(NAVY_BLUE),
                font=f_sub,
            )
            if fit_warnings is not None and pt <= 10:
                fit_warnings.append(f"Bingo label shrunk to {pt}pt on page {page_num}: '{lbl}'")

    # AAC participation strip at bottom (fixed prompts)
    try:
        draw_aac_strip(page, words=["I have it", "Bingo!", "again", "more"])
    except Exception:
        pass

    return page


def _choose_cells(*, rows: int, cols: int, free_center: bool, blanks_count: int, rng: random.Random) -> set[int]:
    total = rows * cols
    blanks: set[int] = set()

    if free_center and rows % 2 == 1 and cols % 2 == 1:
        blanks.add((rows // 2) * cols + (cols // 2))

    target = max(0, int(blanks_count))
    attempts = 0
    while len(blanks) < min(total, target + len(blanks)) and attempts < 10000:
        attempts += 1
        blanks.add(rng.randrange(0, total))

    return blanks


def _draw_bingo_card_leveled(
    *,
    items: list[tuple[str, Image.Image]],
    rows: int,
    cols: int,
    page_num: int,
    total_pages: int,
    pack_code: str,
    theme_name: str,
    theme_slug: str,
    card_num: int,
    level_label: str,
    level_num: int,
    free_center: bool,
    blanks_count: int,
    rng: random.Random,
    show_labels: bool,
    text_only: bool,
    fit_warnings: list[str] | None = None,
) -> Image.Image:
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(page)
    fonts = _load_fonts()
    s = DPI / 72
    # Universal Small Wins frame (STEL_MATCH standard) with hero in header and level pill
    header_icon = _load_header_icon(theme_slug)
    apply_small_wins_frame(
        page,
        product_title="Bingo",
        subtitle=f"Card {card_num} — {level_label}",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=level_num,
        header_left_icon=header_icon,
        show_data_strip=False,
        draw_footer=True,
        draw_subtitle=True,
        header_height_px=int(0.92 * DPI),
        accent_margin_px=int(0.12 * DPI),
        footer_y_offset_px=int(0.08 * DPI),
    )

    # Content area using universal frame geometry: below header, above footer
    scale = DPI / 72
    border_margin = int(0.25 * DPI)
    inner_pad = int(0.10 * DPI)
    header_h = int(1.80 * DPI)
    content_left = border_margin + inner_pad
    content_right = img_width - border_margin - inner_pad
    content_top = header_h + int(0.15 * DPI)
    content_bottom = img_height - safe_footer_inset_px()

    # Add inner board padding so grid fits cleanly inside borders
    board_pad = int(0.22 * DPI)
    grid_area_left = content_left + board_pad
    grid_area_right = content_right - board_pad
    grid_area_top = content_top + board_pad
    grid_area_bottom = content_bottom - board_pad
    available_w = max(1, grid_area_right - grid_area_left)
    available_h = max(1, grid_area_bottom - grid_area_top)

    cell = max(1, min(available_w // cols, available_h // rows))
    grid_w = cell * cols
    grid_h = cell * rows
    grid_left = grid_area_left + (available_w - grid_w) // 2
    grid_top = grid_area_top + (available_h - grid_h) // 2

    draw.rounded_rectangle(
        [grid_left - int(8 * s), grid_top - int(8 * s), grid_left + grid_w + int(8 * s), grid_top + grid_h + int(8 * s)],
        radius=int(12 * s),
        fill=hex_to_rgb(LIGHT_BLUE),
        outline=hex_to_rgb(NAVY_BLUE),
        width=int(2 * s),
    )

    blank_cells = _choose_cells(rows=rows, cols=cols, free_center=free_center, blanks_count=blanks_count, rng=rng)

    for r in range(rows):
        for c in range(cols):
            x0 = grid_left + c * cell
            y0 = grid_top + r * cell
            x1 = x0 + cell
            y1 = y0 + cell
            draw.rectangle([x0, y0, x1, y1], outline=hex_to_rgb(NAVY_BLUE), fill="white", width=int(2 * s))

    need = rows * cols - len(blank_cells)
    # Choose items to fill all required cells. If the pool is smaller than needed,
    # repeat-shuffle to avoid empty cells while keeping variety.
    if len(items) >= need:
        pool = items[:]
        rng.shuffle(pool)
        chosen = pool[:need]
    else:
        pool: list[tuple[str, Image.Image]] = []
        while len(pool) < need:
            tmp = items[:]
            rng.shuffle(tmp)
            pool.extend(tmp)
        chosen = pool[:need]
    it_idx = 0

    for idx in range(rows * cols):
        if idx in blank_cells:
            if free_center and rows % 2 == 1 and cols % 2 == 1 and idx == (rows // 2) * cols + (cols // 2):
                r = idx // cols
                c = idx % cols
                x0 = grid_left + c * cell
                y0 = grid_top + r * cell
                txt = "FREE"
                bbox = draw.textbbox((0, 0), txt, font=fonts["label"])
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                draw.text((x0 + (cell - tw) // 2, y0 + (cell - th) // 2), txt, fill=hex_to_rgb(NAVY_BLUE), font=fonts["label"])
            continue

        if it_idx >= len(chosen):
            continue

        name, img = chosen[it_idx]
        it_idx += 1

        r = idx // cols
        c = idx % cols
        x0 = grid_left + c * cell
        y0 = grid_top + r * cell

        if text_only:
            txt = _normalize_label(name)
            bb = draw.textbbox((0, 0), txt, font=fonts["label"])
            tw = bb[2] - bb[0]
            th = bb[3] - bb[1]
            draw.text((x0 + (cell - tw) // 2, y0 + (cell - th) // 2), txt, fill=hex_to_rgb(NAVY_BLUE), font=fonts["label"])
            continue

        # Maximize icon size inside each cell: ultra-minimal padding, no labels
        pad = int(0.02 * cell)
        label_h = int(0.22 * cell) if show_labels else 0
        box = max(1, cell - 2 * pad - label_h)
        ic = _prepare_icon(img)
        if ic.width > 0 and ic.height > 0:
            ratio = min(box / ic.width, box / ic.height) * 0.86
            ic = ic.resize((max(1, int(ic.width * ratio)), max(1, int(ic.height * ratio))), Image.Resampling.LANCZOS)
        ix = x0 + (cell - ic.width) // 2
        iy = y0 + (cell - ic.height) // 2
        page.paste(ic, (ix, iy), ic)

        if show_labels:
            label = normalize_text(_normalize_label(name))
            label_font, _ = shrink_font_to_fit_with_pt(label, base_pt=13, max_width_px=int(0.86 * cell), bold=True, brand="poppins", min_pt=9)
            bounds = draw.textbbox((0, 0), label, font=label_font)
            label_w, label_height = bounds[2] - bounds[0], bounds[3] - bounds[1]
            draw.text((x0 + (cell - label_w) // 2 - bounds[0], y0 + cell - label_height - int(0.06 * cell) - bounds[1]), label, fill=hex_to_rgb(NAVY_BLUE), font=label_font)

        # Labels suppressed to prioritize icon size

    return page


def _draw_calling_cards(*, items: list[tuple[str, Image.Image]], page_num: int, total_pages: int, pack_code: str, theme_name: str, theme_slug: str) -> Image.Image:
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(page)
    fonts = _load_fonts()
    s = DPI / 72
    # Universal frame (STEL_MATCH) with hero in header and no level pill
    header_icon = _load_header_icon(theme_slug)
    apply_small_wins_frame(
        page,
        product_title="Bingo",
        subtitle="Calling Cards",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        header_left_icon=header_icon,
        show_data_strip=False,
        draw_footer=True,
        draw_subtitle=True,
        header_height_px=int(0.92 * DPI),
        accent_margin_px=int(0.12 * DPI),
        footer_y_offset_px=int(0.08 * DPI),
    )

    cols = 4
    rows = 2
    margin = int(28 * s)
    # Content area using universal frame geometry
    border_margin = int(0.25 * DPI)
    inner_pad = int(0.10 * DPI)
    header_h = int(1.80 * DPI)
    left = border_margin + inner_pad
    right = img_width - border_margin - inner_pad
    top = header_h + int(0.15 * DPI)
    bottom = img_height - safe_footer_inset_px()
    w = (right - left) - 2 * margin
    h = (bottom - top) - margin
    cell = min(max(1, w // cols), max(1, h // rows))

    start_x = left + (max(1, (right - left)) - cols * cell) // 2
    start_y = top + max(0, ((bottom - top) - rows * cell) // 2)

    pool = items[: cols * rows]

    for i in range(cols * rows):
        r = i // cols
        c = i % cols
        x0 = start_x + c * cell
        y0 = start_y + r * cell
        x1 = x0 + cell
        y1 = y0 + cell
        draw.rounded_rectangle([x0, y0, x1, y1], radius=int(8 * s), outline=hex_to_rgb(NAVY_BLUE), fill="white", width=int(2 * s))

        name, img = pool[i]
        # Larger icons on calling cards for visibility
        icon_size = max(1, int(0.68 * cell))
        ic = _prepare_icon(img)
        if ic.width > 0 and ic.height > 0:
            ratio = min(icon_size / ic.width, icon_size / ic.height)
            ic = ic.resize((max(1, int(ic.width * ratio)), max(1, int(ic.height * ratio))), Image.Resampling.LANCZOS)
        ix = x0 + (cell - ic.width) // 2
        iy = y0 + int(0.06 * cell)
        page.paste(ic, (ix, iy), ic)
        label = normalize_text(_normalize_label(name))
        label_font, _ = shrink_font_to_fit_with_pt(label, base_pt=12, max_width_px=int(0.85 * cell), bold=True, brand="poppins", min_pt=9)
        bounds = draw.textbbox((0, 0), label, font=label_font)
        label_w, label_h = bounds[2] - bounds[0], bounds[3] - bounds[1]
        draw.text((x0 + (cell - label_w) // 2 - bounds[0], y0 + cell - label_h - int(0.08 * cell) - bounds[1]), label, fill=hex_to_rgb(NAVY_BLUE), font=label_font)

    return page


def generate_bingo_pack(images_folder: str, pack_code: str = "BINGO01", theme_name: str = "Theme", output_dir: str | None = None) -> bool:
    try:
        validate_images_folder(images_folder)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    try:
        items, bingo_source = _load_reviewed_items(images_folder)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

    images_path = Path(images_folder)
    theme_dir = _theme_dir_for_images(images_folder)
    repo_root = Path(__file__).resolve().parents[3]
    out_dir = Path(output_dir) if output_dir else (theme_dir / "OUTPUT")
    if "_TLOT_ARCHIVED_DUPLICATE" in str(out_dir):
        raise ValueError(
            f"Output path points into the archived duplicate folder: {out_dir}\n"
            f"This folder is read-only archived content. Use Studioforge/OUTPUT/ instead."
        )
    out_dir.mkdir(parents=True, exist_ok=True)

    cards_count = 4
    levels = [
        {"level": 1, "label": "Supported — icons and labels", "rows": 2, "cols": 2, "free_center": False, "blanks": 0, "show_labels": True, "text_only": False},
        {"level": 2, "label": "Developing — icons", "rows": 2, "cols": 3, "free_center": False, "blanks": 0, "show_labels": False, "text_only": False},
        {"level": 3, "label": "Independent — larger grid", "rows": 3, "cols": 3, "free_center": True, "blanks": 0, "show_labels": False, "text_only": False},
        {"level": 4, "label": "Extended — printed words", "rows": 3, "cols": 3, "free_center": True, "blanks": 0, "show_labels": False, "text_only": True},
    ]

    page_count = cards_count * len(levels) + 1 + 1  # boards + calling cards + storage label
    total_pages = page_count  # cover page is added later during packaging

    text_fit_warnings: list[str] = []

    def _load_cover_cfg(theme_slug: str) -> dict:
        cfg: dict = {}
        try:
            repo_root = Path(__file__).resolve().parents[3]
            theme_dir = repo_root / "assets" / "themes" / theme_slug
            cover_dir = theme_dir / "cover_config"
            act = "bingo"
            per = cover_dir / f"{act}.json"
            shared = cover_dir / "shared.json"
            if per.exists():
                pd = json.loads(per.read_text(encoding="utf-8"))
                if isinstance(pd, dict):
                    cfg = pd
                if shared.exists():
                    try:
                        sd = json.loads(shared.read_text(encoding="utf-8"))
                        if isinstance(sd, dict):
                            m = {}
                            m.update(sd)
                            m.update(cfg)
                            cfg = m
                    except Exception:
                        pass
            else:
                legacy = theme_dir / "cover_config.json"
                if legacy.exists():
                    ld = json.loads(legacy.read_text(encoding="utf-8"))
                    if isinstance(ld, dict):
                        if "bingo" in ld and isinstance(ld["bingo"], dict):
                            shared_obj = ld.get("shared") if isinstance(ld.get("shared"), dict) else {}
                            m = {}
                            m.update(shared_obj or {})
                            m.update(ld["bingo"])  # type: ignore[index]
                            cfg = m
                        else:
                            cfg = ld
        except Exception:
            cfg = {}
        return cfg

    def build_pages_for_mode(mode: str) -> list[Image.Image]:
        pages: list[Image.Image] = []
        theme_slug = images_path.parent.name
        hero_used_path: str | None = None
        hero = _load_header_icon(theme_slug)
        cover_cfg = _load_cover_cfg(theme_slug)
        rope = cover_cfg.get("rope") if isinstance(cover_cfg, dict) else None
        hero_path_str = None
        book_cover_path_str = None
        try:
            theme_dir = repo_root / "assets" / "themes" / theme_slug
            hero_candidates = [
                # Prefer explicit character heroes first (avoid generic placeholders)
                theme_dir / "characters" / "llama_llama.png",
                theme_dir / "characters" / "mama_llama.png",
                theme_dir / "hero_header.png",
                theme_dir / "heroes" / "hero_header.png",
                theme_dir / "characters" / "hero_header.png",
                theme_dir / "characters" / "header_icon.png",
                theme_dir / "header_icon.png",
                theme_dir / "hero.png",
                theme_dir / "heroes" / "hero.png",
                theme_dir / "characters" / "hero.png",
            ]
            for hp in hero_candidates:
                if hp.exists():
                    hero_path_str = str(hp)
                    break
            # Strict character-first: if we resolved a path from the ordered list,
            # load it and override any previously loaded hero image
            if hero_path_str:
                try:
                    _im_h = Image.open(hero_path_str)
                    hero = _im_h.convert("RGBA") if _im_h.mode != "RGBA" else _im_h
                    hero_used_path = hero_path_str
                except Exception:
                    pass
            cover_names = [
                "book_cover", "cover", "front_cover", "bookfront", "book", "cover_reference"
            ]
            cover_subdirs = [theme_dir, theme_dir / "covers", theme_dir / "images", theme_dir / "marketing", theme_dir / "book"]
            exts = ["png", "jpg", "jpeg", "webp"]
            for sd in cover_subdirs:
                for nm in cover_names:
                    for ex in exts:
                        fp = sd / f"{nm}.{ex}"
                        if fp.exists():
                            book_cover_path_str = str(fp)
                            break
                    if book_cover_path_str:
                        break
                if book_cover_path_str:
                    break
            # Fallback to shared resolver if either is still missing
            try:
                auto_img, auto_hero_path, auto_book = resolve_theme_assets_from_images_folder(str(images_path))
                if hero is None and auto_img is not None:
                    hero = auto_img
                    hero_used_path = auto_hero_path or "<inline-from-auto>"
                if not hero_path_str and auto_hero_path:
                    hero_path_str = auto_hero_path
                if not book_cover_path_str and auto_book:
                    book_cover_path_str = auto_book
            except Exception:
                pass
        except Exception:
            hero_path_str = None
            book_cover_path_str = None
        # Teacher cover page is intentionally NOT generated here; it is added
        # later during packaging. Strict character-first hero resolution still
        # runs above so downstream consumers can reuse the resolved assets.
        page_num = 1
        for lv in levels:
            for card in range(1, cards_count + 1):
                rng = random.Random((lv["level"] * 100000) + (card * 997) + (1 if mode == "bw" else 0) + len(items))
                pages.append(
                    _draw_bingo_card_leveled(
                        items=items,
                        rows=lv["rows"],
                        cols=lv["cols"],
                        page_num=page_num,
                        total_pages=total_pages,
                        pack_code=pack_code,
                        theme_name=theme_name,
                        theme_slug=theme_dir.name,
                        card_num=card,
                        level_label=lv["label"],
                        level_num=lv["level"],
                        free_center=bool(lv.get("free_center")),
                        blanks_count=int(lv.get("blanks", 0)),
                        rng=rng,
                        show_labels=bool(lv.get("show_labels")),
                        text_only=bool(lv.get("text_only")),
                        fit_warnings=text_fit_warnings,
                    )
                )
                page_num += 1

        pages.append(
            _draw_calling_cards(
                items=items,
                page_num=page_num,
                total_pages=total_pages,
                pack_code=pack_code,
                theme_name=theme_name,
                theme_slug=theme_dir.name,
            )
        )
        # Storage label page
        pages.append(generate_storage_label_page(
            product_title="Differentiated Bingo",
            theme_name=theme_name,
            pack_code=pack_code,
            page_num=total_pages,
            total_pages=total_pages,
            labels=[{"header": "Bingo Calling Cards", "subtitle": "4 Levels — Picture + Word"}],
            footer_title=f"{theme_name} | Bingo",
        ))
        return pages

    pages_color = build_pages_for_mode("color")
    pdf_path = out_dir / f"{pack_code}_Bingo_COLOR.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    for p in pages_color:
        buf = io.BytesIO()
        p.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    c.save()

    pages_bw = build_pages_for_mode("bw")
    bw_path = out_dir / f"{pack_code}_Bingo_BW.pdf"
    c_bw = canvas.Canvas(str(bw_path), pagesize=letter)
    for p in pages_bw:
        gray = p.convert("L").convert("RGB")
        buf = io.BytesIO()
        gray.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c_bw.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c_bw.showPage()
    c_bw.save()

    preview_path = out_dir / f"{pack_code}_Bingo_PREVIEW.pdf"
    c_prev = canvas.Canvas(str(preview_path), pagesize=letter)
    preview_pages = [pages_color[index] for index in (0, 1, 5, 9, 13, len(pages_color) - 1) if index < len(pages_color)]
    for p in preview_pages:
        buf = io.BytesIO()
        p.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c_prev.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        # Watermark overlay
        c_prev.saveState()
        try:
            c_prev.setFont("Helvetica-Bold", 140)
            c_prev.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
        except Exception:
            c_prev.setFont("Helvetica-Bold", 110)
            c_prev.setFillColorRGB(0.6, 0.6, 0.6)
        c_prev.translate(PAGE_WIDTH/2, PAGE_HEIGHT/2)
        c_prev.rotate(45)
        c_prev.drawCentredString(0, 0, "PREVIEW")
        c_prev.restoreState()
        c_prev.showPage()
    c_prev.save()

    # Mandatory QA PNG exports
    try:
        qa_dir = out_dir / "QA_OUT"
        qa_dir.mkdir(parents=True, exist_ok=True)
        # cover
        pages_color[0].save(qa_dir / "cover.png", format="PNG", dpi=(DPI, DPI))
        # first activity page (after cover)
        if len(pages_color) > 1:
            pages_color[1].save(qa_dir / "page_first.png", format="PNG", dpi=(DPI, DPI))
        # mid page
        mid_idx = max(0, len(pages_color) // 2)
        pages_color[min(mid_idx, len(pages_color) - 1)].save(qa_dir / "page_mid.png", format="PNG", dpi=(DPI, DPI))
        # last page
        pages_color[-1].save(qa_dir / "page_last.png", format="PNG", dpi=(DPI, DPI))
        # first calling cards page (after first block of cards)
        first_call_idx = len(pages_color) - 1 if len(pages_color) > 1 else None
        if isinstance(first_call_idx, int):
            pages_color[first_call_idx].save(qa_dir / "calling_cards.png", format="PNG", dpi=(DPI, DPI))
    except Exception:
        pass

    # Thumbnails (first two color pages)
    try:
        thumbs_dir = out_dir / "thumbnails"
        thumbs_dir.mkdir(parents=True, exist_ok=True)
        for i, p in enumerate(pages_color[:2], start=1):
            th = p.copy()
            th.thumbnail((500, 647), Image.Resampling.LANCZOS)
            th.save(thumbs_dir / f"{pack_code}_Bingo_thumb{i}.png", "PNG")
    except Exception:
        pass

    # BuildResult manifest with QA warnings
    try:
        thumbs = [str(p) for p in sorted((out_dir / "thumbnails").glob(f"{pack_code}_Bingo_thumb*.png"))]
        warnings = []
        try:
            warnings = assess_files(
                product_name="Bingo",
                color_pdf=str(pdf_path),
                bw_pdf=str(bw_path),
                preview_pdf=str(preview_path),
                expected_pages=None,
            )
        except Exception:
            warnings = []
        try:
            warnings.extend(text_fit_warnings)
        except Exception:
            pass
        # Flag unavoidable repeats when the icon pool is smaller than a level's grid
        try:
            dup_levels: list[int] = []
            for lv in levels:
                rows = int(lv.get("rows", 0))
                cols = int(lv.get("cols", 0))
                free_cell = 1 if lv.get("free_center") and rows % 2 == 1 and cols % 2 == 1 else 0
                req = rows * cols - int(lv.get("blanks", 0) or 0) - free_cell
                if len(items) < req:
                    dup_levels.append(int(lv.get("level", 0)))
            if dup_levels:
                warnings.append(
                    f"Icon pool smaller than grid size; repeats unavoidable for levels {dup_levels}. pool={len(items)}"
                )
        except Exception:
            pass
        manifest = {
            "schema_version": 1,
            "status": "pilot_review",
            "product_name": "Differentiated Bingo",
            "slug": theme_dir.name,
            "pack_code": pack_code,
            "generator": str(Path(__file__).resolve()),
            "images_folder": str(images_path.resolve()),
            "source": str(bingo_source),
            "reading_rope": ["Vocabulary", "Sight Recognition"],
            "teacher_review_required": True,
            "unique_icon_count": len(items),
            "page_count": len(pages_color),
            "files": {
                "color_pdf": str(pdf_path),
                "bw_pdf": str(bw_path),
                "preview_pdf": str(preview_path),
                "thumbnails": thumbs,
            },
            "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": warnings},
        }
        (out_dir / f"{pack_code}_Bingo_BuildResult.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    print(f"OK Generated: {pdf_path}")
    print(f"OK Generated: {bw_path}")
    print(f"OK Generated: {preview_path}")
    return True
