#!/usr/bin/env python3
"""
Readiness and archive-candidate report generator for Small Wins Studio packs.

- Scans OUTPUT/ for PDFs by base_code/suffix mapping
- Also scans BoardReady AAC Boards under assets/themes/<slug>/aac_boards
- Renders first page of each PDF and reports:
  * mean RGB of center region and whole page
  * top 5 colors (percent coverage)
  * distances to brand colors (SWS_TEAL, SWS_NAVY, SWS_TEAL_LT)
- Writes JSON and CSV reports to _reports/
- Emits archive-candidate list: keys with 0 outputs or pages that appear blank (>=95% white)

Usage:
  python Studioforge/tools/readiness_report.py --slug llama_llama_red_pajama --title "Llama Llama Red Pajama" --code LLRP \
    --keys aac_board sorting bingo sequencing storage grammar_mat phoneme rhyme wh_questions cover
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Tuple, Dict, Any

try:
    import fitz  # PyMuPDF
    from PIL import Image, ImageStat
except Exception as e:
    raise SystemExit(f"Missing dependencies (Pillow / PyMuPDF): {e}")

SWS_TEAL    = (0x31, 0xA8, 0xA0)  # #31A8A0
SWS_NAVY    = (0x0D, 0x25, 0x45)  # #0D2545
SWS_TEAL_LT = (0xEA, 0xF8, 0xF8)  # #EAF8F8
WHITE       = (255, 255, 255)
WHITE_NEAR_THR = float(os.getenv("SWS_WHITE_NEAR_THR", "8.0"))
WHITE_DOM_PCT = float(os.getenv("SWS_WHITE_DOM_PCT", "0.985"))
WHITE_STRICT_PCT_SINGLE = float(os.getenv("SWS_WHITE_STRICT_PCT_SINGLE", "0.995"))

SUFFIX = {
    "aac_board":   "BOARD",  # Not used for path match (BoardReady special-case)
    "sorting":     "SORT",
    "bingo":       "BINGO",
    "sequencing":  "SEQ",
    "storage":     "STOR",
    "grammar_mat": "SGM",
    "phoneme":     "PSM",
    "rhyme":       "RHY",
    "wh_questions":"WH",
    "cover":       "COV",
}

# Resolve repository root (two parents up from tools/)
try:
    REPO_ROOT = Path(__file__).resolve().parents[2]
except Exception:
    REPO_ROOT = Path.cwd()

# Additional search roots for OUTPUT PDFs across the repo layout
OUTPUT_DIR_CANDIDATES = [
    Path("OUTPUT"),
    REPO_ROOT / "OUTPUT",
    REPO_ROOT / "Studioforge" / "OUTPUT",
    REPO_ROOT / "Studioforge" / "Accurate generators" / "OUTPUT",
    REPO_ROOT / "production" / "generators" / "Studioforge" / "OUTPUT",
]

# Filename keyword heuristics for products that don't follow base_code-suffix
KEYWORDS: Dict[str, List[str]] = {
    "grammar_mat":  ["grammar", "storygrammarmat", "story_grammar"],
    "phoneme":      ["phoneme", "segmentation"],
    "wh_questions": ["whquestions", "wh_questions", "wh-questions"],
    "bingo":        ["bingo"],
    "sequencing":   ["sequencing", "sequence", "storystrips"],
    "storage":      ["storagelabels", "storage_labels"],
    "rhyme":        ["rhyme"],
    "cover":        ["cover", "cover_page"],
    "sorting":      ["sorting", "sort"],
    "word_wall":    ["wordwall", "word_wall", "vocabulary"],
    "matching":     ["matching"],
    "word_search":  ["wordsearch", "word_search"],
    "adapted":      ["adapted", "adaptedbook"],
    "sentence":     ["sentencestrips", "sentence_strips", "aac_sentence"],
    "yes_no":       ["yesno", "yes_no", "yn"],
    "syllable":     ["syllable", "syl"],
    "inferencing":  ["inferencing", "inference"],
    "scarborough":  ["scarborough", "rope"],
    "spin":         ["spincover", "spin"],
    "find_cover":   ["findandcover", "find_cover"],
    "iep_tracker":  ["iep", "monitoring", "tracker"],
}

@dataclass
class FileCheck:
    product_key: str
    path: str
    size_mb: float
    page0_mean_rgb: Tuple[int, int, int]
    center_mean_rgb: Tuple[int, int, int]
    top_colors: List[Dict[str, Any]]  # [{hex, rgb, pct}]
    brand_dist: Dict[str, float]
    fallback_source: str | None = None
    # Optional, storage-specific label color coverage within label ROI (% of ROI pixels)
    label_color_pct: Dict[str, float] | None = None
    # Optional, AAC-board specific ROI color coverage
    aac_color_pct: Dict[str, float] | None = None

@dataclass
class ProductResult:
    product_key: str
    outputs_found: int
    files: List[FileCheck]


def rgb_dist(a: Tuple[int,int,int], b: Tuple[int,int,int]) -> float:
    return math.sqrt(sum((int(x)-int(y))**2 for x,y in zip(a,b)))


def hex_of(rgb: Tuple[int,int,int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def top_colors(img: Image.Image, n: int = 5) -> List[Tuple[int,Tuple[int,int,int]]]:
    small = img.convert("RGB").resize((256, 256), Image.BILINEAR)
    colors = small.getcolors(256*256)
    if not colors:
        return []
    colors.sort(key=lambda x: x[0], reverse=True)
    return colors[:n]


def mean_rgb(img: Image.Image) -> Tuple[int,int,int]:
    stat = ImageStat.Stat(img.convert("RGB"))
    m = stat.mean  # [R,G,B]
    return tuple(int(round(x)) for x in m)


def is_white_dominant_from_fc(fc: "FileCheck", near_thr: float = WHITE_NEAR_THR, dom_pct: float = WHITE_DOM_PCT) -> bool:
    try:
        if not fc.top_colors:
            return False
        dom = fc.top_colors[0]
        rgb = tuple(dom["rgb"])  # type: ignore[index]
        pct = float(dom["pct"])  # type: ignore[index]
        return (rgb_dist(rgb, WHITE) <= near_thr) and (pct >= dom_pct)
    except Exception:
        return False


def render_first_page(pdf_path: Path, dpi: int = 144) -> Image.Image:
    doc = fitz.open(str(pdf_path))
    try:
        if len(doc) == 0:
            raise RuntimeError("empty document")
        page = doc[0]
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return img
    finally:
        doc.close()


def analyze_pdf(product_key: str, pdf_path: Path) -> FileCheck:
    img = render_first_page(pdf_path)
    w, h = img.size
    cx0, cy0 = int(w*0.3), int(h*0.3)
    cx1, cy1 = int(w*0.7), int(h*0.7)
    center = img.crop((cx0, cy0, cx1, cy1))

    m_full = mean_rgb(img)
    m_center = mean_rgb(center)

    palette = top_colors(img, 5)
    total = sum(c for c,_ in palette) or 1
    palette_out = [
        {"hex": hex_of(rgb), "rgb": list(rgb), "pct": round(count/total, 4)}
        for count, rgb in palette
    ]

    dists = {
        "teal": round(rgb_dist(m_full, SWS_TEAL), 2),
        "navy": round(rgb_dist(m_full, SWS_NAVY), 2),
        "teal_lt": round(rgb_dist(m_full, SWS_TEAL_LT), 2),
    }

    fsrc = None
    m = re.search(r"-FALLBACK-([A-Za-z0-9_]+)", pdf_path.name, re.IGNORECASE)
    if m:
        fsrc = m.group(1)

    # Optional storage-specific label ROI color coverage
    label_pct: Dict[str, float] | None = None
    if product_key == "storage":
        # ROI heuristic: exclude page header/footer and outer margins to focus on labels
        rx0, rx1 = int(w*0.10), int(w*0.90)
        ry0, ry1 = int(h*0.18), int(h*0.88)
        if rx1 > rx0 and ry1 > ry0:
            roi = img.crop((rx0, ry0, rx1, ry1)).convert("RGB")
            # Downscale for speed but preserve color ratios
            target_w = 512
            if roi.width > target_w:
                target_h = max(1, int(roi.height * target_w / roi.width))
                roi = roi.resize((target_w, target_h), Image.BILINEAR)

            def pct_near(im: Image.Image, target: Tuple[int,int,int], tol: int = 16) -> float:
                tw, th = im.size
                pixels = im.load()
                thr2 = tol * tol
                hit = 0
                total = tw * th
                r0, g0, b0 = target
                for yy in range(th):
                    for xx in range(tw):
                        r, g, b = pixels[xx, yy]
                        dr = r - r0; dg = g - g0; db = b - b0
                        if (dr*dr + dg*dg + db*db) <= thr2:
                            hit += 1
                return round(100.0 * hit / max(total, 1), 2)

            pct_teal    = pct_near(roi, SWS_TEAL, tol=18)
            pct_teal_lt = pct_near(roi, SWS_TEAL_LT, tol=18)
            # Legacy palette checks (should be ~0 if fixed)
            LEG_OLIVE = (0xC9, 0xC0, 0x85)  # #C9C085
            LEG_BROWN = (0x5C, 0x5C, 0x3D)  # #5C5C3D
            pct_olive = pct_near(roi, LEG_OLIVE, tol=18)
            pct_brown = pct_near(roi, LEG_BROWN, tol=18)
            label_pct = {
                "teal_31A8A0": pct_teal,
                "teal_lt_EAF5F4": pct_teal_lt,
                "legacy_olive_C9C085": pct_olive,
                "legacy_brown_5C5C3D": pct_brown,
            }

    # Optional AAC-board ROI color coverage
    aac_pct: Dict[str, float] | None = None
    if product_key == "aac_board":
        rx0, rx1 = int(w*0.12), int(w*0.88)
        ry0, ry1 = int(h*0.12), int(h*0.88)
        region = img.crop((rx0, ry0, rx1, ry1)) if (rx1 > rx0 and ry1 > ry0) else img
        roi = region.convert("RGB")
        target_w = 512
        if roi.width > target_w:
            target_h = max(1, int(roi.height * target_w / roi.width))
            roi = roi.resize((target_w, target_h), Image.BILINEAR)

        def pct_near2(im: Image.Image, target: Tuple[int,int,int], tol: int = 16) -> float:
            tw, th = im.size
            pixels = im.load()
            thr2 = tol * tol
            hit = 0
            total = tw * th
            r0, g0, b0 = target
            for yy in range(th):
                for xx in range(tw):
                    r, g, b = pixels[xx, yy]
                    dr = r - r0; dg = g - g0; db = b - b0
                    if (dr*dr + dg*dg + db*db) <= thr2:
                        hit += 1
            return round(100.0 * hit / max(total, 1), 2)

        TEAL_LT_2 = (0xEA, 0xF5, 0xF4)
        pct_teal_strict  = pct_near2(roi, SWS_TEAL, tol=18)
        pct_teal_loose   = pct_near2(roi, SWS_TEAL, tol=30)
        pct_navy         = pct_near2(roi, SWS_NAVY, tol=18)
        pct_lt           = pct_near2(roi, TEAL_LT_2, tol=18)
        aac_pct = {
            "teal_31A8A0_strict": pct_teal_strict,
            "teal_31A8A0_loose": pct_teal_loose,
            "navy_0D2545": pct_navy,
            "teal_lt_EAF5F4": pct_lt,
        }

    return FileCheck(
        product_key=product_key,
        path=str(pdf_path),
        size_mb=round(pdf_path.stat().st_size / (1024*1024), 2),
        page0_mean_rgb=m_full,
        center_mean_rgb=m_center,
        top_colors=palette_out,
        brand_dist=dists,
        fallback_source=fsrc,
        label_color_pct=label_pct,
        aac_color_pct=aac_pct,
    )


def _all_output_pdfs() -> List[Path]:
    seen: set[str] = set()
    out: List[Path] = []
    for d in OUTPUT_DIR_CANDIDATES:
        if not d.exists():
            continue
        for p in d.rglob("*.pdf"):
            key = str(p.resolve()).lower()
            if key not in seen:
                seen.add(key)
                out.append(p)
    return out


def find_outputs(base_code: str, slug: str, keys: List[str]) -> Dict[str, List[Path]]:
    out: Dict[str, List[Path]] = {k: [] for k in keys}
    # BoardReady special-case (anchored to repo root)
    if "aac_board" in keys:
        br_dir = REPO_ROOT / "assets" / "themes" / slug / "aac_boards"
        out["aac_board"] = sorted(br_dir.glob("*.pdf")) if br_dir.exists() else []

    # First pass: suffix-based matches in all candidate OUTPUT dirs
    theme_output_dir = REPO_ROOT / "assets" / "themes" / slug / "OUTPUT"
    for k in keys:
        if k == "aac_board":
            continue
        suf = SUFFIX.get(k)
        if not suf:
            continue
        for d in OUTPUT_DIR_CANDIDATES + [theme_output_dir]:
            if not d.exists():
                continue
            for p in d.glob(f"{base_code}-{suf}*.pdf"):
                if p not in out[k]:
                    out[k].append(p)

    # Second pass: heuristic filename keyword matches (case-insensitive)
    all_pdfs = _all_output_pdfs() + (list(theme_output_dir.rglob("*.pdf")) if theme_output_dir.exists() else [])
    for k in keys:
        if k == "aac_board":
            continue
        toks = [t.lower() for t in KEYWORDS.get(k, [])]
        for p in all_pdfs:
            name = p.name.lower().replace(" ", "")
            name2 = name.replace("_", "")
            parent_str = str(p.parent).lower()
            slug_ns = slug.lower().replace("_", "")
            # Heuristic only if matches this slug in path or appears in filename (sanitized),
            # or base_code is present in filename
            if not (slug.lower() in parent_str or slug_ns in name2 or base_code.lower() in name2):
                continue
            if any(t in name for t in toks):
                if p not in out[k]:
                    out[k].append(p)
    # Normalize sort order
    for k in keys:
        out[k] = sorted(out[k])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--code", required=True)
    ap.add_argument("--keys", nargs="+", required=True)
    args = ap.parse_args()

    keys = list(dict.fromkeys(args.keys))  # de-dupe

    report_dir = Path("_reports")
    report_dir.mkdir(exist_ok=True)

    outputs = find_outputs(args.code, args.slug, keys)

    results: List[ProductResult] = []
    archive_candidates: List[str] = []

    for k in keys:
        files = outputs.get(k, [])
        checks: List[FileCheck] = []
        for p in files:
            try:
                checks.append(analyze_pdf(k, p))
            except Exception as e:
                # Capture an error sentinel file entry
                checks.append(FileCheck(
                    product_key=k,
                    path=str(p),
                    size_mb=round(p.stat().st_size/(1024*1024),2) if p.exists() else 0.0,
                    page0_mean_rgb=(0,0,0),
                    center_mean_rgb=(0,0,0),
                    top_colors=[{"hex":"#000000","rgb":[0,0,0],"pct":0.0}],
                    brand_dist={"teal": -1.0, "navy": -1.0, "teal_lt": -1.0},
                ))
        results.append(ProductResult(product_key=k, outputs_found=len(files), files=checks))

        if len(files) == 0:
            archive_candidates.append(k)
        else:
            try:
                if len(checks) >= 2:
                    if is_white_dominant_from_fc(checks[0], WHITE_NEAR_THR, WHITE_DOM_PCT) and \
                       is_white_dominant_from_fc(checks[1], WHITE_NEAR_THR, WHITE_DOM_PCT):
                        archive_candidates.append(k)
                else:
                    if is_white_dominant_from_fc(checks[0], WHITE_NEAR_THR, WHITE_STRICT_PCT_SINGLE):
                        archive_candidates.append(k)
            except Exception:
                pass

    # Write JSON
    ts = __import__("datetime").datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = report_dir / f"readiness_{args.slug}_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "slug": args.slug,
            "title": args.title,
            "base_code": args.code,
            "keys": keys,
            "results": [
                {
                    "product_key": r.product_key,
                    "outputs_found": r.outputs_found,
                    "files": [asdict(fc) for fc in r.files],
                }
                for r in results
            ],
            "archive_candidates": archive_candidates,
        }, f, ensure_ascii=False, indent=2)

    # Write CSV summary
    csv_path = report_dir / f"readiness_{args.slug}_{ts}.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["product_key","outputs_found","file","size_mb","page0_mean_rgb","center_mean_rgb","top1_hex","top1_pct","dist_teal","dist_navy","dist_teal_lt"])
        for r in results:
            if not r.files:
                w.writerow([r.product_key, r.outputs_found, "", "", "", "", "", "", "", "", ""])
            else:
                for fc in r.files:
                    top1_hex = fc.top_colors[0]["hex"] if fc.top_colors else ""
                    top1_pct = fc.top_colors[0]["pct"] if fc.top_colors else ""
                    w.writerow([
                        r.product_key,
                        r.outputs_found,
                        Path(fc.path).name,
                        fc.size_mb,
                        ":".join(map(str, fc.page0_mean_rgb)),
                        ":".join(map(str, fc.center_mean_rgb)),
                        top1_hex,
                        top1_pct,
                        fc.brand_dist.get("teal"),
                        fc.brand_dist.get("navy"),
                        fc.brand_dist.get("teal_lt"),
                    ])

    # Write archive-candidate list
    txt_path = report_dir / f"ARCHIVE_DRYRUN_candidates_{args.slug}_{ts}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        for k in archive_candidates:
            f.write(k + "\n")

    print(f"Report: {json_path}")
    print(f"Summary: {csv_path}")
    print(f"Archive candidates: {txt_path}")


if __name__ == "__main__":
    main()
