import sys, os, io
sys.path.insert(0, '.')
os.chdir('.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from utils.sws_design import generate_teacher_cover_page, DPI

SLUG = "llama_llama_back_to_school"
PACK_CODE = "LLB01"
THEME_NAME = "Llama Llama Back to School"

# Generate Yes/No cover
yn_cover = generate_teacher_cover_page(
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
yn_cover.save(r'_qa_yn_cover.png')
print(f"Yes/No cover saved: {yn_cover.size}")

# Generate AAC Board cover
aac_cover = generate_teacher_cover_page(
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
aac_cover.save(r'_qa_aac_cover.png')
print(f"AAC Board cover saved: {aac_cover.size}")

# Crop the rope card area from both (right column, lower portion)
for name, img in [("yn", yn_cover), ("aac", aac_cover)]:
    w, h = img.size
    # Right column starts at ~38% width, rope card is in lower portion
    crop = img.crop((int(w*0.38), int(h*0.45), w, int(h*0.85)))
    crop.save(f'_qa_{name}_rope.png')
    print(f"  {name} rope crop: {crop.size}")
