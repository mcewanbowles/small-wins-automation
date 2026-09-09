"""Check text positions in AAC Board PDFs for footer overlap."""
import fitz
from pathlib import Path

base = Path('assets/themes/llama_llama_back_to_school/OUTPUT')

for name, fname in [('COLOR', 'LLB01_AAC_Board_COLOR.pdf'),
                     ('HI-VIS BLACK', 'LLB01_AAC_Board_COLOR_HIGHVIS_BLACK.pdf'),
                     ('HI-VIS YELLOW', 'LLB01_AAC_Board_COLOR_HIGHVIS_YELLOW.pdf')]:
    doc = fitz.open(str(base / fname))
    page = doc[0]
    print(f"\n=== {name} ({page.rect.width:.0f}x{page.rect.height:.0f}) ===")
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue
                if any(k in text for k in ['PCS', 'Small Wins', 'Studio', '2026', 'License', 'Maker']):
                    bbox = span["bbox"]
                    print(f"  y={bbox[1]:.1f}-{bbox[3]:.1f}  x={bbox[0]:.1f}-{bbox[2]:.1f}  {text!r}")
    doc.close()
