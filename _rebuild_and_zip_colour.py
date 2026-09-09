"""Rebuild all products and create a colour-only ZIP for final QA."""
import sys, os, importlib, zipfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pathlib import Path

SLUG = "llama_llama_back_to_school"
THEME_NAME = "Llama Llama Back to School"
PACK_CODE = "LLB01"
THEME_DIR = Path("assets/themes") / SLUG
ICONS_DIR = THEME_DIR / "activity_images"
OUT_DIR = THEME_DIR / "OUTPUT"

# All 17 enabled products (Word Wall + Decoding retired per QA decision)
products = [
    ("IEP Monitoring Form", "Studioforge._TRUTH.IEP_MONITORING", "generate_iep_monitoring_pack"),
    ("Adapted Book", "Studioforge._TRUTH.ADAPTED_BOOK", "generate_adapted_book_pack"),
    ("AAC Board", "Studioforge._TRUTH.AAC_BOARD", "generate_aac_board_pack"),
    ("Bingo", "Studioforge._TRUTH.BINGO", "generate_bingo_pack"),
    ("Sorting Cards", "Studioforge._TRUTH.SORTING", "generate_grounded_sorting_pack"),
    ("Sequencing", "Studioforge._TRUTH.SEQUENCING", "generate_grounded_sequence_pack"),
    ("Yes/No Questions", "Studioforge._TRUTH.YES_NO", "generate_yes_no_pack"),
    ("Vocabulary Snap", "Studioforge._TRUTH.VOCABULARY_SNAP", "generate_vocabulary_snap_pack"),
    ("Syllable Awareness", "Studioforge._TRUTH.SYLLABLE_AWARENESS", "generate_syllable_awareness_pack"),
    ("Matching", "Studioforge._TRUTH.MATCHING", "generate_matching_pack"),
    ("Find & Cover", "Studioforge._TRUTH.FIND_AND_COVER_GENERATOR", "generate_find_and_cover_pack"),
    ("AAC Sentence Building", "Studioforge._TRUTH.SENTENCE_BUILDING", "generate_sentence_building_pack"),
    ("Book Participation", "Studioforge._TRUTH.BOOK_PARTICIPATION", "generate_book_participation_pack"),
    ("Word Search", "Studioforge._TRUTH.WORD_SEARCH", "generate_word_search"),
    ("Inferencing Cards", "Studioforge._TRUTH.INFERENCING", "generate_inferencing_reasoning_pack"),
    ("Print Detective", "Studioforge._TRUTH.PRINT_DETECTIVE", "generate_print_detective_pack_wrapper"),
    ("Story Elements Mat", "Studioforge._TRUTH.STORY_ELEMENTS", "generate_story_elements_mat_pack"),
]

# ── Step 1: Rebuild all products ──
print("=" * 60)
print("REBUILDING ALL PRODUCTS")
print("=" * 60)
results = []
for name, module_path, func_name in products:
    print(f"\n--- {name} ---")
    try:
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        ok = func(str(ICONS_DIR), PACK_CODE, THEME_NAME)
        results.append((name, True, ""))
    except Exception as e:
        results.append((name, False, str(e)))
        import traceback
        traceback.print_exc()

print(f"\n{'=' * 60}")
print("BUILD SUMMARY")
print(f"{'=' * 60}")
for name, ok, err in results:
    status = "OK" if ok else "FAIL"
    print(f"  {status:4s}  {name}")
    if err:
        print(f"        Error: {err[:120]}")

failed = [r for r in results if not r[1]]
if failed:
    print(f"\n{len(failed)} product(s) failed. Check errors above.")

# ── Step 2: Collect colour-only PDFs into a ZIP ──
print(f"\n{'=' * 60}")
print("CREATING COLOUR-ONLY ZIP")
print(f"{'=' * 60}")

zip_path = Path("_LLB01_colour_only_qa.zip")
if zip_path.exists():
    zip_path.unlink()

# Collect all colour PDFs (including hi-vis variants and IEP)
colour_pdfs = []
for f in sorted(OUT_DIR.iterdir()):
    if not f.suffix == ".pdf":
        continue
    name = f.name
    # Include: _COLOR.pdf, _COLOR_HIGHVIS_*.pdf, IEP_MonitoringForm.pdf
    # Exclude: _BW.pdf, _PREVIEW.pdf, BuildResult.json, TPT_Description.txt
    if "_BW" in name or "_PREVIEW" in name:
        continue
    # Exclude retired products (Word Wall, Decoding)
    if "Decoding" in name or "WordWall" in name:
        continue
    if name.endswith("_COLOR.pdf") or "_COLOR_HIGHVIS_" in name or "IEP_MonitoringForm" in name:
        colour_pdfs.append(f)

# Also include Terms of Use
tou_path = Path("assets/global/tpt_support_docs/Terms of Use.pdf")
if tou_path.exists():
    colour_pdfs.append(tou_path)

# Also include teacher covers if they exist
cover_dir = Path("_support_docs_review/Teacher_Covers")
if cover_dir.exists():
    for f in sorted(cover_dir.iterdir()):
        if f.suffix == ".pdf":
            colour_pdfs.append(f)

with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
    for f in colour_pdfs:
        arcname = f.name
        zf.write(str(f), arcname)
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {arcname:50s} {size_mb:6.1f} MB")

total_mb = zip_path.stat().st_size / (1024 * 1024)
print(f"\nZIP created: {zip_path} ({total_mb:.1f} MB, {len(colour_pdfs)} files)")
