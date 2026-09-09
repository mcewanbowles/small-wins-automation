"""Shared SWS brand font registration for ReportLab generators.

Pattern (matches Dignity):
  Poppins (primary) -> Comic Sans (fallback) -> Helvetica (last resort)

Usage:
    from utils.sws_fonts import BRAND_FONT_REGULAR, BRAND_FONT_BOLD, sws_font

    c.setFont(sws_font(bold=True), 14)
    c.setFont(sws_font(), 10)

Or import the constants directly:
    from utils.sws_fonts import BRAND_FONT_REGULAR as FONT_REGULAR
    from utils.sws_fonts import BRAND_FONT_BOLD as FONT_BOLD
"""
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Last-resort defaults (built into ReportLab)
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

_BRAND_FONT_REGULAR = None
_BRAND_FONT_BOLD = None

# Repo root (parents[1] from utils/)
_REPO_ROOT = Path(__file__).resolve().parents[1]

def _register():
    """Register Poppins -> Comic Sans -> Helvetica fallback chain. Idempotent."""
    global _BRAND_FONT_REGULAR, _BRAND_FONT_BOLD

    if _BRAND_FONT_REGULAR and _BRAND_FONT_BOLD:
        return  # already registered

    # Poppins (primary) — repo-root fonts/ folder
    _poppins_reg_paths = [
        _REPO_ROOT / "fonts" / "Poppins-Regular.ttf",
        _REPO_ROOT / "fonts" / "Poppins-Medium.ttf",
    ]
    _poppins_bold_paths = [
        _REPO_ROOT / "fonts" / "Poppins-Bold.ttf",
        _REPO_ROOT / "fonts" / "Poppins-SemiBold.ttf",
    ]
    _reg_path = next((p for p in _poppins_reg_paths if p.exists()), None)
    _bold_path = next((p for p in _poppins_bold_paths if p.exists()), None)
    if _reg_path:
        try:
            pdfmetrics.registerFont(TTFont("Poppins", str(_reg_path)))
            _BRAND_FONT_REGULAR = "Poppins"
        except Exception:
            pass
    if _bold_path:
        try:
            pdfmetrics.registerFont(TTFont("Poppins-Bold", str(_bold_path)))
            _BRAND_FONT_BOLD = "Poppins-Bold"
        except Exception:
            pass

    # Comic Sans (fallback) — standard for TPT SPED, available on Windows
    if not _BRAND_FONT_REGULAR:
        _comic_reg = Path("C:/Windows/Fonts/comic.ttf")
        if _comic_reg.exists():
            try:
                pdfmetrics.registerFont(TTFont("ComicSansMS", str(_comic_reg)))
                _BRAND_FONT_REGULAR = "ComicSansMS"
            except Exception:
                pass
    if not _BRAND_FONT_BOLD:
        _comic_bold = Path("C:/Windows/Fonts/comicbd.ttf")
        if _comic_bold.exists():
            try:
                pdfmetrics.registerFont(TTFont("ComicSansMS-Bold", str(_comic_bold)))
                _BRAND_FONT_BOLD = "ComicSansMS-Bold"
            except Exception:
                pass

    # If we have regular but not bold, use regular for both
    if _BRAND_FONT_REGULAR and not _BRAND_FONT_BOLD:
        _BRAND_FONT_BOLD = _BRAND_FONT_REGULAR

    # Final fallback to Helvetica
    if not _BRAND_FONT_REGULAR:
        _BRAND_FONT_REGULAR = FONT_REGULAR
    if not _BRAND_FONT_BOLD:
        _BRAND_FONT_BOLD = FONT_BOLD


_register()

BRAND_FONT_REGULAR = _BRAND_FONT_REGULAR
BRAND_FONT_BOLD = _BRAND_FONT_BOLD


def sws_font(bold: bool = False) -> str:
    """Return the SWS brand font name for ReportLab setFont() calls."""
    return BRAND_FONT_BOLD if bold else BRAND_FONT_REGULAR
