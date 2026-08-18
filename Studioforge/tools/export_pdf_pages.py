import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception as e:
    raise SystemExit(f"Missing dependency PyMuPDF: {e}")


def export(pdf_path: str, out_dir: str, out_prefix: str, pages=(0, 1), dpi: int = 144) -> None:
    p_pdf = Path(pdf_path)
    if not p_pdf.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(p_pdf))
    try:
        for i in pages:
            if 0 <= i < len(doc):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=dpi, alpha=False)
                out_path = out / f"{out_prefix}_p{i+1}.png"
                pix.save(str(out_path))
    finally:
        doc.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python export_pdf_pages.py <pdf_path> <out_dir> [prefix] [pages_csv] [dpi]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2]
    prefix = sys.argv[3] if len(sys.argv) > 3 else Path(pdf_path).stem
    if len(sys.argv) > 4:
        parts = [s.strip() for s in sys.argv[4].split(",") if s.strip()]
        pages = tuple(max(0, int(x) - 1) for x in parts if x.isdigit())
        if not pages:
            pages = (0, 1)
    else:
        pages = (0, 1)
    dpi = int(sys.argv[5]) if len(sys.argv) > 5 else 144
    export(pdf_path, out_dir, prefix, pages, dpi)
