"""Generate Top Tips for AAC Communication Partners with the standard SWS frame.

Per the spec addendum (SPEC_ADDENDUM_SUPPORT_DOCS_FRAME.md), all support docs
must use apply_small_wins_frame with accent strip, hero, border, and standard
double-line footer.

This generator replaces the static reference PDF with a framed version.
"""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

from utils.UNIVERSAL_STANDARDS import SWS_NAVY, SWS_TEAL, SWS_TEAL_LT
from utils.sws_design import DPI, _brand_font_pt, apply_small_wins_frame, hex_to_rgb, shrink_font_to_fit_with_pt

ROOT = Path(__file__).resolve().parents[2]
THEME = ROOT / "assets" / "themes" / "llama_llama_red_pajama"
OUTPUT = THEME / "OUTPUT"

PAGE_W = int(letter[0] * DPI / 72)
PAGE_H = int(letter[1] * DPI / 72)

NAVY = hex_to_rgb(SWS_NAVY)
TEAL = hex_to_rgb(SWS_TEAL)
TEAL_LT = hex_to_rgb(SWS_TEAL_LT)


def _font(pt: int, bold: bool = False):
    return _brand_font_pt(pt, bold=bold, brand="poppins" if bold else "nunito")


def _fit(text: str, pt: int, width: int, minimum: int = 10, bold: bool = True):
    return shrink_font_to_fit_with_pt(text, base_pt=pt, max_width_px=width, bold=bold, brand="poppins" if bold else "nunito", min_pt=minimum)[0]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def generate_top_tips(pack_code: str = "LLRP-TIPS", theme_name: str = "Llama Llama Red Pajama", output_dir: Path | None = None) -> Path:
    """Generate the Top Tips for AAC Communication Partners PDF with standard frame."""
    # Resolve hero
    hero_img = None
    try:
        for hp in [THEME / "hero.png", THEME / "hero_header.png"]:
            if hp.exists():
                im = Image.open(hp)
                hero_img = im.convert("RGBA") if im.mode != "RGBA" else im
                break
    except Exception:
        pass

    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    apply_small_wins_frame(
        page,
        product_title="Top Tips for AAC Partners",
        subtitle=f"{theme_name} — Small Wins Studio",
        pack_code=pack_code,
        page_num=1,
        total_pages=1,
        level=None,
        draw_footer=True,
        draw_pcs_line=True,
        draw_subtitle=True,
        header_left_icon=hero_img,
    )
    draw = ImageDraw.Draw(page)

    tips = [
        ("WAIT", "Allow 5–10 seconds of silence after each question or prompt. AAC users need time to navigate, select, and confirm their response."),
        ("MODEL", "Point to symbols on the board as you speak. AAC users learn language through repeated modelling, just as speaking children do."),
        ("OFFER CHOICES", "Present two clear options rather than open-ended questions. 'Book or toy?' is easier than 'What do you want?'"),
        ("CONFIRM", "Repeat back what the AAC user selected: 'You said bed. Yes, it is bedtime!' This validates their communication and builds confidence."),
        ("FOLLOW THEIR LEAD", "If the student points to an unexpected symbol, explore it. Communication is about connection, not just correct answers."),
        ("KEEP IT FUN", "Mix communication moments into play and reading. Celebrate every attempt — pointing, eye gaze, vocalisation, or symbol selection."),
        ("PARTNER WITH THE TEAM", "Share successful strategies with the speech pathologist, classroom teacher, and family. Consistency across settings accelerates progress."),
    ]

    margin = int(0.45 * DPI)
    content_w = PAGE_W - 2 * margin
    y = int(1.15 * DPI)

    for label, body in tips:
        # Tip card
        card_h = int(0.42 * DPI)
        # Label pill
        label_font = _fit(label, 14, int(2.0 * DPI), bold=True)
        bbox = draw.textbbox((0, 0), label, font=label_font)
        label_w = bbox[2] - bbox[0] + int(0.3 * DPI)
        label_h = bbox[3] - bbox[1] + int(0.15 * DPI)

        # Draw label pill
        pill_x1 = margin
        pill_y1 = y
        pill_x2 = pill_x1 + label_w
        pill_y2 = pill_y1 + label_h
        draw.rounded_rectangle([pill_x1, pill_y1, pill_x2, pill_y2], radius=int(0.06 * DPI), fill=TEAL)
        # Center label text in pill
        tx = pill_x1 + (label_w - (bbox[2] - bbox[0])) // 2 - bbox[0]
        ty = pill_y1 + (label_h - (bbox[3] - bbox[1])) // 2 - bbox[1]
        draw.text((tx, ty), label, fill=(255, 255, 255), font=label_font)

        # Body text to the right of pill
        body_x = pill_x2 + int(0.15 * DPI)
        body_font = _font(11, bold=False)
        body_w = content_w - (body_x - margin)
        lines = _wrap_text(draw, body, body_font, body_w)
        body_y = pill_y1 + int(0.02 * DPI)
        for line in lines:
            draw.text((body_x, body_y), line, fill=NAVY, font=body_font)
            body_y += int(0.16 * DPI)

        y = max(pill_y2, body_y) + int(0.12 * DPI)

    # Save
    out = output_dir or OUTPUT
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / f"{pack_code}_Top_Tips_AAC.pdf"

    buf = io.BytesIO()
    page.save(buf, format="PNG", dpi=(DPI, DPI))
    buf.seek(0)

    c = rl_canvas.Canvas(str(out_path), pagesize=letter)
    c.drawImage(ImageReader(buf), 0, 0, width=letter[0], height=letter[1])
    c.showPage()
    c.save()

    print(f"OK  {out_path}")
    return out_path


if __name__ == "__main__":
    generate_top_tips()
