"""
IEP_MONITORING_FORM.py
Small Wins Studio — IEP Progress Monitoring & Planning Form Generator

Generates a single A4 portrait page that provides:

  1. STUDENT + GOAL HEADER — editable fields for student name,
     teacher, date range, IEP goal, and target criterion
  2. 10-SESSION DATA GRID — one row per session (aligned to the
     two-week plan), columns for: date, activity used, accuracy %,
     prompt level, independence rating (1–5), notes
  3. GRAPHING STRIP — 10-point progress graph (dot + line) for
     quick visual trend identification, matches IDEA requirements
     for "periodic reports showing progress toward annual goals"
  4. SUMMARY + NEXT STEPS — tick boxes for instructional decisions:
     maintain / increase difficulty / change activity / refer for review
  5. FOOTER — product attribution and compliance note

EVIDENCE BASE:
  - IDEA (2004): IEP teams must document HOW progress will be measured
    and provide periodic reports to parents
  - Best practice (IRIS Center, 2024): formative data collected weekly,
    reviewed for trend to determine responsiveness to instruction
  - AAC literacy research (Wence et al., 2024): data must capture
    modality of response (verbal/AAC/gesture/written) not just correct/incorrect

DESIGN INTENT:
  Teacher prints one form per student per book. Works for a classroom aide
  or the teacher themselves. Circle/tick in hand during the lesson — no
  laptop required. Aligns directly with the two-week planner on the
  Pedagogical Reference Page.

USAGE:
  python IEP_MONITORING_FORM.py <slug> "<Book Title>" <PACK_CODE>
  python IEP_MONITORING_FORM.py stellaluna "Stellaluna" STEL-01

OUTPUT:
  OUTPUT/{pack_code}_IEP_MonitoringForm.pdf
"""

import sys
import io
from pathlib import Path
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
from utils.sws_design import apply_small_wins_frame, hex_to_rgb

# ─────────────────────────────────────────────
# BRAND PALETTE (confirmed SWS values)
# ─────────────────────────────────────────────
TEAL      = (49, 168, 160)
NAVY      = (13, 37, 69)
GOLD      = (225, 180, 45)
TEAL_LT   = (232, 248, 248)
MID_GRAY  = (229, 231, 235)
GRAY_BG   = (248, 249, 250)
WHITE     = (255, 255, 255)
VIO       = (124, 58, 237)
OCN       = (2, 132, 199)
EME       = (5, 150, 105)
RSE       = (225, 29, 72)
GRAY_TXT  = (120, 120, 120)
RED_DOT   = (239, 68, 68)

DPI = 300
PW = int(letter[0] * DPI / 72)
PH = int(letter[1] * DPI / 72)

# Logo asset (same as support docs)
LOGO_PATH = Path("assets/branding/logos/small_wins_logo_with_text.png")

# 10 sessions aligned to two-week plan
SESSIONS = [
    ("1", "Mon Wk 1", "Read aloud + Lesson Slides"),
    ("2", "Tue Wk 1", "AAC Board + Sentence Building"),
    ("3", "Wed Wk 1", "Matching + Sorting"),
    ("4", "Thu Wk 1", "Yes/No + Inferencing"),
    ("5", "Fri Wk 1", "Find & Cover + Bingo"),
    ("6", "Mon Wk 2", "Adapted Book"),
    ("7", "Tue Wk 2", "Sequencing"),
    ("8", "Wed Wk 2", "Syllable + Word Search"),
    ("9", "Thu Wk 2", "Spin & Cover + Inferencing"),
    ("10", "Fri Wk 2", "Bingo + Review"),
]

# Prompt level scale (standard SPED prompting hierarchy)
PROMPT_LEVELS = ["I", "G", "V", "M", "P", "FP"]
PROMPT_KEY    = "I=Independent  G=Gestural  V=Verbal  M=Model  P=Partial Physical  FP=Full Physical"

# Response modality options (AAC-inclusive, evidence-based)
MODALITY_KEY  = "W=Written/typed  A=AAC device/board  S=Spoken  G=Gesture/point  NR=No response"


def _font(pt, bold=False):
    """Brand fonts with robust fallbacks: Poppins (bold) + Nunito (regular)."""
    scale = DPI / 72
    size = max(1, int(pt * scale))
    fonts_dir = Path("fonts")
    assets_dir = Path("assets/fonts")
    pop_b = fonts_dir / "Poppins-Bold.ttf"
    pop_m = fonts_dir / "Poppins-Medium.ttf"
    pop_r = fonts_dir / "Poppins-Regular.ttf"
    nun_r = fonts_dir / "Nunito-Regular.ttf"
    nun_b = fonts_dir / "Nunito-Bold.ttf"
    # Fallback to assets/fonts if it exists
    if not pop_b.exists():
        pop_b = assets_dir / "Poppins-Bold.ttf"
        pop_m = assets_dir / "Poppins-Medium.ttf"
        pop_r = assets_dir / "Poppins-Regular.ttf"
        nun_r = assets_dir / "Nunito-Regular.ttf"
        nun_b = assets_dir / "Nunito-Bold.ttf"

    stack = []
    if bold:
        stack += [pop_b, pop_m, nun_b]
    else:
        stack += [nun_r, pop_r]
    stack += [
        Path("C:/Windows/Fonts/arialbd.ttf") if bold else Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") if bold else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for p in stack:
        try:
            if p and Path(p).exists():
                return ImageFont.truetype(str(p), size)
        except Exception:
            continue
    return ImageFont.load_default()


def _sz(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def _box(draw, rect, radius=0, fill=None, outline=None, width=1):
    if radius:
        draw.rounded_rectangle(rect, radius=radius, fill=fill,
                                outline=outline, width=width)
    else:
        draw.rectangle(rect, fill=fill, outline=outline, width=width)


def _write_line(draw, label, x, y, line_w, scale, label_font=None, line_color=None):
    """A labelled write line (printed label + underline)."""
    f = label_font or _font(7)
    lc = line_color or MID_GRAY
    draw.text((x, y), label, fill=NAVY, font=f)
    lw2, lh = _sz(draw, label, f)
    lx = x + lw2 + int(4 * scale)
    line_y = y + lh
    draw.line([lx, line_y, lx + line_w, line_y], fill=lc,
              width=int(1 * scale))
    return line_y + int(6 * scale)


def _header(page, draw, book_title, pack_code, scale):
    """Draw student/teacher/goal form fields below the accent strip.
    The accent strip and border are now provided by apply_small_wins_frame."""
    # Content starts below the accent strip.
    # Accent strip: starts at border_margin(0.25") + accent_margin(0.08") = 0.33"
    # and is 1.0" tall, so it ends at ~1.33". Start form fields at 1.75" with gap
    # to ensure subtitle text inside the accent strip never overlaps form fields.
    y = int(1.75 * DPI)
    margin = int(28 * scale)
    lf = _font(7.5)
    lw = int((PW - margin * 2 - int(16 * scale)) // 3)

    # Row 1: Student / Teacher / Date range
    col_x = [margin, margin + lw + int(8 * scale), margin + 2 * (lw + int(8 * scale))]
    labels_r1 = ["Student name:", "Teacher:", "Dates (from/to):"]
    for lbl, cx in zip(labels_r1, col_x):
        _, lh = _sz(draw, lbl, lf)
        lw2, _ = _sz(draw, lbl, lf)
        lx2 = cx + lw2 + int(4 * scale)
        draw.text((cx, y), lbl, fill=NAVY, font=lf)
        draw.line([lx2, y + lh, cx + lw - int(4 * scale), y + lh],
                  fill=MID_GRAY, width=int(1 * scale))
    y += int(20 * scale)

    # Row 2: IEP goal (full width)
    g_lbl = "IEP Goal:"
    _, gh = _sz(draw, g_lbl, lf)
    gw2, _ = _sz(draw, g_lbl, lf)
    draw.text((margin, y), g_lbl, fill=NAVY, font=lf)
    draw.line([margin + gw2 + int(4 * scale), y + gh,
               PW - margin, y + gh], fill=MID_GRAY, width=int(1 * scale))
    y += int(20 * scale)

    # Row 3: Criterion / Strand focus
    crit_lbl   = "Mastery criterion (e.g. 80% across 3 sessions):"
    strand_lbl = "Scarborough strand focus:"
    _, ch = _sz(draw, crit_lbl, lf)
    cw2, _ = _sz(draw, crit_lbl, lf)
    draw.text((margin, y), crit_lbl, fill=NAVY, font=lf)
    draw.line([margin + cw2 + int(4 * scale), y + ch,
               margin + lw * 2, y + ch], fill=MID_GRAY, width=int(1 * scale))
    sl2, _ = _sz(draw, strand_lbl, lf)
    draw.text((margin + lw * 2 + int(16 * scale), y), strand_lbl, fill=NAVY, font=lf)
    draw.line([margin + lw * 2 + int(16 * scale) + sl2 + int(4 * scale), y + ch,
               PW - margin, y + ch], fill=MID_GRAY, width=int(1 * scale))
    y += int(16 * scale)

    return y


def _data_grid(page, draw, scale, y_start, sessions=None):
    """
    10-row session data grid.
    Columns: # | Date | Activity | Correct/Total | % | Prompt | Modality | Notes
    Pass sessions to override the default two-week plan (e.g. generic
    session rows for inclusion inside a single-activity package).
    """
    margin = int(28 * scale)
    grid_w = PW - margin * 2

    # Column widths (must sum to grid_w)
    cols = [
        ("#",        int(20 * scale)),
        ("Day",      int(52 * scale)),
        ("Activity", int(grid_w // 4)),
        ("C/Total",  int(38 * scale)),
        ("%",        int(28 * scale)),
        ("Prompt",   int(40 * scale)),
        ("Mode",     int(50 * scale)),   # 4 letter boxes @10+2 need ~46 units
        ("Notes / Observations", None),  # takes remaining width
    ]
    total_fixed = sum(w for _, w in cols if w is not None)
    cols[-1] = (cols[-1][0], grid_w - total_fixed)

    row_h  = int(19 * scale)
    hdr_h  = int(22 * scale)
    hf     = _font(6.5, bold=True)
    cf     = _font(6.5)
    sf     = _font(5.5)

    y = y_start

    # Section heading
    draw.rectangle([margin, y, margin + int(4 * scale), y + int(14 * scale)],
                   fill=TEAL)
    hf2 = _font(8, bold=True)
    draw.text((margin + int(8 * scale), y),
              "SESSION DATA GRID", fill=NAVY, font=hf2)
    y += int(18 * scale)

    # Column headers
    draw.rectangle([margin, y, margin + grid_w, y + hdr_h], fill=NAVY)
    cx = margin
    for col_label, col_w in cols:
        tw, th = _sz(draw, col_label, hf)
        draw.text((cx + (col_w - tw) // 2, y + (hdr_h - th) // 2),
                  col_label, fill=WHITE, font=hf)
        cx += col_w
    y += hdr_h

    # Draw vertical separator line position list
    def col_x_list():
        xs = [margin]
        for _, w in cols:
            xs.append(xs[-1] + w)
        return xs

    xs = col_x_list()

    for i, (num, day, activity) in enumerate(sessions or SESSIONS):
        row_bg = TEAL_LT if i % 2 == 0 else WHITE
        draw.rectangle([margin, y, margin + grid_w, y + row_h], fill=row_bg)

        # Vertical lines
        for x_sep in xs[1:-1]:
            draw.line([x_sep, y, x_sep, y + row_h],
                      fill=MID_GRAY, width=int(1 * scale))

        # Session number
        cx = xs[0]
        tw, th = _sz(draw, num, cf)
        draw.text((cx + (cols[0][1] - tw) // 2, y + (row_h - th) // 2),
                  num, fill=NAVY, font=_font(7, bold=True))

        # Day
        dw, dh = _sz(draw, day, sf)
        draw.text((xs[1] + int(3 * scale), y + (row_h - dh) // 2),
                  day, fill=NAVY, font=sf)

        # Activity
        aw, ah = _sz(draw, activity, sf)
        draw.text((xs[2] + int(3 * scale), y + (row_h - ah) // 2),
                  activity, fill=NAVY, font=sf)

        # Correct/Total — two tiny boxes side by side, sized to fit the column
        box_sz = int(10 * scale)
        gap_slash = int(4 * scale)
        bx = xs[3] + (cols[3][1] - 2 * box_sz - gap_slash) // 2
        by = y + (row_h - box_sz) // 2
        _box(draw, [bx, by, bx + box_sz, by + box_sz],
             fill=WHITE, outline=MID_GRAY, width=int(1 * scale))
        slash_x = bx + box_sz
        slash_w, _ = _sz(draw, "/", sf)
        draw.text((slash_x + (gap_slash - slash_w) // 2, y + (row_h - slash_w) // 2),
                  "/", fill=GRAY_TXT, font=sf)
        _box(draw, [bx + box_sz + gap_slash, by,
                    bx + box_sz + gap_slash + box_sz, by + box_sz],
             fill=WHITE, outline=MID_GRAY, width=int(1 * scale))

        # % column — blank write box
        pw2 = cols[4][1] - int(6 * scale)
        px = xs[4] + int(3 * scale)
        py = y + (row_h - int(12 * scale)) // 2
        _box(draw, [px, py, px + pw2, py + int(12 * scale)],
             fill=WHITE, outline=MID_GRAY, width=int(1 * scale))

        # Prompt level — circle options
        plabel_x = xs[5] + int(3 * scale)
        cir_r    = int(4 * scale)
        cir_y    = y + row_h // 2
        for j, pl in enumerate(PROMPT_LEVELS[:4]):   # I G V M on row; P FP small
            cx2 = plabel_x + j * int(8 * scale)
            draw.ellipse([cx2, cir_y - cir_r, cx2 + cir_r * 2, cir_y + cir_r],
                         outline=MID_GRAY, fill=WHITE, width=int(1 * scale))
            lw2, lh2 = _sz(draw, pl, sf)
            draw.text((cx2 + cir_r - lw2 // 2, cir_y - lh2 // 2),
                      pl, fill=GRAY_TXT, font=sf)

        # Modality — small letter boxes W A S G NR
        mx = xs[6] + int(2 * scale)
        bsz2 = int(10 * scale)
        my = y + (row_h - bsz2) // 2
        for j, ml in enumerate(["W", "A", "S", "G"]):
            _box(draw, [mx, my, mx + bsz2, my + bsz2],
                 fill=WHITE, outline=MID_GRAY, width=int(1 * scale))
            tw2, th2 = _sz(draw, ml, sf)
            draw.text((mx + (bsz2 - tw2) // 2, my + (bsz2 - th2) // 2),
                      ml, fill=GRAY_TXT, font=sf)
            mx += bsz2 + int(2 * scale)
        # total Mode width used: 4*bsz2 + 3*2 = 46 units <= 50 col width

        y += row_h

    # Bottom border
    draw.line([margin, y, margin + grid_w, y], fill=NAVY, width=int(1 * scale))

    # Key below grid
    y += int(6 * scale)
    key_f = _font(5.5)
    draw.text((margin, y), "Prompt key: " + PROMPT_KEY, fill=GRAY_TXT, font=key_f)
    y += int(10 * scale)
    draw.text((margin, y), "Modality key: " + MODALITY_KEY, fill=GRAY_TXT, font=key_f)
    return y + int(10 * scale)


def _progress_graph(page, draw, scale, y_start):
    """
    10-point % progress graph — teacher plots a dot per session.
    Y axis: 0–100% in 20% increments. X axis: 10 sessions.
    A horizontal goal line at 80% (editable convention).
    """
    margin = int(28 * scale)
    grid_w = PW - margin * 2
    graph_h = int(70 * scale)

    y = y_start

    # Section heading
    draw.rectangle([margin, y, margin + int(4 * scale), y + int(14 * scale)],
                   fill=TEAL)
    hf = _font(8, bold=True)
    draw.text((margin + int(8 * scale), y), "PROGRESS GRAPH", fill=NAVY, font=hf)
    y += int(18 * scale)

    axis_f = _font(6)
    left_axis = margin + int(24 * scale)
    graph_x   = left_axis + int(4 * scale)
    graph_end = margin + grid_w
    graph_w   = graph_end - graph_x

    # Y axis labels + horizontal grid lines (0, 20, 40, 60, 80, 100)
    step_h = graph_h / 5
    for i, pct in enumerate([100, 80, 60, 40, 20, 0]):
        gy = y + int(i * step_h)
        draw.line([graph_x, gy, graph_end, gy],
                  fill=(235, 235, 235), width=int(1 * scale))
        lbl = f"{pct}%"
        lw, lh = _sz(draw, lbl, axis_f)
        draw.text((left_axis - lw - int(2 * scale), gy - lh // 2),
                  lbl, fill=GRAY_TXT, font=axis_f)

    # 80% goal line (dashed approximation)
    goal_y = y + int(1 * step_h)
    segment = int(6 * scale)
    gx = graph_x
    while gx < graph_end:
        draw.line([gx, goal_y, min(gx + segment, graph_end), goal_y],
                  fill=RED_DOT, width=int(1 * scale))
        gx += segment * 2
    gl_f = _font(5.5, bold=True)
    glw, glh = _sz(draw, "Goal", gl_f)
    # Label inside the graph area, just above the goal line at the right edge —
    # previously drawn past the right margin.
    draw.text((graph_end - glw - int(4 * scale), goal_y - glh - int(3 * scale)),
              "Goal", fill=RED_DOT, font=gl_f)

    # X axis: 10 session columns with dot circles
    col_w2 = graph_w / 10
    for i in range(10):
        cx2 = int(graph_x + i * col_w2 + col_w2 / 2)
        # Dot circle for teacher to plot
        r = int(5 * scale)
        draw.ellipse([cx2 - r, y + graph_h - r, cx2 + r, y + graph_h + r],
                     outline=MID_GRAY, fill=WHITE, width=int(1 * scale))
        # Session number below
        lbl = str(i + 1)
        lw2, lh2 = _sz(draw, lbl, axis_f)
        draw.text((cx2 - lw2 // 2, y + graph_h + r + int(2 * scale)),
                  lbl, fill=GRAY_TXT, font=axis_f)

    # Outer graph border
    draw.rectangle([graph_x, y, graph_end, y + graph_h],
                   outline=MID_GRAY, width=int(1 * scale))

    note_f = _font(6)
    # Session numbers sit below the axis at graph_h + r + 2*scale and need
    # ~r + 2 + ~6 units — start the note below them, not at +16.
    ny = y + graph_h + int(5 * scale) + int(2 * scale) + int(14 * scale)
    draw.text((margin, ny),
              "Plot accuracy % for each session. Connect dots to show trend. "
              "Dashed red line = 80% mastery goal (adjust to IEP criterion).",
              fill=GRAY_TXT, font=note_f)

    return ny + int(14 * scale)


def _summary_section(page, draw, scale, y_start):
    """
    Post-fortnightly review section: instructional decision tick boxes
    + signature/date + parent communication checkbox.
    """
    margin = int(28 * scale)
    grid_w = PW - margin * 2
    y = y_start

    # Section heading
    draw.rectangle([margin, y, margin + int(4 * scale), y + int(14 * scale)],
                   fill=GOLD)
    hf = _font(8, bold=True)
    draw.text((margin + int(8 * scale), y),
              "END-OF-FORTNIGHT REVIEW & INSTRUCTIONAL DECISIONS", fill=NAVY, font=hf)
    y += int(20 * scale)

    # Two columns
    col_w2 = (grid_w - int(16 * scale)) // 2
    f = _font(7)
    tick_sz = int(12 * scale)

    decisions_l = [
        "Maintain: continue at current level",
        "Increase difficulty: move to harder level",
        "Change activity: not engaging / not appropriate",
        "Reduce prompting: student showing independence",
    ]
    decisions_r = [
        "Review IEP goal: criterion not achievable",
        "Refer to speech pathologist / OT",
        "Share data with family / carer",
        "Student met goal — update IEP",
    ]

    for i, (dl, dr) in enumerate(zip(decisions_l, decisions_r)):
        ry = y + i * int(18 * scale)
        # Left
        draw.rectangle([margin, ry, margin + tick_sz, ry + tick_sz],
                       fill=WHITE, outline=MID_GRAY, width=int(1 * scale))
        tw2, th2 = _sz(draw, dl, f)
        draw.text((margin + tick_sz + int(6 * scale), ry + (tick_sz - th2) // 2),
                  dl, fill=NAVY, font=f)
        # Right
        rx = margin + col_w2 + int(16 * scale)
        draw.rectangle([rx, ry, rx + tick_sz, ry + tick_sz],
                       fill=WHITE, outline=MID_GRAY, width=int(1 * scale))
        draw.text((rx + tick_sz + int(6 * scale), ry + (tick_sz - th2) // 2),
                  dr, fill=NAVY, font=f)

    y += 4 * int(18 * scale) + int(12 * scale)

    # Observations / next steps box
    obs_h = int(32 * scale)
    draw.rectangle([margin, y, margin + grid_w, y + obs_h],
                   fill=GRAY_BG, outline=MID_GRAY, width=int(1 * scale))
    draw.text((margin + int(6 * scale), y + int(4 * scale)),
              "Next steps / adjustments to instruction:", fill=NAVY, font=f)
    y += obs_h + int(10 * scale)

    # Signatures
    sig_w = (grid_w - int(20 * scale)) // 3
    for i, lbl in enumerate(["Teacher signature:", "Date:", "Parent / carer informed:"]):
        sx = margin + i * (sig_w + int(10 * scale))
        draw.text((sx, y), lbl, fill=NAVY, font=f)
        lw2, lh = _sz(draw, lbl, f)
        draw.line([sx, y + lh + int(4 * scale), sx + sig_w, y + lh + int(4 * scale)],
                  fill=MID_GRAY, width=int(1 * scale))

    return y + int(24 * scale)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def generate_iep_monitoring_form(
    slug: str,
    book_title: str,
    pack_code: str,
    output_dir: str = "OUTPUT",
    sessions=None,
) -> bool:
    scale = DPI / 72
    page  = Image.new("RGB", (PW, PH), WHITE)
    draw  = ImageDraw.Draw(page)

    # Resolve hero icon from theme assets
    hero_img = None
    try:
        theme_dir = Path("assets/themes") / slug
        for hp in [theme_dir / "hero.png", theme_dir / "hero_header.png"]:
            if hp.exists():
                im = Image.open(hp)
                hero_img = im.convert("RGBA") if im.mode != "RGBA" else im
                break
    except Exception:
        pass

    # Apply the standard SWS frame (accent strip, border, footer, hero)
    apply_small_wins_frame(
        page,
        product_title="IEP Progress Monitoring",
        subtitle=f"{book_title}",
        pack_code=pack_code,
        page_num=1,
        total_pages=1,
        level=None,
        draw_footer=True,
        draw_pcs_line=True,
        draw_subtitle=True,
        header_left_icon=hero_img,
        footer_compact=False,
    )

    # Subtle right-panel tint (within border, below accent strip, above footer)
    # Do NOT cover the footer area — stop well above the footer y position
    border_inset = int(26 * scale)
    accent_bottom = int(1.33 * DPI)  # accent strip ends at ~1.33"
    footer_top = int(9.5 * DPI)     # footer starts at ~9.5"
    draw.rectangle([int(PW * 0.62), accent_bottom, PW - border_inset, footer_top], fill=(250, 253, 252))

    y = _header(page, draw, book_title, pack_code, scale)
    y = _data_grid(page, draw, scale, y, sessions=sessions)
    y = _progress_graph(page, draw, scale, y)
    y = _summary_section(page, draw, scale, y)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / f"{pack_code}_IEP_MonitoringForm.pdf"

    buf = io.BytesIO()
    page.save(buf, format="PNG", dpi=(DPI, DPI))
    buf.seek(0)

    from reportlab.lib.pagesizes import letter as _LETTER
    c = rl_canvas.Canvas(str(out_path), pagesize=_LETTER)
    c.drawImage(ImageReader(buf), 0, 0, width=_LETTER[0], height=_LETTER[1])
    c.save()

    print(f"OK  {out_path}")
    return True


if __name__ == "__main__":
    _slug  = sys.argv[1] if len(sys.argv) > 1 else "stellaluna"
    _title = sys.argv[2] if len(sys.argv) > 2 else "Stellaluna"
    _code  = sys.argv[3] if len(sys.argv) > 3 else "STEL-01"
    generate_iep_monitoring_form(_slug, _title, _code)
