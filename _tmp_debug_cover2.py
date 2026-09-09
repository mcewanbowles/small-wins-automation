import sys, os
sys.path.insert(0, '.')
os.chdir('.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from PIL import Image, ImageDraw

# Patch ImageDraw.Draw.text to log positions
_orig_text = ImageDraw.ImageDraw.text
_logged_texts = []
def _patched_text(self, xy, text, **kwargs):
    if any(k in str(text) for k in ['Scarborough', 'Strand:', 'AAC Expression', 'Language Structures (this pack)', 'Comprehension', 'Question Answering', 'Word Recognition']):
        _logged_texts.append((text, xy))
    return _orig_text(self, xy, text, **kwargs)
ImageDraw.ImageDraw.text = _patched_text

# Patch page.paste to detect rope image paste
_orig_paste = Image.Image.paste
def _patched_paste(self, im, box=None, mask=None):
    if hasattr(im, 'size') and im.size[0] > 100 and im.size[1] > 50:
        _logged_texts.append((f'[PASTE image {im.size}]', box if isinstance(box, tuple) else (0,0)))
    return _orig_paste(self, im, box, mask)
Image.Image.paste = _patched_paste

import utils.sws_design as sws

SLUG = "llama_llama_back_to_school"
PACK_CODE = "LLB01"
THEME_NAME = "Llama Llama Back to School"

print("=== Yes/No Cover ===")
_logged_texts.clear()
yn_cover = sws.generate_teacher_cover_page(
    theme_name=THEME_NAME,
    pack_code=PACK_CODE,
    product_name="Yes/No Questions",
    page_count=8,
    whats_included=[
        "Yes/No question cards with Boardmaker PCS symbols",
        "Cut-out YES/NO tokens for velcro or pointing",
        "Pointing & eye-gaze desk strip (2-choice and 3-choice)",
        "3-choice strip includes I DON'T KNOW for differentiation",
        "Storage labels for organizing pieces",
        "Full color and black & white versions",
    ],
    also_included=["Quick Start Guide", "Terms of Use", "IEP Monitoring Form (bonus inclusion)"],
    rope_strand="Language Structures",
    rope_skills="Question Answering · AAC Expression",
    draw_footer=True,
)
for text, xy in _logged_texts:
    if any(k in str(text) for k in ['Scarborough', 'Strand:', 'AAC Expression', 'Language Structures (this pack)', 'Comprehension', 'Question Answering', 'Word Recognition', 'PASTE']):
        print(f"  y={xy[1]:5d}  x={xy[0]:5d}  {text}")

print("\n=== AAC Board Cover ===")
_logged_texts.clear()
aac_cover = sws.generate_teacher_cover_page(
    theme_name=THEME_NAME,
    pack_code=PACK_CODE,
    product_name="AAC Communication Board",
    page_count=1,
    whats_included=[
        "6x6 BoardReady layout with core + book vocabulary",
        "4 variants: color, black & white, hi-vis black, hi-vis yellow",
        "Board-only PDF (cover is separate)",
        "Boardmaker PCS symbols throughout",
        "High-visibility variants for print accessibility",
    ],
    also_included=["Quick Start Guide", "Terms of Use", "IEP Monitoring Form (bonus inclusion)"],
    rope_strand="Language Structures",
    rope_skills="AAC · Core Vocabulary · Expressive Communication",
    draw_footer=True,
)
for text, xy in _logged_texts:
    if any(k in str(text) for k in ['Scarborough', 'Strand:', 'AAC Expression', 'Language Structures (this pack)', 'Comprehension', 'Question Answering', 'Word Recognition', 'PASTE']):
        print(f"  y={xy[1]:5d}  x={xy[0]:5d}  {text}")
