#!/usr/bin/env python3
"""
Final ZIP Packager for Small Wins Studio packs

- Collects PDFs for a given slug/base_code from common OUTPUT locations
- Always includes BoardReady AAC Board PDFs from assets/themes/<slug>/aac_boards
- Produces a timestamped ZIP under OUTPUT/PACKAGES

Signature expected by GENERATE_ALL.py:
  package_book(slug: str, book_title: str, pack_code: str) -> bool
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from datetime import datetime
import re

# Candidate OUTPUT roots (mirror readiness_report)
OUTPUT_DIR_CANDIDATES = [
    Path("OUTPUT"),
    Path(__file__).resolve().parents[0] / "OUTPUT",
    Path(__file__).resolve().parents[1] / "Studioforge" / "OUTPUT",
    Path(__file__).resolve().parents[1] / "Studioforge" / "Accurate generators" / "OUTPUT",
]

KEYWORDS = {
    "grammar_mat":  ["grammar", "storygrammarmat", "story_grammar", "story_elements", "storyelementsmat"],
    "phoneme":      ["phoneme", "segmentation"],
    "wh_questions": ["whquestions", "wh_questions", "wh-questions"],
    "bingo":        ["bingo"],
    "sequencing":   ["sequencing", "sequence", "storystrips"],
    "storage":      ["storagelabels", "storage_labels"],
    "rhyme":        ["rhyme"],
    "cover":        ["cover", "cover_page"],
    "sorting":      ["sorting", "sort"],
}


def _all_output_pdfs() -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for d in OUTPUT_DIR_CANDIDATES:
        if not d.exists():
            continue
        for p in d.rglob("*.pdf"):
            key = str(p.resolve()).lower()
            if key not in seen:
                seen.add(key)
                out.append(p)
    return out


def _collect_for_pack(slug: str, base_code: str) -> list[Path]:
    repo_root = Path(__file__).resolve().parents[0]
    # BoardReady AAC boards
    br_dir = repo_root / "assets" / "themes" / slug / "aac_boards"

    selected: list[Path] = []

    # 1) Strict prefix matches (base_code-*) from OUTPUT roots
    for d in OUTPUT_DIR_CANDIDATES:
        if not d.exists():
            continue
        for p in d.glob(f"{base_code}-*.pdf"):
            if p not in selected:
                selected.append(p)

    # 2) Heuristic matches by keyword and slug/base_code presence
    all_pdfs = _all_output_pdfs()
    slug_ns = slug.lower().replace("_", "")
    for p in all_pdfs:
        name = p.name.lower().replace(" ", "")
        name2 = name.replace("_", "")
        parent_str = str(p.parent).lower()
        if not (slug.lower() in parent_str or slug_ns in name2 or base_code.lower() in name2):
            continue
        for toks in KEYWORDS.values():
            if any(t in name for t in toks):
                if p not in selected:
                    selected.append(p)
                break

    # 3) Always include BoardReady AAC boards
    if br_dir.exists():
        for p in sorted(br_dir.glob("*.pdf")):
            nameu = p.name.lower()
            if nameu.endswith("_preview.pdf"):
                continue
            if p not in selected:
                selected.append(p)

    return selected


def _dedupe_by_name_prefer_newest(paths: list[Path]) -> list[Path]:
    """Collapse files with the same basename, keeping the newest (mtime),
    and on ties the largest size. Returns a stable list ordered by (name asc)."""
    best: dict[str, Path] = {}
    for p in paths:
        name = p.name
        try:
            mt = p.stat().st_mtime
            sz = p.stat().st_size
        except Exception:
            mt, sz = 0.0, 0
        cur = best.get(name)
        if cur is None:
            best[name] = p
            continue
        try:
            mt0 = cur.stat().st_mtime
            sz0 = cur.stat().st_size
        except Exception:
            mt0, sz0 = 0.0, 0
        if (mt, sz) > (mt0, sz0):
            best[name] = p
    return [best[k] for k in sorted(best.keys())]


_AAC_VARIANT_RE = re.compile(
    r"^(?:[A-Za-z0-9\-]+_)?AAC_Board(?:_WS)?_"
    r"(COLOR_HIGHVIS|COLOR|BW|WS_COLOR|WS_BW|PREVIEW)\.pdf$",
    re.IGNORECASE,
)


def _dedupe_aac_variants(paths: list[Path]) -> list[Path]:
    """Group all AAC board PDFs across naming variants and keep the newest per
    logical variant (COLOR, BW, COLOR_HIGHVIS, WS_COLOR, WS_BW, PREVIEW).

    Recognises names like:
      - LLRP-BOARD_AAC_Board_COLOR.pdf
      - LLA1_AAC_Board_COLOR.pdf
      - AAC_Board_COLOR.pdf
      - LLA1_AAC_Board_WS_COLOR.pdf
    """
    groups: dict[str, list[Path]] = {}
    others: list[Path] = []
    for p in paths:
        m = _AAC_VARIANT_RE.match(p.name)
        if m:
            var = m.group(1).upper()
            groups.setdefault(var, []).append(p)
        else:
            others.append(p)

    chosen: list[Path] = []
    for var, items in groups.items():
        # newest by mtime, then largest size
        def keyfn(x: Path):
            try:
                st = x.stat()
                return (st.st_mtime, st.st_size)
            except Exception:
                return (0.0, 0)
        best = max(items, key=keyfn)
        chosen.append(best)

    # Also collapse across variants to a single newest AAC board overall.
    if chosen:
        def keyfn2(x: Path):
            try:
                st = x.stat()
                return (st.st_mtime, st.st_size)
            except Exception:
                return (0.0, 0)
        newest = max(chosen, key=keyfn2)
        chosen = [newest]

    return chosen + others


def package_book(slug: str, book_title: str, pack_code: str) -> bool:
    """Create a ZIP that includes all outputs + AAC boards for a pack."""
    files = _collect_for_pack(slug, pack_code)
    # First, collapse AAC board variants across naming conventions by logical variant
    files = _dedupe_aac_variants(files)
    files = _dedupe_by_name_prefer_newest(files)

    if not files:
        print("No files found to package.")
        return False

    out_root = Path("OUTPUT")
    (out_root / "PACKAGES").mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    zip_path = out_root / "PACKAGES" / f"{pack_code}_PACKAGE_{ts}.zip"

    # Determine AAC dir to place under AAC_Boards/ inside ZIP
    repo_root = Path(__file__).resolve().parents[0]
    aac_dir = (repo_root / "assets" / "themes" / slug / "aac_boards").resolve()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        manifest = []
        for p in files:
            p = p.resolve()
            arcname: str
            if aac_dir in p.parents:
                arcname = f"AAC_Boards/{p.name}"
            else:
                arcname = f"Products/{p.name}"
            z.write(p, arcname)
            manifest.append({"name": p.name, "arc": arcname, "size": p.stat().st_size})
        # Write a small JSON manifest inside the zip for traceability
        z.writestr("manifest.json", json.dumps({
            "slug": slug,
            "title": book_title,
            "base_code": pack_code,
            "count": len(files),
            "files": manifest,
        }, ensure_ascii=False, indent=2))

    print(f"Packaged {len(files)} files into {zip_path}")
    return True
