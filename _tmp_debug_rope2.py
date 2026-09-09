import sys, os
sys.path.insert(0, '.')
os.chdir('.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from PIL import Image, ImageDraw
from pathlib import Path

# Patch to capture rope image search and avail_h
_orig_paste = Image.Image.paste
_paste_log = []
def _patched_paste(self, im, box=None, mask=None):
    if hasattr(im, 'size') and im.size[0] > 50 and im.size[1] > 30:
        _paste_log.append((im.size, box))
    return _orig_paste(self, im, box, mask)
Image.Image.paste = _patched_paste

# Patch _draw_scarborough_rope to detect when braided fallback is used
import utils.sws_design as sws
_orig_draw_rope = sws._draw_scarborough_rope
_draw_log = []
def _patched_draw_rope(d, **kwargs):
    _draw_log.append(kwargs)
    return _orig_draw_rope(d, **kwargs)
sws._draw_scarborough_rope = _patched_draw_rope

# Patch Image.open to track rope image loading
_orig_open = Image.open
_open_log = []
def _patched_open(fp, *args, **kwargs):
    if 'rope' in str(fp).lower() or 'scarborough' in str(fp).lower():
        _open_log.append(str(fp))
    return _orig_open(fp, *args, **kwargs)
Image.open = _patched_open

SLUG = "llama_llama_back_to_school"
PACK_CODE = "LLB01"
THEME_NAME = "Llama Llama Back to School"

for name, bullets, skills in [
    ("Yes/No", [
        "Yes/No question cards with Boardmaker PCS symbols",
        "Cut-out YES/NO tokens for velcro or pointing",
        "Pointing & eye-gaze desk strip (2-choice and 3-choice)",
        "3-choice strip includes I DON'T KNOW for differentiation",
        "Storage labels for organizing pieces",
        "Full color and black & white versions",
    ], "Comprehension · Question Answering · AAC Expression"),
    ("AAC Board", [
        "6x6 BoardReady layout with core + book vocabulary",
        "4 variants: color, black & white, hi-vis black, hi-vis yellow",
        "Board-only PDF (cover is separate)",
        "Boardmaker PCS symbols throughout",
        "High-visibility variants for print accessibility",
    ], "AAC · Core Vocabulary · Expressive Communication"),
]:
    _paste_log.clear()
    _draw_log.clear()
    _open_log.clear()
    cover = sws.generate_teacher_cover_page(
        theme_name=THEME_NAME, pack_code=PACK_CODE,
        product_name=name, page_count=8 if name == "Yes/No" else 1,
        whats_included=bullets,
        also_included=["Quick Start Guide", "Terms of Use", "IEP Monitoring Form (bonus inclusion)"],
        rope_strand="Language Structures", rope_skills=skills,
        draw_footer=True,
    )
    print(f"\n{name}:")
    print(f"  Image opens: {_open_log}")
    print(f"  Pastes: {_paste_log}")
    if _draw_log:
        for dl in _draw_log:
            print(f"  Braided fallback: h={dl.get('h')}, w={dl.get('w')}")
