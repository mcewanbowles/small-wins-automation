"""Check book companion PDFs for footer layout, logo position, border format."""
import fitz
from pathlib import Path

# Find PDFs with actual content
outputs = Path(r"D:\Seagate\small-wins-automation\Studioforge\OUTPUT")
pdfs = list(outputs.rglob("*.pdf"))

found = 0
for p in pdfs:
    if found >= 3:
        break
    doc = fitz.open(str(p))
    page = doc[0]
    text = page.get_text().strip()
    if len(text) < 30:
        doc.close()
        continue

    print(f"=== {p.name} ===")
    print(f"Page size: {page.rect}")

    # Check images (logo)
    images = page.get_images()
    print(f"Images: {len(images)}")
    for img in images:
        # Get image placement
        for inst in page.get_image_rects(img[0]):
            print(f"  logo at: ({inst.x0:.0f},{inst.y0:.0f}) -> ({inst.x1:.0f},{inst.y1:.0f}) w={inst.width:.0f} h={inst.height:.0f}")

    # Check drawings (border, header)
    drawings = page.get_drawings()
    print(f"Drawings: {len(drawings)}")
    for i, d in enumerate(drawings[:10]):
        r = d.get("rect")
        fill = d.get("fill")
        stroke = d.get("color")
        if r:
            print(f"  {i}: fill={fill} stroke={stroke} rect=({r.x0:.0f},{r.y0:.0f},{r.x1:.0f},{r.y1:.0f})")

    # Check all text (especially footer area - bottom 100pt)
    print("Footer text (bottom 100pt):")
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span["text"].strip()
                if t:
                    bb = span["bbox"]
                    if bb[1] > page.rect.height - 100:  # bottom 100pt
                        print(f"  y={bb[1]:.0f} x={bb[0]:.0f}-{bb[2]:.0f} sz={span['size']:.0f} '{t}'")

    # Header text (top 100pt)
    print("Header text (top 100pt):")
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                t = span["text"].strip()
                if t:
                    bb = span["bbox"]
                    if bb[1] < 100:
                        print(f"  y={bb[1]:.0f} x={bb[0]:.0f}-{bb[2]:.0f} sz={span['size']:.0f} '{t}'")

    doc.close()
    found += 1
    print()
