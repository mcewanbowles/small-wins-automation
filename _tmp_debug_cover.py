import sys, os
sys.path.insert(0, '.')
os.chdir('.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Monkey-patch to capture layout dimensions
import utils.sws_design as sws

# Save original function
_orig = sws.generate_teacher_cover_page

def debug_cover(*args, **kwargs):
    # Call original but intercept the internal state by patching _text_size
    orig_ts = sws._text_size
    dims = {}
    def ts(draw, text, font):
        r = orig_ts(draw, text, font)
        if 'Scarborough' in text or 'Strand:' in text or 'AAC Expression' in text or 'Language Structures' in text:
            print(f"  TEXT: {text!r} -> size={r}")
        return r
    sws._text_size = ts
    result = _orig(*args, **kwargs)
    sws._text_size = orig_ts
    return result

sws.generate_teacher_cover_page = debug_cover

from PIL import Image

SLUG = "llama_llama_back_to_school"
PACK_CODE = "LLB01"
THEME_NAME = "Llama Llama Back to School"

print("=== Yes/No Cover ===")
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
    rope_skills="Comprehension · Question Answering · AAC Expression",
    draw_footer=True,
)

print("\n=== AAC Board Cover ===")
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
