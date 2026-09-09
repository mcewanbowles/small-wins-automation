"""QA the half-page social story PDF."""
import fitz
from pathlib import Path

pdf = Path(r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo_social_story_half.pdf")
doc = fitz.open(str(pdf))
print(f"Pages: {doc.page_count}")
print(f"Page size: {doc[0].rect}")
print()

total_overlaps = 0
total_oob = 0

for i in range(doc.page_count):
    page = doc[i]
    pr = page.rect
    print(f"===== SHEET {i+1} =====")
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

    print(f"  Text items: {len(items)}")
    for item in items:
        print(f"    [{item['x0']:6.1f}, {item['y0']:6.1f}] -> [{item['x1']:6.1f}, {item['y1']:6.1f}]  sz={item['size']:4.1f}  {item['text'][:60]}")

    # Check overlaps
    overlaps = 0
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            ix = max(0, min(items[a]["x1"], items[b]["x1"]) - max(items[a]["x0"], items[b]["x0"]))
            iy = max(0, min(items[a]["y1"], items[b]["y1"]) - max(items[a]["y0"], items[b]["y0"]))
            if ix > 2 and iy > 2:
                overlaps += 1
                total_overlaps += 1
    if overlaps:
        print(f"  *** OVERLAPS: {overlaps} ***")

    # Check out of bounds (24pt margin for half-page)
    margin = 20
    oob = 0
    for item in items:
        if item["x0"] < margin - 2 or item["x1"] > pr.width - margin + 2:
            oob += 1
            total_oob += 1
        if item["y0"] < margin - 2 or item["y1"] > pr.height - margin + 2:
            oob += 1
            total_oob += 1
    if oob:
        print(f"  *** OUT OF BOUNDS: {oob} ***")

    # Check images
    images = page.get_images()
    print(f"  Images: {len(images)}")
    print()

print(f"TOTAL: {total_overlaps} overlaps, {total_oob} out-of-bounds across {doc.page_count} sheets")
doc.close()
