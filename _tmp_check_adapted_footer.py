"""Check Adapted Book footer clipping after fix."""
import fitz
from pathlib import Path
import numpy as np
from PIL import Image

base = Path('assets/themes/llama_llama_back_to_school/OUTPUT')
qa_dir = Path('_qa_renders')

# Check text positions in the Adapted Book PDF
doc = fitz.open(str(base / 'LLB01_AdaptedBook_COLOR.pdf'))
print(f"Adapted Book: {len(doc)} pages, page size: {doc[0].rect.width:.0f}x{doc[0].rect.height:.0f}")

for p in [2, 3, 8]:
    page = doc[p-1]
    print(f"\n--- Page {p} ---")
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue
                if any(k in text for k in ['PCS', 'Small Wins', 'Studio', '2026', 'License', 'Maker', 'Adapted', 'Llama']):
                    bbox = span["bbox"]
                    print(f"  y={bbox[1]:.1f}-{bbox[3]:.1f}  x={bbox[0]:.1f}-{bbox[2]:.1f}  {text!r}")
doc.close()

# Also check the rendered images for footer content at edges
print("\n=== Rendered image footer check ===")
for p in [2, 3, 8]:
    img = Image.open(qa_dir / f'adapted_book_p{p}.png')
    arr = np.array(img.convert('RGB'))
    h, w = arr.shape[:2]
    print(f"\n  Page {p} ({w}x{h}):")
    # Footer area is at the bottom of each pane
    # Each pane is ~half the sheet width
    # Check left pane footer (left half) and right pane footer (right half)
    for pane_name, px_start, px_end in [('Left pane', 0, w//2), ('Right pane', w//2, w)]:
        # Footer is at bottom ~8% of the pane
        footer_y = int(0.90 * h)
        footer_h = int(0.08 * h)
        footer_region = arr[footer_y:footer_y+footer_h, px_start:px_end]
        # Check left and right edges of footer (5% margin)
        margin = int(0.05 * (px_end - px_start))
        left_edge = footer_region[:, :margin]
        right_edge = footer_region[:, -margin:]
        left_nonwhite = np.sum(np.any(left_edge < 230, axis=2))
        right_nonwhite = np.sum(np.any(right_edge < 230, axis=2))
        print(f"    {pane_name}: left_edge={left_nonwhite}, right_edge={right_nonwhite} non-white pixels")
