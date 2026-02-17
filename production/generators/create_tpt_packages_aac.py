#!/usr/bin/env python3
"""Create TpT-Ready ZIP Package for Brown Bear AAC Literacy Chat Boards.

Packages the AAC product as a single ZIP with:
- Literacy Chat Boards (landscape, color + BW)
- Communication Strips (landscape, color + BW)
- Core Word Board (landscape, color + BW)
- Storage Labels (landscape, color + BW)
- Terms of Use / Credits
- Quick Start Guide
- TpT Description (text file)

Output:
  production/final_products/brown_bear/aac/tpt_zips/

Usage:
  python -m production.generators.create_tpt_packages_aac
"""

from __future__ import annotations

import zipfile
from pathlib import Path


THEME = "brown_bear"
PRODUCT = "aac"

REPO_ROOT = Path(__file__).resolve().parents[2]
FINAL_DIR = REPO_ROOT / "production" / "final_products" / THEME / PRODUCT
SAMPLES_DIR = REPO_ROOT / "samples" / THEME / PRODUCT
SUPPORT_DOCS_DIR = REPO_ROOT / "production" / "support_docs"
OUTPUT_DIR = FINAL_DIR / "tpt_zips"

TOU_PDF = SUPPORT_DOCS_DIR / "Terms_of_Use_Credits.pdf"
QUICK_START_PDF = SAMPLES_DIR / f"{THEME}_{PRODUCT}_quick_start.pdf"

# AAC PDFs to include (landscape versions only for TpT)
AAC_PDFS = [
    {
        "file": "brown_bear_literacy_chat_board_landscape_color_FINAL.pdf",
        "zip_name": "Brown_Bear_Literacy_Chat_Board_Color.pdf",
    },
    {
        "file": "brown_bear_literacy_chat_board_landscape_bw_FINAL.pdf",
        "zip_name": "Brown_Bear_Literacy_Chat_Board_BW.pdf",
    },
    {
        "file": "brown_bear_aac_strips_landscape_color_FINAL.pdf",
        "zip_name": "Brown_Bear_Communication_Strips_Color.pdf",
    },
    {
        "file": "brown_bear_aac_strips_landscape_bw_FINAL.pdf",
        "zip_name": "Brown_Bear_Communication_Strips_BW.pdf",
    },
    {
        "file": "brown_bear_aac_core_board_landscape_color_FINAL.pdf",
        "zip_name": "Brown_Bear_Core_Word_Board_Color.pdf",
    },
    {
        "file": "brown_bear_aac_core_board_landscape_bw_FINAL.pdf",
        "zip_name": "Brown_Bear_Core_Word_Board_BW.pdf",
    },
    {
        "file": "brown_bear_aac_storage_labels_landscape_color_FINAL.pdf",
        "zip_name": "Brown_Bear_AAC_Storage_Labels.pdf",
    },
]

TPT_DESCRIPTION = """Brown Bear - AAC Literacy Chat Boards

WHAT'S INCLUDED:
- Literacy Chat Boards (landscape, full colour + black & white)
- Communication Strips (landscape, full colour + black & white)
- Core Word Board (landscape, full colour + black & white)
- Storage Labels
- Quick Start Guide
- Terms of Use

ABOUT THIS RESOURCE:
These AAC Literacy Chat Boards are designed to support book-based communication during shared reading of Brown Bear, Brown Bear, What Do You See? by Bill Martin Jr.

Use the boards to model core vocabulary, support aided language input, and encourage students to participate in literacy activities using symbols and icons.

PERFECT FOR:
- Special Education (SPED) classrooms
- Speech-Language Pathology (SLP) sessions
- Autism (ASD) support
- AAC users and emerging communicators
- Shared reading and circle time
- 1:1 and small group instruction

HOW TO USE:
1. Print and laminate the boards for durability
2. Place the board within student reach during reading
3. Point to symbols on the board as you read
4. Model core words: look, more, turn, again, I see
5. Encourage student to point, activate, or sign

TEACHING TIPS:
- Use Aided Language Input: point to symbols AS you speak
- Start with 2-3 core words, then expand
- Be consistent - use the same board each reading session
- Accept ALL communication attempts (pointing, eye gaze, device)
- Pair with the student's personal AAC system

PART OF THE BROWN BEAR COLLECTION:
Check out our complete Brown Bear resource collection including Matching, Find & Cover, and Bingo activities - all with 5 levels of differentiation!

SUPPORT A NEW BUSINESS:
Thank you for supporting Small Wins Studio! Your review means the world to us.

---
(c) 2026 Small Wins Studio
PCS symbols used with active PCS Maker Personal License.
For personal and classroom use only. Please purchase additional licenses for other teachers.

KEYWORDS: AAC, augmentative communication, literacy, chat board, communication board,
core words, aided language input, special education, SPED, autism, ASD, speech therapy,
SLP, Brown Bear, shared reading, book companion, visual supports
"""


def create_package() -> Path | None:
    print("\n" + "=" * 60)
    print("TpT Package Creator")
    print(f"Theme: {THEME.replace('_', ' ').title()}")
    print("Product: AAC Literacy Chat Boards")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

    zip_filename = OUTPUT_DIR / f"{THEME}_aac_literacy_chat_boards_TpT.zip"

    try:
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add AAC PDFs
            for pdf_info in AAC_PDFS:
                src = FINAL_DIR / pdf_info["file"]
                if src.exists():
                    zipf.write(src, pdf_info["zip_name"])
                    size_mb = src.stat().st_size / 1024 / 1024
                    print(f"  OK Added: {pdf_info['zip_name']} ({size_mb:.1f} MB)")
                else:
                    print(f"  WARNING Missing: {pdf_info['file']}")

            # Terms of Use
            if TOU_PDF.exists():
                zipf.write(TOU_PDF, "Terms_of_Use_Credits.pdf")
                print(f"  OK Added: Terms_of_Use_Credits.pdf ({TOU_PDF.stat().st_size / 1024:.0f} KB)")
            else:
                print("  WARNING Missing: Terms_of_Use_Credits.pdf")

            # Quick Start
            if QUICK_START_PDF.exists():
                zipf.write(QUICK_START_PDF, "Quick_Start_AAC_Literacy_Chat_Boards.pdf")
                print(f"  OK Added: Quick_Start_AAC_Literacy_Chat_Boards.pdf ({QUICK_START_PDF.stat().st_size / 1024:.0f} KB)")
            else:
                print(f"  WARNING Missing: {QUICK_START_PDF}")

            # TpT Description
            zipf.writestr("TpT_Description.txt", TPT_DESCRIPTION.strip())
            print("  OK Added: TpT_Description.txt")

        zip_size = zip_filename.stat().st_size / 1024 / 1024
        print(f"\nOK Created: {zip_filename.name} ({zip_size:.1f} MB)")

        # Summary
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
