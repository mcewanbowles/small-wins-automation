import sys, os
sys.path.insert(0, '.')
os.chdir('.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from PIL import Image, ImageDraw

# Patch to capture avail_h and rope_img status
_orig_paste = Image.Image.paste
_paste_log = []
def _patched_paste(self, im, box=None, mask=None):
    if hasattr(im, 'size') and im.size[0] > 50 and im.size[1] > 30:
        _paste_log.append((im.size, box))
    return _orig_paste(self, im, box, mask)
Image.Image.paste = _patched_paste

import utils.sws_design as sws

SLUG = "llama_llama_back_to_school"
PACK_CODE = "LLB01"
THEME_NAME = "Llama Llama Back to School"

for name, bullets, skills in [
    ("Yes/No", [
        "Yes/No question cards with Boardmaker PCS symbols",
        "Cut-out YES/NO tokens for velcro or pointing",
        "Pointing & eye-gaze desk strip (2-choice and 3-choice with I don't know)",
        "Storage labels for organizing pieces",
        "Full color and black & white versions",
    ], "Question Answering · AAC Expression"),
    ("AAC Board", [
        "6x6 BoardReady layout with core + book vocabulary",
        "4 variants: color, black & white, hi-vis black, hi-vis yellow",
        "Board-only PDF (cover is separate)",
        "Boardmaker PCS symbols throughout",
        "High-visibility variants for print accessibility",
    ], "AAC · Core Vocabulary · Expressive Communication"),
]:
    _paste_log.clear()
    cover = sws.generate_teacher_cover_page(
        theme_name=THEME_NAME, pack_code=PACK_CODE,
        product_name=name, page_count=8 if name == "Yes/No" else 1,
        whats_included=bullets,
        also_included=["Quick Start Guide", "Terms of Use", "IEP Monitoring Form (bonus inclusion)"],
        rope_strand="Language Structures", rope_skills=skills,
        draw_footer=True,
    )
    print(f"\n{name}: paste_log = {_paste_log}")
