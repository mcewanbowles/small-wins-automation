"""Small Wins Studio — Marketing Thumbnail Generator

Generates 4 Canva-style TPT marketing images per product:
  1. Hero Cover  — book title, product name, hero icon, branding
  2. What's Included — feature bullets with page counts
  3. Closer Look — 2-3 sample pages from the actual PDF
  4. How to Use / Who It's For — usage steps + audience tags

Output: 1000x1000px PNG (TPT-optimised square)
Location: assets/themes/<slug>/OUTPUT/marketing/<product>_<image_type>.png

Brand tokens from CANVA_DESIGN_BRIEF.md + UNIVERSAL_STANDARDS.py:
  SWS Teal #31A8A0, SWS Navy #0D2545, SWS Gold #E1B42D, SWS Cream #FDFCF8
  Level Violet #7C3AED, Ocean #0284C7, Emerald #059669, Rose #E11D48
  Fonts: Poppins Bold/Regular (fallback Arial)
  Logo: assets/branding/logos/small_wins_logo_with_text.png
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

# ── Brand tokens ──────────────────────────────────────────────────────────────
SWS_TEAL = "#31A8A0"
SWS_NAVY = "#0D2545"
SWS_GOLD = "#E1B42D"
SWS_CREAM = "#FDFCF8"
SWS_TEAL_LT = "#E8F8F8"
SWS_FOOTER_GREY = "#F5F5F2"
LEVEL_VIOLET = "#7C3AED"
LEVEL_OCEAN = "#0284C7"
LEVEL_EMERALD = "#059669"
LEVEL_ROSE = "#E11D48"
WHITE = "#FFFFFF"
MUTED = "#6B7280"
BORDER_LIGHT = "#DCE7E6"

# TPT thumbnail size
THUMB_SIZE = 1000

# Repo root
REPO_ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "production" else Path(__file__).resolve().parent
LOGO_PATH = REPO_ROOT / "assets" / "branding" / "logos" / "small_wins_logo_with_text.png"
ROPE_WORD_RECOGNITION = REPO_ROOT / "assets" / "branding" / "rope" / "realistic" / "realistic_scarborough_rope_word_recognition.png"
ROPE_LANGUAGE_COMPREHENSION = REPO_ROOT / "assets" / "branding" / "rope" / "realistic" / "realistic_scarborough_rope_language_comprehension.png"

# ── Product metadata ──────────────────────────────────────────────────────────
PRODUCT_FEATURES = {
    "Matching": {
        "subtitle": "4 Levels · Errorless to Hard",
        "features": ["4 difficulty levels", "Color + B&W versions", "Cut-out pieces included", "Storage labels"],
        "rope": "Vocabulary · Sight Recognition",
        "audience": "SPED · Autism · AAC · Speech Therapy",
    },
    "BookParticipation": {
        "subtitle": "Interactive Story Pieces",
        "features": ["Hero character pieces", "Vocabulary icons", "Question strips", "Turn-the-page cues"],
        "rope": "Vocabulary · Language Structures · Verbal Reasoning",
        "audience": "SPED · Autism · AAC · Early Childhood",
    },
    "AAC_SentenceStrips": {
        "subtitle": "Sentence Building Strips",
        "features": ["6 sentence patterns", "Core + theme pieces", "Cut-out pieces", "AAC-ready"],
        "rope": "Language Structures · Vocabulary",
        "audience": "AAC Users · SPED · Speech Therapy",
    },
    "Sorting": {
        "subtitle": "Reason & Sort Cards",
        "features": ["Guided + open sorts", "Header bank included", "20 sort headers", "Color + B&W"],
        "rope": "Vocabulary · Verbal Reasoning · Language Structures",
        "audience": "SPED · Autism · Speech Therapy",
    },
    "Bingo": {
        "subtitle": "Differentiated Bingo",
        "features": ["8 calling cards", "Multiple board sizes", "Color + B&W", "Vocabulary practice"],
        "rope": "Vocabulary · Sight Recognition",
        "audience": "SPED · Autism · Early Childhood · Speech Therapy",
    },
    "WordSearch": {
        "subtitle": "4 Difficulty Levels",
        "features": ["4 levels of difficulty", "Picture icons + text", "Answer key included", "B&W version"],
        "rope": "Sight Recognition · Vocabulary",
        "audience": "SPED · Early Readers · Speech Therapy",
    },
    "Syllable_Cards": {
        "subtitle": "Syllable Awareness Cards",
        "features": ["Syllable counting", "Visual segmentation dots", "Color + B&W", "Phonological awareness"],
        "rope": "Phonological Awareness",
        "audience": "SPED · Speech Therapy · Early Readers",
    },
    "Sequencing": {
        "subtitle": "Story Sequencing Strips",
        "features": ["4 story events", "Picture + text strips", "Color + B&W", "Narrative retell"],
        "rope": "Language Structures · Literacy Knowledge",
        "audience": "SPED · Autism · Speech Therapy",
    },
    "WordSnap": {
        "subtitle": "Vocabulary Snap Cards",
        "features": ["3 card variants", "Symbol + text decks", "Extra copy deck", "Color + B&W"],
        "rope": "Vocabulary · Sight Recognition",
        "audience": "SPED · Autism · AAC · Early Childhood",
    },
    "FindAndCover": {
        "subtitle": "3 Levels · Visual Scanning",
        "features": ["3 difficulty levels", "1-3 distractors", "Storage labels", "Color + B&W"],
        "rope": "Vocabulary · Visual Discrimination",
        "audience": "SPED · Autism · Work Task Boxes · Early Childhood",
    },
    "YesNoQuestions": {
        "subtitle": "Yes/No Question Cards",
        "features": ["8+ question cards", "Picture-based", "AAC accessible", "Color + B&W"],
        "rope": "Vocabulary · Verbal Reasoning",
        "audience": "SPED · AAC Users · Speech Therapy",
    },
    "Inferencing": {
        "subtitle": "Clue · Think · Infer Cards",
        "features": ["4 reasoning cards", "Clue image + question", "Answer hints", "Color + B&W"],
        "rope": "Verbal Reasoning · Background Knowledge",
        "audience": "SPED · Speech Therapy · Early Readers",
    },
    "Story_Elements_Mat": {
        "subtitle": "Story Elements Mat",
        "features": ["Story element mat", "Character/setting/plot", "Retell support", "Color + B&W"],
        "rope": "Literacy Knowledge · Language Structures",
        "audience": "SPED · Speech Therapy · Early Readers",
    },
    "PrintDetective": {
        "subtitle": "Letters, Words & First Sounds",
        "features": ["4 levels", "Letter/word sorting", "First sound matching", "Print concepts"],
        "rope": "Alphabetic Principle · Print Concepts",
        "audience": "SPED · Emergent Readers · Early Childhood",
    },
}

# How-to-use steps (same for all products)
HOW_TO_STEPS = [
    "Print and laminate all pages",
    "Cut out activity pieces",
    "Store in zip bag or file folder",
    "Re-use across multiple sessions!",
]

AUDIENCE_TAGS = "SPED Classrooms · AAC Users · Speech Therapy · Autism Support"

# Human-readable display names for product keys (used in thumbnails)
PRODUCT_DISPLAY_NAMES = {
    "Matching": "Matching",
    "BookParticipation": "Book Participation",
    "AAC_Sentence_Building": "AAC Sentence Building",
    "AAC_Board": "AAC Board",
    "Sorting": "Sorting Cards",
    "Bingo": "Bingo",
    "WordSearch": "Word Search",
    "Syllable_Cards": "Syllable Awareness",
    "Sequencing": "Sequencing",
    "WordSnap": "Vocabulary Snap",
    "FindAndCover": "Find & Cover",
    "YesNoQuestions": "Yes/No Questions",
    "Inferencing": "Inferencing Cards",
    "Story_Elements_Mat": "Story Elements Mat",
    "PrintDetective": "Print Detective",
    "AdaptedBook": "Adapted Book",
    "IEP_MonitoringForm": "IEP Monitoring Form",
}


def _product_display_name(product_key: str) -> str:
    """Return human-readable product name for thumbnail display."""
    if product_key in PRODUCT_DISPLAY_NAMES:
        return PRODUCT_DISPLAY_NAMES[product_key]
    # Fallback: replace underscores and camelCase boundaries
    name = product_key.replace("_", " ")
    # Split camelCase: FindAndCover -> Find And Cover
    import re as _re
    name = _re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    return name.title()


# ── Font helpers ──────────────────────────────────────────────────────────────
def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    search_dirs = [
        REPO_ROOT / "assets" / "branding" / "fonts",
        REPO_ROOT / "Studioforge" / "Accurate generators" / "Internal covers",
        REPO_ROOT / "fonts",
        Path("C:/Windows/Fonts"),
    ]
    names = ["Poppins-Bold.ttf", "Poppins-SemiBold.ttf", "Poppins-Medium.ttf"] if bold else ["Poppins-Regular.ttf", "Poppins-Medium.ttf"]
    for d in search_dirs:
        for nm in names:
            p = d / nm
            if p.exists():
                try:
                    return ImageFont.truetype(str(p), size)
                except Exception:
                    pass
    # Fallback to Arial
    for d in search_dirs:
        for nm in (["arialbd.ttf"] if bold else ["arial.ttf"]):
            p = d / nm
            if p.exists():
                try:
                    return ImageFont.truetype(str(p), size)
                except Exception:
                    pass
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def _draw_centered(draw: ImageDraw.ImageDraw, text: str, y: int, font: ImageFont.FreeTypeFont, fill, w: int) -> int:
    tw, th = _text_size(draw, text, font)
    x = int((w - tw) / 2)
    draw.text((x, y), text, font=font, fill=fill)
    return th


def _draw_text(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, font: ImageFont.FreeTypeFont, fill) -> int:
    draw.text((x, y), text, font=font, fill=fill)
    _, th = _text_size(draw, text, font)
    return th


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        tw, _ = _text_size(draw, test, font)
        if tw > max_w and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def _draw_pill(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, font: ImageFont.FreeTypeFont, bg_color, text_color=WHITE, pad_x=12, pad_y=6) -> int:
    tw, th = _text_size(draw, text, font)
    w = tw + 2 * pad_x
    h = th + 2 * pad_y
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=_hex_to_rgb(bg_color))
    draw.text((x + pad_x, y + pad_y), text, font=font, fill=_hex_to_rgb(text_color))
    return w


def _draw_checkmark(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, color):
    """Draw a filled circle with a checkmark."""
    draw.ellipse([x, y, x + size, y + size], fill=_hex_to_rgb(color))
    # Simple checkmark
    cx, cy = x + size // 2, y + size // 2
    r = size // 3
    draw.line([(cx - r, cy), (cx - r // 3, cy + r // 2), (cx + r, cy - r // 2)], fill=WHITE, width=max(2, size // 10))


def _draw_arrow(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, color):
    """Draw a right-pointing arrow."""
    draw.polygon([(x, y), (x + size, y + size // 2), (x, y + size)], fill=_hex_to_rgb(color))


def _load_logo() -> Optional[Image.Image]:
    if LOGO_PATH.exists():
        try:
            return Image.open(LOGO_PATH).convert("RGBA")
        except Exception:
            pass
    return None


def _pdf_first_page_image(pdf_path: Path, dpi: int = 150) -> Optional[Image.Image]:
    """Render first page of a PDF to a PIL Image."""
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB" if pix.n < 4 else "RGBA", (pix.width, pix.height), pix.samples)
        doc.close()
        return img
    except Exception:
        return None


def _pdf_page_image(pdf_path: Path, page_num: int, dpi: int = 150) -> Optional[Image.Image]:
    """Render a specific page of a PDF to a PIL Image."""
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        if page_num >= len(doc):
            page_num = 0
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB" if pix.n < 4 else "RGBA", (pix.width, pix.height), pix.samples)
        doc.close()
        return img
    except Exception:
        return None


def _fit_image(img: Image.Image, box_w: int, box_h: int) -> Image.Image:
    """Fit image into a box preserving aspect ratio."""
    img_copy = img.copy()
    img_copy.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)
    return img_copy


def _round_corners(img: Image.Image, radius: int) -> Image.Image:
    """Add rounded corners to an image."""
    from PIL import ImageDraw as ID
    mask = Image.new("L", img.size, 0)
    draw = ID.Draw(mask)
    draw.rounded_rectangle([0, 0, img.size[0], img.size[1]], radius=radius, fill=255)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img.putalpha(mask)
    return img


# ── Image 1: Hero Cover ───────────────────────────────────────────────────────
def generate_hero_cover(
    product_key: str,
    book_title: str,
    pack_code: str,
    hero_icon_path: Optional[Path],
    page_count: int,
    output_path: Path,
) -> bool:
    """Image 1: Hero cover with book title, product name, hero icon, branding."""
    features = PRODUCT_FEATURES.get(product_key, {})
    product_name = _product_display_name(product_key)
    subtitle = features.get("subtitle", "")

    canvas = Image.new("RGB", (THUMB_SIZE, THUMB_SIZE), _hex_to_rgb(SWS_CREAM))
    draw = ImageDraw.Draw(canvas)

    # Teal header band
    header_h = 140
    draw.rectangle([0, 0, THUMB_SIZE, header_h], fill=_hex_to_rgb(SWS_TEAL))

    # Title in header
    font_title = _load_font(36, bold=True)
    font_sub = _load_font(22, bold=False)
    _draw_centered(draw, book_title, 25, font_title, _hex_to_rgb(WHITE), THUMB_SIZE)
    _draw_centered(draw, product_name, 72, font_sub, _hex_to_rgb(WHITE), THUMB_SIZE)

    # Hero icon area
    icon_area_y = header_h + 30
    icon_area_h = 420
    icon_area_x = 100
    icon_area_w = THUMB_SIZE - 200

    # Light teal background box for icon
    draw.rounded_rectangle(
        [icon_area_x, icon_area_y, icon_area_x + icon_area_w, icon_area_y + icon_area_h],
        radius=20, fill=_hex_to_rgb(SWS_TEAL_LT), outline=_hex_to_rgb(SWS_TEAL), width=3
    )

    # Place hero icon if available
    if hero_icon_path and hero_icon_path.exists():
        try:
            hero = Image.open(hero_icon_path).convert("RGBA")
            hero_fit = _fit_image(hero, icon_area_w - 60, icon_area_h - 60)
            hx = icon_area_x + (icon_area_w - hero_fit.width) // 2
            hy = icon_area_y + (icon_area_h - hero_fit.height) // 2
            canvas.paste(hero_fit, (hx, hy), hero_fit)
        except Exception:
            pass

    # Subtitle below icon
    font_feat = _load_font(24, bold=True)
    _draw_centered(draw, subtitle, icon_area_y + icon_area_h + 20, font_feat, _hex_to_rgb(SWS_NAVY), THUMB_SIZE)

    # Page count badge
    font_badge = _load_font(18, bold=True)
    badge_text = f"{page_count} pages"
    bw = _draw_pill(draw, badge_text, 0, 0, font_badge, SWS_GOLD, SWS_NAVY)
    # Position bottom center
    badge_y = THUMB_SIZE - 130
    draw_pill_at = (THUMB_SIZE - bw) // 2
    _draw_pill(draw, badge_text, draw_pill_at, badge_y, font_badge, SWS_GOLD, SWS_NAVY)

    # Cross-sell text
    font_cross = _load_font(16, bold=False)
    cross_text = f"Part of the {book_title} Bundle · 15 Activities"
    _draw_centered(draw, cross_text, badge_y + 45, font_cross, _hex_to_rgb(MUTED), THUMB_SIZE)

    # Navy footer band
    footer_h = 60
    draw.rectangle([0, THUMB_SIZE - footer_h, THUMB_SIZE, THUMB_SIZE], fill=_hex_to_rgb(SWS_NAVY))

    # Logo in footer
    logo = _load_logo()
    if logo:
        logo_fit = _fit_image(logo, 180, footer_h - 20)
        canvas.paste(logo_fit, (20, THUMB_SIZE - footer_h + 10), logo_fit if logo_fit.mode == "RGBA" else None)

    # Website text
    font_footer = _load_font(14, bold=False)
    _draw_centered(draw, "smallwinsstudio.com", THUMB_SIZE - footer_h + 22, font_footer, _hex_to_rgb(WHITE), THUMB_SIZE)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(output_path), "PNG", optimize=True)
    return True


# ── Image 2: What's Included ──────────────────────────────────────────────────
def generate_whats_included(
    product_key: str,
    book_title: str,
    pack_code: str,
    page_count: int,
    output_path: Path,
    bundle_activity_count: int = 17,
) -> bool:
    """Image 2: What's included — feature bullets with checkmarks."""
    features = PRODUCT_FEATURES.get(product_key, {})
    product_name = _product_display_name(product_key)
    feature_list = features.get("features", ["Color version", "B&W version", "Ready to print"])
    rope = features.get("rope", "Vocabulary")

    canvas = Image.new("RGB", (THUMB_SIZE, THUMB_SIZE), _hex_to_rgb(SWS_CREAM))
    draw = ImageDraw.Draw(canvas)

    # Teal header
    header_h = 120
    draw.rectangle([0, 0, THUMB_SIZE, header_h], fill=_hex_to_rgb(SWS_TEAL))
    font_head = _load_font(32, bold=True)
    font_sub = _load_font(20, bold=False)
    _draw_centered(draw, "What's Included", 25, font_head, _hex_to_rgb(WHITE), THUMB_SIZE)
    _draw_centered(draw, f"{product_name} · {page_count} pages", 70, font_sub, _hex_to_rgb(WHITE), THUMB_SIZE)

    # Feature bullets
    font_bullet = _load_font(22, bold=True)
    font_body = _load_font(20, bold=False)
    y = header_h + 50
    check_size = 32
    check_x = 80
    text_x = check_x + check_size + 16

    for feature in feature_list:
        _draw_checkmark(draw, check_x, y, check_size, SWS_TEAL)
        _draw_text(draw, feature, text_x, y + 4, font_bullet, _hex_to_rgb(SWS_NAVY))
        y += 55

    # Divider
    y += 20
    draw.line([(80, y), (THUMB_SIZE - 80, y)], fill=_hex_to_rgb(BORDER_LIGHT), width=2)
    y += 25

    # Reading Rope section
    font_rope_title = _load_font(18, bold=True)
    font_rope_body = _load_font(16, bold=False)
    _draw_text(draw, "Scarborough Reading Rope", 80, y, font_rope_title, _hex_to_rgb(SWS_NAVY))
    y += 30
    rope_box_h = 80
    draw.rounded_rectangle([80, y, THUMB_SIZE - 80, y + rope_box_h], radius=12, fill=_hex_to_rgb(SWS_TEAL_LT), outline=_hex_to_rgb(SWS_TEAL), width=2)
    rope_lines = _wrap_text(draw, rope, font_rope_body, THUMB_SIZE - 200)
    for line in rope_lines:
        _draw_text(draw, line, 100, y + 12, font_rope_body, _hex_to_rgb(SWS_NAVY))
        y += 24

    y += 30

    # Cross-sell box
    font_cross = _load_font(18, bold=True)
    cross_text = f"Part of the {book_title} Bundle"
    cross_lines = _wrap_text(draw, cross_text, font_cross, THUMB_SIZE - 160)
    for line in cross_lines:
        _draw_text(draw, line, 80, y, font_cross, _hex_to_rgb(SWS_GOLD))
        y += 26
    font_cross_sub = _load_font(16, bold=False)
    _draw_text(draw, f"{bundle_activity_count} activities · Save with the bundle", 80, y, font_cross_sub, _hex_to_rgb(MUTED))

    # Navy footer
    footer_h = 60
    draw.rectangle([0, THUMB_SIZE - footer_h, THUMB_SIZE, THUMB_SIZE], fill=_hex_to_rgb(SWS_NAVY))
    logo = _load_logo()
    if logo:
        logo_fit = _fit_image(logo, 180, footer_h - 20)
        canvas.paste(logo_fit, (20, THUMB_SIZE - footer_h + 10), logo_fit if logo_fit.mode == "RGBA" else None)
    font_footer = _load_font(14, bold=False)
    _draw_centered(draw, "smallwinsstudio.com", THUMB_SIZE - footer_h + 22, font_footer, _hex_to_rgb(WHITE), THUMB_SIZE)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(output_path), "PNG", optimize=True)
    return True


# ── Image 3: Closer Look ──────────────────────────────────────────────────────
def generate_closer_look(
    product_key: str,
    book_title: str,
    pack_code: str,
    color_pdf_path: Path,
    output_path: Path,
) -> bool:
    """Image 3: Closer look — 2-3 sample pages from the actual PDF."""
    product_name = _product_display_name(product_key)

    canvas = Image.new("RGB", (THUMB_SIZE, THUMB_SIZE), _hex_to_rgb(SWS_CREAM))
    draw = ImageDraw.Draw(canvas)

    # Teal header
    header_h = 100
    draw.rectangle([0, 0, THUMB_SIZE, header_h], fill=_hex_to_rgb(SWS_TEAL))
    font_head = _load_font(28, bold=True)
    font_sub = _load_font(18, bold=False)
    _draw_centered(draw, "A Closer Look", 20, font_head, _hex_to_rgb(WHITE), THUMB_SIZE)
    _draw_centered(draw, product_name, 62, font_sub, _hex_to_rgb(WHITE), THUMB_SIZE)

    # Get 2 sample pages from the PDF
    page_indices = [0, 2] if color_pdf_path and color_pdf_path.exists() else []
    page_images = []
    for idx in page_indices:
        img = _pdf_page_image(color_pdf_path, idx, dpi=120)
        if img:
            page_images.append(img)

    if not page_images:
        # Fallback: show placeholder text
        font_placeholder = _load_font(20, bold=False)
        _draw_centered(draw, "Preview pages available after build", 400, font_placeholder, _hex_to_rgb(MUTED), THUMB_SIZE)
    else:
        # Display pages side by side or stacked
        if len(page_images) >= 2:
            # Side by side
            gap = 20
            page_w = (THUMB_SIZE - 120 - gap) // 2
            page_h = 600
            for i, img in enumerate(page_images[:2]):
                img_fit = _fit_image(img, page_w, page_h)
                img_rounded = _round_corners(img_fit, 12)
                px = 60 + i * (page_w + gap)
                py = header_h + 40
                # Shadow effect
                draw.rounded_rectangle([px + 4, py + 4, px + img_rounded.width + 4, py + img_rounded.height + 4], radius=12, fill=(200, 200, 200))
                canvas.paste(img_rounded, (px, py), img_rounded)
                # Border
                draw.rounded_rectangle([px, py, px + img_rounded.width, py + img_rounded.height], radius=12, outline=_hex_to_rgb(SWS_TEAL), width=2)

            # Labels
            font_label = _load_font(16, bold=True)
            for i, label in enumerate(["Page 1", "Page 3"][:len(page_images)]):
                px = 60 + i * (page_w + gap) + page_w // 2 - 30
                py = header_h + 40 + page_h + 15
                _draw_text(draw, label, px, py, font_label, _hex_to_rgb(SWS_NAVY))
        elif len(page_images) == 1:
            page_w = THUMB_SIZE - 120
            page_h = 600
            img_fit = _fit_image(page_images[0], page_w, page_h)
            img_rounded = _round_corners(img_fit, 12)
            px = 60
            py = header_h + 40
            draw.rounded_rectangle([px + 4, py + 4, px + img_rounded.width + 4, py + img_rounded.height + 4], radius=12, fill=(200, 200, 200))
            canvas.paste(img_rounded, (px, py), img_rounded)
            draw.rounded_rectangle([px, py, px + img_rounded.width, py + img_rounded.height], radius=12, outline=_hex_to_rgb(SWS_TEAL), width=2)

    # Navy footer
    footer_h = 60
    draw.rectangle([0, THUMB_SIZE - footer_h, THUMB_SIZE, THUMB_SIZE], fill=_hex_to_rgb(SWS_NAVY))
    logo = _load_logo()
    if logo:
        logo_fit = _fit_image(logo, 180, footer_h - 20)
        canvas.paste(logo_fit, (20, THUMB_SIZE - footer_h + 10), logo_fit if logo_fit.mode == "RGBA" else None)
    font_footer = _load_font(14, bold=False)
    _draw_centered(draw, "smallwinsstudio.com", THUMB_SIZE - footer_h + 22, font_footer, _hex_to_rgb(WHITE), THUMB_SIZE)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(output_path), "PNG", optimize=True)
    return True


# ── Image 4: How to Use / Who It's For ────────────────────────────────────────
def generate_how_to_use(
    product_key: str,
    book_title: str,
    pack_code: str,
    output_path: Path,
) -> bool:
    """Image 4: How to use + who it's for."""
    features = PRODUCT_FEATURES.get(product_key, {})
    product_name = _product_display_name(product_key)
    audience = features.get("audience", AUDIENCE_TAGS)

    canvas = Image.new("RGB", (THUMB_SIZE, THUMB_SIZE), _hex_to_rgb(SWS_CREAM))
    draw = ImageDraw.Draw(canvas)

    # Teal header
    header_h = 100
    draw.rectangle([0, 0, THUMB_SIZE, header_h], fill=_hex_to_rgb(SWS_TEAL))
    font_head = _load_font(28, bold=True)
    font_sub = _load_font(18, bold=False)
    _draw_centered(draw, "How to Use", 20, font_head, _hex_to_rgb(WHITE), THUMB_SIZE)
    _draw_centered(draw, product_name, 62, font_sub, _hex_to_rgb(WHITE), THUMB_SIZE)

    # How-to steps with numbered circles
    font_step = _load_font(20, bold=True)
    font_step_num = _load_font(18, bold=True)
    y = header_h + 50
    step_size = 36
    step_x = 80
    text_x = step_x + step_size + 16

    for i, step in enumerate(HOW_TO_STEPS, 1):
        # Numbered circle
        draw.ellipse([step_x, y, step_x + step_size, y + step_size], fill=_hex_to_rgb(SWS_GOLD))
        num_text = str(i)
        nw, nh = _text_size(draw, num_text, font_step_num)
        draw.text((step_x + (step_size - nw) // 2, y + (step_size - nh) // 2 - 2), num_text, font=font_step_num, fill=_hex_to_rgb(SWS_NAVY))
        # Step text
        _draw_text(draw, step, text_x, y + 6, font_step, _hex_to_rgb(SWS_NAVY))
        y += 55

    # Divider
    y += 20
    draw.line([(80, y), (THUMB_SIZE - 80, y)], fill=_hex_to_rgb(BORDER_LIGHT), width=2)
    y += 25

    # Perfect for section
    font_pf_title = _load_font(22, bold=True)
    _draw_text(draw, "Perfect for:", 80, y, font_pf_title, _hex_to_rgb(SWS_TEAL))
    y += 40

    # Audience tags as pills
    font_tag = _load_font(16, bold=True)
    tags = audience.split(" · ")
    tag_x = 80
    tag_y = y
    for tag in tags:
        tag_text = tag.strip()
        if not tag_text:
            continue
        tw, th = _text_size(draw, tag_text, font_tag)
        pill_w = tw + 24
        if tag_x + pill_w > THUMB_SIZE - 80:
            tag_x = 80
            tag_y += th + 20
        _draw_pill(draw, tag_text, tag_x, tag_y, font_tag, SWS_TEAL_LT, SWS_NAVY, pad_x=12, pad_y=8)
        tag_x += pill_w + 12

    # Navy footer
    footer_h = 60
    draw.rectangle([0, THUMB_SIZE - footer_h, THUMB_SIZE, THUMB_SIZE], fill=_hex_to_rgb(SWS_NAVY))
    logo = _load_logo()
    if logo:
        logo_fit = _fit_image(logo, 180, footer_h - 20)
        canvas.paste(logo_fit, (20, THUMB_SIZE - footer_h + 10), logo_fit if logo_fit.mode == "RGBA" else None)
    font_footer = _load_font(14, bold=False)
    _draw_centered(draw, "smallwinsstudio.com", THUMB_SIZE - footer_h + 22, font_footer, _hex_to_rgb(WHITE), THUMB_SIZE)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(output_path), "PNG", optimize=True)
    return True


# ── Main entry point ──────────────────────────────────────────────────────────
def generate_marketing_thumbnails(
    images_folder: str,
    pack_code: str = "LLB01",
    theme_name: str = "Theme",
) -> bool:
    """Generate all 4 marketing thumbnails for every product in the book's OUTPUT dir."""
    images_path = Path(images_folder).resolve()
    if images_path.name == "icons" and images_path.parent.name == ".sf_build":
        theme_dir = images_path.parent.parent
    else:
        theme_dir = images_path.parent
    output_dir = theme_dir / "OUTPUT"
    marketing_dir = output_dir / "marketing"

    # Load book vocab for title and hero
    vocab_path = theme_dir / "book_vocab.json"
    book_title = theme_name
    hero_icon_key = None
    if vocab_path.exists():
        try:
            vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
            book_title = vocab.get("title") or theme_name
            hero_icon_key = vocab.get("hero_icon") or None
        except Exception:
            pass

    # Find hero icon
    hero_icon_path = None
    if hero_icon_key:
        hero_path = images_path / hero_icon_key
        if hero_path.exists():
            hero_icon_path = hero_path
    if not hero_icon_path:
        # Try first activity image
        for p in sorted(images_path.glob("*.png")):
            hero_icon_path = p
            break

    # Find all color PDFs
    pdfs = sorted(output_dir.glob(f"{pack_code}*_COLOR.pdf"))
    if not pdfs:
        print(f"ERROR: No color PDFs found in {output_dir}")
        return False

    print(f"\n{'='*70}")
    print(f"  MARKETING THUMBNAILS: {book_title}")
    print(f"  {len(pdfs)} products found")
    print(f"{'='*70}")

    # Count products for the "N activities" cross-sell text
    bundle_activity_count = len(pdfs)

    generated = 0
    for pdf_path in pdfs:
        # Extract product key from filename
        # LLB01_Matching_COLOR.pdf -> Matching
        m = re.match(rf"{re.escape(pack_code)}_(.+?)_COLOR\.pdf", pdf_path.name)
        if not m:
            continue
        product_key = m.group(1)

        # Skip variant/secondary PDFs
        if product_key in ("WordSnap_ExtraCopy", "WordSnap_SymbolOnly", "WordSnap_SymbolText", "WordSnap_TextOnly", "WordWall_Banner", "WordWall", "Decoding"):
            continue

        # Get page count
        page_count = 0
        try:
            import fitz
            doc = fitz.open(str(pdf_path))
            page_count = len(doc)
            doc.close()
        except Exception:
            pass

        # Generate 4 images
        images = [
            ("hero", generate_hero_cover),
            ("whats_included", generate_whats_included),
            ("closer_look", generate_closer_look),
            ("how_to_use", generate_how_to_use),
        ]

        for img_type, gen_func in images:
            out_path = marketing_dir / f"{pack_code}_{product_key}_{img_type}.png"
            try:
                if img_type == "hero":
                    ok = gen_func(product_key, book_title, pack_code, hero_icon_path, page_count, out_path)
                elif img_type == "whats_included":
                    ok = gen_func(product_key, book_title, pack_code, page_count, out_path, bundle_activity_count=bundle_activity_count)
                elif img_type == "closer_look":
                    ok = gen_func(product_key, book_title, pack_code, pdf_path, out_path)
                else:
                    ok = gen_func(product_key, book_title, pack_code, out_path)
                if ok:
                    generated += 1
                    print(f"  OK {out_path.name}")
            except Exception as e:
                print(f"  ERROR {img_type} for {product_key}: {e}")

    print(f"\n  {generated} marketing thumbnails generated in {marketing_dir}")
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python marketing_thumbnail_generator.py <images_folder> [pack_code] [theme_name]")
        sys.exit(1)
    images_folder = sys.argv[1]
    pack_code = sys.argv[2] if len(sys.argv) > 2 else "LLB01"
    theme_name = sys.argv[3] if len(sys.argv) > 3 else "Theme"
    ok = generate_marketing_thumbnails(images_folder, pack_code, theme_name)
    sys.exit(0 if ok else 1)
