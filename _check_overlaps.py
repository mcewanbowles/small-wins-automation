"""Check specific overlaps in the activities PDF."""
import fitz

doc = fitz.open(r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo_activities.pdf")
for page_idx in [0, 1, 2, 3, 4, 5, 6, 7, 8]:  # all 10 pages (0-indexed)
    page = doc[page_idx]
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
                items.append({"text": text, "x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3]})
    overlaps = []
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            ix = max(0, min(items[a]["x1"], items[b]["x1"]) - max(items[a]["x0"], items[b]["x0"]))
            iy = max(0, min(items[a]["y1"], items[b]["y1"]) - max(items[a]["y0"], items[b]["y0"]))
            if ix > 2 and iy > 2:
                ta = items[a]["text"][:35]
                tb = items[b]["text"][:35]
                overlaps.append(f"  [{ta}] overlaps [{tb}] by {ix:.0f}x{iy:.0f}")
    if overlaps:
        print(f"=== PAGE {page_idx+1} ({len(overlaps)} overlaps) ===")
        for o in overlaps[:8]:
            print(o)
        if len(overlaps) > 8:
            print(f"  ... and {len(overlaps)-8} more")
        print()
doc.close()
