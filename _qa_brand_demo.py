"""QA all brand demo PDFs for alignment, overlap, and clipping issues."""
import fitz
from pathlib import Path

pdfs = [
    Path(r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo_activities.pdf"),
    Path(r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo_social_story_formats.pdf"),
    Path(r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo_support.pdf"),
]

grand_overlaps = 0
grand_oob = 0

for pdf in pdfs:
    if not pdf.exists():
        print(f"MISSING: {pdf}")
        continue
    doc = fitz.open(str(pdf))
    print(f"===== {pdf.name} =====")
    print(f"Pages: {doc.page_count}")
    print(f"Page size: {doc[0].rect}")

    for i in range(doc.page_count):
        page = doc[i]
        pr = page.rect
        blocks = page.get_text("dict")["blocks"]
        items = []
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if not text:
                        continue
                    bbox = span["bbox"]
                    items.append({
                        "text": text,
                        "x0": round(bbox[0], 1),
                        "y0": round(bbox[1], 1),
                        "x1": round(bbox[2], 1),
                        "y1": round(bbox[3], 1),
                        "size": round(span["size"], 1),
                    })

        # Check overlaps
        overlaps = 0
        for a in range(len(items)):
            for b in range(a + 1, len(items)):
                ix = max(0, min(items[a]["x1"], items[b]["x1"]) - max(items[a]["x0"], items[b]["x0"]))
                iy = max(0, min(items[a]["y1"], items[b]["y1"]) - max(items[a]["y0"], items[b]["y0"]))
                if ix > 2 and iy > 2:
                    overlaps += 1
                    grand_overlaps += 1

        # Check out of bounds — use smaller margin for multi-up layouts
        margin = 30 if doc.page_count <= 3 else 12  # half-page=8, mini-book=4
        oob = 0
        for item in items:
            if item["x0"] < margin - 2 or item["x1"] > pr.width - margin + 2:
                oob += 1
                grand_oob += 1
            if item["y0"] < margin - 2 or item["y1"] > pr.height - margin + 2:
                oob += 1
                grand_oob += 1

        # Print summary per page
        title_item = next((it for it in items if it["size"] >= 18), None)
        title = title_item["text"][:40] if title_item else "?"
        status = "OK" if overlaps == 0 and oob == 0 else f"OVERLAPS={overlaps} OOB={oob}"
        print(f"  Page {i+1:2d}: {len(items):3d} items  |  {title:40s}  |  {status}")

    doc.close()
    print()

print(f"GRAND TOTAL: {grand_overlaps} overlaps, {grand_oob} out-of-bounds")
