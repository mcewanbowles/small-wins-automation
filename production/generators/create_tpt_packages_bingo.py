#!/usr/bin/env python3
"""Create TpT-Ready ZIP Packages for Brown Bear Bingo.

Packages each level with ONLY the required documents:
- Color PDF (integrated cover as first page)
- Black & White PDF (integrated cover as first page)
- Terms of Use / Credits (official)
- Quick Start Guide (product-level)

Output:
  production/final_products/brown_bear/bingo/tpt_zips/

Usage:
  python production/generators/create_tpt_packages_bingo.py
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from PyPDF2 import PdfReader


THEME = "brown_bear"
PRODUCT = "bingo"

LEVELS = [
    {"num": 1, "name": "Real_Photos"},
    {"num": 2, "name": "Icons_Only"},
    {"num": 3, "name": "Real_Photos"},
    {"num": 4, "name": "Real_Photos_Text"},
    {"num": 5, "name": "Text_Only"},
]

REPO_ROOT = Path(__file__).resolve().parents[2]
FINAL_DIR = REPO_ROOT / "production" / "final_products" / THEME / PRODUCT
SUPPORT_DOCS_DIR = REPO_ROOT / "production" / "support_docs"
OUTPUT_DIR = FINAL_DIR / "tpt_zips"

TOU_PDF = SUPPORT_DOCS_DIR / "Terms_of_Use_Credits.pdf"
QUICK_START_PDF = FINAL_DIR / f"{THEME}_{PRODUCT}_quick_start.pdf"


def create_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")


def get_level_pdfs(level_num: int, level_name: str) -> dict[str, Path] | None:
    color_pdf = FINAL_DIR / f"{THEME}_{PRODUCT}_level{level_num}_{level_name}_color_FINAL.pdf"
    bw_pdf = FINAL_DIR / f"{THEME}_{PRODUCT}_level{level_num}_{level_name}_bw_FINAL.pdf"

    if not color_pdf.exists():
        print(f"  WARNING No color PDF found for Level {level_num}")
        return None
    if not bw_pdf.exists():
        print(f"  WARNING No B&W PDF found for Level {level_num}")
        return None

    try:
        color_pages = len(PdfReader(str(color_pdf)).pages)
        bw_pages = len(PdfReader(str(bw_pdf)).pages)
        print(f"  Info: Level {level_num} page counts: color={color_pages}, bw={bw_pages}")
        if color_pages < 2 or bw_pages < 2:
            print("  WARNING PDF page count looks low; it may be missing integrated cover")
    except Exception:
        print("  WARNING Could not read PDF page count for verification")

    return {"color": color_pdf, "bw": bw_pdf}


def create_level_package(level: dict) -> Path | None:
    level_num = level["num"]
    level_name = level["name"]

    print(f"\n{'=' * 60}")
    print(f"Creating TpT Package for Bingo Level {level_num} ({level_name})")
    print(f"{'=' * 60}")

    pdfs = get_level_pdfs(level_num, level_name)
    if not pdfs:
        print(f"FAILED to find PDFs for Level {level_num}")
        return None

    zip_filename = OUTPUT_DIR / f"{THEME}_{PRODUCT}_level{level_num}_TpT.zip"

    try:
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            color_name = f"Brown_Bear_Bingo_Level{level_num}_{level_name}_Color.pdf"
            zipf.write(pdfs["color"], color_name)
            print(f"  OK Added: {color_name} ({pdfs['color'].stat().st_size / 1024 / 1024:.1f} MB)")

            bw_name = f"Brown_Bear_Bingo_Level{level_num}_{level_name}_BW.pdf"
            zipf.write(pdfs["bw"], bw_name)
            print(f"  OK Added: {bw_name} ({pdfs['bw'].stat().st_size / 1024 / 1024:.1f} MB)")

            if TOU_PDF.exists():
                zipf.write(TOU_PDF, "Terms_of_Use_Credits.pdf")
                print(f"  OK Added: Terms_of_Use_Credits.pdf ({TOU_PDF.stat().st_size / 1024:.0f} KB)")
            else:
                print("  WARNING Missing: Terms_of_Use_Credits.pdf")

            if QUICK_START_PDF.exists():
                zipf.write(QUICK_START_PDF, "Quick_Start_Bingo.pdf")
                print(f"  OK Added: Quick_Start_Bingo.pdf ({QUICK_START_PDF.stat().st_size / 1024:.0f} KB)")
            else:
                print(f"  WARNING Missing: {QUICK_START_PDF.name}")

        zip_size = zip_filename.stat().st_size / 1024 / 1024
        print(f"\nOK Created: {zip_filename.name} ({zip_size:.1f} MB)")
        return zip_filename

    except Exception as e:
        print(f"Error creating ZIP for Level {level_num}: {e}")
        return None


def create_all_packages() -> list[Path]:
    print("\n" + "=" * 60)
    print("TpT Package Creator")
    print(f"Theme: {THEME.replace('_', ' ').title()}")
    print("Product: Bingo")
    print("=" * 60)

    create_output_dir()

    created: list[Path] = []
    for level in LEVELS:
        package = create_level_package(level)
        if package:
            created.append(package)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nCreated {len(created)} TpT packages:")
    for package in created:
        size = package.stat().st_size / 1024 / 1024
        print(f"  OK {package.name} ({size:.1f} MB)")

    print(f"\nOutput location: {OUTPUT_DIR}")
    print("\nAll packages ready for TpT upload!")

    return created


if __name__ == "__main__":
    create_all_packages()
