#!/usr/bin/env python3
"""Create upload-ready folder bundles per theme/product.

This script COPIES existing generated assets into a tidy structure for easy
TpT uploading and marketing workflows.

Output:
  production/upload_ready/{theme}/{product}/
    finals/
    previews/
    tpt_zips/
    thumbnails/
    freebie/
    listings/

Usage:
  python production/generators/create_upload_ready_folders.py
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


THEME = "brown_bear"

REPO_ROOT = Path(__file__).resolve().parents[2]
FINAL_ROOT = REPO_ROOT / "production" / "final_products" / THEME
MARKETING_ROOT = REPO_ROOT / "production" / "marketing" / THEME
OUT_ROOT = REPO_ROOT / "production" / "upload_ready" / THEME


@dataclass(frozen=True)
class ProductSpec:
    product_id: str
    title: str


PRODUCTS: list[ProductSpec] = [
    ProductSpec(product_id="matching", title="Matching"),
    ProductSpec(product_id="find_cover", title="Find & Cover"),
]


MATCHING_FREEBIE_LISTING_TEXT = """Brown Bear Matching | FREE Sampler (Levels 1–5)

Try before you buy! This FREE Brown Bear Matching sampler gives you a quick, usable preview of the full differentiated bundle—perfect for SPED, autism support, early learners, and SLP sessions.

Includes:
- 5 sample pages (Levels 1–5)
- Icon cutout pieces
- Quick Start guide (how to use + level overview)
- Terms of Use

Love it? Grab the full Brown Bear Matching Bundle (Levels 1–5) for the complete set of worksheets, cutouts, and differentiation.
"""


def _ensure_empty_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_tree(src_dir: Path, dst_dir: Path) -> None:
    if not src_dir.exists():
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(src_dir)
        _copy_file(p, dst_dir / rel)


def _copy_freebie(final_dir: Path, out_dir: Path) -> None:
    freebie_src = final_dir / "freebie"
    if freebie_src.exists():
        _copy_tree(freebie_src, out_dir / "freebie")


def _copy_tpt_zips(final_dir: Path, out_dir: Path) -> None:
    zips_src = final_dir / "tpt_zips"
    if zips_src.exists():
        _copy_tree(zips_src, out_dir / "tpt_zips")


def _copy_thumbnails(product_id: str, out_dir: Path) -> None:
    thumbs_src = MARKETING_ROOT / product_id / "thumbnails"
    if thumbs_src.exists():
        _copy_tree(thumbs_src, out_dir / "thumbnails")


def _copy_pdfs_split(final_dir: Path, out_dir: Path) -> None:
    finals_out = out_dir / "finals"
    previews_out = out_dir / "previews"
    finals_out.mkdir(parents=True, exist_ok=True)
    previews_out.mkdir(parents=True, exist_ok=True)

    for pdf in sorted(final_dir.glob("*.pdf")):
        name = pdf.name
        if name.endswith("_PREVIEW.pdf") or name.endswith("_preview.pdf"):
            _copy_file(pdf, previews_out / name)
        else:
            _copy_file(pdf, finals_out / name)


def _write_listings(product_id: str, out_dir: Path) -> None:
    listings_dir = out_dir / "listings"
    listings_dir.mkdir(parents=True, exist_ok=True)

    marketing_dir = MARKETING_ROOT / product_id
    if marketing_dir.exists():
        for txt in sorted(marketing_dir.glob("*.txt")):
            _copy_file(txt, listings_dir / txt.name)

    if product_id == "matching":
        (listings_dir / "FREE_SAMPLER_description.txt").write_text(
            MATCHING_FREEBIE_LISTING_TEXT, encoding="utf-8"
        )


def build_bundle(product: ProductSpec) -> Path:
    final_dir = FINAL_ROOT / product.product_id
    if not final_dir.exists():
        raise FileNotFoundError(str(final_dir))

    out_dir = OUT_ROOT / product.product_id
    _ensure_empty_dir(out_dir)

    _copy_pdfs_split(final_dir, out_dir)
    _copy_tpt_zips(final_dir, out_dir)
    _copy_thumbnails(product.product_id, out_dir)
    _write_listings(product.product_id, out_dir)

    _copy_freebie(final_dir, out_dir)

    return out_dir


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Upload-Ready Bundle Builder")
    print("=" * 60)
    print(f"Theme: {THEME}")
    print(f"Output: {OUT_ROOT}")

    for p in PRODUCTS:
        out_dir = build_bundle(p)
        print(f"OK Built: {out_dir}")


if __name__ == "__main__":
    main()
