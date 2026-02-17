#!/usr/bin/env python3
"""Create TpT-Ready ZIP Package for Brown Bear Sequencing.

Packages the Sequencing product as a single ZIP with:
- Color PDF (all levels + student template + cutouts + answer key)
- Black & White PDF
- Terms of Use / Credits
- Quick Start Guide
- TpT Description (text file)

Output:
  production/final_products/brown_bear/sequencing/tpt_zips/

Usage:
  python -m production.generators.create_tpt_packages_sequencing
"""

from __future__ import annotations

import zipfile
from pathlib import Path


THEME = "brown_bear"
PRODUCT = "sequencing"

REPO_ROOT = Path(__file__).resolve().parents[2]
FINAL_DIR = REPO_ROOT / "production" / "final_products" / THEME / PRODUCT
SAMPLES_DIR = REPO_ROOT / "samples" / THEME / PRODUCT
SUPPORT_DOCS_DIR = REPO_ROOT / "production" / "support_docs"
OUTPUT_DIR = FINAL_DIR / "tpt_zips"

TOU_PDF = SUPPORT_DOCS_DIR / "Terms_of_Use_Credits.pdf"
QUICK_START_PDF = SAMPLES_DIR / f"{THEME}_{PRODUCT}_quick_start.pdf"

COLOR_PDF = FINAL_DIR / f"{THEME}_{PRODUCT}_color_FINAL.pdf"
BW_PDF = FINAL_DIR / f"{THEME}_{PRODUCT}_bw_FINAL.pdf"

TPT_DESCRIPTION = """Brown Bear - Story Sequencing Activity (4 Differentiated Levels)

WHAT'S INCLUDED:
- 4 levelled sequencing activity pages
- Student template page (blank, for cut & paste)
- Cut-out picture cards (10 characters)
- Answer key
- Full colour AND black & white versions
- Quick Start Guide
- Terms of Use

ABOUT THIS RESOURCE:
This story sequencing activity uses the beloved characters from Brown Bear, Brown Bear, What Do You See? by Bill Martin Jr. Students arrange picture cards in story order to build comprehension, retelling, and narrative sequencing skills.

4 LEVELS OF DIFFERENTIATION:
Level 1: Look at the story order (visual model with pictures in place)
Level 2: Cut and paste in story order (hands-on sequencing)
Level 3: Pictures + words - read and match the sequence
Level 4: Write the character names in order (highest challenge)

PERFECT FOR:
- Special Education (SPED) classrooms
- Autism (ASD) support
- Early childhood and kindergarten
- Speech-Language Pathology (SLP) sessions
- Occupational therapy
- Morning work and independent stations
- Small group instruction

HOW TO USE:
1. Print and laminate for durability (or use as worksheets)
2. Cut out the picture cards from the cut-outs page
3. Read the book aloud first
4. Students sequence the cards on the template or activity page
5. Check against the answer key

TEACHING TIPS:
- Start with Level 1 as a visual model before moving to hands-on
- Use the cut-out cards with the student template for reusable practice
- Add Velcro dots for a hands-on, reusable activity
- Model sequencing language: first, next, then, last
- Perfect for retelling practice after shared reading

PART OF THE BROWN BEAR COLLECTION:
Check out our complete Brown Bear resource collection including Matching, Find & Cover, Bingo, and AAC Literacy Chat Boards!

SUPPORT A NEW BUSINESS:
Thank you for supporting Small Wins Studio! Your review means the world to us.

---
(c) 2026 Small Wins Studio
PCS symbols used with active PCS Maker Personal License.
For personal and classroom use only. Please purchase additional licenses for other teachers.

KEYWORDS: sequencing, story order, retelling, narrative, Brown Bear, special education,
SPED, autism, ASD, early childhood, kindergarten, differentiated, cut and paste,
hands-on learning, visual supports, speech therapy, SLP, literacy, comprehension
"""


def create_package() -> Path | None:
    print("\n" + "=" * 60)
    print("TpT Package Creator")
    print(f"Theme: {THEME.replace('_', ' ').title()}")
    print("Product: Sequencing")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

    zip_filename = OUTPUT_DIR / f"{THEME}_{PRODUCT}_TpT.zip"

    try:
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Color PDF
            if COLOR_PDF.exists():
                zipf.write(COLOR_PDF, "Brown_Bear_Sequencing_Color.pdf")
                size_mb = COLOR_PDF.stat().st_size / 1024 / 1024
                print(f"  OK Added: Brown_Bear_Sequencing_Color.pdf ({size_mb:.1f} MB)")
            else:
                print(f"  WARNING Missing: {COLOR_PDF.name}")

            # BW PDF
            if BW_PDF.exists():
                zipf.write(BW_PDF, "Brown_Bear_Sequencing_BW.pdf")
                size_mb = BW_PDF.stat().st_size / 1024 / 1024
                print(f"  OK Added: Brown_Bear_Sequencing_BW.pdf ({size_mb:.1f} MB)")
            else:
                print(f"  WARNING Missing: {BW_PDF.name}")

            # Terms of Use
            if TOU_PDF.exists():
                zipf.write(TOU_PDF, "Terms_of_Use_Credits.pdf")
                print(f"  OK Added: Terms_of_Use_Credits.pdf ({TOU_PDF.stat().st_size / 1024:.0f} KB)")
            else:
                print("  WARNING Missing: Terms_of_Use_Credits.pdf")

            # Quick Start
            if QUICK_START_PDF.exists():
                zipf.write(QUICK_START_PDF, "Quick_Start_Sequencing.pdf")
                print(f"  OK Added: Quick_Start_Sequencing.pdf ({QUICK_START_PDF.stat().st_size / 1024:.0f} KB)")
            else:
                print(f"  WARNING Missing: {QUICK_START_PDF}")

            # TpT Description
            zipf.writestr("TpT_Description.txt", TPT_DESCRIPTION.strip())
            print("  OK Added: TpT_Description.txt")

        zip_size = zip_filename.stat().st_size / 1024 / 1024
        print(f"\nOK Created: {zip_filename.name} ({zip_size:.1f} MB)")

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"\n  OK {zip_filename.name} ({zip_size:.1f} MB)")
        print(f"\nOutput location: {OUTPUT_DIR}")
        print("\nPackage ready for TpT upload!")

        return zip_filename

    except Exception as e:
        print(f"Error creating ZIP: {e}")
        return None


if __name__ == "__main__":
    create_package()
