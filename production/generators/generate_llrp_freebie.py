"""LLRP Free Sampler — real-page freebie for TPT.

Builds a freebie PDF from REAL pages of the finished Llama Llama Red Pajama
suite (no placeholders, unlike the retired generate_freebie.py):

  Page 1      branded FREE SAMPLER cover + call to action
  Pages 2..N  one real interior page per flagship activity, stamped
              "FREE SAMPLE" (un-watermarked — this content is genuinely usable)
  Final pages call-to-action listing all products + Terms of Use appended

Usage:  python production/generators/generate_llrp_freebie.py
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

from production.generators.generate_book_participation_pieces import (
    _activity_page,
    _center,
    _fit,
    _font,
    _save_pdf,
)
from utils.UNIVERSAL_STANDARDS import SWS_GOLD, SWS_NAVY, SWS_TEAL, SWS_TEAL_LT
from utils.sws_design import DPI, hex_to_rgb

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "assets" / "themes" / "llama_llama_red_pajama" / "OUTPUT"
TOU = ROOT / "assets" / "global" / "tpt_support_docs" / "Terms of Use.pdf"
PACK_CODE = "LLRP-FREE"
OUT_PDF = OUTPUT / f"{PACK_CODE}_LLRP_Free_Sampler.pdf"
OUT_JSON = OUTPUT / f"{PACK_CODE}_Freebie_BuildResult.json"

# (product name for label, source color PDF, 1-based page to sample)
SAMPLES = [
    ("AAC Communication Board", "LLRP-AAC-REVIEW_AAC_Board_COLOR.pdf", 1),
    ("Matching Cards", "LLRP-MATCH-REVIEW_Matching_COLOR.pdf", 2),
    ("AAC Sentence Building", "LLRP-SENT-LAUNCH_AAC_SentenceStrips_COLOR.pdf", 2),
    ("Story Sequencing", "LLRP-SEQ-LAUNCH_Sequencing_COLOR.pdf", 2),
    ("Vocabulary Snap", "LLRP-VWW-LAUNCH_WordSnap_SymbolText_COLOR.pdf", 2),
    ("Syllable Awareness", "LLRP-SYL-LAUNCH_Syllable_Cards_COLOR.pdf", 2),
    ("CVC Decode & Build", "LLRP-DEC-LAUNCH_Decoding_COLOR.pdf", 2),
    ("Differentiated Bingo", "LLRP-BINGO-LAUNCH_Bingo_COLOR.pdf", 2),
]

ALL_PRODUCTS = [
    "AAC Communication Board", "Matching Cards", "Book Participation Pieces",
    "AAC Sentence Building", "Story Sequencing", "Yes/No Questions",
    "Clue-Think-Infer", "Vocabulary Snap", "Syllable Awareness",
    "CVC Decode & Build", "Story Grammar & Retell", "Differentiated Word Search",
    "Differentiated Bingo", "Reason & Sort: Category Sorting",
    "Print Detective: Letters, Words & First Sounds",
]

PAGE_W, PAGE_H = int(612 * DPI / 72), int(792 * DPI / 72)


def _pill(draw: ImageDraw.ImageDraw, box, text, pt, fill_rgb, text_rgb=(255, 255, 255)):
    draw.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=fill_rgb)
    font = _fit(text, pt, box[2] - box[0] - 60, bold=True)
    _center(draw, box, text, font, text_rgb)


def _cover_page(total_pages: int) -> Image.Image:
    page = _activity_page("Llama Llama Red Pajama", "FREE SAMPLER", PACK_CODE, 1, total_pages)
    draw = ImageDraw.Draw(page)
    navy, teal, gold, teal_lt = hex_to_rgb(SWS_NAVY), hex_to_rgb(SWS_TEAL), hex_to_rgb(SWS_GOLD), hex_to_rgb(SWS_TEAL_LT)

    _pill(draw, (560, 620, PAGE_W - 560, 720), "FREE SAMPLER - TRY BEFORE YOU BUY", 20, teal)
    title = _fit("Llama Llama Red Pajama", 40, PAGE_W - 700, bold=True)
    _center(draw, (350, 780, PAGE_W - 350, 900), "Llama Llama Red Pajama", title, navy)
    sub = _font(15)
    _center(draw, (350, 900, PAGE_W - 350, 980), "Literacy + AAC Activity Suite", sub, navy)

    box = (430, 1060, PAGE_W - 430, 1750)
    draw.rounded_rectangle(box, radius=42, fill=teal_lt, outline=teal, width=4)
    head = _font(17, True)
    _center(draw, (box[0], box[1] + 45, box[2], box[1] + 140), "What's inside this freebie:", head, navy)
    items = [
        "1 real page from 8 different activities",
        "AAC, matching, sentence building, sequencing,",
        "vocabulary, syllables, decoding and bingo",
        "Every activity is differentiated + low prep",
        "Color and ink-friendly B&W in the full products",
    ]
    y = box[1] + 190
    body = _font(14)
    for item in items:
        _center(draw, (box[0], y, box[2], y + 80), item, body, navy)
        y += 105

    _pill(draw, (560, 1920, PAGE_W - 560, 2050), "Love it? Get the complete bundle - 15 activities", 18, gold, navy)
    note = _font(11)
    _center(draw, (350, 2100, PAGE_W - 350, 2180),
            "teacherspayteachers.com/Store/Small-Wins-Studio", note, navy)
    return page


def _sample_page(pdf_name: str, page_1based: int, label: str, page_num: int, total: int) -> Image.Image:
    """Render one real page and stamp a FREE SAMPLE ribbon."""
    src = fitz.open(OUTPUT / pdf_name)
    idx = max(0, min(page_1based - 1, src.page_count - 1))
    pix = src.load_page(idx).get_pixmap(matrix=fitz.Matrix(DPI / 72, DPI / 72), alpha=False)
    src.close()
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    stamp = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    w, h = 1000, 120
    box = (img.width - w - 60, 40, img.width - 60, 40 + h)
    sd.rounded_rectangle(box, radius=60, fill=hex_to_rgb(SWS_GOLD))
    f = _fit("FREE SAMPLE", 16, w - 80, bold=True)
    _center(sd, box, "FREE SAMPLE", f, hex_to_rgb(SWS_NAVY))
    return Image.alpha_composite(img.convert("RGBA"), stamp).convert("RGB")


def _cta_page(page_num: int, total: int) -> Image.Image:
    page = _activity_page("Llama Llama Red Pajama", "GET THE FULL SUITE", PACK_CODE, page_num, total)
    draw = ImageDraw.Draw(page)
    navy, teal, gold = hex_to_rgb(SWS_NAVY), hex_to_rgb(SWS_TEAL), hex_to_rgb(SWS_GOLD)

    head = _fit("The complete suite - 15 differentiated activities", 24, PAGE_W - 700, bold=True)
    _center(draw, (350, 640, PAGE_W - 350, 760), "The complete suite - 15 differentiated activities", head, navy)
    _pill(draw, (700, 830, PAGE_W - 700, 930), "COVERS SCARBOROUGH'S READING ROPE", 15, teal)

    col_w = (PAGE_W - 900) // 2
    item_f = _font(13)
    for i, name in enumerate(ALL_PRODUCTS):
        col, row = divmod(i, 8)
        x = 500 + col * (col_w + 120)
        y = 1040 + row * 140
        draw.rounded_rectangle((x, y, x + col_w, y + 105), radius=30,
                               fill=hex_to_rgb(SWS_TEAL_LT), outline=teal, width=3)
        _center(draw, (x, y, x + col_w, y + 105), name, _fit(name, 13, col_w - 50, minimum=8, bold=False), navy)

    _pill(draw, (560, 2200, PAGE_W - 560, 2320),
          "Search 'Small Wins Studio' on Teachers Pay Teachers", 17, gold, navy)
    return page


def generate_freebie() -> dict:
    total = 2 + len(SAMPLES)
    pages = [_cover_page(total)]
    used = []
    for i, (label, pdf_name, page_no) in enumerate(SAMPLES):
        pages.append(_sample_page(pdf_name, page_no, label, i + 2, total))
        used.append({"product": label, "source": pdf_name, "page": page_no})
    pages.append(_cta_page(total, total))
    _save_pdf(OUT_PDF, pages)

    # Append Terms of Use so the freebie is self-contained.
    if TOU.is_file():
        doc = fitz.open(OUT_PDF)
        tou = fitz.open(TOU)
        doc.insert_pdf(tou)
        tmp = OUT_PDF.with_suffix(".tmp.pdf")
        doc.save(str(tmp), deflate=True)
        doc.close(); tou.close()
        tmp.replace(OUT_PDF)

    manifest = {
        "schema_version": 1,
        "status": "pilot_review",
        "product_id": "llrp_free_sampler",
        "product_name": "Llama Llama Red Pajama - Free Sampler",
        "pack_code": PACK_CODE,
        "sampled_pages": used,
        "terms_of_use_appended": TOU.is_file(),
        "files": {"color_pdf": str(OUT_PDF)},
        "meta": {"warnings": []},
    }
    OUT_JSON.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"OK  {OUT_PDF}")
    return manifest


if __name__ == "__main__":
    generate_freebie()
