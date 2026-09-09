"""Find a book companion activity PDF with teal header and check layout."""
import fitz
from pathlib import Path

outputs = Path(r"D:\Seagate\small-wins-automation\Studioforge\OUTPUT")
pdfs = list(outputs.rglob("*.pdf"))
for p in pdfs[:30]:
    doc = fitz.open(str(p))
    page = doc[0]
    text = page.get_text().strip()
    drawings = page.get_drawings()
    has_teal = False
    for d in drawings:
        fill = d.get("fill")
        if fill and abs(fill[0] - 0.19) < 0.05 and abs(fill[1] - 0.66) < 0.05:
            has_teal = True
            break
    if has_teal and len(text) > 20:
        print(f"--- {p.name} ---")
        for d in drawings[:8]:
            r = d.get("rect")
            fill = d.get("fill")
            if r and fill:
                h = r.height
                print(f"  fill=({fill[0]:.2f},{fill[1]:.2f},{fill[2]:.2f}) y=({r.y0:.0f}-{r.y1:.0f}) h={h:.0f}")
        for block in page.get_text("dict")["blocks"][:4]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    t = span["text"].strip()
                    if t:
                        bb = span["bbox"]
                        sz = span["size"]
                        print(f"  text: y={bb[1]:.0f} sz={sz:.0f} {t[:60]}")
        doc.close()
        break
    doc.close()
