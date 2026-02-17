#!/usr/bin/env python3
"""Professional Quick Start Guide Generator — Rich 2-Column Layout.

Produces a single-page Quick Start for each product (Matching, Find & Cover,
Bingo) using the same design language as the old HTML templates but rendered
entirely in ReportLab so no browser/wkhtmltopdf dependency is needed.

Design:
- Small Wins logo (top-left) + teal header accent (top-right)
- 2-column body with detailed sections
- Teal section headings with underlines
- Content boxes (grey bg, teal left border)
- Yellow highlight boxes
- Numbered steps with teal circles
- Light-blue rounded border (matching product design system)
- Gold standard footer (grey, 2 lines)
"""

import os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
try:
    pdfmetrics.registerFont(TTFont('ComicSans', 'C:/Windows/Fonts/comic.ttf'))
    pdfmetrics.registerFont(TTFont('ComicSans-Bold', 'C:/Windows/Fonts/comicbd.ttf'))
    TITLE_FONT = 'ComicSans-Bold'
    BODY_FONT = 'ComicSans'
except Exception:
    try:
        pdfmetrics.registerFont(TTFont('ComicSans', '/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf'))
        pdfmetrics.registerFont(TTFont('ComicSans-Bold', '/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS_Bold.ttf'))
        TITLE_FONT = 'ComicSans-Bold'
        BODY_FONT = 'ComicSans'
    except Exception:
        TITLE_FONT = 'Helvetica-Bold'
        BODY_FONT = 'Helvetica'

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
TEAL = HexColor('#20B2AA')
LIGHT_BLUE_BORDER = HexColor('#A0C4E8')
TEXT_COLOR = HexColor('#333333')
SECTION_BG = HexColor('#F8F9FA')
HIGHLIGHT_BG = HexColor('#FFFBEA')
HIGHLIGHT_BORDER = HexColor('#FFD700')
INFO_BG = HexColor('#E6F7FF')
INFO_BORDER = HexColor('#1890FF')
FOOTER_GREY = HexColor('#999999')

# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = letter  # 612 x 792 pt
BORDER_MARGIN = 0.25 * inch
CONTENT_LEFT = BORDER_MARGIN + 0.35 * inch
CONTENT_RIGHT = PAGE_W - BORDER_MARGIN - 0.35 * inch
CONTENT_W = CONTENT_RIGHT - CONTENT_LEFT
COL_GAP = 0.18 * inch
COL_W = (CONTENT_W - COL_GAP) / 2
COL1_X = CONTENT_LEFT
COL2_X = CONTENT_LEFT + COL_W + COL_GAP

# Font sizes
HEADER_TITLE_SIZE = 20
HEADER_SUB_SIZE = 11
SECTION_TITLE_SIZE = 11
BODY_SIZE = 9
SMALL_SIZE = 8
STEP_NUM_SIZE = 7

LOGO_PATH = Path(__file__).parent / 'assets' / 'branding' / 'logos' / 'small_wins_logo_with_text.png'


# ===================================================================
# Drawing helpers
# ===================================================================

def _draw_border(c):
    """Light-blue rounded border matching the product design system."""
    c.setStrokeColor(LIGHT_BLUE_BORDER)
    c.setLineWidth(3)
    c.roundRect(BORDER_MARGIN, BORDER_MARGIN,
                PAGE_W - 2 * BORDER_MARGIN, PAGE_H - 2 * BORDER_MARGIN,
                9, stroke=1, fill=0)


def _draw_header(c, title, subtitle):
    """Logo (left) + teal accent bar with title (right). Returns y below header."""
    header_top = PAGE_H - BORDER_MARGIN - 0.12 * inch
    accent_h = 0.65 * inch
    logo_w = 1.25 * inch

    # Logo
    if LOGO_PATH.exists():
        logo_x = CONTENT_LEFT
        logo_y = header_top - accent_h - 0.08 * inch
        c.drawImage(str(LOGO_PATH), logo_x, logo_y,
                    width=logo_w, height=accent_h + 0.08 * inch,
                    preserveAspectRatio=True, mask='auto')

    # Teal accent bar
    accent_x = CONTENT_LEFT + logo_w + 0.12 * inch
    accent_w = CONTENT_RIGHT - accent_x
    accent_y = header_top - accent_h
    c.setFillColor(TEAL)
    c.roundRect(accent_x, accent_y, accent_w, accent_h, 9, stroke=0, fill=1)

    # Title text (white, centred in accent bar)
    mid_x = accent_x + accent_w / 2
    c.setFillColor(white)
    c.setFont(TITLE_FONT, HEADER_TITLE_SIZE)
    c.drawCentredString(mid_x, accent_y + accent_h - 0.28 * inch, title)
    c.setFont(BODY_FONT, HEADER_SUB_SIZE)
    c.drawCentredString(mid_x, accent_y + 0.12 * inch, subtitle)

    return accent_y - 0.12 * inch  # y below header


def _draw_footer(c, product_name, pack_code):
    """Gold-standard 2-line footer in grey."""
    y2 = BORDER_MARGIN + 0.15 * inch
    y1 = y2 + 0.14 * inch
    c.setFillColor(FOOTER_GREY)
    c.setFont(BODY_FONT, SMALL_SIZE)
    c.drawCentredString(PAGE_W / 2, y2,
                        'Small Wins Studio | PCS symbols used with active PCS Maker Personal License. | \u00a9 2026')
    c.setFont(TITLE_FONT, SMALL_SIZE + 1)
    c.drawCentredString(PAGE_W / 2, y1,
                        f'Quick Start Guide \u2014 {product_name} | {pack_code}')


def _section_heading(c, x, y, text, col_w=None):
    """Teal bold heading with underline. Returns y below."""
    w = col_w or COL_W
    c.setFillColor(TEAL)
    c.setFont(TITLE_FONT, SECTION_TITLE_SIZE)
    c.drawString(x, y, text)
    y -= 3
    c.setStrokeColor(TEAL)
    c.setLineWidth(1.5)
    c.line(x, y, x + w, y)
    return y - 8


def _body_text(c, x, y, text, bold=False, color=None, size=None):
    """Draw a single line of body text. Returns y below."""
    c.setFillColor(color or TEXT_COLOR)
    c.setFont(TITLE_FONT if bold else BODY_FONT, size or BODY_SIZE)
    c.drawString(x, y, text)
    return y - (size or BODY_SIZE) - 3


def _bullet_list(c, x, y, items):
    """Draw bullet list. Items can be str or (bold_part, rest). Returns y below."""
    for item in items:
        if isinstance(item, tuple):
            c.setFillColor(TEAL)
            c.setFont(TITLE_FONT, BODY_SIZE)
            c.drawString(x, y, '\u2022 ')
            bx = x + c.stringWidth('\u2022 ', TITLE_FONT, BODY_SIZE)
            c.drawString(bx, y, item[0])
            rx = bx + c.stringWidth(item[0], TITLE_FONT, BODY_SIZE)
            c.setFillColor(TEXT_COLOR)
            c.setFont(BODY_FONT, BODY_SIZE)
            c.drawString(rx, y, ' ' + item[1])
        else:
            c.setFillColor(TEXT_COLOR)
            c.setFont(BODY_FONT, BODY_SIZE)
            c.drawString(x, y, f'\u2022 {item}')
        y -= BODY_SIZE + 3.5
    return y


def _numbered_list(c, x, y, items):
    """Draw numbered list with teal circle badges. Returns y below."""
    for i, item in enumerate(items, 1):
        cx = x + 5
        cy = y + 3
        c.setFillColor(TEAL)
        c.circle(cx, cy, 5.5, stroke=0, fill=1)
        c.setFillColor(white)
        c.setFont(TITLE_FONT, STEP_NUM_SIZE)
        c.drawCentredString(cx, cy - 2.5, str(i))
        c.setFillColor(TEXT_COLOR)
        c.setFont(BODY_FONT, BODY_SIZE)
        c.drawString(x + 14, y, item)
        y -= BODY_SIZE + 4
    return y


def _content_box(c, x, y, w, lines, border_color=None):
    """Grey box with optional left border. Returns y below."""
    line_h = BODY_SIZE + 3
    box_h = len(lines) * line_h + 10
    box_y = y - box_h + 4
    c.setFillColor(SECTION_BG)
    c.roundRect(x, box_y, w, box_h, 4, stroke=0, fill=1)
    if border_color:
        c.setFillColor(border_color)
        c.rect(x, box_y, 3.5, box_h, stroke=0, fill=1)
    ty = y - 4
    for line in lines:
        if isinstance(line, tuple):
            c.setFillColor(TEAL)
            c.setFont(TITLE_FONT, BODY_SIZE)
            c.drawString(x + 10, ty, line[0])
            rx = x + 10 + c.stringWidth(line[0], TITLE_FONT, BODY_SIZE)
            c.setFillColor(TEXT_COLOR)
            c.setFont(BODY_FONT, BODY_SIZE)
            c.drawString(rx, ty, ' ' + line[1])
        else:
            c.setFillColor(TEXT_COLOR)
            c.setFont(BODY_FONT, BODY_SIZE)
            c.drawString(x + 10, ty, line)
        ty -= line_h
    return box_y - 4


def _highlight_box(c, x, y, w, lines):
    """Yellow highlight box. Returns y below."""
    line_h = BODY_SIZE + 3
    box_h = len(lines) * line_h + 12
    box_y = y - box_h + 4
    c.setFillColor(HIGHLIGHT_BG)
    c.setStrokeColor(HIGHLIGHT_BORDER)
    c.setLineWidth(1.5)
    c.roundRect(x, box_y, w, box_h, 5, stroke=1, fill=1)
    ty = y - 4
    for line in lines:
        if isinstance(line, tuple):
            c.setFillColor(HexColor('#D97706'))
            c.setFont(TITLE_FONT, BODY_SIZE)
            c.drawString(x + 8, ty, line[0])
            rx = x + 8 + c.stringWidth(line[0], TITLE_FONT, BODY_SIZE)
            c.setFillColor(TEXT_COLOR)
            c.setFont(BODY_FONT, BODY_SIZE)
            c.drawString(rx, ty, ' ' + line[1])
        else:
            c.setFillColor(TEXT_COLOR)
            c.setFont(BODY_FONT, BODY_SIZE)
            c.drawString(x + 8, ty, line)
        ty -= line_h
    return box_y - 4


def _info_box(c, x, y, w, lines):
    """Blue info box. Returns y below."""
    line_h = BODY_SIZE + 3
    box_h = len(lines) * line_h + 10
    box_y = y - box_h + 4
    c.setFillColor(INFO_BG)
    c.roundRect(x, box_y, w, box_h, 4, stroke=0, fill=1)
    c.setFillColor(INFO_BORDER)
    c.rect(x, box_y, 3.5, box_h, stroke=0, fill=1)
    ty = y - 4
    for line in lines:
        if isinstance(line, tuple):
            c.setFillColor(TEAL)
            c.setFont(TITLE_FONT, BODY_SIZE)
            c.drawString(x + 10, ty, line[0])
            rx = x + 10 + c.stringWidth(line[0], TITLE_FONT, BODY_SIZE)
            c.setFillColor(TEXT_COLOR)
            c.setFont(BODY_FONT, BODY_SIZE)
            c.drawString(rx, ty, ' ' + line[1])
        else:
            c.setFillColor(TEXT_COLOR)
            c.setFont(BODY_FONT, BODY_SIZE)
            c.drawString(x + 10, ty, line)
        ty -= line_h
    return box_y - 4


# ===================================================================
# MATCHING Quick Start
# ===================================================================

def generate_matching_quick_start(output_path, theme_name='Brown Bear', pack_code='BB03'):
    c = canvas.Canvas(str(output_path), pagesize=letter)
    _draw_border(c)
    y = _draw_header(c, 'QUICK START GUIDE', f'Matching to Boards \u2014 {theme_name}')

    # ---- LEFT COLUMN ----
    ly = y
    ly = _section_heading(c, COL1_X, ly, '\U0001f4e6 What this resource is')
    ly = _content_box(c, COL1_X, ly, COL_W, [
        'Match Boardmaker icons to real photographs.',
        'Students learn that symbols represent actual',
        'objects \u2014 critical for AAC users and supports',
        'generalisation beyond symbolic representations.',
    ], border_color=TEAL)

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f4da Part of a Differentiated Series')
    ly = _highlight_box(c, COL1_X, ly, COL_W, [
        ('This is part of a 5-level Matching series!', ''),
        'There are 5 levels available, each building on',
        ('the last for differentiation and growth tracking.', ''),
        ('Save with the complete bundle!', ''),
    ])

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f4e6 What\u2019s included')
    ly = _bullet_list(c, COL1_X + 6, ly, [
        '12 matching boards activity boards',
        'Cut-out matching pieces',
        'Colour + Black & White versions',
        ('Bonus:', 'Storage labels'),
    ])

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f527 Set-up steps')
    ly = _numbered_list(c, COL1_X + 6, ly, [
        'Print (Colour or B/W).',
        '(Optional) Print on cardstock for durability.',
        '(Optional) Laminate boards + pieces.',
        'Cut the pieces.',
        '(Optional) Add Velcro to boards + pieces.',
        'Store each board with its pieces.',
    ])

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f527 Prep (choose what suits your classroom)')
    ly = _content_box(c, COL1_X, ly, COL_W, [
        ('You\u2019ll need:', 'printer + scissors (or paper trimmer)'),
        ('Optional:', 'cardstock, laminator, Velcro dots, zip bags'),
    ], border_color=TEAL)

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f464 Student routine (station friendly)')
    ly = _numbered_list(c, COL1_X + 6, ly, [
        'Look at the target (icon OR photo).',
        'Think about what it represents.',
        'Find the matching piece.',
        'Place it on the Velcro strip.',
        'Both icon and photo = the SAME thing!',
    ])

    # ---- RIGHT COLUMN ----
    ry = y
    ry = _section_heading(c, COL2_X, ry, '\U0001f468\u200d\U0001f3eb Teaching support (prompting ladder)')
    ry = _content_box(c, COL2_X, ry, COL_W, [
        'Use the least help possible, then fade prompts:',
    ], border_color=TEAL)
    ry = _numbered_list(c, COL2_X + 6, ry, [
        'Independent (wait time)',
        'Gesture (point to the spot)',
        'Verbal cue (\u201cmatch\u201d, \u201csame\u201d)',
        'Model (place one piece)',
        'Physical support (only if needed)',
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\U0001f4ac Communication + AAC')
    ry = _info_box(c, COL2_X, ry, COL_W, [
        ('AAC users:', 'This resource is perfect for'),
        'communication modeling! Model a few consistent',
        'words while matching using AAC e.g. My turn,',
        'Your turn, Same, Different, Again etc.',
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\U0001f3af Ways to use this set (low-prep)')
    ry = _bullet_list(c, COL2_X + 6, ry, [
        ('Independent work station:', 'board + pieces in a pouch'),
        ('Work box / task box:', 'one board per box'),
        ('File folder activity:', 'board in folder, pieces in pocket'),
        ('1:1 teaching:', 'hand one piece at a time'),
        ('Small group rotation:', 'swap boards when finished'),
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\U0001f527 Troubleshooting (teacher time-savers)')
    ry = _bullet_list(c, COL2_X + 6, ry, [
        ('If confused:', 'Show the real object if possible'),
        ('If wrong matches:', 'Compare icon and photo side-by-side'),
        ('If showing success:', 'Discuss \u201csame but looks different\u201d'),
        ('If mastering:', 'This is advanced generalisation!'),
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\u27a1\ufe0f Next steps (when ready)')
    ry = _highlight_box(c, COL2_X, ry, COL_W, [
        ('When student achieves 80%+ independent accuracy:', ''),
        'Progress to the next level for more challenge!',
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\U0001f3ae Quick games (same materials)')
    ry = _bullet_list(c, COL2_X + 6, ry, [
        ('Real vs Symbol:', 'Sort into \u201creal\u201d and \u201cicon\u201d piles'),
        ('Photo Hunt:', 'Find the real photo that matches'),
        ('Match Pairs:', 'Lay all out, find icon-photo pairs'),
        ('Which is Which:', 'Name the object, student finds both'),
    ])

    _draw_footer(c, f'{theme_name} Matching', pack_code)
    c.save()
    print(f'OK Generated: {output_path}')


# ===================================================================
# FIND & COVER Quick Start
# ===================================================================

def generate_find_cover_quick_start(output_path, theme_name='Brown Bear', pack_code='BB04'):
    c = canvas.Canvas(str(output_path), pagesize=letter)
    _draw_border(c)
    y = _draw_header(c, 'QUICK START GUIDE', f'Find & Cover \u2014 {theme_name}')

    # ---- LEFT COLUMN ----
    ly = y
    ly = _section_heading(c, COL1_X, ly, '\U0001f4e6 What this resource is')
    ly = _content_box(c, COL1_X, ly, COL_W, [
        'A differentiated Find & Cover activity using',
        f'{theme_name} vocabulary. Students find target',
        'icons on a grid and cover them with chips,',
        'dabbers, or dry-erase markers.',
    ], border_color=TEAL)

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f4da Part of a Differentiated Series')
    ly = _highlight_box(c, COL1_X, ly, COL_W, [
        ('This is part of a 5-level Find & Cover series!', ''),
        'There are 5 levels available, each building on',
        ('the last for differentiation and growth tracking.', ''),
        ('Save with the complete bundle!', ''),
    ])

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f4e6 What\u2019s included')
    ly = _bullet_list(c, COL1_X + 6, ly, [
        '12 Find & Cover activity boards',
        'Cut-out covering pieces',
        'Colour + Black & White versions',
        ('Bonus:', 'Storage labels'),
    ])

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f527 Set-up steps')
    ly = _numbered_list(c, COL1_X + 6, ly, [
        'Print (Colour or B/W).',
        '(Optional) Print on cardstock for durability.',
        '(Optional) Laminate boards for reuse.',
        'Gather chips, dabbers, or dry-erase markers.',
        'Store each board in a folder or pouch.',
    ])

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f527 Prep (choose what suits your classroom)')
    ly = _content_box(c, COL1_X, ly, COL_W, [
        ('You\u2019ll need:', 'printer + chips or dabbers'),
        ('Optional:', 'cardstock, laminator, dry-erase markers'),
    ], border_color=TEAL)

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f464 Student routine (station friendly)')
    ly = _numbered_list(c, COL1_X + 6, ly, [
        'Look at the target icon at the top.',
        'Scan the grid to find matching icons.',
        'Cover each match with a chip or dabber.',
        'Check: did you find them all?',
        'Say or sign what you found!',
    ])

    # ---- RIGHT COLUMN ----
    ry = y
    ry = _section_heading(c, COL2_X, ry, '\U0001f468\u200d\U0001f3eb Teaching support (prompting ladder)')
    ry = _content_box(c, COL2_X, ry, COL_W, [
        'Use the least help possible, then fade prompts:',
    ], border_color=TEAL)
    ry = _numbered_list(c, COL2_X + 6, ry, [
        'Independent (wait time)',
        'Gesture (point to area)',
        'Verbal cue (\u201cfind\u201d, \u201clook\u201d)',
        'Model (cover one match)',
        'Physical support (only if needed)',
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\U0001f4ac Communication + AAC')
    ry = _info_box(c, COL2_X, ry, COL_W, [
        ('AAC users:', 'This resource is perfect for'),
        'communication modeling! Model a few consistent',
        'words: find, cover, same, more, done, look.',
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\U0001f3af Ways to use this set (low-prep)')
    ry = _bullet_list(c, COL2_X + 6, ry, [
        ('Independent work station:', 'board + chips in a pouch'),
        ('Work box / task box:', 'one board per box'),
        ('File folder activity:', 'board in folder, chips in bag'),
        ('1:1 teaching:', 'point to each icon while searching'),
        ('Small group rotation:', 'swap boards when finished'),
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\U0001f527 Troubleshooting (teacher time-savers)')
    ry = _bullet_list(c, COL2_X + 6, ry, [
        ('If confused:', 'Point to target, then scan together'),
        ('If missing icons:', 'Use finger to track row by row'),
        ('If showing success:', 'Increase to next level'),
        ('If mastering:', 'Try timed challenges!'),
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\u27a1\ufe0f Next steps (when ready)')
    ry = _highlight_box(c, COL2_X, ry, COL_W, [
        ('When student achieves 80%+ independent accuracy:', ''),
        'Progress to the next level for more challenge!',
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\U0001f3ae Quick games (same materials)')
    ry = _bullet_list(c, COL2_X + 6, ry, [
        ('Race:', 'Who covers all targets first?'),
        ('Count:', 'How many did you find? Count aloud!'),
        ('Point & Name:', 'Say what you found!'),
        ('Memory:', 'Cover board, recall what was there'),
    ])

    _draw_footer(c, f'{theme_name} Find & Cover', pack_code)
    c.save()
    print(f'OK Generated: {output_path}')


# ===================================================================
# BINGO Quick Start
# ===================================================================

def generate_bingo_quick_start(output_path, theme_name='Brown Bear', pack_code='BB02'):
    c = canvas.Canvas(str(output_path), pagesize=letter)
    _draw_border(c)
    y = _draw_header(c, 'QUICK START GUIDE', f'Bingo \u2014 {theme_name}')

    # ---- LEFT COLUMN ----
    ly = y
    ly = _section_heading(c, COL1_X, ly, '\U0001f4e6 What this resource is')
    ly = _content_box(c, COL1_X, ly, COL_W, [
        f'A differentiated Bingo game using {theme_name}',
        'vocabulary. Students listen, look, and cover',
        'matches on their Bingo board. 5 levels from',
        '3\u00d73 real photos to 4\u00d74 text-only.',
    ], border_color=TEAL)

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f4da Part of a Differentiated Series')
    ly = _highlight_box(c, COL1_X, ly, COL_W, [
        ('This is part of a 5-level Bingo series!', ''),
        'There are 5 levels available, each building on',
        ('the last for differentiation and growth tracking.', ''),
        ('Save with the complete bundle!', ''),
    ])

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f4e6 What\u2019s included (per level)')
    ly = _bullet_list(c, COL1_X + 6, ly, [
        '8 unique Bingo cards',
        '1 calling cards page (cut out to call the game)',
        'Colour + Black & White versions',
        ('Bonus:', 'Storage labels'),
    ])

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f527 Set-up steps')
    ly = _numbered_list(c, COL1_X + 6, ly, [
        'Print Bingo cards (Colour or B/W).',
        'Print and cut out calling cards.',
        '(Optional) Laminate cards for reuse.',
        'Gather chips, dabbers, or tokens.',
        'Store cards + calling cards together.',
    ])

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f3b2 How to play')
    ly = _numbered_list(c, COL1_X + 6, ly, [
        'Give each player a Bingo card.',
        'Draw a calling card and show/say it.',
        'Players find and cover the match.',
        'First to complete a win pattern wins!',
    ])

    ly -= 2
    ly = _section_heading(c, COL1_X, ly, '\U0001f3c6 Suggested win patterns')
    ly = _bullet_list(c, COL1_X + 6, ly, [
        ('Line:', 'any horizontal or vertical row'),
        ('Four corners:', 'cover all 4 corners'),
        ('X:', 'diagonals (if appropriate)'),
        ('Blackout:', 'cover the whole board'),
    ])

    # ---- RIGHT COLUMN ----
    ry = y
    ry = _section_heading(c, COL2_X, ry, '\U0001f468\u200d\U0001f3eb Teaching support (prompting ladder)')
    ry = _content_box(c, COL2_X, ry, COL_W, [
        'Use the least help possible, then fade prompts:',
    ], border_color=TEAL)
    ry = _numbered_list(c, COL2_X + 6, ry, [
        'Independent (wait time)',
        'Gesture (point to area on card)',
        'Verbal cue (\u201cfind\u201d, \u201clook\u201d)',
        'Model (cover one match)',
        'Physical support (only if needed)',
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\U0001f4ac Communication + AAC')
    ry = _info_box(c, COL2_X, ry, COL_W, [
        ('AAC users:', 'This resource is perfect for'),
        'communication modeling! Model: look, find,',
        'same, cover, more, done, my turn, your turn.',
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\U0001f3af Ways to use this set (low-prep)')
    ry = _bullet_list(c, COL2_X + 6, ry, [
        ('Whole class:', 'teacher calls, all students play'),
        ('Small group:', '3\u20134 students, take turns calling'),
        ('1:1 teaching:', 'teacher and student play together'),
        ('Independent:', 'student matches calling cards solo'),
        ('Reward activity:', 'earned game time with peers'),
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\U0001f527 Troubleshooting (teacher time-savers)')
    ry = _bullet_list(c, COL2_X + 6, ry, [
        ('If confused:', 'Hold calling card next to board'),
        ('If slow scanning:', 'Use finger to track row by row'),
        ('If showing success:', 'Move to next level'),
        ('If mastering:', 'Try text-only Level 5!'),
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\u27a1\ufe0f Next steps (when ready)')
    ry = _highlight_box(c, COL2_X, ry, COL_W, [
        ('When student achieves 80%+ independent accuracy:', ''),
        'Progress to the next level for more challenge!',
    ])

    ry -= 2
    ry = _section_heading(c, COL2_X, ry, '\U0001f527 Prep & Storage')
    ry = _content_box(c, COL2_X, ry, COL_W, [
        ('You\u2019ll need:', 'printer + scissors + chips/dabbers'),
        ('Optional:', 'cardstock, laminator, zip bags'),
        'Store cards + calling cards in labelled bags.',
        'Colour-code bags by level.',
    ], border_color=TEAL)

    _draw_footer(c, f'{theme_name} Bingo', pack_code)
    c.save()
    print(f'OK Generated: {output_path}')


# ===================================================================
# Main
# ===================================================================

if __name__ == '__main__':
    os.makedirs('review_pdfs', exist_ok=True)
    os.makedirs('samples/brown_bear/matching', exist_ok=True)
    os.makedirs('samples/brown_bear/find_cover', exist_ok=True)
    os.makedirs('samples/brown_bear/bingo', exist_ok=True)

    generate_matching_quick_start('review_pdfs/brown_bear_matching_quick_start.pdf')
    generate_matching_quick_start('samples/brown_bear/matching/brown_bear_matching_quick_start.pdf')

    generate_find_cover_quick_start('review_pdfs/brown_bear_find_cover_quick_start.pdf')
    generate_find_cover_quick_start('samples/brown_bear/find_cover/brown_bear_find_cover_quick_start.pdf')

    generate_bingo_quick_start('review_pdfs/brown_bear_bingo_quick_start.pdf')
    generate_bingo_quick_start('samples/brown_bear/bingo/brown_bear_bingo_quick_start.pdf')

    print('\nOK Professional Quick Start guides generated!')
    print('  Matching:     review_pdfs/brown_bear_matching_quick_start.pdf')
    print('  Find & Cover: review_pdfs/brown_bear_find_cover_quick_start.pdf')
    print('  Bingo:        review_pdfs/brown_bear_bingo_quick_start.pdf')
