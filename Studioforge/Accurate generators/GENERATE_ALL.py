# SWS-GEN-VERSION: 2026-07-07 (see CHANGELOG.md in this pack for what changed)
"""
GENERATE ALL — Master Pack Runner
Small Wins Studio

Runs every generator for a given book slug in one command.
Produces complete OUTPUT/ folder ready for ZIP packaging.

Usage:
  python GENERATE_ALL.py stellaluna Stellaluna STEL
  python GENERATE_ALL.py stellaluna Stellaluna STEL --skip bingo spin
  python GENERATE_ALL.py stellaluna Stellaluna STEL --only matching word_search

Available keys (use with --skip or --only):
  Core activities:
    adapted, matching, find_cover, word_search, sentence, aac_board,
    sorting, bingo, spin, yes_no, sequencing, syllable, inferencing,
    scarborough, storage, word_wall, grammar_mat, phoneme, rhyme,
    wh_questions, iep_tracker

  Literacy extras:
    lesson_slides

  Support:
    cover, thumbnails, listing, zip_pack
"""

from __future__ import annotations
import sys
import time
import traceback
import re
from pathlib import Path
try:
    _repo_root = Path(__file__).resolve().parents[2]
    # Insert paths so that production/generators has highest precedence,
    # then Generators/, and ARCHIVE last. Using insert(0) means the last
    # item added wins precedence.
    _extra_paths = [
        _repo_root,                                      # lowest precedence
        _repo_root / "utils",
        _repo_root / "Generators" / "ARCHIVE generators",
        _repo_root / "Generators",
        _repo_root / "production" / "generators" / "generators",  # highest precedence
    ]
    for _p in _extra_paths:
        if _p.exists():
            _p_str = str(_p)
            if _p_str not in sys.path:
                sys.path.insert(0, _p_str)
except Exception:
    pass


# ── Product registry ──────────────────────────────────────────────────────────
# (key, display_name, pack_suffix, module, function)
PRODUCTS = [
    # ── Core activity generators ──────────────────────────────────────────────
    ("adapted",      "Adapted Book",              "ADPT",   "ADAPTED_BOOK_GENERATOR",      "build_pdf"),
    ("matching",     "Matching Cards",            "MATCH",  "MATCHING_GENERATOR",          "generate_matching_pack"),
    ("find_cover",   "Find & Cover",              "FAC",    "FIND_AND_COVER_GENERATOR",    "generate_find_and_cover_pack"),
    ("word_search",  "Word Search",               "WS",     "WORD_SEARCH_GENERATOR",       "generate_word_search"),
    ("sentence",     "AAC Sentence Strips",       "AAC",    "SENTENCE_STRIPS_AAC",         "generate_aac_pack"),
    ("aac_board",    "AAC Board",                  "BOARD",  "AAC_BOARD_GENERATOR",         "main"),
    ("sorting",      "Sorting Cards",             "SORT",   "SORTING_CARDS",               "generate_sorting_cards"),
    ("bingo",        "Bingo",                     "BINGO",  "BINGO_GENERATOR",             "generate_bingo_pack"),
    ("spin",         "Spin & Cover",              "SC",     "SPIN_COVER_GENERATOR",        "generate_spin_cover_pack"),
    ("yes_no",       "Yes/No Questions",          "YN",     "YES_NO_GENERATOR",            "generate_yes_no_pack"),
    ("sequencing",   "Sequencing Cards",          "SEQ",    "STORY_STRIPS_SEQUENCE",       "generate_story_strips"),
    ("syllable",     "Syllable Cards",            "SYL",    "SYLLABLE_CARDS",              "build_pdf"),
    ("inferencing",  "Inferencing Cards",         "INF",    "INFERENCING_CARDS",           "build_pdf"),
    ("scarborough",  "Scarborough Rope Insert",   "ROPE",   "SCARBOROUGH_ROPE_PAGE",       "build_pdf"),
    ("storage",      "Storage Labels",            "STOR",   "STORAGE_LABELS",              "generate_storage_labels"),
    # ── New literacy generators ───────────────────────────────────────────────
    ("word_wall",    "Vocabulary Word Wall",      "VWW",    "VOCAB_WORD_WALL",             "generate_word_wall"),
    ("grammar_mat",  "Story Grammar Mat",         "SGM",    "STORY_GRAMMAR_MAT",           "generate_story_grammar_mat"),
    ("phoneme",      "Phoneme Segmentation",      "PSM",    "PHONEME_SEGMENTATION_MATS",   "generate_phoneme_segmentation"),
    ("rhyme",        "Rhyme Cards",               "RHY",    "RHYME_CARDS",                 "generate_rhyme_cards"),
    ("wh_questions", "WH Questions",              "WH",     "WH_QUESTIONS_GENERATOR",      "generate_wh_questions"),
    ("iep_tracker",  "IEP Data Tracker",          "IEP",    "IEP_MONITORING_FORM",         "generate_iep_monitoring_form"),
    # ── Premium/advanced generators ───────────────────────────────────────────
    ("lesson_slides","Lesson Slides",             "SLIDES", "LESSON_SLIDES_GENERATOR",     "main"),
    # ── Support / post-processing ─────────────────────────────────────────────
    ("cover",        "Cover Pages",               "COV",    "COVER_GENERATOR_V2",          "generate_cover_page"),
    ("thumbnails",   "Thumbnails (raw QA raster — NOT branded TPT thumbnails)", "THUMB",  "THUMBNAILS_ALL",              "generate_thumbnails"),
    ("listing",      "TPT Listing Text",          "LIST",   "LISTING_GENERATOR",           "generate_listing"),
    ("zip_pack",     "Final ZIP Packages",        "ZIP",    "FINAL_ZIP_PACKAGER",          "package_book"),
]

# Products whose function signature is build_pdf(slug, book_title, pack_code)
BUILD_PDF_PRODUCTS = {"adapted", "syllable", "scarborough", "inferencing", "word_wall", "phoneme", "rhyme"}

# Products skipped by default (run with --all to include, or name explicitly)
# NOTE: "storage" is excluded here (not "advanced", just genuinely broken) —
# STORAGE_LABELS.py has no single generate_storage_labels() entry point, only
# per-product helpers (add_matching_storage_labels, add_aac_storage_labels, etc.)
# AND still uses the old pre-rebrand olive/tan palette. Needs a real fix, not a rename.
ADVANCED = {"lesson_slides", "cover", "thumbnails", "listing", "zip_pack", "storage"}

# Default run set — everything except advanced support tools
DEFAULT_KEYS = {p[0] for p in PRODUCTS} - ADVANCED


def _colour(text, code): return f"\033[{code}m{text}\033[0m"
def green(t):  return _colour(t, "32")
def red(t):    return _colour(t, "31")
def yellow(t): return _colour(t, "33")
def bold(t):   return _colour(t, "1")
def cyan(t):   return _colour(t, "36")


def run_generator(key, display_name, pack_suffix, module_name, func_name,
                  slug, book_title, base_code, images_folder) -> tuple[bool, float, str]:
    """Import module and call generator. Returns (success, elapsed, error)."""
    pack_code = f"{base_code}-{pack_suffix}"
    # If icons are sourced from another theme, tag outputs for generators
    # that consume a concrete images_folder (handled in the else-branch below).
    def _theme_from_images_path(p: Path) -> str | None:
        try:
            t = Path(p)
            prev = None
            for _ in range(8):
                if t.name == "themes" and prev is not None:
                    return prev.name
                if t.parent == t:
                    break
                prev = t
                t = t.parent
        except Exception:
            return None
        return None
    src_theme = _theme_from_images_path(Path(images_folder)) if images_folder else None
    fallback_tag = f"-FALLBACK-{src_theme.upper()}" if (src_theme and src_theme != slug) else ""
    t0 = time.time()
    try:
        import importlib
        import importlib.util
        if key == "iep_tracker":
            try:
                mod = importlib.import_module(module_name)
            except Exception:
                alt_path = Path(__file__).resolve().parents[1] / "Accurate generators" / "IEP_MONITORING_FORM.py"
                if alt_path.exists():
                    spec = importlib.util.spec_from_file_location("_SWS_IEP_MONITORING_FORM_ALT", str(alt_path))
                    if spec and spec.loader:
                        alt_mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(alt_mod)
                        mod = alt_mod
                    else:
                        raise
                else:
                    raise
        else:
            mod = importlib.import_module(module_name)
            if key == "matching":
                # Force Accurate generators version for Matching
                try:
                    acc_path = Path(__file__).resolve().parents[1] / "Accurate generators" / "MATCHING_GENERATOR.py"
                    if acc_path.exists():
                        spec = importlib.util.spec_from_file_location("_SWS_MATCHING_ACCURATE", str(acc_path))
                        if spec and spec.loader:
                            alt_mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(alt_mod)
                            mod = alt_mod
                except Exception:
                    pass
            elif key == "word_search":
                # Prefer Accurate Word Search (updated cover template)
                try:
                    acc_path = Path(__file__).resolve().parents[1] / "Accurate generators" / "WORD_SEARCH_GENERATOR.py"
                    if acc_path.exists():
                        spec = importlib.util.spec_from_file_location("_SWS_WORD_SEARCH_ACCURATE", str(acc_path))
                        if spec and spec.loader:
                            alt_mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(alt_mod)
                            mod = alt_mod
                except Exception:
                    pass
            elif key == "find_cover":
                # Prefer Accurate Find & Cover
                try:
                    acc_path = Path(__file__).resolve().parents[1] / "Accurate generators" / "FIND_AND_COVER_GENERATOR.py"
                    if acc_path.exists():
                        spec = importlib.util.spec_from_file_location("_SWS_FIND_COVER_ACCURATE", str(acc_path))
                        if spec and spec.loader:
                            alt_mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(alt_mod)
                            mod = alt_mod
                except Exception:
                    pass
            elif key == "yes_no":
                # Prefer Accurate Yes/No Questions
                try:
                    acc_path = Path(__file__).resolve().parents[1] / "Accurate generators" / "YES_NO_GENERATOR.py"
                    if acc_path.exists():
                        spec = importlib.util.spec_from_file_location("_SWS_YES_NO_ACCURATE", str(acc_path))
                        if spec and spec.loader:
                            alt_mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(alt_mod)
                            mod = alt_mod
                except Exception:
                    pass
            elif key == "sorting":
                # Prefer Accurate Sorting Cards
                try:
                    acc_path = Path(__file__).resolve().parents[1] / "Accurate generators" / "SORTING_CARDS.py"
                    if acc_path.exists():
                        spec = importlib.util.spec_from_file_location("_SWS_SORTING_ACCURATE", str(acc_path))
                        if spec and spec.loader:
                            alt_mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(alt_mod)
                            mod = alt_mod
                except Exception:
                    pass
            elif key == "sentence":
                # Prefer Accurate AAC Sentence Strips
                try:
                    acc_path = Path(__file__).resolve().parents[1] / "Accurate generators" / "SENTENCE_STRIPS_AAC.py"
                    if acc_path.exists():
                        spec = importlib.util.spec_from_file_location("_SWS_SENTENCE_ACCURATE", str(acc_path))
                        if spec and spec.loader:
                            alt_mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(alt_mod)
                            mod = alt_mod
                except Exception:
                    pass
            elif key == "syllable":
                # Prefer Accurate Syllable Cards
                try:
                    acc_path = Path(__file__).resolve().parents[1] / "Accurate generators" / "SYLLABLE_CARDS.py"
                    if acc_path.exists():
                        spec = importlib.util.spec_from_file_location("_SWS_SYLLABLE_ACCURATE", str(acc_path))
                        if spec and spec.loader:
                            alt_mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(alt_mod)
                            mod = alt_mod
                except Exception:
                    pass
            elif key == "inferencing":
                # Prefer Accurate Inferencing Cards
                try:
                    acc_path = Path(__file__).resolve().parents[1] / "Accurate generators" / "INFERENCING_CARDS.py"
                    if acc_path.exists():
                        spec = importlib.util.spec_from_file_location("_SWS_INFERENCING_ACCURATE", str(acc_path))
                        if spec and spec.loader:
                            alt_mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(alt_mod)
                            mod = alt_mod
                except Exception:
                    pass
            elif key == "word_wall":
                # Prefer Accurate Vocab Word Wall
                try:
                    acc_path = Path(__file__).resolve().parents[1] / "Accurate generators" / "VOCAB_WORD_WALL.py"
                    if acc_path.exists():
                        spec = importlib.util.spec_from_file_location("_SWS_WORD_WALL_ACCURATE", str(acc_path))
                        if spec and spec.loader:
                            alt_mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(alt_mod)
                            mod = alt_mod
                except Exception:
                    pass
        # Special-case: storage labels — production module may not expose generate_storage_labels
        if key == "storage" and not hasattr(mod, func_name):
            alt_path = Path(__file__).resolve().parents[2] / "Generators" / "ARCHIVE generators" / "STORAGE_LABELS.py"
            if alt_path.exists():
                spec = importlib.util.spec_from_file_location("_SWS_STORAGE_LABELS_ALT", str(alt_path))
                if spec and spec.loader:
                    alt_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(alt_mod)
                    mod = alt_mod
        fn  = getattr(mod, func_name)

        # lesson_slides has its own main() that reads sys.argv — call differently
        if key == "lesson_slides":
            result = fn()
        # listing needs (book_slug, product_key, book_title=...)
        elif key == "listing":
            result = fn(slug, "all", book_title=book_title, use_ai=True)
        # zip needs (slug, book_title, pack_code, standard_docs_folder)
        elif key == "zip_pack":
            result = fn(slug, book_title, pack_code)
        # thumbnails needs (slug, book_title, pack_code)
        elif key == "thumbnails":
            result = fn(slug, book_title, base_code)
        # cover pages are generated via COVER_GENERATOR_V2.main() CLI
        elif key == "cover":
            _argv_backup = sys.argv[:]
            try:
                sys.argv = [
                    "COVER_GENERATOR_V2.py",
                    "--book", slug,
                    "--title", book_title,
                    "--all",
                ]
                main_fn = getattr(mod, "main", None)
                if callable(main_fn):
                    main_fn()
                    result = True
                else:
                    # Fall back: try function directly with minimal defaults
                    result = fn(book_title, "matching", 10)
            finally:
                sys.argv = _argv_backup
        # iep tracker — standalone pdf
        elif key == "iep_tracker":
            result = fn(slug, book_title, pack_code)
        # word search takes (slug, book_title, pack_code)
        elif key == "word_search":
            result = fn(slug, book_title, pack_code)
        elif key == "word_wall":
            result = fn(slug, book_title, pack_code)
        # rhyme takes (slug, book_title, pack_code)
        elif key == "rhyme":
            result = fn(slug, book_title, pack_code)
        elif key == "wh_questions":
            # WH Questions expects (slug, book_title, pack_code)
            result = fn(slug, book_title, pack_code)
        # storage always uses (slug, book_title, pack_code)
        elif key == "storage":
            result = fn(slug, book_title, pack_code)
        elif key == "aac_board":
            _argv_backup = sys.argv[:]
            try:
                sys.argv = ["AAC_BOARD_GENERATOR.py", "--book", slug]
                result = fn()
            finally:
                sys.argv = _argv_backup
        # standard: build_pdf products — these resolve the images folder internally
        # from slug (adapted, scarborough), or via a build_pdf() wrapper that does
        # the same resolution (syllable, inferencing) — see those files.
        elif key in BUILD_PDF_PRODUCTS:
            result = fn(slug, book_title, pack_code)
        # standard: everything else takes a real images_folder path, not the slug.
        # (This was the core bug: these generators check `Path(images_folder).exists()`
        # directly — passing the bare slug always failed that check.)
        else:
            # Generators in this branch read icons directly from images_folder.
            # For sequencing, support both archived (slug, book_title, pack_code)
            # and production (images_folder, pack_code, theme_name) signatures.
            if key == "sequencing":
                try:
                    import inspect
                    p0 = next(iter(inspect.signature(fn).parameters.values()), None)
                    if p0 and p0.name in {"slug", "book_slug"}:
                        result = fn(slug, book_title, pack_code)
                    else:
                        pack_code2 = pack_code + fallback_tag
                        result = fn(images_folder, pack_code2, book_title)
                except Exception:
                    pack_code2 = pack_code + fallback_tag
                    result = fn(images_folder, pack_code2, book_title)
            else:
                # If images come from a different theme, append a visible fallback tag
                # to the pack_code so filenames signal cross-theme sourcing.
                pack_code2 = pack_code + fallback_tag
                result = fn(images_folder, pack_code2, book_title)

        elapsed = time.time() - t0
        if result is False:
            return False, elapsed, "Generator returned False"
        return True, elapsed, ""

    except ImportError as e:
        return False, time.time() - t0, f"ImportError: {e}"
    except Exception:
        return False, time.time() - t0, traceback.format_exc(limit=3)


def _count_icons(path: Path) -> int:
    exts = ("*.png", "*.jpg", "*.jpeg")
    n = 0
    for pat in exts:
        n += len(list(path.glob(pat)))
    return n


def resolve_images_folder(slug: str, *, min_icons: int = 6) -> tuple[Path | None, int]:
    """Return a usable images folder for generators that need icons.

    Prefers the target theme's activity_images/icons_colored/icons if they have
    at least min_icons; otherwise, falls back to the richest available theme
    folder across assets/themes/*.
    """
    # Use absolute paths anchored at repo root so CWD does not matter
    try:
        repo = _repo_root  # set during module import above
    except Exception:
        repo = Path(__file__).resolve().parents[2]
    base = repo / "assets" / "themes" / slug
    candidates = [base / "activity_images", base / "icons_colored", base / "icons", base / "real_images"]
    for p in candidates:
        if p.exists():
            n = _count_icons(p)
            if n >= min_icons:
                return p, n
    # Prefer topic-relevant global libraries before scanning other themes
    try:
        repos_to_scan = [repo]
        try:
            parent_repo = repo.parent
            if parent_repo.exists():
                repos_to_scan.append(parent_repo)
        except Exception:
            pass
        # Tokenize slug for simple relevance against global folder names
        tokens = [t for t in re.split(r"[_\\/\-\s]+", slug.lower()) if t]
        best_g: Path | None = None
        best_g_n = 0
        for r in repos_to_scan:
            gdir = r / "assets" / "global"
            if not gdir.exists():
                continue
            for d in gdir.iterdir():
                if not d.is_dir():
                    continue
                name_lc = d.name.lower()
                if not any(t in name_lc for t in tokens):
                    # Only consider global libs that look topic-relevant
                    continue
                # Consider common subfolders; if none exist, allow the folder itself
                subs = ("activity_images", "icons_colored", "icons", "real_images")
                cands = [d / s for s in subs if (d / s).exists()] or [d]
                for cand in cands:
                    n = _count_icons(cand)
                    if n > best_g_n:
                        best_g, best_g_n = cand, n
        if best_g is not None and best_g_n >= min_icons:
            return best_g, best_g_n
    except Exception:
        pass

    # Fallback: scan other themes
    themes = repo / "assets" / "themes"
    best_p: Path | None = None
    best_n = 0
    if themes.exists():
        for t in themes.iterdir():
            if not t.is_dir():
                continue
            for sub in ("activity_images", "icons_colored", "icons", "characters", "aac_boards/previews"):
                cand = t / sub
                if cand.exists():
                    n = _count_icons(cand)
                    if n > best_n:
                        best_p, best_n = cand, n
    # Prefer any best candidate found across themes, even if < min_icons
    if best_p is not None and best_n > 0:
        return best_p, best_n
    # Else, return first existing path for the slug (even if empty)
    for p in candidates:
        if p.exists():
            return p, _count_icons(p)
    return None, 0


def generate_all(slug: str, book_title: str, base_code: str,
                  skip: list[str] = None,
                  only: list[str] = None,
                  include_advanced: bool = False) -> None:
    skip = set(skip or [])
    only = set(only or [])

    print()
    print(bold("=" * 70))
    print(bold("  SMALL WINS STUDIO — GENERATE ALL"))
    print(bold(f"  Book  : {book_title}  ({slug})"))
    print(bold(f"  Code  : {base_code}-*"))
    print(bold("=" * 70))
    print()

    # Resolve images folder with fallback across themes if needed
    found_path, n_icons = resolve_images_folder(slug, min_icons=6)
    if not found_path:
        # Fallback to the canonical theme activity_images path even if empty;
        # some generators (e.g. AAC Board) don't require icons to run.
        try:
            repo = _repo_root
        except Exception:
            repo = Path(__file__).resolve().parents[2]
        fallback = repo / "assets" / "themes" / slug / "activity_images"
        print(yellow(f"  WARNING: No rich icon folder found; using fallback: {fallback}"))
        found_path = fallback
        n_icons = _count_icons(found_path) if found_path.exists() else 0
    print(f"  Images : {found_path}  ({n_icons} icons)")
    # Prominent warning if images come from a different theme
    try:
        src_theme = None
        t = Path(found_path)
        prev = None
        for _ in range(8):
            if t.name == "themes" and prev is not None:
                src_theme = prev.name
                break
            if t.parent == t:
                break
            prev = t
            t = t.parent
        if src_theme and src_theme != slug:
            print(bold(yellow(f"  !!! CROSS-THEME ICON FALLBACK: using '{src_theme}' icons for '{slug}' !!!")))
            print(yellow("  Filenames will be tagged with -FALLBACK-<source_theme> to make this visible."))
    except Exception:
        pass
    print(f"  Output : OUTPUT/")
    print()

    Path("OUTPUT").mkdir(exist_ok=True)

    # Build run list
    run_keys = DEFAULT_KEYS if not include_advanced else {p[0] for p in PRODUCTS}
    if only:
        run_keys = only
    run_keys = run_keys - skip

    products_to_run = [p for p in PRODUCTS if p[0] in run_keys]
    # Remove duplicates (keep first occurrence)
    seen = set()
    products_to_run = [p for p in products_to_run
                       if p[0] not in seen and not seen.add(p[0])]

    n = len(products_to_run)
    print(f"  Running {n} generators:")
    for item in products_to_run:
        print(f"    · {item[1]}")
    print()

    results = []
    total_t0 = time.time()

    for i, (key, display_name, pack_suffix, module_name, func_name) in \
            enumerate(products_to_run, 1):
        pad    = 35
        prefix = f"  [{i:02d}/{n:02d}]  {display_name:{pad}}"
        print(prefix, end="", flush=True)

        ok, elapsed, err = run_generator(
            key, display_name, pack_suffix, module_name, func_name,
            slug, book_title, base_code, str(found_path)
        )

        if ok:
            print(green(f"✓  ({elapsed:.1f}s)"))
        else:
            short = (err.split("\n")[-2] if "\n" in err else err)[:60]
            print(red(f"✗  ({elapsed:.1f}s)  {short}"))

        results.append((display_name, ok, elapsed, err))

    total_elapsed = time.time() - total_t0

    # ── Summary ───────────────────────────────────────────────────────────────
    passed = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]

    print()
    print(bold("=" * 70))
    print(f"  {green(f'{len(passed)}/{n} succeeded')}   "
          f"{red(f'{len(failed)} failed') if failed else green('all passed')}")
    print(f"  Total time: {total_elapsed:.1f}s")

    if failed:
        print()
        print(yellow("  Failed:"))
        for name, _, _, err in failed:
            print(f"    · {name}")
            for line in err.split("\n"):
                line = line.strip()
                if line and not line.startswith("Traceback") \
                        and not line.startswith("File"):
                    print(f"      {line[:80]}")
                    break

    # ── Output file list ──────────────────────────────────────────────────────
    print()
    output_files = sorted(Path("OUTPUT").glob(f"{base_code}-*.pdf"))
    if output_files:
        total_mb = 0.0
        print(f"  Output files ({len(output_files)}):")
        for f in output_files:
            mb = f.stat().st_size / (1024 * 1024)
            total_mb += mb
            print(f"    {f.name:<55}  {mb:.1f} MB")
        print(f"  Total size: {total_mb:.1f} MB")

    br_dir = Path(f"assets/themes/{slug}/aac_boards")
    br_pdfs = sorted(br_dir.glob("*.pdf")) if br_dir.exists() else []
    if br_pdfs:
        total_mb = 0.0
        print(f"  BoardReady AAC boards ({len(br_pdfs)}):")
        for f in br_pdfs:
            mb = f.stat().st_size / (1024 * 1024)
            total_mb += mb
            print(f"    {f.name:<55}  {mb:.1f} MB")
        print(f"  Total size (BoardReady): {total_mb:.1f} MB")

    print(bold("=" * 70))
    print()

    if failed:
        sys.exit(1)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    key_list = "  ".join(p[0] for p in PRODUCTS)
    parser = argparse.ArgumentParser(
        description="Generate all products for a book pack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python GENERATE_ALL.py stellaluna Stellaluna STEL
  python GENERATE_ALL.py stellaluna Stellaluna STEL --skip bingo spin
  python GENERATE_ALL.py stellaluna Stellaluna STEL --only matching word_search bingo
  python GENERATE_ALL.py stellaluna Stellaluna STEL --all   (includes lesson slides, zip etc)

Default runs all activity generators. Use --all for support tools too.

Product keys:
  {key_list}
"""
    )
    parser.add_argument("slug",       help="Book slug e.g. stellaluna")
    parser.add_argument("book_title", help="Book title e.g. Stellaluna")
    parser.add_argument("base_code",  help="Base code e.g. STEL")
    parser.add_argument("--skip",  nargs="+", default=[], metavar="KEY")
    parser.add_argument("--only",  nargs="+", default=[], metavar="KEY")
    parser.add_argument("--all",   action="store_true",
                        help="Include advanced/support generators too")

    args = parser.parse_args()
    generate_all(args.slug, args.book_title, args.base_code,
                 skip=args.skip, only=args.only,
                 include_advanced=args.all)
