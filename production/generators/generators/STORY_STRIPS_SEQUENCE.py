import io
import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from utils.sws_design import apply_small_wins_frame, row_gap_px, safe_footer_inset_px, generate_internal_cover_page, generate_teacher_cover_page, _brand_font_pt
from utils.UNIVERSAL_STANDARDS import SWS_NAVY

# Landscape orientation — multiple levels per page to avoid empty space
PAGE_WIDTH_PT, PAGE_HEIGHT_PT = landscape(letter)
DPI = 300
PAGE_W = int(PAGE_WIDTH_PT * DPI / 72)
PAGE_H = int(PAGE_HEIGHT_PT * DPI / 72)

NAVY = SWS_NAVY


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _load_fonts() -> dict[str, ImageFont.ImageFont]:
    # Brand fonts (Poppins) via shared loader
    return {
        "label": _brand_font_pt(16, bold=True, brand="poppins"),
        "small": _brand_font_pt(10, bold=False, brand="poppins"),
        "prompt": _brand_font_pt(15, bold=True, brand="poppins"),
    }


@dataclass(frozen=True)
class ThemeItem:
    name: str
    image: Image.Image


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


def _read_theme_items(images_folder: str) -> list[ThemeItem]:
    images_dir = Path(images_folder)
    if not images_dir.exists():
        return []
    files = sorted([
        p for p in images_dir.glob("*.png")
        if p.is_file() and not p.name.startswith(".")
        and not any(k in str(p).lower() for k in ["aac_core", "aac_core_text", "global"])
    ])
    out: list[ThemeItem] = []
    for p in files:
        try:
            img = _prepare_icon(Image.open(p))
        except Exception:
            continue
        name = p.stem.replace("_", " ").replace("-", " ").title()
        out.append(ThemeItem(name=name, image=img))
    return out


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
            f"Sequencing must not read from AAC core/global folders: {p}. Use assets/themes/<slug>/activity_images/."
        )
    files = [f for f in p.glob("*.png") if f.is_file() and not f.name.startswith(".")]
    if len(files) < 5:
        raise ValueError(f"Too few images in {p} — found {len(files)}, need at least 5.")


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def _draw_story_strip(
    page: Image.Image,
    *,
    items: list[ThemeItem],
    labels: list[str],
    show_images: bool,
    show_numbers: bool,
    writing_line: bool,
    y_start: int | None = None,
    y_end: int | None = None,
) -> None:
    d = ImageDraw.Draw(page)
    fonts = _load_fonts()
    scale = DPI / 72

    n = len(labels)
    side = int(0.55 * DPI)
    # Default region: below header to above footer
    if y_start is None:
        y_start = int(1.85 * DPI)
    if y_end is None:
        y_end = PAGE_H - safe_footer_inset_px()

    gap = row_gap_px()
    avail_w = PAGE_W - 2 * side
    box_w = (avail_w - (n - 1) * gap) // n
    box_h = min(int(1.85 * DPI), max(int(1.20 * DPI), y_end - y_start))

    total_w = n * box_w + (n - 1) * gap
    x0 = (PAGE_W - total_w) // 2
    y0 = y_start + max(0, ((y_end - y_start) - box_h) // 2)

    for i in range(n):
        x = x0 + i * (box_w + gap)
        y = y0
        d.rounded_rectangle(
            [x, y, x + box_w, y + box_h],
            radius=int(18 * scale),
            outline=hex_to_rgb(NAVY),
            width=int(3 * scale),
            fill=(255, 255, 255),
        )

        if show_numbers:
            num = str(i + 1)
            d.text((x + int(10 * scale), y + int(8 * scale)), num, fill=hex_to_rgb(NAVY), font=fonts["label"])

        # Avoid duplicate numbers: if boxes are numbered, suppress centered label when numeric
        lab = labels[i]
        if not show_numbers and str(lab).strip():
            bounds = d.textbbox((0, 0), lab, font=fonts["label"])
            lw, lh = bounds[2] - bounds[0], bounds[3] - bounds[1]
            d.text((x + (box_w - lw) // 2 - bounds[0], y + int(10 * scale) - bounds[1]), lab, fill=hex_to_rgb(NAVY), font=fonts["label"])

        if writing_line:
            line_y = y + box_h - int(22 * scale)
            d.line(
                [(x + int(14 * scale), line_y), (x + box_w - int(14 * scale), line_y)],
                fill=hex_to_rgb(NAVY),
                width=int(3 * scale),
            )

        if show_images and i < len(items):
            img = items[i].image.copy()
            pad = int(14 * scale)
            top_pad = int(34 * scale)
            bottom_pad = int(34 * scale)
            img.thumbnail((box_w - 2 * pad, box_h - top_pad - bottom_pad), Image.Resampling.LANCZOS)
            ix = x + (box_w - img.width) // 2
            iy = y + top_pad + ((box_h - top_pad - bottom_pad) - img.height) // 2
            page.paste(img, (ix, iy), img)


def _cutouts_page(page: Image.Image, *, items: list[ThemeItem], count: int, y_start: int | None = None, y_end: int | None = None) -> None:
    d = ImageDraw.Draw(page)
    scale = DPI / 72
    fonts = _load_fonts()

    gap = row_gap_px()
    side_margin = int(0.55 * DPI)
    if y_start is None:
        y_start = int(1.85 * DPI)
    if y_end is None:
        y_end = PAGE_H - safe_footer_inset_px()

    total = min(max(1, count), len(items))
    cols = min(5, total)
    rows = (total + cols - 1) // cols
    seq = items[:total]

    avail_h = max(int(1 * DPI), y_end - y_start)
    avail_w = PAGE_W - 2 * side_margin
    box = min(int(1.35 * DPI), (avail_w - (cols - 1) * gap) // cols, (avail_h - (rows - 1) * gap) // rows)

    grid_w = cols * box + (cols - 1) * gap
    grid_h = rows * box + (rows - 1) * gap
    x0 = (PAGE_W - grid_w) // 2
    y0 = y_start + max(0, (avail_h - grid_h) // 2)

    for i in range(total):
        r = i // cols
        c = i % cols
        x = x0 + c * (box + gap)
        y = y0 + r * (box + gap)
        d.rounded_rectangle(
            [x, y, x + box, y + box],
            radius=int(18 * scale),
            outline=hex_to_rgb(NAVY),
            width=int(3 * scale),
            fill=(255, 255, 255),
        )
        img = seq[i].image.copy()
        pad = int(12 * scale)
        img.thumbnail((box - 2 * pad, box - 2 * pad), Image.Resampling.LANCZOS)
        ix = x + (box - img.width) // 2
        iy = y + (box - img.height) // 2
        page.paste(img, (ix, iy), img)
        # Label under image inside the token
        try:
            lbl = seq[i].name
            tw, th = _text_size(d, lbl, fonts["small"])
            d.text((x + (box - tw) // 2, y + box - th - int(6 * scale)), lbl, fill=hex_to_rgb(NAVY), font=fonts["small"])
        except Exception:
            pass


def _page_to_pdf(pages: list[Image.Image], pdf_path: Path, *, watermark_preview: bool) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(pdf_path), pagesize=(PAGE_WIDTH_PT, PAGE_HEIGHT_PT))
    for p in pages:
        buf = io.BytesIO()
        p.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH_PT, height=PAGE_HEIGHT_PT)
        if watermark_preview:
            c.saveState()
            try:
                c.setFont("Helvetica-Bold", 110)
            except Exception:
                pass
            try:
                c.setFillAlpha(0.22)
            except Exception:
                pass
            c.translate(PAGE_WIDTH_PT / 2, PAGE_HEIGHT_PT / 2)
            c.rotate(30)
            c.setFillGray(0.5)
            c.drawCentredString(0, 0, "PREVIEW")
            c.restoreState()
        c.showPage()
    c.save()


def generate_story_strips(
    images_folder: str,
    pack_code: str = "SEQ01",
    theme_name: str = "Theme",
    sequence_order: list[str] | None = None,
    output_dir: str | None = None,
) -> bool:
    try:
        _validate_images_folder(images_folder)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    items = _read_theme_items(images_folder)
    if len(items) < 5:
        print(f"❌ ERROR: Need at least 5 icons in {images_folder} for sequencing")
        return False
    
    # Determine story order
    # If sequence_order provided, use it to sort by filename stem order.
    # Else use filename order (warning logged), never random in published output.
    files = sorted([
        p for p in Path(images_folder).glob("*.png")
        if p.is_file() and not p.name.startswith('.')
        and not any(k in str(p).lower() for k in ["aac_core", "aac_core_text", "global"])
    ])
    stems = [p.stem.lower() for p in files]
    if sequence_order and isinstance(sequence_order, list) and len(sequence_order) > 0:
        order_keys = [Path(s).stem.lower() for s in sequence_order]
        indices = [stems.index(k) for k in order_keys if k in stems]
        if not indices:
            print("❌ ERROR: sequence_order provided but none of the filenames matched theme images.")
            return False
        story = [items[i] for i in indices]
    else:
        print("WARNING: No sequence_order provided — images will appear in filename order.")
        story = items[:]
    story = story[:10]

    # Guardrailed output path: Studioforge/OUTPUT/{pack_code}
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = Path(output_dir) if output_dir else (repo_root / "Studioforge" / "OUTPUT" / pack_code)
    if "_TLOT_ARCHIVED_DUPLICATE" in str(out_dir):
        print(f"❌ ERROR: Output path points into archived duplicate: {out_dir}")
        return False
    out_dir.mkdir(parents=True, exist_ok=True)

    pages: list[Image.Image] = []

    def _make_page(*, subtitle: str, labels: list[str], show_images: bool, show_numbers: bool, writing_line: bool, page_num: int, total_pages: int, level: int | None) -> Image.Image:
        page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        d = ImageDraw.Draw(page)
        fonts = _load_fonts()
        scale = DPI / 72

        prompt = "Look at the pictures. Tell the story in order." if show_images else ("Write or draw what happens." if writing_line else "Cut and paste the pictures in order.")
        pw, ph = _text_size(d, prompt, fonts["prompt"])
        # Place prompt directly under the header accent strip
        d.text(((PAGE_W - pw) // 2, int(1.50 * DPI)), prompt, fill=hex_to_rgb(NAVY), font=fonts["prompt"])

        _draw_story_strip(
            page,
            items=story,
            labels=labels,
            show_images=show_images,
            show_numbers=show_numbers,
            writing_line=writing_line,
        )

        apply_small_wins_frame(
            page,
            product_title="Sequencing",
            subtitle=f"{theme_name} — {subtitle}",
            pack_code=pack_code,
            page_num=page_num,
            total_pages=total_pages,
            level=level,
            footer_title=f"{theme_name} | Sequencing",
            header_left_icon=(hero_img if hero_img is not None else (story[0].image if story else None)),
            footer_y_offset_px=int(0.10 * DPI),
            draw_footer=True,
            draw_subtitle=True,
        )
        return page

    # Three levels + cutouts per brief
    # Level 1: pre-sequenced with numbers
    # Level 2: numbered blank boxes + cutouts (scrambled icons) on separate page
    # Level 3: blank boxes (no numbers) + same cutouts page reused
    level_count = 3
    # Internal teacher cover page as Page 1 (per Lucky 8 master)
    def _load_cover_cfg(theme_slug: str) -> dict:
        cfg: dict = {}
        try:
            repo_root = Path(__file__).resolve().parents[1]
            theme_dir = repo_root / "assets" / "themes" / theme_slug
            cover_dir = theme_dir / "cover_config"
            per = cover_dir / "sequencing.json"
            shared = cover_dir / "shared.json"
            if per.exists():
                pd = per.read_text(encoding="utf-8")
                cfg = __import__('json').loads(pd)
                if shared.exists():
                    try:
                        sd = __import__('json').loads(shared.read_text(encoding="utf-8"))
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
                    ld = __import__('json').loads(legacy.read_text(encoding="utf-8"))
                    if isinstance(ld, dict):
                        if "sequencing" in ld and isinstance(ld["sequencing"], dict):
                            m = {}
                            if isinstance(ld.get("shared"), dict):
                                m.update(ld["shared"])  # type: ignore[index]
                            m.update(ld["sequencing"])  # type: ignore[index]
                            cfg = m
                        else:
                            cfg = ld
        except Exception:
            cfg = {}
        return cfg

    hero = story[0].image if story else None
    pages = []
    theme_slug = Path(images_folder).parent.name
    cover_cfg = _load_cover_cfg(theme_slug)
    rope = cover_cfg.get("rope") if isinstance(cover_cfg, dict) else None
    # Resolve hero/book cover assets for header and left panel (match Matching generator behavior)
    hero_path_str = None
    book_cover_path_str = None
    try:
        theme_dir = repo_root / "assets" / "themes" / theme_slug
        hero_candidates = [
            theme_dir / "hero_header.png",
            theme_dir / "heroes" / "hero_header.png",
            theme_dir / "characters" / "hero_header.png",
            theme_dir / "hero.png",
            theme_dir / "heroes" / "hero.png",
            theme_dir / "characters" / "hero.png",
            theme_dir / "header_icon.png",
        ]
        for hp in hero_candidates:
            if hp.exists():
                hero_path_str = str(hp)
                break
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
    except Exception:
        hero_path_str = None
        book_cover_path_str = None

    # Load hero image object for header if path available
    hero_img = None
    try:
        if hero_path_str:
            _im = Image.open(hero_path_str)
            hero_img = _im.convert("RGBA") if _im.mode != "RGBA" else _im
    except Exception:
        hero_img = None

    n = min(5, len(story))
    sequence_labels = ["FIRST", "NEXT", "THEN", "LAST"][:n]

    # Landscape layout: combine multiple levels per page to avoid empty space
    # Page 1: Level 1 (top half) + Level 2 (bottom half)
    # Page 2: Cut-Out Cards (top half) + Level 3 (bottom half)
    total_pages = 2
    scale = DPI / 72
    header_bottom = int(1.65 * DPI)
    footer_top = PAGE_H - safe_footer_inset_px()
    mid_y = (header_bottom + footer_top) // 2
    half_gap = int(10 * scale)

    # ── Page 1: Level 1 (top) + Level 2 (bottom) ──
    page1 = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d1 = ImageDraw.Draw(page1)
    fonts1 = _load_fonts()

    # Level 1 label + prompt
    lvl1_label = "Level 1 — Supported"
    lvl1_prompt = "Look at the pictures. Tell the story in order."
    d1.text((int(0.55 * DPI), header_bottom + int(4 * scale)), lvl1_label, fill=hex_to_rgb(NAVY), font=fonts1["prompt"])
    d1.text((int(0.55 * DPI), header_bottom + int(22 * scale)), lvl1_prompt, fill=hex_to_rgb(NAVY), font=fonts1["small"])
    _draw_story_strip(
        page1,
        items=story,
        labels=sequence_labels,
        show_images=True,
        show_numbers=False,
        writing_line=False,
        y_start=header_bottom + int(40 * scale),
        y_end=mid_y - half_gap,
    )

    # Level 2 label + prompt
    lvl2_label = "Level 2 — Developing"
    lvl2_prompt = "Cut and paste the pictures in order."
    d1.text((int(0.55 * DPI), mid_y + half_gap + int(4 * scale)), lvl2_label, fill=hex_to_rgb(NAVY), font=fonts1["prompt"])
    d1.text((int(0.55 * DPI), mid_y + half_gap + int(22 * scale)), lvl2_prompt, fill=hex_to_rgb(NAVY), font=fonts1["small"])
    _draw_story_strip(
        page1,
        items=story,
        labels=sequence_labels,
        show_images=False,
        show_numbers=False,
        writing_line=False,
        y_start=mid_y + half_gap + int(40 * scale),
        y_end=footer_top,
    )

    # Divider line between the two halves
    d1.line([(int(0.40 * DPI), mid_y), (PAGE_W - int(0.40 * DPI), mid_y)], fill=(200, 200, 200), width=max(1, int(1 * scale)))

    apply_small_wins_frame(
        page1,
        product_title="Sequencing",
        subtitle=f"{theme_name} — Levels 1 & 2",
        pack_code=pack_code,
        page_num=1,
        total_pages=total_pages,
        level=None,
        footer_title=f"{theme_name} | Sequencing",
        header_left_icon=(hero_img if hero_img is not None else (story[0].image if story else None)),
        footer_y_offset_px=int(0.10 * DPI),
        draw_footer=True,
        draw_subtitle=True,
    )
    pages.append(page1)

    # ── Page 2: Cut-Out Cards (top) + Level 3 (bottom) ──
    scrambled = story[:]
    random.Random((pack_code + "|" + theme_name).lower()).shuffle(scrambled)
    page2 = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d2 = ImageDraw.Draw(page2)
    fonts2 = _load_fonts()

    # Cut-outs label
    cut_label = "Cut-Out Cards"
    cut_prompt = "Cut out the cards. Paste them in the correct order."
    d2.text((int(0.55 * DPI), header_bottom + int(4 * scale)), cut_label, fill=hex_to_rgb(NAVY), font=fonts2["prompt"])
    d2.text((int(0.55 * DPI), header_bottom + int(22 * scale)), cut_prompt, fill=hex_to_rgb(NAVY), font=fonts2["small"])
    _cutouts_page(
        page2,
        items=scrambled,
        count=min(10, len(scrambled)),
        y_start=header_bottom + int(40 * scale),
        y_end=mid_y - half_gap,
    )

    # Level 3 label + prompt
    lvl3_label = "Level 3 — Independent"
    lvl3_prompt = "Draw or write what happens in order."
    d2.text((int(0.55 * DPI), mid_y + half_gap + int(4 * scale)), lvl3_label, fill=hex_to_rgb(NAVY), font=fonts2["prompt"])
    d2.text((int(0.55 * DPI), mid_y + half_gap + int(22 * scale)), lvl3_prompt, fill=hex_to_rgb(NAVY), font=fonts2["small"])
    _draw_story_strip(
        page2,
        items=story,
        labels=["" for _ in range(n)],
        show_images=False,
        show_numbers=False,
        writing_line=True,
        y_start=mid_y + half_gap + int(40 * scale),
        y_end=footer_top,
    )

    # Divider line
    d2.line([(int(0.40 * DPI), mid_y), (PAGE_W - int(0.40 * DPI), mid_y)], fill=(200, 200, 200), width=max(1, int(1 * scale)))

    apply_small_wins_frame(
        page2,
        product_title="Sequencing",
        subtitle=f"{theme_name} — Cut-Outs & Level 3",
        pack_code=pack_code,
        page_num=2,
        total_pages=total_pages,
        level=None,
        footer_title=f"{theme_name} | Sequencing",
        header_left_icon=(hero_img if hero_img is not None else (scrambled[0].image if scrambled else (story[0].image if story else None))),
        footer_y_offset_px=int(0.10 * DPI),
        draw_footer=True,
        draw_subtitle=True,
    )
    pages.append(page2)

    out_color = out_dir / f"{pack_code}_Sequencing_COLOR.pdf"
    out_bw = out_dir / f"{pack_code}_Sequencing_BW.pdf"
    out_preview = out_dir / f"{pack_code}_Sequencing_PREVIEW.pdf"

    _page_to_pdf(pages, out_color, watermark_preview=False)
    bw_pages = [p.convert("L").convert("RGB") for p in pages]
    _page_to_pdf(bw_pages, out_bw, watermark_preview=False)
    _page_to_pdf(pages, out_preview, watermark_preview=True)

    # Standard QA_OUT exports (fixed filenames)
    try:
        qa_dir = out_dir / "QA_OUT"
        qa_dir.mkdir(parents=True, exist_ok=True)
        # First activity page
        pages[0].save(qa_dir / "page_first.png", format="PNG", dpi=(DPI, DPI))
        # Mid page
        mid_idx = max(0, len(pages) // 2)
        pages[min(mid_idx, len(pages) - 1)].save(qa_dir / "page_mid.png", format="PNG", dpi=(DPI, DPI))
        # Last page
        pages[-1].save(qa_dir / "page_last.png", format="PNG", dpi=(DPI, DPI))
        # Calling-cards placeholder: use page 2 (cut-outs + level 3)
        call_idx = min(1, len(pages) - 1)
        pages[call_idx].save(qa_dir / "calling_cards.png", format="PNG", dpi=(DPI, DPI))
    except Exception:
        pass

    print(f"OK Generated: {out_color}")
    print(f"OK Generated: {out_bw}")
    print(f"OK Generated: {out_preview}")
    return True
