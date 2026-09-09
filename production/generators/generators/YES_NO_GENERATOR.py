from __future__ import annotations

import io
import math
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from utils.sws_design import _brand_font_pt, generate_internal_cover_page, shrink_font_to_fit_with_pt, normalize_text, apply_small_wins_frame
from utils.qa import assess_files
from utils.UNIVERSAL_STANDARDS import SWS_TEAL, SWS_NAVY, SWS_TEAL_LT
import json
from datetime import datetime
import hashlib
from typing import Dict, List, Tuple
import argparse
import sys

PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

TITLE_BLUE = SWS_TEAL
NAVY_BLUE = SWS_NAVY
LIGHT_BLUE = SWS_TEAL_LT
# Brief: YES (emerald) and NO (rose)
GREEN = "#059669"
RED = "#E11D48"


def hex_to_rgb(hex_color: str):
    hex_color = str(hex_color).lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def load_fonts():
    scale = DPI / 72
    try:
        return {
            "title": ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(24 * scale)),
            "question": ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(16 * scale)),
            "yes_no": ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(28 * scale)),
            "footer": ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(11 * scale)),
            "copyright": ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(7 * scale)),
            "cutout_label": ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(20 * scale)),
        }
    except Exception:
        d = ImageFont.load_default()
        return {"title": d, "question": d, "yes_no": d, "footer": d, "copyright": d, "cutout_label": d}


def _read_icons(images_folder: str) -> list[tuple[str, Image.Image]]:
    p = Path(images_folder)
    files = sorted([
        f for f in p.glob("*.png")
        if f.is_file() and not f.name.startswith(".")
        and not any(k in str(f).lower() for k in ["aac_core", "aac_core_text", "global", "grounding_note", "citations"])
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


def _theme_dir_for_images(images_folder: str) -> Path:
    images = Path(images_folder)
    if images.name == "icons" and images.parent.name == ".sf_build":
        return images.parent.parent
    return images.parent


def _load_book_vocab(images_folder: str) -> dict | None:
    try:
        p = _theme_dir_for_images(images_folder) / "book_vocab.json"
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                try:
                    return json.loads(p.read_text(encoding="utf-8-sig"))
                except Exception:
                    pass
    except Exception:
        return None
    return None


def _sanitize_key(s: str) -> str:
    t = re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _indef_article(label: str) -> str:
    s = str(label or "").strip().lower()
    w = re.sub(r"[^a-z0-9]+", " ", s).strip().split(" ")[0] if s else ""
    if not w:
        return "a"
    # Common silent-h cases that take 'an'
    for pref in ("honest", "honor", "hour", "heir", "herb"):
        if w.startswith(pref):
            return "an"
    # Leading 'yoo' or 'w' sounds that take 'a'
    for pref in ("unicorn", "university", "unit", "user", "euro", "one", "once"):
        if w.startswith(pref):
            return "a"
    return "an" if (w[:1] in "aeiou") else "a"


def _build_questions_from_vocab(*, vocab: dict, icons: list[tuple[str, Image.Image]]) -> List[Dict]:
    try:
        qs = []
        icon_keys: Dict[str, str] = {}
        for name, _ in icons:
            clean = _normalize_label(name, theme_name=str(vocab.get("title") or "").strip() or "Theme")
            k = _sanitize_key(clean)
            icon_keys[k] = clean
        # Prefer longest canonical key first (e.g., 'bat wing' over 'bat')
        sorted_keys = sorted(icon_keys.keys(), key=lambda x: len(x), reverse=True)
        theme_key = _sanitize_key(str(vocab.get("title") or "").strip())
        syn: Dict[str, List[str]] = {}
        try:
            for k, arr in (vocab.get("icon_search_terms") or {}).items():
                mk = _sanitize_key(k)
                syn[mk] = list({_sanitize_key(x) for x in (arr or [])} | {mk})
        except Exception:
            pass
        def _match_key(text: str) -> str | None:
            t = _sanitize_key(text)
            cands: List[str] = []
            for k in sorted_keys:
                if re.search(rf"\b{re.escape(k)}\b", t):
                    cands.append(k)
                    continue
                for alt in syn.get(k, []):
                    if alt and re.search(rf"\b{re.escape(alt)}\b", t):
                        cands.append(k)
                        break
            if not cands:
                return None
            if theme_key and theme_key in cands and len(cands) > 1:
                cands = [c for c in cands if c != theme_key]
            cands.sort(key=lambda x: len(x), reverse=True)
            return cands[0] if cands else None
        for item in (vocab.get("yes_no_questions") or []):
            try:
                q = str(item.get("question") or "").strip()
                if not q:
                    continue
                explicit_key = _sanitize_key(item.get("image_key") or "")
                mk = explicit_key if explicit_key in icon_keys else _match_key(q)
                if mk and mk in icon_keys:
                    qs.append({"image_key": mk, "recall": q, "answer": str(item.get("answer") or "").strip().lower()})
            except Exception:
                continue
        return qs
    except Exception:
        return []


def _report_yes_no(images_folder: str, *, theme_name: str) -> dict:
    icons = _read_icons(images_folder)
    vocab = _load_book_vocab(images_folder) or {}
    auto = _build_questions_from_vocab(vocab=vocab or {}, icons=icons)
    try:
        total_book_q = len(vocab.get("yes_no_questions") or [])
    except Exception:
        total_book_q = 0
    mapped_keys = {str(q.get("image_key", "")).strip().lower() for q in auto}
    icon_rows: List[Dict] = []
    fallbacks: List[Dict] = []
    for name, _img in icons:
        clean = _normalize_label(name, theme_name=theme_name)
        key_display = re.sub(r"\s+", " ", clean).strip().lower()
        k = _sanitize_key(clean)
        used = k in mapped_keys
        icon_rows.append({"label": clean, "key": k, "display_key": key_display, "has_book_q": used})
        if not used:
            art = _indef_article(clean)
            fallbacks.append({"label": clean, "question": f"Is this {art} {clean.lower()}?", "image_key": k})
    # Find unmatched questions in vocab
    unmatched: List[str] = []
    try:
        all_qs = list(vocab.get("yes_no_questions") or [])
        # Build matcher with longest-first preference and synonyms
        icon_key_labels: Dict[str, str] = {}
        for n, _ in icons:
            cl = _normalize_label(n, theme_name=theme_name)
            icon_key_labels[_sanitize_key(cl)] = cl
        syn: Dict[str, List[str]] = {}
        try:
            for k, arr in (vocab.get("icon_search_terms") or {}).items():
                mk = _sanitize_key(k)
                syn[mk] = list({_sanitize_key(x) for x in (arr or [])} | {mk})
        except Exception:
            pass
        sorted_keys = sorted(icon_key_labels.keys(), key=lambda x: len(x), reverse=True)
        for item in all_qs:
            q = str(item.get("question") or "").strip()
            explicit_key = _sanitize_key(item.get("image_key") or "")
            t = _sanitize_key(q)
            hit = explicit_key in icon_key_labels
            for kk in sorted_keys:
                if hit:
                    break
                if re.search(rf"\b{re.escape(kk)}\b", t):
                    hit = True
                    break
                for alt in syn.get(kk, []):
                    if alt and re.search(rf"\b{re.escape(alt)}\b", t):
                        hit = True
                        break
            if not hit:
                unmatched.append(q)
    except Exception:
        pass
    estimate_cards = len(icons)
    pages_questions = int(math.ceil(estimate_cards / 4.0))
    total_estimate = pages_questions + 2
    coverage_pct = (100.0 * len(mapped_keys) / estimate_cards) if estimate_cards else 0.0
    return {
        "theme": theme_name,
        "images_folder": str(images_folder),
        "icons_detected": icon_rows,
        "book_questions_found": len(auto),
        "book_questions_total": total_book_q,
        "coverage_pct": coverage_pct,
        "book_questions_mapped": auto,
        "book_questions_unmatched": unmatched,
        "fallback_questions": fallbacks,
        "estimate": {"cards": estimate_cards, "question_pages": pages_questions, "total_pages": total_estimate},
    }



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
            f"Yes/No Questions must not read from AAC core/global: {p}. Use assets/themes/<slug>/activity_images/."
        )
    files = [f for f in p.glob("*.png") if f.is_file() and not f.name.startswith(".")]
    if len(files) < 4:
        raise ValueError(f"Too few images in {p} — found {len(files)}, need at least 4.")


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def _draw_small_border(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, height: int, scale: float):
    border_radius = int(10 * scale)
    draw.rounded_rectangle(
        [x, y, x + width, y + height],
        radius=border_radius,
        outline=hex_to_rgb(NAVY_BLUE),
        width=int(2 * scale),
    )
    accent_height = int(5 * scale)
    draw.rounded_rectangle(
        [x, y, x + width, y + accent_height],
        radius=border_radius,
        fill=hex_to_rgb(TITLE_BLUE),
        outline=None,
    )


def _wrap_two_lines(text: str) -> tuple[str, str | None]:
    words = [w for w in str(text).strip().split() if w]
    if len(words) <= 4:
        return (" ".join(words), None)
    mid = max(1, len(words) // 2)
    return (" ".join(words[:mid]), " ".join(words[mid:]))


def _normalize_label(name: str, *, theme_name: str) -> str:
    s = str(name).strip()
    s = re.sub(r"\([^)]*\)", "", s).strip()
    s = re.sub(r"\s+\d+$", "", s).strip()
    s = re.sub(r"\s{2,}", " ", s).strip()

    if theme_name.strip().lower() == "stellaluna":
        if s.lower().startswith("a "):
            s = s[2:].strip()

    if "tree" in s.lower() and "palm" in s.lower():
        s = "Tree"

    return s


def _prepare_card_icon(icon: Image.Image) -> Image.Image:
    image = icon.convert("RGBA")
    edge = max(2, int(image.width * 0.02))
    image = image.crop((edge, edge, image.width - edge, image.height - edge))
    pixels = []
    source_pixels = image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()
    for red, green, blue, alpha in source_pixels:
        neutral_background = max(red, green, blue) - min(red, green, blue) < 12 and (red + green + blue) / 3 > 150
        pixels.append((red, green, blue, 0 if neutral_background else alpha))
    image.putdata(pixels)
    bounds = image.getchannel("A").getbbox()
    return image.crop(bounds) if bounds else image


def _draw_yes_no_card(
    *,
    draw: ImageDraw.ImageDraw,
    page: Image.Image,
    question_text: str,
    icon: Image.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    scale: float,
    fonts: dict,
    fit_warnings: list[str] | None = None,
    because_prompt: bool = False,
):
    _draw_small_border(draw, x, y, width, height, scale)

    qy = y + int(15 * scale)
    l1, l2 = _wrap_two_lines(question_text)
    max_w = max(1, width - int(20 * scale))
    # First line shrink-to-fit
    qf1, pt1 = shrink_font_to_fit_with_pt(normalize_text(l1), base_pt=16, max_width_px=max_w, bold=True, brand="poppins", min_pt=10)
    qw, qh = _text_size(draw, l1, qf1)
    draw.text((x + (width - qw) // 2, qy), l1, fill=hex_to_rgb(NAVY_BLUE), font=qf1)
    if l2:
        # Second line shrink-to-fit
        qf2, pt2 = shrink_font_to_fit_with_pt(normalize_text(l2), base_pt=16, max_width_px=max_w, bold=True, brand="poppins", min_pt=10)
        qw2, _ = _text_size(draw, l2, qf2)
        draw.text((x + (width - qw2) // 2, qy + int(20 * scale)), l2, fill=hex_to_rgb(NAVY_BLUE), font=qf2)
        qy += int(20 * scale)
        if fit_warnings is not None and (pt1 <= 12 or pt2 <= 12):
            fit_warnings.append(f"Yes/No question shrunk to {min(pt1, pt2)}pt: '{l1} {l2}'")
    else:
        if fit_warnings is not None and pt1 <= 12:
            fit_warnings.append(f"Yes/No question shrunk to {pt1}pt: '{l1}'")

    answer_h = int(70 * scale)
    bottom_pad = int(12 * scale)
    answers_y = y + height - bottom_pad - answer_h

    img_y = qy + int(24 * scale)
    img_bottom = answers_y - int(12 * scale)
    img_size = max(int(70 * scale), min(int(135 * scale), img_bottom - img_y))
    ic = _prepare_card_icon(icon)
    if ic.width > 0 and ic.height > 0:
        ratio = min(img_size / ic.width, img_size / ic.height)
        ic = ic.resize((max(1, int(ic.width * ratio)), max(1, int(ic.height * ratio))), Image.Resampling.LANCZOS)
    ix = x + (width - ic.width) // 2
    iy = img_y + max(0, (img_size - ic.height) // 2)
    page.paste(ic, (ix, iy), ic)

    pad_x = int(14 * scale)
    spacing = int(12 * scale)
    answer_w = max(int(width * 0.40), int((width - 2 * pad_x - spacing) // 2))

    yes_x = x + pad_x
    draw.rounded_rectangle(
        [yes_x, answers_y, yes_x + answer_w, answers_y + answer_h],
        radius=int(8 * scale),
        fill=hex_to_rgb(GREEN),
        outline=hex_to_rgb(NAVY_BLUE),
        width=int(2 * scale),
    )
    yes_text = "YES"
    ybw, ybh = _text_size(draw, yes_text, fonts["yes_no"])
    draw.text(
        (yes_x + (answer_w - ybw) // 2, answers_y + (answer_h - ybh) // 2 - int(3 * scale)),
        yes_text,
        fill="white",
        font=fonts["yes_no"],
    )

    no_x = yes_x + answer_w + spacing
    draw.rounded_rectangle(
        [no_x, answers_y, no_x + answer_w, answers_y + answer_h],
        radius=int(8 * scale),
        fill=hex_to_rgb(RED),
        outline=hex_to_rgb(NAVY_BLUE),
        width=int(2 * scale),
    )
    no_text = "NO"
    nbw, nbh = _text_size(draw, no_text, fonts["yes_no"])
    draw.text(
        (no_x + (answer_w - nbw) // 2, answers_y + (answer_h - nbh) // 2 - int(3 * scale)),
        no_text,
        fill="white",
        font=fonts["yes_no"],
    )

    # Optional explanation prompt for comprehension/opinion
    if because_prompt:
        prompt = "because..."
        pf, _ = shrink_font_to_fit_with_pt(
            prompt,
            base_pt=12,
            max_width_px=width - 2 * pad_x,
            bold=False,
            brand="poppins",
            min_pt=9,
        )
        pw, ph = _text_size(draw, prompt, pf)
        draw.text(
            (x + (width - pw) // 2, answers_y + answer_h + int(6 * scale)),
            prompt,
            fill=hex_to_rgb(NAVY_BLUE),
            font=pf,
        )


def _page_questions(*, items: list[tuple[str, Image.Image]], page_num: int, total_pages: int, pack_code: str, theme_name: str, fit_warnings: list[str] | None = None, questions_map: dict[str, dict] | None = None) -> Image.Image:
    img_w = int(PAGE_WIDTH * DPI / 72)
    img_h = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(page)
    scale = DPI / 72
    fonts = load_fonts()

    title_text = normalize_text(f"{theme_name} - Yes/No Questions")
    usable_w = img_w - int(2 * 30 * scale)
    tf, tpt = shrink_font_to_fit_with_pt(title_text, base_pt=24, max_width_px=usable_w, bold=True, brand="poppins", min_pt=14)
    tw, th = _text_size(draw, title_text, tf)
    draw.text(((img_w - tw) // 2, int(25 * scale)), title_text, fill=hex_to_rgb(TITLE_BLUE), font=tf)
    if fit_warnings is not None and tpt <= 20:
        fit_warnings.append(f"Yes/No title shrunk to {tpt}pt on page {page_num}")

    border_margin = int(15 * scale)
    grid_start_y = int(65 * scale)
    grid_height = img_h - grid_start_y - int(60 * scale)

    card_w = (img_w - 2 * border_margin - int(50 * scale)) // 2
    card_h = (grid_height - int(20 * scale)) // 2
    gap_x = int(25 * scale)
    gap_y = int(20 * scale)

    x0 = border_margin
    y0 = grid_start_y

    for i, (name, img) in enumerate(items[:4]):
        row = i // 2
        col = i % 2
        cx = x0 + col * (card_w + gap_x)
        cy = y0 + row * (card_h + gap_y)
        clean = _normalize_label(name, theme_name=theme_name)
        key = re.sub(r"\s+", " ", clean).strip().lower()
        q = f"Is this {_indef_article(clean)} {clean.lower()}?"
        because = False
        if isinstance(questions_map, dict):
            qd = questions_map.get(key)
            if isinstance(qd, dict):
                if qd.get("recall"):
                    q = qd["recall"]
                elif qd.get("comprehension"):
                    q = qd["comprehension"]
                    because = True
                elif qd.get("opinion"):
                    q = qd["opinion"]
                    because = True
        _draw_yes_no_card(draw=draw, page=page, question_text=q, icon=img, x=cx, y=cy, width=card_w, height=card_h, scale=scale, fonts=fonts, fit_warnings=fit_warnings, because_prompt=because)

    apply_small_wins_frame(
        page,
        product_title="Yes/No Questions",
        subtitle="",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        draw_accent_strip=False,
        draw_header=False,
        draw_subtitle=False,
        draw_footer=True,
        footer_title=f"{theme_name} | Yes/No Questions",
    )

    return page


def _page_cutouts(*, page_num: int, total_pages: int, pack_code: str, theme_name: str) -> Image.Image:
    img_w = int(PAGE_WIDTH * DPI / 72)
    img_h = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(page)
    scale = DPI / 72
    fonts = load_fonts()

    title = "YES / NO Tokens"
    tw, _ = _text_size(draw, title, fonts["title"])
    draw.text(((img_w - tw) // 2, int(25 * scale)), title, fill=hex_to_rgb(TITLE_BLUE), font=fonts["title"])

    token_w = int(2.4 * DPI)
    token_h = int(1.1 * DPI)
    gap = int(0.25 * DPI)

    cols = 2
    rows = 6
    total_w = cols * token_w + (cols - 1) * gap
    x0 = (img_w - total_w) // 2
    y0 = int(120 * scale)

    labels = [("YES", GREEN), ("NO", RED)]
    for r in range(rows):
        for c in range(cols):
            txt, color = labels[c]
            x = x0 + c * (token_w + gap)
            y = y0 + r * (token_h + gap)
            draw.rounded_rectangle([x, y, x + token_w, y + token_h], radius=int(10 * scale), fill=hex_to_rgb(color), outline=hex_to_rgb(NAVY_BLUE), width=int(2 * scale))
            bw, bh = _text_size(draw, txt, fonts["cutout_label"])
            draw.text((x + (token_w - bw) // 2, y + (token_h - bh) // 2 - int(2 * scale)), txt, fill="white", font=fonts["cutout_label"])

    apply_small_wins_frame(
        page,
        product_title="Yes/No Questions",
        subtitle="Cut-Out Tokens",
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=None,
        draw_accent_strip=False,
        draw_header=False,
        draw_subtitle=False,
        draw_footer=True,
        footer_title=f"{theme_name} | Yes/No Questions",
    )

    return page


def _page_answer_key(questions: list[dict], page_num: int, total_pages: int, pack_code: str, theme_name: str) -> Image.Image:
    img_w = int(PAGE_WIDTH * DPI / 72)
    img_h = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(page)
    apply_small_wins_frame(page, product_title="Yes/No Answer Key", subtitle=theme_name, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=None, draw_footer=True, draw_subtitle=True)
    top = int(1.85 * DPI)
    row_h = int(0.92 * DPI)
    left = int(0.62 * DPI)
    right = img_w - int(0.62 * DPI)
    for index, item in enumerate(questions[:8], start=1):
        y = top + (index - 1) * row_h
        box = (left, y, right, y + row_h - int(0.10 * DPI))
        draw.rounded_rectangle(box, radius=int(0.10 * DPI), fill="white", outline=hex_to_rgb(LIGHT_BLUE), width=3)
        number_box = (left + 25, y + 25, left + 115, y + 115)
        draw.ellipse(number_box, fill=hex_to_rgb(NAVY_BLUE))
        answer = str(item.get("answer") or "").strip().upper()
        number_font = _brand_font_pt(10, bold=True, brand="poppins")
        nb = draw.textbbox((0, 0), str(index), font=number_font)
        draw.text((number_box[0] + (90 - (nb[2] - nb[0])) // 2 - nb[0], number_box[1] + (90 - (nb[3] - nb[1])) // 2 - nb[1]), str(index), font=number_font, fill="white")
        question = str(item.get("question") or "").strip()
        question_font, _ = shrink_font_to_fit_with_pt(question, base_pt=12, max_width_px=right - left - 520, bold=True, brand="poppins", min_pt=9)
        draw.text((left + 150, y + 55), question, font=question_font, fill=hex_to_rgb(NAVY_BLUE))
        answer_box = (right - 340, y + 35, right - 35, y + row_h - int(0.16 * DPI))
        draw.rounded_rectangle(answer_box, radius=int(0.10 * DPI), fill=hex_to_rgb(GREEN if answer == "YES" else RED), outline=hex_to_rgb(NAVY_BLUE), width=3)
        answer_font = _brand_font_pt(12, bold=True, brand="poppins")
        ab = draw.textbbox((0, 0), answer, font=answer_font)
        draw.text((answer_box[0] + (answer_box[2] - answer_box[0] - (ab[2] - ab[0])) // 2 - ab[0], answer_box[1] + (answer_box[3] - answer_box[1] - (ab[3] - ab[1])) // 2 - ab[1]), answer, font=answer_font, fill="white")
    return page


def generate_yes_no_pack(images_folder: str, pack_code: str = "YN01", theme_name: str = "Theme", questions: list[dict] | None = None, output_dir: str | None = None) -> bool:
    try:
        _validate_images_folder(images_folder)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    icons = _read_icons(images_folder)
    if len(icons) < 4:
        print("❌ ERROR: Need at least 4 icons for Yes/No Questions")
        return False

    # Guardrailed output path: Studioforge/OUTPUT/{pack_code}
    out_dir = Path(output_dir) if output_dir else (_theme_dir_for_images(images_folder) / "OUTPUT")
    if "_TLOT_ARCHIVED_DUPLICATE" in str(out_dir):
        print(f"❌ ERROR: Output path points into archived duplicate: {out_dir}")
        return False
    out_dir.mkdir(parents=True, exist_ok=True)
    images_path = Path(images_folder)
    # Build questions map from explicit input or book_vocab.json
    questions_map: dict[str, dict] | None = None
    question_entries: list[dict] = []
    if questions:
        question_entries = list(questions)
        qm: dict[str, dict] = {}
        for q in questions:
            try:
                key = str(q.get("image_key", "")).strip().lower()
                if key:
                    qm[key] = q
                    qm.setdefault(key.replace("_", " "), q)
            except Exception:
                continue
        questions_map = qm
    else:
        vocab = _load_book_vocab(images_folder)
        if vocab:
            question_entries = list(vocab.get("yes_no_questions") or [])
            auto = _build_questions_from_vocab(vocab=vocab, icons=icons)
            if auto:
                qm: dict[str, dict] = {}
                for q in auto:
                    try:
                        key = str(q.get("image_key", "")).strip().lower()
                        if key:
                            qm[key] = q
                            qm.setdefault(key.replace("_", " "), q)
                    except Exception:
                        continue
                questions_map = qm
            else:
                print("WARNING: No mappable yes/no questions found in book_vocab.json — using generic labels.")
        else:
            print("WARNING: No book_vocab.json found — using generic labels.")

    # Filter icons to only those that have matching reviewed questions
    if questions_map:
        filtered_icons = []
        for name, img in icons:
            key = name.lower().replace(" ", "_")
            if key in questions_map or name.lower() in questions_map:
                filtered_icons.append((name, img))
        if filtered_icons:
            icons = filtered_icons
            # Also filter question_entries to match
            icon_keys = {name.lower().replace(" ", "_") for name, _ in icons}
            question_entries = [q for q in question_entries if str(q.get("image_key", "")).strip().lower() in icon_keys or str(q.get("image_key", "")).strip().lower().replace("_", " ") in {name.lower() for name, _ in icons}]

    if not question_entries or not icons:
        print("ERROR: Yes/No requires at least one reviewed question and answer per icon")
        return False

    # Validate that all remaining question entries have valid answers
    if any(str(item.get("answer") or "").strip().lower() not in {"yes", "no"} for item in question_entries):
        print("ERROR: Yes/No questions must have answer 'yes' or 'no'")
        return False

    cards_per_page = 4
    num_pages = int(math.ceil(len(icons) / float(cards_per_page)))
    # +1 for cutouts, +1 for cover
    total_pages = num_pages + 3

    pages: list[Image.Image] = []
    text_fit_warnings: list[str] = []
    # No cover page — teacher cover is added later during packaging

    page_start = 1
    for p in range(num_pages):
        chunk = icons[p * cards_per_page : (p + 1) * cards_per_page]
        while len(chunk) < 4:
            chunk.append(chunk[-1])
        pages.append(_page_questions(items=chunk, page_num=page_start + p, total_pages=total_pages, pack_code=pack_code, theme_name=theme_name, fit_warnings=text_fit_warnings, questions_map=questions_map))

    pages.append(_page_cutouts(page_num=total_pages - 1, total_pages=total_pages, pack_code=pack_code, theme_name=theme_name))
    pages.append(_page_answer_key(question_entries, total_pages, total_pages, pack_code, theme_name))

    out_color = out_dir / f"{pack_code}_YesNoQuestions_COLOR.pdf"
    out_bw = out_dir / f"{pack_code}_YesNoQuestions_BW.pdf"
    out_preview = out_dir / f"{pack_code}_YesNoQuestions_PREVIEW.pdf"

    c = canvas.Canvas(str(out_color), pagesize=letter)
    for p in pages:
        buf = io.BytesIO()
        p.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c.showPage()
    c.save()

    bw_pages = [p.convert("L").convert("RGB") for p in pages]
    c_bw = canvas.Canvas(str(out_bw), pagesize=letter)
    for p in bw_pages:
        buf = io.BytesIO()
        p.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c_bw.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        c_bw.showPage()
    c_bw.save()

    c_prev = canvas.Canvas(str(out_preview), pagesize=letter)
    for p in pages:
        buf = io.BytesIO()
        p.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)
        c_prev.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        # Watermark
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

    # Thumbnails
    try:
        thumbs_dir = out_dir / "thumbnails"
        thumbs_dir.mkdir(parents=True, exist_ok=True)
        for i, pg in enumerate(pages[:2], start=1):
            th = pg.copy()
            th.thumbnail((500, 647), Image.Resampling.LANCZOS)
            th.save(thumbs_dir / f"{pack_code}_YesNo_thumb{i}.png", "PNG")
    except Exception:
        pass

    # BuildResult manifest
    try:
        thumbs = [str(p) for p in sorted((out_dir / "thumbnails").glob(f"{pack_code}_YesNo_thumb*.png"))]
        try:
            warnings = assess_files(
                product_name="Yes/No Questions",
                color_pdf=str(out_color),
                bw_pdf=str(out_bw),
                preview_pdf=str(out_preview),
                expected_pages=None,
            )
        except Exception:
            warnings = []
        try:
            warnings.extend(text_fit_warnings)
        except Exception:
            pass
        source = _theme_dir_for_images(images_folder) / "book_vocab.json"
        manifest = {
            "schema_version": 1,
            "status": "pilot_review",
            "product_name": "Yes/No Questions",
            "slug": _theme_dir_for_images(images_folder).name,
            "pack_code": pack_code,
            "page_count": len(pages),
            "reading_rope": ["Vocabulary", "Verbal Reasoning"],
            "teacher_review_required": True,
            "source": str(source),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "files": {
                "color_pdf": str(out_color),
                "bw_pdf": str(out_bw),
                "preview_pdf": str(out_preview),
                "thumbnails": thumbs,
            },
            "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": warnings},
        }
        (out_dir / f"{pack_code}_YesNoQuestions_BuildResult.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    print(f"OK Generated: {out_color}")
    print(f"OK Generated: {out_bw}")
    print(f"OK Generated: {out_preview}")
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--slug", default=None)
    ap.add_argument("--images", default=None)
    ap.add_argument("--pack", default="YN01")
    ap.add_argument("--theme", default=None)
    args = ap.parse_args()

    slug = (args.slug or "").strip() or None
    theme = (args.theme or (slug.replace("_", " ").title() if slug else "Theme"))
    if args.images:
        images_folder = args.images
    elif slug:
        images_folder = str((Path("assets") / "themes" / slug / "activity_images").resolve())
    else:
        images_folder = str((Path.cwd() / "images").resolve())

    if args.report:
        try:
            rep = _report_yes_no(images_folder, theme_name=theme)
            sys.stdout.write(json.dumps(rep, ensure_ascii=False, indent=2))
            sys.stdout.flush()
            raise SystemExit(0)
        except SystemExit:
            raise
        except Exception as e:
            sys.stderr.write(str(e) + "\n")
            raise SystemExit(2)
    else:
        ok = generate_yes_no_pack(images_folder, pack_code=args.pack, theme_name=theme)
        raise SystemExit(0 if ok else 1)
