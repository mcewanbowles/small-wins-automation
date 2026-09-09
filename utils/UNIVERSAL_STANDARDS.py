from __future__ import annotations

"""
Universal design constants and helpers for all generators.
Single source of truth for colours, copyright, footer/header rules, and
label cleaning used across products.
"""

# Core brand (SWS confirmed palette)
SWS_TEAL    = "#31A8A0"
SWS_NAVY    = "#0D2545"
SWS_GOLD    = "#E1B42D"
SWS_TEAL_LT = "#E8F8F8"   # light teal background
MID_GRAY    = "#E5E7EB"
WHITE       = "#FFFFFF"
BLACK       = "#000000"

# Backward-compatible aliases used across existing generators
BRAND_TEAL = SWS_TEAL        # headers, borders, primary brand
BRAND_NAVY = SWS_NAVY        # body text
STEEL_BLUE = SWS_NAVY        # muted labels (remapped to brand navy)
PAGE_WHITE = "#FFFFFF"
CREAM = "#FFFDF7"            # adapted book body only
COPYRIGHT_YEAR = 2026         # NEVER 2025 — single source of truth

# Canonical PCS attribution — single source of truth.
# All generators MUST use this exact string (with ®).
# Format: copyright first, then PCS attribution.
PCS_ATTRIBUTION = (
    f"© {COPYRIGHT_YEAR} Small Wins Studio. "
    "PCS® symbols used with active PCS Maker Personal License"
)
PCS_ATTRIBUTION_FOOTER = (
    f"PCS® symbols used with active PCS Maker Personal License. | "
    f"© {COPYRIGHT_YEAR} Small Wins Studio"
)

# Level colours (mapped to Scarborough strands palette)
LEVEL_VIOLET  = "#7C3AED"   # Level 1
LEVEL_OCEAN   = "#0284C7"   # Level 2
LEVEL_EMERALD = "#059669"   # Level 3
LEVEL_ROSE    = "#E11D48"   # Level 4

# Canonical level mapping used by new generators
LEVEL_COLORS = {
    1: LEVEL_VIOLET,
    2: LEVEL_OCEAN,
    3: LEVEL_EMERALD,
    4: LEVEL_ROSE,
}

LEVEL_NAMES = {
    1: "Supported",
    2: "Developing",
    3: "Independent",
    4: "Extended",
}

# Backward-compatible level aliases expected by older generators
LEVEL_1_GREEN = LEVEL_VIOLET
LEVEL_2_BLUE  = LEVEL_OCEAN
LEVEL_3_AMBER = LEVEL_EMERALD
LEVEL_4_CORAL = LEVEL_ROSE

# Activity type colours (border when product has no levels)
COLOUR_LITERACY = SWS_TEAL       # Adapted Book, AAC Board, Sentence Strips,
                                 # Scarborough Rope, Worksheet
COLOUR_COMPREHENSION = SWS_NAVY  # Yes/No, Inferencing, Story Elements
COLOUR_GAMES = "#7F77DD"         # Matching, Bingo, Spin & Cover, Find & Cover
COLOUR_PHONOLOGICAL = "#1D9E75"  # Syllable Cards, Word Search
COLOUR_SEQUENCING = "#E07B00"    # Story Sequencing, Sorting Cards

# Border/header/footer rules (Step 5 spec)
BORDER_STROKE_PT = 5
BORDER_RADIUS_PT = 14
BORDER_INSET_PT = 26
FOOTER_BORDER_CLEARANCE = 10   # minimum clearance above inner border edge (pt)
LEVEL_BADGE_MIN_GAP_PT = 12
HEADER_ALWAYS_TEAL = True


def clean_label(label: str) -> str:
    """Strip trailing numeric disambiguators (e.g., 'Branch 2' -> 'Branch').
    Keep internal digits (e.g., 'Level 2') intact when not at the end.
    """
    import re
    if not isinstance(label, str):
        return ""
    s = label.strip()
    return re.sub(r"\s+\d+$", "", s)


# Scarborough strand mapping used across UI, listings, and PDF generators
# Format: code -> (list of strand names, tier: 'upper'|'lower'|'both'|'all')
STRAND_PILLS = {
    'AB': (['Background Knowledge', 'Literacy Knowledge'], 'upper'),
    'SL': (['All 8 strands'], 'all'),
    'AC': (['Vocabulary', 'Language Structures'], 'upper'),
    'SS': (['Language Structures', 'Vocabulary'], 'upper'),
    'SE': (['Literacy Knowledge', 'Background Knowledge'], 'upper'),
    'SQ': (['Literacy Knowledge', 'Verbal Reasoning'], 'upper'),
    'YN': (['Verbal Reasoning'], 'upper'),
    'IN': (['Verbal Reasoning'], 'upper'),
    'MT': (['Vocabulary'], 'upper'),
    'SR': (['Vocabulary', 'Verbal Reasoning'], 'upper'),
    'WK': (['Verbal Reasoning', 'Vocabulary'], 'upper'),
    'WS': (['Phonological Awareness', 'Decoding'], 'lower'),
    'SY': (['Phonological Awareness'], 'lower'),
    'FC': (['Sight Recognition'], 'lower'),
    'SC': (['Sight Recognition'], 'lower'),
    'BG': (['Sight Recognition', 'Vocabulary'], 'both'),
    'VW': (['Vocabulary'], 'upper'),
}

# Legacy alias — keep for backward compatibility during transition
COLORS = {
    "navy_blue":   SWS_NAVY,
    "teal":        SWS_TEAL,
    "gold":        SWS_GOLD,
    "light_gray":  MID_GRAY,
    "white":       WHITE,
    "black":       BLACK,
}

# Fonts and page border helpers
from PIL import ImageFont

def _first_font(paths: list[str], size: int):
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

def load_fonts(scale: float) -> dict:
    def fam(pt: float, *, bold=False):
        sz = max(1, int(pt * scale))
        win = [
            f"C:/Windows/Fonts/{'Poppins-Bold.ttf' if bold else 'Poppins-Regular.ttf'}",
            f"C:/Windows/Fonts/{'Nunito-Bold.ttf' if bold else 'Nunito-Regular.ttf'}",
            f"C:/Windows/Fonts/{'arialbd.ttf' if bold else 'arial.ttf'}",
        ]
        nix = [
            f"/usr/share/fonts/truetype/poppins/{'Poppins-Bold.ttf' if bold else 'Poppins-Regular.ttf'}",
            f"/usr/share/fonts/truetype/nunito/{'Nunito-Bold.ttf' if bold else 'Nunito-Regular.ttf'}",
            f"/usr/share/fonts/truetype/dejavu/{'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'}",
        ]
        return _first_font(win + nix, sz)

    return {
        # General
        "title":        fam(24, bold=True),
        "subtitle":     fam(16),
        "heading":      fam(18, bold=True),
        "body":         fam(12),
        "small":        fam(10),
        "footer":       fam(11),
        "copyright":    fam(7),
        # Common generator-specific keys
        "question":     fam(16, bold=True),
        "yes_no":       fam(28, bold=True),
        "cutout_label": fam(20, bold=True),
        "storage_title": fam(26, bold=True),
        "storage_label": fam(13, bold=True),
        "instruction":   fam(12),
        "cell":          fam(10, bold=True),
    }

def draw_page_border(draw, page_w: int, page_h: int, *, dpi: int = 300,
                     stroke_pt: float | None = None,
                     inset_pt: float | None = None,
                     radius_pt: float | None = None,
                     color: str | None = None,
                     fill: str | None = None) -> None:
    sp = stroke_pt if stroke_pt is not None else BORDER_STROKE_PT
    ip = inset_pt if inset_pt is not None else BORDER_INSET_PT
    rp = radius_pt if radius_pt is not None else BORDER_RADIUS_PT
    col = color or SWS_TEAL
    bg  = fill or "#EAF5F4"
    px = lambda pt: int(pt * dpi / 72)
    x0, y0 = px(ip), px(ip)
    x1, y1 = page_w - px(ip), page_h - px(ip)
    r = px(rp)
    w = max(1, px(sp))
    # Fill panel
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=bg)
    # Border stroke
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, outline=col, width=w)
