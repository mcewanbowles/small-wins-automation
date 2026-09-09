"""Rebuild all products affected by the QA fixes."""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# Fix Windows console encoding for emoji characters in print statements
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SLUG = "llama_llama_back_to_school"
THEME_NAME = "Llama Llama Back to School"
PACK_CODE = "LLB01"
THEME_DIR = os.path.join("assets", "themes", SLUG)
ICONS_DIR = os.path.join(THEME_DIR, "activity_images")

# Products to rebuild (affected by fixes)
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
]

results = []
for name, module_path, func_name in products:
    print(f"\n{'='*60}")
    print(f"Building: {name}")
    print(f"{'='*60}")
    try:
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        ok = func(ICONS_DIR, PACK_CODE, THEME_NAME)
        results.append((name, ok, ""))
    except Exception as e:
        results.append((name, False, str(e)))
        import traceback
        traceback.print_exc()

print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
for name, ok, err in results:
    status = "OK" if ok else "FAIL"
    print(f"  {status:4s}  {name}")
    if err:
        print(f"        Error: {err[:100]}")
