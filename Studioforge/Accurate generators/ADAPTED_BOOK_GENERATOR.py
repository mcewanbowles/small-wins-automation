#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
try:
    _repo_root = Path(__file__).resolve().parents[2]
    _extra_paths = [
        _repo_root,
        _repo_root / "utils",
        _repo_root / "Generators" / "ARCHIVE generators",
        _repo_root / "Generators",
        _repo_root / "production" / "generators" / "generators",
    ]
    for _p in _extra_paths:
        if _p.exists():
            _p_str = str(_p)
            if _p_str not in sys.path:
                sys.path.insert(0, _p_str)
except Exception:
    pass
from utils.sws_design import generate_internal_cover_page, generate_teacher_cover_page, shrink_font_to_fit_with_pt, normalize_text, apply_small_wins_frame
from utils.logs import write_log, prune_logs
from utils.qa import assess_files
from utils.preview import make_preview_pdf_from_images, save_thumbnails_from_images
from utils.UNIVERSAL_STANDARDS import COPYRIGHT_YEAR

DPI = 300
PAGE_W_PT, PAGE_H_PT = letter
PAGE_W = int(PAGE_W_PT * DPI / 72)
PAGE_H = int(PAGE_H_PT * DPI / 72)
SHEET_W_PT, SHEET_H_PT = landscape(letter)
SHEET_W = int(SHEET_W_PT * DPI / 72)
SHEET_H = int(SHEET_H_PT * DPI / 72)

TEAL_ACCENT = "#31A8A0"
NAVY_BLUE = "#0D2545"   # SWS_NAVY
TITLE_BLUE = "#31A8A0"  # SWS_TEAL
STEEL_BLUE = "#5B7AA0"
LIGHT_GRAY = "#E8E8E8"
CREAM_PAGE_BG = "#FFFDF7"
VELCRO_BOX_BG = "#EEF4FB"
VELCRO_BOX_BD = "#0D2545"  # SWS_NAVY
REVIEW_GREEN = "#E8F5E9"

FONT_DIR = Path("assets/fonts/")



def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = str(hex_color).lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
def _font(path: Path, pt: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(path), int(pt * (DPI / 72)))
    except Exception:
        return ImageFont.load_default()


def load_fonts() -> dict[str, ImageFont.ImageFont]:
    poppins_bold = FONT_DIR / "Poppins-Bold.ttf"
    poppins_semi = FONT_DIR / "Poppins-SemiBold.ttf"
    poppins_reg = FONT_DIR / "Poppins-Regular.ttf"
    comic = Path("C:/Windows/Fonts/comic.ttf")
    dejavu_bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    dejavu_reg = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

    def best(bold=False, pt=16):
        stack = [poppins_bold if bold else poppins_reg]
        stack += [comic]
        stack += [dejavu_bold if bold else dejavu_reg]
        for p in stack:
            if p.exists():
                try:
                    return ImageFont.truetype(str(p), int(pt * (DPI / 72)))
                except Exception:
                    continue
        return ImageFont.load_default()

    return {
        "book_title": best(bold=True, pt=22),
        "product_label": best(bold=False, pt=13),
        "page_header": best(bold=True, pt=11),
        "sentence": best(bold=True, pt=22),
        "word_label": best(bold=True, pt=16),
        "instruction": best(bold=False, pt=12),
        "footer": best(bold=False, pt=9),
        "cutout_title": best(bold=True, pt=18),
        "cutout_label": best(bold=True, pt=13),
        "storage_title": best(bold=True, pt=20),
        "storage_pack": best(bold=False, pt=11),
    }


def generate_story_via_api(title: str, vocab_words: list[str], aac_extras: list[str] | None = None) -> dict | None:
    """Generate adapted book story JSON via Anthropics API.
    Returns a dict with keys: pages (list of dicts) and review_sentence, or None if unavailable.
    Safe fallback: returns None if anthropic is not installed or API key missing.
    """
    try:
        import os
        # Gate AI usage behind SWS_USE_AI; when disabled, skip cleanly.
        use_ai = str(os.getenv("SWS_USE_AI", "")).strip().lower() in ("1", "true", "yes", "on")
        if not use_ai:
            try:
                print("AI disabled via SWS_USE_AI — skipping AI story generation")
            except Exception:
                pass
            return None
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print(" ANTHROPIC_API_KEY not set -- skipping AI story generation")
            return None
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        system = (
            "You are a special education literacy specialist writing adapted books for students with autism, "
            "AAC users, and complex communication needs. Rules: max 8 words per sentence, simple present tense, "
            "contains the target word, no idioms, suitable ages 3-12. Return ONLY valid JSON, no markdown."
        )
        prompt = (
            f"Create adapted book for: \"{title}\"\n"
            f"Vocabulary: {' | '.join((vocab_words or [])[:12])}\n"
            "Select 8 words, order as narrative: intro -> events -> conclusion.\n\n"
            "Return exactly this JSON:\n{\n  \"pages\": [\n    {\"page_num\": 3, \"image_word\": \"word\", \"sentence\": \"Simple sentence.\", \"aac_prompt\": \"Question?\"}\n  ],\n  \"review_sentence\": \"One sentence summary (max 10 words).\"\n}"
        )
        resp = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=800,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            txt = resp.content[0].text if getattr(resp, "content", None) else "{}"
        except Exception:
            txt = "{}"
        import json as _json
        return _json.loads(txt)
    except Exception as e:
        try:
            print(f" AI story generation unavailable: {e}")
        except Exception:
            pass
        return None


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def _read_cache(slug: str) -> dict[str, Any] | None:
    p = Path(f"assets/themes/{slug}/config/adapted_book.json")
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _images_dir_candidates(slug: str) -> list[Path]:
    root = Path("assets") / "themes" / slug
    return [
        root / "activity_images",
        root / "icons",
        root / "images",
    ]


def _load_image_for_word(slug: str, word: str) -> Image.Image | None:
    cand_names = [f"{word}.png", f"{word}.PNG", f"{word}.jpg", f"{word}.jpeg", f"{word}.webp"]
    for d in _images_dir_candidates(slug):
        try:
            if d.exists():
                for nm in cand_names:
                    p = d / nm
                    if p.exists():
                        try:
                            img = Image.open(p).convert("RGBA")
                            return img
                        except Exception:
                            continue
        except Exception:
            continue
    return None


def _header_stripe(page: Image.Image, *, text: str) -> None:
    d = ImageDraw.Draw(page)
    h = int(0.8 * (DPI / 0.72))  # ~60px at 300dpi relative
    d.rectangle([0, 0, PAGE_W, h], fill=hex_to_rgb(TEAL_ACCENT))
    f = load_fonts()["product_label"]
    tw, th = _text_size(d, text, f)
    d.text(((PAGE_W - tw) // 2, (h - th) // 2), text, fill=(255, 255, 255), font=f)


def _footer_rule(page: Image.Image, *, slug: str, pack_code: str) -> None:
    d = ImageDraw.Draw(page)
    y = PAGE_H - int(0.83 * (DPI / 0.72))
    d.line([(0, y), (PAGE_W, y)], fill=hex_to_rgb(LIGHT_GRAY), width=1)
    f = load_fonts()["footer"]
    label = f"Small Wins Studio · © {COPYRIGHT_YEAR} · PCS® symbols used with active PCS Maker Personal License · {slug}"
    tw, th = _text_size(d, label, f)
    d.text((int(0.25 * DPI), y + int(0.20 * DPI)), label, fill=hex_to_rgb(STEEL_BLUE), font=f)


def _cover_page(slug: str, title: str) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(page)
    fonts = load_fonts()

    _header_stripe(page, text="Small Wins Studio")

    img = None
    cover_img = _load_image_for_word(slug, title)
    if cover_img is None:
        # Try first vocab image based on cache content if any
        cache = _read_cache(slug) or {}
        pages = cache.get("pages", [])
        if pages:
            img = _load_image_for_word(slug, str(pages[0].get("image_word", "")))
    else:
        img = cover_img

    # Image zone 800x800 centered
    box_size = int(800 * (DPI / 72) / 4)  # roughly 800px at 300dpi; approximate scaling
    box_size = int(800 * (DPI / 96))  # better approximation (~2500/3)
    box_size = min(box_size, int(2.4 * DPI))  # clamp so it fits
    box_size = int(2.2 * DPI)
    bx = (PAGE_W - box_size) // 2
    by = int(0.30 * PAGE_H)
    d.rounded_rectangle([bx, by, bx + box_size, by + box_size], radius=int(18 * (DPI / 72)), outline=hex_to_rgb(NAVY_BLUE), width=int(4 * (DPI / 72)), fill=(255, 255, 255))
    if img is not None:
        img = img.copy()
        img.thumbnail((int(box_size * 0.85), int(box_size * 0.85)), Image.Resampling.LANCZOS)
        ix = bx + (box_size - img.width) // 2
        iy = by + (box_size - img.height) // 2
        page.paste(img.convert("RGBA"), (ix, iy), img.convert("RGBA"))

    # Title band
    band_w, band_h = int(1450 * (DPI / 72)), int(200 * (DPI / 72) / 4)
    band_w = min(PAGE_W - int(0.2 * DPI), int(PAGE_W * 0.88))
    band_h = int(0.9 * DPI)
    band_x = (PAGE_W - band_w) // 2
    band_y = int(0.70 * PAGE_H)
    d.rounded_rectangle([band_x, band_y, band_x + band_w, band_y + band_h], radius=int(20 * (DPI / 72)), fill=hex_to_rgb(TEAL_ACCENT))
    t1 = title
    t2 = "Adapted Book for Read-Alouds"
    t1f = fonts["book_title"]
    t2f = fonts["product_label"]
    tw1, th1 = _text_size(d, t1, t1f)
    tw2, th2 = _text_size(d, t2, t2f)
    d.text((band_x + (band_w - tw1) // 2, band_y + int(0.20 * band_h) - 2), t1, fill=(255, 255, 255), font=t1f)
    d.text((band_x + (band_w - tw2) // 2, band_y + int(0.58 * band_h)), t2, fill=(230, 245, 247), font=t2f)

    return page


def _howto_page() -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(page)
    fonts = load_fonts()
    _header_stripe(page, text="HOW TO USE THIS BOOK")
    steps = [
        ("1.", "Before reading -- Talk about the cover. 'What do you see?'"),
        ("2.", "During reading -- Place matching piece in the box."),
        ("3.", "After reading -- Use Review page to retell the story."),
    ]
    y = int(1.2 * DPI)
    for circ, text in steps:
        d.ellipse([int(0.6 * DPI), y, int(0.6 * DPI) + int(0.55 * DPI), y + int(0.55 * DPI)], fill=hex_to_rgb("#31A8A0"))
        d.text((int(0.6 * DPI) + int(0.20 * DPI), y + int(0.11 * DPI)), circ, fill=(255, 255, 255), font=fonts["page_header"])
        d.text((int(1.35 * DPI), y + int(0.10 * DPI)), text, fill=hex_to_rgb(NAVY_BLUE), font=fonts["instruction"])
        y += int(0.85 * DPI)
    inst_box = [int(0.5 * DPI), y + int(0.2 * DPI), PAGE_W - int(0.5 * DPI), y + int(1.2 * DPI)]
    d.rounded_rectangle(inst_box, radius=10, outline=hex_to_rgb(NAVY_BLUE), width=2, fill=hex_to_rgb(VELCRO_BOX_BG))
    d.text((inst_box[0] + int(0.25 * DPI), inst_box[1] + int(0.20 * DPI)), "CUT OUT page 13 - LAMINATE - STORE in a zip bag.", fill=hex_to_rgb(STEEL_BLUE), font=fonts["instruction"])
    return page


def _story_page(
    slug: str,
    *,
    page_num: int,
    total_pages: int,
    title: str,
    image_word: str,
    sentence: str,
    fit_warnings: list[str] | None = None,
) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(page)
    fonts = load_fonts()
    # Running header
    head_h = int(0.32 * DPI)
    d.text((int(0.30 * DPI), int(0.10 * DPI)), title, fill=hex_to_rgb(TITLE_BLUE), font=fonts["page_header"])
    right = f"Adapted Book - pg {page_num}/{total_pages}"
    tw, th = _text_size(d, right, fonts["page_header"])
    d.text((PAGE_W - tw - int(0.30 * DPI), int(0.10 * DPI)), right, fill=hex_to_rgb(STEEL_BLUE), font=fonts["page_header"])
    d.line([(0, head_h), (PAGE_W, head_h)], fill=hex_to_rgb(LIGHT_GRAY), width=1)
    # Image box
    ibox = [int(0.33 * DPI), int(0.40 * DPI), PAGE_W - int(0.33 * DPI), int(4.0 * DPI)]
    d.rounded_rectangle(ibox, radius=20, outline=hex_to_rgb(TITLE_BLUE), width=3, fill=(255, 255, 255))
    img = _load_image_for_word(slug, image_word)
    if img is not None:
        im = img.copy()
        im.thumbnail((ibox[2] - ibox[0] - int(0.60 * DPI), ibox[3] - ibox[1] - int(0.60 * DPI)), Image.Resampling.LANCZOS)
        ix = ibox[0] + (ibox[2] - ibox[0] - im.width) // 2
        iy = ibox[1] + (ibox[3] - ibox[1] - im.height) // 2
        page.paste(im.convert("RGBA"), (ix, iy), im.convert("RGBA"))
    else:
        ph = "image missing"
        tw2, th2 = _text_size(d, ph, fonts["instruction"])
        d.text((ibox[0] + (ibox[2] - ibox[0] - tw2) // 2, ibox[1] + (ibox[3] - ibox[1] - th2) // 2), ph, fill=hex_to_rgb(STEEL_BLUE), font=fonts["instruction"])
    # Sentence box
    sbox = [int(0.33 * DPI), int(4.15 * DPI), PAGE_W - int(0.33 * DPI), int(5.07 * DPI)]
    d.rounded_rectangle(sbox, radius=12, outline=hex_to_rgb(TITLE_BLUE), width=2, fill=hex_to_rgb(CREAM_PAGE_BG))
    # Center sentence with shrink-to-fit
    sent = normalize_text(sentence or "")
    usable_w = (sbox[2] - sbox[0] - int(0.40 * DPI))
    fnt, chosen_pt = shrink_font_to_fit_with_pt(
        sent,
        base_pt=22,
        max_width_px=usable_w,
        bold=True,
        brand="poppins",
        min_pt=12,
    )
    sw, sh = _text_size(d, sent, fnt)
    d.text((sbox[0] + (sbox[2] - sbox[0] - sw) // 2, sbox[1] + (sbox[3] - sbox[1] - sh) // 2), sent, fill=hex_to_rgb(NAVY_BLUE), font=fnt)
    if fit_warnings is not None and chosen_pt <= 16:
        fit_warnings.append(f"Story sentence shrunk to {chosen_pt}pt on page {page_num}: '{sent[:60]}...'")
    # Velcro zone
    d.text((PAGE_W // 2 - int(1.8 * DPI), int(5.2 * DPI)), "PLACE THE MATCHING PIECE HERE", fill=hex_to_rgb(STEEL_BLUE), font=fonts["instruction"])
    left_box = [int(0.52 * DPI), int(5.5 * DPI), int(2.4 * DPI), int(7.4 * DPI)]
    right = [int(4.0 * DPI), int(5.5 * DPI), int(5.88 * DPI), int(7.4 * DPI)]
    d.rounded_rectangle(left_box, radius=12, outline=hex_to_rgb(TITLE_BLUE), width=3, fill=(255, 255, 255))
    # word label under image
    wl = image_word.title()
    lw, lh = _text_size(d, wl, fonts["word_label"])
    d.text((left_box[0] + (left_box[2] - left_box[0] - lw) // 2, left_box[3] - lh - int(0.10 * DPI)), wl, fill=hex_to_rgb(NAVY_BLUE), font=fonts["word_label"])
    # dashed right box
    d.rounded_rectangle(right, radius=12, outline=hex_to_rgb(TITLE_BLUE), width=2, fill=hex_to_rgb(VELCRO_BOX_BG))
    d.text((right[0] + int(0.22 * DPI), right[1] + int(0.75 * DPI)), "place piece here", fill=hex_to_rgb(STEEL_BLUE), font=fonts["instruction"])
    return page


def _review_page(
    slug: str,
    *,
    title: str,
    review_sentence: str,
    all_words: list[str],
    fit_warnings: list[str] | None = None,
) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(page)
    fonts = load_fonts()
    _header_stripe(page, text="THE END")
    box = [int(0.33 * DPI), int(0.55 * DPI), PAGE_W - int(0.33 * DPI), int(1.40 * DPI)]
    d.rounded_rectangle(box, radius=15, outline=hex_to_rgb("#4CAF50"), width=2, fill=hex_to_rgb(REVIEW_GREEN))
    rev = normalize_text(review_sentence or "")
    usable_rw = (box[2] - box[0] - int(0.40 * DPI))
    rfnt, rpt = shrink_font_to_fit_with_pt(
        rev,
        base_pt=22,
        max_width_px=usable_rw,
        bold=True,
        brand="poppins",
        min_pt=12,
    )
    sw, sh = _text_size(d, rev, rfnt)
    d.text((box[0] + (box[2] - box[0] - sw) // 2, box[1] + (box[3] - box[1] - sh) // 2), rev, fill=hex_to_rgb(NAVY_BLUE), font=rfnt)
    if fit_warnings is not None and rpt <= 16:
        fit_warnings.append(f"Review sentence shrunk to {rpt}pt: '{rev[:60]}...'")
    d.text((int(0.40 * DPI), int(1.75 * DPI)), "Words from this story:", fill=hex_to_rgb(TITLE_BLUE), font=fonts["page_header"]) 
    # grid 4x2
    cols, rows = 4, 2
    cell_w, cell_h = int(1.6 * DPI), int(1.6 * DPI)
    x0 = int(0.6 * DPI)
    y0 = int(2.05 * DPI)
    gap_x, gap_y = int(0.30 * DPI), int(0.30 * DPI)
    words = (all_words or [])[:8]
    for i, w in enumerate(words):
        r = i // cols
        c = i % cols
        x = x0 + c * (cell_w + gap_x)
        y = y0 + r * (cell_h + gap_y)
        d.rounded_rectangle([x, y, x + cell_w, y + cell_h], radius=8, outline=hex_to_rgb(TITLE_BLUE), width=2, fill=(255, 255, 255))
        img = _load_image_for_word(slug, w)
        if img is not None:
            ic = img.copy()
            ic.thumbnail((int(cell_w * 0.70), int(cell_h * 0.70)), Image.Resampling.LANCZOS)
            ix = x + (cell_w - ic.width) // 2
            iy = y + int(0.09 * DPI)
            page.paste(ic.convert("RGBA"), (ix, iy), ic.convert("RGBA"))
        wl = w.title()
        tw, th = _text_size(d, wl, fonts["word_label"])
        d.text((x + (cell_w - tw) // 2, y + cell_h - th - int(0.08 * DPI)), wl, fill=hex_to_rgb(NAVY_BLUE), font=fonts["word_label"]) 
    return page


def _cutout_page(slug: str, words: list[str]) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(page)
    fonts = load_fonts()
    _header_stripe(page, text="CUT-OUT PIECES")
    d.text((PAGE_W // 2 - int(1.8 * DPI), int(0.95 * DPI)), "Print - Laminate - Cut", fill=hex_to_rgb(STEEL_BLUE), font=fonts["instruction"])
    cols, rows = 4, 2
    outer_w, outer_h = int(1.1 * DPI), int(1.27 * DPI)
    inner_w, inner_h = outer_w - int(0.27 * DPI), outer_h - int(0.27 * DPI)
    x0 = int(0.5 * DPI)
    y0 = int(1.5 * DPI)
    gap = int(0.20 * DPI)
    for i in range(cols * rows):
        r = i // cols
        c = i % cols
        x = x0 + c * (outer_w + gap)
        y = y0 + r * (outer_h + gap)
        d.rounded_rectangle([x, y, x + outer_w, y + outer_h], radius=8, outline=hex_to_rgb("#CCCCCC"), width=2)
        ix = x + int(0.135 * DPI)
        iy = y + int(0.135 * DPI)
        d.rounded_rectangle([ix, iy, ix + inner_w, iy + inner_h], radius=12, outline=hex_to_rgb(TITLE_BLUE), width=3, fill=(255, 255, 255))
        w = words[i] if i < len(words) else ""
        img = _load_image_for_word(slug, w) if w else None
        if img is not None:
            ic = img.copy()
            ic.thumbnail((int(inner_w * 0.70), int(inner_h * 0.60)), Image.Resampling.LANCZOS)
            cx = ix + (inner_w - ic.width) // 2
            cy = iy + int(0.12 * DPI)
            page.paste(ic.convert("RGBA"), (cx, cy), ic.convert("RGBA"))
        if w:
            tw, th = _text_size(d, w.title(), fonts["cutout_label"])
            d.text((ix + (inner_w - tw) // 2, iy + inner_h - th - int(0.06 * DPI)), w.title(), fill=hex_to_rgb(NAVY_BLUE), font=fonts["cutout_label"]) 
    return page


def _storage_page(slug: str, title: str, pack_code: str, words: list[str]) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(page)
    fonts = load_fonts()
    _header_stripe(page, text="STORAGE")
    box = [int(0.33 * DPI), int(0.70 * DPI), PAGE_W - int(0.33 * DPI), int(2.60 * DPI)]
    d.rounded_rectangle(box, radius=15, outline=hex_to_rgb(TITLE_BLUE), width=3, fill=hex_to_rgb(VELCRO_BOX_BG))
    d.text((box[0] + int(0.22 * DPI), box[1] + int(0.18 * DPI)), "Adapted Book", fill=hex_to_rgb(NAVY_BLUE), font=fonts["storage_title"]) 
    # Thumbnails grid
    cols, rows = 4, 2
    cell = int(0.72 * DPI)
    gap = int(0.14 * DPI)
    gx = box[0] + int(0.22 * DPI)
    gy = box[1] + int(0.70 * DPI)
    for i, w in enumerate((words or [])[:8]):
        r = i // cols
        c = i % cols
        x = gx + c * (cell + gap)
        y = gy + r * (cell + gap)
        d.rectangle([x, y, x + cell, y + cell], outline=hex_to_rgb(TITLE_BLUE), width=2, fill=(255, 255, 255))
        img = _load_image_for_word(slug, w)
        if img is not None:
            ic = img.copy()
            ic.thumbnail((int(cell * 0.72), int(cell * 0.72)), Image.Resampling.LANCZOS)
            ix = x + (cell - ic.width) // 2
            iy = y + (cell - ic.height) // 2
            page.paste(ic.convert("RGBA"), (ix, iy), ic.convert("RGBA"))
    d.text((box[0] + int(0.22 * DPI), box[3] - int(0.38 * DPI)), f"{title} - {pack_code}", fill=hex_to_rgb(STEEL_BLUE), font=fonts["storage_pack"]) 
    d.text((int(0.40 * DPI), int(2.90 * DPI)), "Cut out and tape to storage bin.", fill=hex_to_rgb(STEEL_BLUE), font=fonts["instruction"])
    return page


def _to_landscape(page_img: Image.Image) -> Image.Image:
    sheet = Image.new("RGB", (SHEET_W, SHEET_H), "white")
    try:
        img = page_img.convert("RGB")
    except Exception:
        return sheet
    max_w = int(SHEET_W * 0.86)
    max_h = int(SHEET_H * 0.86)
    img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    x = (SHEET_W - img.width) // 2
    y = (SHEET_H - img.height) // 2
    sheet.paste(img, (x, y))
    return sheet


def _compose_story_2up(slug: str, title: str, left_meta: dict, right_meta: dict | None, *, left_idx: int, right_idx: int | None, total_story_pages: int, pack_code: str) -> Image.Image:
    sheet = Image.new("RGB", (SHEET_W, SHEET_H), "white")
    gutter = int(0.30 * DPI)
    margin = int(0.45 * DPI)
    pane_w = (SHEET_W - (2 * margin) - gutter) // 2
    pane_h = SHEET_H - (2 * margin)

    lp = _story_page(
        slug,
        page_num=left_idx,
        total_pages=total_story_pages,
        title=title,
        image_word=str(left_meta.get("image_word", "")),
        sentence=str(left_meta.get("sentence", "")) or " ",
        fit_warnings=None,
    )
    left_pane = Image.new("RGB", (pane_w, pane_h), "white")
    apply_small_wins_frame(
        left_pane,
        product_title=f"{title} | Adapted Book",
        subtitle=f"Page {left_idx}/{total_story_pages}",
        pack_code=pack_code,
        page_num=0,
        total_pages=0,
        level=None,
        footer_title=f"{title} | Adapted Book",
    )
    lp = lp.convert("RGB")
    inset_x = int(0.50 * DPI)
    top_y = int(1.85 * DPI)
    bot_margin = int(0.70 * DPI)
    avail_w = max(1, pane_w - 2 * inset_x)
    avail_h = max(1, pane_h - top_y - bot_margin)
    lp.thumbnail((avail_w, avail_h), Image.Resampling.LANCZOS)
    lpx = inset_x + (avail_w - lp.width) // 2
    lpy = top_y + (avail_h - lp.height) // 2
    left_pane.paste(lp, (lpx, lpy))
    lx = margin
    ly = margin
    sheet.paste(left_pane, (lx, ly))

    if right_meta is not None:
        rp = _story_page(
            slug,
            page_num=(right_idx or left_idx + 1),
            total_pages=total_story_pages,
            title=title,
            image_word=str(right_meta.get("image_word", "")),
            sentence=str(right_meta.get("sentence", "")) or " ",
            fit_warnings=None,
        )
        right_pane = Image.new("RGB", (pane_w, pane_h), "white")
        apply_small_wins_frame(
            right_pane,
            product_title=f"{title} | Adapted Book",
            subtitle=f"Page {(right_idx or left_idx + 1)}/{total_story_pages}",
            pack_code=pack_code,
            page_num=0,
            total_pages=0,
            level=None,
            footer_title=f"{title} | Adapted Book",
        )
        rp = rp.convert("RGB")
        inset_x = int(0.50 * DPI)
        top_y = int(1.85 * DPI)
        bot_margin = int(0.70 * DPI)
        avail_w = max(1, pane_w - 2 * inset_x)
        avail_h = max(1, pane_h - top_y - bot_margin)
        rp.thumbnail((avail_w, avail_h), Image.Resampling.LANCZOS)
        rpx = inset_x + (avail_w - rp.width) // 2
        rpy = top_y + (avail_h - rp.height) // 2
        right_pane.paste(rp, (rpx, rpy))
        rx = margin + pane_w + gutter
        ry = margin
        sheet.paste(right_pane, (rx, ry))

    d = ImageDraw.Draw(sheet)
    cy0 = margin
    cy1 = SHEET_H - margin
    cx = margin + pane_w + (gutter // 2)
    d.line([(cx, cy0), (cx, cy1)], fill=hex_to_rgb(LIGHT_GRAY), width=2)
    return sheet


def build_pdf(slug: str, title: str, pack_code: str) -> tuple[Path, Path]:
    out_dir = Path(f"assets/themes/{slug}/OUTPUT")
    out_dir.mkdir(parents=True, exist_ok=True)

    source_path = Path(f"assets/themes/{slug}/config/adapted_book.json")
    cache = _read_cache(slug)
    if not cache:
        raise ValueError(f"Missing reviewed adapted-book config: {source_path}")
    pages_meta = cache.get("pages", [])
    if not isinstance(pages_meta, list) or len(pages_meta) != 8:
        raise ValueError("Adapted-book config must contain exactly eight reviewed pages")
    for index, entry in enumerate(pages_meta, start=1):
        word = str(entry.get("image_word") or "").strip()
        sentence = str(entry.get("sentence") or "").strip()
        if not word or not sentence or _load_image_for_word(slug, word) is None:
            raise ValueError(f"Invalid adapted-book page {index}: reviewed sentence and local image are required")
    words = [str(p.get("image_word", "")).strip() for p in pages_meta]

    pages: list[Image.Image] = []
    text_fit_warnings: list[str] = []

    # Teacher cover (replaces old internal cover + custom cover + how-to page)
    hero = _load_image_for_word(slug, title)
    content_pages_after_cover = 9
    icov = generate_teacher_cover_page(
        theme_name=title,
        pack_code=pack_code,
        product_name="Adapted Reading Companion",
        page_count=content_pages_after_cover,
        level_count=None,
        hero_image=hero,
        top_tips=[
            "Print in landscape and laminate sheets for durability.",
            "Read each page; place the matching piece in the velcro box.",
            "Use the review page to retell the story with all 8 images.",
        ],
        whats_included=[
            "8-page adapted story with matching pieces",
            "Review page for story retell",
            "Cut-out pieces sheet and storage label",
            "Boardmaker PCS symbols throughout",
        ],
    )
    pages.append(_to_landscape(icov))

    # Ensure 8 story entries

    # Create 2-up story sheets (4 sheets total)
    story_total = 8
    for idx in range(0, story_total, 2):
        left = pages_meta[idx]
        right = pages_meta[idx + 1] if idx + 1 < len(pages_meta) else None
        sheet = _compose_story_2up(
            slug,
            title,
            left,
            right,
            left_idx=idx + 1,
            right_idx=(idx + 2 if right is not None else None),
            total_story_pages=story_total,
            pack_code=pack_code,
        )
        pages.append(sheet)

    # Review + cutouts + storage centered on landscape
    pages.append(
        _to_landscape(
            _review_page(
                slug,
                title=title,
                review_sentence=str(cache.get("review_sentence", "The end.")),
                all_words=words,
                fit_warnings=text_fit_warnings,
            )
        )
    )
    pages.append(_to_landscape(_cutout_page(slug, words)))
    pages.append(_to_landscape(_storage_page(slug, title, pack_code, words)))

    out_color = out_dir / f"{pack_code}_AdaptedBook_COLOR.pdf"
    out_bw = out_dir / f"{pack_code}_AdaptedBook_BW.pdf"

    # Write COLOR (landscape)
    c = canvas.Canvas(str(out_color), pagesize=landscape(letter))
    for p in pages:
        buf = io.BytesIO()
        img = p if p.size == (SHEET_W, SHEET_H) else _to_landscape(p)
        img.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=SHEET_W_PT, height=SHEET_H_PT)
        c.showPage()
    c.save()

    # Write BW (landscape)
    c2 = canvas.Canvas(str(out_bw), pagesize=landscape(letter))
    for p in pages:
        base = p if p.size == (SHEET_W, SHEET_H) else _to_landscape(p)
        pbw = base.convert("L").convert("RGB")
        buf = io.BytesIO()
        pbw.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c2.drawImage(ImageReader(buf), 0, 0, width=SHEET_W_PT, height=SHEET_H_PT)
        c2.showPage()
    c2.save()
    
    # Create PREVIEW PDF (sample pages with watermark) using utils.preview
    out_prev = None
    try:
        preview_indices = list(range(len(pages)))
        out_prev = make_preview_pdf_from_images(
            pages=pages,
            indices=preview_indices,
            out_pdf_path=out_dir / f"{pack_code}_AdaptedBook_PREVIEW.pdf",
            page_size=(SHEET_W_PT, SHEET_H_PT),
            watermark="PREVIEW",
        )
        try:
            save_thumbnails_from_images(
                pages=pages,
                indices=preview_indices,
                out_dir=out_dir / "thumbnails",
                name_prefix=f"{pack_code}_AdaptedBook",
            )
        except Exception:
            pass
    except Exception:
        pass

    # Write BuildResult manifest
    try:
        thumb_dir = out_dir / "thumbnails"
        thumbs = []
        if thumb_dir.exists():
            thumbs = [str(p) for p in sorted(thumb_dir.glob(f"{pack_code}_AdaptedBook_thumb*.png"))]
        warnings = []
        try:
            warnings = assess_files(
                product_name="Adapted Book",
                color_pdf=str(out_color),
                bw_pdf=str(out_bw),
                preview_pdf=(str(out_prev) if out_prev else None),
                expected_pages=len(pages),
            )
        except Exception:
            warnings = []
        # Add any text-fit observations
        try:
            warnings.extend(text_fit_warnings)
        except Exception:
            pass

        manifest = {
            "schema_version": 1,
            "status": "pilot_review",
            "product_name": "Adapted Reading Companion",
            "slug": slug,
            "pack_code": pack_code,
            "page_count": len(pages),
            "reading_rope": ["Vocabulary", "Language Structures", "Literacy Knowledge"],
            "teacher_review_required": bool(cache.get("teacher_review_required", True)),
            "source": str(source_path),
            "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "files": {
                "color_pdf": str(out_color),
                "bw_pdf": str(out_bw),
                "preview_pdf": (str(out_prev) if out_prev else None),
                "thumbnails": thumbs,
            },
            "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": warnings},
        }
        (out_dir / f"{pack_code}_AdaptedBook_BuildResult.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        try:
            lines = [
                f"Color: {out_color}",
                f"BW: {out_bw}",
                f"Preview: {out_prev if out_prev else 'None'}",
                f"Thumbnails: {len(thumbs)}",
            ]
            write_log("Adapted Book", out_dir, lines)
            prune_logs("Adapted Book", out_dir, keep=20)
        except Exception:
            pass
    except Exception:
        pass

    return out_color, out_bw


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print("Usage: ADAPTED_BOOK_GENERATOR.py <slug> <title> <pack_code>")
        return 2
    slug = argv[1]
    title = argv[2]
    pack_code = argv[3]
    try:
        c, b = build_pdf(slug, title, pack_code)
        print(f"OK Generated: {c}")
        print(f"OK Generated: {b}")
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

