"""Render PDF pages to PNG for visual QA."""
import sys, os, subprocess
from pathlib import Path

def render_pdf_pages(pdf_path, out_prefix, max_pages=None, dpi=100):
    """Render PDF pages to PNG using pdf2image or PyMuPDF."""
    pdf_path = Path(pdf_path)
    out_prefix = Path(out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    # Try PyMuPDF (fitz)
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        pages = []
        n = min(len(doc), max_pages) if max_pages else len(doc)
        for i in range(n):
            page = doc[i]
            mat = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=mat)
            out = f"{out_prefix}_p{i+1}.png"
            pix.save(out)
            pages.append(out)
            print(f"  Rendered page {i+1}/{n}: {out} ({pix.width}x{pix.height})")
        doc.close()
        return pages
    except ImportError:
        pass

    # Try pdf2image
    try:
        from pdf2image import convert_from_path
        pages_imgs = convert_from_path(str(pdf_path), dpi=dpi)
        pages = []
        for i, img in enumerate(pages_imgs[:max_pages] if max_pages else pages_imgs):
            out = f"{out_prefix}_p{i+1}.png"
            img.save(out)
            pages.append(out)
            print(f"  Rendered page {i+1}/{len(pages_imgs)}: {out} ({img.size})")
        return pages
    except ImportError:
        pass

    print(f"  ERROR: Neither PyMuPDF nor pdf2image available")
    return []

if __name__ == '__main__':
    base = Path('assets/themes/llama_llama_back_to_school/OUTPUT')
    qa_dir = Path('_qa_renders')
    qa_dir.mkdir(exist_ok=True)

    pdfs = [
        ('LLB01_IEP_MonitoringForm.pdf', 'iep', 1, 150),
        ('LLB01_YesNoQuestions_COLOR.pdf', 'yesno', 5, 100),
        ('LLB01_AAC_Board_COLOR.pdf', 'aac_color', 1, 150),
        ('LLB01_AAC_Board_COLOR_HIGHVIS_BLACK.pdf', 'aac_hvblack', 1, 150),
        ('LLB01_AAC_Board_COLOR_HIGHVIS_YELLOW.pdf', 'aac_hvyellow', 1, 150),
        ('LLB01_AdaptedBook_COLOR.pdf', 'adapted_book', 8, 100),
    ]

    for pdf_name, prefix, pages, dpi in pdfs:
        pdf_path = base / pdf_name
        if not pdf_path.exists():
            print(f"\nSKIP {pdf_name}: not found")
            continue
        print(f"\n=== {pdf_name} ===")
        render_pdf_pages(pdf_path, qa_dir / prefix, max_pages=pages, dpi=dpi)
