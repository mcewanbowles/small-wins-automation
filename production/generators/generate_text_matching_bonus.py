#!/usr/bin/env python3

import os
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from PIL import Image
import tempfile


NAVY = HexColor('#1E3A5F')
TEAL = HexColor('#2AAEAE')
WHITE = HexColor('#FFFFFF')
LIGHT_GRAY = HexColor('#999999')
BG = HexColor('#F0F8FF')

LIGHT_BLUE_BORDER = '#A0C4E8'
NAVY_BORDER = '#1E3A5F'


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return r, g, b


def _load_brown_bear_icon_image() -> Image.Image | None:
    root = _project_root()
    icons_colored_dir = root / 'assets' / 'themes' / 'brown_bear' / 'icons_colored'
    legacy_icons_dir = root / 'assets' / 'themes' / 'brown_bear' / 'icons'
    icons_dir = icons_colored_dir if icons_colored_dir.exists() else legacy_icons_dir
    p = icons_dir / 'Brown bear.png'
    if not p.exists():
        p = icons_dir / 'Brown Bear.png'
    if not p.exists():
        return None
    return Image.open(p)


def _draw_frame(c: canvas.Canvas, width: float, height: float, title: str, subtitle: str | None = None):
    margin = 0.5 * inch
    c.setStrokeColor(NAVY)
    c.setLineWidth(3)
    c.roundRect(margin, margin, width - 2 * margin, height - 2 * margin, 0.12 * inch)

    accent_padding = 0.3 * inch
    accent_h = 0.95 * inch
    accent_y = margin + (height - 2 * margin) - accent_h - accent_padding
    accent_w = (width - 2 * margin) - 2 * accent_padding

    c.setFillColor(TEAL)
    c.roundRect(margin + accent_padding, accent_y, accent_w, accent_h, 0.12 * inch, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 24)
    c.drawCentredString(width / 2, accent_y + accent_h * 0.62, title)

    if subtitle:
        c.setFont('Helvetica', 10)
        c.drawCentredString(width / 2, accent_y + accent_h * 0.22, subtitle)

    return {
        'margin': margin,
        'accent_y': accent_y,
    }


def _footer(c: canvas.Canvas, width: float, margin: float):
    y = margin + 0.18 * inch
    c.setFillColor(LIGHT_GRAY)
    c.setFont('Helvetica', 9)
    c.drawCentredString(width / 2, y + 13, 'teacherspayteachers.com/Store/Small-Wins-Studio')
    c.setFont('Helvetica', 8.5)
    c.drawCentredString(width / 2, y, 'Small Wins Studio  © 2026 All rights reserved.')


def _draw_matching_cutouts_header(c: canvas.Canvas, title: str, subtitle: str, pack_code: str = 'BB03'):
    width, height = letter
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin

    c.setStrokeColorRGB(*_hex_to_rgb(LIGHT_BLUE_BORDER))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)

    accent_margin = 0.08 * inch
    accent_height = 1.0 * inch
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin

    c.setFillColor(TEAL)
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)

    c.setFillColorRGB(*_hex_to_rgb('#001F3F'))
    try:
        c.setFont('Comic-Sans-MS-Bold', 28)
    except Exception:
        c.setFont('Helvetica-Bold', 28)
    title_y = accent_y + accent_height / 2 + 10
    c.drawCentredString(width / 2, title_y, title)

    try:
        c.setFont('Comic-Sans-MS', 20)
    except Exception:
        c.setFont('Helvetica', 20)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawCentredString(width / 2, title_y - 32, subtitle)

    footer_y = border_margin + 0.3 * inch
    c.setFont('Helvetica', 9)
    c.setFillColorRGB(*_hex_to_rgb('#999999'))
    footer_line2 = ' 2025 Small Wins Studio. PCS symbols used with active PCS Maker Personal License.'
    c.drawCentredString(width / 2, footer_y, footer_line2)

    c.setFillColorRGB(0, 0, 0)
    footer_line1 = f'Text Matching Bonus | {pack_code}'
    c.drawCentredString(width / 2, footer_y + 12, footer_line1)

    return {
        'border_margin': border_margin,
        'accent_y': accent_y,
    }


def _draw_bonus_cover_page(c: canvas.Canvas, theme_name: str = 'Brown Bear', pack_code: str = 'BB03'):
    width, height = letter
    border_margin = 0.25 * inch
    content_width = width - 2 * border_margin
    content_height = height - 2 * border_margin

    c.setStrokeColorRGB(*_hex_to_rgb(LIGHT_BLUE_BORDER))
    c.setLineWidth(3)
    c.roundRect(border_margin, border_margin, content_width, content_height, 10, stroke=1, fill=0)

    accent_margin = 0.08 * inch
    accent_height = 1.0 * inch
    accent_x = border_margin + accent_margin
    accent_y = height - border_margin - accent_height - accent_margin - 0.1 * inch
    accent_width = content_width - 2 * accent_margin

    c.setFillColor(TEAL)
    c.roundRect(accent_x, accent_y, accent_width, accent_height, 8, stroke=0, fill=1)

    c.setFillColorRGB(*_hex_to_rgb('#001F3F'))
    try:
        c.setFont('Comic-Sans-MS-Bold', 34)
    except Exception:
        c.setFont('Helvetica-Bold', 34)
    c.drawCentredString(width / 2, accent_y + accent_height / 2 + 12, 'Text Matching Cards')

    try:
        c.setFont('Comic-Sans-MS', 22)
    except Exception:
        c.setFont('Helvetica', 22)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawCentredString(width / 2, accent_y + accent_height / 2 - 24, f'{theme_name} BONUS')

    icon = _load_brown_bear_icon_image()
    if icon is not None:
        tmp_dir = Path(tempfile.gettempdir())
        tmp_path = tmp_dir / 'bb_bonus_cover_icon.png'
        icon.convert('RGBA').save(tmp_path)
        img_size = 3.0 * inch
        img_x = width / 2 - img_size / 2
        img_y = accent_y - 3.45 * inch
        c.drawImage(str(tmp_path), img_x, img_y, width=img_size, height=img_size, preserveAspectRatio=True, mask='auto')

    c.setFillColorRGB(*_hex_to_rgb('#001F3F'))
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(width / 2, accent_y - 3.75 * inch, 'Cut-and-use word cards')
    c.setFont('Helvetica', 12)
    c.setFillColorRGB(0.25, 0.25, 0.25)
    c.drawCentredString(width / 2, accent_y - 4.05 * inch, '4 pages (20 cards per page)')
    c.drawCentredString(width / 2, accent_y - 4.25 * inch, 'Includes “Brown Bear” set + “Real Photo” set')

    footer_y = border_margin + 0.3 * inch
    c.setFont('Helvetica', 9)
    c.setFillColorRGB(*_hex_to_rgb('#999999'))
    footer_line2 = ' 2025 Small Wins Studio. PCS symbols used with active PCS Maker Personal License.'
    c.drawCentredString(width / 2, footer_y, footer_line2)
    c.setFont('Helvetica', 10)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width / 2, footer_y + 12, f'Matching Bonus | {pack_code}')

    c.showPage()


def _bonus_labels_for_brown_bear_icons() -> list[str]:
    root = _project_root()
    icons_colored_dir = root / 'assets' / 'themes' / 'brown_bear' / 'icons_colored'
    legacy_icons_dir = root / 'assets' / 'themes' / 'brown_bear' / 'icons'
    icons_dir = icons_colored_dir if icons_colored_dir.exists() else legacy_icons_dir
    if not icons_dir.exists():
        raise FileNotFoundError(str(icons_dir))

    labels: list[str] = []
    for p in sorted(icons_dir.glob('*.png')):
        stem = p.stem
        if stem.lower() == 'brown bear':
            continue
        labels.append(stem.title())

    if 'Brown Bear' not in labels:
        labels.insert(0, 'Brown Bear')

    if 'Bear' not in labels:
        labels.insert(1, 'Bear')

    return labels


def _draw_thank_you_page(c: canvas.Canvas):
    width, height = letter
    frame = _draw_frame(
        c,
        width,
        height,
        'BONUS: Text Matching',
        'Large-print word cards + game ideas (SPED-friendly)',
    )

    margin = frame['margin']
    content_left = margin + 0.35 * inch
    content_right = width - margin - 0.35 * inch
    content_w = content_right - content_left

    y = frame['accent_y'] - 0.40 * inch

    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 18)
    c.drawString(content_left, y, 'Thank you for purchasing!')

    y -= 0.30 * inch
    c.setFont('Helvetica', 11)
    c.drawString(content_left, y, 'This bonus adds text-only matching cards to extend learning and increase flexibility.')

    box_gap = 0.22 * inch
    box_h = 1.45 * inch

    def box(title: str, lines: list[str], y_top: float):
        c.setFillColor(BG)
        c.setStrokeColor(TEAL)
        c.setLineWidth(2)
        c.roundRect(content_left, y_top - box_h, content_w, box_h, 0.12 * inch, fill=1, stroke=1)

        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 12)
        c.drawString(content_left + 0.22 * inch, y_top - 0.28 * inch, title)

        c.setFont('Helvetica', 10.5)
        yy = y_top - 0.55 * inch
        for line in lines:
            c.drawString(content_left + 0.28 * inch, yy, f'- {line}')
            yy -= 0.18 * inch

    y -= 0.35 * inch
    box(
        'Why text-only cards help (SPED benefits)',
        [
            'Supports early literacy and vocabulary (print awareness)',
            'Builds generalization: picture ↔ word ↔ real-world concepts',
            'Gives a higher-level option without changing the matching routine',
            'Great for AAC modeling: same/different, my turn/your turn, more, finished',
        ],
        y,
    )

    y -= box_h + box_gap
    box(
        'Two versions included (use both!)',
        [
            '“Brown Bear” to match book-based icons and story themes',
            '“Bear” to match real photos and real-world vocabulary',
            'Use whichever word is already in your student’s system',
        ],
        y,
    )

    y -= box_h + box_gap
    box(
        'Easy game ideas (new ways to use the same materials)',
        [
            'Memory: place cards face down and find pairs',
            'I Spy: pick a word card and find the matching picture',
            'Sort & Match: nouns vs color+animal phrases (Black Sheep vs Sheep)',
            'Partner Match: one student has words, one has pictures',
            'Errorless choice: show 2–3 cards and ask “Which says …?”',
        ],
        y,
    )

    _footer(c, width, margin)
    c.showPage()


def _draw_text_cutout_page_20(c: canvas.Canvas, words: list[str], page_title: str, subtitle: str = 'Brown Bear', pack_code: str = 'BB03'):
    width, height = letter

    header = _draw_matching_cutouts_header(c, page_title, subtitle, pack_code=pack_code)

    box_size = 1.28 * inch
    spacing = 0.05 * inch
    border_pts = 3
    cols = 4
    rows = 5

    grid_width = cols * box_size + (cols - 1) * spacing
    start_x = (width - grid_width) / 2
    # Match Matching cutouts template positioning
    content_top = header['accent_y'] - 0.4 * inch
    start_y = content_top - 0.3 * inch

    def fit_font(text: str) -> int:
        max_size = 22
        min_size = 10
        target_w = box_size - 0.18 * inch
        for fs in range(max_size, min_size - 1, -1):
            try:
                c.setFont('Comic-Sans-MS-Bold', fs)
                font_name = 'Comic-Sans-MS-Bold'
            except Exception:
                c.setFont('Helvetica-Bold', fs)
                font_name = 'Helvetica-Bold'
            if c.stringWidth(text, font_name, fs) <= target_w:
                return fs
        return min_size

    for col in range(cols):
        if col >= len(words):
            break
        word = words[col]
        for row in range(rows):
            box_x = start_x + col * (box_size + spacing)
            box_y = start_y - row * (box_size + spacing) - box_size
            c.setStrokeColorRGB(*_hex_to_rgb(NAVY_BORDER))
            c.setLineWidth(border_pts)
            c.roundRect(box_x, box_y, box_size, box_size, 8.64, stroke=1, fill=0)

            fs = fit_font(word)
            c.setFillColorRGB(*_hex_to_rgb('#001F3F'))
            try:
                c.setFont('Comic-Sans-MS-Bold', fs)
                font_name = 'Comic-Sans-MS-Bold'
            except Exception:
                c.setFont('Helvetica-Bold', fs)
                font_name = 'Helvetica-Bold'
            text_y = box_y + box_size / 2 - fs * 0.35
            c.drawCentredString(box_x + box_size / 2, text_y, word)

    c.showPage()


def _draw_text_cutouts_pages(c: canvas.Canvas, labels: list[str]):
    width, height = letter
    margin = 0.5 * inch

    cols = 3
    rows = 5
    gap = 0.18 * inch

    usable_w = width - 2 * margin
    usable_h = height - 2 * margin - 1.15 * inch

    card_w = (usable_w - (cols - 1) * gap) / cols
    card_h = (usable_h - (rows - 1) * gap) / rows

    def header(page_title: str):
        frame = _draw_frame(c, width, height, page_title, 'Cut out and use with your matching boards')
        _footer(c, width, frame['margin'])
        return frame

    def draw_card(x: float, y: float, text: str):
        c.setFillColor(WHITE)
        c.setStrokeColor(NAVY)
        c.setLineWidth(2)
        c.roundRect(x, y, card_w, card_h, 0.10 * inch, fill=1, stroke=1)

        c.setFillColor(NAVY)
        max_font = 28
        min_font = 14
        target_w = card_w - 0.30 * inch
        font_size = max_font
        while font_size >= min_font:
            c.setFont('Helvetica-Bold', font_size)
            if c.stringWidth(text, 'Helvetica-Bold', font_size) <= target_w:
                break
            font_size -= 1

        c.setFont('Helvetica-Bold', font_size)
        c.drawCentredString(x + card_w / 2, y + card_h / 2 - font_size * 0.35, text)

    per_page = cols * rows
    pages = (len(labels) + per_page - 1) // per_page

    idx = 0
    for page in range(pages):
        header('Text Matching Cards')

        top = height - margin - 1.35 * inch
        for r in range(rows):
            for col in range(cols):
                if idx >= len(labels):
                    break
                x = margin + col * (card_w + gap)
                y = top - r * (card_h + gap) - card_h
                draw_card(x, y, labels[idx])
                idx += 1
            if idx >= len(labels):
                break

        c.showPage()


def generate_text_matching_bonus(output_path: Path):
    c = canvas.Canvas(str(output_path), pagesize=letter)

    _draw_bonus_cover_page(c, theme_name='Brown Bear', pack_code='BB03')

    character_words = [
        'Brown Bear',
        'Red Bird',
        'Yellow Duck',
        'Blue Horse',
        'Green Frog',
        'Purple Cat',
        'Black Sheep',
        'Eyes',
    ]

    real_words = [
        'Bear',
        'Bird',
        'Duck',
        'Horse',
        'Frog',
        'Cat',
        'Dog',
        'Sheep',
    ]

    _draw_text_cutout_page_20(c, character_words[0:4], 'Cut Out Matching Pieces', subtitle='Brown Bear Characters', pack_code='BB03')
    _draw_text_cutout_page_20(c, character_words[4:8], 'Cut Out Matching Pieces', subtitle='Brown Bear Characters', pack_code='BB03')
    _draw_text_cutout_page_20(c, real_words[0:4], 'Cut Out Matching Pieces', subtitle='Real Photos', pack_code='BB03')
    _draw_text_cutout_page_20(c, real_words[4:8], 'Cut Out Matching Pieces', subtitle='Real Photos', pack_code='BB03')

    c.save()
    return output_path


if __name__ == '__main__':
    root = _project_root()
    out = root / 'production' / 'final_products' / 'brown_bear' / 'matching' / 'BONUS_Text_Matching_Cards.pdf'
    os.makedirs(out.parent, exist_ok=True)
    generate_text_matching_bonus(out)
    print(f"OK Created: {out}")
