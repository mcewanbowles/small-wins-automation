"""Generate example support docs for LLB01 and zip them for review."""
import sys, os, io, json, zipfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from utils.sws_design import (
    generate_teacher_cover_page, DPI, apply_small_wins_frame,
    _brand_font_pt, hex_to_rgb, NAVY_HEX, DEFAULT_ACCENT_TEAL_HEX,
)

SLUG = "llama_llama_back_to_school"
PACK_CODE = "LLB01"
THEME_NAME = "Llama Llama Back to School"
THEME_DIR = Path("assets/themes") / SLUG
OUT_DIR = THEME_DIR / "OUTPUT"
TMP_DIR = Path("_support_docs_review")
TMP_DIR.mkdir(exist_ok=True)

# ── 1. Copy Terms of Use ──
tou_src = Path("assets/global/tpt_support_docs/Terms of Use.pdf")
tou_dst = TMP_DIR / "Terms of Use.pdf"
shutil.copy2(str(tou_src), str(tou_dst))
print("1. Terms of Use.pdf")

# ── 2. Generate sample TPT descriptions for key products ──
import importlib
app = importlib.import_module("studioforge_app")

products_to_demo = [
    ("Yes/No Questions", "Yes/No Questions", 8),
    ("AAC Board", "AAC Communication Board", 1),
    ("Matching", "Matching Cards", 19),
    ("Bingo", "Differentiated Bingo", 18),
    ("Sequencing", "Story Sequencing", 3),
]

desc_dir = TMP_DIR / "TPT_Descriptions"
desc_dir.mkdir(exist_ok=True)
for name, display, pages in products_to_demo:
    app.write_product_support_docs(desc_dir, PACK_CODE, name, display, pages)
    print(f"2. TPT description: {name}")

# ── 3. Generate sample listing template with ALL products ──
built = ["Matching", "Find & Cover", "AAC Sentence Building", "Book Participation Pieces",
         "Sorting Cards", "Bingo", "AAC Board", "Word Search", "Yes/No Questions",
         "Sequencing", "Vocabulary Snap", "Syllable Awareness", "Adapted Book",
         "Inferencing Cards", "Story Elements Mat", "Print Detective",
         "IEP Monitoring Form"]
listing = app.generate_listing_template(THEME_NAME, built, 180)
listing_path = TMP_DIR / "Listing_Template.json"
listing_path.write_text(json.dumps(listing, indent=2, ensure_ascii=False), encoding="utf-8")
print("3. Listing_Template.json")

listing_txt = TMP_DIR / "Listing_Template.txt"
lines = [
    f"TPT Title: {listing['tpt_title']}",
    "",
    "Description:",
    listing["description"],
    "",
    f"Bullets ({len(listing['bullets'])} total):",
]
for b in listing["bullets"]:
    lines.append(f"  - {b}")
listing_txt.write_text("\n".join(lines), encoding="utf-8")
print("3b. Listing_Template.txt")

# ── 4. Generate sample teacher cover pages ──
cover_dir = TMP_DIR / "Teacher_Covers"
cover_dir.mkdir(exist_ok=True)

# Yes/No cover
yn_cover = generate_teacher_cover_page(
    theme_name=THEME_NAME,
    pack_code=PACK_CODE,
    product_name="Yes/No Questions",
    page_count=8,
    whats_included=[
        "Yes/No question cards with Boardmaker PCS symbols",
        "Cut-out YES/NO tokens for velcro or pointing",
        "Pointing & eye-gaze desk strip (2-choice and 3-choice with I don't know)",
        "Storage labels for organizing pieces",
        "Full color and black & white versions",
    ],
    also_included=["Quick Start Guide", "Terms of Use", "IEP Monitoring Form (bonus inclusion)"],
    rope_strand="Language Structures",
    rope_skills="Question Answering · AAC Expression",
    draw_footer=True,
)
buf = io.BytesIO()
yn_cover.save(buf, format="PNG", dpi=(DPI, DPI))
buf.seek(0)
c = canvas.Canvas(str(cover_dir / "LLB01_YesNo_Cover.pdf"), pagesize=letter)
c.drawImage(ImageReader(buf), 0, 0, width=letter[0], height=letter[1])
c.showPage(); c.save()
print("4a. Teacher cover: Yes/No Questions")

# AAC Board cover
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
buf = io.BytesIO()
aac_cover.save(buf, format="PNG", dpi=(DPI, DPI))
buf.seek(0)
c = canvas.Canvas(str(cover_dir / "LLB01_AACBoard_Cover.pdf"), pagesize=letter)
c.drawImage(ImageReader(buf), 0, 0, width=letter[0], height=letter[1])
c.showPage(); c.save()
print("4b. Teacher cover: AAC Board")

# ── 5. Write product bullets reference ──
bullets_ref = TMP_DIR / "Product_Bullets_Reference.txt"
product_bullets = {
    "Book Participation Pieces": ["Read-aloud companion", "Velcro-friendly pieces", "Storage mat + labels", "Color + black & white"],
    "Matching": ["4 differentiated levels", "Storage labels included", "Color + black & white"],
    "Find & Cover": ["3 differentiated levels", "Storage labels included", "Color + black & white"],
    "Word Search": ["Vocabulary practice", "4 differentiated grids", "Preview included"],
    "AAC Sentence Building": ["Sentence building strips", "Core + book vocabulary", "Storage labels included", "Color + black & white"],
    "AAC Board": ["Core + book vocabulary", "4 variants: color, BW, hi-vis black, hi-vis yellow", "Board-only PDF (cover separate)"],
    "Sequencing": ["Story sequencing strips", "Cut-out picture cards", "Storage labels included", "Color + black & white"],
    "Sorting Cards": ["Guided + open sorts", "Interchangeable headers", "Storage labels included", "Color + black & white"],
    "Bingo": ["4 differentiated levels", "Calling cards included", "Storage labels included", "Color + black & white"],
    "Yes/No Questions": ["Yes/No question cards", "Cut-out tokens + desk strip", "2-choice and 3-choice (I don't know) strips", "Storage labels included", "Color + black & white"],
    "Inferencing Cards": ["Clue-based reasoning cards", "Discussion guide", "Color + black & white"],
    "Vocabulary Snap": ["Symbol+text, symbol-only, text-only decks", "Extra copy cards included", "Storage labels included", "Color + black & white"],
    "Syllable Awareness": ["Syllable segmentation cards", "2x2 grid layout", "Storage labels included", "Color + black & white"],
    "Story Elements Mat": ["Story element cards", "Retell framework", "Color + black & white"],
    "Print Detective": ["4 print-concepts levels", "Letter/word sorting", "Color + black & white"],
    "Adapted Book": ["Adapted book with Velcro pieces", "Storage label included", "Color + black & white"],
    "IEP Monitoring Form": ["Progress tracking form", "IEP goal data sheet", "Bonus inclusion in bundle"],
}
lines = ["Product Cover Bullets Reference", "=" * 50, ""]
for name, bullets in product_bullets.items():
    lines.append(f"{name}:")
    for b in bullets:
        lines.append(f"  - {b}")
    lines.append("")
bullets_ref.write_text("\n".join(lines), encoding="utf-8")
print("5. Product_Bullets_Reference.txt")

# ── 6. Write a summary README ──
readme = TMP_DIR / "README.txt"
readme.write_text("""Small Wins Studio - Support Docs Review Package (v2)
====================================================

Theme: Llama Llama Back to School (LLB01)
Generated for Claude review - all issues from v1 addressed

Changes since v1:
  - ToU: PCS licensing language now acknowledges pending Tobii Dynavox confirmation
  - ToU: Added liability/warranty disclaimer
  - ToU: "All sales are final" replaced with TPT platform policy reference
  - ToU: Content shortened to prevent footer overlap
  - ToU: IEP Monitoring Form now says "bonus inclusion" (not "sold separately")
  - Product descriptions: now product-specific (not placeholder text)
  - Product descriptions: "1 printable pages" grammar fixed (page/pages)
  - Listing template: all 19 products now have bullets (was 6)
  - Listing template: total pages corrected to 180 (was 120)
  - Listing template: Find & Cover page count fixed (40, was 15)
  - Listing template: AAC Sentence Building page count fixed (8, was 6)
  - Vocabulary Snap bullet: "Word Wall banner" replaced with "Extra copy cards"
  - Teacher covers: blank hero rectangle now falls back to Small Wins logo
  - IEP Monitoring Form: consistently described as "bonus inclusion" everywhere

Contents:
  Terms of Use.pdf              - Branded TOU with PCS licensing, disclaimer
  README.txt                    - This file

  TPT_Descriptions/             - Sample TPT product descriptions (product-specific)
    LLB01_Yes-No_Questions_TPT_Description.txt
    LLB01_AAC_Board_TPT_Description.txt
    LLB01_Matching_TPT_Description.txt
    LLB01_Bingo_TPT_Description.txt
    LLB01_Sequencing_TPT_Description.txt

  Listing_Template.json         - TPT listing template (title, description, 19 bullets)
  Listing_Template.txt          - Human-readable version of the listing template

  Teacher_Covers/               - Sample teacher cover pages (PDF)
    LLB01_YesNo_Cover.pdf       - Yes/No Questions cover with desk strip features
    LLB01_AACBoard_Cover.pdf    - AAC Board cover with hi-vis variants

  Product_Bullets_Reference.txt - All 20 product cover bullets in one reference

Review Questions for Claude:
  1. Are the Terms of Use clear and legally sound for a TPT seller?
  2. Are the product descriptions accurate and compelling?
  3. Is the listing template optimized for TPT search?
  4. Are the teacher cover pages consistent and professional?
  5. Do the product bullets accurately reflect each product's features?
  6. Is the PCS licensing language correct and transparent?
  7. Are there any inconsistencies across the docs?
""", encoding="utf-8")
print("6. README.txt")

# ── 7. Create the ZIP ──
zip_path = Path("_support_docs_review.zip")
if zip_path.exists():
    zip_path.unlink()

with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(str(TMP_DIR)):
        for f in files:
            fp = Path(root) / f
            arcname = fp.relative_to(TMP_DIR)
            zf.write(str(fp), str(arcname))

print(f"\nZIP created: {zip_path} ({zip_path.stat().st_size:,} bytes)")

with zipfile.ZipFile(str(zip_path), "r") as zf:
    print(f"\nContents ({len(zf.namelist())} files):")
    for name in sorted(zf.namelist()):
        info = zf.getinfo(name)
        print(f"  {name:50s} {info.file_size:>8,} bytes")
