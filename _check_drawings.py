"""Check PDF drawing commands to verify colours and positions."""
import fitz

doc = fitz.open(r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo.pdf")

for pg in range(doc.page_count):
    page = doc[pg]
    drawings = page.get_drawings()
    print(f"\n===== PAGE {pg+1}: {len(drawings)} drawings =====")
    for i, d in enumerate(drawings[:12]):
        r = d.get("rect")
        fill = d.get("fill")
        stroke = d.get("color")
        print(f"  {i}: fill={fill} stroke={stroke} rect=({r.x0:.0f},{r.y0:.0f},{r.x1:.0f},{r.y1:.0f}) w={r.width:.0f} h={r.height:.0f}")

doc.close()
