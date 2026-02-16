#!/usr/bin/env python3
"""Create TpT-Ready ZIP Packages for Brown Bear Find & Cover.

Packages each level with ONLY the required documents:
- Color PDF
- Black & White PDF
- Terms of Use / Credits (official)
- Quick Start Guide (product-level)

Output:
  production/final_products/brown_bear/find_cover/tpt_zips/

Usage:
  python production/generators/create_tpt_packages_find_cover.py
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from PyPDF2 import PdfReader


THEME = "brown_bear"
PRODUCT = "find_cover"

LEVELS = [
    {"num": 1, "name": "Errorless"},
    {"num": 2, "name": "Supported"},
    {"num": 3, "name": "Independent"},
    {"num": 4, "name": "Generalization"},
    {"num": 5, "name": "Extension"},
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

    # Verify these are the integrated FINAL PDFs (cover + activity + cutouts/labels + storage labels).
    # We don't hard-fail, but we do warn if the PDF looks suspiciously small.
    try:
        color_pages = len(PdfReader(str(color_pdf)).pages)
        bw_pages = len(PdfReader(str(bw_pdf)).pages)
        print(f"  Info: Level {level_num} page counts: color={color_pages}, bw={bw_pages}")
        if color_pages < 10 or bw_pages < 10:
            print("  WARNING PDF page count looks low; it may be missing integrated cover/cutouts/labels")
    except Exception:
        print("  WARNING Could not read PDF page count for verification")

    return {"color": color_pdf, "bw": bw_pdf}


def create_level_package(level: dict) -> Path | None:
    level_num = level["num"]
    level_name = level["name"]

    print(f"\n{'=' * 60}")
    print(f"Creating TpT Package for Find & Cover Level {level_num} ({level_name})")
    print(f"{'=' * 60}")

    pdfs = get_level_pdfs(level_num, level_name)
    if not pdfs:
        print(f"FAILED to find PDFs for Level {level_num}")
        return None

    zip_filename = OUTPUT_DIR / f"{THEME}_{PRODUCT}_level{level_num}_TpT.zip"

    try:
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            color_name = f"Brown_Bear_Find_And_Cover_Level{level_num}_{level_name}_Color.pdf"
            zipf.write(pdfs["color"], color_name)
            print(f"  OK Added: {color_name} ({pdfs['color'].stat().st_size / 1024 / 1024:.1f} MB)")

            bw_name = f"Brown_Bear_Find_And_Cover_Level{level_num}_{level_name}_BW.pdf"
            zipf.write(pdfs["bw"], bw_name)
            print(f"  OK Added: {bw_name} ({pdfs['bw'].stat().st_size / 1024 / 1024:.1f} MB)")

            if TOU_PDF.exists():
                zipf.write(TOU_PDF, "Terms_of_Use_Credits.pdf")
                print(f"  OK Added: Terms_of_Use_Credits.pdf ({TOU_PDF.stat().st_size / 1024:.0f} KB)")
            else:
                print("  WARNING Missing: Terms_of_Use_Credits.pdf")

            if QUICK_START_PDF.exists():
                zipf.write(QUICK_START_PDF, "Quick_Start_Find_And_Cover.pdf")
                print(f"  OK Added: Quick_Start_Find_And_Cover.pdf ({QUICK_START_PDF.stat().st_size / 1024:.0f} KB)")
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
    print("Product: Find & Cover")
    print("=" * 60)

    create_output_dir()

    created_packages: list[Path] = []
    for level in LEVELS:
        package = create_level_package(level)
        if package:
            created_packages.append(package)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nCreated {len(created_packages)} TpT packages:")
    for package in created_packages:
        size = package.stat().st_size / 1024 / 1024
        print(f"  OK {package.name} ({size:.1f} MB)")

    print(f"\nOutput location: {OUTPUT_DIR}")
    print("\nAll packages ready for TpT upload!")

    return created_packages


if __name__ == "__main__":
    create_all_packages()
