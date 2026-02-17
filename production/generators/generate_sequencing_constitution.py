#!/usr/bin/env python3
"""Sequencing Production Constitution Generator.

Runs the draft sequencing generator, copies outputs to production/final_products/,
and generates preview PDFs.

Output:
  production/final_products/brown_bear/sequencing/
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from generators.sequencing.generate_sequencing_brown_bear import main as generate_sequencing

THEME = "brown_bear"
PRODUCT = "sequencing"
PACK_CODE = "BB-SEQ"

OUTPUT_DIR = REPO_ROOT / "output" / PRODUCT
FINAL_DIR = REPO_ROOT / "production" / "final_products" / THEME / PRODUCT
SAMPLES_DIR = REPO_ROOT / "samples" / THEME / PRODUCT


def main() -> int:
    print("=" * 60)
    print(f"Brown Bear Sequencing - Production Export")
    print("=" * 60)

    # Step 1: Generate draft PDFs
    generate_sequencing()

    # Step 2: Copy to production final_products
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    color_src = OUTPUT_DIR / "BROWN_BEAR_SEQ_Sequencing.pdf"
    bw_src = OUTPUT_DIR / "BROWN_BEAR_SEQ_Sequencing_BW.pdf"
    preview_src = OUTPUT_DIR / "BROWN_BEAR_SEQ_Sequencing_PREVIEW.pdf"

    color_dst = FINAL_DIR / f"{THEME}_{PRODUCT}_color_FINAL.pdf"
    bw_dst = FINAL_DIR / f"{THEME}_{PRODUCT}_bw_FINAL.pdf"
    preview_dst = FINAL_DIR / f"{THEME}_{PRODUCT}_preview.pdf"

    for src, dst in [(color_src, color_dst), (bw_src, bw_dst), (preview_src, preview_dst)]:
        if src.exists():
            shutil.copy2(src, dst)
            print(f"OK Copied: {dst.name}")
        else:
            print(f"WARNING Missing: {src}")

    # Step 3: Copy Quick Start to samples and final
    qs_src = REPO_ROOT / "samples" / THEME / PRODUCT / f"{THEME}_{PRODUCT}_quick_start.pdf"
    if qs_src.exists():
        qs_dst = FINAL_DIR / f"{THEME}_{PRODUCT}_quick_start.pdf"
        shutil.copy2(qs_src, qs_dst)
        print(f"OK Copied Quick Start: {qs_dst.name}")

    print(f"\nOK Final products exported to:\n  {FINAL_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
