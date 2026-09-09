"""Render PDF pages as PNG images for visual design review."""
import fitz
from pathlib import Path

out_dir = Path(r"D:\Seagate\small-wins-automation\Dignity\products\_review")
out_dir.mkdir(exist_ok=True)

pdfs = [
    ("activities", Path(r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo_activities.pdf")),
    ("formats", Path(r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo_social_story_formats.pdf")),
    ("support", Path(r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo_support.pdf")),
]

for name, pdf in pdfs:
    doc = fitz.open(str(pdf))
    count = doc.page_count
    for i in range(count):
        page = doc[i]
        mat = fitz.Matrix(2, 2)  # 2x zoom for clarity
        pix = page.get_pixmap(matrix=mat)
        pix.save(str(out_dir / f"{name}_p{i+1:02d}.png"))
    doc.close()
    print(f"Rendered {count} pages from {pdf.name}")

print(f"\nImages saved to: {out_dir}")
