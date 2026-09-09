"""Extract text from PDF pages for QA verification."""
import sys
import fitz
from pathlib import Path

def extract_text(pdf_path, max_pages=None):
    """Extract text from each page of a PDF."""
    doc = fitz.open(str(pdf_path))
    pages = []
    n = min(len(doc), max_pages) if max_pages else len(doc)
    for i in range(n):
        page = doc[i]
        text = page.get_text()
        pages.append(text)
    doc.close()
    return pages

base = Path('assets/themes/llama_llama_back_to_school/OUTPUT')

# 1. IEP Monitoring Form
print("=" * 60)
print("ITEM 1: IEP Monitoring Form")
print("=" * 60)
pages = extract_text(base / 'LLB01_IEP_MonitoringForm.pdf', 1)
for i, text in enumerate(pages):
    print(f"\n--- Page {i+1} ---")
    # Look for subtitle and grid header
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if any(k in line for k in ['Llama', 'Lama', 'Back', 'School', 'C/Total', 'Total', 'IEP', 'Monitoring']):
            print(f"  {line!r}")

# 2. Yes/No Questions - check questions and answers
print("\n" + "=" * 60)
print("ITEM 2: Yes/No Questions - card content")
print("=" * 60)
pages = extract_text(base / 'LLB01_YesNoQuestions_COLOR.pdf', 5)
for i, text in enumerate(pages):
    print(f"\n--- Page {i+1} ---")
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if any(k in line for k in ['Is this', 'Does', 'Can', 'Are', 'Should', 'YES', 'NO', 'Llama', 'cubby', 'classroom']):
            print(f"  {line!r}")

# 3. AAC Board footer text
print("\n" + "=" * 60)
print("ITEM 4: AAC Board footer text")
print("=" * 60)
for name, fname in [('COLOR', 'LLB01_AAC_Board_COLOR.pdf'),
                     ('HI-VIS BLACK', 'LLB01_AAC_Board_COLOR_HIGHVIS_BLACK.pdf'),
                     ('HI-VIS YELLOW', 'LLB01_AAC_Board_COLOR_HIGHVIS_YELLOW.pdf')]:
    pages = extract_text(base / fname, 1)
    print(f"\n--- {name} ---")
    for line in pages[0].split('\n'):
        line = line.strip()
        if not line:
            continue
        if any(k in line for k in ['PCS', 'Small Wins', 'Studio', '2026', 'License', 'Maker']):
            print(f"  {line!r}")

# 4. Adapted Book footer
print("\n" + "=" * 60)
print("ITEM 6: Adapted Book footer text")
print("=" * 60)
pages = extract_text(base / 'LLB01_AdaptedBook_COLOR.pdf', 8)
for i, text in enumerate(pages):
    print(f"\n--- Page {i+1} ---")
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if any(k in line for k in ['PCS', 'Small Wins', 'Studio', '2026', 'License', 'Maker']):
            print(f"  {line!r}")
