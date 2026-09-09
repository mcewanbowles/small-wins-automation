"""Analyze color values used in text across key pages."""
import fitz

doc = fitz.open(r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo_activities.pdf")
for i in [4, 5, 6, 7, 9]:  # Yes/No, Choice Board, Visual Support, AAC
    page = doc[i]
    blocks = page.get_text("dict")["blocks"]
    print(f"=== Page {i+1} colors ===")
    seen = set()
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span["text"].strip()
                if text and len(text) > 2:
                    color = span.get("color", 0)
                    r = (color >> 16) & 255
                    g = (color >> 8) & 255
                    b = color & 255
                    hex_color = f"#{r:02X}{g:02X}{b:02X}"
                    key = (hex_color, round(span["size"]))
                    if key not in seen:
                        seen.add(key)
                        print(f"  [{hex_color}] size={span['size']:.0f} \"{text[:50]}\"")
    print()
doc.close()
